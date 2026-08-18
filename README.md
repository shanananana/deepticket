<p align="center">
  <img src="docs/assets/banner-header.png" width="100%" alt="DeepTicket 品牌 Banner">
</p>

<p align="center">
  <a href="README.en.md">English</a>
  ·
  <a href="CHANGELOG.md">更新日志</a>
  ·
  <a href="https://github.com/shanananana/deepticket/releases/tag/v0.3.1">v0.3.1</a>
  ·
  <a href="LICENSE">MIT</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python 3.11+">
  <img src="https://img.shields.io/github/v/release/shanananana/deepticket?label=release" alt="release">
  <img src="https://img.shields.io/badge/OpenHands-1.39.1-purple" alt="OpenHands">
  <img src="https://img.shields.io/badge/docker-GHCR-2496ED" alt="Docker">
</p>

<h3 align="center">业务组自托管的 Agent 编排层</h3>

<p align="center"><strong>让一线先查证据，再决定要不要升级研发</strong></p>

<p align="center">跑在 OpenHands 上 · 接 Git / 日志 / 配置 / MCP · 也能接工单和告警 · 不替代公司 Copilot</p>

<p align="center">
  <a href="#简介"><strong>简介</strong></a>
  ·
  <a href="#演示"><strong>演示</strong></a>
  ·
  <a href="#特性"><strong>特性</strong></a>
  ·
  <a href="#典型场景"><strong>典型场景</strong></a>
  ·
  <a href="#快速开始"><strong>快速开始</strong></a>
  ·
  <a href="#文档"><strong>文档</strong></a>
</p>

---

## 简介

DeepTicket 是业务组自己部署的 **Agent 编排层**：把 Git 知识库、内网日志与配置、MCP 工具、工单/告警接到同一工作台，在 OpenHands 上跑多轮排查。

它解决的不是「多聊几句」，而是 **一线关单前能查到依据**——源码路径、日志行、配置项——而不是只检索几段文档。研发继续用 Copilot；业务组通常 Docker 起一套小的，先在小范围试。

---

## 演示

<p align="center">
  <video src="https://github.com/user-attachments/assets/3bc7b913-f3a9-49c5-bbe7-1c15f1a0381b" width="720" controls autoplay muted loop playsinline></video>
</p>
<p align="center"><sub>ad-agent ROI 归因 Demo · 查日志 等功能需真实真实mcp或skill后生效 部分ui为突出展示与实际项目不一致</sub></p>

---

## 特性

<h3>接得进</h3>

<ul>
<li><strong>多项目</strong> — 侧栏切换，每项目独立 repos、MCP、agents.md</li>
<li><strong>Ingress</strong> — 工单/告警 HTTP 进来，后台异步分析</li>
<li><strong>按项目配 MCP</strong> — 查配置、查发布、接内网文档，各管各的</li>
</ul>

<h3>查得到</h3>

<ul>
<li><strong>Git 同步</strong> — 代码进 workspace，Agent 能翻源码</li>
<li><strong>日志 / 配置</strong> — Skill 模板或 MCP，接你们已有平台</li>
<li><strong>回答带证据</strong> — 路径、片段、配置键；agents.md 约束只读与依据优先</li>
</ul>

<h3>回得去</h3>

<ul>
<li><strong>Webhook 写回</strong> — 分析结论回工单/ITSM，写哪里项目里配</li>
<li><strong>人机分工</strong> — 能对上先关单；对不上再 @ 研发，少截图来回</li>
<li><strong>yaml + 侧栏</strong> — 配置可版本管理，也可运行时改</li>
</ul>

---

## 亮点

<h3>证据优先，不空聊</h3>

<p>DeepTicket 默认让 Agent 在 workspace 里找依据再下结论，而不是堆通用建议。项目级 <code>agents.md</code> 写清楚：只读、引用路径、不确定就标注。</p>

<blockquote>
<p>一线要的是「能不能关单」；研发要的是「升级时带上下文」——中间这层就是 DeepTicket 干的事。</p>
</blockquote>

---

## 和纯 RAG / 公司 Copilot 的区别

<p>帮你归类：你要的是「灌库问答」、公司统一 Copilot，还是「业务组自己接内网、能写回工单」？</p>

| | 纯 RAG | 平台 Copilot | DeepTicket |
|--|:--:|:--:|:--:|
| 读 Git 源码 | 片段 | 有限 | ✅ |
| 内网日志 / 配置 | 灌库 | 粗 | ✅ MCP / Skill |
| 工单 / 告警回写 | ❌ | 弱 | ✅ Ingress |
| 业务组自己部署 | 看情况 | 等平台 | ✅ Docker / yaml |

