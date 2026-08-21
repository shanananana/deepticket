from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from deepticket.api.deps import get_service
from deepticket.auth.dependencies import get_current_user
from deepticket.auth.user_store import AuthUser

router = APIRouter(prefix="/api/usage", tags=["Usage"])


@router.get("/summary")
async def usage_summary(
    request: Request,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    service = get_service(request)
    data = service.list_user_token_summary(user.uid)
    return {
        "user": {"username": user.username},
        "summary": data["summary"],
        "conversations": data["conversations"],
    }


@router.get("/runs")
async def usage_runs(
    request: Request,
    user: AuthUser = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    service = get_service(request)
    runs = service.list_user_token_runs(user.uid, limit=limit)
    return {
        "user": {"username": user.username},
        "runs": runs,
    }
