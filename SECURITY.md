# 安全策略 / Security Policy

## 支持的版本

| 版本 | 支持 |
|------|------|
| 最新 release（当前 [v0.3.1](https://github.com/shanananana/deepticket/releases/latest)） | ✅ |
| 更早版本 | ❌ 请升级后复测 |

## 报告漏洞

**请勿在公开 Issue 中披露安全漏洞。**

请通过以下方式私下报告：

1. **推荐：** GitHub [Private vulnerability reporting](https://github.com/shanananana/deepticket/security/advisories/new)（仓库 → Security → Report a vulnerability）
2. 或通过仓库维护者 GitHub 账号私信联系

请在报告中尽量包含：

- 问题类型（如越权、注入、敏感信息泄露）
- 受影响组件与版本
- 复现步骤或 PoC
- 影响评估（若已知）

## 响应预期

- **48 小时内**：确认收到
- **7 个工作日内**：初步评估与严重程度分级
- 修复后会在 release / advisory 中致谢（除非你希望匿名）

## 安全使用建议

- 勿将 `deepticket.yaml`、`.env` 中的 **LLM API Key、Ingress Key** 提交到仓库
- 生产环境将 Web 绑定 `127.0.0.1` 或置于反向代理之后，并修改默认 `admin` 密码
- Agent Server（8100）建议仅本机访问，勿暴露到公网
