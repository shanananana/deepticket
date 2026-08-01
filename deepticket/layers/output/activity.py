"""将 OpenHands Agent 事件转为用户可读的活动描述。"""

from __future__ import annotations

from typing import Any

_TOOL_LABELS: dict[str, str] = {
    "terminal": "执行命令",
    "file_editor": "编辑文件",
    "str_replace_editor": "编辑文件",
    "browser": "浏览网页",
    "grep": "搜索代码",
    "glob": "查找文件",
    "think": "推理分析",
    "finish": "整理结论",
    "execute_ipython_cell": "运行代码",
    "web_read": "读取网页",
}


def _truncate(text: str, limit: int = 120) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def format_agent_activity(event: dict[str, Any]) -> str | None:
    """从 Agent Server 事件提取一条活动文案；无则返回 None。"""
    kind = event.get("kind") or ""
    if kind in {"SystemPromptEvent", "ConversationStateUpdateEvent"}:
        return None

    if kind == "MessageEvent":
        if event.get("source") != "agent":
            return None
        content = event.get("content") or event.get("message")
        if isinstance(content, list):
            parts = [
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("text")
            ]
            text = " ".join(parts).strip()
        elif isinstance(content, str):
            text = content.strip()
        else:
            text = ""
        return _truncate(text) if text else None

    if kind == "ActionEvent":
        summary = (event.get("summary") or "").strip()
        if summary:
            return _truncate(summary)

        tool = (event.get("tool_name") or "").strip()
        prefix = _TOOL_LABELS.get(tool, f"调用 {tool}" if tool else "Agent 操作")

        action = event.get("action") or {}
        if tool == "terminal":
            command = (action.get("command") or "").strip()
            if command:
                return f"{prefix}: {_truncate(command, 100)}"

        reasoning = (event.get("reasoning_content") or "").strip()
        if reasoning:
            return _truncate(reasoning)

        return prefix if tool else "Agent 正在处理"

    if kind == "ObservationEvent":
        observation = event.get("observation") or {}
        if observation.get("is_error"):
            tool = (event.get("tool_name") or "工具").strip()
            return f"{tool} 执行出错"
        return None

    return None
