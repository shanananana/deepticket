from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StreamChunk:
    delta: str = ""
    conversation_id: str | None = None
    done: bool = False
    activity: str | None = None
    activity_kind: str | None = None
    confidence: dict[str, Any] | None = field(default=None)
