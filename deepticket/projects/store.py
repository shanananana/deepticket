from __future__ import annotations

import logging
from typing import Any

from deepticket.config.schema import AppConfig
from deepticket.layers.storage.base import StorageBackend
from deepticket.projects.merge import deep_merge
from deepticket.projects.models import ProjectConfigRecord, ProjectSummary

logger = logging.getLogger(__name__)

_NS_PROJECTS = "project_configs"
_NS_INDEX = "project_index"
_DEFAULT_PROJECT_ID = "default"


class ProjectConfigStore:
    """项目配置：Redis 优先；deepticket.yaml 仅作缺省兜底。"""

    def __init__(self, storage: StorageBackend, app_config: AppConfig) -> None:
        self.storage = storage
        self.app_config = app_config

    @staticmethod
    def default_project_id() -> str:
        return _DEFAULT_PROJECT_ID

    def yaml_fallback(self, project_id: str | None = None) -> ProjectConfigRecord:
        """从 deepticket.yaml 生成的兜底配置（不写入 Redis）。"""
        return self.default_record(project_id)

    def default_record(self, project_id: str | None = None) -> ProjectConfigRecord:
        pid = project_id or _DEFAULT_PROJECT_ID
        name = "默认项目" if pid == _DEFAULT_PROJECT_ID else pid
        return ProjectConfigRecord(
            id=pid,
            name=name,
            description="从 deepticket.yaml 迁移的默认配置",
            knowledge={"repos": [repo.model_dump() for repo in self.app_config.knowledge.repos]},
            mcp={"servers": dict(self.app_config.mcp.servers)},
            extensions={
                "user_skills_dir": self.app_config.extensions.user_skills_dir or "",
                "agents_md": "",
            },
        )

    def resolve(self, project_id: str, raw: dict[str, Any] | None) -> ProjectConfigRecord | None:
        """Redis raw + yaml 兜底 → 运行时有效配置。"""
        if raw is None:
            if project_id == _DEFAULT_PROJECT_ID:
                return self.yaml_fallback(_DEFAULT_PROJECT_ID)
            return None
        fallback = self.yaml_fallback(project_id).model_dump(mode="json")
        merged = deep_merge(fallback, raw)
        merged["id"] = project_id
        return ProjectConfigRecord.model_validate(merged)

    def ensure_default_project(self) -> ProjectConfigRecord:
        index = self._load_index()
        if _DEFAULT_PROJECT_ID not in index:
            self._ensure_index_entry(_DEFAULT_PROJECT_ID)
            logger.info("已注册默认项目索引: %s（配置走 Redis 或 yaml 兜底）", _DEFAULT_PROJECT_ID)
        return self.get(_DEFAULT_PROJECT_ID)

    def _load_index(self) -> list[str]:
        doc = self.storage.get_json(_NS_INDEX, "all") or {}
        ids = doc.get("project_ids") or []
        return [str(item) for item in ids if str(item).strip()]

    def _save_index(self, project_ids: list[str]) -> None:
        clean = sorted({item.strip() for item in project_ids if item.strip()})
        self.storage.set_json(_NS_INDEX, "all", {"project_ids": clean})

    def _ensure_index_entry(self, project_id: str) -> None:
        index = self._load_index()
        if project_id not in index:
            index.append(project_id)
            self._save_index(index)

    def list_ids(self) -> list[str]:
        return self._load_index()

    def list_summaries(self) -> list[ProjectSummary]:
        items: list[ProjectSummary] = []
        for project_id in self.list_ids():
            record = self.get(project_id)
            if record is None:
                continue
            items.append(
                ProjectSummary(
                    id=record.id,
                    name=record.name,
                    description=record.description,
                    enabled=record.enabled,
                    repo_count=len(record.knowledge.repos),
                    mcp_count=len(record.mcp.servers),
                )
            )
        return items

    def get_raw(self, project_id: str) -> dict[str, Any] | None:
        return self.storage.get_json(_NS_PROJECTS, project_id)

    def has_redis_config(self, project_id: str) -> bool:
        return self.get_raw(project_id) is not None

    def get(self, project_id: str) -> ProjectConfigRecord | None:
        return self.resolve(project_id, self.get_raw(project_id))

    def apply_patch(self, project_id: str, patch: dict[str, Any]) -> ProjectConfigRecord:
        """将 patch 合并进 Redis；仅保存显式修改的字段。"""
        clean_patch = {k: v for k, v in patch.items() if k != "id"}
        raw = self.get_raw(project_id) or {}
        merged_raw = deep_merge(raw, clean_patch)
        merged_raw["id"] = project_id
        self.storage.set_json(_NS_PROJECTS, project_id, merged_raw)
        self._ensure_index_entry(project_id)
        resolved = self.resolve(project_id, merged_raw)
        if resolved is None:
            raise ValueError(f"项目配置无效: {project_id}")
        return resolved

    def save(self, record: ProjectConfigRecord) -> ProjectConfigRecord:
        return self.apply_patch(record.id, record.model_dump_redis())

    def patch_meta(
        self,
        project_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        enabled: bool | None = None,
    ) -> ProjectConfigRecord:
        patch: dict[str, Any] = {}
        if name is not None:
            patch["name"] = name
        if description is not None:
            patch["description"] = description
        if enabled is not None:
            patch["enabled"] = enabled
        if not patch:
            existing = self.get(project_id)
            if existing is None:
                raise ValueError(f"项目不存在: {project_id}")
            return existing
        return self.apply_patch(project_id, patch)

    def patch_knowledge(self, project_id: str, repos: list[dict[str, Any]]) -> ProjectConfigRecord:
        return self.apply_patch(project_id, {"knowledge": {"repos": repos}})

    def patch_mcp(self, project_id: str, servers: dict[str, Any]) -> ProjectConfigRecord:
        return self.apply_patch(project_id, {"mcp": {"servers": servers}})

    def patch_extensions(
        self,
        project_id: str,
        *,
        user_skills_dir: str | None = None,
        agents_md: str | None = None,
    ) -> ProjectConfigRecord:
        ext_patch: dict[str, Any] = {}
        if user_skills_dir is not None:
            ext_patch["user_skills_dir"] = user_skills_dir
        if agents_md is not None:
            ext_patch["agents_md"] = agents_md
        if not ext_patch:
            existing = self.get(project_id)
            if existing is None:
                raise ValueError(f"项目不存在: {project_id}")
            return existing
        return self.apply_patch(project_id, {"extensions": ext_patch})

    def delete(self, project_id: str) -> bool:
        if project_id == _DEFAULT_PROJECT_ID:
            return False
        if self.get_raw(project_id) is None:
            return False
        self.storage.delete(_NS_PROJECTS, project_id)
        index = [item for item in self._load_index() if item != project_id]
        self._save_index(index)
        return True
