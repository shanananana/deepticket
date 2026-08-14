from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from deepticket.layers.storage.base import StorageBackend

_ZSET_MARK = "__zset__"


class LocalStorage(StorageBackend):
    """本地文件模拟 Redis JSON / Hash / ZSET。"""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, namespace: str, key: str) -> Path:
        safe_key = key.replace("/", "_")
        directory = self.root / namespace
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{safe_key}.json"

    def get_json(self, namespace: str, key: str) -> dict[str, Any] | None:
        path = self._path(namespace, key)
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and _ZSET_MARK in data:
            return None
        return data

    def set_json(self, namespace: str, key: str, value: dict[str, Any]) -> None:
        path = self._path(namespace, key)
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def delete(self, namespace: str, key: str) -> None:
        path = self._path(namespace, key)
        if path.is_file():
            path.unlink()

    def delete_many(self, namespace: str, keys: list[str]) -> None:
        for key in keys:
            self.delete(namespace, key)

    def list_keys(self, namespace: str) -> list[str]:
        directory = self.root / namespace
        if not directory.is_dir():
            return []
        keys: list[str] = []
        for path in directory.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                keys.append(path.stem)
                continue
            if isinstance(data, dict) and _ZSET_MARK in data:
                continue
            keys.append(path.stem)
        return sorted(keys)

    def hgetall(self, namespace: str, key: str) -> dict[str, str] | None:
        path = self._path(namespace, key)
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or _ZSET_MARK in data:
            return None
        return {str(k): "" if v is None else str(v) for k, v in data.items()}

    def hset(self, namespace: str, key: str, mapping: dict[str, str]) -> None:
        if not mapping:
            return
        current = self.hgetall(namespace, key) or {}
        current.update({str(k): str(v) for k, v in mapping.items()})
        self._path(namespace, key).write_text(
            json.dumps(current, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load_zset(self, namespace: str, key: str) -> dict[str, float]:
        path = self._path(namespace, key)
        if not path.is_file():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or _ZSET_MARK not in data:
            return {}
        raw = data[_ZSET_MARK]
        if not isinstance(raw, dict):
            return {}
        return {str(member): float(score) for member, score in raw.items()}

    def _save_zset(self, namespace: str, key: str, members: dict[str, float]) -> None:
        self._path(namespace, key).write_text(
            json.dumps({_ZSET_MARK: members}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def zadd(self, namespace: str, key: str, mapping: dict[str, float]) -> None:
        if not mapping:
            return
        members = self._load_zset(namespace, key)
        for member, score in mapping.items():
            members[str(member)] = float(score)
        self._save_zset(namespace, key, members)

    def _sorted_members(
        self, namespace: str, key: str, *, reverse: bool
    ) -> list[str]:
        members = self._load_zset(namespace, key)
        return [
            member
            for member, _ in sorted(
                members.items(), key=lambda item: (item[1], item[0]), reverse=reverse
            )
        ]

    @staticmethod
    def _slice(items: list[str], start: int, end: int) -> list[str]:
        if not items:
            return []
        if end == -1:
            stop = None
        else:
            stop = end + 1
        return items[start:stop]

    def zrevrange(
        self, namespace: str, key: str, start: int, end: int
    ) -> list[str]:
        return self._slice(self._sorted_members(namespace, key, reverse=True), start, end)

    def zrange(self, namespace: str, key: str, start: int, end: int) -> list[str]:
        return self._slice(self._sorted_members(namespace, key, reverse=False), start, end)

    def zcard(self, namespace: str, key: str) -> int:
        return len(self._load_zset(namespace, key))

    def zrem(self, namespace: str, key: str, *members: str) -> None:
        if not members:
            return
        data = self._load_zset(namespace, key)
        changed = False
        for member in members:
            if member in data:
                del data[member]
                changed = True
        if changed:
            if data:
                self._save_zset(namespace, key, data)
            else:
                self.delete(namespace, key)

    def zremrangebyrank(
        self, namespace: str, key: str, start: int, end: int
    ) -> list[str]:
        ordered = self._sorted_members(namespace, key, reverse=False)
        removed = self._slice(ordered, start, end)
        if removed:
            self.zrem(namespace, key, *removed)
        return removed
