from __future__ import annotations

import uuid
from typing import Any, Callable

from deepticket.layers.storage.base import StorageBackend
from deepticket.layers.storage.json_index import index_json_key, list_indexed_json_keys
from deepticket.utils.time import utc_now_iso

_NS_RUNS = "token_usage_runs"
_NS_CHAT_USAGE = "chat_usage"


class TokenUsageStore:
    """Token 用量：按对话累计 + 每次 Agent 运行的增量记录。"""

    def __init__(self, storage: StorageBackend) -> None:
        self.storage = storage

    def record_run(
        self,
        *,
        uid: str,
        username: str,
        chat_id: str,
        chat_title: str,
        agent_conversation_id: str,
        model: str,
        model_label: str,
        delta: dict[str, int],
        cumulative: dict[str, int | str],
    ) -> dict[str, Any]:
        run_id = uuid.uuid4().hex
        now = utc_now_iso()
        doc = {
            "run_id": run_id,
            "uid": uid,
            "username": username,
            "chat_id": chat_id,
            "chat_title": chat_title[:48],
            "agent_conversation_id": agent_conversation_id,
            "model": model,
            "model_label": model_label,
            "prompt_tokens": delta["prompt_tokens"],
            "completion_tokens": delta["completion_tokens"],
            "reasoning_tokens": delta["reasoning_tokens"],
            "total_tokens": delta["total_tokens"],
            "cumulative_prompt_tokens": cumulative["prompt_tokens"],
            "cumulative_completion_tokens": cumulative["completion_tokens"],
            "cumulative_reasoning_tokens": cumulative["reasoning_tokens"],
            "cumulative_total_tokens": cumulative["total_tokens"],
            "recorded_at": now,
        }
        self.storage.set_json(_NS_RUNS, run_id, doc)
        index_json_key(self.storage, _NS_RUNS, run_id, sort_field="recorded_at", doc=doc)
        return doc

    def list_recent_runs(self, *, limit: int = 50) -> list[dict[str, Any]]:
        runs: list[dict[str, Any]] = []
        for key in list_indexed_json_keys(
            self.storage, _NS_RUNS, limit=limit, sort_field="recorded_at"
        ):
            doc = self.storage.get_json(_NS_RUNS, key)
            if doc:
                runs.append(doc)
        return runs

    def list_conversation_usage(
        self,
        *,
        resolve_username: Callable[[str], str | None],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for key in self.storage.list_keys(_NS_CHAT_USAGE):
            doc = self.storage.get_json(_NS_CHAT_USAGE, key)
            if not doc:
                continue
            if int(doc.get("total_tokens") or 0) <= 0:
                continue
            uid = str(doc.get("uid") or "")
            username = resolve_username(uid) or uid[:8]
            items.append(
                {
                    "uid": uid,
                    "username": username,
                    "chat_id": doc.get("chat_id", ""),
                    "chat_title": doc.get("chat_title") or "新会话",
                    "agent_conversation_id": doc.get("agent_conversation_id") or None,
                    "model": doc.get("model") or "",
                    "model_label": doc.get("model_label") or doc.get("model") or "",
                    "prompt_tokens": int(doc.get("prompt_tokens") or 0),
                    "completion_tokens": int(doc.get("completion_tokens") or 0),
                    "reasoning_tokens": int(doc.get("reasoning_tokens") or 0),
                    "total_tokens": int(doc.get("total_tokens") or 0),
                    "updated_at": doc.get("updated_at"),
                }
            )
        items.sort(key=lambda item: item.get("updated_at") or "", reverse=True)
        return items

    @staticmethod
    def summarize_conversations(conversations: list[dict[str, Any]]) -> dict[str, int]:
        summary = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "reasoning_tokens": 0,
            "total_tokens": 0,
            "conversation_count": len(conversations),
        }
        for item in conversations:
            summary["prompt_tokens"] += int(item.get("prompt_tokens") or 0)
            summary["completion_tokens"] += int(item.get("completion_tokens") or 0)
            summary["reasoning_tokens"] += int(item.get("reasoning_tokens") or 0)
            summary["total_tokens"] += int(item.get("total_tokens") or 0)
        return summary
