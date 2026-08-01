from __future__ import annotations

from deepticket.config.routing_schema import RouteConfig, RoutingConfig
from deepticket.layers.input.ingress_models import IngressEvent


def classify_ingress_event(
    event: IngressEvent,
    routing: RoutingConfig,
) -> RouteConfig:
    """按配置规则判定事件类型；显式 type 优先，否则规则匹配，最后 default。"""
    if event.type:
        explicit = routing.route_for_type(event.type)
        if explicit is not None:
            return explicit
        raise ValueError(f"未知路由类型: {event.type}")

    haystack = f"{event.title}\n{event.body}".lower()
    title_lower = event.title.lower()
    source_lower = event.source.lower()

    for route in routing.routes:
        if route.match.default:
            continue
        match_cfg = route.match
        if match_cfg.sources and source_lower not in {
            item.lower() for item in match_cfg.sources
        }:
            continue
        if match_cfg.title_keywords and not any(
            kw.lower() in title_lower for kw in match_cfg.title_keywords
        ):
            continue
        if match_cfg.body_keywords and not any(
            kw.lower() in haystack for kw in match_cfg.body_keywords
        ):
            continue
        return route

    default_route = routing.default_route()
    if default_route is None:
        raise ValueError("routing 配置为空，无法分类")
    return default_route
