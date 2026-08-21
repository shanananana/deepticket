from __future__ import annotations

import logging
import asyncio
import contextlib
import copy
import json
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import httpx
import websockets

from deepticket.config.schema import EngineConfig
from deepticket.layers.engine.conversation_history import (
    extract_message_text,
    format_history_prompt,
    history_is_synced,
)
from deepticket.layers.engine.stream_reply import ReplyStreamState, consume_stream_content
from deepticket.layers.input.models import AgentInput
from deepticket.layers.output.activity import format_agent_activity
from deepticket.layers.output.models import StreamChunk

logger = logging.getLogger(__name__)

_TERMINAL_STATUSES = frozenset({"finished", "error", "stuck"})


class OpenHandsEngine:
    """引擎层：对接 OpenHands Agent Server（Conversation API + 事件 WebSocket）。"""

    def __init__(
        self,
        config: EngineConfig,
        *,
        llm_model: str,
        llm_api_key: str,
        llm_base_url: str,
        workspace_dir: str | Path,
    ) -> None:
        self.config = config
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key
        self.llm_base_url = llm_base_url
        self.workspace_dir = str(Path(workspace_dir).resolve())
        self._agent_timeout_seconds = config.agent_timeout_seconds
        self._cancel_events: dict[str, asyncio.Event] = {}
        self.server = (
            f"http://{config.agent_server_host}:{config.agent_server_port}"
        )
        self.gateway_model = f"openhands_{config.llm_profile}"
        self._settings_cache_key: tuple[str, str, str, str, str] | None = None
        self._settings_cache_value: dict[str, Any] | None = None

    def _invalidate_settings_cache(self) -> None:
        self._settings_cache_key = None
        self._settings_cache_value = None

    def _settings_cache_identity(
        self,
        *,
        mcp_config: dict[str, Any] | None,
        agents_md: str,
    ) -> tuple[str, str, str, str, str]:
        return (
            json.dumps(mcp_config or {}, sort_keys=True, ensure_ascii=False),
            (agents_md or "").strip(),
            self.llm_model,
            self.llm_api_key,
            self.llm_base_url,
        )

    def _client(self, timeout: float | None = 60.0) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=timeout, trust_env=False)

    def _headers(self, *, stream: bool = False) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.session_api_key:
            headers["X-Session-API-Key"] = self.config.session_api_key
        if stream:
            headers["Accept"] = "text/event-stream"
        return headers

    def _ws_url(self, conversation_id: str) -> str:
        host = self.config.agent_server_host
        port = self.config.agent_server_port
        url = f"ws://{host}:{port}/sockets/events/{conversation_id}"
        if self.config.session_api_key:
            from urllib.parse import urlencode

            url = f"{url}?{urlencode({'session_api_key': self.config.session_api_key})}"
        return url

    @staticmethod
    def _message_content(agent_input: AgentInput) -> list[dict[str, Any]]:
        parts: list[dict[str, Any]] = [
            {"type": "text", "text": agent_input.prompt},
        ]
        for url in agent_input.image_urls:
            parts.append({"type": "image", "image_urls": [url]})
        return parts

    async def cancel_conversation(self, conversation_id: str) -> bool:
        stop = self._cancel_events.get(conversation_id)
        if stop is None:
            return False
        stop.set()
        return True

    def _register_cancel(self, conversation_id: str, stop: asyncio.Event) -> None:
        self._cancel_events[conversation_id] = stop

    def _unregister_cancel(self, conversation_id: str) -> None:
        self._cancel_events.pop(conversation_id, None)

    async def ensure_ready(self, *, max_attempts: int = 60) -> None:
        last_error: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                async with self._client(timeout=10.0) as client:
                    health = await client.get(f"{self.server}/health")
                    health.raise_for_status()
                await self.register_llm_profile()
                return
            except (httpx.HTTPError, RuntimeError) as exc:
                last_error = exc
                if attempt == max_attempts:
                    break
                await asyncio.sleep(1)
        raise RuntimeError(
            f"Agent Server 未就绪 ({self.server}): {last_error}"
        ) from last_error

    async def register_llm_profile(self) -> None:
        if not self.llm_api_key.strip():
            logger.warning("跳过 LLM profile 注册：api_key 未配置")
            return
        await self._register_profile()

    def build_headers(self, *, stream: bool = False) -> dict[str, str]:
        return self._headers(stream=stream)

    async def sync_mcp_config(self, servers: dict[str, dict]) -> None:
        """同步 MCP 到 Agent Server；传空 dict 会清空旧配置。"""
        self._invalidate_settings_cache()
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
        self._invalidate_settings_cache()
        body = {
            "llm": {
                "model": self.llm_model,
                "api_key": self.llm_api_key,
                "base_url": self.llm_base_url,
                "stream": True,
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

    async def _load_agent_settings(
        self,
        client: httpx.AsyncClient,
        *,
        mcp_config: dict[str, Any] | None = None,
        agents_md: str = "",
    ) -> dict[str, Any]:
        resp = await client.get(
            f"{self.server}/api/settings",
            headers=self._headers(),
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"读取 Agent 配置失败: {resp.status_code} {resp.text}"
            )
        data = resp.json()
        agent_settings = copy.deepcopy(data.get("agent_settings") or {})
        llm = dict(agent_settings.get("llm") or {})
        llm.update(
            {
                "model": self.llm_model,
                "api_key": self.llm_api_key,
                "base_url": self.llm_base_url,
                "stream": True,
            }
        )
        agent_settings["llm"] = llm
        if mcp_config is not None:
            agent_settings["mcp_config"] = copy.deepcopy(mcp_config)
        suffix = (agents_md or "").strip()
        if suffix:
            agent_context = dict(agent_settings.get("agent_context") or {})
            existing = str(agent_context.get("system_message_suffix") or "").strip()
            merged = f"{existing}\n\n{suffix}".strip() if existing else suffix
            agent_context["system_message_suffix"] = merged
            agent_settings["agent_context"] = agent_context
        return agent_settings

    async def _load_agent_settings_cached(
        self,
        client: httpx.AsyncClient,
        *,
        mcp_config: dict[str, Any] | None = None,
        agents_md: str = "",
    ) -> dict[str, Any]:
        cache_key = self._settings_cache_identity(
            mcp_config=mcp_config,
            agents_md=agents_md,
        )
        if self._settings_cache_key == cache_key and self._settings_cache_value is not None:
            return copy.deepcopy(self._settings_cache_value)
        settings = await self._load_agent_settings(
            client,
            mcp_config=mcp_config,
            agents_md=agents_md,
        )
        self._settings_cache_key = cache_key
        self._settings_cache_value = settings
        return copy.deepcopy(settings)

    async def _start_conversation(
        self,
        client: httpx.AsyncClient,
        agent_input: AgentInput,
        agent_settings: dict[str, Any],
        *,
        workspace_dir: str | None = None,
    ) -> str:
        working_dir = workspace_dir or agent_input.workspace_dir or self.workspace_dir
        body: dict[str, Any] = {
            "workspace": {"working_dir": working_dir},
            "agent_settings": agent_settings,
            "initial_message": {
                "role": "user",
                "content": self._message_content(agent_input),
                "run": True,
            },
            "autotitle": False,
        }
        if agent_input.conversation_id:
            body["conversation_id"] = agent_input.conversation_id
        resp = await client.post(
            f"{self.server}/api/conversations",
            headers=self._headers(),
            json=body,
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"启动对话失败: {resp.status_code} {resp.text}"
            )
        data = resp.json()
        conversation_id = data.get("id") or data.get("conversation_id")
        if not conversation_id:
            raise RuntimeError("Agent Server 未返回 conversation_id")
        return str(conversation_id)

    async def _create_conversation_shell(
        self,
        client: httpx.AsyncClient,
        agent_settings: dict[str, Any],
        *,
        workspace_dir: str | None = None,
        conversation_id: str | None = None,
    ) -> str:
        working_dir = workspace_dir or self.workspace_dir
        body: dict[str, Any] = {
            "workspace": {"working_dir": working_dir},
            "agent_settings": agent_settings,
            "autotitle": False,
        }
        if conversation_id:
            body["conversation_id"] = conversation_id
        resp = await client.post(
            f"{self.server}/api/conversations",
            headers=self._headers(),
            json=body,
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"创建对话容器失败: {resp.status_code} {resp.text}"
            )
        data = resp.json()
        conv_id = data.get("id") or data.get("conversation_id")
        if not conv_id:
            raise RuntimeError("Agent Server 未返回 conversation_id")
        return str(conv_id)

    async def _list_conversation_messages(
        self,
        client: httpx.AsyncClient,
        conversation_id: str,
    ) -> list[tuple[str, str]]:
        # 勿用 kind=MessageEvent 过滤：空会话会 500，且部分版本过滤结果为空。
        list_client = self._client(timeout=30.0)
        try:
            resp = await list_client.get(
                f"{self.server}/api/conversations/{conversation_id}/events/search",
                headers=self._headers(),
                params={
                    "limit": 200,
                    "sort_order": "TIMESTAMP",
                },
            )
        finally:
            await list_client.aclose()
        if resp.status_code >= 400:
            logger.warning(
                "读取 OpenHands 消息失败: conversation=%s status=%s",
                conversation_id,
                resp.status_code,
            )
            return []
        messages: list[tuple[str, str]] = []
        for event in resp.json().get("items", []):
            if event.get("kind") != "MessageEvent":
                continue
            source = str(event.get("source") or "")
            if source == "user":
                role = "user"
            elif source == "agent":
                role = "assistant"
            else:
                continue
            llm_message = event.get("llm_message") or {}
            text = extract_message_text(llm_message.get("content"))
            if text:
                messages.append((role, text))
        return messages

    async def _post_conversation_message(
        self,
        client: httpx.AsyncClient,
        conversation_id: str,
        *,
        content: str,
        run: bool,
        image_urls: list[str] | None = None,
    ) -> None:
        body: dict[str, Any] = {
            "role": "user",
            "content": [{"type": "text", "text": content}],
            "run": run,
        }
        for url in image_urls or []:
            body["content"].append({"type": "image", "image_urls": [url]})
        resp = await client.post(
            f"{self.server}/api/conversations/{conversation_id}/events",
            headers=self._headers(),
            json=body,
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"写入对话消息失败: {resp.status_code} {resp.text}"
            )

    async def _bootstrap_conversation_with_history(
        self,
        client: httpx.AsyncClient,
        agent_input: AgentInput,
        agent_settings: dict[str, Any],
        history: list[dict[str, str]],
        *,
        workspace_dir: str | None = None,
    ) -> str:
        conv_id = await self._create_conversation_shell(
            client,
            agent_settings,
            workspace_dir=workspace_dir,
        )
        prompt = format_history_prompt(history, agent_input.prompt)
        await self._post_conversation_message(
            client,
            conv_id,
            content=prompt,
            run=True,
            image_urls=agent_input.image_urls,
        )
        logger.info(
            "已用 Redis 历史重建 OpenHands 对话: conversation=%s history_turns=%d",
            conv_id,
            len(history),
        )
        return conv_id

    async def _send_message(
        self,
        client: httpx.AsyncClient,
        conversation_id: str,
        agent_input: AgentInput,
    ) -> None:
        body = {
            "role": "user",
            "content": self._message_content(agent_input),
            "run": True,
        }
        resp = await client.post(
            f"{self.server}/api/conversations/{conversation_id}/events",
            headers=self._headers(),
            json=body,
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"发送消息失败: {resp.status_code} {resp.text}"
            )

    async def _ensure_conversation(
        self,
        client: httpx.AsyncClient,
        agent_input: AgentInput,
        agent_settings: dict[str, Any],
        *,
        workspace_dir: str | None = None,
    ) -> tuple[str, str | None]:
        history = list(agent_input.history_messages or [])
        stored_id = agent_input.conversation_id

        if stored_id:
            probe = await client.get(
                f"{self.server}/api/conversations/{stored_id}",
                headers=self._headers(),
            )
            if probe.status_code == 200:
                if history:
                    openhands_messages = await self._list_conversation_messages(
                        client, stored_id
                    )
                    if history_is_synced(openhands_messages, history):
                        baseline = probe.json().get("leaf_event_id")
                        await self._send_message(client, stored_id, agent_input)
                        return (
                            stored_id,
                            str(baseline) if baseline else None,
                        )
                    logger.warning(
                        "OpenHands 历史与 Redis 不一致，将注入 Redis 上下文后重建: id=%s",
                        stored_id,
                    )
                else:
                    baseline = probe.json().get("leaf_event_id")
                    await self._send_message(client, stored_id, agent_input)
                    return (
                        stored_id,
                        str(baseline) if baseline else None,
                    )
            else:
                logger.warning(
                    "OpenHands conversation 不可用，将重建: id=%s status=%s",
                    stored_id,
                    probe.status_code,
                )

        if history:
            conv_id = await self._bootstrap_conversation_with_history(
                client,
                agent_input,
                agent_settings,
                history,
                workspace_dir=workspace_dir,
            )
            return conv_id, None

        conversation_id = await self._start_conversation(
            client,
            agent_input,
            agent_settings,
            workspace_dir=workspace_dir,
        )
        return conversation_id, None

    async def _fetch_conversation_error(
        self,
        client: httpx.AsyncClient,
        conversation_id: str,
    ) -> str | None:
        resp = await client.get(
            f"{self.server}/api/conversations/{conversation_id}/events/search",
            headers=self._headers(),
            params={"limit": 30, "kind": "ConversationErrorEvent"},
        )
        if resp.status_code >= 400:
            return None
        for event in reversed(resp.json().get("items", [])):
            detail = event.get("detail") or event.get("message")
            code = event.get("code")
            if detail or code:
                return f"{code}: {detail}" if code else str(detail)
        return None

    async def _push_event(
        self,
        event: dict[str, Any],
        *,
        seen_event_ids: set[str],
        out_queue: asyncio.Queue[StreamChunk | None],
        reply_state: ReplyStreamState,
    ) -> None:
        kind = event.get("kind") or ""

        if kind == "StreamingDeltaEvent":
            content = event.get("content")
            if isinstance(content, str):
                delta = consume_stream_content(reply_state, content)
                if delta:
                    await out_queue.put(StreamChunk(delta=delta))
            return

        event_id = event.get("id")
        if event_id:
            if event_id in seen_event_ids:
                return
            seen_event_ids.add(event_id)

        if kind == "ActionEvent" and event.get("source") == "agent":
            reply_state.reset_turn()

        label = format_agent_activity(event)
        if label:
            await out_queue.put(
                StreamChunk(activity=label.text, activity_kind=label.kind)
            )

    async def _subscribe_events_websocket(
        self,
        conversation_id: str,
        *,
        seen_event_ids: set[str],
        out_queue: asyncio.Queue[StreamChunk | None],
        poll_stop: asyncio.Event,
        reply_state: ReplyStreamState,
    ) -> None:
        ws_headers: dict[str, str] = {}
        if self.config.session_api_key:
            ws_headers["X-Session-API-Key"] = self.config.session_api_key
        try:
            async with websockets.connect(
                self._ws_url(conversation_id),
                additional_headers=ws_headers or None,
                open_timeout=10,
            ) as ws:
                while not poll_stop.is_set():
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=0.5)
                    except TimeoutError:
                        continue
                    except websockets.ConnectionClosed:
                        break
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8", errors="replace")
                    try:
                        event = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(event, dict):
                        await self._push_event(
                            event,
                            seen_event_ids=seen_event_ids,
                            out_queue=out_queue,
                            reply_state=reply_state,
                        )
        except Exception:
            await out_queue.put(
                StreamChunk(
                    activity="WebSocket 不可用，已切换 HTTP 轮询模式",
                    activity_kind="system",
                )
            )
            await self._poll_agent_activities(
                conversation_id,
                client=None,
                seen_event_ids=seen_event_ids,
                out_queue=out_queue,
                poll_stop=poll_stop,
                reply_state=reply_state,
            )

    async def _poll_agent_activities(
        self,
        conversation_id: str,
        *,
        client: httpx.AsyncClient | None = None,
        seen_event_ids: set[str],
        out_queue: asyncio.Queue[StreamChunk | None],
        poll_stop: asyncio.Event,
        reply_state: ReplyStreamState,
    ) -> None:
        owns_client = client is None
        if client is None:
            client = self._client(timeout=10.0)
        try:
            while not poll_stop.is_set():
                try:
                    resp = await client.get(
                        f"{self.server}/api/conversations/{conversation_id}/events/search",
                        headers=self._headers(),
                        params={"limit": 80, "sort_order": "TIMESTAMP"},
                    )
                    resp.raise_for_status()
                    items = resp.json().get("items", [])
                    for event in items:
                        await self._push_event(
                            event,
                            seen_event_ids=seen_event_ids,
                            out_queue=out_queue,
                            reply_state=reply_state,
                        )
                except httpx.HTTPError as exc:
                    logger.debug("Agent 活动轮询失败: %s", exc)
                try:
                    await asyncio.wait_for(poll_stop.wait(), timeout=0.35)
                except TimeoutError:
                    continue
        finally:
            if owns_client:
                await client.aclose()

    async def _wait_for_agent_done(
        self,
        client: httpx.AsyncClient,
        conversation_id: str,
        poll_stop: asyncio.Event,
        *,
        baseline_leaf_event_id: str | None = None,
    ) -> str:
        observed_running = False
        deadline = time.monotonic() + self._agent_timeout_seconds
        baseline_leaf = baseline_leaf_event_id
        new_conversation = baseline_leaf is None
        while not poll_stop.is_set():
            resp = await client.get(
                f"{self.server}/api/conversations/{conversation_id}",
                headers=self._headers(),
            )
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"查询对话状态失败: {resp.status_code} {resp.text}"
                )
            data = resp.json()
            status = str(data.get("execution_status", "idle")).lower()
            leaf_event_id = data.get("leaf_event_id")
            progressed = (
                leaf_event_id is not None
                and baseline_leaf is not None
                and str(leaf_event_id) != baseline_leaf
            )
            if status == "running":
                observed_running = True
            turn_done = observed_running or progressed or new_conversation
            if status in _TERMINAL_STATUSES and turn_done:
                if status != "finished":
                    detail = await self._fetch_conversation_error(
                        client, conversation_id
                    )
                    msg = detail or f"Agent 运行异常结束: {status}"
                    raise RuntimeError(msg)
                return status
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    f"Agent 运行超时（{self._agent_timeout_seconds}s）"
                )
            await asyncio.sleep(0.4)

    async def fetch_conversation_token_usage(
        self, conversation_id: str
    ) -> dict[str, int | str] | None:
        """从 Agent Server 读取 OpenHands 累计 token 用量及模型。"""
        async with self._client(timeout=15.0) as client:
            resp = await client.get(
                f"{self.server}/api/conversations/{conversation_id}",
                headers=self._headers(),
            )
            if resp.status_code >= 400:
                logger.warning(
                    "读取 conversation token 失败: id=%s status=%s",
                    conversation_id,
                    resp.status_code,
                )
                return None
            data = resp.json()
        usage_map = (data.get("stats") or {}).get("usage_to_metrics") or {}
        if not usage_map:
            return None
        metrics = next(iter(usage_map.values()), None)
        if not isinstance(metrics, dict):
            return None
        accumulated = metrics.get("accumulated_token_usage") or {}
        prompt = int(accumulated.get("prompt_tokens") or 0)
        completion = int(accumulated.get("completion_tokens") or 0)
        reasoning = int(accumulated.get("reasoning_tokens") or 0)
        model = str(
            metrics.get("model_name")
            or accumulated.get("model")
            or self.llm_model
            or ""
        ).strip()
        return {
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "reasoning_tokens": reasoning,
            "total_tokens": prompt + completion + reasoning,
            "model": model,
        }

    async def _fetch_final_response(
        self,
        client: httpx.AsyncClient,
        conversation_id: str,
    ) -> str:
        resp = await client.get(
            f"{self.server}/api/conversations/{conversation_id}/agent_final_response",
            headers=self._headers(),
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"获取 Agent 回复失败: {resp.status_code} {resp.text}"
            )
        text = resp.json().get("response")
        return text if isinstance(text, str) else ""

    @staticmethod
    async def _stream_text_deltas(
        text: str,
        out_queue: asyncio.Queue[StreamChunk | None],
        *,
        paced: bool = True,
    ) -> None:
        if not text:
            return
        step = 10 if paced else 48
        for idx, start in enumerate(range(0, len(text), step)):
            await out_queue.put(StreamChunk(delta=text[start : start + step]))
            if paced and idx % 3 == 2:
                await asyncio.sleep(0.016)
            else:
                await asyncio.sleep(0)

    @staticmethod
    async def _emit_final_reply(
        final_text: str,
        reply_state: ReplyStreamState,
        out_queue: asyncio.Queue[StreamChunk | None],
    ) -> None:
        if not final_text.strip():
            return
        if reply_state.delta_count == 0:
            await OpenHandsEngine._stream_text_deltas(final_text, out_queue)
            return
        if final_text.startswith(reply_state.emitted):
            remainder = final_text[len(reply_state.emitted) :]
            if remainder:
                await OpenHandsEngine._stream_text_deltas(
                    remainder, out_queue, paced=False
                )
            return
        if len(final_text) > len(reply_state.emitted):
            await OpenHandsEngine._stream_text_deltas(final_text, out_queue)

    async def stream(self, agent_input: AgentInput) -> AsyncIterator[StreamChunk]:
        out_queue: asyncio.Queue[StreamChunk | None] = asyncio.Queue()
        poll_stop = asyncio.Event()
        seen_event_ids: set[str] = set()
        reply_state = ReplyStreamState()

        errors: list[BaseException] = []

        async def run_agent() -> None:
            client = self._client(timeout=None)
            ws_task: asyncio.Task[None] | None = None
            conversation_id: str | None = None
            try:
                await out_queue.put(
                    StreamChunk(activity="正在连接 Agent…", activity_kind="system")
                )
                agent_settings = await self._load_agent_settings_cached(
                    client,
                    mcp_config=agent_input.mcp_config,
                    agents_md=agent_input.agents_md,
                )
                workspace_dir = agent_input.workspace_dir or self.workspace_dir
                conversation_id, baseline_leaf_event_id = (
                    await self._ensure_conversation(
                        client,
                        agent_input,
                        agent_settings,
                        workspace_dir=workspace_dir,
                    )
                )
                self._register_cancel(conversation_id, poll_stop)
                await out_queue.put(StreamChunk(conversation_id=conversation_id))
                await out_queue.put(
                    StreamChunk(
                        activity="Agent 已就绪，开始分析…",
                        activity_kind="system",
                    )
                )
                ws_task = asyncio.create_task(
                    self._subscribe_events_websocket(
                        conversation_id,
                        seen_event_ids=seen_event_ids,
                        out_queue=out_queue,
                        poll_stop=poll_stop,
                        reply_state=reply_state,
                    )
                )
                await self._wait_for_agent_done(
                    client,
                    conversation_id,
                    poll_stop,
                    baseline_leaf_event_id=(
                        str(baseline_leaf_event_id)
                        if baseline_leaf_event_id
                        else None
                    ),
                )
                poll_stop.set()
                if ws_task is not None:
                    try:
                        await asyncio.wait_for(ws_task, timeout=1.0)
                    except TimeoutError:
                        ws_task.cancel()
                final_text = await self._fetch_final_response(client, conversation_id)
                if not final_text.strip() and reply_state.delta_count == 0:
                    detail = await self._fetch_conversation_error(
                        client, conversation_id
                    )
                    if detail:
                        raise RuntimeError(detail)
                await self._emit_final_reply(final_text, reply_state, out_queue)
            except httpx.HTTPError as exc:
                errors.append(RuntimeError(f"Agent Server 请求失败: {exc}"))
            except BaseException as exc:
                errors.append(exc)
            finally:
                poll_stop.set()
                if ws_task is not None and not ws_task.done():
                    ws_task.cancel()
                if conversation_id:
                    self._unregister_cancel(conversation_id)
                await client.aclose()
                if errors:
                    await out_queue.put(
                        StreamChunk(
                            activity=str(errors[-1]),
                            activity_kind="error",
                        )
                    )
                await out_queue.put(None)

        worker = asyncio.create_task(run_agent())
        try:
            while True:
                item = await out_queue.get()
                if item is None:
                    break
                yield item
            if errors:
                raise errors[0]
        finally:
            poll_stop.set()
            if not worker.done():
                worker.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await worker
