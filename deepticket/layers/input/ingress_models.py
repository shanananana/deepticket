from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IngressEvent:
    """外部系统推送的统一输入结构。"""

    source: str
    external_id: str
    title: str
    body: str
    type: str | None = None
    repo_ids: list[str] = field(default_factory=list)
    logs: str = ""
    image_urls: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
