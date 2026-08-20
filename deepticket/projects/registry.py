from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from deepticket.config.mcp_loader import filter_enabled_servers, validate_mcp_servers
from deepticket.config.schema import AppConfig, ExtensionsConfig, KnowledgeConfig
from deepticket.layers.knowledge.manager import GitSyncResult, KnowledgeManager
from deepticket.layers.knowledge.skill_manager import SkillInfo, SkillManager
from deepticket.paths import resolve_from_project
from deepticket.projects.models import ProjectConfigRecord, ProjectSummary
from deepticket.projects.permissions import ProjectPermissionStore
from deepticket.projects.store import ProjectConfigStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProjectRuntime:
    workspace_dir: Path
    mcp_servers: dict
    agents_md: str


class ProjectContext:
    """单个项目的运行时视图（知识库 / Skill / workspace / MCP）。"""

    def __init__(
        self,
        record: ProjectConfigRecord,
        *,
        app_config: AppConfig,
        resolve_path,
    ) -> None:
        self.record = record
        self._app_config = app_config
        self._resolve_path = resolve_path
        self._workspace_dir = resolve_path(f"workspace/{record.id}/project")
        self._git_cache_dir = resolve_path(f"workspace/{record.id}/knowledge")
        self._skills_target = self._workspace_dir / ".openhands" / "skills"

    @property
    def project_id(self) -> str:
        return self.record.id

    def knowledge_config(self) -> KnowledgeConfig:
        return KnowledgeConfig(
            git_cache_dir=str(self._git_cache_dir),
            workspace_dir=str(self._workspace_dir),
            repos=list(self.record.knowledge.repos),
        )

    def knowledge_manager(self) -> KnowledgeManager:
        return KnowledgeManager(self.knowledge_config())

    def skill_manager(self) -> SkillManager:
        extensions = ExtensionsConfig(
            skills_dir=self._app_config.extensions.skills_dir,
            user_skills_dir=self.record.extensions.user_skills_dir or "",
            workspace_skills_dir=str(self._skills_target),
        )
        return SkillManager(
            skills_dir=self._resolve_path(extensions.skills_dir),
            user_skills_dir=(
                self._resolve_path(extensions.user_skills_dir)
                if extensions.user_skills_dir
                else None
            ),
            workspace_skills_dir=self._skills_target,
        )

    def runtime(self) -> ProjectRuntime:
        servers = filter_enabled_servers(self.record.mcp.servers)
        errors = validate_mcp_servers(servers)
        if errors:
            raise ValueError(f"项目 {self.record.id} MCP 配置无效: {'; '.join(errors)}")
        return ProjectRuntime(
            workspace_dir=self._workspace_dir,
            mcp_servers=servers,
            agents_md=self.record.extensions.agents_md or "",
        )

    def list_repos(self) -> list[dict[str, str]]:
        return self.knowledge_manager().list_repos()

    def list_skills(self) -> list[SkillInfo]:
        return self.skill_manager().list_skills()

    def sync_knowledge(self) -> list[GitSyncResult]:
        return self.knowledge_manager().sync_all()

    def publish_skills(self) -> list[str]:
        return self.skill_manager().publish_to_workspace()


class ProjectRegistry:
    def __init__(
        self,
        storage,
        app_config: AppConfig,
        *,
        resolve_path=resolve_from_project,
    ) -> None:
        self.config_store = ProjectConfigStore(storage, app_config)
        self.permissions = ProjectPermissionStore(storage)
        self.app_config = app_config
        self._resolve_path = resolve_path
        self._skills_ready: set[str] = set()

    def ensure_skills_published(self, project: ProjectContext) -> None:
        pid = project.project_id
        if pid in self._skills_ready:
            return
        try:
            published = project.publish_skills()
            if published:
                logger.info(
                    "项目 %s Skills 已发布: %s",
                    pid,
                    ", ".join(published),
                )
        except OSError as exc:
            logger.warning("项目 %s Skill 发布失败: %s", pid, exc)
        self._skills_ready.add(pid)

    def invalidate_project_skills(self, project_id: str) -> None:
        self._skills_ready.discard(project_id)

    def reload_project_skills(self, project: ProjectContext) -> list[str]:
        self._skills_ready.discard(project.project_id)
        published = project.publish_skills()
        self._skills_ready.add(project.project_id)
        return published

    def bootstrap(self, *, bootstrap_uid: str, bootstrap_username: str) -> None:
        self.config_store.ensure_default_project()
        self.permissions.ensure_default_access(bootstrap_uid, bootstrap_username)

    def get(self, project_id: str) -> ProjectContext | None:
        record = self.config_store.get(project_id)
        if record is None or not record.enabled:
            return None
        return ProjectContext(record, app_config=self.app_config, resolve_path=self._resolve_path)

    def require(self, project_id: str) -> ProjectContext:
        ctx = self.get(project_id)
        if ctx is None:
            raise KeyError(f"项目不存在或已禁用: {project_id}")
        return ctx

    def list_summaries_for_user(self, uid: str, *, is_admin: bool) -> list[ProjectSummary]:
        if is_admin:
            return self.config_store.list_summaries()
        allowed = set(self.permissions.list_project_ids_for_user(uid))
        return [
            item
            for item in self.config_store.list_summaries()
            if item.id in allowed and item.enabled
        ]

    def user_can_access(self, uid: str, project_id: str, *, is_admin: bool) -> bool:
        if is_admin:
            return self.get(project_id) is not None
        return self.permissions.user_has_access(uid, project_id) and self.get(project_id) is not None

    def save_project(self, record: ProjectConfigRecord) -> ProjectConfigRecord:
        return self.config_store.save(record)

    def patch_project_meta(
        self,
        project_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        enabled: bool | None = None,
    ) -> ProjectConfigRecord:
        return self.config_store.patch_meta(
            project_id,
            name=name,
            description=description,
            enabled=enabled,
        )

    def patch_project_knowledge(
        self, project_id: str, repos: list[dict]
    ) -> ProjectConfigRecord:
        return self.config_store.patch_knowledge(project_id, repos)

    def patch_project_mcp(self, project_id: str, servers: dict) -> ProjectConfigRecord:
        return self.config_store.patch_mcp(project_id, servers)

    def patch_project_extensions(
        self,
        project_id: str,
        *,
        user_skills_dir: str | None = None,
        agents_md: str | None = None,
    ) -> ProjectConfigRecord:
        return self.config_store.patch_extensions(
            project_id,
            user_skills_dir=user_skills_dir,
            agents_md=agents_md,
        )

    def delete_project(self, project_id: str) -> bool:
        return self.config_store.delete(project_id)
