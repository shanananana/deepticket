from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi.responses import StreamingResponse

from deepticket.layers.output.adapter import OutputAdapter
from deepticket.layers.output.models import StreamChunk


async def iter_sse_chunks(chunks: AsyncIterator[StreamChunk]) -> AsyncIterator[str]:
    sent_meta = False
    try:
        async for chunk in chunks:
            if chunk.conversation_id and not sent_meta:
                sent_meta = True
                yield OutputAdapter.sse_meta_event(chunk.conversation_id)
            if chunk.delta:
                payload = {
                    "choices": [{"delta": {"content": chunk.delta}, "index": 0}]
                }
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            if chunk.activity:
                activity = json.dumps({"activity": chunk.activity}, ensure_ascii=False)
                yield f"event: activity\ndata: {activity}\n\n"
            if chunk.done:
                yield "data: [DONE]\n\n"
    except RuntimeError as exc:
        yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"


def sse_response(
    chunks: AsyncIterator[StreamChunk],
    *,
    conversation_id: str | None = None,
) -> StreamingResponse:
    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
    if conversation_id:
        headers["X-OpenHands-ServerConversation-ID"] = conversation_id
    return StreamingResponse(
        iter_sse_chunks(chunks),
        media_type="text/event-stream",
        headers=headers,
    )
