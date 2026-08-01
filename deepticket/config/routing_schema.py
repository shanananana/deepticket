"""路由配置：外部 Ingress 事件类型 → Agent 分析 → Outbound 出口。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RouteMatchConfig(BaseModel):
    """路由匹配条件；routes 列表中先声明的规则优先命中。"""

    default: bool = Field(
        default=False,
        description="true 表示兜底路由；通常放在 routes 最后一条",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="匹配 Ingress 事件的 source 字段，如 jira、alertmanager",
    )
    title_keywords: list[str] = Field(
        default_factory=list,
        description="标题包含任一关键词即命中（大小写不敏感）",
    )
    body_keywords: list[str] = Field(
        default_factory=list,
        description="正文包含任一关键词即命中（大小写不敏感）",
    )


class OutboundConfig(BaseModel):
    """分析完成后的结果投递方式。"""

    method: Literal["store_only", "webhook"] = Field(
        default="store_only",
        description="store_only：仅存 Redis/本地，用 GET /api/ingress/jobs/{id} 查；"
        "webhook：POST JSON 到 url",
    )
    url_env: str = Field(
        default="",
        description="可选；当 url 为空时从环境变量读 Webhook 地址（遗留）；推荐直接在 url 填写",
    )
    url: str = Field(
        default="",
        description="Webhook 完整 URL；非空时优先于 url_env",
    )
    timeout_seconds: float = Field(
        default=30.0,
        description="Webhook HTTP 超时（秒）",
    )
    extra_headers_env: str = Field(
        default="",
        description="可选；环境变量名，值为 JSON 对象，合并到 Webhook 请求头",
    )


class RouteConfig(BaseModel):
    """单条 Ingress 路由：匹配规则 + 分析参数 + 出口。"""

    type: str = Field(
        min_length=1,
        description="路由类型名；Ingress 请求可显式传 type 跳过自动匹配",
    )
    description: str = Field(
        default="",
        description="人类可读说明；GET /api/ingress/routes 会返回",
    )
    match: RouteMatchConfig = Field(
        default_factory=RouteMatchConfig,
        description="自动分类时的匹配条件",
    )
    outbound: OutboundConfig = Field(
        default_factory=OutboundConfig,
        description="分析结果如何送出",
    )
    prompt_suffix: str = Field(
        default="",
        description="追加到工单正文后的 Agent 提示（如「优先给止血建议」）",
    )
    repo_ids: list[str] = Field(
        default_factory=list,
        description="默认关联的 knowledge.repos.id；事件未带 repo_ids 时使用",
    )


class RoutingConfig(BaseModel):
    routes: list[RouteConfig] = Field(default_factory=list)

    def route_for_type(self, route_type: str) -> RouteConfig | None:
        for route in self.routes:
            if route.type == route_type:
                return route
        return None

    def default_route(self) -> RouteConfig | None:
        for route in self.routes:
            if route.match.default:
                return route
        return self.routes[-1] if self.routes else None
