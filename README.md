<p align="center">
  <a href="README.en.md">English</a>
  ·
  <a href="CHANGELOG.md">更新日志</a>
  ·
  <a href="https://github.com/shanananana/deepticket/releases">Releases</a>
  ·
  <a href="https://github.com/shanananana/deepticket/stargazers">GitHub Stars</a>
  ·
  <a href="https://github.com/OpenHands/OpenHands">OpenHands</a>
  ·
  <a href="LICENSE">MIT</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python 3.11+">
  <img src="https://img.shields.io/github/v/release/shanananana/deepticket?label=release" alt="Latest release">
  <img src="https://img.shields.io/badge/OpenHands-1.39.1-purple" alt="OpenHands 1.39.1">
  <img src="https://img.shields.io/badge/status-alpha-orange" alt="Alpha">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
</p>

**面向业务组内网部署的 SRE Agent 编排层**（[最新 v0.2.3](https://github.com/shanananana/deepticket/releases/tag/v0.2.3)）— **不替换**公司级 AIOps / Copilot 平台，而是接你们已有的 **MCP、日志、配置中心、ITSM**，在 [OpenHands](https://github.com/OpenHands/OpenHands) 之上做 Ingress/Webhook 闭环；**一套服务可接多团队多项目**，每项目独立知识库 / MCP / agents.md，让 Agent 在 **Git 源码 + 日志 + 配置** 三源上可复核排障；工作台含 Thinking 步骤与**分析置信度**。

关键词：AIOps · SRE · on-call · 企业内网 · 业务组 · 自托管 · MCP 集成 · 编排层 · 工单自动化 · 故障根因分析 · LLM Agent · FastAPI

- **薄编排层** — 自托管部署，yaml 增量接入；与监控 / ITSM / 配置中心**并存**，不抢平台 Agent 位子
- **多团队 / 多项目** — 一套 DeepTicket 服务多个业务线；每项目独立知识库、MCP、agents.md 与工作区，侧栏切换、后台分项配置
- **MCP / Skill 扩展** — 大厂常见内网 MCP（日志、配置、CMDB…）直接挂载；平台级 Agent 很少做到这个粒度
- **Ingress / Outbound** — 告警 / 工单 HTTP 进，分析结论 Webhook 回写
- **Workbench** — 多轮追问、Thinking 步骤、分析置信度；SSE 心跳适配网关
- **示例** — 垂类 Agent 见 [ad_agent](https://github.com/shanananana/ad_agent)；DeepTicket 负责**接基建 + 跑排障流水线**

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

**Docker（免装 Python）：** 见 [docs/docker.md](docs/docker.md) — `cp .env.docker.example .env` → `docker compose up -d --build` → 打开 http://127.0.0.1:8600（LLM 可在 Web 配置）

**本机脚本：**

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

DeepTicket 的定位：**业务组级薄编排层** — 统一 Ingress 进、Webhook 出、Git 知识库、Skill/MCP 扩展，让 Agent 在「源码 +（可选）日志 +（可选）配置」上作答，而不是只靠模型猜测。

> **说明：** 项目为 Alpha。配好 **LLM API Key** 并在 `knowledge.repos` 挂载本组 **一个或多个 Git 仓库** 即可跑代码级排障；日志 / 配置 MCP 与 Skill **按需扩展**，不强制。

---

## 为什么更适合大厂业务组

平台级通用 Agent（公司 Copilot、统一 AI 门户）擅长**广度**：文档问答、代码补全、通用聊天。DeepTicket 刻意做**窄而深**的 on-call 编排 — 一次故障里把 **读源码 → 查日志 → 对配置 → 回写工单** 串成可复核流程。

成熟团队通常已有丰富基建，DeepTicket **不与之冲突**：

| 你们已有的 | DeepTicket 做什么 |
|------------|-------------------|
| 日志平台（ELK / Loki / 自研） | 通过 `log-query` Skill 或 **MCP** 查询，不另建索引 |
| 配置中心 / Apollo / Nacos | 通过 `config-query` Skill 或 **MCP** 拉运行时配置 |
| ITSM / Jira / 自研工单 | **Ingress 进、Webhook 出**，不改原有流转 |
| 内部 MCP Server（CMDB、发布、监控…） | `deepticket.yaml` 挂载，Agent 按需调用 |
| 公司级 AIOps / Copilot 平台 | **并存** — DeepTicket 是业务组可自托管的编排层，不绑平台排期 |

**典型落地形态：** 业务组 clone DeepTicket → 填 `deepticket.yaml`（LLM Key + 默认 Git / MCP 兜底）→ **按项目**挂各组仓库与 MCP → 值班用工作台切换项目，监控/工单走 Ingress。数据留在组内，**不必等公司级 Agent 平台排期**。

**多团队接入：** 同一实例可注册多个项目（如 `ad-agent`、`payment`、`infra`）。每个项目拥有独立的 Git 知识库、MCP 列表、agents.md 提示词与 Agent 工作区；`deepticket.yaml` 仅作默认兜底，运行配置存 Redis，管理员可在工作台 **分项修改、单独保存**，无需一次改全表。

垂类业务 Agent（如 [ad_agent](https://github.com/shanananana/ad_agent)）负责「懂业务对话」；DeepTicket 负责「**接基建、跑 SRE 流水线**」— 两者可组合，而不是二选一。

---

## 对比一览

| 能力 | 纯 RAG 知识库 | 平台级通用 Agent | 传统工单 AI | **DeepTicket** |
|------|:-------------:|:----------------:|:-----------:|:--------------:|
| 定位 | 文档片段 | 公司统一 Copilot，广而浅 | 摘要 / 分类 | **业务组 SRE 编排，窄而深** |
| 读真实 Git 源码 / 调用链 | 片段检索，易过时 | 有限 / 通用对话 | 通常不支持 | ✅ 只读 clone + Agent 读文件 |
| 对接线上日志 / 配置 | 需人工灌库 | 通常无内网 MCP 粒度 | 有限 | ✅ Skill / **MCP**（挂你们已有服务） |
| 与现有 ITSM / 监控并存 | ❌ | 常绑统一平台 | 部分 | ✅ Ingress + Webhook，**增量接入** |
| 业务组自托管 / 独立试点 | 中 | 需等平台排期 | SaaS 为主 | ✅ 自托管 + yaml，挂多仓库，**不抢平台位子** |
| **多团队 / 多项目隔离** | 弱 | 常统一租户 | 按产品切 | ✅ 侧栏选项目；每项目独立 repos / MCP / agents.md / workspace |
| 工单 / 告警自动触发 | ❌ | 弱 | 部分 | ✅ Ingress + 异步队列 |
| 工程师多轮协作 + 置信度 | 聊天 | 有 | 弱 | ✅ 工作台 + SSE + 分析置信度 |
| 开箱即用程度 | 低（embedding / 向量库 / 灌库） | 高（SaaS） | SaaS 较高 | ✅ LLM Key + Git 仓库即可跑；日志/配置 MCP 按需 |

---

## 谁在用

| 场景 | 状态 |
|------|------|
| 作者团队内部试点 | 🟢 用于工单初筛、项目答疑、Ingress 联调 |
| 公开生产案例 | 🟡 尚无 — 欢迎 Issue 分享你的场景（可匿名） |

若你在试用 DeepTicket，欢迎在 [Discussions / Issues](https://github.com/shanananana/deepticket/issues) 留言，我们会考虑收录到本节（可匿名）。

---

## 多团队 / 多项目

一套 DeepTicket 可同时服务多个业务线或小组，避免「每个团队各部署一套 Agent 平台」：

| 维度 | 说明 |
|------|------|
| **项目切换** | 工作台侧栏选择项目；聊天、知识库、Skill 发布均按 `project_id` 隔离 |
| **独立配置** | 每项目可配自己的 Git 仓库、MCP Server、agents.md（注入 OpenHands 系统提示） |
| **配置存储** | 运行时以 **Redis 为准**；`deepticket.yaml` 作默认兜底，未写入 Redis 的字段自动回落 |
| **后台管理** | 侧栏 **Token 消耗** 与 **项目配置** 并列；在「项目配置」中分项编辑（基本信息 / 成员 / Repos / MCP / agents.md），支持载入 yaml 默认后再改 |
| **权限** | 可按项目分配成员（API）；管理员可见全部项目 |

新建项目、修改 MCP 等操作见侧栏 **项目配置**（管理员），或通过 `PUT/PATCH /api/admin/projects/{id}` 接入 CI / 运维脚本。

> **说明：** Ingress 工单链路当前仍走 `default` 项目；多项目主要覆盖 **工作台问答** 与 **按项目知识库 / MCP**。后续可按 `project_id` 扩展 Ingress 路由。

---

## 架构一览

<p align="center">
  <a href="docs/assets/architecture.svg">
    <img src="docs/assets/architecture.png" alt="DeepTicket 五层架构：输入、编排、引擎、知识、输出" width="720">
  </a>
</p>

<p align="center"><sub>点击图片查看 SVG 矢量源 · 编排层为 DeepTicket 本体 · 8600 对外 / 8100 建议仅本机</sub></p>

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
| `knowledge.repos` | 默认 Git 仓库（代码分析；多项目可在后台按项目覆盖） |
| `ingress` | 外部工单/告警接入与 Webhook 回写 |
| `storage` | 本地或 **Redis**（多项目配置、聊天历史、权限建议用 Redis） |
| `web` | 工作台 SSE 心跳间隔（`sse_heartbeat_seconds`） |
| `extensions` / `mcp` | 默认 Skill 目录与 MCP；各项目可在后台单独覆盖 |

**多项目运行时配置** 存 Redis（`project_configs`），不由 yaml 热更新；yaml 仅提供首次兜底。管理员 API：`GET/PATCH /api/admin/projects/{id}` 及 `/knowledge`、`/mcp`、`/extensions` 子路径。

日志、配置中心对接请改 `log-query` / `config-query` Skill 模板，或接 MCP。字段说明见 **`deepticket.example.yaml`** 内注释。

---

## 使用方式

**Web 工作台** — 登录 → **选择项目** → 新建对话 → 描述问题或粘贴日志 → 需要时「同步知识库」→ 多轮追问直至缩小范围。截图可直接 **粘贴 / 点「截图」上传 / 拖入输入框**（类似 Cursor，无需填 URL）。Agent 在后台运行，**关页后回复仍会写入历史**，重新打开同一对话即可查看。设置里可开 **录屏模式**，Agent 步骤会保持展开；含读代码/查日志等验证步骤的分析对话会展示 **置信度** 徽章（纯寒暄不展示）。网关前部署时可在 `deepticket.yaml` 配置 **`web.sse_heartbeat_seconds`** 保持 SSE 长连接。

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
<summary><strong>适合大厂 / 业务组内网吗？会和公司 AIOps 平台冲突吗？</strong></summary>
<p>DeepTicket 是<strong>薄编排层</strong>，不是又一个要替换全公司工具的平台级 Agent。它通过 Ingress/Webhook 和 Skill/<strong>MCP</strong> 把你们已有的日志、配置、ITSM、内部 MCP 服务串进一次排障流程，<strong>不另建监控栈、不绑 Copilot 排期</strong>。适合一个业务组自托管试点：yaml 配置、数据留在组内。平台 Agent 做广度，DeepTicket 做 on-call 深度 — 读源码、对日志、查配置、回写工单。</p>
</details>

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
<summary><strong>如何接入多个团队 / 多个项目？</strong></summary>
<p>启用 Redis 存储后，在侧栏打开 <strong>项目配置</strong>（管理员，位于 Token 消耗下方）新建项目，分别为各项目配置 Git 仓库、MCP 与 agents.md。用户登录后在侧栏切换项目即可；对话与知识库按项目隔离。yaml 里的 <code>knowledge</code> / <code>mcp</code> 仅作默认兜底，后台保存的内容写入 Redis 优先生效。</p>
</details>

<details>
<summary><strong>Alpha 阶段缺什么？</strong></summary>
<p>项目为 Alpha，公开生产案例仍在收集中。最小可用：<strong>LLM Key + Git 仓库</strong> 即可代码级分析；日志 / 配置 MCP 与 Skill 有模板，<strong>按需对接</strong>，不挡上手。</p>
</details>

---

## 参与贡献

欢迎 Star、Issue 和 PR。第一次贡献请读 **[CONTRIBUTING.md](CONTRIBUTING.md)**，并关注 **`good first issue`**。

---

<p align="center">⭐ 如果这个项目对你有帮助，欢迎 <a href="https://github.com/shanananana/deepticket">Star</a> 支持一下～</p>

---

## License

[MIT](LICENSE)
