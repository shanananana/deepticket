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
            "/api/uploads/images/" + "a" * 32 + ".png",
            "http://127.0.0.1:8600/api/uploads/images/" + "b" * 32 + ".jpg",
        ]
    )
    assert urls == [
        "https://example.com/a.png",
        "/api/uploads/images/" + "a" * 32 + ".png",
        "/api/uploads/images/" + "b" * 32 + ".jpg",
    ]


def test_resolve_image_urls_for_agent() -> None:
    from deepticket.layers.input.image_urls import resolve_image_urls_for_agent

    relative = "/api/uploads/images/" + "c" * 32 + ".webp"
    resolved = resolve_image_urls_for_agent(
        [
            relative,
            "https://example.com/external.png",
            "http://localhost:8600/api/uploads/images/" + "d" * 32 + ".png",
        ],
        public_base_url="http://127.0.0.1:8600",
    )
    assert resolved == [
        "http://127.0.0.1:8600/api/uploads/images/" + "c" * 32 + ".webp",
        "https://example.com/external.png",
        "http://127.0.0.1:8600/api/uploads/images/" + "d" * 32 + ".png",
    ]


def test_inline_local_upload_images(tmp_path) -> None:
    from deepticket.layers.input.image_urls import inline_local_upload_images

    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
    )
    filename = "c" * 32 + ".png"
    (tmp_path / filename).write_bytes(png)
    inlined = inline_local_upload_images(
        [
            f"/api/uploads/images/{filename}",
            "https://example.com/external.png",
        ],
        uploads_dir=tmp_path,
    )
    assert inlined[0].startswith("data:image/png;base64,")
    assert inlined[1] == "https://example.com/external.png"


def test_inline_local_upload_images_missing_file(tmp_path) -> None:
    from deepticket.layers.input.image_urls import inline_local_upload_images

    filename = "d" * 32 + ".jpg"
    try:
        inline_local_upload_images(
            [f"/api/uploads/images/{filename}"],
            uploads_dir=tmp_path,
        )
    except RuntimeError as exc:
        assert "本地截图不存在" in str(exc)
    else:
        raise AssertionError("expected missing upload to fail")


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
        workspace_dir="/tmp/deepticket-workspace",
    )
    content = engine._message_content(
        AgentInput(
            prompt="hello",
            image_urls=["https://example.com/a.png"],
        )
    )
    assert isinstance(content, list)
    assert content[0]["type"] == "text"
    assert content[1]["type"] == "image"
    assert content[1]["image_urls"] == ["https://example.com/a.png"]
