from __future__ import annotations

from typing import Any

_EVIDENCE_KINDS = frozenset({"log", "config", "code", "search", "evidence", "skill"})
_ANALYSIS_KINDS = _EVIDENCE_KINDS | frozenset({"terminal", "error"})
_PENALTY_KINDS = frozenset({"error"})


def is_confidence_applicable(activities: list[dict[str, str]] | None = None) -> bool:
    """是否存在可验证的分析步骤（读代码/日志/跑命令等）。"""
    acts = activities or []
    return any((item.get("kind") or "default") in _ANALYSIS_KINDS for item in acts)


def compute_confidence(
    *,
    activities: list[dict[str, str]] | None = None,
    reply: str = "",
    ok: bool = True,
    require_analysis: bool = False,
) -> dict[str, Any] | None:
    """基于 Agent 活动与回复内容估算分析置信度（0–100）。

    纯聊天（无读代码/查日志等步骤）且 ``require_analysis=True`` 时返回 ``None``，
    由上层决定是否展示置信度。
    """
    acts = activities or []
    if require_analysis and not is_confidence_applicable(acts):
        return None

    kinds = [item.get("kind") or "default" for item in acts]
    evidence_count = sum(1 for kind in kinds if kind in _EVIDENCE_KINDS)
    error_count = sum(1 for kind in kinds if kind in _PENALTY_KINDS)
    has_key_evidence = "evidence" in kinds
    reply_text = (reply or "").strip()

    score = 40
    reasons: list[str] = []

    if evidence_count:
        bonus = min(30, evidence_count * 8)
        score += bonus
        reasons.append(f"已执行 {evidence_count} 步可验证操作（读代码/日志/配置等）")
    else:
        reasons.append("未观察到读代码、查日志或查配置等验证步骤")

    if has_key_evidence:
        score += 15
        reasons.append("Agent 给出了基于数据的 key finding")

    if error_count:
        penalty = min(25, error_count * 12)
        score -= penalty
        reasons.append(f"发生 {error_count} 次工具或步骤错误")

    if not ok:
        score -= 30
        reasons.append("Agent 运行未正常结束")

    if reply_text:
        if len(reply_text) >= 80:
            score += 10
            reasons.append("回复内容较为完整")
        elif len(reply_text) < 30 and evidence_count == 0:
            score -= 8
            reasons.append("回复较短，结论可能不充分")
    else:
        score -= 20
        reasons.append("未生成文本结论")

    score = max(0, min(100, score))

    if score >= 75:
        level, label = "high", "高"
    elif score >= 50:
        level, label = "medium", "中"
    else:
        level, label = "low", "低"

    return {
        "score": score,
        "level": level,
        "label": label,
        "reasons": reasons,
        "applicable": True,
    }
