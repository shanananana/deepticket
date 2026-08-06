from __future__ import annotations

import asyncio

import pytest

from deepticket.api.streaming import iter_sse_chunks
from deepticket.layers.output.models import StreamChunk


async def _slow_chunks():
    yield StreamChunk(delta="hi")
    await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_sse_emits_ping_on_idle() -> None:
    events: list[str] = []

    async def collect() -> None:
        async for event in iter_sse_chunks(_slow_chunks(), heartbeat_seconds=0.01):
            events.append(event)
            if event.startswith("event: ping"):
                return

    await asyncio.wait_for(collect(), timeout=2.0)
    assert any(event.startswith("event: ping") for event in events)


@pytest.mark.asyncio
async def test_sse_emits_confidence_event() -> None:
    async def chunks():
        yield StreamChunk(
            confidence={
                "score": 82,
                "level": "high",
                "label": "高",
                "reasons": ["test"],
            }
        )

    events = [event async for event in iter_sse_chunks(chunks(), heartbeat_seconds=0)]
    assert any("event: confidence" in event for event in events)
    assert any('"score": 82' in event for event in events)
