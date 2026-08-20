
from __future__ import annotations

import logging

from deepticket.auth.user_store import AuthUser, UserStore
from deepticket import __version__
from deepticket.chat_runs import ChatRunManager
from deepticket.config.mcp_loader import filter_enabled_servers, validate_mcp_servers
from deepticket.config.routing_schema import RoutingConfig
from deepticket.chat_orchestrator import ChatOrchestrator
from deepticket.config.llm_loader import LlmConfig
from deepticket.config.schema import AppConfig
from deepticket.ingress_runner import IngressRunner
from deepticket.layers.engine.openhands_engine import OpenHandsEngine
from deepticket.layers.ingress.pipeline import IngressJobResult
from deepticket.layers.input.ingress_models import IngressEvent
from deepticket.layers.input.models import ChatInput, TicketInput
from deepticket.layers.knowledge.manager import GitSyncResult, KnowledgeManager
from deepticket.layers.knowledge.skill_manager import SkillInfo, SkillManager
from deepticket.config.redis_url import redact_redis_url, resolve_redis_url
from deepticket.layers.storage import create_storage
from deepticket.layers.storage.base import StorageBackend
from deepticket.layers.storage.chat_history import ChatHistoryStore
from deepticket.layers.storage.token_usage import TokenUsageStore
from deepticket.observability.metrics import get_metrics
from deepticket.paths import resolve_from_project
from deepticket.projects.registry import ProjectContext, ProjectRegistry

logger = logging.getLogger(__name__)
_metrics = get_metrics()


class DeepTicketService:
    """五层编排：输入 → 知识/存储 → 引擎 → 输出。"""

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
        self.ingress = IngressRunner(self)
        self.chat = ChatOrchestrator(self)
        _metrics.queue_backlog_alert = config.ingress.queue_backlog_alert
        self.chat_runs = ChatRunManager(self)

    def _resolve_agent_image_urls(self, urls: list[str]) -> list[str]:
        return self.chat.resolve_agent_image_urls(urls)

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
            await self.engine.sync_mcp_config(servers)
            if servers:
                logger.info("MCP 已同步: %s", ", ".join(servers.keys()))
            else:
                logger.info("MCP 无启用项，已清空 Agent Server 中的 MCP 配置")
        except (OSError, ValueError, RuntimeError) as exc:
            logger.error("MCP 同步失败（服务仍启动）: %s", exc)

        try:
            default_project = self.projects.require(
                self.projects.config_store.default_project_id()
            )
            self.projects.ensure_skills_published(default_project)
        except (KeyError, OSError) as exc:
            logger.warning("默认项目 Skill 预热失败: %s", exc)

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
        self, agent_input, project: ProjectContext
    ) -> None:
        self.chat.apply_project_runtime(agent_input, project)

    def list_project_git_repos(self, project: ProjectContext) -> list[dict[str, str]]:
        return project.list_repos()

    def sync_project_knowledge(self, project: ProjectContext) -> list[GitSyncResult]:
        return project.sync_knowledge()

    def reload_project_skills(self, project: ProjectContext) -> list[str]:
        return self.projects.reload_project_skills(project)

    def refresh_project_skills(self, project_id: str) -> list[str]:
        self.projects.invalidate_project_skills(project_id)
        project = self.projects.require(project_id)
        return self.projects.reload_project_skills(project)

    def list_project_skills(self, project: ProjectContext) -> list[SkillInfo]:
        return project.list_skills()

    def list_recent_ingress_jobs(self, *, limit: int = 20) -> list[dict]:
        return self.ingress.list_recent_jobs(limit=limit)

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
        return self.ingress.get_job(job_id)

    def get_ingress_queue_info(self) -> dict[str, int]:
        pending = self.ingress.queue.qsize()
        _metrics.observe_queue_depth(pending)
        return {
            "workers": self.ingress.queue.worker_count,
            "pending": pending,
        }

    def get_metrics_snapshot(self) -> dict:
        return _metrics.snapshot(queue_pending=self.ingress.queue.qsize())

    def get_public_health(self) -> dict[str, object]:
        configured = self.is_llm_configured()
        return {
            "ok": True,
            "project": "deepticket",
            "version": __version__,
            "auth": True,
            "register_enabled": self.config.auth.register_enabled,
            "llm_configured": configured,
            "model_label": self.llm_label if configured else "未配置",
            "storage_backend": self.config.storage.backend,
            "ingress_queue_pending": self.ingress.queue.qsize(),
        }

    async def mark_ingress_job_failed(
        self, job_id: str, *, error: str, event: IngressEvent | None = None
    ) -> None:
        await self.ingress.mark_failed(job_id, error=error, event=event)

    async def start_ingress_workers(self) -> None:
        await self.ingress.start_workers()

    async def stop_ingress_workers(self) -> None:
        await self.ingress.stop_workers()

    async def submit_ingress_event(self, event: IngressEvent) -> IngressJobResult:
        return await self.ingress.submit(event)

    async def run_ingress_event(
        self,
        event: IngressEvent,
        *,
        job_id: str | None = None,
    ) -> IngressJobResult:
        return await self.ingress.run_event(event, job_id=job_id)

    async def run_chat_stream(self, payload: ChatInput, **kwargs):
        async for chunk in self.chat.run_chat_stream(payload, **kwargs):
            yield chunk

    async def run_ticket_stream(self, payload: TicketInput, **kwargs):
        async for chunk in self.chat.run_ticket_stream(payload, **kwargs):
            yield chunk

    async def _run_stream(self, agent_input):
        """兼容测试 monkeypatch；生产路径见 ChatOrchestrator。"""
        async for chunk in self.chat._run_stream(agent_input):
            yield chunk

    def get_storage_info(self) -> dict[str, str | int]:
        backend = self.config.storage.backend
        info: dict[str, str | int] = {
            "backend": backend,
            "conversation_count": self.chat.conversation_count(),
            "ticket_count": self.chat.ticket_count(),
            "ingress_job_count": self.ingress.job_count(),
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
