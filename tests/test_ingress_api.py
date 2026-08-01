from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from deepticket.core.app_factory import create_app
from deepticket.layers.ingress.pipeline import IngressJobResult
from deepticket.service import DeepTicketService


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    async def _noop_startup(self: DeepTicketService) -> None:
        return None

    monkeypatch.setattr(DeepTicketService, "startup", _noop_startup)
    with TestClient(create_app()) as test_client:
        yield test_client


def test_ingress_accepts_event(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    fake_result = IngressJobResult(
        job_id="job123",
        route_type="incident",
        source="monitor",
        external_id="x1",
        status="finished",
        reply="analysis done",
        conversation_id="conv-1",
        outbound_method="store_only",
        outbound_ok=True,
        outbound_detail="stored",
        metadata={},
    )
    monkeypatch.setattr(
        DeepTicketService,
        "run_ingress_event",
        AsyncMock(return_value=fake_result),
    )
    resp = client.post(
        "/api/ingress/events",
        json={
            "source": "monitor",
            "external_id": "x1",
            "title": "500 error",
            "body": "details",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["job_id"] == "job123"
    assert data["route_type"] == "incident"
    assert data["reply"] == "analysis done"


def test_ingress_list_routes(client: TestClient):
    resp = client.get("/api/ingress/routes")
    assert resp.status_code == 200
    assert "routes" in resp.json()
