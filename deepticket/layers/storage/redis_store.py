from __future__ import annotations

import json
from typing import Any

import redis

from deepticket.layers.storage.base import StorageBackend


class RedisStorage(StorageBackend):
    def __init__(
        self,
        url: str,
        key_prefix: str = "deepticket:",
        *,
        ttl_seconds: int = 31_536_000,
    ) -> None:
        self.client = redis.Redis.from_url(url, decode_responses=True)
        self.key_prefix = key_prefix.rstrip(":") + ":"
        self.ttl_seconds = max(0, int(ttl_seconds))

    def _redis_key(self, namespace: str, key: str) -> str:
        return f"{self.key_prefix}{namespace}:{key}"

    def get_json(self, namespace: str, key: str) -> dict[str, Any] | None:
        raw = self.client.get(self._redis_key(namespace, key))
        if raw is None:
            return None
        return json.loads(raw)

    def set_json(self, namespace: str, key: str, value: dict[str, Any]) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        redis_key = self._redis_key(namespace, key)
        if self.ttl_seconds > 0:
            self.client.set(redis_key, payload, ex=self.ttl_seconds)
        else:
            self.client.set(redis_key, payload)

    def delete(self, namespace: str, key: str) -> None:
        self.client.delete(self._redis_key(namespace, key))

    def list_keys(self, namespace: str) -> list[str]:
        pattern = f"{self.key_prefix}{namespace}:*"
        prefix_len = len(f"{self.key_prefix}{namespace}:")
        keys: list[str] = []
        for full_key in self.client.scan_iter(match=pattern):
            keys.append(full_key[prefix_len:])
        return sorted(keys)
