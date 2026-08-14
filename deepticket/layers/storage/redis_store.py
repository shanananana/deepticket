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

    def _touch_ttl(self, redis_key: str) -> None:
        if self.ttl_seconds > 0:
            self.client.expire(redis_key, self.ttl_seconds)

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

    def delete_many(self, namespace: str, keys: list[str]) -> None:
        if not keys:
            return
        self.client.delete(*(self._redis_key(namespace, key) for key in keys))

    def list_keys(self, namespace: str) -> list[str]:
        pattern = f"{self.key_prefix}{namespace}:*"
        prefix_len = len(f"{self.key_prefix}{namespace}:")
        keys: list[str] = []
        for full_key in self.client.scan_iter(match=pattern):
            keys.append(full_key[prefix_len:])
        return sorted(keys)

    def hgetall(self, namespace: str, key: str) -> dict[str, str] | None:
        data = self.client.hgetall(self._redis_key(namespace, key))
        if not data:
            return None
        return {str(k): str(v) for k, v in data.items()}

    def hset(self, namespace: str, key: str, mapping: dict[str, str]) -> None:
        if not mapping:
            return
        redis_key = self._redis_key(namespace, key)
        self.client.hset(redis_key, mapping=mapping)
        self._touch_ttl(redis_key)

    def hget(self, namespace: str, key: str, field: str) -> str | None:
        value = self.client.hget(self._redis_key(namespace, key), field)
        return None if value is None else str(value)

    def get_hashes(
        self, namespace: str, keys: list[str]
    ) -> list[dict[str, str] | None]:
        if not keys:
            return []
        pipe = self.client.pipeline(transaction=False)
        for key in keys:
            pipe.hgetall(self._redis_key(namespace, key))
        rows = pipe.execute()
        out: list[dict[str, str] | None] = []
        for data in rows:
            if not data:
                out.append(None)
            else:
                out.append({str(k): str(v) for k, v in data.items()})
        return out

    def zadd(self, namespace: str, key: str, mapping: dict[str, float]) -> None:
        if not mapping:
            return
        redis_key = self._redis_key(namespace, key)
        self.client.zadd(redis_key, mapping)
        self._touch_ttl(redis_key)

    def zrevrange(
        self, namespace: str, key: str, start: int, end: int
    ) -> list[str]:
        return [
            str(item)
            for item in self.client.zrevrange(
                self._redis_key(namespace, key), start, end
            )
        ]

    def zrange(self, namespace: str, key: str, start: int, end: int) -> list[str]:
        return [
            str(item)
            for item in self.client.zrange(self._redis_key(namespace, key), start, end)
        ]

    def zcard(self, namespace: str, key: str) -> int:
        return int(self.client.zcard(self._redis_key(namespace, key)))

    def zrem(self, namespace: str, key: str, *members: str) -> None:
        if not members:
            return
        self.client.zrem(self._redis_key(namespace, key), *members)

    def zremrangebyrank(
        self, namespace: str, key: str, start: int, end: int
    ) -> list[str]:
        redis_key = self._redis_key(namespace, key)
        members = [str(item) for item in self.client.zrange(redis_key, start, end)]
        if members:
            self.client.zremrangebyrank(redis_key, start, end)
        return members
