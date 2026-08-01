from __future__ import annotations

import uuid

from deepticket.auth.user_store import UserStore
from deepticket.layers.storage.chat_history import ChatHistoryStore
from deepticket.layers.storage.local import LocalStorage


def test_register_login_and_isolation(tmp_path):
    storage = LocalStorage(tmp_path)
    users = UserStore(storage)
    chats = ChatHistoryStore(storage)

    suffix = uuid.uuid4().hex[:8]
    user_a = users.register(f"user_a_{suffix}", "password-123")
    user_b = users.register(f"user_b_{suffix}", "password-123")

    _, token_a = users.login(user_a.username, "password-123")
    assert users.resolve_token(token_a) is not None
    assert users.resolve_token("invalid-token") is None

    thread = chats.create_thread(user_a.uid, title="test")
    chats.append_message(user_a.uid, thread["chat_id"], role="user", content="hi")
    assert chats.get_thread(user_b.uid, thread["chat_id"]) is None


def test_duplicate_username_rejected(tmp_path):
    storage = LocalStorage(tmp_path)
    users = UserStore(storage)
    name = f"dup_{uuid.uuid4().hex[:6]}"
    users.register(name, "password-123")
    try:
        users.register(name, "password-456")
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "占用" in str(exc)
