from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from deepticket.api.deps import get_service
from deepticket.api.schemas import CancelAgentRequest, ChatRequest, OkResponse, TicketRequest
from deepticket.api.streaming import sse_response
from deepticket.auth.dependencies import get_current_user
from deepticket.auth.user_store import AuthUser
from deepticket.layers.input.models import ChatInput, TicketInput
from deepticket.projects.dependencies import get_project_context
from deepticket.projects.registry import ProjectContext

router = APIRouter(prefix="/api", tags=["Agent"])


@router.post("/chat")
async def chat(
    body: ChatRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
    project: ProjectContext = Depends(get_project_context),
):
    service = get_service(request)
    thread = service.chat_history.get_thread(
        project.project_id, user.uid, body.chat_id
    )
    if thread is None:
        raise HTTPException(status_code=404, detail="聊天不存在")

    conversation_id = body.conversation_id or thread.get("agent_conversation_id")
    chunks = service.run_chat_stream(
        ChatInput(
            message=body.message,
            conversation_id=conversation_id,
            image_urls=list(body.image_urls),
        ),
        project=project,
        uid=user.uid,
        chat_id=body.chat_id,
    )
    heartbeat = service.config.web.sse_heartbeat_seconds
    return sse_response(
        chunks,
        conversation_id=conversation_id,
        heartbeat_seconds=heartbeat,
    )


@router.post("/ticket")
async def ticket(
    body: TicketRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
    project: ProjectContext = Depends(get_project_context),
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
        ),
        project=project,
    )
    return sse_response(
        chunks,
        heartbeat_seconds=service.config.web.sse_heartbeat_seconds,
    )


@router.post("/agent/cancel", response_model=OkResponse)
async def cancel_agent(
    body: CancelAgentRequest,
    request: Request,
    _: AuthUser = Depends(get_current_user),
) -> OkResponse:
    service = get_service(request)
    ok = await service.engine.cancel_conversation(body.conversation_id)
    if not ok:
        raise HTTPException(status_code=404, detail="未找到运行中的 Agent 会话")
    return OkResponse()
