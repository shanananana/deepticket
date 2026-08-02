from __future__ import annotations

import time
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from deepticket.core.app_factory import create_app
from deepticket.layers.output.models import StreamChunk
from deepticket.service import DeepTicketService
from tests.conftest import INGRESS_AUTH_HEADERS


def _write_client_config(path: Path) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "llm": {"api_key": "test-api-key"},
                "ingress": {
                    "api_key": "test-ingress-key",
                    "routes": [
                        {
                            "type": "default",
                            "match": {"default": True},
                            "outbound": {"method": "store_only"},
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )


def _wait_for_job(client: TestClient, job_id: str, *, timeout: float = 5.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(
            f"/api/ingress/jobs/{job_id}",
            headers=INGRESS_AUTH_HEADERS,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data["status"] in ("finished", "failed"):
                return data
        time.sleep(0.05)
    raise AssertionError(f"任务未在 {timeout}s 内完成: {job_id}")


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
    config_path = tmp_path / "deepticket.yaml"
    _write_client_config(config_path)
    monkeypatch.setenv("DEEPTICKET_CONFIG", str(config_path))

    async def _noop_startup(self: DeepTicketService) -> None:
        return None

    async def _fake_stream(self, agent_input) -> AsyncIterator[StreamChunk]:
        del agent_input
        yield StreamChunk(delta="analysis done", conversation_id="conv-1")

    monkeypatch.setattr(DeepTicketService, "startup", _noop_startup)
    monkeypatch.setattr(DeepTicketService, "_run_stream", _fake_stream)

    with TestClient(create_app()) as test_client:
        yield test_client


def test_ingress_requires_api_key(client: TestClient):
    resp = client.post(
        "/api/ingress/events",
        json={
            "source": "monitor",
            "external_id": "x1",
            "title": "500 error",
            "body": "details",
        },
    )
    assert resp.status_code == 401


def test_ingress_accepts_event_async(client: TestClient):
    resp = client.post(
        "/api/ingress/events",
        headers=INGRESS_AUTH_HEADERS,
        json={
            "source": "monitor",
            "external_id": "x1",
            "title": "500 error",
            "body": "details",
        },
    )
    assert resp.status_code == 202, resp.text
    data = resp.json()
    assert data["status"] == "queued"
    assert data["job_id"]

    finished = _wait_for_job(client, data["job_id"])
    assert finished["status"] == "finished"
    assert finished["reply"] == "analysis done"


def test_ingress_list_routes(client: TestClient):
    resp = client.get("/api/ingress/routes", headers=INGRESS_AUTH_HEADERS)
    assert resp.status_code == 200
    assert "routes" in resp.json()