<p>和 OpenHands：OpenHands 跑 Agent 引擎；DeepTicket 是外面的工作台、知识库同步与工单接入。</p>

---

## 典型场景

<h3>产品 / 运营 / QA</h3>

<p>日志、配置接好，再挂几个 MCP，就可以给非研发开账号。常见问法：「这是 bug 吗？」「和设计一致吗？」「文档写的和线上为什么不一样？」</p>

<p>回答里会带上日志片段、配置项、代码位置，自己能对上就先关单；对不上再 @ 研发。</p>

<h3>报表、指标</h3>

<p>接了报表或 BI 的 MCP 之后，可以问跨表问题，比如活动 ROI 和日报对不上。人先让机器跑一轮关联，再看最后几条要不要信。</p>

<p>垂类例子见 <a href="https://github.com/shanananana/ad_agent">ad_agent</a>（投放 ROI）；DeepTicket 本身只管接线和多项目配置。</p>

<h3>工单、告警</h3>

<p>内部工单或报警平台 HTTP 打进来，后台异步分析，结论用 Webhook 写回去。值班先看一眼机器总结，再决定要不要升级叫人。</p>

---

## 快速开始

<p align="center">打开 <strong>http://127.0.0.1:8600</strong> · 默认 <code>admin / admin</code> · LLM Key 可在侧栏 <strong>LLM 配置</strong> 填写</p>

<table>
<tr>
<td width="50%" valign="top">

<details open>
<summary><strong>🐳 Docker（远程镜像，推荐）</strong></summary>

<pre><code>mkdir deepticket &amp;&amp; cd deepticket
curl -LO https://raw.githubusercontent.com/shanananana/deepticket/main/docker-compose.image.yml
curl -LO https://raw.githubusercontent.com/shanananana/deepticket/main/.env.docker.example
cp .env.docker.example .env
docker compose -f docker-compose.image.yml up -d
</code></pre>

<p><code>ghcr.io/shanananana/deepticket:v0.3.1</code> · 详见 <a href="docs/docker.md">docs/docker.md</a></p>

</details>

</td>
<td width="50%" valign="top">

<details>
<summary><strong>📦 Clone（开发调试）</strong></summary>

<pre><code>git clone https://github.com/shanananana/deepticket.git
cd deepticket
bash scripts/setup.sh
bash scripts/start_all.sh
</code></pre>

<p>体验：粘贴 <a href="docs/DEMO_PROMPT.md">DEMO_PROMPT</a> 里的 Nginx 日志 · 录屏 <a href="docs/quickstart-demo.md">quickstart-demo</a></p>

</details>

</td>
</tr>
</table>

<p align="center"><sub>停止：<code>docker compose down</code> · 日志：<code>docker compose logs -f deepticket</code> · 自检：<code>bash scripts/verify.sh</code></sub></p>

---

## 架构

<p align="center">
  <a href="docs/assets/architecture.svg"><img src="docs/assets/architecture.png" width="640" alt="五层架构"></a>
</p>

---

## 文档

| 文档 | 说明 |
|------|------|
| [docs/docker.md](docs/docker.md) | Docker 部署、GHCR 镜像、持久化配置 |
| [docs/DEMO_PROMPT.md](docs/DEMO_PROMPT.md) | 复制即用的示例提问（Nginx 日志等） |
| [docs/quickstart-demo.md](docs/quickstart-demo.md) | 录屏 demo 与 ROI 场景说明 |
| [deepticket.example.yaml](deepticket.example.yaml) | 统一配置模板（复制为 deepticket.yaml） |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 本地开发、测试、贡献指南 |
| [CHANGELOG.md](CHANGELOG.md) | 版本更新记录 |

<p>多项目、MCP、Ingress、agents.md 可在工作台侧栏配置，或通过管理员 API：<code>/api/admin/projects/{id}</code></p>

---

## 常见问题

<p><strong>最少要有什么？</strong> LLM Key；Git 仓库可选；日志、配置 MCP 用到再接。</p>

<p><strong>和公司 Copilot？</strong> 不冲突，一般是业务组自己起一套小的。</p>

<p><strong>项目阶段？</strong> Alpha（当前 v0.3.1），欢迎 Star 和 Issue。</p>

<p>本地开发：<code>pip install -e ".[dev]"</code> · <code>pytest -q</code> · <code>bash scripts/verify.sh --online</code></p>

---

<p align="center"><sub>⭐ 有帮助请 <a href="https://github.com/shanananana/deepticket">Star</a> · <a href="LICENSE">MIT</a></sub></p>
