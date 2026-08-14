from __future__ import annotations

import json
import time
import uuid
from typing import Any

from deepticket.layers.storage.base import StorageBackend
from deepticket.projects.store import ProjectConfigStore
from deepticket.utils.time import utc_now_iso

_NS_CHATS = "chats"
_NS_CHAT = "chat"
_NS_CHAT_MSGS = "chat_msgs"
_NS_MSG = "msg"
_NS_CHAT_USAGE = "chat_usage"

_TITLE_MAX = 48
_SEARCH_MAX = 4000
_MAX_MESSAGES = 200


class ChatHistoryStore:
    """按 project + uid 隔离的聊天：会话 ZSET + 会话 Hash + 消息 ZSET/Hash。"""

    def __init__(self, storage: StorageBackend) -> None:
        self.storage = storage

    @staticmethod
    def default_project_id() -> str:
        return ProjectConfigStore.default_project_id()

    def list_threads(self, project_id: str, uid: str) -> list[dict[str, Any]]:
        chat_ids = self.storage.zrevrange(_NS_CHATS, self._chats_key(project_id, uid), 0, -1)
        if not chat_ids:
            return []
        metas = self.storage.get_hashes(
            _NS_CHAT, [self._chat_key(project_id, uid, chat_id) for chat_id in chat_ids]
        )
        items: list[dict[str, Any]] = []
        for chat_id, meta in zip(chat_ids, metas, strict=False):
            if not meta or meta.get("uid") != uid:
                continue
            if meta.get("project_id") and meta.get("project_id") != project_id:
                continue
            items.append(
                {
                    "chat_id": chat_id,
                    "title": meta.get("title") or "新会话",
                    "updated_at": meta.get("updated_at") or "",
                    "search_text": meta.get("search_text") or "",
                }
            )
        return items

    def get_thread(
        self, project_id: str, uid: str, chat_id: str
    ) -> dict[str, Any] | None:
        meta = self._load_chat_meta(project_id, uid, chat_id)
        if meta is None:
            return None
        msg_ids = self.storage.zrange(
            _NS_CHAT_MSGS, self._msgs_key(project_id, uid, chat_id), 0, -1
        )
        messages = self._load_messages(project_id, uid, chat_id, msg_ids)
        return self._thread_from_meta(meta, messages)

    def get_thread_summary(
        self, project_id: str, uid: str, chat_id: str
    ) -> dict[str, Any] | None:
        """会话元数据（不含消息正文），供 token / 状态等轻量读取。"""
        meta = self._load_chat_meta(project_id, uid, chat_id)
        if meta is None:
            return None
        return self._thread_from_meta(meta, [])

    def get_status(
        self, project_id: str, uid: str, chat_id: str
    ) -> dict[str, Any] | None:
        meta = self._load_chat_meta(project_id, uid, chat_id)
        if meta is None:
            return None
        msgs_key = self._msgs_key(project_id, uid, chat_id)
        message_count = self.storage.zcard(_NS_CHAT_MSGS, msgs_key)
        latest = None
        if message_count:
            latest_ids = self.storage.zrange(_NS_CHAT_MSGS, msgs_key, -1, -1)
            loaded = self._load_messages(project_id, uid, chat_id, latest_ids)
            latest = loaded[0] if loaded else None
        return {
            "chat_id": chat_id,
            "agent_run_status": meta.get("agent_run_status") or "idle",
            "agent_run_error": meta.get("agent_run_error") or None,
            "message_count": message_count,
            "updated_at": meta.get("updated_at"),
            "latest_message": latest,
        }

    def create_thread(
        self,
        project_id: str,
        uid: str,
        *,
        title: str = "新会话",
    ) -> dict[str, Any]:
        chat_id = uuid.uuid4().hex
        now = utc_now_iso()
        score = _score_now()
        mapping = {
            "chat_id": chat_id,
            "project_id": project_id,
            "uid": uid,
            "title": title[:_TITLE_MAX],
            "agent_conversation_id": "",
            "agent_run_status": "idle",
            "created_at": now,
            "updated_at": now,
            "search_text": "",
            "msg_count": "0",
        }
        self.storage.hset(_NS_CHAT, self._chat_key(project_id, uid, chat_id), mapping)
        self.storage.zadd(_NS_CHATS, self._chats_key(project_id, uid), {chat_id: score})
        return self._thread_from_meta(mapping, [])

    def delete_thread(self, project_id: str, uid: str, chat_id: str) -> bool:
        meta = self._load_chat_meta(project_id, uid, chat_id)
        if meta is None:
            return False
        msg_ids = self.storage.zrange(
            _NS_CHAT_MSGS, self._msgs_key(project_id, uid, chat_id), 0, -1
        )
        msg_keys = [
            self._msg_key(project_id, uid, chat_id, msg_id) for msg_id in msg_ids
        ]
        self.storage.delete_many(_NS_MSG, msg_keys)
        self.storage.delete(_NS_CHAT_MSGS, self._msgs_key(project_id, uid, chat_id))
        self.storage.delete(_NS_CHAT, self._chat_key(project_id, uid, chat_id))
        self.storage.zrem(_NS_CHATS, self._chats_key(project_id, uid), chat_id)
        self.storage.delete(_NS_CHAT_USAGE, self._usage_key(project_id, uid, chat_id))
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
        image_urls: list[str] | None = None,
    ) -> dict[str, Any]:
        meta = self._load_chat_meta(project_id, uid, chat_id)
        if meta is None:
            raise KeyError(f"chat not found: {chat_id}")

        now = utc_now_iso()
        score = _score_now()
        msg_id = uuid.uuid4().hex
        message = {
            "msg_id": msg_id,
            "role": role,
            "content": content,
            "created_at": now,
            "sender_uid": uid if role == "user" else "assistant",
        }
        if activities:
            message["activities"] = list(activities)
        if confidence:
            message["confidence"] = confidence
        if image_urls:
            message["image_urls"] = list(image_urls)

        msg_key = self._msg_key(project_id, uid, chat_id, msg_id)
        self.storage.hset(_NS_MSG, msg_key, _message_to_hash(message, project_id, uid, chat_id))
        self.storage.zadd(
            _NS_CHAT_MSGS, self._msgs_key(project_id, uid, chat_id), {msg_id: score}
        )
        self._trim_messages(project_id, uid, chat_id)

        title = meta.get("title") or "新会话"
        if role == "user" and (title == "新会话" or not title.strip()):
            title = _title_from_message(content)

        search_text = _append_search_text(
            meta.get("search_text") or "",
            content=content,
            activities=activities,
            title=title if title != (meta.get("title") or "") else None,
        )
        chat_update: dict[str, str] = {
            "title": title[:_TITLE_MAX],
            "updated_at": now,
            "search_text": search_text[:_SEARCH_MAX],
            "msg_count": str(
                self.storage.zcard(_NS_CHAT_MSGS, self._msgs_key(project_id, uid, chat_id))
            ),
        }
        if agent_conversation_id:
            chat_update["agent_conversation_id"] = agent_conversation_id
        self.storage.hset(_NS_CHAT, self._chat_key(project_id, uid, chat_id), chat_update)
        self.storage.zadd(_NS_CHATS, self._chats_key(project_id, uid), {chat_id: score})

        return self.get_thread(project_id, uid, chat_id) or self._thread_from_meta(
            {**meta, **chat_update}, [message]
        )

    def rename_thread(
        self, project_id: str, uid: str, chat_id: str, title: str
    ) -> dict[str, Any] | None:
        meta = self._load_chat_meta(project_id, uid, chat_id)
        if meta is None:
            return None
        clean = " ".join(title.strip().split())[:_TITLE_MAX]
        if not clean:
            return self.get_thread(project_id, uid, chat_id)
        now = utc_now_iso()
        self.storage.hset(
            _NS_CHAT,
            self._chat_key(project_id, uid, chat_id),
            {"title": clean, "updated_at": now},
        )
        self.storage.zadd(
            _NS_CHATS, self._chats_key(project_id, uid), {chat_id: _score_now()}
        )
        return self.get_thread(project_id, uid, chat_id)

    def set_agent_conversation_id(
        self, project_id: str, uid: str, chat_id: str, agent_conversation_id: str
    ) -> None:
        meta = self._load_chat_meta(project_id, uid, chat_id)
        if meta is None:
            raise KeyError(f"chat not found: {chat_id}")
        self.storage.hset(
            _NS_CHAT,
            self._chat_key(project_id, uid, chat_id),
            {
                "agent_conversation_id": agent_conversation_id,
                "updated_at": utc_now_iso(),
            },
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
        meta = self._load_chat_meta(project_id, uid, chat_id)
        if meta is None:
            raise KeyError(f"chat not found: {chat_id}")
        mapping = {
            "agent_run_status": status,
            "updated_at": utc_now_iso(),
        }
        if error:
            mapping["agent_run_error"] = error[:500]
        else:
            mapping["agent_run_error"] = ""
        self.storage.hset(_NS_CHAT, self._chat_key(project_id, uid, chat_id), mapping)

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
        meta = self._load_chat_meta(project_id, uid, chat_id)
        if meta is None:
            raise KeyError(f"chat not found: {chat_id}")
        now = utc_now_iso()
        usage = {
            "prompt_tokens": str(max(0, prompt_tokens)),
            "completion_tokens": str(max(0, completion_tokens)),
            "reasoning_tokens": str(max(0, reasoning_tokens)),
            "total_tokens": str(max(0, total_tokens)),
            "model": model,
            "model_label": model_label,
            "token_updated_at": now,
            "updated_at": now,
        }
        self.storage.hset(_NS_CHAT, self._chat_key(project_id, uid, chat_id), usage)
        summary = {
            "project_id": project_id,
            "uid": uid,
            "chat_id": chat_id,
            "chat_title": meta.get("title") or "新会话",
            "agent_conversation_id": meta.get("agent_conversation_id") or "",
            "prompt_tokens": max(0, prompt_tokens),
            "completion_tokens": max(0, completion_tokens),
            "reasoning_tokens": max(0, reasoning_tokens),
            "total_tokens": max(0, total_tokens),
            "model": model,
            "model_label": model_label,
            "updated_at": now,
        }
        self.storage.set_json(
            _NS_CHAT_USAGE, self._usage_key(project_id, uid, chat_id), summary
        )
        return summary

    def _trim_messages(self, project_id: str, uid: str, chat_id: str) -> None:
        msgs_key = self._msgs_key(project_id, uid, chat_id)
        count = self.storage.zcard(_NS_CHAT_MSGS, msgs_key)
        overflow = count - _MAX_MESSAGES
        if overflow <= 0:
            return
        removed = self.storage.zremrangebyrank(_NS_CHAT_MSGS, msgs_key, 0, overflow - 1)
        if removed:
            self.storage.delete_many(
                _NS_MSG,
                [
                    self._msg_key(project_id, uid, chat_id, msg_id)
                    for msg_id in removed
                ],
            )

    def _load_chat_meta(
        self, project_id: str, uid: str, chat_id: str
    ) -> dict[str, str] | None:
        meta = self.storage.hgetall(_NS_CHAT, self._chat_key(project_id, uid, chat_id))
        if not meta or meta.get("uid") != uid:
            return None
        if meta.get("project_id") and meta.get("project_id") != project_id:
            return None
        return meta

    def _load_messages(
        self,
        project_id: str,
        uid: str,
        chat_id: str,
        msg_ids: list[str],
    ) -> list[dict[str, Any]]:
        if not msg_ids:
            return []
        rows = self.storage.get_hashes(
            _NS_MSG,
            [self._msg_key(project_id, uid, chat_id, msg_id) for msg_id in msg_ids],
        )
        messages: list[dict[str, Any]] = []
        for msg_id, row in zip(msg_ids, rows, strict=False):
            if not row:
                continue
            messages.append(_hash_to_message(row, fallback_id=msg_id))
        return messages

    @staticmethod
    def _thread_from_meta(
        meta: dict[str, str], messages: list[dict[str, Any]]
    ) -> dict[str, Any]:
        doc: dict[str, Any] = {
            "chat_id": meta.get("chat_id") or "",
            "project_id": meta.get("project_id"),
            "uid": meta.get("uid") or "",
            "title": meta.get("title") or "新会话",
            "messages": messages,
            "agent_conversation_id": meta.get("agent_conversation_id") or None,
            "agent_run_status": meta.get("agent_run_status") or "idle",
            "created_at": meta.get("created_at"),
            "updated_at": meta.get("updated_at"),
        }
        if meta.get("agent_run_error"):
            doc["agent_run_error"] = meta["agent_run_error"]
        if meta.get("token_updated_at") or meta.get("total_tokens"):
            doc["token_usage"] = {
                "prompt_tokens": int(meta.get("prompt_tokens") or 0),
                "completion_tokens": int(meta.get("completion_tokens") or 0),
                "reasoning_tokens": int(meta.get("reasoning_tokens") or 0),
                "total_tokens": int(meta.get("total_tokens") or 0),
                "model": meta.get("model") or "",
                "model_label": meta.get("model_label") or "",
                "updated_at": meta.get("token_updated_at") or meta.get("updated_at"),
            }
        if not doc["agent_conversation_id"]:
            doc["agent_conversation_id"] = None
        return doc

    @staticmethod
    def _chats_key(project_id: str, uid: str) -> str:
        return f"{project_id}:{uid}"

    @staticmethod
    def _chat_key(project_id: str, uid: str, chat_id: str) -> str:
        return f"{project_id}:{uid}:{chat_id}"

    @staticmethod
    def _msgs_key(project_id: str, uid: str, chat_id: str) -> str:
        return f"{project_id}:{uid}:{chat_id}"

    @staticmethod
    def _msg_key(project_id: str, uid: str, chat_id: str, msg_id: str) -> str:
        return f"{project_id}:{uid}:{chat_id}:{msg_id}"

    @staticmethod
    def _usage_key(project_id: str, uid: str, chat_id: str) -> str:
        return f"{project_id}:{uid}:{chat_id}"


def _score_now() -> float:
    return time.time() * 1000.0


def _title_from_message(message: str) -> str:
    text = " ".join(message.strip().split())
    if not text:
        return "新会话"
    return text[:_TITLE_MAX]


def _append_search_text(
    existing: str,
    *,
    content: str,
    activities: list[dict[str, str]] | None,
    title: str | None,
) -> str:
    parts: list[str] = []
    if title:
        parts.append(title)
    if content.strip():
        parts.append(content.strip())
    for act in activities or []:
        text = act.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
    if not parts:
        return existing[:_SEARCH_MAX]
    merged = f"{existing} {' '.join(parts)}".strip() if existing else " ".join(parts)
    return merged[:_SEARCH_MAX]


def _message_to_hash(
    message: dict[str, Any],
    project_id: str,
    uid: str,
    chat_id: str,
) -> dict[str, str]:
    mapping = {
        "msg_id": str(message.get("msg_id") or ""),
        "project_id": project_id,
        "uid": uid,
        "chat_id": chat_id,
        "role": str(message.get("role") or ""),
        "content": str(message.get("content") or ""),
        "created_at": str(message.get("created_at") or ""),
        "sender_uid": str(message.get("sender_uid") or ""),
    }
    if message.get("image_urls") is not None:
        mapping["image_urls"] = json.dumps(
            message["image_urls"], ensure_ascii=False
        )
    if message.get("activities") is not None:
        mapping["activities"] = json.dumps(
            message["activities"], ensure_ascii=False
        )
    if message.get("confidence") is not None:
        mapping["confidence"] = json.dumps(
            message["confidence"], ensure_ascii=False
        )
    return mapping


def _hash_to_message(row: dict[str, str], *, fallback_id: str) -> dict[str, Any]:
    message: dict[str, Any] = {
        "msg_id": row.get("msg_id") or fallback_id,
        "role": row.get("role") or "",
        "content": row.get("content") or "",
        "created_at": row.get("created_at") or "",
        "sender_uid": row.get("sender_uid") or "",
    }
    if row.get("image_urls"):
        try:
            message["image_urls"] = json.loads(row["image_urls"])
        except json.JSONDecodeError:
            message["image_urls"] = []
    if row.get("activities"):
        try:
            message["activities"] = json.loads(row["activities"])
        except json.JSONDecodeError:
            message["activities"] = []
    if row.get("confidence"):
        try:
            message["confidence"] = json.loads(row["confidence"])
        except json.JSONDecodeError:
            pass
    return message
