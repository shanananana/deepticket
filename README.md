<p align="center">
  <a href="README.en.md">English</a>
  ·
  <a href="CHANGELOG.md">更新日志</a>
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

**面向线上故障与项目答疑的智能 Agent 平台** — 在 [OpenHands](https://github.com/OpenHands/OpenHands) 之上做 **Ingress / Webhook 编排**，让 Agent 基于 **Git 源码 + 日志 + 配置** 做可复核的根因分析，而不是纯 RAG 猜答案。

关键词：AIOps · SRE · on-call · 工单自动化 · 故障根因分析 · LLM Agent · MCP · FastAPI

- **Ingress** — 监控 / Jira / ITSM HTTP 推送，异步队列 + API Key
- **Outbound** — 分析结果 Webhook 回写或仅存库
- **Workbench** — 多轮追问、贴日志、Thinking 步骤、分析置信度；SSE 心跳防网关断连
- **示例** — 垂类 Agent 可参考 [ad_agent](https://github.com/shanananana/ad_agent)（Spring AI 广告投放）；DeepTicket 负责编排与三源验证流水线

<p align="center">
  <a href="docs/quickstart-demo.md"><strong>5 分钟上手</strong></a>
  ·
  <a href="docs/DEMO_PROMPT.md">示例提问</a>
  ·
  <a href="https://github.com/shanananana/ad_agent">ad_agent 垂类 Demo</a>
</p>

---

## Demo

<p align="center">
  <a href="docs/assets/demo.mp4">
    <img src="docs/assets/demo.gif" width="720" alt="DeepTicket 演示：OpenHands Agent 分析 ad_agent 投放 ROI 下降根因，展示 Thinking 步骤与置信度">
  </a>
</p>

<p align="center"><sub>点击 GIF 观看完整录屏 · Agent 查 log、读配置与代码，给出可复核结论</sub></p>

---

## 5 分钟上手

```bash
git clone https://github.com/shanananana/deepticket.git
cd deepticket
bash scripts/setup.sh          # 创建 deepticket.yaml
# 编辑 deepticket.yaml，填写 llm.api_key
bash scripts/start_all.sh      # Web :8600 + Agent Server :8100
bash scripts/quickstart_demo.sh # 打印下一步；可选 ROI demo 说明
```

打开 http://127.0.0.1:8600 ，默认 `admin` / `admin`。新建对话，粘贴 [docs/DEMO_PROMPT.md](docs/DEMO_PROMPT.md) 里的 **Nginx 日志** 示例即可体验（**无需**配置 Git 仓库）。

完整 ROI 录屏 Demo（读 `campaign_metrics.log` + 代码）：见 [docs/quickstart-demo.md](docs/quickstart-demo.md)。

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
| 工程师多轮协作 | 聊天 | 弱 | ✅ Web 工作台 + SSE + 分析置信度 |
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

详见上方 [5 分钟上手](#5-分钟上手)。常用命令：

| 常用命令 | 说明 |
|----------|------|
| `bash scripts/start_all.sh` | 日常启动 |
| `bash scripts/quickstart_demo.sh` | 上手提示 / 可选 ROI log 预生成 |
| `bash scripts/status.sh` | 检查服务与队列 |
| `bash scripts/verify.sh` | 离线/在线自检 |

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
| `web` | 工作台 SSE 心跳间隔（`sse_heartbeat_seconds`） |
| `extensions` / `mcp` | Skill 与 MCP 扩展 |

日志、配置中心对接请改 `log-query` / `config-query` Skill 模板，或接 MCP。字段说明见 **`deepticket.example.yaml`** 内注释。

---

## 使用方式

**Web 工作台** — 登录 → 新建对话 → 描述问题或粘贴日志 → 需要时「同步知识库」→ 多轮追问直至缩小范围。设置里可开 **录屏模式**，Agent 步骤会保持展开；含读代码/查日志等验证步骤的分析对话会展示 **置信度** 徽章（纯寒暄不展示）。网关前部署时可在 `deepticket.yaml` 配置 **`web.sse_heartbeat_seconds`** 保持 SSE 长连接。

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

## 常见问题

<details>
<summary><strong>DeepTicket 和 OpenHands 是什么关系？</strong></summary>
<p>OpenHands 提供 Agent 运行时（读文件、终端、MCP）。DeepTicket 在其上增加多用户工作台、Git 知识库同步、Ingress 工单接入、Webhook 回写与路由分类，面向 SRE/值班场景。</p>
</details>

<details>
<summary><strong>和 RAG 知识库 / Spring AI Agent 有什么区别？</strong></summary>
<p>RAG 擅长文档检索；Spring AI 垂类 Agent（如 <a href="https://github.com/shanananana/ad_agent">ad_agent</a>）擅长单一业务对话。DeepTicket 强调<strong>读真实 Git 仓库 + 查日志/配置 + 工单闭环</strong>，适合 on-call 初筛与可复核排障。</p>
</details>

<details>
<summary><strong>能否接 Jira、Prometheus、企业微信？</strong></summary>
<p>可以。外部系统 HTTP POST 到 Ingress（带 API Key），DeepTicket 异步分析后 Webhook 回写 ITSM；详见 <code>deepticket.example.yaml</code> 与 <code>bash scripts/test_ingress_e2e.sh</code>。</p>
</details>

<details>
<summary><strong>Alpha 阶段缺什么？</strong></summary>
<p>日志/配置 Skill 默认为模板，需按内网环境对接 MCP 或脚本；公开生产案例仍在收集中。接好 Git 仓库即可做代码级分析。</p>
</details>

---

## 参与贡献

欢迎 Star、Issue 和 PR。第一次贡献请读 **[CONTRIBUTING.md](CONTRIBUTING.md)**，并关注 **`good first issue`**。

---

<p align="center">⭐ 如果这个项目对你有帮助，欢迎 <a href="https://github.com/shanananana/deepticket">Star</a> 支持一下～</p>

---

## License

[MIT](LICENSE)
