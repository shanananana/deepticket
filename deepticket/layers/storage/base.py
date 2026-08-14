from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StorageBackend(ABC):
    """存储层抽象：JSON 文档 + Hash / ZSET（聊天结构化存储）。"""

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

    def hgetall(self, namespace: str, key: str) -> dict[str, str] | None:
        raise NotImplementedError(f"{type(self).__name__} 不支持 Hash")

    def hset(self, namespace: str, key: str, mapping: dict[str, str]) -> None:
        raise NotImplementedError(f"{type(self).__name__} 不支持 Hash")

    def hget(self, namespace: str, key: str, field: str) -> str | None:
        data = self.hgetall(namespace, key)
        if data is None:
            return None
        return data.get(field)

    def get_hashes(
        self, namespace: str, keys: list[str]
    ) -> list[dict[str, str] | None]:
        return [self.hgetall(namespace, key) for key in keys]

    def zadd(self, namespace: str, key: str, mapping: dict[str, float]) -> None:
        raise NotImplementedError(f"{type(self).__name__} 不支持 ZSET")

    def zrevrange(
        self, namespace: str, key: str, start: int, end: int
    ) -> list[str]:
        raise NotImplementedError(f"{type(self).__name__} 不支持 ZSET")

    def zrange(self, namespace: str, key: str, start: int, end: int) -> list[str]:
        raise NotImplementedError(f"{type(self).__name__} 不支持 ZSET")

    def zcard(self, namespace: str, key: str) -> int:
        raise NotImplementedError(f"{type(self).__name__} 不支持 ZSET")

    def zrem(self, namespace: str, key: str, *members: str) -> None:
        raise NotImplementedError(f"{type(self).__name__} 不支持 ZSET")

    def zremrangebyrank(
        self, namespace: str, key: str, start: int, end: int
    ) -> list[str]:
        """删除 rank 区间内的成员，返回被删 member 列表。"""
        raise NotImplementedError(f"{type(self).__name__} 不支持 ZSET")

    def delete_many(self, namespace: str, keys: list[str]) -> None:
        for key in keys:
            self.delete(namespace, key)

    def _full_key(self, namespace: str, key: str) -> str:
        return f"{namespace}:{key}"
