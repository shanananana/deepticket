from __future__ import annotations

import asyncio
import time

import pytest

from deepticket.layers.input.ingress_models import IngressEvent
from deepticket.layers.ingress.queue import IngressJobQueue, IngressQueueItem


@pytest.mark.asyncio
async def test_ingress_queue_processes_items_in_order() -> None:
    processed: list[str] = []

    async def handler(item: IngressQueueItem) -> None:
        processed.append(item.job_id)
        await asyncio.sleep(0)

    queue = IngressJobQueue(workers=1)
    await queue.start(handler)

    event = IngressEvent(
        source="test",
        external_id="1",
        title="t",
        body="b",
    )
    await queue.enqueue(IngressQueueItem(job_id="job-a", event=event))
    await queue.enqueue(IngressQueueItem(job_id="job-b", event=event))

    deadline = time.monotonic() + 2.0
    while len(processed) < 2:
        if time.monotonic() > deadline:
            break
        await asyncio.sleep(0.05)

    await queue.stop()
    assert processed == ["job-a", "job-b"]
