from deepticket.layers.output.activity import AgentActivity, format_agent_activity


def test_action_event_uses_summary():
    event = {
        "id": "1",
        "kind": "ActionEvent",
        "tool_name": "grep",
        "summary": "Search for budget_changes in workspace/project/ad-agent",
        "action": {"command": "grep -R budget_changes workspace/project/ad-agent"},
    }
    result = format_agent_activity(event)
    assert result == AgentActivity(
        "Search for budget_changes in workspace/project/ad-agent",
        "search",
    )


def test_action_event_log_query_skill():
    event = {
        "id": "2",
        "kind": "ActionEvent",
        "tool_name": "terminal",
        "action": {
            "command": "python scripts/query_campaign_metrics.py --start 2025-03-10 --end 2025-03-20",
        },
    }
    result = format_agent_activity(event)
    assert result is not None
    assert result.kind == "log"
    assert "ROI" in result.text or "日志" in result.text


def test_action_event_read_code_path():
    event = {
        "id": "3",
        "kind": "ActionEvent",
        "tool_name": "terminal",
        "action": {"command": "cat workspace/project/ad-agent/config/campaigns.yaml"},
    }
    result = format_agent_activity(event)
    assert result is not None
    assert result.kind == "code"
    assert "campaigns.yaml" in result.text


def test_observation_key_finding():
    event = {
        "id": "4",
        "kind": "ObservationEvent",
        "tool_name": "terminal",
        "observation": {
            "content": "--- key finding (demo) ---\nalbum_bad_001: ROI 1.30 -> 0.43",
        },
    }
    result = format_agent_activity(event)
    assert result is not None
    assert result.kind == "evidence"
    assert "关键发现" in result.text


def test_skips_state_update_events():
    event = {"id": "5", "kind": "ConversationStateUpdateEvent"}
    assert format_agent_activity(event) is None
