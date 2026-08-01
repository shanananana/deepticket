from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REQUIRED_FIELDS = ("transport",)


def load_mcp_servers(config_path: str | Path) -> dict[str, dict[str, Any]]:
    path = Path(config_path)
    if not path.is_file():
        return {}

    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "servers" in raw:
        servers = raw["servers"]
    elif isinstance(raw, dict) and "mcpServers" in raw:
        servers = raw["mcpServers"]
    elif isinstance(raw, dict):
        servers = raw
    else:
        raise ValueError(f"MCP 配置格式无效: {path}")

    if not isinstance(servers, dict):
        raise ValueError(f"MCP 配置 servers 必须是对象: {path}")
    return servers


def filter_enabled_servers(servers: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """过滤 enabled=false 的条目，并去掉 enabled 字段再同步给 Agent Server。"""
    result: dict[str, dict[str, Any]] = {}
    for name, spec in servers.items():
        if not isinstance(spec, dict):
            raise ValueError(f"MCP server '{name}' 配置必须是对象")
        if spec.get("enabled") is False:
            continue
        payload = {key: value for key, value in spec.items() if key != "enabled"}
        result[name] = payload
    return result


def validate_mcp_servers(servers: dict[str, dict[str, Any]]) -> list[str]:
    """返回校验错误列表；空列表表示通过。"""
    errors: list[str] = []
    for name, spec in servers.items():
        if not isinstance(spec, dict):
            errors.append(f"{name}: 配置必须是对象")
            continue
        for field in _REQUIRED_FIELDS:
            if field not in spec or spec[field] in ("", None):
                errors.append(f"{name}: 缺少字段 {field}")
        transport = spec.get("transport")
        if transport == "stdio":
            if not spec.get("command"):
                errors.append(f"{name}: stdio transport 需要 command")
    return errors


def servers_for_sync(config_path: str | Path) -> dict[str, dict[str, Any]]:
    """加载并返回应同步到 Agent Server 的 MCP 配置。"""
    loaded = load_mcp_servers(config_path)
    enabled = filter_enabled_servers(loaded)
    errors = validate_mcp_servers(enabled)
    if errors:
        raise ValueError("MCP 配置无效: " + "; ".join(errors))
    return enabled
