from __future__ import annotations

import pytest

from deepticket.layers.storage.local import LocalStorage
from deepticket.layers.storage.token_usage import TokenUsageStore


@pytest.fixture
def store(tmp_path) -> TokenUsageStore:
    return TokenUsageStore(LocalStorage(tmp_path / "data"))


def test_record_run_and_list(store: TokenUsageStore) -> None:
    store.record_run(
        uid="uid1",
        username="alice",
        chat_id="chat1",
        chat_title="ROI 分析",
        agent_conversation_id="conv-1",
        model="openai/deepseek-v4-flash",
        model_label="DeepSeek V4 Flash",
        delta={
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "reasoning_tokens": 5,
            "total_tokens": 125,
        },
        cumulative={
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "reasoning_tokens": 5,
            "total_tokens": 125,
        },
    )
    runs = store.list_recent_runs(limit=10)
    assert len(runs) == 1
    assert runs[0]["username"] == "alice"
    assert runs[0]["chat_id"] == "chat1"
    assert runs[0]["model"] == "openai/deepseek-v4-flash"
    assert runs[0]["total_tokens"] == 125


def test_list_conversation_usage(store: TokenUsageStore) -> None:
    storage = store.storage
    storage.set_json(
        "chat_usage",
        "default:uid1:chat1",
        {
            "uid": "uid1",
            "chat_id": "chat1",
            "chat_title": "测试对话",
            "prompt_tokens": 500,
            "completion_tokens": 50,
            "reasoning_tokens": 10,
            "total_tokens": 560,
            "model": "openai/deepseek-v4-flash",
            "model_label": "DeepSeek V4 Flash",
            "updated_at": "2026-08-04T12:00:00+00:00",
        },
    )
    items = store.list_conversation_usage(resolve_username=lambda uid: "alice")
    assert len(items) == 1
    assert items[0]["username"] == "alice"
    assert items[0]["chat_title"] == "测试对话"
    assert items[0]["model"] == "openai/deepseek-v4-flash"
    assert items[0]["model_label"] == "DeepSeek V4 Flash"
    assert items[0]["total_tokens"] == 560

    summary = store.summarize_conversations(items)
    assert summary["total_tokens"] == 560
    assert summary["conversation_count"] == 1


def test_list_user_conversation_usage(store: TokenUsageStore) -> None:
    storage = store.storage
    storage.set_json(
        "chat_usage",
        "default:uid1:chat1",
        {
            "project_id": "default",
            "uid": "uid1",
            "chat_id": "chat1",
            "chat_title": "我的对话",
            "total_tokens": 100,
            "prompt_tokens": 80,
            "completion_tokens": 20,
            "reasoning_tokens": 0,
            "updated_at": "2026-08-04T12:00:00+00:00",
        },
    )
    storage.set_json(
        "chat_usage",
        "default:uid2:chat2",
        {
            "project_id": "default",
            "uid": "uid2",
            "chat_id": "chat2",
            "chat_title": "他人对话",
            "total_tokens": 999,
            "prompt_tokens": 999,
            "completion_tokens": 0,
            "reasoning_tokens": 0,
            "updated_at": "2026-08-04T12:00:00+00:00",
        },
    )
    items = store.list_user_conversation_usage("uid1")
    assert len(items) == 1
    assert items[0]["chat_title"] == "我的对话"
    assert items[0]["project_id"] == "default"


def test_list_user_runs(store: TokenUsageStore) -> None:
    store.record_run(
        uid="uid1",
        username="alice",
        chat_id="chat1",
        chat_title="A",
        agent_conversation_id="conv-1",
        model="m",
        model_label="M",
        delta={"prompt_tokens": 1, "completion_tokens": 1, "reasoning_tokens": 0, "total_tokens": 2},
        cumulative={"prompt_tokens": 1, "completion_tokens": 1, "reasoning_tokens": 0, "total_tokens": 2},
    )
    store.record_run(
        uid="uid2",
        username="bob",
        chat_id="chat2",
        chat_title="B",
        agent_conversation_id="conv-2",
        model="m",
        model_label="M",
        delta={"prompt_tokens": 9, "completion_tokens": 9, "reasoning_tokens": 0, "total_tokens": 18},
        cumulative={"prompt_tokens": 9, "completion_tokens": 9, "reasoning_tokens": 0, "total_tokens": 18},
    )
    runs = store.list_user_runs("uid1", limit=10)
    assert len(runs) == 1
    assert runs[0]["uid"] == "uid1"
