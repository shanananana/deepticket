

<p align="center">
  <img src="docs/assets/banner.png" alt="DeepTicket — 智能 Agent 平台 · 故障排查与项目答疑" width="720">
</p>

<p align="center">
  <a href="README.en.md">English</a>
  ·
  <a href="https://github.com/shanananana/deepticket/stargazers">GitHub Stars</a>
  ·
  <a href="https://github.com/OpenHands/OpenHands">OpenHands</a>
  ·
  <a href="LICENSE">MIT</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/OpenHands-1.39.1-purple" alt="OpenHands 1.39.1">
  <img src="https://img.shields.io/badge/status-alpha-orange" alt="Alpha">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
</p>

**面向线上故障与项目答疑的智能 Agent 平台**（OpenHands · SRE / AIOps · 工单 · MCP · Webhook）。内置 [OpenHands](https://github.com/OpenHands/OpenHands) Agent Server，支持**服务器一键部署**（`bash scripts/start_all.sh`）：MCP、Skill 与知识库在服务端统一配置，产品、运营等非开发同学打开浏览器即可提问，无需每人本地安装 Agent 或单独配 MCP；并串联 Git 源码、日志/配置查询与 Ingress / Webhook，形成可复核的排查流水线。

- **Ingress** — 监控 / 工单 HTTP 推送，异步队列 + API Key
- **Outbound** — 分析结果 Webhook 回写或仅存库
- **Workbench** — 多轮追问、贴日志、截图 URL

---

## Demo

  https://github.com/user-attachments/assets/8a1fc061-dd87-4fee-b8b3-9b62b8b594a0
  
---

## 为什么做 DeepTicket

线上排障和项目答疑里，常见三类失败：

1. **纯聊天 / 纯 RAG** — 只能检索文档片段，难以读调用链、对照线上日志与运行时配置，容易「看起来像真的」但无法复核。  
2. **传统工单 AI** — 擅长摘要、分类、模板回复，很少基于**真实 Git 仓库**做代码级推理，也难接入内网日志 / 配置中心。  
3. **把 OpenHands 直接丢给值班同学** — 能力强，但缺少 Ingress/Webhook、路由、知识库同步和统一配置，难和 ITSM / 监控闭环。

DeepTicket 的定位：**在 OpenHands 之上做编排层** — 统一 Ingress 进、Webhook 出、Git 知识库、Skill/MCP 扩展，让 Agent 在「源码 +（可选）日志 +（可选）配置」上作答，而不是只靠模型猜测。

> **诚实说明：** 项目为 Alpha；日志 / 配置 Skill 默认为模板，需按你们环境对接后才有完整「三源验证」。接好 Git 仓库即可开始代码级排障与答疑。

---

## 对比一览

| 能力 | 纯 RAG 知识库 | 传统工单 AI | **DeepTicket** |
|------|:-------------:|:-----------:|:--------------:|
| 读真实 Git 源码 / 调用链 | 片段检索，易过时 | 通常不支持 | ✅ 只读 clone + Agent 读文件 |
| 对接线上日志 | 需人工灌库 | 有限 | ✅ log-query Skill / MCP（需自行配置） |
| 对接配置中心 | 弱 | 有限 | ✅ config-query Skill / MCP（需自行配置） |
| 工单 / 告警自动触发 | ❌ | 部分 | ✅ Ingress + 异步队列 |
| 结论回写 ITSM | ❌ | 部分 | ✅ Webhook Outbound |
| 工程师多轮协作 | 聊天 | 弱 | ✅ Web 工作台 + SSE |
| 开箱即用程度 | 中 | SaaS 较高 | ⚠️ 需 yaml + LLM + 集成（Alpha） |

---

## 谁在用

| 场景 | 状态 |
|------|------|
| 作者团队内部试点 | 🟢 用于工单初筛、项目答疑、Ingress 联调 |
| 公开生产案例 | 🟡 尚无 — 欢迎 Issue 分享你的场景（可匿名） |

若你在试用 DeepTicket，欢迎在 [Discussions / Issues](https://github.com/shanananana/deepticket/issues) 留言，我们会考虑收录到本节（可匿名）。

---

## 架构一览

<p align="center">
  <img src="docs/assets/architecture.svg" alt="DeepTicket architecture" width="720">
</p>

<p align="center"><sub>用户与上游系统只访问 <strong>8600</strong>；Agent Server <strong>8100</strong> 建议仅绑定 <code>127.0.0.1</code></sub></p>

---

## 快速开始

```bash
git clone https://github.com/shanananana/deepticket.git
cd deepticket
bash scripts/setup.sh          # 创建 deepticket.yaml、安装依赖
# 编辑 deepticket.yaml（LLM、Git 仓库等；参考 deepticket.example.yaml）
bash scripts/start_all.sh      # 启动 Web（8600）+ Agent Server（8100，本机内部）
```

浏览器打开 http://127.0.0.1:8600 ，默认 `admin` / `admin`（**生产环境请尽快改密码**）。

| 常用命令 | 说明 |
|----------|------|
| `bash scripts/start_all.sh` | 日常启动 |
| `bash scripts/status.sh` | 检查服务与队列 |
| `bash scripts/verify.sh` | 离线/在线自检 |

**本地 ad_agent 演示：** 在 `deepticket.yaml` 配置 `knowledge.repos` 指向 `workspace/knowledge/ad-agent`，同步知识库后执行 `bash scripts/refresh_ad_agent_logs.sh` 预生成 log。

日常只需访问 **8600**；8100 为 Agent 内部端口，生产环境绑定 `127.0.0.1` 即可。

---

## 配置

所有项集中在 **`deepticket.yaml`**（从 `deepticket.example.yaml` 复制；含密钥，已 gitignore）。常用区块：

| 区块 | 作用 |
|------|------|
| `llm` | 模型与 API Key |
| `knowledge.repos` | 只读 Git 仓库（代码分析） |
| `ingress` | 外部工单/告警接入与 Webhook 回写 |
| `storage` | 本地或 Redis |
| `extensions` / `mcp` | Skill 与 MCP 扩展 |

日志、配置中心对接请改 `log-query` / `config-query` Skill 模板，或接 MCP。字段说明见 **`deepticket.example.yaml`** 内注释。

---

## 使用方式

**Web 工作台** — 登录 → 新建对话 → 描述问题或粘贴日志 → 需要时「同步知识库」→ 多轮追问直至缩小范围。设置里可开 **录屏模式**，Agent 步骤会保持展开。

**外部系统自动化** — 监控/ITSM/Jira 等 HTTP 推送事件，DeepTicket 异步分析后 Webhook 回写或仅存库；一般只需改 yaml，不必改主程序。本地联调：`bash scripts/test_ingress_e2e.sh`。

---

## 开发与验证

```bash
pip install -e ".[dev]"
pytest -q
bash scripts/verify.sh --online
```

**环境：** macOS / Linux · Python 3.11+ · OpenAI 兼容 LLM · Redis 可选（Docker 或公司实例）

---

## 参与贡献

欢迎 Star、Issue 和 PR。第一次贡献请读 **[CONTRIBUTING.md](CONTRIBUTING.md)**，并关注 **`good first issue`**。

---

<p align="center">⭐ 如果这个项目对你有帮助，欢迎 <a href="https://github.com/shanananana/deepticket">Star</a> 支持一下～</p>

---

## License

[MIT](LICENSE)
