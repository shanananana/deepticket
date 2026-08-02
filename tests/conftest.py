from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("DEEPTICKET_CONFIG", str(tmp_path / "missing-deepticket.yaml"))
    monkeypatch.setenv("LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("LLM_MODEL", "openai/test-model")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("INGRESS_API_KEY", "test-ingress-key")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


INGRESS_AUTH_HEADERS = {"X-Ingress-API-Key": "test-ingress-key"}
