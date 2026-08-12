from __future__ import annotations

import uuid
from typing import Any

from deepticket.layers.storage.base import StorageBackend
from deepticket.projects.store import ProjectConfigStore
from deepticket.utils.time import utc_now_iso

_NS_THREADS = "chat_threads"
_NS_INDEX = "chat_index"
_TITLE_MAX = 48
_SEARCH_MAX = 4000
_MAX_MESSAGES = 200


class ChatHistoryStore:
    """按 project + uid 隔离的聊天线程与消息历史。"""

    def __init__(self, storage: StorageBackend) -> None:
        self.storage = storage

    @staticmethod
    def default_project_id() -> str:
        return ProjectConfigStore.default_project_id()

    def list_threads(self, project_id: str, uid: str) -> list[dict[str, Any]]:
        index = self._load_index(project_id, uid)
        items = index.get("threads", [])
        return sorted(
            items,
            key=lambda item: item.get("updated_at", ""),
            reverse=True,
        )

    def get_thread(
        self, project_id: str, uid: str, chat_id: str
    ) -> dict[str, Any] | None:
        doc = self.storage.get_json(
            _NS_THREADS, self._thread_key(project_id, uid, chat_id)
        )
        if not doc or doc.get("uid") != uid:
            return None
        if doc.get("project_id") and doc.get("project_id") != project_id:
            return None
        return doc

    def create_thread(
        self,
        project_id: str,
        uid: str,
        *,
        title: str = "新会话",
    ) -> dict[str, Any]:
        chat_id = uuid.uuid4().hex
        now = utc_now_iso()
        doc = {
            "chat_id": chat_id,
            "project_id": project_id,
            "uid": uid,
            "title": title[:_TITLE_MAX],
            "messages": [],
            "agent_conversation_id": None,
            "created_at": now,
            "updated_at": now,
        }
        self.storage.set_json(
            _NS_THREADS, self._thread_key(project_id, uid, chat_id), doc
        )
        self._upsert_index(project_id, uid, chat_id, doc["title"], now, search_text="")
        return doc

    def delete_thread(self, project_id: str, uid: str, chat_id: str) -> bool:
        doc = self.get_thread(project_id, uid, chat_id)
        if not doc:
            return False
        self.storage.delete(
            _NS_THREADS, self._thread_key(project_id, uid, chat_id)
        )
        index = self._load_index(project_id, uid)
        threads = [
            item
            for item in index.get("threads", [])
            if item.get("chat_id") != chat_id
        ]
        self.storage.set_json(_NS_INDEX, self._index_key(project_id, uid), {"threads": threads})
        return True

    def append_message(
        self,
        project_id: str,
        uid: str,
        chat_id: str,
        *,
        role: str,
        content: str,
        agent_conversation_id: str | None = None,
        activities: list[dict[str, str]] | None = None,
        confidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        doc = self.get_thread(project_id, uid, chat_id)
        if not doc:
            raise KeyError(f"chat not found: {chat_id}")

        now = utc_now_iso()
        message: dict[str, Any] = {
            "role": role,
            "content": content,
            "created_at": now,
        }
        if activities:
            message["activities"] = activities
        if confidence:
            message["confidence"] = confidence
        doc["messages"].append(message)
        if len(doc["messages"]) > _MAX_MESSAGES:
            doc["messages"] = doc["messages"][-_MAX_MESSAGES:]
        doc["updated_at"] = now
        if agent_conversation_id:
            doc["agent_conversation_id"] = agent_conversation_id

        if role == "user" and (
            doc["title"] == "新会话" or len(doc["title"].strip()) == 0
        ):
            doc["title"] = _title_from_message(content)

        self.storage.set_json(
            _NS_THREADS, self._thread_key(project_id, uid, chat_id), doc
        )
        self._upsert_index(
            project_id,
            uid,
            chat_id,
            doc["title"],
            now,
            search_text=self._build_search_text(doc),
        )
        return doc

    def rename_thread(
        self, project_id: str, uid: str, chat_id: str, title: str
    ) -> dict[str, Any] | None:
        doc = self.get_thread(project_id, uid, chat_id)
        if not doc:
            return None
        clean = " ".join(title.strip().split())[:_TITLE_MAX]
        if not clean:
            return doc
        doc["title"] = clean
        doc["updated_at"] = utc_now_iso()
        self.storage.set_json(
            _NS_THREADS, self._thread_key(project_id, uid, chat_id), doc
        )
        self._upsert_index(
            project_id,
            uid,
            chat_id,
            clean,
            doc["updated_at"],
            search_text=self._build_search_text(doc),
        )
        return doc

    def set_agent_conversation_id(
        self, project_id: str, uid: str, chat_id: str, agent_conversation_id: str
    ) -> None:
        doc = self.get_thread(project_id, uid, chat_id)
        if not doc:
            raise KeyError(f"chat not found: {chat_id}")
        doc["agent_conversation_id"] = agent_conversation_id
        doc["updated_at"] = utc_now_iso()
        self.storage.set_json(
            _NS_THREADS, self._thread_key(project_id, uid, chat_id), doc
        )

    def set_agent_run_status(
        self,
        project_id: str,
        uid: str,
        chat_id: str,
        *,
        status: str,
        error: str | None = None,
    ) -> None:
        doc = self.get_thread(project_id, uid, chat_id)
        if not doc:
            raise KeyError(f"chat not found: {chat_id}")
        doc["agent_run_status"] = status
        if error:
            doc["agent_run_error"] = error[:500]
        elif "agent_run_error" in doc:
            doc.pop("agent_run_error", None)
        doc["updated_at"] = utc_now_iso()
        self.storage.set_json(
            _NS_THREADS, self._thread_key(project_id, uid, chat_id), doc
        )

    def set_token_usage(
        self,
        project_id: str,
        uid: str,
        chat_id: str,
        *,
        prompt_tokens: int,
        completion_tokens: int,
        reasoning_tokens: int,
        total_tokens: int,
        model: str = "",
        model_label: str = "",
    ) -> dict[str, Any]:
        doc = self.get_thread(project_id, uid, chat_id)
        if not doc:
            raise KeyError(f"chat not found: {chat_id}")
        now = utc_now_iso()
        doc["token_usage"] = {
            "prompt_tokens": max(0, prompt_tokens),
            "completion_tokens": max(0, completion_tokens),
            "reasoning_tokens": max(0, reasoning_tokens),
            "total_tokens": max(0, total_tokens),
            "model": model,
            "model_label": model_label,
            "updated_at": now,
        }
        doc["updated_at"] = now
        self.storage.set_json(
            _NS_THREADS, self._thread_key(project_id, uid, chat_id), doc
        )
        return doc

    @staticmethod
    def _thread_key(project_id: str, uid: str, chat_id: str) -> str:
        return f"{project_id}:{uid}:{chat_id}"

    @staticmethod
    def _index_key(project_id: str, uid: str) -> str:
        return f"{project_id}:{uid}"

    def _load_index(self, project_id: str, uid: str) -> dict[str, Any]:
        return self.storage.get_json(_NS_INDEX, self._index_key(project_id, uid)) or {
            "threads": []
        }

    def _upsert_index(
        self,
        project_id: str,
        uid: str,
        chat_id: str,
        title: str,
        updated_at: str,
        *,
        search_text: str,
    ) -> None:
        index = self._load_index(project_id, uid)
        threads = [
            item for item in index.get("threads", []) if item.get("chat_id") != chat_id
        ]
        threads.append(
            {
                "chat_id": chat_id,
                "title": title[:_TITLE_MAX],
                "updated_at": updated_at,
                "search_text": search_text[:_SEARCH_MAX],
            }
        )
        self.storage.set_json(
            _NS_INDEX, self._index_key(project_id, uid), {"threads": threads}
        )

    @staticmethod
    def _build_search_text(doc: dict[str, Any]) -> str:
        parts = [doc.get("title") or ""]
        for item in doc.get("messages") or []:
            content = item.get("content")
            if isinstance(content, str) and content.strip():
                parts.append(content.strip())
            for act in item.get("activities") or []:
                text = act.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        blob = " ".join(parts)
        return blob[:_SEARCH_MAX]


def _title_from_message(message: str) -> str:
    text = " ".join(message.strip().split())
    if not text:
        return "新会话"
    return text[:_TITLE_MAX]
