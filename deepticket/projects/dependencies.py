from __future__ import annotations

from fastapi import Depends, HTTPException, Query, Request, status

from deepticket.api.deps import get_service
from deepticket.auth.dependencies import get_current_user
from deepticket.auth.user_store import AuthUser
from deepticket.projects.registry import ProjectContext


def get_project_id(
    project_id: str = Query(..., min_length=1, max_length=64, alias="project_id"),
) -> str:
    return project_id.strip()


def get_project_context(
    request: Request,
    project_id: str = Depends(get_project_id),
    user: AuthUser = Depends(get_current_user),
) -> ProjectContext:
    service = get_service(request)
    if not service.projects.user_can_access(
        user.uid, project_id, is_admin=service.is_admin(user)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该项目",
        )
    try:
        return service.projects.require(project_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
