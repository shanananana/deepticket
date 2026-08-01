from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from deepticket.api.deps import get_service
from deepticket.api.schemas import CreateChatRequest, OkResponse, RenameChatRequest
from deepticket.auth.dependencies import get_current_user
from deepticket.auth.user_store import AuthUser

router = APIRouter(prefix="/api/chats", tags=["Chats"])


def _chat_payload(thread: dict) -> dict:
    return {
        "chat_id": thread["chat_id"],
        "title": thread["title"],
        "messages": thread.get("messages", []),
        "agent_conversation_id": thread.get("agent_conversation_id"),
        "created_at": thread.get("created_at"),
        "updated_at": thread.get("updated_at"),
    }


@router.get("")
async def list_chats(request: Request, user: AuthUser = Depends(get_current_user)) -> dict:
    return {"chats": get_service(request).chat_history.list_threads(user.uid)}


@router.post("")
async def create_chat(
    body: CreateChatRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    thread = get_service(request).chat_history.create_thread(user.uid, title=body.title)
    return {"chat": _chat_payload(thread)}


@router.get("/{chat_id}")
async def get_chat(
    chat_id: str, request: Request, user: AuthUser = Depends(get_current_user)
) -> dict:
    thread = get_service(request).chat_history.get_thread(user.uid, chat_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="聊天不存在")
    return {"chat": _chat_payload(thread)}


@router.patch("/{chat_id}")
async def rename_chat(
    chat_id: str,
    body: RenameChatRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    thread = get_service(request).chat_history.rename_thread(user.uid, chat_id, body.title)
    if thread is None:
        raise HTTPException(status_code=404, detail="聊天不存在")
    return {"chat": _chat_payload(thread)}


@router.delete("/{chat_id}", response_model=OkResponse)
async def delete_chat(
    chat_id: str,
    request: Request,
    user: AuthUser = Depends(get_current_user),
) -> OkResponse:
    deleted = get_service(request).chat_history.delete_thread(user.uid, chat_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="聊天不存在")
    return OkResponse()
