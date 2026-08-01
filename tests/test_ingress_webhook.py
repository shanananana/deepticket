from __future__ import annotations

import json
import logging
import threading
from collections.abc import AsyncIterator, Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from deepticket.core.app_factory import create_app
from deepticket.layers.output.models import StreamChunk
from deepticket.service import DeepTicketService


class _WebhookHandler(BaseHTTPRequestHandler):
    received: list[dict] = []

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        type(self).received.append(payload)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"{}")


@pytest.fixture
def webhook_server() -> Iterator[tuple[str, list[dict]]]:
    _WebhookHandler.received = []
    server = HTTPServer(("127.0.0.1", 0), _WebhookHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}/callback", _WebhookHandler.received
    server.shutdown()


def _write_test_config(path: Path, *, webhook_url: str) -> None:
    example = Path("deepticket.example.yaml")
    data = yaml.safe_load(example.read_text(encoding="utf-8"))
    data["llm"]["api_key"] = "test-api-key"
    for route in data["ingress"]["routes"]:
        if route.get("type") == "ticket":
            route["outbound"]["url"] = webhook_url
            route["outbound"]["url_env"] = ""
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


@pytest.fixture
def ingress_client(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    webhook_server: tuple[str, list[dict]],
) -> Iterator[TestClient]:
    webhook_url, _received = webhook_server
    config_path = tmp_path / "deepticket.yaml"
    _write_test_config(config_path, webhook_url=webhook_url)
    monkeypatch.setenv("DEEPTICKET_CONFIG", str(config_path))

    async def _noop_startup(self: DeepTicketService) -> None:
        return None

    async def _fake_stream(self, agent_input) -> AsyncIterator[StreamChunk]:
        del agent_input
        yield StreamChunk(delta="根因：下游依赖超时。", conversation_id="conv-test-1")

    monkeypatch.setattr(DeepTicketService, "startup", _noop_startup)
    monkeypatch.setattr(DeepTicketService, "_run_stream", _fake_stream)

    with TestClient(create_app()) as test_client:
        yield test_client


def test_ingress_ticket_webhook_roundtrip(
    ingress_client: TestClient,
    webhook_server: tuple[str, list[dict]],
    caplog: pytest.LogCaptureFixture,
):
    _url, received = webhook_server
    caplog.set_level(logging.INFO)
    resp = ingress_client.post(
        "/api/ingress/events",
        json={
            "source": "jira",
            "external_id": "T-9001",
            "title": "接口 500",
            "body": "订单服务报错，请分析",
            "type": "ticket",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["route_type"] == "ticket"
    assert data["outbound_method"] == "webhook"
    assert data["outbound_ok"] is True
    assert "根因" in data["reply"]

    assert len(received) == 1
    callback = received[0]
    assert callback["external_id"] == "T-9001"
    assert callback["source"] == "jira"
    assert callback["type"] == "ticket"
    assert callback["reply"]

    messages = [record.getMessage() for record in caplog.records]
    assert any("Ingress 收到事件" in msg for msg in messages)
    assert any("Ingress 任务完成" in msg for msg in messages)
    assert any("Webhook 投递请求" in msg for msg in messages)
    assert any("Webhook 响应成功" in msg for msg in messages)

    job_id = data["job_id"]
    fetched = ingress_client.get(f"/api/ingress/jobs/{job_id}")
    assert fetched.status_code == 200
    assert fetched.json()["job_id"] == job_id
