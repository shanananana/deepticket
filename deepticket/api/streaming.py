from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi.responses import StreamingResponse

from deepticket.layers.output.adapter import OutputAdapter
from deepticket.layers.output.models import StreamChunk

# 部分反向代理/浏览器会缓冲小 SSE 包；注释行垫片强制尽快刷到客户端
_SSE_FLUSH = ": " + ("." * 2048) + "\n\n"
_DEFAULT_HEARTBEAT_SECONDS = 15.0


async def iter_sse_chunks(
    chunks: AsyncIterator[StreamChunk],
    *,
    heartbeat_seconds: float = _DEFAULT_HEARTBEAT_SECONDS,
) -> AsyncIterator[str]:
    sent_meta = False
    chunk_queue: asyncio.Queue[tuple[str, object]] = asyncio.Queue()

    async def feed() -> None:
        try:
            async for chunk in chunks:
                await chunk_queue.put(("chunk", chunk))
        except Exception as exc:
            await chunk_queue.put(("error", exc))
        finally:
            await chunk_queue.put(("end", None))

    feeder = asyncio.create_task(feed())
    try:
        while True:
            try:
                if heartbeat_seconds > 0:
                    kind, item = await asyncio.wait_for(
                        chunk_queue.get(),
                        timeout=heartbeat_seconds,
                    )
                else:
                    kind, item = await chunk_queue.get()
            except TimeoutError:
                yield "event: ping\ndata: {}\n\n"
                continue

            if kind == "end":
                break
            if kind == "error":
                raise item  # type: ignore[misc]

            chunk = item
            assert isinstance(chunk, StreamChunk)

            if chunk.conversation_id and not sent_meta:
                sent_meta = True
                yield OutputAdapter.sse_meta_event(chunk.conversation_id)
                yield _SSE_FLUSH

            if chunk.activity:
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
    except RuntimeError as exc:
        yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"
    finally:
        feeder.cancel()
        try:
            await feeder
        except asyncio.CancelledError:
            pass


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
