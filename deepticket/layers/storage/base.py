from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StorageBackend(ABC):
    """存储层抽象：会话 / 工单 / 任意 JSON 文档。"""

    @abstractmethod
    def get_json(self, namespace: str, key: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def set_json(self, namespace: str, key: str, value: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, namespace: str, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_keys(self, namespace: str) -> list[str]:
        raise NotImplementedError

    def _full_key(self, namespace: str, key: str) -> str:
        return f"{namespace}:{key}"
