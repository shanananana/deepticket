from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricsCollector:
    """进程内运行指标（Agent / Webhook / Ingress 队列）。"""

    queue_backlog_alert: int = 10
    agent_runs_total: int = 0
    agent_runs_failed: int = 0
    agent_in_flight: int = 0
    agent_duration_ms_total: int = 0
    agent_duration_ms_last: int = 0
    agent_tokens_estimated: int = 0
    webhook_success_total: int = 0
    webhook_failure_total: int = 0
    ingress_jobs_finished: int = 0
    ingress_jobs_failed: int = 0
    queue_peak_pending: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def observe_queue_depth(self, pending: int) -> None:
        with self._lock:
            if pending > self.queue_peak_pending:
                self.queue_peak_pending = pending

    def agent_run_started(self) -> None:
        with self._lock:
            self.agent_in_flight += 1

    def agent_run_finished(
        self,
        *,
        duration_ms: int,
        ok: bool,
        tokens_estimated: int = 0,
    ) -> None:
        with self._lock:
            self.agent_in_flight = max(0, self.agent_in_flight - 1)
            self.agent_runs_total += 1
            if not ok:
                self.agent_runs_failed += 1
            self.agent_duration_ms_total += max(0, duration_ms)
            self.agent_duration_ms_last = max(0, duration_ms)
            self.agent_tokens_estimated += max(0, tokens_estimated)

    def record_webhook(self, *, ok: bool) -> None:
        with self._lock:
            if ok:
                self.webhook_success_total += 1
            else:
                self.webhook_failure_total += 1

    def record_ingress_job(self, *, ok: bool) -> None:
        with self._lock:
            if ok:
                self.ingress_jobs_finished += 1
            else:
                self.ingress_jobs_failed += 1

    def snapshot(self, *, queue_pending: int = 0) -> dict[str, Any]:
        self.observe_queue_depth(queue_pending)
        with self._lock:
            webhook_total = self.webhook_success_total + self.webhook_failure_total
            webhook_rate = (
                round(self.webhook_success_total / webhook_total, 4)
                if webhook_total
                else None
            )
            alerts: list[str] = []
            if queue_pending >= self.queue_backlog_alert:
                alerts.append(
                    f"Ingress 队列积压 {queue_pending}（阈值 {self.queue_backlog_alert}）"
                )
            if self.agent_in_flight >= max(3, self.queue_backlog_alert // 2):
                alerts.append(f"Agent 并发运行 {self.agent_in_flight} 路")
            if webhook_total >= 5 and webhook_rate is not None and webhook_rate < 0.8:
                alerts.append(
                    f"Webhook 成功率偏低: {webhook_rate * 100:.1f}%"
                )
            avg_ms = (
                self.agent_duration_ms_total // self.agent_runs_total
                if self.agent_runs_total
                else 0
            )
            return {
                "agent": {
                    "runs_total": self.agent_runs_total,
                    "runs_failed": self.agent_runs_failed,
                    "in_flight": self.agent_in_flight,
                    "duration_ms_total": self.agent_duration_ms_total,
                    "duration_ms_last": self.agent_duration_ms_last,
                    "duration_ms_avg": avg_ms,
                    "tokens_estimated": self.agent_tokens_estimated,
                },
                "webhook": {
                    "success_total": self.webhook_success_total,
                    "failure_total": self.webhook_failure_total,
                    "success_rate": webhook_rate,
                },
                "ingress": {
                    "jobs_finished": self.ingress_jobs_finished,
                    "jobs_failed": self.ingress_jobs_failed,
                    "queue_pending": queue_pending,
                    "queue_peak_pending": self.queue_peak_pending,
                },
                "alerts": alerts,
                "collected_at": time.time(),
            }


_metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    return _metrics
