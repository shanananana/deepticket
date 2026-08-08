from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from deepticket.config.schema import AppConfig
from deepticket.layers.storage.local import LocalStorage
from deepticket.projects.models import ProjectMemberRecord
from deepticket.projects.permissions import ProjectPermissionStore
from deepticket.projects.store import ProjectConfigStore


def test_project_config_redis_merge(tmp_path):
    storage = LocalStorage(str(tmp_path / "data"))
    store = ProjectConfigStore(storage, AppConfig())
    store.ensure_default_project()

    saved = store.patch_extensions("default", agents_md="你是 SRE 助手")
    assert "SRE" in saved.extensions.agents_md
    raw = store.get_raw("default")
    assert raw is not None
    assert "knowledge" not in raw
    assert raw["extensions"]["agents_md"] == "你是 SRE 助手"


def test_yaml_fallback_when_redis_missing(tmp_path):
    storage = LocalStorage(str(tmp_path / "data"))
    app_config = AppConfig()
    app_config.knowledge.repos = []
    app_config.mcp.servers = {
        "yaml-mcp": {"transport": "stdio", "command": "echo", "enabled": True}
    }
    store = ProjectConfigStore(storage, app_config)
    store.ensure_default_project()

    assert store.get_raw("default") is None
    resolved = store.get("default")
    assert resolved is not None
    assert "yaml-mcp" in resolved.mcp.servers


def test_patch_mcp_merge_without_touching_repos(tmp_path):
    storage = LocalStorage(str(tmp_path / "data"))
    store = ProjectConfigStore(storage, AppConfig())
    store.ensure_default_project()

    store.patch_knowledge(
        "default",
        [{"id": "repo-a", "url": "https://example.com/a.git", "key": "", "branch": "main"}],
    )
    store.patch_mcp(
        "default",
        {"proj-mcp": {"transport": "stdio", "command": "my-mcp", "enabled": True}},
    )

    raw = store.get_raw("default")
    assert raw is not None
    assert raw["knowledge"]["repos"][0]["id"] == "repo-a"
    assert "proj-mcp" in raw["mcp"]["servers"]
    assert "knowledge" in raw
    assert "mcp" in raw
    assert "name" not in raw


def test_project_permissions_revoke_on_replace(tmp_path):
    storage = LocalStorage(str(tmp_path / "data"))
    perms = ProjectPermissionStore(storage)
    perms.set_members("demo", [ProjectMemberRecord(uid="uid-a", username="alice")])
    assert perms.user_has_access("uid-a", "demo") is True
    perms.set_members("demo", [ProjectMemberRecord(uid="uid-b", username="bob")])
    assert perms.user_has_access("uid-a", "demo") is False
    assert perms.user_has_access("uid-b", "demo") is True


def test_project_permissions(tmp_path):
    storage = LocalStorage(str(tmp_path / "data"))
    perms = ProjectPermissionStore(storage)
    perms.set_members(
        "demo",
        [],
    )
    perms.grant("uid-a", "demo")
    assert perms.user_has_access("uid-a", "demo") is True
    assert perms.user_has_access("uid-b", "demo") is False


def test_create_second_project_and_patch_sections(client: TestClient):
    token = client.post(
        "/api/auth/login", json={"username": "admin", "password": "admin"}
    ).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    project_id = f"proj_{uuid.uuid4().hex[:6]}"
    resp = client.put(
        f"/api/admin/projects/{project_id}",
        headers=headers,
        json={
            "id": project_id,
            "name": "测试项目",
            "description": "multi-project",
            "enabled": True,
            "knowledge": {"repos": []},
            "mcp": {"servers": {}},
            "extensions": {"agents_md": "项目专用 agents.md", "user_skills_dir": ""},
        },
    )
    assert resp.status_code == 200
    listed = client.get("/api/projects", headers=headers)
    assert listed.status_code == 200
    ids = {item["id"] for item in listed.json()["projects"]}
    assert project_id in ids

    mcp_resp = client.patch(
        f"/api/admin/projects/{project_id}/mcp",
        headers=headers,
        json={
            "servers": {
                "only-one": {"transport": "stdio", "command": "tool", "enabled": True}
            }
        },
    )
    assert mcp_resp.status_code == 200
    raw = client.get(f"/api/admin/projects/{project_id}", headers=headers).json()
    assert raw["raw"]["mcp"]["servers"]["only-one"]["command"] == "tool"
    assert raw["project"]["extensions"]["agents_md"] == "项目专用 agents.md"

    chat = client.post(
        "/api/chats",
        headers=headers,
        json={"title": "项目会话", "project_id": project_id},
    )
    assert chat.status_code == 200
    assert chat.json()["chat"]["project_id"] == project_id
