from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from deepticket.api.deps import get_service

INGRESS_API_KEY_HEADER = "X-Ingress-API-Key"
_ingress_key_header = APIKeyHeader(name=INGRESS_API_KEY_HEADER, auto_error=False)


def _extract_provided_key(
    request: Request,
    header_key: str | None,
) -> str:
    if header_key and header_key.strip():
        return header_key.strip()
    auth = request.headers.get("Authorization", "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


def verify_ingress_api_key(
    request: Request,
    header_key: str | None = Depends(_ingress_key_header),
) -> None:
    """校验 Ingress API 密钥（X-Ingress-API-Key 或 Authorization: Bearer）。"""
    expected = get_service(request).config.ingress.api_key.strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingress api_key 未配置，请在 deepticket.yaml 的 ingress.api_key 填写或运行 setup.sh 生成",
        )

    provided = _extract_provided_key(request, header_key)
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ingress API 密钥无效或缺失",
            headers={"WWW-Authenticate": "Bearer"},
        )
