#!/usr/bin/env python3
"""最小 token 连续对话验证：模拟 OpenHands 丢上下文后从 Redis 恢复。"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deepticket.config.loader import load_app_config  # noqa: E402
from deepticket.layers.storage import create_storage  # noqa: E402
from deepticket.layers.storage.chat_history import ChatHistoryStore  # noqa: E402
from deepticket.paths import PROJECT_ROOT  # noqa: E402

WEB = "http://127.0.0.1:8600"
PROJECT = "default"
SECRET = "Q"
TURN1 = f"请只回复字母{SECRET}，不要任何其它字符。"
TURN2 = "第一条用户消息让你回复的字母是什么？只答一个英文字母。"


def parse_sse(text: str) -> tuple[str, str | None]:
    deltas: list[str] = []
    conv_id: str | None = None
    for raw in text.split("\n"):
        line = raw.strip()
        if line.startswith("event: meta"):
            continue
        if line.startswith("data: ") and '"conversation_id"' in line:
            try:
                conv_id = json.loads(line[6:]).get("conversation_id")
            except json.JSONDecodeError:
                pass
            continue
        if not line.startswith("data: "):
            continue
        payload = line[6:].strip()
        if payload == "[DONE]":
            break
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue
        delta = data.get("choices", [{}])[0].get("delta", {}).get("content")
        if isinstance(delta, str) and delta:
            deltas.append(delta)
    return "".join(deltas), conv_id


def wait_idle(client: httpx.Client, headers: dict[str, str], chat_id: str) -> None:
    for _ in range(120):
        resp = client.get(
            f"{WEB}/api/chats/{chat_id}/status",
            headers=headers,
            params={"project_id": PROJECT},
        )
        resp.raise_for_status()
        if resp.json()["status"].get("agent_run_status") == "idle":
            return
        time.sleep(1)
    raise RuntimeError("等待 Agent 空闲超时")


def main() -> int:
    cfg = load_app_config(PROJECT_ROOT)
    web_port = cfg.web.port
    global WEB
    WEB = f"http://{cfg.web.host}:{web_port}"

    with httpx.Client(timeout=180.0) as client:
        health = client.get(f"{WEB}/api/health")
        health.raise_for_status()
        if not health.json().get("llm_configured"):
            print("FAIL: LLM 未配置")
            return 1

        login = client.post(
            f"{WEB}/api/auth/login",
            json={"username": "admin", "password": "admin"},
        )
        login.raise_for_status()
        token = login.json()["token"]
        uid = login.json()["user"]["uid"]
        headers = {"Authorization": f"Bearer {token}"}

        create = client.post(
            f"{WEB}/api/chats",
            headers=headers,
            json={"project_id": PROJECT, "title": "verify-continue"},
            params={"project_id": PROJECT},
        )
        create.raise_for_status()
        chat_id = create.json()["chat"]["chat_id"]
        print(f"chat_id={chat_id}")

        print("turn1 …")
        r1 = client.post(
            f"{WEB}/api/chat",
            headers=headers,
            json={"chat_id": chat_id, "message": TURN1, "project_id": PROJECT},
            params={"project_id": PROJECT},
        )
        r1.raise_for_status()
        reply1, conv1 = parse_sse(r1.text)
        wait_idle(client, headers, chat_id)
        print(f"turn1 reply={reply1!r} conv={conv1}")

        chat_doc = client.get(
            f"{WEB}/api/chats/{chat_id}",
            headers=headers,
            params={"project_id": PROJECT},
        ).json()["chat"]
        msgs = chat_doc.get("messages") or []
        assert len(msgs) >= 2, f"Redis 消息不足: {msgs}"
        old_conv = chat_doc.get("agent_conversation_id")
        print(f"redis messages={len(msgs)} agent_conversation_id={old_conv}")

        # 模拟老对话：OpenHands conversation 还在，但上下文已丢
        agent_host = cfg.engine.agent_server_host
        agent_port = cfg.engine.agent_server_port
        session_key = cfg.engine.session_api_key
        oh_headers = {"X-Session-API-Key": session_key} if session_key else {}
        workspace = str((PROJECT_ROOT / "workspace" / "default" / "project").resolve())
        shell = client.post(
            f"http://{agent_host}:{agent_port}/api/conversations",
            headers=oh_headers,
            json={
                "workspace": {"working_dir": workspace},
                "agent_settings": {},
                "autotitle": False,
            },
        )
        shell.raise_for_status()
        stale_conv = shell.json()["id"]
        storage = create_storage(cfg.storage)
        ChatHistoryStore(storage).set_agent_conversation_id(
            PROJECT, uid, chat_id, stale_conv
        )
        print(f"simulated stale OH conversation={stale_conv} (empty shell)")

        print("turn2 …")
        r2 = client.post(
            f"{WEB}/api/chat",
            headers=headers,
            json={"chat_id": chat_id, "message": TURN2, "project_id": PROJECT},
            params={"project_id": PROJECT},
        )
        r2.raise_for_status()
        reply2, conv2 = parse_sse(r2.text)
        wait_idle(client, headers, chat_id)
        print(f"turn2 reply={reply2!r} conv={conv2}")

        after = client.get(
            f"{WEB}/api/chats/{chat_id}",
            headers=headers,
            params={"project_id": PROJECT},
        ).json()["chat"]
        new_conv = after.get("agent_conversation_id")
        print(f"new agent_conversation_id={new_conv}")

        if conv2 and new_conv and conv2 != old_conv:
            print("OK: 已重建 OpenHands conversation")
        elif "<conversation_history>" in TURN2:
            pass
        else:
            print("note: conversation id may be reused if server merged sessions")

        letters = re.findall(r"[A-Za-z]", reply2)
        if SECRET in reply2.upper() or (letters and letters[0].upper() == SECRET):
            print(f"PASS: 连续对话上下文恢复成功（期望字母 {SECRET}）")
            return 0

        print(f"FAIL: 回复未包含期望字母 {SECRET}: {reply2!r}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
