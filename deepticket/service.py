
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import AsyncIterator
import httpx
from dataclasses import asdict
from pathlib import Path

from deepticket.auth.user_store import AuthUser, UserStore
from deepticket.chat_runs import ChatRunManager
from deepticket.config.mcp_loader import filter_enabled_servers, validate_mcp_servers
from deepticket.config.routing_schema import RoutingConfig
from deepticket.config.schema import AppConfig
from deepticket.layers.engine.openhands_engine import OpenHandsEngine
from deepticket.layers.ingress.pipeline import IngressJobResult, collect_stream_text
from deepticket.layers.ingress.queue import IngressJobQueue, IngressQueueItem
from deepticket.layers.input.adapter import InputAdapter
from deepticket.layers.input.image_urls import inline_local_upload_images
from deepticket.layers.input.classifier import classify_ingress_event
from deepticket.layers.input.ingress_adapter import IngressAdapter
from deepticket.layers.input.ingress_models import IngressEvent
from deepticket.layers.input.models import AgentInput, ChatInput, TicketInput
from deepticket.layers.knowledge.manager import GitSyncResult, KnowledgeManager
from deepticket.layers.knowledge.skill_manager import SkillInfo, SkillManager
from deepticket.layers.output.confidence import compute_confidence
from deepticket.layers.output.models import StreamChunk
from deepticket.layers.output.outbound.registry import get_outbound_handler
from deepticket.layers.output.outbound_models import OutboundPayload
from deepticket.config.redis_url import redact_redis_url, resolve_redis_url
from deepticket.layers.storage import create_storage
from deepticket.layers.storage.base import StorageBackend
from deepticket.layers.storage.chat_history import ChatHistoryStore
from deepticket.layers.storage.token_usage import TokenUsageStore
from deepticket.observability.metrics import get_metrics
from deepticket.paths import PROJECT_ROOT, resolve_from_project
from deepticket.projects.registry import ProjectContext, ProjectRegistry

