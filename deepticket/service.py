
from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from dataclasses import asdict
from pathlib import Path

from deepticket.auth.user_store import UserStore
from deepticket.config.mcp_loader import filter_enabled_servers, validate_mcp_servers
from deepticket.config.routing_schema import RoutingConfig
from deepticket.config.schema import AppConfig
from deepticket.layers.engine.openhands_engine import OpenHandsEngine
from deepticket.layers.ingress.pipeline import IngressJobResult, collect_stream_text
from deepticket.layers.input.adapter import InputAdapter
from deepticket.layers.input.classifier import classify_ingress_event
from deepticket.layers.input.ingress_adapter import IngressAdapter
from deepticket.layers.input.ingress_models import IngressEvent
from deepticket.layers.input.models import AgentInput, ChatInput, TicketInput
from deepticket.layers.knowledge.manager import GitSyncResult, KnowledgeManager
from deepticket.layers.knowledge.skill_manager import SkillInfo, SkillManager
from deepticket.layers.output.models import StreamChunk
from deepticket.layers.output.outbound.registry import get_outbound_handler
from deepticket.layers.output.outbound_models import OutboundPayload
from deepticket.config.redis_url import redact_redis_url, resolve_redis_url
from deepticket.layers.storage import create_storage
from deepticket.layers.storage.base import StorageBackend
from deepticket.layers.storage.chat_history import ChatHistoryStore
from deepticket.paths import resolve_from_project

logger = logging.getLogger(__name__)


