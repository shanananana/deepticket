from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from deepticket.api.deps import get_service
from deepticket.auth.dependencies import get_current_user
from deepticket.auth.user_store import AuthUser

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("")
async def list_projects(
    request: Request, user: AuthUser = Depends(get_current_user)
) -> dict:
    service = get_service(request)
    return {"projects": service.list_user_projects(user)}
