<p align="center">
  <img src="docs/assets/banner-header.png" width="100%" alt="DeepTicket">
</p>

<p align="center">
  <a href="README.en.md">English</a>
  ·
  <a href="CHANGELOG.md">更新日志</a>
  ·
  <a href="https://github.com/shanananana/deepticket/releases/tag/v0.3.0">v0.3.0</a>
  ·
  <a href="LICENSE">MIT</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python 3.11+">
  <img src="https://img.shields.io/github/v/release/shanananana/deepticket?label=release" alt="release">
  <img src="https://img.shields.io/badge/OpenHands-1.39.1-purple" alt="OpenHands">
  <img src="https://img.shields.io/badge/docker-GHCR-2496ED" alt="Docker">
</p>

<h3 align="center">业务组自托管的 SRE Agent 编排层</h3>

<p align="center">接 MCP / 日志 / 配置 / ITSM，在 OpenHands 上跑可复核排障 — 不替换公司 Copilot 平台</p>

<p align="center">
  <a href="#快速开始"><strong>快速开始</strong></a>
  ·
  <a href="docs/docker.md">Docker 文档</a>
  ·
  <a href="docs/DEMO_PROMPT.md">示例提问</a>
  ·
  <a href="docs/assets/architecture.svg">架构图</a>
</p>

---

## Demo

<p align="center">
  <a href="docs/assets/demo.mp4"><img src="docs/assets/demo.gif" width="640" alt="DeepTicket 演示"></a>
</p>

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

<p><code>ghcr.io/shanananana/deepticket:v0.3.0</code> · 详见 <a href="docs/docker.md">docs/docker.md</a></p>

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

<p>体验：粘贴 <a href="docs/DEMO_PROMPT.md">DEMO_PROMPT</a> 里的 Nginx 日志 · ROI 录屏 <a href="docs/quickstart-demo.md">quickstart-demo</a></p>

</details>

</td>
</tr>
</table>

<p align="center"><sub>停止：<code>docker compose down</code> · 日志：<code>docker compose logs -f deepticket</code> · 自检：<code>bash scripts/verify.sh</code></sub></p>

---

## 是什么

DeepTicket 是 **OpenHands 之上的薄编排层**：工作台 + Git 知识库 + Ingress/Webhook + 多项目配置，让 Agent 在 **源码 + 日志 + 配置** 上作答，而不是纯 RAG 猜测。

<p align="center">
  <a href="docs/assets/architecture.svg"><img src="docs/assets/architecture.png" width="640" alt="五层架构"></a>
</p>

| | 纯 RAG | 平台 Copilot | **DeepTicket** |
|--|:--:|:--:|:--:|
| 读 Git 源码 | 片段 | 有限 | ✅ |
| 内网日志 / 配置 | 灌库 | 粗 | ✅ MCP / Skill |
| 工单 / 告警闭环 | ❌ | 弱 | ✅ Ingress |
| 业务组自托管试点 | 中 | 等平台 | ✅ Docker / yaml |

---

## 更多

<details>
<summary><strong>核心能力</strong></summary>

<ul>
<li><strong>多项目</strong> — 侧栏切换；每项目独立 repos / MCP / agents.md（Redis 存储，后台分项保存）</li>
<li><strong>工作台</strong> — 多轮对话、Thinking 步骤、置信度、截图上传、关页后 Agent 仍写回历史</li>
<li><strong>Ingress</strong> — 告警 HTTP 进 → 异步分析 → Webhook 回写（<code>bash scripts/test_ingress_e2e.sh</code>）</li>
<li><strong>示例</strong> — 垂类 Agent 见 <a href="https://github.com/shanananana/ad_agent">ad_agent</a>；DeepTicket 负责接基建</li>
</ul>

</details>

<details>
<summary><strong>配置</strong></summary>

<p>主配置 <code>deepticket.yaml</code>（从 <code>deepticket.example.yaml</code> 复制）。常用：<code>llm</code> · <code>knowledge.repos</code> · <code>ingress</code> · <code>storage</code>（多项目建议 Redis）· <code>mcp</code></p>
<p>管理员 API：<code>/api/admin/projects/{id}</code> · 项目配置见工作台侧栏</p>

</details>

<details>
<summary><strong>开发与贡献</strong></summary>

<pre><code>pip install -e ".[dev]"
pytest -q
bash scripts/verify.sh --online
</code></pre>
<p>见 <a href="CONTRIBUTING.md">CONTRIBUTING.md</a> · Alpha（<a href="https://github.com/shanananana/deepticket/releases/tag/v0.3.0">v0.3.0</a>），欢迎 Star / Issue</p>

</details>

<details>
<summary><strong>常见问题</strong></summary>

<p><strong>和 OpenHands？</strong> OpenHands 跑 Agent；DeepTicket 加工单接入、知识库、多用户工作台。</p>
<p><strong>和 Copilot 冲突吗？</strong> 不冲突。业务组薄层自托管，与公司平台 Agent 并存。</p>
<p><strong>最小要能跑？</strong> LLM Key +（可选）Git 仓库；日志 / 配置 MCP 按需接。</p>

</details>

---

<p align="center"><sub>⭐ 有帮助请 <a href="https://github.com/shanananana/deepticket">Star</a> · <a href="LICENSE">MIT</a></sub></p>
