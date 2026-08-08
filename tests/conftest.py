from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from deepticket.core.app_factory import create_app
from deepticket.service import DeepTicketService


@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("DEEPTICKET_CONFIG", str(tmp_path / "missing-deepticket.yaml"))
    monkeypatch.setenv("LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("LLM_MODEL", "openai/test-model")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("INGRESS_API_KEY", "test-ingress-key")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
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

    monkeypatch.setattr(DeepTicketService, "startup", _noop_startup)
    with TestClient(create_app()) as test_client:
        test_client.app.state.deepticket.service.config.auth.register_enabled = True
        yield test_client


INGRESS_AUTH_HEADERS = {"X-Ingress-API-Key": "test-ingress-key"}
