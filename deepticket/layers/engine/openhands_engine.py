from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import httpx

from deepticket.config.schema import EngineConfig
from deepticket.layers.input.models import AgentInput
from deepticket.layers.output.activity import format_agent_activity
from deepticket.layers.output.adapter import OutputAdapter
from deepticket.layers.output.models import StreamChunk


class OpenHandsEngine:
    """引擎层：对接 OpenHands Agent Server 的 OpenAI 网关。"""

    def __init__(
        self,
        config: EngineConfig,
        *,
        llm_model: str,
        llm_api_key: str,
        llm_base_url: str,
    ) -> None:
        self.config = config
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key
        self.llm_base_url = llm_base_url
        self.server = (
            f"http://{config.agent_server_host}:{config.agent_server_port}"
        )
        self.gateway_model = f"openhands_{config.llm_profile}"

    def _client(self, timeout: float | None = 60.0) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=timeout, trust_env=False)

    def _headers(self, *, stream: bool = False) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.session_api_key:
            headers["X-Session-API-Key"] = self.config.session_api_key
        if stream:
            headers["Accept"] = "text/event-stream"
        return headers

    async def ensure_ready(self, *, max_attempts: int = 60) -> None:
        last_error: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                async with self._client(timeout=10.0) as client:
                    health = await client.get(f"{self.server}/health")
                    health.raise_for_status()
                await self._register_profile()
                return
            except (httpx.HTTPError, RuntimeError) as exc:
                last_error = exc
                if attempt == max_attempts:
                    break
                import asyncio

                await asyncio.sleep(1)
        raise RuntimeError(
            f"Agent Server 未就绪 ({self.server}): {last_error}"
        ) from last_error

    def build_headers(self, *, stream: bool = False) -> dict[str, str]:
        return self._headers(stream=stream)

    @staticmethod
    def _build_user_message(agent_input: AgentInput) -> str | list[dict[str, object]]:
        if not agent_input.image_urls:
            return agent_input.prompt
        content: list[dict[str, object]] = [
            {"type": "text", "text": agent_input.prompt},
        ]
        for url in agent_input.image_urls:
            content.append({"type": "image_url", "image_url": {"url": url}})
        return content

    async def sync_mcp_config(self, servers: dict[str, dict]) -> None:
        """同步 MCP 到 Agent Server；传空 dict 会清空旧配置。"""
        body = {"agent_settings_diff": {"mcp_config": servers}}
        async with self._client() as client:
            resp = await client.patch(
                f"{self.server}/api/settings",
                headers=self._headers(),
                json=body,
            )
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"同步 MCP 配置失败: {resp.status_code} {resp.text}"
                )

    async def _register_profile(self) -> None:
        body = {
            "llm": {
                "model": self.llm_model,
                "api_key": self.llm_api_key,
                "base_url": self.llm_base_url,
            },
            "include_secrets": True,
        }
        async with self._client() as client:
            resp = await client.post(
                f"{self.server}/api/profiles/{self.config.llm_profile}",
                headers=self._headers(),
                json=body,
            )
            if resp.status_code not in (200, 201):
                raise RuntimeError(
                    f"注册 LLM profile 失败: {resp.status_code} {resp.text}"
                )

    async def _poll_agent_activities(
        self,
        conversation_id: str,
        *,
        seen_event_ids: set[str],
        out_queue: asyncio.Queue[StreamChunk | None],
        poll_stop: asyncio.Event,
    ) -> None:
        await out_queue.put(StreamChunk(activity="Agent 已就绪，开始分析…"))
        while not poll_stop.is_set():
            try:
                async with self._client(timeout=10.0) as client:
                    resp = await client.get(
                        f"{self.server}/api/conversations/{conversation_id}/events/search",
                        headers=self._headers(),
                        params={"limit": 80, "sort_order": "TIMESTAMP"},
                    )
                    resp.raise_for_status()
                    items = resp.json().get("items", [])
                for event in items:
                    event_id = event.get("id")
                    if not event_id or event_id in seen_event_ids:
                        continue
                    seen_event_ids.add(event_id)
                    label = format_agent_activity(event)
                    if label:
                        await out_queue.put(StreamChunk(activity=label))
            except httpx.HTTPError:
                pass
            try:
                await asyncio.wait_for(poll_stop.wait(), timeout=0.75)
            except TimeoutError:
                continue

    async def stream(self, agent_input: AgentInput) -> AsyncIterator[StreamChunk]:
        payload = {
            "model": self.gateway_model,
            "stream": True,
            "messages": [
                {
                    "role": "user",
                    "content": self._build_user_message(agent_input),
                }
            ],
        }
        headers = self._headers(stream=True)
        if agent_input.conversation_id:
            headers["X-OpenHands-ServerConversation-ID"] = agent_input.conversation_id

        yield StreamChunk(activity="正在连接 Agent…")

        client = self._client(timeout=None)
        try:
            req = client.build_request(
                "POST",
                f"{self.server}/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp = await client.send(req, stream=True)
        except httpx.HTTPError as exc:
            await client.aclose()
            raise RuntimeError(f"Agent Server 请求失败: {exc}") from exc

        if resp.status_code >= 400:
            text = await resp.aread()
            await resp.aclose()
            await client.aclose()
            raise RuntimeError(f"Agent Server 返回 {resp.status_code}: {text.decode()}")

        out_queue: asyncio.Queue[StreamChunk | None] = asyncio.Queue()
        poll_stop = asyncio.Event()
        seen_event_ids: set[str] = set()
        poller_task: asyncio.Task[None] | None = None

        async def pump_sse() -> None:
            nonlocal poller_task
            conversation_id = (
                resp.headers.get("x-openhands-serverconversation-id")
                or resp.headers.get("x-openhands-server-conversation-id")
            )
            if conversation_id:
                await out_queue.put(StreamChunk(conversation_id=conversation_id))
                poller_task = asyncio.create_task(
                    self._poll_agent_activities(
                        conversation_id,
                        seen_event_ids=seen_event_ids,
                        out_queue=out_queue,
                        poll_stop=poll_stop,
                    )
                )

            buffer = ""
            try:
                async for raw in resp.aiter_bytes():
                    if not raw:
                        continue
                    buffer += raw.decode("utf-8", errors="replace")
                    parts = buffer.split("\n\n")
                    buffer = parts.pop() if parts else ""

                    for part in parts:
                        for line in part.split("\n"):
                            line = line.strip()
                            if not line:
                                continue
                            chunk = OutputAdapter.parse_sse_line(line)
                            if chunk is None:
                                continue
                            if (
                                chunk.conversation_id is None
                                and conversation_id
                            ):
                                chunk.conversation_id = conversation_id
                            await out_queue.put(chunk)
            finally:
                poll_stop.set()
                if poller_task is not None:
                    try:
                        await asyncio.wait_for(poller_task, timeout=1.5)
                    except TimeoutError:
                        poller_task.cancel()
                await out_queue.put(None)

        pump_task = asyncio.create_task(pump_sse())
        try:
            while True:
                item = await out_queue.get()
                if item is None:
                    break
                yield item
        finally:
            poll_stop.set()
            if not pump_task.done():
                pump_task.cancel()
                try:
                    await pump_task
                except asyncio.CancelledError:
                    pass
            await resp.aclose()
            await client.aclose()
