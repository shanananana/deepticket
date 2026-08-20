from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from deepticket.layers.input.adapter import InputAdapter
from deepticket.layers.input.image_urls import inline_local_upload_images
from deepticket.layers.input.models import AgentInput, ChatInput, TicketInput
from deepticket.layers.output.confidence import compute_confidence
from deepticket.layers.output.models import StreamChunk
from deepticket.layers.storage.json_index import count_indexed_keys, index_json_key
from deepticket.observability.metrics import get_metrics
from deepticket.paths import PROJECT_ROOT
from deepticket.projects.registry import ProjectContext
from deepticket.utils.time import utc_now_iso

if TYPE_CHECKING:
    from deepticket.service import DeepTicketService

logger = logging.getLogger(__name__)
_metrics = get_metrics()


class ChatOrchestrator:
    """聊天 / 工单 Agent 流编排。"""

    NAMESPACE_CONVERSATION = "conversations"
    NAMESPACE_TICKET = "tickets"

    def __init__(self, service: DeepTicketService) -> None:
        self._service = service

    def apply_project_runtime(
        self, agent_input: AgentInput, project: ProjectContext
    ) -> None:
        runtime = project.runtime()
        agent_input.workspace_dir = str(runtime.workspace_dir)
        agent_input.mcp_config = runtime.mcp_servers
        agent_input.agents_md = runtime.agents_md
        self._service.projects.ensure_skills_published(project)

    def resolve_agent_image_urls(self, urls: list[str]) -> list[str]:
        return inline_local_upload_images(
            urls,
            uploads_dir=PROJECT_ROOT / "data" / "uploads" / "images",
        )

    async def run_chat_stream(
        self,
        payload: ChatInput,
        *,
        project: ProjectContext,
        uid: str | None = None,
        chat_id: str | None = None,
    ) -> AsyncIterator[StreamChunk]:
        self._service.require_llm_configured()
        if not uid or not chat_id:
            agent_input = InputAdapter.from_chat(payload)
            agent_input.image_urls = self.resolve_agent_image_urls(
                agent_input.image_urls
            )
            self.apply_project_runtime(agent_input, project)
            async for chunk in self._run_stream(agent_input):
                yield chunk
            return

        agent_input = InputAdapter.from_chat(payload)
        stored_image_urls = list(agent_input.image_urls)
        agent_input.image_urls = self.resolve_agent_image_urls(stored_image_urls)
        self.apply_project_runtime(agent_input, project)

        thread = self._service.chat_history.get_thread_summary(
            project.project_id, uid, chat_id
        )
        if thread is None:
            raise RuntimeError(f"聊天不存在: {chat_id}")
        if thread.get("agent_conversation_id") and not agent_input.conversation_id:
            agent_input.conversation_id = thread["agent_conversation_id"]

        self._service.chat_history.append_message(
            project.project_id,
            uid,
            chat_id,
            role="user",
            content=payload.message.strip(),
            image_urls=stored_image_urls or None,
        )

        run = await self._service.chat_runs.start(
            project=project,
            uid=uid,
            chat_id=chat_id,
            payload=payload,
            agent_input=agent_input,
        )
        try:
            async for chunk in self._service.chat_runs.subscribe(run):
                yield chunk
        except asyncio.CancelledError:
            return

    async def run_ticket_stream(
        self, payload: TicketInput, *, project: ProjectContext
    ) -> AsyncIterator[StreamChunk]:
        self._service.require_llm_configured()
        agent_input = InputAdapter.from_ticket(payload)
        self.apply_project_runtime(agent_input, project)
        self._service.storage.set_json(
            self.NAMESPACE_TICKET,
            payload.ticket_id,
            {
                "ticket_id": payload.ticket_id,
                "title": payload.title,
                "status": "running",
                "repo_ids": payload.repo_ids,
            },
        )
        assistant_parts: list[str] = []
        activity_log: list[dict[str, str]] = []
        async for chunk in self._run_stream(agent_input):
            if chunk.activity:
                activity_log.append(
                    {
                        "text": chunk.activity,
                        "kind": chunk.activity_kind or "default",
                    }
                )
            if chunk.delta:
                assistant_parts.append(chunk.delta)
            yield chunk
        yield StreamChunk(
            confidence=compute_confidence(
                activities=activity_log,
                reply="".join(assistant_parts),
                ok=True,
            )
        )

    async def _run_stream(self, agent_input: AgentInput) -> AsyncIterator[StreamChunk]:
        conversation_id = agent_input.conversation_id
        text_parts: list[str] = []
        started = time.monotonic()
        ok = True
        _metrics.agent_run_started()
        try:
            async for chunk in self._service.engine.stream(agent_input):
                if chunk.conversation_id and not conversation_id:
                    conversation_id = chunk.conversation_id
                if chunk.delta:
                    text_parts.append(chunk.delta)
                yield chunk
        except Exception:
            ok = False
            raise
        finally:
            duration_ms = int((time.monotonic() - started) * 1000)
            _metrics.agent_run_finished(
                duration_ms=duration_ms,
                ok=ok,
                tokens_estimated=0,
            )

        if conversation_id:
            doc = {
                "conversation_id": conversation_id,
                "source": agent_input.source,
                "ticket_id": agent_input.ticket_id,
                "last_reply": "".join(text_parts),
                "updated_at": utc_now_iso(),
            }
            self._service.storage.set_json(
                self.NAMESPACE_CONVERSATION,
                conversation_id,
                doc,
            )
            index_json_key(
                self._service.storage,
                self.NAMESPACE_CONVERSATION,
                conversation_id,
                sort_field="updated_at",
                doc=doc,
            )
        if agent_input.ticket_id:
            existing = self._service.storage.get_json(
                self.NAMESPACE_TICKET,
                agent_input.ticket_id,
            ) or {"ticket_id": agent_input.ticket_id}
            existing["status"] = "finished"
            existing["conversation_id"] = conversation_id
            existing["reply"] = "".join(text_parts)
            existing["updated_at"] = utc_now_iso()
            self._service.storage.set_json(
                self.NAMESPACE_TICKET,
                agent_input.ticket_id,
                existing,
            )
            index_json_key(
                self._service.storage,
                self.NAMESPACE_TICKET,
                agent_input.ticket_id,
                sort_field="updated_at",
                doc=existing,
            )

    def conversation_count(self) -> int:
        return count_indexed_keys(self._service.storage, self.NAMESPACE_CONVERSATION)

    def ticket_count(self) -> int:
        return count_indexed_keys(self._service.storage, self.NAMESPACE_TICKET)
