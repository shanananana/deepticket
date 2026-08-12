from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest

from deepticket.chat_runs import ChatRunManager
from deepticket.layers.input.models import ChatInput
from deepticket.layers.output.models import StreamChunk
from deepticket.layers.storage.chat_history import ChatHistoryStore
from deepticket.layers.storage.local import LocalStorage


class _FakeProject:
    project_id = "default"


class _FakeService:
    def __init__(self, tmp_path) -> None:
        storage = LocalStorage(str(tmp_path / "data"))
        self.chat_history = ChatHistoryStore(storage)
        self._chunks: list[StreamChunk] = []

    async def _run_stream(self, agent_input) -> AsyncIterator[StreamChunk]:
        yield StreamChunk(conversation_id="conv-test", delta="Hello")
        yield StreamChunk(conversation_id="conv-test", delta=" world")
        await asyncio.sleep(0.05)

    async def record_chat_token_usage(self, **_kwargs) -> None:
        return None


@pytest.mark.asyncio
async def test_chat_run_persists_after_subscriber_disconnect(tmp_path) -> None:
    service = _FakeService(tmp_path)
    manager = ChatRunManager(service)
    service.chat_runs = manager

    project = _FakeProject()
    thread = service.chat_history.create_thread("default", "u1")
    chat_id = thread["chat_id"]
    service.chat_history.append_message(
        "default", "u1", chat_id, role="user", content="hi"
    )

    payload = ChatInput(message="follow up")
    agent_input = type("AgentInput", (), {"conversation_id": None})()

    run = await manager.start(
        project=project,
        uid="u1",
        chat_id=chat_id,
        payload=payload,
        agent_input=agent_input,
    )

    subscriber = manager.subscribe(run)
    first = await anext(subscriber)
    assert first.delta == "Hello"

    await subscriber.aclose()

    for _ in range(50):
        doc = service.chat_history.get_thread("default", "u1", chat_id)
        assert doc is not None
        if doc.get("agent_run_status") == "idle":
            messages = doc.get("messages") or []
            assert any(m.get("role") == "assistant" and m.get("content") == "Hello world" for m in messages)
            return
        await asyncio.sleep(0.05)

    raise AssertionError("assistant message was not persisted after subscriber disconnect")


@pytest.mark.asyncio
async def test_chat_run_status_running_while_in_progress(tmp_path) -> None:
    service = _FakeService(tmp_path)
    gate = asyncio.Event()

    async def slow_stream(agent_input) -> AsyncIterator[StreamChunk]:
        yield StreamChunk(delta="part1")
        await gate.wait()
        yield StreamChunk(delta="part2")

    service._run_stream = slow_stream  # type: ignore[method-assign]
    manager = ChatRunManager(service)

    project = _FakeProject()
    thread = service.chat_history.create_thread("default", "u1")
    chat_id = thread["chat_id"]

    run = await manager.start(
        project=project,
        uid="u1",
        chat_id=chat_id,
        payload=ChatInput(message="q"),
        agent_input=type("AgentInput", (), {"conversation_id": None})(),
    )

    doc = None
    for _ in range(50):
        doc = service.chat_history.get_thread("default", "u1", chat_id)
        if doc is not None and doc.get("agent_run_status") == "running":
            break
        await asyncio.sleep(0.01)
    assert doc is not None
    assert doc.get("agent_run_status") == "running"

    gate.set()
    async for _chunk in manager.subscribe(run):
        pass

    doc = service.chat_history.get_thread("default", "u1", chat_id)
    assert doc is not None
    assert doc.get("agent_run_status") == "idle"
