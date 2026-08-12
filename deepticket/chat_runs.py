from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

import httpx

from deepticket.layers.input.models import AgentInput, ChatInput
from deepticket.layers.output.confidence import compute_confidence
from deepticket.layers.output.models import StreamChunk
from deepticket.projects.registry import ProjectContext

logger = logging.getLogger(__name__)

_SENTINEL = object()


@dataclass
class _ChatRun:
    project_id: str
    uid: str
    chat_id: str
    agent_conversation_id: str | None = None
    subscribers: list[asyncio.Queue] = field(default_factory=list)
    task: asyncio.Task | None = None
    cancel_requested: bool = False
    done: bool = False


class ChatRunManager:
    """后台执行 Agent；SSE 仅订阅进度，客户端断连不终止任务。"""

    def __init__(self, service: object) -> None:
        self._service = service
        self._runs: dict[str, _ChatRun] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _key(project_id: str, uid: str, chat_id: str) -> str:
        return f"{project_id}:{uid}:{chat_id}"

    async def start(
        self,
        *,
        project: ProjectContext,
        uid: str,
        chat_id: str,
        payload: ChatInput,
        agent_input: AgentInput,
    ) -> _ChatRun:
        key = self._key(project.project_id, uid, chat_id)
        async with self._lock:
            existing = self._runs.get(key)
            if existing is not None and not existing.done:
                raise RuntimeError("该对话已有进行中的 Agent 任务，请稍候")

            run = _ChatRun(
                project_id=project.project_id,
                uid=uid,
                chat_id=chat_id,
                agent_conversation_id=agent_input.conversation_id,
            )
            self._runs[key] = run

        run.task = asyncio.create_task(
            self._execute(run, project=project, payload=payload, agent_input=agent_input),
            name=f"chat-run:{chat_id}",
        )
        return run

    async def subscribe(self, run: _ChatRun) -> AsyncIterator[StreamChunk]:
        queue: asyncio.Queue = asyncio.Queue(maxsize=512)
        run.subscribers.append(queue)
        try:
            while True:
                item = await queue.get()
                if item is _SENTINEL:
                    break
                assert isinstance(item, StreamChunk)
                yield item
        finally:
            if queue in run.subscribers:
                run.subscribers.remove(queue)

    def is_running(self, project_id: str, uid: str, chat_id: str) -> bool:
        run = self._runs.get(self._key(project_id, uid, chat_id))
        return run is not None and not run.done

    async def cancel_chat(
        self,
        *,
        project_id: str,
        uid: str,
        chat_id: str,
        conversation_id: str | None = None,
    ) -> bool:
        key = self._key(project_id, uid, chat_id)
        run = self._runs.get(key)
        if run is None or run.done:
            conv_id = conversation_id or (run.agent_conversation_id if run else None)
            if conv_id:
                return await self._service.engine.cancel_conversation(conv_id)
            return False

        run.cancel_requested = True
        conv_id = conversation_id or run.agent_conversation_id
        if conv_id:
            await self._service.engine.cancel_conversation(conv_id)
        if run.task is not None and not run.task.done():
            run.task.cancel()
        return True

    async def _execute(
        self,
        run: _ChatRun,
        *,
        project: ProjectContext,
        payload: ChatInput,
        agent_input: AgentInput,
    ) -> None:
        service = self._service
        project_id = run.project_id
        uid = run.uid
        chat_id = run.chat_id

        assistant_parts: list[str] = []
        activity_log: list[dict[str, str]] = []
        agent_conversation_id = agent_input.conversation_id
        confidence: dict | None = None

        try:
            service.chat_history.set_agent_run_status(
                project_id, uid, chat_id, status="running"
            )
            async for chunk in service._run_stream(agent_input):
                if run.cancel_requested:
                    break
                if chunk.conversation_id:
                    agent_conversation_id = chunk.conversation_id
                    run.agent_conversation_id = agent_conversation_id
                if chunk.activity:
                    activity_log.append(
                        {
                            "text": chunk.activity,
                            "kind": chunk.activity_kind or "default",
                        }
                    )
                if chunk.delta:
                    assistant_parts.append(chunk.delta)
                await self._broadcast(run, chunk)

            if run.cancel_requested:
                service.chat_history.set_agent_run_status(
                    project_id, uid, chat_id, status="idle"
                )
                return

            reply_text = "".join(assistant_parts)
            confidence = compute_confidence(
                activities=activity_log,
                reply=reply_text,
                ok=True,
                require_analysis=True,
            )
            if confidence:
                await self._broadcast(run, StreamChunk(confidence=confidence))

            if assistant_parts:
                service.chat_history.append_message(
                    project_id,
                    uid,
                    chat_id,
                    role="assistant",
                    content=reply_text,
                    agent_conversation_id=agent_conversation_id,
                    activities=activity_log or None,
                    confidence=confidence if confidence else None,
                )
            elif agent_conversation_id:
                service.chat_history.set_agent_conversation_id(
                    project_id, uid, chat_id, agent_conversation_id
                )

            if agent_conversation_id:
                try:
                    await service.record_chat_token_usage(
                        project_id=project_id,
                        uid=uid,
                        chat_id=chat_id,
                        agent_conversation_id=agent_conversation_id,
                    )
                except httpx.HTTPError as exc:
                    logger.warning("记录 token 用量失败: %s", exc)
                except RuntimeError as exc:
                    logger.warning("记录 token 用量失败: %s", exc)

            service.chat_history.set_agent_run_status(
                project_id, uid, chat_id, status="idle"
            )
        except asyncio.CancelledError:
            service.chat_history.set_agent_run_status(
                project_id, uid, chat_id, status="idle"
            )
            raise
        except Exception as exc:
            logger.exception("Chat run failed: %s", exc)
            service.chat_history.set_agent_run_status(
                project_id,
                uid,
                chat_id,
                status="failed",
                error=str(exc),
            )
            await self._broadcast(
                run,
                StreamChunk(activity=str(exc), activity_kind="error"),
            )
        finally:
            run.done = True
            await self._broadcast_sentinel(run)
            async with self._lock:
                self._runs.pop(
                    self._key(project_id, uid, chat_id),
                    None,
                )

    async def _broadcast(self, run: _ChatRun, chunk: StreamChunk) -> None:
        for queue in list(run.subscribers):
            try:
                queue.put_nowait(chunk)
            except asyncio.QueueFull:
                logger.debug("chat run subscriber queue full, dropping chunk")

    async def _broadcast_sentinel(self, run: _ChatRun) -> None:
        for queue in list(run.subscribers):
            try:
                queue.put_nowait(_SENTINEL)
            except asyncio.QueueFull:
                pass
