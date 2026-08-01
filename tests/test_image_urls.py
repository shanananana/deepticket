from __future__ import annotations

from deepticket.layers.engine.openhands_engine import OpenHandsEngine
from deepticket.layers.input.adapter import InputAdapter
from deepticket.layers.input.image_urls import normalize_image_urls
from deepticket.layers.input.ingress_adapter import IngressAdapter
from deepticket.layers.input.ingress_models import IngressEvent
from deepticket.layers.input.models import AgentInput, TicketInput
from deepticket.config.routing_schema import OutboundConfig, RouteConfig, RouteMatchConfig


def test_normalize_image_urls_filters_invalid() -> None:
    urls = normalize_image_urls(
        [
            "https://example.com/a.png",
            "ftp://bad.example/x.png",
            "not-a-url",
            "https://example.com/a.png",
        ]
    )
    assert urls == ["https://example.com/a.png"]


def test_ingress_adapter_passes_image_urls() -> None:
    route = RouteConfig(
        type="ticket",
        description="test",
        match=RouteMatchConfig(sources=["jira"]),
        outbound=OutboundConfig(method="store_only"),
    )
    event = IngressEvent(
        source="jira",
        external_id="IMG-1",
        title="截图报错",
        body="页面白屏",
        image_urls=["https://example.com/screen.png"],
        metadata={"image_urls": ["https://example.com/ignored-dup.png"]},
    )
    ticket = IngressAdapter.to_ticket(event, route)
    assert ticket.image_urls == [
        "https://example.com/screen.png",
        "https://example.com/ignored-dup.png",
    ]


def test_input_adapter_builds_multimodal_agent_input() -> None:
    ticket = TicketInput(
        ticket_id="T-1",
        title="UI 异常",
        description="按钮点击无响应",
        image_urls=["https://example.com/ui.png"],
    )
    agent_input = InputAdapter.from_ticket(ticket)
    assert agent_input.image_urls == ["https://example.com/ui.png"]
    assert "附件图片" in agent_input.prompt


def test_openhands_engine_multimodal_payload() -> None:
    from deepticket.config.schema import EngineConfig

    engine = OpenHandsEngine(
        EngineConfig(),
        llm_model="openai/deepseek-v4-flash",
        llm_api_key="k",
        llm_base_url="https://api.deepseek.com/v1",
    )
    content = engine._build_user_message(
        AgentInput(
            prompt="hello",
            image_urls=["https://example.com/a.png"],
        )
    )
    assert isinstance(content, list)
    assert content[0]["type"] == "text"
    assert content[1]["type"] == "image_url"
