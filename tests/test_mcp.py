from __future__ import annotations

import json

from deepticket.config.mcp_loader import (
    filter_enabled_servers,
    load_mcp_servers,
    servers_for_sync,
    validate_mcp_servers,
)


def test_filter_enabled_servers():
    raw = {
        "disabled": {"transport": "stdio", "command": "echo", "enabled": False},
        "active": {"transport": "stdio", "command": "true", "enabled": True},
        "default_on": {"transport": "stdio", "command": "true"},
    }
    enabled = filter_enabled_servers(raw)
    assert set(enabled.keys()) == {"active", "default_on"}
    assert "enabled" not in enabled["active"]


def test_validate_mcp_servers_detects_missing_command():
    errors = validate_mcp_servers({"bad": {"transport": "stdio"}})
    assert any("command" in item for item in errors)


def test_servers_for_sync_roundtrip(tmp_path):
    config = tmp_path / "servers.json"
    config.write_text(
        json.dumps(
            {
                "servers": {
                    "demo": {
                        "transport": "stdio",
                        "command": "true",
                        "enabled": True,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    loaded = load_mcp_servers(config)
    assert "demo" in loaded
    synced = servers_for_sync(config)
    assert synced["demo"]["command"] == "true"
