from __future__ import annotations

import json

from deepticket.layers.output.models import StreamChunk


class OutputAdapter:
    """输出层：把引擎 SSE 转为统一 chunk。"""

    @staticmethod
    def parse_sse_line(line: str) -> StreamChunk | None:
        if not line.startswith("data: "):
            return None
        payload = line[6:].strip()
        if payload == "[DONE]":
            return StreamChunk(done=True)

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return None

        delta = data.get("choices", [{}])[0].get("delta", {}).get("content")
        if isinstance(delta, str) and delta:
            return StreamChunk(delta=delta)
        return None

    @staticmethod
    def sse_meta_event(conversation_id: str) -> str:
        meta = json.dumps({"conversation_id": conversation_id})
        return f"event: meta\ndata: {meta}\n\n"
