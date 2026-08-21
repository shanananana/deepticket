from __future__ import annotations

from deepticket.layers.engine.conversation_history import (
    extract_message_text,
    filter_chat_history,
    format_history_prompt,
    history_is_synced,
    history_prefix_match_len,
)


def test_extract_message_text_from_blocks() -> None:
    content = [{"type": "text", "text": "你好"}]
    assert extract_message_text(content) == "你好"


def test_history_prefix_match_len() -> None:
    oh = [("user", "你好"), ("assistant", "你好呀")]
    redis = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好呀"},
        {"role": "user", "content": "我刚刚说了什么"},
    ]
    assert history_prefix_match_len(oh, redis) == 2


def test_filter_chat_history_skips_empty() -> None:
    items = filter_chat_history(
        [
            {"role": "user", "content": "A"},
            {"role": "system", "content": "ignore"},
            {"role": "assistant", "content": ""},
        ]
    )
    assert items == [("user", "A")]


def test_history_is_synced() -> None:
    oh = [("user", "你好"), ("assistant", "你好呀")]
    redis = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好呀"},
    ]
    assert history_is_synced(oh, redis) is True
    assert history_is_synced([("user", "你好")], redis) is False


def test_format_history_prompt() -> None:
    prompt = format_history_prompt(
        [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好呀"},
        ],
        "我刚刚说了什么",
    )
    assert "<conversation_history>" in prompt
    assert "User: 你好" in prompt
    assert "Assistant: 你好呀" in prompt
    assert prompt.endswith("我刚刚说了什么")
