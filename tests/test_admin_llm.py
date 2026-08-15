from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from deepticket.config.llm_loader import LlmConfig
from deepticket.core.app_factory import create_app
from deepticket.service import DeepTicketService


@pytest.fixture
def client_no_llm(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
    config_path = tmp_path / "deepticket.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "llm": {
                    "api_key": "",
                    "model": "openai/test-model",
                    "base_url": "http://127.0.0.1:1",
                    "label": "Test Model",
                },
                "storage": {
                    "backend": "local",
                    "local": {"root": str(tmp_path / "data")},
                },
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DEEPTICKET_CONFIG", str(config_path))
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    async def _noop_startup(self: DeepTicketService) -> None:
        bootstrap_user = self.users.ensure_bootstrap_user(
            self.config.auth.bootstrap_username,
            self.config.auth.bootstrap_password,
        )
        if bootstrap_user is not None:
            self.projects.bootstrap(
                bootstrap_uid=bootstrap_user.uid,
                bootstrap_username=bootstrap_user.username,
            )
        else:
            self.projects.config_store.ensure_default_project()

    async def _fake_apply_llm(self: DeepTicketService, llm: LlmConfig) -> None:
        self.llm_label = llm.label
        self.engine.llm_model = llm.model
        self.engine.llm_api_key = llm.api_key
        self.engine.llm_base_url = llm.base_url

    monkeypatch.setattr(DeepTicketService, "startup", _noop_startup)
    monkeypatch.setattr(DeepTicketService, "apply_llm_config", _fake_apply_llm)

    with TestClient(create_app()) as test_client:
        yield test_client


def test_health_without_llm(client_no_llm: TestClient):
    resp = client_no_llm.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["llm_configured"] is False
    assert data["model_label"] == "未配置"


def test_chat_requires_llm(client_no_llm: TestClient):
    token = client_no_llm.post(
        "/api/auth/login", json={"username": "admin", "password": "admin"}
    ).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    chat_id = client_no_llm.post(
        "/api/chats",
        json={"project_id": "default", "title": "t"},
        headers=headers,
    ).json()["chat"]["chat_id"]
    resp = client_no_llm.post(
        "/api/chat?project_id=default",
        json={"chat_id": chat_id, "message": "hello"},
        headers=headers,
    )
    assert resp.status_code == 503


def test_admin_update_llm(client_no_llm: TestClient):
    token = client_no_llm.post(
        "/api/auth/login", json={"username": "admin", "password": "admin"}
    ).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    get_resp = client_no_llm.get("/api/admin/llm", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["configured"] is False

    put_resp = client_no_llm.put(
        "/api/admin/llm",
        headers=headers,
        json={
            "api_key": "sk-test-key",
            "model": "openai/test-model",
            "base_url": "http://127.0.0.1:1",
            "label": "Test Model",
        },
    )
    assert put_resp.status_code == 200
    body = put_resp.json()
    assert body["configured"] is True

    health = client_no_llm.get("/api/health").json()
    assert health["llm_configured"] is True

    config_path = Path(get_resp.json()["config_path"])
    saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert saved["llm"]["api_key"] == "sk-test-key"
