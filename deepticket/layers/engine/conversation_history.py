from __future__ import annotations

from typing import Any


def normalize_message_text(text: str) -> str:
    return " ".join((text or "").split())


def extract_message_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return normalize_message_text(content)
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                text = block.get("text")
                if text:
                    parts.append(str(text))
            elif isinstance(block, str) and block.strip():
                parts.append(block)
        return normalize_message_text("\n".join(parts))
    return normalize_message_text(str(content))


def filter_chat_history(
    redis_history: list[dict[str, str]],
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for item in redis_history:
        role = str(item.get("role") or "")
        content = normalize_message_text(str(item.get("content") or ""))
        if role in ("user", "assistant") and content:
            pairs.append((role, content))
    return pairs


def history_prefix_match_len(
    openhands_messages: list[tuple[str, str]],
    redis_history: list[dict[str, str]],
) -> int:
    """返回 Redis 历史与 OpenHands 已有一致的前缀长度。"""
    redis_pairs = filter_chat_history(redis_history)
    matched = 0
    for idx, (role, content) in enumerate(redis_pairs):
        if idx >= len(openhands_messages):
            break
        oh_role, oh_content = openhands_messages[idx]
        if oh_role == role and oh_content == content:
            matched = idx + 1
        else:
            break
    return matched


def history_is_synced(
    openhands_messages: list[tuple[str, str]],
    redis_history: list[dict[str, str]],
) -> bool:
    redis_pairs = filter_chat_history(redis_history)
    if not redis_pairs:
        return True
    return history_prefix_match_len(openhands_messages, redis_history) >= len(
        redis_pairs
    )


def format_history_prompt(
    redis_history: list[dict[str, str]],
    current_prompt: str,
) -> str:
    """将 Redis 对话历史注入当前 user 消息（OpenHands 不支持回放 assistant event）。"""
    pairs = filter_chat_history(redis_history)
    current = normalize_message_text(current_prompt)
    if not pairs:
        return current_prompt
    lines: list[str] = []
    for role, content in pairs:
        label = "User" if role == "user" else "Assistant"
        lines.append(f"{label}: {content}")
    body = "\n".join(lines)
    return (
        "<conversation_history>\n"
        f"{body}\n"
        "</conversation_history>\n\n"
        f"{current}"
    )