class DeepTicketService:
    """五层编排：输入 → 知识/存储 → 引擎 → 输出。"""

    NAMESPACE_CONVERSATION = "conversations"
    NAMESPACE_TICKET = "tickets"
    NAMESPACE_INGRESS = "ingress_jobs"

    def __init__(
        self,
        config: AppConfig,
        *,
        llm_model: str,
        llm_api_key: str,
        llm_base_url: str,
        llm_label: str,
    ) -> None:
        self.config = config
        self.llm_label = llm_label
        self.storage: StorageBackend = create_storage(config.storage)
        self.users = UserStore(self.storage)
        self.chat_history = ChatHistoryStore(self.storage)
        self.knowledge = KnowledgeManager(config.knowledge)
        self.skills = SkillManager(
            skills_dir=self._resolve_path(config.extensions.skills_dir),
            user_skills_dir=(
                self._resolve_path(config.extensions.user_skills_dir)
                if config.extensions.user_skills_dir
                else None
            ),
            workspace_skills_dir=self._resolve_path(
                config.extensions.workspace_skills_dir
            ),
        )
        self.engine = OpenHandsEngine(
            config.engine,
            llm_model=llm_model,
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
        )
        self.routing = RoutingConfig(routes=list(config.ingress.routes))

    @staticmethod
    def _resolve_path(raw: str) -> Path:
        return resolve_from_project(raw)

    async def startup(self) -> None:
        bootstrap = self.users.ensure_bootstrap_user("admin", "admin")
        if bootstrap:
            logger.info("已创建默认账户: admin / admin")

        await self.engine.ensure_ready()
        try:
            published = self.skills.publish_to_workspace()
            if published:
                logger.info("Skills 已发布: %s", ", ".join(published))
        except OSError as exc:
            logger.error("Skill 发布失败（服务仍启动）: %s", exc)

        try:
            servers = filter_enabled_servers(self.config.mcp.servers)
            errors = validate_mcp_servers(servers)
            if errors:
                raise ValueError("MCP 配置无效: " + "; ".join(errors))
            await self.engine.sync_mcp_config(servers)
            if servers:
                logger.info("MCP 已同步: %s", ", ".join(servers.keys()))
            else:
                logger.info("MCP 无启用项，已清空 Agent Server 中的 MCP 配置")
        except (OSError, ValueError, RuntimeError) as exc:
            logger.error("MCP 同步失败（服务仍启动）: %s", exc)

        if not self.config.knowledge.repos:
            return
        try:
            self.knowledge.sync_all()
        except RuntimeError as exc:
            logger.error("知识层 Git 同步失败（服务仍启动）: %s", exc)

    def list_git_repos(self) -> list[dict[str, str]]:
        return self.knowledge.list_repos()

    def list_skills(self) -> list[SkillInfo]:
        return self.skills.list_skills()

    def reload_skills(self) -> list[str]:
        return self.skills.publish_to_workspace()

    def sync_knowledge(self) -> list[GitSyncResult]:
        return self.knowledge.sync_all()

    def list_routes(self) -> list[dict[str, str]]:
        return [
            {
                "type": route.type,
                "description": route.description,
                "outbound_method": route.outbound.method,
            }
            for route in self.routing.routes
        ]

    def get_ingress_job(self, job_id: str) -> dict | None:
        return self.storage.get_json(self.NAMESPACE_INGRESS, job_id)

    async def run_ingress_event(self, event: IngressEvent) -> IngressJobResult:
        """外部事件：分类 → Agent 分析 → 按类型出口投递。"""
        route = classify_ingress_event(event, self.routing)
        logger.info(
            "Ingress 收到事件: source=%s external_id=%s route=%s",
            event.source,
            event.external_id,
            route.type,
        )
        ticket = IngressAdapter.to_ticket(event, route)
        job_id = uuid.uuid4().hex

        running_doc = {
            "job_id": job_id,
            "route_type": route.type,
            "source": event.source,
            "external_id": event.external_id,
            "status": "running",
            "metadata": ticket.metadata,
        }
        self.storage.set_json(self.NAMESPACE_INGRESS, job_id, running_doc)

        reply = ""
        conversation_id: str | None = None
        error: str | None = None
        status = "finished"

        try:
            reply, conversation_id = await collect_stream_text(
                self.run_ticket_stream(ticket)
            )
        except RuntimeError as exc:
            status = "failed"
            error = str(exc)
            logger.error("Ingress 任务 Agent 失败 (%s): %s", job_id, exc)

        outbound_payload = OutboundPayload(
            job_id=job_id,
            route_type=route.type,
            source=event.source,
            external_id=event.external_id,
            status=status,
            reply=reply,
            conversation_id=conversation_id,
            error=error,
            metadata=ticket.metadata,
        )
        handler = get_outbound_handler(route.outbound.method)
        outbound_result = await handler.deliver(outbound_payload, route.outbound)
        logger.info(
            "Ingress 任务完成: job_id=%s status=%s outbound=%s ok=%s detail=%s",
            job_id,
            status,
            route.outbound.method,
            outbound_result.ok,
            outbound_result.detail,
        )

        result = IngressJobResult(
            job_id=job_id,
            route_type=route.type,
            source=event.source,
            external_id=event.external_id,
            status=status,
            reply=reply,
            conversation_id=conversation_id,
            outbound_method=route.outbound.method,
            outbound_ok=outbound_result.ok,
            outbound_detail=outbound_result.detail,
            metadata={
                **ticket.metadata,
                "outbound_response_status": outbound_result.response_status,
                "error": error,
            },
        )
        self.storage.set_json(self.NAMESPACE_INGRESS, job_id, asdict(result))
        return result

    async def run_chat_stream(
        self,
        payload: ChatInput,
        *,
        uid: str | None = None,
        chat_id: str | None = None,
    ) -> AsyncIterator[StreamChunk]:
        agent_input = InputAdapter.from_chat(payload)

        if uid and chat_id:
            thread = self.chat_history.get_thread(uid, chat_id)
            if thread is None:
                raise RuntimeError(f"聊天不存在: {chat_id}")
            if thread.get("agent_conversation_id") and not agent_input.conversation_id:
                agent_input.conversation_id = thread["agent_conversation_id"]
            self.chat_history.append_message(
                uid, chat_id, role="user", content=payload.message.strip()
            )

        assistant_parts: list[str] = []
        agent_conversation_id = agent_input.conversation_id
        async for chunk in self._run_stream(agent_input):
            if chunk.conversation_id:
                agent_conversation_id = chunk.conversation_id
            if chunk.delta:
                assistant_parts.append(chunk.delta)
            yield chunk

        if uid and chat_id:
            if assistant_parts:
                self.chat_history.append_message(
                    uid,
                    chat_id,
                    role="assistant",
                    content="".join(assistant_parts),
                    agent_conversation_id=agent_conversation_id,
                )
            elif agent_conversation_id:
                self.chat_history.set_agent_conversation_id(
                    uid, chat_id, agent_conversation_id
                )

    async def run_ticket_stream(self, payload: TicketInput) -> AsyncIterator[StreamChunk]:
        agent_input = InputAdapter.from_ticket(payload)
        self.storage.set_json(
            self.NAMESPACE_TICKET,
            payload.ticket_id,
            {
                "ticket_id": payload.ticket_id,
                "title": payload.title,
                "status": "running",
                "repo_ids": payload.repo_ids,
            },
        )
        async for chunk in self._run_stream(agent_input):
            yield chunk

    async def _run_stream(self, agent_input: AgentInput) -> AsyncIterator[StreamChunk]:
        conversation_id = agent_input.conversation_id
        text_parts: list[str] = []

        async for chunk in self.engine.stream(agent_input):
            if chunk.conversation_id and not conversation_id:
                conversation_id = chunk.conversation_id
            if chunk.delta:
                text_parts.append(chunk.delta)
            yield chunk

        if conversation_id:
            self.storage.set_json(
                self.NAMESPACE_CONVERSATION,
                conversation_id,
                {
                    "conversation_id": conversation_id,
                    "source": agent_input.source,
                    "ticket_id": agent_input.ticket_id,
                    "last_reply": "".join(text_parts),
                },
            )
        if agent_input.ticket_id:
            existing = self.storage.get_json(
                self.NAMESPACE_TICKET,
                agent_input.ticket_id,
            ) or {"ticket_id": agent_input.ticket_id}
            existing["status"] = "finished"
            existing["conversation_id"] = conversation_id
            existing["reply"] = "".join(text_parts)
            self.storage.set_json(
                self.NAMESPACE_TICKET,
                agent_input.ticket_id,
                existing,
            )

    def get_storage_info(self) -> dict[str, str | list[str]]:
        backend = self.config.storage.backend
        info: dict[str, str | list[str]] = {
            "backend": backend,
            "conversation_keys": self.storage.list_keys(self.NAMESPACE_CONVERSATION),
            "ticket_keys": self.storage.list_keys(self.NAMESPACE_TICKET),
        }
        if backend == "local":
            info["local_root"] = self.config.storage.local.root
        else:
            redis_cfg = self.config.storage.redis
            info["redis_url"] = redact_redis_url(
                resolve_redis_url(
                    redis_cfg.url,
                    username=redis_cfg.username,
                    password=redis_cfg.password,
                )
            )
            info["redis_prefix"] = redis_cfg.key_prefix
        return info

    def get_extensions_info(self) -> dict[str, object]:
        mcp_servers = filter_enabled_servers(self.config.mcp.servers)
        return {
            "skills_dir": str(self._resolve_path(self.config.extensions.skills_dir)),
            "user_skills_dir": self.config.extensions.user_skills_dir or None,
            "workspace_skills_dir": str(
                self._resolve_path(self.config.extensions.workspace_skills_dir)
            ),
            "mcp_servers": sorted(mcp_servers.keys()),
            "mcp_configured": bool(mcp_servers),
            "skills": [
                {"name": s.name, "source": s.source, "path": s.path}
                for s in self.list_skills()
            ],
        }
