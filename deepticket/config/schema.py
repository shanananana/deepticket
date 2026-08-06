from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from deepticket.config.routing_schema import RouteConfig


class LlmSettings(BaseModel):
    """大模型连接配置（OpenAI 兼容 API）。"""

    model: str = Field(
        default="openai/deepseek-v4-flash",
        description="模型 ID，传给 OpenHands LLM profile；格式通常为 openai/<name>",
    )
    api_key: str = Field(
        default="",
        description="LLM API 密钥；必填。直接写在 deepticket.yaml（已 gitignore）",
    )
    base_url: str = Field(
        default="https://api.deepseek.com/v1",
        description="OpenAI 兼容 API 的 Base URL",
    )
    label: str = Field(
        default="DeepSeek V4 Flash",
        description="在 Web UI /health 中展示的模型名称",
    )


class WebSettings(BaseModel):
    """DeepTicket Web 服务（登录页、工作台、Ingress API）。"""

    host: str = Field(
        default="127.0.0.1",
        description="监听地址；生产环境可改为 0.0.0.0",
    )
    port: int = Field(
        default=8600,
        description="Web 端口；浏览器与外部 Ingress 均访问此端口",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:8600",
            "http://localhost:8600",
        ],
        description="允许的浏览器 Origin；生产请改为实际域名",
    )
    sse_heartbeat_seconds: float = Field(
        default=15.0,
        ge=0,
        le=120,
        description="SSE ping 间隔（秒），防止网关 idle 断连；0 表示关闭",
    )


class AuthSettings(BaseModel):
    """登录与注册策略。"""

    register_enabled: bool = Field(
        default=False,
        description="是否开放 /api/auth/register；生产建议 false",
    )
    bootstrap_username: str = Field(
        default="admin",
        description="首次启动时若不存在用户则创建的默认用户名",
    )
    bootstrap_password: str = Field(
        default="admin",
        description="默认 bootstrap 密码；生产环境请尽快修改",
    )
    admin_usernames: list[str] = Field(
        default_factory=list,
        description="管理员用户名列表；留空则仅 bootstrap_username 为管理员",
    )


class LocalStorageConfig(BaseModel):
    """本地文件存储（STORAGE_BACKEND=local 时生效）。"""

    root: str = Field(
        default="./data",
        description="JSON 业务数据目录（账号、对话、Ingress 任务等）",
    )


class RedisStorageConfig(BaseModel):
    """Redis 存储连接。"""

    url: str = Field(
        default="redis://127.0.0.1:6379/0",
        description="Redis 地址与 db，如 redis://127.0.0.1:6379/0；也可在 URL 内写密码",
    )
    username: str = Field(
        default="",
        description="可选；Redis 6 ACL 用户名。与 password 均留空则无鉴权（本地 Docker 默认）",
    )
    password: str = Field(
        default="",
        description="可选；Redis 密码；留空则无鉴权（本地 Docker 默认）",
    )
    key_prefix: str = Field(
        default="deepticket:",
        description="键前缀，避免与公司其它 Redis 数据冲突",
    )
    ttl_seconds: int = Field(
        default=31_536_000,
        description="键过期时间（秒）；0 表示永不过期。默认 365 天",
    )


class StorageConfig(BaseModel):
    """业务数据持久化：账号、对话、Ingress 任务、工单元数据。"""

    backend: Literal["local", "redis"] = Field(
        default="local",
        description="存储后端：local 写 ./data；redis 写 Redis（推荐）",
    )
    local: LocalStorageConfig = Field(default_factory=LocalStorageConfig)
    redis: RedisStorageConfig = Field(default_factory=RedisStorageConfig)
    redis_start_docker: bool = Field(
        default=True,
        description="start_all.sh 是否在本地 Docker 自动启动 Redis；接公司 Redis 时设为 false",
    )


class GitRepoConfig(BaseModel):
    """Git 知识源：DeepTicket 只读 clone 到 workspace，供 Agent 查代码。"""

    id: str = Field(description="仓库唯一 ID；Ingress repo_ids / 提问时引用此 id")
    url: str = Field(
        description="不含 token 的仓库地址，如 https://github.com/org/repo.git 或 https://gitlab.com/group/project.git",
    )
    key: str = Field(
        description="Git 访问令牌（只读）；直接写在 deepticket.yaml 的 key 字段",
    )
    url_template: str | None = Field(
        default=None,
        description=(
            "可选；自定义 clone URL，{key} 为令牌占位。"
            "GitLab.com 会自动用 oauth2:{key}@；自建 GitLab 若域名非常规可显式写此字段"
        ),
    )
    branch: str = Field(default="main", description="同步分支")
    workspace_subdir: str | None = Field(
        default=None,
        description="挂载到 workspace/project 下的子目录名；默认等于 id",
    )


