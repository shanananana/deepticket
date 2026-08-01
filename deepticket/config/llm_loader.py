from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LlmConfig:
    model: str
    api_key: str
    base_url: str
    label: str
