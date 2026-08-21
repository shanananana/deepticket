<p align="center">
  <img src="docs/assets/banner-header.png" width="100%" alt="DeepTicket 品牌 Banner">
</p>

<p align="center">
  <a href="README.en.md">English</a>
  ·
  <a href="CHANGELOG.md">更新日志</a>
  ·
  <a href="https://github.com/shanananana/deepticket/releases/tag/v0.3.3">v0.3.3</a>
  ·
  <a href="LICENSE">MIT</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python 3.11+">
  <img src="https://img.shields.io/github/v/release/shanananana/deepticket?label=release" alt="release">
  <img src="https://img.shields.io/badge/OpenHands-1.39.1-purple" alt="OpenHands">
  <img src="https://img.shields.io/badge/docker-GHCR-2496ED" alt="Docker">
</p>

<h1 align="center">DeepTicket</h1>

<p align="center"><strong>连接内部系统的 AI 排障工作台。</strong></p>

<p align="center"><strong>从一张工单出发，联动代码、日志与配置，完成第一轮排查。</strong></p>

<p align="center">它把内部系统中的事件送进 Agent，将项目源码、日志、配置和内部工具接到同一次分析里，再把带证据的结论回写原系统。</p>

<p align="center">
  <a href="#它是什么"><strong>它是什么</strong></a>
  ·
  <a href="#演示"><strong>演示</strong></a>
  ·
  <a href="#核心能力"><strong>核心能力</strong></a>
  ·
  <a href="#5-分钟跑起来"><strong>5 分钟上手</strong></a>
  ·
  <a href="#架构"><strong>架构</strong></a>
  ·
  <a href="#文档"><strong>文档</strong></a>
</p>

---

## 它是什么

DeepTicket 是一层部署在团队自己环境里的 **AI 工单排障与 Agent 编排平台**。

它提供统一的 HTTP Ingress API 和可配置 Webhook：内部工单、告警、监控平台或自研系统，只要能够发送或接收 HTTP 请求，就可以按统一事件格式接入。DeepTicket 当前提供的是通用接入能力，不内置某个具体厂商的专用适配器。

进入 DeepTicket 的工单会按项目路由到对应的 Git 仓库、日志查询 Skill、配置中心 MCP 和其他内部工具。OpenHands Agent 完成多轮分析后，DeepTicket 将摘要、证据、影响面、根因假设和建议通过 Webhook 写回原工单系统，也可以选择只存储、不回调。

一句话概括：**DeepTicket 让内部工单从“人工转述问题”，变成“自动带着项目上下文完成第一轮排查”。**

---

## 演示

<p align="center">
  <video src="https://github.com/user-attachments/assets/3bc7b913-f3a9-49c5-bbe7-1c15f1a0381b" width="720" controls autoplay muted loop playsinline></video>
</p>
<p align="center"><sub>ad-agent ROI 归因 Demo · 查日志等能力需接入真实 Skill / MCP 后生效；部分 UI 为演示强化，与实际项目样式可能不同</sub></p>

---

## 为什么是 DeepTicket

很多问题并不需要立刻叫研发，却也不是一句“建议检查日志”就能结束。

DeepTicket 把问题分析所需的上下文放到同一个工作台里：项目源码、运行日志、配置项、内部工具和原始工单。客服、运营、产品与研发可以围绕同一份上下文协作。Agent 先读取事实，再给出问题原因、影响范围和处理建议。

> **从“问一个 AI”到“完成一次排查”。**
>
> 重点不是让对话更长，而是让每个结论都更接近证据。

### 它适合谁

- 希望由业务团队自己部署、自己接入内网数据的团队
- 需要让产品、运营、QA 或值班同学先完成一轮事实核查的团队
- 已经有 Git、日志平台、配置中心或 ITSM，但缺少统一 Agent 入口的团队

### 它不是什么

DeepTicket 不是公司级 Copilot 的替代品，也不是把所有文档灌进向量库的纯 RAG。它更像一层面向具体项目的“排查与回写编排”：接入真实工具，限定项目边界，让 Agent 对着可验证的上下文工作。

