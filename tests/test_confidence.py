from __future__ import annotations

from deepticket.layers.output.confidence import compute_confidence, is_confidence_applicable


def test_confidence_high_with_evidence() -> None:
    result = compute_confidence(
        activities=[
            {"text": "查询投放 ROI", "kind": "log"},
            {"text": "读取 campaigns.yaml", "kind": "code"},
            {"text": "关键发现: ROI 下降", "kind": "evidence"},
        ],
        reply="根据 campaign_metrics.log 与 budget_audit.log，7/28 后低 ROI 计划被放大预算。",
        ok=True,
    )
    assert result is not None
    assert result["level"] == "high"
    assert result["score"] >= 75
    assert result["label"] == "高"
    assert result["reasons"]
    assert result["applicable"] is True


def test_confidence_low_without_evidence() -> None:
    result = compute_confidence(
        activities=[{"text": "推理分析", "kind": "think"}],
        reply="可能是网络问题。",
        ok=True,
        require_analysis=False,
    )
    assert result is not None
    assert result["level"] in {"low", "medium"}
    assert result["score"] < 75
    assert any("未观察到" in reason for reason in result["reasons"])


def test_confidence_penalized_on_errors() -> None:
    result = compute_confidence(
        activities=[
            {"text": "tool 出错", "kind": "error"},
            {"text": "读取代码", "kind": "code"},
        ],
        reply="分析失败，工具执行出错。",
        ok=False,
    )
    assert result is not None
    assert result["score"] <= 60
    assert any("错误" in reason or "未正常" in reason for reason in result["reasons"])


def test_confidence_skipped_for_pure_chat() -> None:
    assert is_confidence_applicable(
        [
            {"text": "问题已提交", "kind": "system"},
            {"text": "连接 Agent", "kind": "system"},
            {"text": "开始回复", "kind": "handoff"},
        ]
    ) is False
    result = compute_confidence(
        activities=[
            {"text": "问题已提交", "kind": "system"},
            {"text": "开始回复", "kind": "handoff"},
        ],
        reply="你好",
        ok=True,
        require_analysis=True,
    )
    assert result is None


def test_confidence_shown_when_code_step_present() -> None:
    result = compute_confidence(
        activities=[
            {"text": "读取 main.py", "kind": "code"},
        ],
        reply="你好",
        ok=True,
        require_analysis=True,
    )
    assert result is not None
    assert result["applicable"] is True
