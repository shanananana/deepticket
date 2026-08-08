from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from deepticket.api.deps import get_service
from deepticket.api.schemas import (
    OkResponse,
    ProjectConfigRequest,
    ProjectExtensionsPatchRequest,
    ProjectKnowledgePatchRequest,
    ProjectMcpPatchRequest,
    ProjectMembersUpdateRequest,
    ProjectMetaPatchRequest,
)
from deepticket.auth.dependencies import get_admin_user
from deepticket.auth.user_store import AuthUser
from deepticket.projects.models import ProjectConfigRecord, ProjectMemberRecord

router = APIRouter(prefix="/api/admin/projects", tags=["Admin Projects"])


def _project_admin_payload(service, project_id: str) -> dict:
    store = service.projects.config_store
    record = store.get(project_id)
    if record is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    members = service.projects.permissions.list_members(project_id)
    raw = store.get_raw(project_id)
    return {
        "project": record.model_dump(mode="json"),
        "raw": raw,
        "in_redis": raw is not None,
        "members": [member.model_dump() for member in members],
        "defaults": store.yaml_fallback(project_id).model_dump(mode="json"),
    }


@router.get("")
async def admin_list_projects(
    request: Request, _: AuthUser = Depends(get_admin_user)
) -> dict:
    service = get_service(request)
    projects = service.projects.config_store.list_summaries()
    items = []
    for summary in projects:
        members = service.projects.permissions.list_members(summary.id)
        raw = service.projects.config_store.get_raw(summary.id)
        items.append(
            {
                **summary.model_dump(),
                "in_redis": raw is not None,
                "members": [member.model_dump() for member in members],
                "config": raw,
            }
        )
    return {"projects": items}


@router.get("/{project_id}")
async def admin_get_project(
    project_id: str,
    request: Request,
    _: AuthUser = Depends(get_admin_user),
) -> dict:
    service = get_service(request)
    return _project_admin_payload(service, project_id)


@router.put("/{project_id}")
async def admin_save_project(
    project_id: str,
    body: ProjectConfigRequest,
    request: Request,
    _: AuthUser = Depends(get_admin_user),
) -> dict:
    if body.id != project_id:
        raise HTTPException(status_code=400, detail="路径 project_id 与 body.id 不一致")
    service = get_service(request)
    try:
        record = ProjectConfigRecord.model_validate(body.model_dump())
        saved = service.projects.save_project(record)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"project": saved.model_dump(mode="json"), "in_redis": True}


@router.patch("/{project_id}")
async def admin_patch_project_meta(
    project_id: str,
    body: ProjectMetaPatchRequest,
    request: Request,
    _: AuthUser = Depends(get_admin_user),
) -> dict:
    service = get_service(request)
    try:
        saved = service.projects.patch_project_meta(
            project_id,
            name=body.name,
            description=body.description,
            enabled=body.enabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"project": saved.model_dump(mode="json"), "in_redis": True}


@router.patch("/{project_id}/knowledge")
async def admin_patch_project_knowledge(
    project_id: str,
    body: ProjectKnowledgePatchRequest,
    request: Request,
    _: AuthUser = Depends(get_admin_user),
) -> dict:
    service = get_service(request)
    try:
        saved = service.projects.patch_project_knowledge(project_id, body.repos)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"project": saved.model_dump(mode="json"), "in_redis": True}


@router.patch("/{project_id}/mcp")
async def admin_patch_project_mcp(
    project_id: str,
    body: ProjectMcpPatchRequest,
    request: Request,
    _: AuthUser = Depends(get_admin_user),
) -> dict:
    service = get_service(request)
    try:
        saved = service.projects.patch_project_mcp(project_id, body.servers)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"project": saved.model_dump(mode="json"), "in_redis": True}


@router.patch("/{project_id}/extensions")
async def admin_patch_project_extensions(
    project_id: str,
    body: ProjectExtensionsPatchRequest,
    request: Request,
    _: AuthUser = Depends(get_admin_user),
) -> dict:
    service = get_service(request)
    try:
        saved = service.projects.patch_project_extensions(
            project_id,
            user_skills_dir=body.user_skills_dir,
            agents_md=body.agents_md,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"project": saved.model_dump(mode="json"), "in_redis": True}


@router.delete("/{project_id}", response_model=OkResponse)
async def admin_delete_project(
    project_id: str,
    request: Request,
    _: AuthUser = Depends(get_admin_user),
) -> OkResponse:
    service = get_service(request)
    if not service.projects.delete_project(project_id):
        raise HTTPException(status_code=400, detail="无法删除该项目")
    return OkResponse()


@router.put("/{project_id}/members")
async def admin_set_project_members(
    project_id: str,
    body: ProjectMembersUpdateRequest,
    request: Request,
    _: AuthUser = Depends(get_admin_user),
) -> dict:
    service = get_service(request)
    if service.projects.config_store.get(project_id) is None:
        raise HTTPException(status_code=404, detail="项目不存在")

    members: list[ProjectMemberRecord] = []
    missing: list[str] = []
    for username in body.usernames:
        clean = username.strip()
        if not clean:
            continue
        lookup = service.storage.get_json("users_by_name", clean.lower())
        if not lookup:
            missing.append(clean)
            continue
        user = service.users.get_user(str(lookup.get("uid") or ""))
        if user is None:
            missing.append(clean)
            continue
        members.append(ProjectMemberRecord(uid=user.uid, username=user.username))

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"用户不存在: {', '.join(missing)}",
        )

    saved = service.projects.permissions.set_members(project_id, members)
    return {"members": [item.model_dump() for item in saved]}
