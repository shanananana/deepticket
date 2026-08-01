from __future__ import annotations

from deepticket.config.redis_url import resolve_redis_url
from deepticket.config.schema import StorageConfig
from deepticket.layers.storage.base import StorageBackend
from deepticket.layers.storage.local import LocalStorage
from deepticket.layers.storage.redis_store import RedisStorage


def create_storage(config: StorageConfig) -> StorageBackend:
    if config.backend == "redis":
        url = resolve_redis_url(
            config.redis.url,
            username=config.redis.username,
            password=config.redis.password,
        )
        return RedisStorage(
            url=url,
            key_prefix=config.redis.key_prefix,
            ttl_seconds=config.redis.ttl_seconds,
        )
    return LocalStorage(root=config.local.root)