---

## 核心能力

### 01 · 接入真实上下文

- **Git 知识库同步**：将一个或多个项目仓库同步到 Agent workspace，支持源码、文档和配置一起检索
- **日志与配置查询**：通过内置 Skill 模板或 MCP 接入已有平台，不要求先改造数据链路
- **多项目隔离**：每个项目拥有独立的 repos、MCP、Skill、<code>agents.md</code> 和成员配置

### 02 · 让结论有依据

- **证据优先**：回答可引用源码路径、日志片段、配置键和相关文件
- **权限隔离**：Git 与内部系统使用只开放 Read / Read API 的 Access Token，从接入层限制 Agent 的访问范围；<code>agents.md</code> 负责补充分析规范、证据引用和不确定性说明
- **过程可见**：工作台展示 Agent 的分析步骤、流式回复、置信度和历史对话
- **不确定就标注**：没有足够证据时明确说明缺失信息，而不是用通用话术填空

### 03 · 从入口到回写闭环

- **Ingress**：通过 HTTP API / Webhook 接入任意内部工单、ITSM、告警或自研系统
- **异步分析**：后台队列执行 Agent 任务，不依赖调用方一直保持连接
- **Webhook 回写**：把分析结论写回原工单系统，也可以只存储、不回调
- **人机协作**：机器先完成事实整理，人结合业务判断原因、影响范围和处理方式

### 04 · 方便试点，也方便治理

- **Docker 一键启动**：Web、OpenHands Agent Server 与 Redis 可用 Compose 启动
- **YAML + 管理侧栏**：配置既可版本管理，也可在运行时由管理员调整
- **Token 与运行观测**：查看 Agent 用量、运行状态、Ingress 队列和 Webhook 成功失败
- **自托管**：数据、模型配置和项目接入关系留在自己的环境中

---

## 一次排查是怎样完成的

~~~text
工单 / 告警 / 用户提问
          ↓
       Ingress
          ↓
按项目路由：Git + 日志 + 配置 + MCP / Skill
          ↓
OpenHands Agent 多轮分析
          ↓
带证据的结论：摘要 · 根因假设 · 影响面 · 建议
          ↓
工作台查看 / 人工确认 / Webhook 回写
~~~

### 和纯 RAG、公司 Copilot 的区别

| 能力 | 纯 RAG | 公司级 Copilot | DeepTicket |
|---|:---:|:---:|:---:|
| 读取项目源码 | 文档片段 | 视平台而定 | ✅ Git workspace |
| 查询内网日志 / 配置 | 需要先灌库 | 通常较粗 | ✅ MCP / Skill |
| 多项目隔离 | 通常有限 | 平台统一管理 | ✅ 项目级配置 |
| 接收工单 / 告警 | ❌ | 视集成而定 | ✅ HTTP API / Webhook |
| 结论写回原系统 | ❌ | 视集成而定 | ✅ Webhook |
| 业务团队自托管 | 视方案而定 | 通常不支持 | ✅ Docker / YAML |

**和 OpenHands 的关系：** OpenHands 负责 Agent 执行；DeepTicket 负责工作台、项目配置、知识库同步、Ingress 和结果回写。

---

## 典型场景

### 产品 / 运营 / QA：先判断是不是 Bug

把日志和配置查询接好后，客服、运营、产品等角色可以直接问：

> “这个现象和需求一致吗？”
>
> “线上配置为什么和文档不一致？”
>
> “这是数据问题、配置问题，还是代码问题？”

回答带上日志、配置项和代码位置，帮助不同角色共同判断问题原因，并决定后续的处理方式。

### 值班与告警：先整理，再决定是否叫人

任意支持 HTTP 的工单或告警系统都可以推送事件，DeepTicket 在后台完成关联项目、读取代码与配置、整理影响面，并通过 Webhook 将结果回写原系统。值班同学看到的是一份可审阅的分析草稿，而不是一条孤立的错误消息。

