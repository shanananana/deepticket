# 工作台示例提问

复制到 DeepTicket 对话输入框即可。需已配置 LLM API Key 并完成知识库同步（ROI 场景见 [quickstart-demo.md](quickstart-demo.md)）。

## 通用（无需 ad_agent 数据）

```
根据下面这段 Nginx 错误日志，推断最可能的根因，并给出 3 条可执行的排查步骤：

2026-08-01T10:12:03 upstream timed out (110: Connection timed out) while reading response header from upstream
2026-08-01T10:12:03 client: 10.0.1.5, server: api.example.com, request: "GET /v1/orders HTTP/1.1"
```

## ad_agent ROI 归因（需 demo 数据）

```
为什么 2026-07-28 之后整体投放 ROI 明显降低？

请直接查 ad-agent 的 campaign_metrics.log：对比 7/24-7/27 与 7/28-8/01，
并读 budget_audit.log 与 campaigns.yaml 给出根因和建议。不要运行 generate_campaign_data.py。
```

## Ingress 联调（需 `bash scripts/test_ingress_e2e.sh`）

外部系统推送工单后，Agent 会自动分析并 Webhook 回写；见 `deepticket.example.yaml` 中 `ingress` 配置。
