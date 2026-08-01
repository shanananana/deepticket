import pytest

from deepticket.config.routing_schema import RoutingConfig
from deepticket.layers.input.classifier import classify_ingress_event
from deepticket.layers.input.ingress_models import IngressEvent


@pytest.fixture
def routing() -> RoutingConfig:
    return RoutingConfig.model_validate(
        {
            "routes": [
                {
                    "type": "incident",
                    "match": {
                        "sources": ["monitor"],
                        "title_keywords": ["500"],
                    },
                    "outbound": {"method": "webhook"},
                },
                {
                    "type": "default",
                    "match": {"default": True},
                    "outbound": {"method": "store_only"},
                },
            ]
        }
    )


def test_classify_by_source_and_keyword(routing: RoutingConfig):
    event = IngressEvent(
        source="monitor",
        external_id="a1",
        title="API 500 spike",
        body="error rate high",
    )
    route = classify_ingress_event(event, routing)
    assert route.type == "incident"


def test_classify_explicit_type(routing: RoutingConfig):
    event = IngressEvent(
        source="anything",
        external_id="a2",
        title="hello",
        body="world",
        type="default",
    )
    route = classify_ingress_event(event, routing)
    assert route.type == "default"


def test_classify_unknown_explicit_type_raises(routing: RoutingConfig):
    event = IngressEvent(
        source="x",
        external_id="a3",
        title="t",
        body="b",
        type="unknown-type",
    )
    with pytest.raises(ValueError, match="未知路由类型"):
        classify_ingress_event(event, routing)


def test_classify_fallback_default(routing: RoutingConfig):
    event = IngressEvent(
        source="email",
        external_id="a4",
        title="weekly report",
        body="stats attached",
    )
    route = classify_ingress_event(event, routing)
    assert route.type == "default"