### 报表与指标：把跨系统关联交给 Agent

接入报表或 BI MCP 后，可以分析活动 ROI、日报与投放日志之间的不一致。垂类示例见 [ad_agent](https://github.com/shanananana/ad_agent)；DeepTicket 本身负责项目隔离、工具接入和编排，不绑定具体业务领域。

---

## 5 分钟跑起来

### 方式一：拉取预构建镜像（推荐）

前提：已安装 Docker Desktop 或 Docker Engine + Compose v2。

~~~bash
mkdir deepticket && cd deepticket
curl -LO https://raw.githubusercontent.com/shanananana/deepticket/main/docker-compose.image.yml
curl -LO https://raw.githubusercontent.com/shanananana/deepticket/main/.env.docker.example
cp .env.docker.example .env
docker compose -f docker-compose.image.yml up -d
~~~

打开 **http://127.0.0.1:8600**，使用默认账户 <code>admin / admin</code> 登录。LLM Key 可以提前写入 <code>.env</code>，也可以登录后在侧栏 **LLM 配置** 中填写。

> ⚠️ 默认账号仅用于本地体验。部署到内网或生产环境前，请立即修改密码、配置鉴权和持久化策略。

### 方式二：Clone 后启动（适合开发调试）

~~~bash
git clone https://github.com/shanananana/deepticket.git
cd deepticket
bash scripts/setup.sh
bash scripts/start_all.sh
~~~

第一次体验可以直接复制 [DEMO_PROMPT.md](docs/DEMO_PROMPT.md) 中的 Nginx 日志提问；想看“日志 → 配置 / 代码 → ROI 结论”的完整流程，参考 [5 分钟上手 & ROI 演示](docs/quickstart-demo.md)。

常用命令：

~~~bash
docker compose logs -f deepticket  # 查看日志
docker compose down                 # 停止服务
bash scripts/verify.sh              # 本地自检
~~~

---

## 架构

<p align="center">
  <a href="docs/assets/architecture.svg"><img src="docs/assets/architecture.png" width="720" alt="DeepTicket 五层架构"></a>
</p>

DeepTicket 将系统拆成输入、知识、引擎、输出和存储等层：输入负责聊天与 Ingress，知识层负责 Git / Skill / MCP，上层由 OpenHands 执行分析，输出层负责流式展示与 Webhook 回写，存储层负责对话、项目配置和运行记录。

---

## 文档

| 文档 | 适合什么时候看 |
|---|---|
| [docs/docker.md](docs/docker.md) | Docker 部署、GHCR 镜像、数据卷和内网试点 |
| [docs/quickstart-demo.md](docs/quickstart-demo.md) | 从零体验 Demo 与 ROI 场景 |
| [docs/DEMO_PROMPT.md](docs/DEMO_PROMPT.md) | 复制即用的 Nginx / ROI 示例提问 |
| [deepticket.example.yaml](deepticket.example.yaml) | 查看完整配置项和接入示例 |
| [deepticket/skills/README.md](deepticket/skills/README.md) | 编写与挂载项目 Skill |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 本地开发、测试与贡献指南 |
| [CHANGELOG.md](CHANGELOG.md) | 版本变化与已知能力边界 |

多项目、MCP、Ingress 和 <code>agents.md</code> 都可以在工作台侧栏配置，也可以通过管理员 API 管理：<code>/api/admin/projects/{id}</code>。

---

## 当前状态

DeepTicket 当前处于 **Alpha（v0.3.3）**。核心链路已经覆盖：项目管理、Git 知识库、Skill / MCP、OpenHands Agent、工作台对话、Ingress 异步分析、Webhook 回写和运行观测。

如果这个方向对你有帮助，欢迎 [Star](https://github.com/shanananana/deepticket)、提交 [Issue](https://github.com/shanananana/deepticket/issues)，或分享你的接入场景。

<p align="center"><sub>DeepTicket · Evidence before escalation · MIT License</sub></p>
