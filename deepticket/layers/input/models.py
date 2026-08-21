from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatInput:
    message: str
    conversation_id: str | None = None
    image_urls: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TicketInput:
    ticket_id: str
    title: str
    description: str
    repo_ids: list[str] = field(default_factory=list)
    logs: str = ""
    image_urls: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentInput:
    """输入层统一结构。"""

    prompt: str
    conversation_id: str | None = None
    source: str = "chat"
    ticket_id: str | None = None
    repo_ids: list[str] = field(default_factory=list)
    image_urls: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    workspace_dir: str | None = None
    mcp_config: dict[str, Any] | None = None
    agents_md: str = ""
    history_messages: list[dict[str, str]] = field(default_factory=list)
