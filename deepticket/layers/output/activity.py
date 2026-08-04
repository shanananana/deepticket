"""将 OpenHands Agent 事件转为用户可读的活动描述。"""

from __future__ import annotations

import re
from dataclasses import dataclass
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

_LOG_QUERY_RE = re.compile(
    r"query_campaign_metrics|query_logs|query_ad_roi|generate_campaign_data|log-query|/skills/log-query/",
    re.IGNORECASE,
)
_CONFIG_QUERY_RE = re.compile(
    r"config-query|/skills/config-query/",
    re.IGNORECASE,
)
_WORKSPACE_RE = re.compile(r"workspace/project/[^\s'\"]+")
_READ_FILE_RE = re.compile(
    r"(?:cat|sed|head|tail|view|read)\s+[^\s|;&]+|"
    r"workspace/project/[^\s'\"]+\.(?:py|yaml|yml|json|md|go|java|ts)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AgentActivity:
    text: str
    kind: str = "default"


def _truncate(text: str, limit: int = 120) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def _observation_text(observation: dict[str, Any]) -> str:
    for key in ("content", "message", "output", "text"):
        val = observation.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    extras = observation.get("extras")
    if isinstance(extras, dict):
        for key in ("content", "output", "text"):
            val = extras.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    return ""


def _classify_command(command: str) -> AgentActivity | None:
    cmd = command.strip()
    if not cmd:
        return None
    if _LOG_QUERY_RE.search(cmd):
        if "generate_campaign_data" in cmd:
            return AgentActivity("生成投放指标日志（演示数据）", "log")
        if "query_campaign_metrics" in cmd or "query_ad_roi" in cmd:
            return AgentActivity("查询投放 ROI / 指标日志", "log")
        if "query_logs" in cmd:
            return AgentActivity("使用 log-query Skill 查询日志", "log")
        if "campaign_metrics.log" in cmd or "budget_audit.log" in cmd:
            return AgentActivity("读取 ad_agent 投放/审计日志", "log")
        return AgentActivity("使用 log-query Skill 查询日志/指标", "log")
    if _CONFIG_QUERY_RE.search(cmd) or "query_config" in cmd:
        return AgentActivity("使用 config-query Skill 查询配置", "config")
    if ".openhands/skills/" in cmd:
        return AgentActivity(f"调用 Skill: {_truncate(cmd, 90)}", "skill")
    workspace = _WORKSPACE_RE.search(cmd)
    if workspace:
        path = workspace.group(0)
        if any(x in cmd.lower() for x in ("grep", "rg ", "find ")):
            return AgentActivity(f"在代码库中搜索: {_truncate(path, 80)}", "search")
        return AgentActivity(f"读取代码: {_truncate(path, 80)}", "code")
    if _READ_FILE_RE.search(cmd):
        return AgentActivity(f"读取文件: {_truncate(cmd, 90)}", "code")
    if cmd.startswith("grep") or " rg " in f" {cmd} ":
        return AgentActivity(f"搜索代码: {_truncate(cmd, 90)}", "search")
    return AgentActivity(f"执行命令: {_truncate(cmd, 100)}", "terminal")


def _classify_summary(summary: str, tool: str) -> AgentActivity:
    text = summary.strip()
    lower = text.lower()
    if _LOG_QUERY_RE.search(text):
        return AgentActivity(_truncate(text), "log")
    if _CONFIG_QUERY_RE.search(text):
        return AgentActivity(_truncate(text), "config")
    if "workspace/project" in lower or tool in {"grep", "glob"}:
        kind = "search" if tool in {"grep", "glob"} else "code"
        return AgentActivity(_truncate(text), kind)
    if tool == "think":
        return AgentActivity(_truncate(text), "think")
    return AgentActivity(_truncate(text), "default")


def _evidence_from_output(text: str) -> AgentActivity | None:
    compact = " ".join(text.split())
    if not compact:
        return None
    markers = (
        "key finding",
        "LIKELY_CAUSE",
        "daily_budget",
        "budget_changes",
        "ROI",
    )
    if not any(m.lower() in compact.lower() for m in markers):
        return None
    line = compact
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if any(m.lower() in stripped.lower() for m in markers):
            line = stripped
            break
    return AgentActivity(f"关键发现: {_truncate(line, 140)}", "evidence")


def format_agent_activity(event: dict[str, Any]) -> AgentActivity | None:
    """从 Agent Server 事件提取活动文案与类型；无则返回 None。"""
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
        if not text:
            return None
        return AgentActivity(_truncate(text), "think")

    if kind == "ActionEvent":
        summary = (event.get("summary") or "").strip()
        tool = (event.get("tool_name") or "").strip()
        action = event.get("action") or {}

        if tool == "terminal":
            command = (action.get("command") or "").strip()
            if command:
                classified = _classify_command(command)
                if classified:
                    return classified

        if summary:
            return _classify_summary(summary, tool)

        prefix = _TOOL_LABELS.get(tool, f"调用 {tool}" if tool else "Agent 操作")
        reasoning = (event.get("reasoning_content") or "").strip()
        if reasoning:
            return AgentActivity(_truncate(reasoning), "think")
        if tool == "think":
            return AgentActivity(prefix, "think")
        return AgentActivity(prefix, "default") if tool else AgentActivity("Agent 正在处理", "default")

    if kind == "ObservationEvent":
        observation = event.get("observation") or {}
        if observation.get("is_error"):
            tool = (event.get("tool_name") or "工具").strip()
            return AgentActivity(f"{tool} 执行出错", "error")
        body = _observation_text(observation)
        evidence = _evidence_from_output(body)
        if evidence:
            return evidence
        return None

    return None
