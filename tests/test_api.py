from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from deepticket.core.app_factory import create_app
from deepticket.service import DeepTicketService


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    async def _noop_startup(self: DeepTicketService) -> None:
        self.users.ensure_bootstrap_user("admin", "admin")

    monkeypatch.setattr(DeepTicketService, "startup", _noop_startup)
    with TestClient(create_app()) as test_client:
        yield test_client


def test_health_endpoint(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["project"] == "deepticket"
    assert "layers" in data


def test_auth_register_login_flow(client: TestClient):
    username = f"pytest_{uuid.uuid4().hex[:8]}"
    password = "pytest-pass-123"

    reg = client.post(
        "/api/auth/register",
        json={"username": username, "password": password},
    )
    assert reg.status_code == 200

    login = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert login.status_code == 200
    token = login.json()["token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["user"]["username"] == username

    chats = client.get("/api/chats", headers={"Authorization": f"Bearer {token}"})
    assert chats.status_code == 200


def test_protected_route_requires_auth(client: TestClient):
    resp = client.get("/api/chats")
    assert resp.status_code == 401


def _register_and_login(client: TestClient, username: str, password: str = "pw-123456") -> str:
    client.post("/api/auth/register", json={"username": username, "password": password})
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()["token"]


def test_chat_rename_flow(client: TestClient):
    token = _register_and_login(client, f"rename_{uuid.uuid4().hex[:6]}")
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post("/api/chats", json={"title": "旧名字"}, headers=headers)
    chat_id = created.json()["chat"]["chat_id"]

    renamed = client.patch(
        f"/api/chats/{chat_id}",
        json={"title": "新名字"},
        headers=headers,
    )
    assert renamed.status_code == 200
    assert renamed.json()["chat"]["title"] == "新名字"

    got = client.get(f"/api/chats/{chat_id}", headers=headers)
    assert got.json()["chat"]["title"] == "新名字"


def test_chat_isolation_between_users(client: TestClient):
    t1 = _register_and_login(client, f"iso_a_{uuid.uuid4().hex[:6]}")
    t2 = _register_and_login(client, f"iso_b_{uuid.uuid4().hex[:6]}")

    h1 = {"Authorization": f"Bearer {t1}"}
    created = client.post("/api/chats", json={"title": "私有"}, headers=h1)
    chat_id = created.json()["chat"]["chat_id"]

    # 用户 B 无法访问用户 A 的会话
    resp = client.get(f"/api/chats/{chat_id}", headers={"Authorization": f"Bearer {t2}"})
    assert resp.status_code == 404
    resp = client.delete(f"/api/chats/{chat_id}", headers={"Authorization": f"Bearer {t2}"})
    assert resp.status_code == 404


def test_default_admin_created(client: TestClient):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert resp.status_code == 200
    assert resp.json()["user"]["username"] == "admin"
