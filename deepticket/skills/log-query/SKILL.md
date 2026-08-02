---
name: log-query
description: 查询投放/业务日志与指标。用户提到 ROI、消耗、转化、日志、trace、报错、线上数据时使用。
---

# 日志查询 Skill

对接**只读**日志/指标查询。生产环境请替换为你们真实 API。

## ad_agent 项目（workspace/project/ad-agent）

`data/campaign_metrics.log` 与 `data/budget_audit.log` **已在本地预生成**，分析时**直接查询，不要运行 generate**。

仅当上述 log 文件不存在或为空时，才允许执行：

```bash
python scripts/generate_campaign_data.py --start 2026-07-24 --end 2026-08-01
```

正常分析流程（只读）：

```bash
cd workspace/project/ad-agent
python scripts/query_campaign_metrics.py --start 2026-07-24 --end 2026-07-27
python scripts/query_campaign_metrics.py --start 2026-07-28 --end 2026-08-01
python scripts/query_campaign_metrics.py --album-id album_bad_001 --start 2026-07-24 --end 2026-08-01
cat data/budget_audit.log
```

日志文件：

| 文件 | 说明 |
|------|------|
| `data/campaign_metrics.log` | 日粒度 ROI/spend（JSONL） |
| `data/budget_audit.log` | 预算变更审计（2026-07-28 起低 ROI 计划被放大） |

输出含 `--- key finding ---` 时，结合 `budget_audit.log`、`config/campaigns.yaml` 与 `budget_allocator.py` 做归因。

本地刷新 log（运维/演示用，不在 Agent 对话里跑）：项目根目录 `./scripts/refresh_ad_agent_logs.sh`

## 适用场景

- 工单附带 `logs` 字段或指标问题（ROI 下降、消耗异常）
- 按 traceId / 时间范围查 ERROR
- 对比故障前后两个时间窗口

## 生产接入指引

1. 在 `skills/log-query/scripts/` 添加查询脚本（或 MCP）
2. 填写下方平台 API、索引名、字段规范
3. Agent 应优先 **只读查询**，不要删除或修改日志

## 占位 API（请替换）

- 平台：`<YOUR_LOG_PLATFORM>`
- 查询入口：`<YOUR_LOG_QUERY_ENDPOINT>`
- 鉴权：环境变量 `LOG_QUERY_TOKEN`（勿提交 Git）
