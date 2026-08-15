from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from deepticket.api.deps import get_llm, get_service
from deepticket.auth.dependencies import get_admin_user, get_current_user
from deepticket.auth.user_store import AuthUser
from deepticket.projects.dependencies import get_project_context
from deepticket.projects.registry import ProjectContext

router = APIRouter(prefix="/api", tags=["System"])


@router.get("/health")
async def health(request: Request) -> dict:
    service = get_service(request)
    public = service.get_public_health()
    return {
        **public,
        "register_enabled": service.config.auth.register_enabled,
        "multi_project": True,
    }


@router.get("/metrics")
async def metrics(request: Request, _: AuthUser = Depends(get_admin_user)) -> dict:
    service = get_service(request)
    llm = get_llm(request)
    return {
        "metrics": service.get_metrics_snapshot(),
        "model_label": service.llm_label,
        "model": llm.model,
        "projects": service.projects.config_store.list_summaries(),
        "storage": service.get_storage_info(),
        "extensions": service.get_extensions_info(),
        "ingress": {
            "auth": bool(service.config.ingress.api_key.strip()),
            "queue": service.get_ingress_queue_info(),
            "routes": service.list_routes(),
        },
    }


@router.get("/knowledge/repos")
async def knowledge_repos(
    request: Request,
    project: ProjectContext = Depends(get_project_context),
    _: AuthUser = Depends(get_current_user),
) -> dict:
    service = get_service(request)
    return {
        "project_id": project.project_id,
        "repos": service.list_project_git_repos(project),
    }


@router.post("/knowledge/sync")
async def knowledge_sync(
    request: Request,
    project: ProjectContext = Depends(get_project_context),
    _: AuthUser = Depends(get_current_user),
) -> dict:
    service = get_service(request)
    try:
        results = service.sync_project_knowledge(project)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "project_id": project.project_id,
        "synced": [
            {
                "repo_id": item.repo_id,
                "action": item.action,
                "workspace_path": item.workspace_path,
                "branch": item.branch,
            }
            for item in results
        ],
    }


@router.get("/skills")
async def skills_list(
    request: Request,
    project: ProjectContext = Depends(get_project_context),
    _: AuthUser = Depends(get_current_user),
) -> dict:
    service = get_service(request)
    return {
        "project_id": project.project_id,
        "skills": [
            {"name": s.name, "source": s.source, "path": s.path}
            for s in service.list_project_skills(project)
        ],
    }


@router.post("/skills/reload")
async def skills_reload(
    request: Request,
    project: ProjectContext = Depends(get_project_context),
    _: AuthUser = Depends(get_current_user),
) -> dict:
    service = get_service(request)
    try:
        published = service.reload_project_skills(project)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"project_id": project.project_id, "published": published}


@router.get("/storage/info")
async def storage_info(request: Request, _: AuthUser = Depends(get_current_user)) -> dict:
    return get_service(request).get_storage_info()
