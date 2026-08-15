from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from deepticket.api.deps import get_app_state, get_service
from deepticket.auth.dependencies import get_admin_user
from deepticket.auth.user_store import AuthUser
from deepticket.config.llm_loader import LlmConfig
from deepticket.config.schema import LlmSettings
from deepticket.config.yaml_loader import resolve_config_path
from deepticket.config.yaml_persist import update_llm_in_yaml
from deepticket.core.bootstrap import llm_is_configured

router = APIRouter(prefix="/api/admin", tags=["Admin"])


class AdminLlmResponse(BaseModel):
    configured: bool
    model: str
    base_url: str
    label: str
    api_key_hint: str
    config_path: str


class AdminLlmUpdateRequest(BaseModel):
    api_key: str = Field(min_length=1, description="LLM API Key")
    model: str = Field(default="openai/deepseek-v4-flash", min_length=1)
    base_url: str = Field(default="https://api.deepseek.com/v1", min_length=1)
    label: str = Field(default="DeepSeek V4 Flash", min_length=1)


def _mask_api_key(api_key: str) -> str:
    key = api_key.strip()
    if not key:
        return ""
    if len(key) <= 8:
        return "已配置"
    return f"…{key[-4:]}"


@router.get("/llm", response_model=AdminLlmResponse)
async def get_admin_llm(
    request: Request,
    _: AuthUser = Depends(get_admin_user),
) -> AdminLlmResponse:
    state = get_app_state(request)
    llm = state.llm
    return AdminLlmResponse(
        configured=llm_is_configured(llm),
        model=llm.model,
        base_url=llm.base_url,
        label=llm.label,
        api_key_hint=_mask_api_key(llm.api_key),
        config_path=str(resolve_config_path()),
    )


@router.put("/llm")
async def update_admin_llm(
    body: AdminLlmUpdateRequest,
    request: Request,
    _: AuthUser = Depends(get_admin_user),
) -> dict:
    service = get_service(request)
    state = get_app_state(request)
    api_key = body.api_key.strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="api_key 不能为空")

    llm = LlmConfig(
        model=body.model.strip(),
        api_key=api_key,
        base_url=body.base_url.strip(),
        label=body.label.strip(),
    )
    llm_settings = LlmSettings(
        model=llm.model,
        api_key=llm.api_key,
        base_url=llm.base_url,
        label=llm.label,
    )

    try:
        config_path = update_llm_in_yaml(llm_settings)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"写入配置失败: {exc}") from exc

    os.environ["LLM_API_KEY"] = llm.api_key
    os.environ["LLM_MODEL"] = llm.model
    os.environ["LLM_BASE_URL"] = llm.base_url
    os.environ["LLM_LABEL"] = llm.label

    try:
        await service.apply_llm_config(llm)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    state.set_llm(llm)
    return {
        "ok": True,
        "configured": True,
        "model": llm.model,
        "label": llm.label,
        "config_path": str(config_path),
        "api_key_hint": _mask_api_key(llm.api_key),
    }
