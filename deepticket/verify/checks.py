from __future__ import annotations

import os
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

import httpx

from deepticket.auth.user_store import UserStore
from deepticket.config.mcp_loader import filter_enabled_servers, validate_mcp_servers
from deepticket.core.bootstrap import load_runtime_config
from deepticket.layers.engine.openhands_engine import OpenHandsEngine
from deepticket.layers.knowledge.skill_manager import SkillManager
from deepticket.layers.storage.chat_history import ChatHistoryStore
from deepticket.layers.storage.local import LocalStorage
from deepticket.paths import (
    DEFAULT_CONFIG_EXAMPLE_PATH,
    PROJECT_ROOT,
    SKILLS_DIR,
    resolve_from_project,
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    message: str
    optional: bool = False


def check_package_layout() -> CheckResult:
    example_config = PROJECT_ROOT / DEFAULT_CONFIG_EXAMPLE_PATH
    missing = [
        str(path)
        for path in (SKILLS_DIR, example_config)
        if not path.exists()
    ]
    if missing:
        return CheckResult(
            "package_layout",
            False,
            f"缺少目录/文件: {', '.join(missing)}",
        )
    skill_count = sum(1 for p in SKILLS_DIR.iterdir() if (p / "SKILL.md").is_file())
    return CheckResult(
        "package_layout",
        skill_count > 0,
        f"skills={skill_count}, config_example={'ok' if example_config.is_file() else 'missing'}",
    )


def check_config_load() -> CheckResult:
    try:
        config = load_runtime_config()
    except (ValueError, OSError) as exc:
        return CheckResult("config_load", False, str(exc))
    return CheckResult(
        "config_load",
        True,
        f"storage={config.storage.backend}, skills_dir={config.extensions.skills_dir}",
    )


def check_skills_publish() -> CheckResult:
    config = load_runtime_config()
    skills_path = resolve_from_project(config.extensions.skills_dir)

    with tempfile.TemporaryDirectory() as tmp:
        workspace_skills = Path(tmp) / "skills"
        manager = SkillManager(
            skills_dir=skills_path,
            user_skills_dir=None,
            workspace_skills_dir=workspace_skills,
        )
        listed = manager.list_skills()
        published = manager.publish_to_workspace()
        if not listed:
            return CheckResult("skills", False, "未找到任何 SKILL.md")
        if len(published) != len(listed):
            return CheckResult(
                "skills",
                False,
                f"发布数量不一致: listed={len(listed)}, published={len(published)}",
            )
        names = ", ".join(item.name for item in listed)
        return CheckResult("skills", True, f"已发布 {len(published)} 个: {names}")


def check_mcp_config_file() -> CheckResult:
    config = load_runtime_config()
    loaded = config.mcp.servers

    if not loaded:
        return CheckResult(
            "mcp_config",
            True,
            "未配置 MCP servers（deepticket.yaml 的 mcp.servers 为空）",
            optional=True,
        )

    try:
        enabled = filter_enabled_servers(loaded)
        errors = validate_mcp_servers(enabled)
    except ValueError as exc:
        return CheckResult("mcp_config", False, str(exc))

    if errors:
        return CheckResult("mcp_config", False, "; ".join(errors))

    return CheckResult(
        "mcp_config",
        True,
        f"总计 {len(loaded)} 项，启用 {len(enabled)} 项: {', '.join(enabled.keys()) or '(无)'}",
    )


async def check_mcp_agent_sync() -> CheckResult:
    config = load_runtime_config()

    try:
        servers = filter_enabled_servers(config.mcp.servers)
        errors = validate_mcp_servers(servers)
        if errors:
            raise ValueError("; ".join(errors))
    except ValueError as exc:
        return CheckResult("mcp_agent_sync", False, str(exc), optional=True)

    engine_cfg = config.engine
    if os.environ.get("OH_SESSION_API_KEYS_0"):
        engine_cfg = engine_cfg.model_copy(
            update={"session_api_key": os.environ["OH_SESSION_API_KEYS_0"]}
        )

    server = f"http://{engine_cfg.agent_server_host}:{engine_cfg.agent_server_port}"

    try:
        async with httpx.AsyncClient(timeout=5.0, trust_env=False) as client:
            health = await client.get(f"{server}/health")
            if health.status_code >= 400:
                return CheckResult(
                    "mcp_agent_sync",
                    True,
                    f"Agent Server 未运行，跳过 ({server})",
                    optional=True,
                )
    except httpx.HTTPError:
        return CheckResult(
            "mcp_agent_sync",
            True,
            f"Agent Server 不可达，跳过 ({server})",
            optional=True,
        )

    engine = OpenHandsEngine(
        engine_cfg,
        llm_model=os.environ.get("LLM_MODEL", "openai/deepseek-v4-flash"),
        llm_api_key=os.environ.get("LLM_API_KEY", "verify-placeholder"),
        llm_base_url=os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1"),
        workspace_dir=PROJECT_ROOT / "workspace" / "project",
    )

    probe_name = "deepticket-sync-probe"
    probe_servers = {
        probe_name: {
            "transport": "stdio",
            "command": "true",
            "args": [],
            "description": "DeepTicket verify 同步探针（非真实 MCP）",
        }
    }
    used_probe = not servers
    targets = servers if servers else probe_servers

    try:
        await engine.sync_mcp_config(targets)
    except RuntimeError as exc:
        return CheckResult("mcp_agent_sync", False, str(exc))

    headers = engine.build_headers()
    try:
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            resp = await client.get(f"{server}/api/settings", headers=headers)
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPError as exc:
        return CheckResult("mcp_agent_sync", False, f"读取 Agent settings 失败: {exc}")

    remote_mcp = (payload.get("agent_settings") or {}).get("mcp_config") or {}
    if not isinstance(remote_mcp, dict):
        return CheckResult("mcp_agent_sync", False, "Agent settings 中 mcp_config 格式异常")

    missing = [name for name in targets if name not in remote_mcp]
    if missing:
        return CheckResult(
            "mcp_agent_sync",
            False,
            f"已同步但 Agent 缺少 MCP 项: {', '.join(missing)}",
        )

    if used_probe:
        try:
            await engine.sync_mcp_config(servers)
        except RuntimeError as exc:
            return CheckResult(
                "mcp_agent_sync",
                False,
                f"探针验证通过，但恢复实际 MCP 配置失败: {exc}",
            )
        return CheckResult(
            "mcp_agent_sync",
            True,
            "MCP 同步通路正常（探针验证后已恢复实际配置）",
            optional=False,
        )

    return CheckResult(
        "mcp_agent_sync",
        True,
        f"已同步到 Agent Server: {', '.join(servers.keys())}",
        optional=False,
    )


def check_auth_and_chat_storage() -> CheckResult:
    with tempfile.TemporaryDirectory() as tmp:
        storage = LocalStorage(Path(tmp))
        users = UserStore(storage)
        chats = ChatHistoryStore(storage)

        suffix = uuid.uuid4().hex[:8]
        username = f"verify_{suffix}"
        user = users.register(username, "verify-pass-123")
        _, token = users.login(username, "verify-pass-123")
        resolved = users.resolve_token(token)
        if resolved is None or resolved.uid != user.uid:
            return CheckResult("auth_chat", False, "登录 token 无法解析")

        thread = chats.create_thread(user.uid, title="verify")
        chats.append_message(user.uid, thread["chat_id"], role="user", content="ping")
        doc = chats.get_thread(user.uid, thread["chat_id"])
        if not doc or len(doc["messages"]) != 1:
            return CheckResult("auth_chat", False, "聊天记录写入失败")

        other = users.register(f"other_{suffix}", "verify-pass-123")
        if chats.get_thread(other.uid, thread["chat_id"]) is not None:
            return CheckResult("auth_chat", False, "聊天未按 uid 隔离")

        return CheckResult("auth_chat", True, "注册/登录/聊天隔离正常")


async def check_web_health() -> CheckResult:
    host = os.environ.get("WEB_HOST", "127.0.0.1")
    port = os.environ.get("WEB_PORT", "8600")
    url = f"http://{host}:{port}/api/health"
    try:
        async with httpx.AsyncClient(timeout=3.0, trust_env=False) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError:
        return CheckResult(
            "web_health",
            True,
            f"Web 服务未运行，跳过 ({url})",
            optional=True,
        )

    if not data.get("ok"):
        return CheckResult("web_health", False, "health 返回 ok=false")
    return CheckResult(
        "web_health",
        True,
        f"Web 在线 · layers={len(data.get('layers', []))}",
        optional=True,
    )
