from __future__ import annotations

import time
from typing import Any

from deepticket.layers.storage.base import StorageBackend

_INDEX_MEMBER = "__index__"


def _score_from_doc(doc: dict[str, Any], *, field: str) -> float:
    raw = doc.get(field)
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str) and raw:
        try:
            return float(time.mktime(time.strptime(raw[:19], "%Y-%m-%dT%H:%M:%S")) * 1000)
        except ValueError:
            pass
    return time.time() * 1000.0


def index_json_key(
    storage: StorageBackend,
    namespace: str,
    key: str,
    *,
    sort_field: str = "recorded_at",
    doc: dict[str, Any] | None = None,
) -> None:
    """将 JSON 文档 key 写入 namespace 内 ZSET 索引（member=__index__）。"""
    score = _score_from_doc(doc or {}, field=sort_field) if doc else time.time() * 1000.0
    storage.zadd(namespace, _INDEX_MEMBER, {key: score})


def list_indexed_json_keys(
    storage: StorageBackend,
    namespace: str,
    *,
    limit: int,
    sort_field: str = "recorded_at",
) -> list[str]:
    """按索引取最近 limit 个 key；索引为空时回退 SCAN 并惰性重建。"""
    indexed = storage.zrevrange(namespace, _INDEX_MEMBER, 0, max(0, limit - 1))
    if indexed:
        return indexed
    keys = storage.list_keys(namespace)
    if not keys:
        return []
    if _INDEX_MEMBER in keys:
        keys = [item for item in keys if item != _INDEX_MEMBER]
    scored: list[tuple[float, str]] = []
    for key in keys:
        doc = storage.get_json(namespace, key)
        if not doc:
            continue
        scored.append((_score_from_doc(doc, field=sort_field), key))
    scored.sort(key=lambda item: item[0], reverse=True)
    for score, key in scored[: max(limit, 50)]:
        storage.zadd(namespace, _INDEX_MEMBER, {key: score})
    return [key for _, key in scored[:limit]]


def count_indexed_keys(storage: StorageBackend, namespace: str) -> int:
    count = storage.zcard(namespace, _INDEX_MEMBER)
    if count:
        return count
    keys = storage.list_keys(namespace)
    return len([item for item in keys if item != _INDEX_MEMBER])
