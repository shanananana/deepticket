---
name: config-query
description: 查询公司内部配置中心/CMDB/Apollo 等配置项。当用户提到配置、开关、feature flag、环境变量时使用。
---

# 配置查询 Skill

这是 DeepTicket 内置的 **Skill 模板**。请替换为你们公司真实的配置查询逻辑。

## 适用场景

- 排查「配置不一致」「开关未打开」「环境配错」类工单
- 需要对比 test / staging / prod 配置差异
- 需要查询某个服务的关键配置项

## 实现指引（由用户团队自行替换）

1. 在 `skills/config-query/scripts/` 添加配置查询脚本
2. 填写配置中心地址、命名空间、应用名规则
3. 输出时 **脱敏** API Key、密码等字段

## 示例流程

1. 从工单识别服务名、环境、配置 key
2. 调用内部配置 API（占位）
3. 返回当前值 + 最近变更记录（如有）
4. 判断是否与代码/文档预期一致

## 占位 API（请替换）

- 配置中心：`<YOUR_CONFIG_CENTER>`
- 查询入口：`<YOUR_CONFIG_QUERY_ENDPOINT>`
- 鉴权：通过环境变量 `CONFIG_QUERY_TOKEN`（由进程环境提供，勿提交 Git）
