"""从 OpenHands StreamingDeltaEvent 提取用户可见的回复文本。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReplyStreamState:
    llm_buffer: str = ""
    emitted: str = ""
    delta_count: int = 0

    def reset_turn(self) -> None:
        self.llm_buffer = ""
        self.emitted = ""


def _read_json_string_value(raw: str, start: int) -> str:
    out: list[str] = []
    i = start
    while i < len(raw):
        ch = raw[i]
        if ch == "\\":
            if i + 1 < len(raw):
                n = raw[i + 1]
                escapes = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}
                out.append(escapes.get(n, n))
                i += 2
                continue
        if ch == '"':
            break
        out.append(ch)
        i += 1
    return "".join(out)


def extract_visible_reply(raw: str) -> str | None:
    """从 LLM 流式输出中提取应对用户展示的文本片段。"""
    for marker in ('"message":"', '"message": "',
                   '"message":\n"', '"message": \n"'):
        idx = raw.find(marker)
        if idx >= 0:
            return _read_json_string_value(raw, idx + len(marker))

    stripped = raw.lstrip()
    if not stripped:
        return None
    if stripped.startswith(("{", "[", "<")):
        return None
    if stripped.startswith('"') and ":" in stripped[:24]:
        return None
    return raw


def consume_stream_content(state: ReplyStreamState, content: str) -> str:
    """追加 LLM token，返回相对已发送部分的新增可见文本。"""
    if not content:
        return ""
    state.llm_buffer += content
    visible = extract_visible_reply(state.llm_buffer)
    if visible is None:
        return ""
    if len(visible) <= len(state.emitted):
        return ""
    delta = visible[len(state.emitted) :]
    state.emitted = visible
    state.delta_count += 1
    return delta
