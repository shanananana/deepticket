from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from deepticket.config.schema import GitRepoConfig


class ProjectExtensionsConfig(BaseModel):
    """项目级 Skill / agents.md 配置。"""

    user_skills_dir: str = Field(
        default="",
        description="项目自定义 Skill 目录；留空则仅用内置 Skill",
    )
    agents_md: str = Field(
        default="",
        description="注入 OpenHands system_message_suffix 的项目说明（类似 AGENTS.md）",
    )


class ProjectKnowledgeConfig(BaseModel):
    repos: list[GitRepoConfig] = Field(default_factory=list)


class ProjectMcpConfig(BaseModel):
    servers: dict[str, Any] = Field(default_factory=dict)


class ProjectConfigRecord(BaseModel):
    """Redis 中存储的项目配置；缺省字段由代码默认值补齐。"""

    id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=512)
    enabled: bool = True
    knowledge: ProjectKnowledgeConfig = Field(default_factory=ProjectKnowledgeConfig)
    mcp: ProjectMcpConfig = Field(default_factory=ProjectMcpConfig)
    extensions: ProjectExtensionsConfig = Field(default_factory=ProjectExtensionsConfig)

    def model_dump_redis(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class ProjectSummary(BaseModel):
    id: str
    name: str
    description: str = ""
    enabled: bool = True
    repo_count: int = 0
    mcp_count: int = 0


class ProjectMemberRecord(BaseModel):
    uid: str
    username: str


class UserProjectMembership(BaseModel):
    project_ids: list[str] = Field(default_factory=list)
