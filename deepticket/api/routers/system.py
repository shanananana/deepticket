from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from deepticket.api.deps import get_llm, get_service
from deepticket.auth.dependencies import get_current_user
from deepticket.auth.user_store import AuthUser

router = APIRouter(prefix="/api", tags=["System"])


@router.get("/health")
async def health(request: Request) -> dict:
    service = get_service(request)
    llm = get_llm(request)
    return {
        "ok": True,
        "project": "deepticket",
        "version": "0.1.0",
        "layers": ["input", "output", "engine", "knowledge", "storage"],
        "auth": True,
        "agent_server": (
            f"http://{service.config.engine.agent_server_host}:"
            f"{service.config.engine.agent_server_port}"
        ),
        "model_label": service.llm_label,
        "model": llm.model,
        "gateway_model": f"openhands_{service.config.engine.llm_profile}",
        "profile": service.config.engine.llm_profile,
        "workspace": service.config.knowledge.workspace_dir,
        "storage": service.get_storage_info(),
        "knowledge_repos": service.list_git_repos(),
        "extensions": service.get_extensions_info(),
    }


@router.get("/knowledge/repos")
async def knowledge_repos(request: Request, _: AuthUser = Depends(get_current_user)) -> dict:
    return {"repos": get_service(request).list_git_repos()}


@router.post("/knowledge/sync")
async def knowledge_sync(request: Request, _: AuthUser = Depends(get_current_user)) -> dict:
    try:
        results = get_service(request).sync_knowledge()
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "synced": [
            {
                "repo_id": item.repo_id,
                "action": item.action,
                "workspace_path": item.workspace_path,
                "branch": item.branch,
            }
            for item in results
        ]
    }


@router.get("/skills")
async def skills_list(request: Request, _: AuthUser = Depends(get_current_user)) -> dict:
    service = get_service(request)
    return {
        "skills": [
            {"name": s.name, "source": s.source, "path": s.path}
            for s in service.list_skills()
        ]
    }


@router.post("/skills/reload")
async def skills_reload(request: Request, _: AuthUser = Depends(get_current_user)) -> dict:
    try:
        published = get_service(request).reload_skills()
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"published": published}


@router.get("/storage/info")
async def storage_info(request: Request, _: AuthUser = Depends(get_current_user)) -> dict:
    return get_service(request).get_storage_info()
