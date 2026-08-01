from deepticket.layers.output.activity import format_agent_activity


def test_action_event_uses_summary():
    event = {
        "id": "1",
        "kind": "ActionEvent",
        "tool_name": "terminal",
        "summary": "List files in workspace/project directory",
        "action": {"command": "ls -la workspace/project"},
    }
    assert format_agent_activity(event) == "List files in workspace/project directory"


def test_action_event_falls_back_to_command():
    event = {
        "id": "2",
        "kind": "ActionEvent",
        "tool_name": "terminal",
        "action": {"command": "grep -R error workspace/project"},
    }
    assert "grep -R error workspace/project" in (format_agent_activity(event) or "")


def test_skips_state_update_events():
    event = {"id": "3", "kind": "ConversationStateUpdateEvent"}
    assert format_agent_activity(event) is None
