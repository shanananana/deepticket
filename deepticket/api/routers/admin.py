from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from deepticket.api.deps import get_service
from deepticket.auth.dependencies import get_admin_user
from deepticket.auth.user_store import AuthUser

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/token-usage")
async def admin_token_usage(
    request: Request,
    user: AuthUser = Depends(get_admin_user),
) -> dict:
    service = get_service(request)
    return {
        "user": {"username": user.username, "is_admin": True},
        **service.list_admin_token_usage(),
    }
