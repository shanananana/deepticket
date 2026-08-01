---
name: log-query
description: 查询公司内部日志系统，用于工单排障。当用户提到日志、报错、trace、堆栈时使用。
---

# 日志查询 Skill

这是 DeepTicket 内置的 **Skill 模板**。请替换为你们公司真实的日志查询流程。

## 适用场景

- 工单附带 `logs` 字段或日志文件路径
- 需要按 traceId / requestId / 用户 ID 检索
- 需要按时间范围过滤 ERROR / WARN

## 实现指引（由用户团队自行替换）

1. 在 `skills/log-query/scripts/` 添加查询脚本（如 `query_logs.sh` 或 Python CLI）
2. 在下方填写你们内部的日志平台 API、索引名、字段规范
3. Agent 应优先 **只读查询**，不要删除或修改日志

## 示例流程

1. 从工单描述提取 traceId 与时间范围
2. 调用内部日志 API（占位）
3. 汇总前 20 条相关 ERROR 日志
4. 结合 workspace 代码给出根因分析

## 占位 API（请替换）

- 平台：`<YOUR_LOG_PLATFORM>`
- 查询入口：`<YOUR_LOG_QUERY_ENDPOINT>`
- 鉴权：通过环境变量 `LOG_QUERY_TOKEN`（由进程环境提供，勿提交 Git）
