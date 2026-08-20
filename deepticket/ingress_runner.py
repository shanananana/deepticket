from __future__ import annotations

import logging
import uuid
from dataclasses import asdict
from typing import TYPE_CHECKING

from deepticket.layers.ingress.pipeline import IngressJobResult, collect_stream_text
from deepticket.layers.ingress.queue import IngressJobQueue, IngressQueueItem
from deepticket.layers.input.classifier import classify_ingress_event
from deepticket.layers.input.ingress_adapter import IngressAdapter
from deepticket.layers.input.ingress_models import IngressEvent
from deepticket.layers.output.confidence import compute_confidence
from deepticket.layers.output.models import StreamChunk
from deepticket.layers.output.outbound.registry import get_outbound_handler
from deepticket.layers.output.outbound_models import OutboundPayload
from deepticket.layers.storage.json_index import count_indexed_keys, index_json_key, list_indexed_json_keys
from deepticket.observability.metrics import get_metrics
from deepticket.utils.time import utc_now_iso

if TYPE_CHECKING:
    from deepticket.service import DeepTicketService

logger = logging.getLogger(__name__)
_metrics = get_metrics()


class IngressRunner:
    """Ingress 入队、执行、出站与任务索引。"""

    NAMESPACE_INGRESS = "ingress_jobs"

    def __init__(self, service: DeepTicketService) -> None:
        self._service = service
        self._queue = IngressJobQueue(workers=service.config.ingress.queue_workers)
        _metrics.queue_backlog_alert = service.config.ingress.queue_backlog_alert

    @property
    def queue(self) -> IngressJobQueue:
        return self._queue

    def _persist_job(self, job_id: str, doc: dict) -> None:
        self._service.storage.set_json(self.NAMESPACE_INGRESS, job_id, doc)
        index_json_key(
            self._service.storage,
            self.NAMESPACE_INGRESS,
            job_id,
            sort_field="updated_at",
            doc=doc,
        )

    def list_recent_jobs(self, *, limit: int = 20) -> list[dict]:
        jobs: list[dict] = []
        for key in list_indexed_json_keys(
            self._service.storage,
            self.NAMESPACE_INGRESS,
            limit=limit,
            sort_field="updated_at",
        ):
            doc = self._service.storage.get_json(self.NAMESPACE_INGRESS, key)
            if not doc:
                continue
            jobs.append(
                {
                    "job_id": doc.get("job_id", key),
                    "status": doc.get("status", "unknown"),
                    "source": doc.get("source", ""),
                    "external_id": doc.get("external_id", ""),
                    "route_type": doc.get("route_type", ""),
                    "outbound_method": doc.get("outbound_method", ""),
                    "outbound_ok": doc.get("outbound_ok"),
                    "outbound_detail": (doc.get("outbound_detail") or "")[:120],
                }
            )
        return jobs

    def get_job(self, job_id: str) -> dict | None:
        return self._service.storage.get_json(self.NAMESPACE_INGRESS, job_id)

    def job_count(self) -> int:
        return count_indexed_keys(self._service.storage, self.NAMESPACE_INGRESS)

    async def mark_failed(
        self, job_id: str, *, error: str, event: IngressEvent | None = None
    ) -> None:
        existing = self._service.storage.get_json(self.NAMESPACE_INGRESS, job_id) or {}
        doc = {
            **existing,
            "job_id": job_id,
            "status": "failed",
            "reply": existing.get("reply") or "",
            "outbound_ok": False,
            "outbound_detail": error[:500],
            "metadata": {
                **(existing.get("metadata") or {}),
                "error": error,
            },
        }
        if event is not None:
            doc.setdefault("source", event.source)
            doc.setdefault("external_id", event.external_id)
        self._persist_job(job_id, doc)
        _metrics.record_ingress_job(ok=False)
        logger.error("Ingress 任务失败: job_id=%s error=%s", job_id, error)

    async def start_workers(self) -> None:
        await self._queue.start(
            self._process_item,
            on_failure=self._on_failure,
        )

    async def stop_workers(self) -> None:
        await self._queue.stop()

    async def _on_failure(self, item: IngressQueueItem, exc: BaseException) -> None:
        await self.mark_failed(item.job_id, error=str(exc), event=item.event)

    async def _process_item(self, item: IngressQueueItem) -> None:
        await self.run_event(item.event, job_id=item.job_id)

    async def submit(self, event: IngressEvent) -> IngressJobResult:
        self._service.require_llm_configured()
        route = classify_ingress_event(event, self._service.routing)
        ticket = IngressAdapter.to_ticket(event, route)
        job_id = uuid.uuid4().hex

        queued_doc = {
            "job_id": job_id,
            "route_type": route.type,
            "source": event.source,
            "external_id": event.external_id,
            "status": "queued",
            "reply": "",
            "conversation_id": None,
            "outbound_method": route.outbound.method,
            "outbound_ok": False,
            "outbound_detail": "已入队，等待处理",
            "metadata": ticket.metadata,
            "updated_at": utc_now_iso(),
        }
        self._persist_job(job_id, queued_doc)
        await self._queue.enqueue(IngressQueueItem(job_id=job_id, event=event))
        logger.info(
            "Ingress 任务入队: job_id=%s source=%s external_id=%s route=%s queue=%s",
            job_id,
            event.source,
            event.external_id,
            route.type,
            self._queue.qsize(),
        )
        payload = {k: v for k, v in queued_doc.items() if k != "updated_at"}
        return IngressJobResult(**payload)

    @staticmethod
    def _confidence_chunk(
        *,
        activities: list[dict[str, str]],
        reply: str,
        ok: bool = True,
    ) -> StreamChunk:
        return StreamChunk(
            confidence=compute_confidence(
                activities=activities,
                reply=reply,
                ok=ok,
            )
        )

    async def run_event(
        self,
        event: IngressEvent,
        *,
        job_id: str | None = None,
    ) -> IngressJobResult:
        route = classify_ingress_event(event, self._service.routing)
        ticket = IngressAdapter.to_ticket(event, route)
        if job_id is None:
            job_id = uuid.uuid4().hex
            running_doc = {
                "job_id": job_id,
                "route_type": route.type,
                "source": event.source,
                "external_id": event.external_id,
                "status": "running",
                "metadata": ticket.metadata,
            }
            self._persist_job(job_id, running_doc)
        else:
            existing = self._service.storage.get_json(self.NAMESPACE_INGRESS, job_id) or {}
            existing.update(
                {
                    "job_id": job_id,
                    "route_type": route.type,
                    "source": event.source,
                    "external_id": event.external_id,
                    "status": "running",
                    "metadata": ticket.metadata,
                }
            )
            self._persist_job(job_id, existing)

        logger.info(
            "Ingress 开始处理: job_id=%s source=%s external_id=%s route=%s",
            job_id,
            event.source,
            event.external_id,
            route.type,
        )

        reply = ""
        conversation_id: str | None = None
        confidence: dict | None = None
        error: str | None = None
        status = "finished"

        try:
            default_project = self._service.projects.require(
                self._service.projects.config_store.default_project_id()
            )
            reply, conversation_id, confidence = await collect_stream_text(
                self._service.chat.run_ticket_stream(ticket, project=default_project)
            )
        except Exception as exc:
            status = "failed"
            error = str(exc)
            logger.error("Ingress 任务 Agent 失败 (%s): %s", job_id, exc)

        outbound_payload = OutboundPayload(
            job_id=job_id,
            route_type=route.type,
            source=event.source,
            external_id=event.external_id,
            status=status,
            reply=reply,
            conversation_id=conversation_id,
            error=error,
            metadata={
                **ticket.metadata,
                **({"confidence": confidence} if confidence else {}),
            },
        )
        handler = get_outbound_handler(route.outbound.method)
        outbound_result = await handler.deliver(outbound_payload, route.outbound)
        logger.info(
            "Ingress 任务完成: job_id=%s status=%s outbound=%s ok=%s detail=%s",
            job_id,
            status,
            route.outbound.method,
            outbound_result.ok,
            outbound_result.detail,
        )

        result = IngressJobResult(
            job_id=job_id,
            route_type=route.type,
            source=event.source,
            external_id=event.external_id,
            status=status,
            reply=reply,
            conversation_id=conversation_id,
            outbound_method=route.outbound.method,
            outbound_ok=outbound_result.ok,
            outbound_detail=outbound_result.detail,
            metadata={
                **ticket.metadata,
                **({"confidence": confidence} if confidence else {}),
                "outbound_response_status": outbound_result.response_status,
                "error": error,
            },
        )
        persisted = asdict(result)
        persisted["updated_at"] = utc_now_iso()
        self._persist_job(job_id, persisted)
        _metrics.record_ingress_job(ok=status == "finished")
        if route.outbound.method == "webhook":
            _metrics.record_webhook(ok=outbound_result.ok)
        return result
