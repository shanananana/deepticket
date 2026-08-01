from __future__ import annotations

from deepticket.layers.input.image_urls import (
    image_urls_from_metadata,
    normalize_image_urls,
)
from deepticket.layers.input.models import AgentInput, ChatInput, TicketInput


class InputAdapter:
    """输入层：把外部请求规范化为 AgentInput。"""

    @staticmethod
    def from_chat(payload: ChatInput) -> AgentInput:
        image_urls = normalize_image_urls(
            payload.image_urls,
            image_urls_from_metadata(payload.metadata),
        )
        return AgentInput(
            prompt=payload.message.strip(),
            conversation_id=payload.conversation_id,
            source="chat",
            image_urls=image_urls,
            metadata=payload.metadata,
        )

    @staticmethod
    def from_ticket(payload: TicketInput) -> AgentInput:
        image_urls = normalize_image_urls(
            payload.image_urls,
            image_urls_from_metadata(payload.metadata),
        )
        repo_hint = ""
        if payload.repo_ids:
            repo_hint = f"\n\n关联代码仓库 ID: {', '.join(payload.repo_ids)}"

        logs_block = ""
        if payload.logs.strip():
            logs_block = f"\n\n--- 日志 ---\n{payload.logs.strip()}"

        images_block = ""
        if image_urls:
            lines = "\n".join(f"- {url}" for url in image_urls)
            images_block = f"\n\n--- 附件图片 ---\n{lines}"

        prompt = (
            f"工单 {payload.ticket_id}: {payload.title}\n\n"
            f"{payload.description.strip()}"
            f"{repo_hint}"
            f"{logs_block}"
            f"{images_block}\n\n"
            "请分析根因并给出修复建议。知识层代码为只读，不要修改仓库文件。"
        )
        if image_urls:
            prompt += " 若模型支持视觉，请结合附件图片内容分析。"
        return AgentInput(
            prompt=prompt,
            source="ticket",
            ticket_id=payload.ticket_id,
            repo_ids=list(payload.repo_ids),
            image_urls=image_urls,
            metadata=payload.metadata,
        )
