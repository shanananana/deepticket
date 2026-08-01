from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request

from deepticket.api.deps import get_service
from deepticket.api.schemas import (
    IngressEventRequest,
    IngressJobResponse,
)
from deepticket.layers.input.ingress_models import IngressEvent

router = APIRouter(prefix="/api/ingress", tags=["Ingress"])


@router.get("/routes")
async def list_routes(request: Request) -> dict:
    service = get_service(request)
    return {"routes": service.list_routes()}


@router.post("/events", response_model=IngressJobResponse)
async def ingest_event(body: IngressEventRequest, request: Request) -> IngressJobResponse:
    service = get_service(request)
    event = IngressEvent(
        source=body.source,
        external_id=body.external_id,
        title=body.title,
        body=body.body,
        type=body.type,
        repo_ids=list(body.repo_ids),
        logs=body.logs,
        image_urls=list(body.image_urls),
        metadata=dict(body.metadata),
    )
    try:
        result = await service.run_ingress_event(event)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return IngressJobResponse(**asdict(result))


@router.get("/jobs/{job_id}", response_model=IngressJobResponse)
async def get_job(job_id: str, request: Request) -> IngressJobResponse:
    service = get_service(request)
    doc = service.get_ingress_job(job_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return IngressJobResponse(**doc)
