from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StreamChunk:
    delta: str = ""
    conversation_id: str | None = None
    done: bool = False
    activity: str | None = None
    activity_kind: str | None = None
