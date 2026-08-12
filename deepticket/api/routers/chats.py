from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from deepticket.api.deps import get_service
from deepticket.api.schemas import CreateChatRequest, OkResponse, RenameChatRequest
from deepticket.auth.dependencies import get_current_user
from deepticket.auth.user_store import AuthUser
from deepticket.projects.dependencies import get_project_id

router = APIRouter(prefix="/api/chats", tags=["Chats"])


def _chat_payload(thread: dict) -> dict:
    return {
        "chat_id": thread["chat_id"],
        "project_id": thread.get("project_id"),
        "title": thread["title"],
        "messages": thread.get("messages", []),
        "agent_conversation_id": thread.get("agent_conversation_id"),
        "agent_run_status": thread.get("agent_run_status", "idle"),
        "agent_run_error": thread.get("agent_run_error"),
        "created_at": thread.get("created_at"),
        "updated_at": thread.get("updated_at"),
    }


@router.get("")
async def list_chats(
    request: Request,
    project_id: str = Depends(get_project_id),
    user: AuthUser = Depends(get_current_user),
) -> dict:
    service = get_service(request)
    if not service.projects.user_can_access(
        user.uid, project_id, is_admin=service.is_admin(user)
    ):
        raise HTTPException(status_code=403, detail="无权访问该项目")
    return {
        "project_id": project_id,
        "chats": service.chat_history.list_threads(project_id, user.uid),
    }


@router.post("")
async def create_chat(
    body: CreateChatRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    service = get_service(request)
    project_id = body.project_id.strip()
    if not service.projects.user_can_access(
        user.uid, project_id, is_admin=service.is_admin(user)
    ):
        raise HTTPException(status_code=403, detail="无权访问该项目")
    thread = service.chat_history.create_thread(
        project_id, user.uid, title=body.title
    )
    return {"chat": _chat_payload(thread)}


@router.get("/{chat_id}")
async def get_chat(
    chat_id: str,
    request: Request,
    project_id: str = Depends(get_project_id),
    user: AuthUser = Depends(get_current_user),
) -> dict:
    service = get_service(request)
    thread = service.chat_history.get_thread(project_id, user.uid, chat_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="聊天不存在")
    return {"chat": _chat_payload(thread)}


@router.patch("/{chat_id}")
async def rename_chat(
    chat_id: str,
    body: RenameChatRequest,
    request: Request,
    project_id: str = Depends(get_project_id),
    user: AuthUser = Depends(get_current_user),
) -> dict:
    service = get_service(request)
    thread = service.chat_history.rename_thread(
        project_id, user.uid, chat_id, body.title
    )
    if thread is None:
        raise HTTPException(status_code=404, detail="聊天不存在")
    return {"chat": _chat_payload(thread)}


@router.delete("/{chat_id}", response_model=OkResponse)
async def delete_chat(
    chat_id: str,
    request: Request,
    project_id: str = Depends(get_project_id),
    user: AuthUser = Depends(get_current_user),
) -> OkResponse:
    service = get_service(request)
    deleted = service.chat_history.delete_thread(project_id, user.uid, chat_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="聊天不存在")
    return OkResponse()
