from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from deepticket.layers.output.confidence import compute_confidence
from deepticket.layers.output.models import StreamChunk


@dataclass
class IngressJobResult:
    job_id: str
    route_type: str
    source: str
    external_id: str
    status: str
    reply: str
    conversation_id: str | None
    outbound_method: str
    outbound_ok: bool
    outbound_detail: str
    metadata: dict[str, Any]


async def collect_stream_text(
    chunks,
) -> tuple[str, str | None, dict[str, Any] | None]:
    parts: list[str] = []
    activities: list[dict[str, str]] = []
    conversation_id: str | None = None
    confidence: dict[str, Any] | None = None
    async for chunk in chunks:
        if isinstance(chunk, StreamChunk):
            if chunk.conversation_id:
                conversation_id = chunk.conversation_id
            if chunk.activity:
                activities.append(
                    {
                        "text": chunk.activity,
                        "kind": chunk.activity_kind or "default",
                    }
                )
            if chunk.delta:
                parts.append(chunk.delta)
            if chunk.confidence:
                confidence = chunk.confidence
    reply = "".join(parts)
    if confidence is None:
        confidence = compute_confidence(
            activities=activities,
            reply=reply,
            ok=True,
            require_analysis=False,
        )
    return reply, conversation_id, confidence
