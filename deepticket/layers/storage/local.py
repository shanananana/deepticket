from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from deepticket.layers.storage.base import StorageBackend


class LocalStorage(StorageBackend):
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
        return json.loads(path.read_text(encoding="utf-8"))

    def set_json(self, namespace: str, key: str, value: dict[str, Any]) -> None:
        path = self._path(namespace, key)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

    def delete(self, namespace: str, key: str) -> None:
        path = self._path(namespace, key)
        if path.is_file():
            path.unlink()

    def list_keys(self, namespace: str) -> list[str]:
        directory = self.root / namespace
        if not directory.is_dir():
            return []
        return sorted(path.stem for path in directory.glob("*.json"))
