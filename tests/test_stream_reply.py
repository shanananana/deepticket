from __future__ import annotations

from deepticket.layers.engine.stream_reply import (
    ReplyStreamState,
    consume_stream_content,
    extract_visible_reply,
)


def test_extract_visible_reply_from_finish_json() -> None:
    raw = '{"message":"Hello world","success":true}'
    assert extract_visible_reply(raw) == "Hello world"


def test_extract_visible_reply_plain_text() -> None:
    assert extract_visible_reply("plain answer") == "plain answer"


def test_extract_visible_reply_skips_json_prefix() -> None:
    assert extract_visible_reply('{"other":1}') is None


def test_consume_stream_content_incremental() -> None:
    state = ReplyStreamState()
    d1 = consume_stream_content(state, '{"message":"Hel')
    d2 = consume_stream_content(state, 'lo"}')
    assert d1 == "Hel"
    assert d2 == "lo"
    assert state.delta_count == 2


def test_consume_stream_content_no_duplicate() -> None:
    state = ReplyStreamState()
    first = consume_stream_content(state, '{"message":"same"}')
    second = consume_stream_content(state, '{"message":"same"}')
    assert first == "same"
    assert second == ""


def test_reset_turn_clears_buffer() -> None:
    state = ReplyStreamState()
    consume_stream_content(state, '{"message":"turn1"}')
    state.reset_turn()
    delta = consume_stream_content(state, '{"message":"turn2"}')
    assert delta == "turn2"
