from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OutboundPayload:
    job_id: str
    route_type: str
    source: str
    external_id: str
    status: str
    reply: str = ""
    conversation_id: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OutboundResult:
    method: str
    ok: bool
    detail: str = ""
    response_status: int | None = None
