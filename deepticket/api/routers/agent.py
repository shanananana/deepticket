from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from deepticket.api.deps import get_service
from deepticket.api.schemas import ChatRequest, TicketRequest
from deepticket.api.streaming import sse_response
from deepticket.auth.dependencies import get_current_user
from deepticket.auth.user_store import AuthUser
from deepticket.layers.input.models import ChatInput, TicketInput

router = APIRouter(prefix="/api", tags=["Agent"])


@router.post("/chat")
async def chat(
    body: ChatRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
):
    service = get_service(request)
    thread = service.chat_history.get_thread(user.uid, body.chat_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="聊天不存在")

    conversation_id = body.conversation_id or thread.get("agent_conversation_id")
    chunks = service.run_chat_stream(
        ChatInput(
            message=body.message,
            conversation_id=conversation_id,
            image_urls=list(body.image_urls),
        ),
        uid=user.uid,
        chat_id=body.chat_id,
    )
    return sse_response(chunks, conversation_id=conversation_id)


@router.post("/ticket")
async def ticket(
    body: TicketRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
):
    service = get_service(request)
    chunks = service.run_ticket_stream(
        TicketInput(
            ticket_id=body.ticket_id,
            title=body.title,
            description=body.description,
            repo_ids=body.repo_ids,
            logs=body.logs,
            image_urls=list(body.image_urls),
        )
    )
    return sse_response(chunks)
