from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi.responses import StreamingResponse

from deepticket.layers.output.adapter import OutputAdapter
from deepticket.layers.output.models import StreamChunk

_SSE_FLUSH = ": " + ("." * 2048) + "\n\n"
_DEFAULT_HEARTBEAT_SECONDS = 15.0
_HEARTBEAT_ACTIVITY = "仍在分析…"
_HEARTBEAT_KIND = "system"
_HEARTBEAT_COMMENT = ": heartbeat\n\n"


async def _iter_with_idle_heartbeat(
    chunks: AsyncIterator[StreamChunk],
    *,
    interval: float = _DEFAULT_HEARTBEAT_SECONDS,
) -> AsyncIterator[StreamChunk]:
    """chunk 流空闲超过 interval 时注入固定 activity，避免网关断连。"""
    chunk_iter = chunks.__aiter__()
    pending: asyncio.Task[StreamChunk] | None = None

    try:
        while True:
            if pending is None:
                pending = asyncio.create_task(chunk_iter.__anext__())
            done, _ = await asyncio.wait({pending}, timeout=interval)
            if pending in done:
                try:
                    chunk = pending.result()
                except StopAsyncIteration:
                    break
                pending = None
                yield chunk
                if chunk.done:
                    break
                continue
            yield StreamChunk(
                activity=_HEARTBEAT_ACTIVITY,
                activity_kind=_HEARTBEAT_KIND,
            )
    finally:
        if pending is not None and not pending.done():
            pending.cancel()
            with asyncio.suppress(asyncio.CancelledError, StopAsyncIteration):
                await pending


async def iter_sse_chunks(
    chunks: AsyncIterator[StreamChunk],
    *,
    heartbeat_seconds: float = _DEFAULT_HEARTBEAT_SECONDS,
) -> AsyncIterator[str]:
    sent_meta = False
    idle_interval = heartbeat_seconds if heartbeat_seconds > 0 else _DEFAULT_HEARTBEAT_SECONDS
    async for chunk in _iter_with_idle_heartbeat(chunks, interval=idle_interval):
        if chunk.conversation_id and not sent_meta:
            sent_meta = True
            yield OutputAdapter.sse_meta_event(chunk.conversation_id)
            yield _SSE_FLUSH

        if chunk.activity:
            if chunk.activity == _HEARTBEAT_ACTIVITY and chunk.activity_kind == _HEARTBEAT_KIND:
                yield _HEARTBEAT_COMMENT
            payload = {"activity": chunk.activity}
            if chunk.activity_kind:
                payload["kind"] = chunk.activity_kind
            activity = json.dumps(payload, ensure_ascii=False)
            yield f"event: activity\ndata: {activity}\n\n"
            yield _SSE_FLUSH
            await asyncio.sleep(0)

        if chunk.confidence:
            confidence = json.dumps(chunk.confidence, ensure_ascii=False)
            yield f"event: confidence\ndata: {confidence}\n\n"
            yield _SSE_FLUSH
            await asyncio.sleep(0)

        if chunk.delta:
            payload = {
                "choices": [{"delta": {"content": chunk.delta}, "index": 0}]
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            yield _SSE_FLUSH
            await asyncio.sleep(0)

        if chunk.done:
            yield "data: [DONE]\n\n"


def sse_response(
    chunks: AsyncIterator[StreamChunk],
    *,
    conversation_id: str | None = None,
    heartbeat_seconds: float = _DEFAULT_HEARTBEAT_SECONDS,
) -> StreamingResponse:
    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    if conversation_id:
        headers["X-OpenHands-ServerConversation-ID"] = conversation_id
    return StreamingResponse(
        iter_sse_chunks(chunks, heartbeat_seconds=heartbeat_seconds),
        media_type="text/event-stream",
        headers=headers,
    )
