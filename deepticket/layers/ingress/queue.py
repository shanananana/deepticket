from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from deepticket.layers.input.ingress_models import IngressEvent

logger = logging.getLogger(__name__)

IngressQueueHandler = Callable[["IngressQueueItem"], Awaitable[None]]
IngressQueueFailureHandler = Callable[["IngressQueueItem", BaseException], Awaitable[None]]


@dataclass(frozen=True)
class IngressQueueItem:
    job_id: str
    event: IngressEvent


class IngressJobQueue:
    """进程内 asyncio 队列；Ingress 事件异步入队，由 worker 消费。"""

    def __init__(self, *, workers: int) -> None:
        self._workers = max(1, workers)
        self._queue: asyncio.Queue[IngressQueueItem | None] = asyncio.Queue()
        self._tasks: list[asyncio.Task] = []
        self._handler: IngressQueueHandler | None = None
        self._on_failure: IngressQueueFailureHandler | None = None

    def qsize(self) -> int:
        return self._queue.qsize()

    @property
    def worker_count(self) -> int:
        return self._workers

    async def start(
        self,
        handler: IngressQueueHandler,
        *,
        on_failure: IngressQueueFailureHandler | None = None,
    ) -> None:
        if self._tasks:
            return
        self._handler = handler
        self._on_failure = on_failure
        for worker_id in range(self._workers):
            self._tasks.append(asyncio.create_task(self._worker(worker_id)))
        logger.info("Ingress 队列已启动: workers=%s", self._workers)

    async def stop(self) -> None:
        if not self._tasks:
            return
        for _ in self._tasks:
            await self._queue.put(None)
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        self._handler = None
        self._on_failure = None
        logger.info("Ingress 队列已停止")

    async def enqueue(self, item: IngressQueueItem) -> None:
        await self._queue.put(item)

    async def _worker(self, worker_id: int) -> None:
        while True:
            item = await self._queue.get()
            try:
                if item is None:
                    return
                if self._handler is None:
                    logger.error("Ingress worker %s: handler 未设置", worker_id)
                    continue
                await self._handler(item)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error(
                    "Ingress worker %s 处理失败 job_id=%s: %s",
                    worker_id,
                    item.job_id if item else "?",
                    exc,
                    exc_info=True,
                )
                if item is not None and self._on_failure is not None:
                    try:
                        await self._on_failure(item, exc)
                    except Exception as mark_exc:
                        logger.error(
                            "Ingress 失败回调异常 job_id=%s: %s",
                            item.job_id,
                            mark_exc,
                            exc_info=True,
                        )
            finally:
                self._queue.task_done()
