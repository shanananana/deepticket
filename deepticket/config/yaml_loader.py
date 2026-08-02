from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from deepticket.config.schema import AppConfig
from deepticket.paths import DEFAULT_CONFIG_PATH, PROJECT_ROOT

_ENV_PATTERN = re.compile(r"^\$\{([A-Z0-9_]+)\}$")


def resolve_config_path(path: str | Path | None = None) -> Path:
    raw = path or os.environ.get("DEEPTICKET_CONFIG", str(DEFAULT_CONFIG_PATH))
    config_path = Path(raw)
    if config_path.is_absolute():
        return config_path
    return PROJECT_ROOT / config_path


def _resolve_env_string(value: str) -> str:
    match = _ENV_PATTERN.match(value.strip())
    if not match:
        return value
    return os.environ.get(match.group(1), "").strip()


def _resolve_env_in_obj(value: Any) -> Any:
    if isinstance(value, str):
        return _resolve_env_string(value)
    if isinstance(value, list):
        return [_resolve_env_in_obj(item) for item in value]
    if isinstance(value, dict):
        return {key: _resolve_env_in_obj(item) for key, item in value.items()}
    return value


def _resolve_repo_keys(config: AppConfig) -> AppConfig:
    repos = []
    for repo in config.knowledge.repos:
        repos.append(repo.model_copy(update={"key": _resolve_env_string(repo.key)}))
    knowledge = config.knowledge.model_copy(update={"repos": repos})
    return config.model_copy(update={"knowledge": knowledge})


def _sync_process_env(config: AppConfig) -> None:
    """把配置同步到环境变量，供 shell 脚本与鉴权中间件使用。"""
    if config.llm.api_key:
        os.environ.setdefault("LLM_API_KEY", config.llm.api_key)
    os.environ.setdefault("LLM_MODEL", config.llm.model)
    os.environ.setdefault("LLM_BASE_URL", config.llm.base_url)
    os.environ.setdefault("LLM_LABEL", config.llm.label)
    os.environ.setdefault("WEB_HOST", config.web.host)
    os.environ.setdefault("WEB_PORT", str(config.web.port))
    os.environ.setdefault("STORAGE_BACKEND", config.storage.backend)
    os.environ.setdefault("REDIS_URL", config.storage.redis.url)
    os.environ.setdefault("REDIS_KEY_PREFIX", config.storage.redis.key_prefix)
    os.environ.setdefault("REDIS_TTL_SECONDS", str(config.storage.redis.ttl_seconds))
    os.environ.setdefault(
        "REDIS_START_DOCKER", "1" if config.storage.redis_start_docker else "0"
    )
    os.environ.setdefault("AGENT_SERVER_HOST", config.engine.agent_server_host)
    os.environ.setdefault("AGENT_SERVER_PORT", str(config.engine.agent_server_port))
    if config.engine.session_api_key:
        os.environ.setdefault("OH_SESSION_API_KEYS_0", config.engine.session_api_key)
    if config.ingress.api_key:
        os.environ.setdefault("INGRESS_API_KEY", config.ingress.api_key)
    os.environ.setdefault("INGRESS_QUEUE_WORKERS", str(config.ingress.queue_workers))


def load_yaml_config(path: Path) -> AppConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    resolved = _resolve_env_in_obj(raw)
    config = AppConfig.model_validate(resolved)
    return _resolve_repo_keys(config)


def load_app_config_from_env() -> AppConfig:
    from deepticket.config.env_loader import load_app_config_from_env as _load

    return _load()


def load_app_config(
    path: str | Path | None = None,
    *,
    dotenv_root: Path | None = None,
) -> AppConfig:
    config_path = resolve_config_path(path)
    if config_path.is_file():
        config = load_yaml_config(config_path)
    else:
        config = load_app_config_from_env()

    _sync_process_env(config)
    return config
