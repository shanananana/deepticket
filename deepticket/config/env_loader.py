from __future__ import annotations

import os

from deepticket.config.repos_loader import load_git_repos_from_env
from deepticket.config.schema import (
    AppConfig,
    EngineConfig,
    ExtensionsConfig,
    IngressSettings,
    KnowledgeConfig,
    LlmSettings,
    LocalStorageConfig,
    RedisStorageConfig,
    StorageConfig,
    WebSettings,
)
from deepticket.paths import DEFAULT_SKILLS_DIR, DEFAULT_WORKSPACE_SKILLS_DIR


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    if not raw:
        return default
    return int(raw)


def _env_bool(name: str, default: bool) -> bool:
    raw = _env(name).lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def load_app_config_from_env() -> AppConfig:
    storage_backend = _env("STORAGE_BACKEND", "redis")
    if storage_backend not in ("local", "redis"):
        raise ValueError(f"STORAGE_BACKEND 无效: {storage_backend}")

    legacy_repos_path = _env("GIT_REPOS_CONFIG_PATH", "/dev/null/legacy-repos.json")

    return AppConfig(
        llm=LlmSettings(
            model=_env("LLM_MODEL", "openai/deepseek-v4-flash"),
            api_key=_env("LLM_API_KEY"),
            base_url=_env("LLM_BASE_URL", "https://api.deepseek.com/v1"),
            label=_env("LLM_LABEL", "DeepSeek V4 Flash"),
        ),
        web=WebSettings(
            host=_env("WEB_HOST", "127.0.0.1"),
            port=_env_int("WEB_PORT", 8600),
        ),
        storage=StorageConfig(
            backend=storage_backend,  # type: ignore[arg-type]
            local=LocalStorageConfig(root=_env("STORAGE_LOCAL_ROOT", "./data")),
            redis=RedisStorageConfig(
                url=_env("REDIS_URL", "redis://127.0.0.1:6379/0"),
                username=_env("REDIS_USERNAME"),
                password=_env("REDIS_PASSWORD"),
                key_prefix=_env("REDIS_KEY_PREFIX", "deepticket:"),
                ttl_seconds=_env_int("REDIS_TTL_SECONDS", 31_536_000),
            ),
            redis_start_docker=_env_bool("REDIS_START_DOCKER", True),
        ),
        knowledge=KnowledgeConfig(
            git_cache_dir=_env("KNOWLEDGE_GIT_CACHE_DIR", "./workspace/knowledge"),
            workspace_dir=_env("KNOWLEDGE_WORKSPACE_DIR", "./workspace/project"),
            repos=load_git_repos_from_env(config_path=legacy_repos_path),
        ),
        engine=EngineConfig(
            agent_server_host=_env("AGENT_SERVER_HOST", "127.0.0.1"),
            agent_server_port=_env_int("AGENT_SERVER_PORT", 8100),
            llm_profile=_env("OH_LLM_PROFILE", "deepseek-v4-flash"),
            session_api_key=_env("OH_SESSION_API_KEYS_0"),
        ),
        extensions=ExtensionsConfig(
            skills_dir=_env("SKILLS_DIR", str(DEFAULT_SKILLS_DIR)),
            user_skills_dir=_env("USER_SKILLS_DIR", ""),
            workspace_skills_dir=_env(
                "WORKSPACE_SKILLS_DIR", str(DEFAULT_WORKSPACE_SKILLS_DIR)
            ),
        ),
        ingress=IngressSettings(
            api_key=_env("INGRESS_API_KEY"),
            queue_workers=_env_int("INGRESS_QUEUE_WORKERS", 1),
        ),
    )