logger = logging.getLogger(__name__)
_metrics = get_metrics()


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
        self.token_usage = TokenUsageStore(self.storage)
        self.projects = ProjectRegistry(self.storage, config, resolve_path=self._resolve_path)
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
            workspace_dir=self._resolve_path(config.knowledge.workspace_dir),
        )
        self.routing = RoutingConfig(routes=list(config.ingress.routes))
        self._ingress_queue = IngressJobQueue(workers=config.ingress.queue_workers)
        _metrics.queue_backlog_alert = config.ingress.queue_backlog_alert
        self.chat_runs = ChatRunManager(self)

    def _resolve_agent_image_urls(self, urls: list[str]) -> list[str]:
        return inline_local_upload_images(
            urls,
            uploads_dir=PROJECT_ROOT / "data" / "uploads" / "images",
        )

    @staticmethod
    def _resolve_path(raw: str) -> Path:
        return resolve_from_project(raw)

    def is_llm_configured(self) -> bool:
        return bool(self.engine.llm_api_key.strip())

    def require_llm_configured(self) -> None:
        if not self.is_llm_configured():
            raise RuntimeError(
                "LLM 未配置：请管理员在工作台侧栏「LLM 配置」填写 API Key"
            )

    async def apply_llm_config(self, llm: LlmConfig) -> None:
        self.llm_label = llm.label
        self.engine.llm_model = llm.model
        self.engine.llm_api_key = llm.api_key
        self.engine.llm_base_url = llm.base_url
        self.config = self.config.model_copy(
            update={
                "llm": self.config.llm.model_copy(
                    update={
                        "model": llm.model,
                        "api_key": llm.api_key,
                        "base_url": llm.base_url,
                        "label": llm.label,
                    }
                )
            }
        )
        await self.engine.register_llm_profile()

    async def startup(self) -> None:
        bootstrap_user = self.users.ensure_bootstrap_user(
            self.config.auth.bootstrap_username,
            self.config.auth.bootstrap_password,
        )
        if bootstrap_user is not None:
            doc = self.storage.get_json("users", bootstrap_user.uid) or {}
            if doc.get("bootstrap"):
                logger.info(
                    "已创建默认账户: %s（请尽快修改密码）",
                    self.config.auth.bootstrap_username,
                )
            self.projects.bootstrap(
                bootstrap_uid=bootstrap_user.uid,
                bootstrap_username=bootstrap_user.username,
            )
        else:
            self.projects.config_store.ensure_default_project()

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
            await self.engine.  sync_mcp_config(servers)
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

    def is_admin(self, user: AuthUser) -> bool:
        admins = self.config.auth.admin_usernames
        if not admins:
            admins = [self.config.auth.bootstrap_username]
        return user.username.lower() in {name.lower() for name in admins}

    def grant_default_project(self, user: AuthUser) -> None:
        self.projects.permissions.ensure_default_access(user.uid, user.username)

    def list_user_projects(self, user: AuthUser) -> list[dict[str, object]]:
        summaries = self.projects.list_summaries_for_user(
            user.uid, is_admin=self.is_admin(user)
        )
        return [item.model_dump() for item in summaries]

    def apply_project_runtime(
        self, agent_input: AgentInput, project: ProjectContext
    ) -> None:
        runtime = project.runtime()
        agent_input.workspace_dir = str(runtime.workspace_dir)
        agent_input.mcp_config = runtime.mcp_servers
        agent_input.agents_md = runtime.agents_md
        try:
            published = project.publish_skills()
            if published:
                logger.info(
                    "项目 %s Skills 已发布: %s",
                    project.project_id,
                    ", ".join(published),
                )
        except OSError as exc:
            logger.warning("项目 %s Skill 发布失败: %s", project.project_id, exc)

    def list_project_git_repos(self, project: ProjectContext) -> list[dict[str, str]]:
        return project.list_repos()

    def sync_project_knowledge(self, project: ProjectContext) -> list[GitSyncResult]:
        return project.sync_knowledge()

    def reload_project_skills(self, project: ProjectContext) -> list[str]:
        return project.publish_skills()

    def list_project_skills(self, project: ProjectContext) -> list[SkillInfo]:
        return project.list_skills()

    def list_recent_ingress_jobs(self, *, limit: int = 20) -> list[dict]:
        keys = self.storage.list_keys(self.NAMESPACE_INGRESS)
        jobs: list[dict] = []
        for key in keys:
            doc = self.storage.get_json(self.NAMESPACE_INGRESS, key)
            if not doc:
                continue
            jobs.append(
                {
                    "job_id": doc.get("job_id", key),
                    "status": doc.get("status", "unknown"),
                    "source": doc.get("source", ""),
                    "external_id": doc.get("external_id", ""),
                    "route_type": doc.get("route_type", ""),
                    "outbound_method": doc.get("outbound_method", ""),
                    "outbound_ok": doc.get("outbound_ok"),
                    "outbound_detail": (doc.get("outbound_detail") or "")[:120],
                }
            )
        jobs.sort(key=lambda item: item["job_id"], reverse=True)
        return jobs[:limit]

    def list_admin_token_usage(self, *, run_limit: int = 50) -> dict:
        def resolve_username(uid: str) -> str | None:
            user = self.users.get_user(uid)
            return user.username if user else None

        conversations = self.token_usage.list_conversation_usage(
            resolve_username=resolve_username
        )
        runs = self.token_usage.list_recent_runs(limit=run_limit)
        return {
            "summary": self.token_usage.summarize_conversations(conversations),
            "conversations": conversations,
            "runs": runs,
        }

    async def record_chat_token_usage(
        self,
        *,
        project_id: str,
        uid: str,
        chat_id: str,
        agent_conversation_id: str,
    ) -> None:
        usage = await self.engine.fetch_conversation_token_usage(agent_conversation_id)
        if not usage:
            return

        thread = self.chat_history.get_thread_summary(project_id, uid, chat_id)
        if thread is None:
            return

        user = self.users.get_user(uid)
        username = user.username if user else uid[:8]
        model = str(usage.get("model") or self.engine.llm_model or "").strip()
        model_label = self.llm_label if model == self.engine.llm_model else model
        prev = thread.get("token_usage") or {}
        delta = {
            "prompt_tokens": max(
                0, int(usage["prompt_tokens"]) - int(prev.get("prompt_tokens") or 0)
            ),
            "completion_tokens": max(
                0,
                int(usage["completion_tokens"]) - int(prev.get("completion_tokens") or 0),
            ),
            "reasoning_tokens": max(
                0,
                int(usage["reasoning_tokens"]) - int(prev.get("reasoning_tokens") or 0),
            ),
            "total_tokens": max(
                0, int(usage["total_tokens"]) - int(prev.get("total_tokens") or 0)
            ),
        }

        self.chat_history.set_token_usage(
            project_id,
            uid,
            chat_id,
            prompt_tokens=int(usage["prompt_tokens"]),
            completion_tokens=int(usage["completion_tokens"]),
            reasoning_tokens=int(usage["reasoning_tokens"]),
            total_tokens=int(usage["total_tokens"]),
            model=model,
            model_label=model_label,
        )

        if delta["total_tokens"] <= 0 and not prev:
            delta = {
                "prompt_tokens": int(usage["prompt_tokens"]),
                "completion_tokens": int(usage["completion_tokens"]),
                "reasoning_tokens": int(usage["reasoning_tokens"]),
                "total_tokens": int(usage["total_tokens"]),
            }

        if delta["total_tokens"] > 0:
            self.token_usage.record_run(
                uid=uid,
                username=username,
                chat_id=chat_id,
                chat_title=thread.get("title") or "新会话",
                agent_conversation_id=agent_conversation_id,
                model=model,
                model_label=model_label,
                delta=delta,
                cumulative=usage,
            )

    def get_ingress_job(self, job_id: str) -> dict | None:
        return self.storage.get_json(self.NAMESPACE_INGRESS, job_id)

    def get_ingress_queue_info(self) -> dict[str, int]:
        pending = self._ingress_queue.qsize()
        _metrics.observe_queue_depth(pending)
        return {
            "workers": self._ingress_queue.worker_count,
            "pending": pending,
        }

    def get_metrics_snapshot(self) -> dict:
        return _metrics.snapshot(queue_pending=self._ingress_queue.qsize())

    def get_public_health(self) -> dict[str, object]:
        configured = self.is_llm_configured()
        return {
            "ok": True,
            "project": "deepticket",
            "version": "0.1.0",
            "auth": True,
            "register_enabled": self.config.auth.register_enabled,
            "llm_configured": configured,
            "model_label": self.llm_label if configured else "未配置",
            "storage_backend": self.config.storage.backend,
            "ingress_queue_pending": self._ingress_queue.qsize(),
        }

    async def mark_ingress_job_failed(
        self, job_id: str, *, error: str, event: IngressEvent | None = None
    ) -> None:
        existing = self.storage.get_json(self.NAMESPACE_INGRESS, job_id) or {}
        doc = {
            **existing,
            "job_id": job_id,
            "status": "failed",
            "reply": existing.get("reply") or "",
            "outbound_ok": False,
            "outbound_detail": error[:500],
            "metadata": {
                **(existing.get("metadata") or {}),
                "error": error,
            },
        }
        if event is not None:
            doc.setdefault("source", event.source)
            doc.setdefault("external_id", event.external_id)
        self.storage.set_json(self.NAMESPACE_INGRESS, job_id, doc)
        _metrics.record_ingress_job(ok=False)
        logger.error("Ingress 任务失败: job_id=%s error=%s", job_id, error)

    async def _on_ingress_queue_failure(
        self, item: IngressQueueItem, exc: BaseException
    ) -> None:
        await self.mark_ingress_job_failed(
            item.job_id,
            error=str(exc),
            event=item.event,
        )

    async def start_ingress_workers(self) -> None:
        await self._ingress_queue.start(
            self._process_ingress_queue_item,
            on_failure=self._on_ingress_queue_failure,
        )

    async def stop_ingress_workers(self) -> None:
        await self._ingress_queue.stop()

    async def _process_ingress_queue_item(self, item: IngressQueueItem) -> None:
        await self.run_ingress_event(item.event, job_id=item.job_id)

    async def submit_ingress_event(self, event: IngressEvent) -> IngressJobResult:
        """校验并入队；立即返回 queued 状态，由后台 worker 执行分析。"""
        self.require_llm_configured()
        route = classify_ingress_event(event, self.routing)
        ticket = IngressAdapter.to_ticket(event, route)
        job_id = uuid.uuid4().hex

        queued_doc = {
            "job_id": job_id,
            "route_type": route.type,
            "source": event.source,
            "external_id": event.external_id,
            "status": "queued",
            "reply": "",
            "conversation_id": None,
            "outbound_method": route.outbound.method,
            "outbound_ok": False,
            "outbound_detail": "已入队，等待处理",
            "metadata": ticket.metadata,
        }
        self.storage.set_json(self.NAMESPACE_INGRESS, job_id, queued_doc)
        await self._ingress_queue.enqueue(
            IngressQueueItem(job_id=job_id, event=event)
        )
        logger.info(
            "Ingress 任务入队: job_id=%s source=%s external_id=%s route=%s queue=%s",
            job_id,
            event.source,
            event.external_id,
            route.type,
            self._ingress_queue.qsize(),
        )
        return IngressJobResult(**queued_doc)

    @staticmethod
    def _confidence_chunk(
        *,
        activities: list[dict[str, str]],
        reply: str,
        ok: bool = True,
    ) -> StreamChunk:
        return StreamChunk(
            confidence=compute_confidence(
                activities=activities,
                reply=reply,
                ok=ok,
            )
        )

    async def run_ingress_event(
        self,
        event: IngressEvent,
        *,
        job_id: str | None = None,
    ) -> IngressJobResult:
        """外部事件：分类 → Agent 分析 → 按类型出口投递。"""
        route = classify_ingress_event(event, self.routing)
        ticket = IngressAdapter.to_ticket(event, route)
        if job_id is None:
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
        else:
            existing = self.storage.get_json(self.NAMESPACE_INGRESS, job_id) or {}
            existing.update(
                {
                    "job_id": job_id,
                    "route_type": route.type,
                    "source": event.source,
                    "external_id": event.external_id,
                    "status": "running",
                    "metadata": ticket.metadata,
                }
            )
            self.storage.set_json(self.NAMESPACE_INGRESS, job_id, existing)

        logger.info(
            "Ingress 开始处理: job_id=%s source=%s external_id=%s route=%s",
            job_id,
            event.source,
            event.external_id,
            route.type,
        )

        reply = ""
        conversation_id: str | None = None
        confidence: dict | None = None
        error: str | None = None
        status = "finished"

        try:
            default_project = self.projects.require(
                self.projects.config_store.default_project_id()
            )
            reply, conversation_id, confidence = await collect_stream_text(
                self.run_ticket_stream(ticket, project=default_project)
            )
        except Exception as exc:
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
            metadata={
                **ticket.metadata,
                **({"confidence": confidence} if confidence else {}),
            },
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
                **({"confidence": confidence} if confidence else {}),
                "outbound_response_status": outbound_result.response_status,
                "error": error,
            },
        )
        self.storage.set_json(self.NAMESPACE_INGRESS, job_id, asdict(result))
        _metrics.record_ingress_job(ok=status == "finished")
        if route.outbound.method == "webhook":
            _metrics.record_webhook(ok=outbound_result.ok)
        return result

    async def run_chat_stream(
        self,
        payload: ChatInput,
        *,
        project: ProjectContext,
        uid: str | None = None,
        chat_id: str | None = None,
    ) -> AsyncIterator[StreamChunk]:
        self.require_llm_configured()
        if not uid or not chat_id:
            agent_input = InputAdapter.from_chat(payload)
            agent_input.image_urls = self._resolve_agent_image_urls(
                agent_input.image_urls
            )
            self.apply_project_runtime(agent_input, project)
            async for chunk in self._run_stream(agent_input):
                yield chunk
            return

        agent_input = InputAdapter.from_chat(payload)
        stored_image_urls = list(agent_input.image_urls)
        agent_input.image_urls = self._resolve_agent_image_urls(
            stored_image_urls
        )
        self.apply_project_runtime(agent_input, project)

        thread = self.chat_history.get_thread(project.project_id, uid, chat_id)
        if thread is None:
            raise RuntimeError(f"聊天不存在: {chat_id}")
        if thread.get("agent_conversation_id") and not agent_input.conversation_id:
            agent_input.conversation_id = thread["agent_conversation_id"]

        self.chat_history.append_message(
            project.project_id,
            uid,
            chat_id,
            role="user",
            content=payload.message.strip(),
            image_urls=stored_image_urls or None,
        )

        run = await self.chat_runs.start(
            project=project,
            uid=uid,
            chat_id=chat_id,
            payload=payload,
            agent_input=agent_input,
        )
        try:
            async for chunk in self.chat_runs.subscribe(run):
                yield chunk
        except asyncio.CancelledError:
            # 客户端断连：仅取消 SSE 订阅，后台 Agent 继续执行并持久化回复。
            return

    async def run_ticket_stream(
        self, payload: TicketInput, *, project: ProjectContext
    ) -> AsyncIterator[StreamChunk]:
        self.require_llm_configured()
        agent_input = InputAdapter.from_ticket(payload)
        self.apply_project_runtime(agent_input, project)
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
        yield self._confidence_chunk(
            activities=activity_log,
            reply="".join(assistant_parts),
        )

    async def _run_stream(self, agent_input: AgentInput) -> AsyncIterator[StreamChunk]:
        conversation_id = agent_input.conversation_id
        text_parts: list[str] = []
        started = time.monotonic()
        ok = True
        _metrics.agent_run_started()
        try:
            async for chunk in self.engine.stream(agent_input):
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

    def get_storage_info(self) -> dict[str, str | int]:
        backend = self.config.storage.backend
        info: dict[str, str | int] = {
            "backend": backend,
            "conversation_count": len(
                self.storage.list_keys(self.NAMESPACE_CONVERSATION)
            ),
            "ticket_count": len(self.storage.list_keys(self.NAMESPACE_TICKET)),
            "ingress_job_count": len(self.storage.list_keys(self.NAMESPACE_INGRESS)),
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
