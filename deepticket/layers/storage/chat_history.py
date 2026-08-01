from __future__ import annotations

import uuid
from typing import Any

from deepticket.layers.storage.base import StorageBackend
from deepticket.utils.time import utc_now_iso

_NS_THREADS = "chat_threads"
_NS_INDEX = "chat_index"
_TITLE_MAX = 48


class ChatHistoryStore:
    """按 uid 隔离的聊天线程与消息历史。"""

    def __init__(self, storage: StorageBackend) -> None:
        self.storage = storage

    def list_threads(self, uid: str) -> list[dict[str, Any]]:
        index = self._load_index(uid)
        items = index.get("threads", [])
        return sorted(
            items,
            key=lambda item: item.get("updated_at", ""),
            reverse=True,
        )

    def get_thread(self, uid: str, chat_id: str) -> dict[str, Any] | None:
        doc = self.storage.get_json(_NS_THREADS, self._thread_key(uid, chat_id))
        if not doc or doc.get("uid") != uid:
            return None
        return doc

    def create_thread(self, uid: str, *, title: str = "新会话") -> dict[str, Any]:
        chat_id = uuid.uuid4().hex
        now = utc_now_iso()
        doc = {
            "chat_id": chat_id,
            "uid": uid,
            "title": title[:_TITLE_MAX],
            "messages": [],
            "agent_conversation_id": None,
            "created_at": now,
            "updated_at": now,
        }
        self.storage.set_json(_NS_THREADS, self._thread_key(uid, chat_id), doc)
        self._upsert_index(uid, chat_id, doc["title"], now)
        return doc

    def delete_thread(self, uid: str, chat_id: str) -> bool:
        doc = self.get_thread(uid, chat_id)
        if not doc:
            return False
        self.storage.delete(_NS_THREADS, self._thread_key(uid, chat_id))
        index = self._load_index(uid)
        threads = [
            item
            for item in index.get("threads", [])
            if item.get("chat_id") != chat_id
        ]
        self.storage.set_json(_NS_INDEX, uid, {"threads": threads})
        return True

    def append_message(
        self,
        uid: str,
        chat_id: str,
        *,
        role: str,
        content: str,
        agent_conversation_id: str | None = None,
    ) -> dict[str, Any]:
        doc = self.get_thread(uid, chat_id)
        if not doc:
            raise KeyError(f"chat not found: {chat_id}")

        now = utc_now_iso()
        doc["messages"].append(
            {
                "role": role,
                "content": content,
                "created_at": now,
            }
        )
        doc["updated_at"] = now
        if agent_conversation_id:
            doc["agent_conversation_id"] = agent_conversation_id

        if role == "user" and (
            doc["title"] == "新会话" or len(doc["title"].strip()) == 0
        ):
            doc["title"] = _title_from_message(content)

        self.storage.set_json(_NS_THREADS, self._thread_key(uid, chat_id), doc)
        self._upsert_index(uid, chat_id, doc["title"], now)
        return doc

    def rename_thread(self, uid: str, chat_id: str, title: str) -> dict[str, Any] | None:
        doc = self.get_thread(uid, chat_id)
        if not doc:
            return None
        clean = " ".join(title.strip().split())[:_TITLE_MAX]
        if not clean:
            return doc
        doc["title"] = clean
        doc["updated_at"] = utc_now_iso()
        self.storage.set_json(_NS_THREADS, self._thread_key(uid, chat_id), doc)
        self._upsert_index(uid, chat_id, clean, doc["updated_at"])
        return doc

    def set_agent_conversation_id(
        self, uid: str, chat_id: str, agent_conversation_id: str
    ) -> None:
        doc = self.get_thread(uid, chat_id)
        if not doc:
            raise KeyError(f"chat not found: {chat_id}")
        doc["agent_conversation_id"] = agent_conversation_id
        doc["updated_at"] = utc_now_iso()
        self.storage.set_json(_NS_THREADS, self._thread_key(uid, chat_id), doc)

    @staticmethod
    def _thread_key(uid: str, chat_id: str) -> str:
        return f"{uid}:{chat_id}"

    def _load_index(self, uid: str) -> dict[str, Any]:
        return self.storage.get_json(_NS_INDEX, uid) or {"threads": []}

    def _upsert_index(
        self, uid: str, chat_id: str, title: str, updated_at: str
    ) -> None:
        index = self._load_index(uid)
        threads = [
            item for item in index.get("threads", []) if item.get("chat_id") != chat_id
        ]
        threads.append(
            {
                "chat_id": chat_id,
                "title": title[:_TITLE_MAX],
                "updated_at": updated_at,
            }
        )
        self.storage.set_json(_NS_INDEX, uid, {"threads": threads})


def _title_from_message(message: str) -> str:
    text = " ".join(message.strip().split())
    if not text:
        return "新会话"
    return text[:_TITLE_MAX]
