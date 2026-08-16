# 工作台示例提问

复制到 DeepTicket 对话输入框即可。

**默认不启用 MCP** — Demo 走 **log-query Skill**（查示例 log）+ **repo-workspace**（读 ad-agent 代码/配置）。需已配置 LLM，并完成知识库同步 + 示例 log 预生成（见下方准备）。

## 准备（一次性）

1. 项目配置 → **知识库** 含 `ad-agent` 仓库（Docker 默认 `deepticket.docker.yaml` 已配公开仓）
2. 工作台 → **同步知识库**
3. 生成示例 log：
   ```bash
   bash scripts/refresh_ad_agent_logs.sh          # 本机 clone 启动
   bash scripts/docker/seed_demo_logs.sh          # Docker 容器内或挂载仓库后
   ```

## 主推：ROI + Skill + 读代码（录屏推荐）

```
7/28 之后投放 ROI 变差了，帮我查原因。

请去 ad-agent 项目只读排查：
1）查 campaign_metrics.log，对比 7/24-7/27 和 7/28-8/01；
2）看 budget_audit.log；
3）再读 config/campaigns.yaml 和 budget_allocator.py 说明根因。

不要运行 generate_campaign_data.py。
```

## 备用：纯日志推理（无需 ad-agent）

```
根据下面这段 Nginx 错误日志，推断最可能的根因，并给出 3 条可执行的排查步骤：

2026-08-01T10:12:03 upstream timed out (110: Connection timed out) while reading response header from upstream
2026-08-01T10:12:03 client: 10.0.1.5, server: api.example.com, request: "GET /v1/orders HTTP/1.1"
```

## Ingress 联调（需 `bash scripts/test_ingress_e2e.sh`）

外部系统推送工单后，Agent 会自动分析并 Webhook 回写；见 `deepticket.example.yaml` 中 `ingress` 配置。
