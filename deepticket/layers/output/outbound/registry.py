from __future__ import annotations

import json
import logging
import os
from typing import Protocol

import httpx

from deepticket.config.routing_loader import resolve_outbound_url
from deepticket.config.routing_schema import OutboundConfig
from deepticket.layers.output.outbound_models import OutboundPayload, OutboundResult

logger = logging.getLogger(__name__)


class OutboundHandler(Protocol):
    async def deliver(
        self,
        payload: OutboundPayload,
        config: OutboundConfig,
    ) -> OutboundResult: ...


class StoreOnlyOutbound:
    async def deliver(
        self,
        payload: OutboundPayload,
        config: OutboundConfig,
    ) -> OutboundResult:
        return OutboundResult(method="store_only", ok=True, detail="结果已写入 DeepTicket 存储")


class WebhookOutbound:
    async def deliver(
        self,
        payload: OutboundPayload,
        config: OutboundConfig,
    ) -> OutboundResult:
        url = resolve_outbound_url(config.url, config.url_env)
        if not url:
            env_hint = config.url_env or "(未配置 url / url_env)"
            return OutboundResult(
                method="webhook",
                ok=False,
                detail=f"Webhook URL 未配置: {env_hint}",
            )

        logger.info(
            "Webhook 投递请求: url=%s external_id=%s job_id=%s",
            url,
            payload.external_id,
            payload.job_id,
        )

        headers = {"Content-Type": "application/json"}
        extra_env = config.extra_headers_env.strip()
        if extra_env:
            raw = os.environ.get(extra_env, "").strip()
            if raw:
                try:
                    headers.update(json.loads(raw))
                except json.JSONDecodeError as exc:
                    return OutboundResult(
                        method="webhook",
                        ok=False,
                        detail=f"Webhook 头配置 JSON 无效 ({extra_env}): {exc}",
                    )

        body = {
            "job_id": payload.job_id,
            "type": payload.route_type,
            "source": payload.source,
            "external_id": payload.external_id,
            "status": payload.status,
            "reply": payload.reply,
            "conversation_id": payload.conversation_id,
            "error": payload.error,
            "metadata": payload.metadata,
        }

        try:
            async with httpx.AsyncClient(
                timeout=config.timeout_seconds,
                trust_env=False,
            ) as client:
                resp = await client.post(url, headers=headers, json=body)
        except httpx.HTTPError as exc:
            logger.error("Webhook 投递失败: %s", exc)
            return OutboundResult(method="webhook", ok=False, detail=str(exc))

        if resp.status_code >= 400:
            logger.warning(
                "Webhook 响应失败: url=%s status=%s external_id=%s",
                url,
                resp.status_code,
                payload.external_id,
            )
            return OutboundResult(
                method="webhook",
                ok=False,
                detail=resp.text[:500],
                response_status=resp.status_code,
            )
        logger.info(
            "Webhook 响应成功: url=%s status=%s external_id=%s",
            url,
            resp.status_code,
            payload.external_id,
        )
        return OutboundResult(
            method="webhook",
            ok=True,
            detail="已回调外部系统",
            response_status=resp.status_code,
        )


_OUTBOUND_HANDLERS: dict[str, OutboundHandler] = {
    "store_only": StoreOnlyOutbound(),
    "webhook": WebhookOutbound(),
}


def get_outbound_handler(method: str) -> OutboundHandler:
    handler = _OUTBOUND_HANDLERS.get(method)
    if handler is None:
        raise ValueError(f"未知 outbound method: {method}")
    return handler
