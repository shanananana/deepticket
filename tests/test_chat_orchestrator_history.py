from __future__ import annotations

from deepticket.chat_orchestrator import ChatOrchestrator


def test_history_from_thread_excludes_current_user_message() -> None:
    thread = {
        "messages": [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好呀"},
            {"role": "user", "content": "我刚刚说了什么"},
        ]
    }
    history = ChatOrchestrator._history_from_thread(
        thread,
        current_user_message="我刚刚说了什么",
    )
    assert history == [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好呀"},
    ]
