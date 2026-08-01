from __future__ import annotations

from deepticket.config.routing_schema import RouteConfig
from deepticket.layers.input.image_urls import (
    image_urls_from_metadata,
    normalize_image_urls,
)
from deepticket.layers.input.ingress_models import IngressEvent
from deepticket.layers.input.models import TicketInput


class IngressAdapter:
    """外部事件 → 内部 TicketInput（Agent 是否查代码由 Skill 判断，不在此硬编码）。"""

    @staticmethod
    def to_ticket(event: IngressEvent, route: RouteConfig) -> TicketInput:
        repo_ids = event.repo_ids or list(route.repo_ids)
        image_urls = normalize_image_urls(
            event.image_urls,
            image_urls_from_metadata(event.metadata),
        )
        description = event.body.strip()
        if route.prompt_suffix.strip():
            description = f"{description}\n\n{route.prompt_suffix.strip()}"

        return TicketInput(
            ticket_id=event.external_id,
            title=event.title.strip(),
            description=description,
            repo_ids=repo_ids,
            logs=event.logs.strip(),
            image_urls=image_urls,
            metadata={
                "source": event.source,
                "route_type": route.type,
                **event.metadata,
            },
        )
