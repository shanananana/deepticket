from __future__ import annotations

import os

from deepticket.config.llm_loader import LlmConfig
from deepticket.config.loader import load_app_config
from deepticket.config.schema import AppConfig
from deepticket.paths import PROJECT_ROOT
from deepticket.service import DeepTicketService


def load_runtime_config(*, dotenv_root=PROJECT_ROOT) -> AppConfig:
    config = load_app_config(dotenv_root=dotenv_root)
    engine = config.engine

    if os.environ.get("AGENT_SERVER_HOST"):
        engine = engine.model_copy(
            update={"agent_server_host": os.environ["AGENT_SERVER_HOST"]}
        )
    if os.environ.get("AGENT_SERVER_PORT"):
        engine = engine.model_copy(
            update={"agent_server_port": int(os.environ["AGENT_SERVER_PORT"])}
        )
    session_key = os.environ.get("OH_SESSION_API_KEYS_0", "").strip()
    if session_key:
        engine = engine.model_copy(update={"session_api_key": session_key})

    return config.model_copy(update={"engine": engine})


def build_service(config: AppConfig, llm: LlmConfig) -> DeepTicketService:
    return DeepTicketService(
        config,
        llm_model=llm.model,
        llm_api_key=llm.api_key,
        llm_base_url=llm.base_url,
        llm_label=llm.label,
    )


def load_llm_config(config: AppConfig | None = None) -> LlmConfig:
    cfg = config or load_runtime_config()
    return LlmConfig(
        model=cfg.llm.model,
        api_key=cfg.llm.api_key.strip(),
        base_url=cfg.llm.base_url.strip(),
        label=cfg.llm.label,
    )


def llm_is_configured(llm: LlmConfig) -> bool:
    return bool(llm.api_key.strip())