class KnowledgeConfig(BaseModel):
    """知识层：Git 缓存目录与工作区。"""

    git_cache_dir: str = Field(
        default="./workspace/knowledge",
        description="Git clone 缓存（只读源码）",
    )
    workspace_dir: str = Field(
        default="./workspace/project",
        description="Agent 工作区根目录；repo 以 symlink 形式挂载到此",
    )
    repos: list[GitRepoConfig] = Field(
        default_factory=list,
        description="要同步的 Git 仓库列表；为空则 Agent 无法基于真实代码分析",
    )


class EngineConfig(BaseModel):
    """OpenHands Agent Server 连接与 LLM profile。"""

    agent_server_host: str = Field(
        default="127.0.0.1",
        description="Agent Server 地址；通常与 Web 同机，用户无需直接访问",
    )
    agent_server_port: int = Field(
        default=8100,
        description="Agent Server 端口；由 start_all.sh 后台拉起",
    )
    llm_profile: str = Field(
        default="deepseek-v4-flash",
        description="OpenHands LLM profile 名；启动时注册 llm 配置到此 profile",
    )
    session_api_key: str = Field(
        default="",
        description="DeepTicket ↔ Agent Server 会话密钥；留空时 setup.sh 自动生成",
    )
    agent_timeout_seconds: int = Field(
        default=600,
        ge=60,
        le=3600,
        description="单次 Agent 运行最长等待秒数",
    )


class ExtensionsConfig(BaseModel):
    """Skill 目录（Agent 排查 SOP）。"""

    skills_dir: str = Field(
        default="deepticket/skills",
        description="项目内置 Skill（可提交到 Git）",
    )
    user_skills_dir: str = Field(
        default="",
        description="用户自定义 Skill 目录；留空表示不使用",
    )
    workspace_skills_dir: str = Field(
        default="workspace/project/.openhands/skills",
        description="发布到 Agent 工作区的 Skill 目标目录",
    )


class IngressSettings(BaseModel):
    """外部系统接入（Ingress）：监控、Jira、ITSM 等 POST /api/ingress/events。

    需携带 ingress.api_key（X-Ingress-API-Key 或 Bearer）。事件异步入队处理，
    POST 立即返回 202 + job_id，用 GET /api/ingress/jobs/{job_id} 轮询结果。
    """

    api_key: str = Field(
        default="",
        description=(
            "Ingress API 密钥；请求头 X-Ingress-API-Key 或 Authorization: Bearer。"
            "留空时 setup.sh 自动生成"
        ),
    )
    queue_workers: int = Field(
        default=1,
        ge=1,
        le=16,
        description="Ingress 异步队列 worker 数量；单进程内并发处理任务数",
    )
    queue_backlog_alert: int = Field(
        default=10,
        ge=1,
        description="队列 pending 超过此值时在 /api/metrics 产生告警",
    )
    routes: list[RouteConfig] = Field(
        default_factory=list,
        description=(
            "路由规则列表，按声明顺序匹配。"
            "每条含 match（来源/关键词）、outbound（store_only 或 webhook）、"
            "可选 prompt_suffix 与 repo_ids"
        ),
    )


class McpSettings(BaseModel):
    """MCP 工具服务器；启动时同步到 Agent Server。"""

    servers: dict[str, Any] = Field(
        default_factory=dict,
        description="MCP server 定义（transport/command/args 等）；enabled: false 可禁用",
    )


class AppConfig(BaseModel):
    """DeepTicket 统一配置根对象（deepticket.yaml）。"""

    llm: LlmSettings = Field(default_factory=LlmSettings)
    web: WebSettings = Field(default_factory=WebSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    knowledge: KnowledgeConfig = Field(default_factory=KnowledgeConfig)
    engine: EngineConfig = Field(default_factory=EngineConfig)
    extensions: ExtensionsConfig = Field(default_factory=ExtensionsConfig)
    ingress: IngressSettings = Field(default_factory=IngressSettings)
    mcp: McpSettings = Field(default_factory=McpSettings)
