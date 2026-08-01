from __future__ import annotations

import pytest

from deepticket.layers.storage.chat_history import ChatHistoryStore
from deepticket.layers.storage.local import LocalStorage


@pytest.fixture
def store(tmp_path):
    return ChatHistoryStore(LocalStorage(tmp_path))


def test_thread_lifecycle(store):
    t = store.create_thread("u1", title="测试会话")
    assert t["chat_id"]
    assert t["title"] == "测试会话"

    fetched = store.get_thread("u1", t["chat_id"])
    assert fetched and fetched["uid"] == "u1"

    store.append_message("u1", t["chat_id"], role="user", content="你好")
    store.append_message("u1", t["chat_id"], role="assistant", content="你好，我是助手")
    doc = store.get_thread("u1", t["chat_id"])
    assert len(doc["messages"]) == 2
    assert doc["messages"][0]["role"] == "user"


def test_rename(store):
    t = store.create_thread("u1", title="旧标题")
    updated = store.rename_thread("u1", t["chat_id"], "新标题")
    assert updated["title"] == "新标题"
    assert store.get_thread("u1", t["chat_id"])["title"] == "新标题"


def test_rename_trims_and_limits(store):
    t = store.create_thread("u1")
    long_title = "  这是一个   很长的标题   " + "x" * 100
    updated = store.rename_thread("u1", t["chat_id"], long_title)
    assert len(updated["title"]) == 48
    assert updated["title"].startswith("这是一个 很长的标题")


def test_isolation(store):
    a = store.create_thread("user_a", title="A 的会话")
    b = store.create_thread("user_b", title="B 的会话")
    assert store.get_thread("user_a", b["chat_id"]) is None
    assert store.get_thread("user_b", a["chat_id"]) is None
    assert len(store.list_threads("user_a")) == 1


def test_delete(store):
    t = store.create_thread("u1")
    assert store.delete_thread("u1", t["chat_id"]) is True
    assert store.get_thread("u1", t["chat_id"]) is None
    assert store.list_threads("u1") == []


def test_auto_title_from_first_message(store):
    t = store.create_thread("u1", title="新会话")
    store.append_message("u1", t["chat_id"], role="user", content="帮我分析线上 500 错误")
    doc = store.get_thread("u1", t["chat_id"])
    assert doc["title"] == "帮我分析线上 500 错误"


def test_list_sorted_by_updated(store):
    t1 = store.create_thread("u1", title="第一个")
    t2 = store.create_thread("u1", title="第二个")
    store.append_message("u1", t1["chat_id"], role="user", content="更新第一个")
    listed = store.list_threads("u1")
    assert listed[0]["chat_id"] == t1["chat_id"]
    assert listed[1]["chat_id"] == t2["chat_id"]
