from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, Request

from deepticket.config.llm_loader import LlmConfig
from deepticket.service import DeepTicketService


@dataclass
class AppState:
    service: DeepTicketService
    llm: LlmConfig

    def set_llm(self, llm: LlmConfig) -> None:
        self.llm = llm


def get_app_state(request: Request) -> AppState:
    state = getattr(request.app.state, "deepticket", None)
    if state is None:
        raise HTTPException(status_code=503, detail="服务尚未初始化")
    return state


def get_service(request: Request) -> DeepTicketService:
    return get_app_state(request).service


def get_llm(request: Request) -> LlmConfig:
    return get_app_state(request).llm
