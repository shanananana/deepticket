from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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


async def collect_stream_text(chunks) -> tuple[str, str | None]:
    parts: list[str] = []
    conversation_id: str | None = None
    async for chunk in chunks:
        if isinstance(chunk, StreamChunk):
            if chunk.conversation_id:
                conversation_id = chunk.conversation_id
            if chunk.delta:
                parts.append(chunk.delta)
    return "".join(parts), conversation_id
