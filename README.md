<p align="center">
  <img src="docs/assets/banner-header.png" width="100%" alt="DeepTicket">
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

<h3 align="center">业务组自托管的 SRE Agent 编排层</h3>

<p align="center">OpenHands 上面薄薄一层：接日志、配置、MCP，也能接工单和告警。不跟公司 Copilot 抢位置。</p>

<p align="center">
  <a href="#典型场景"><strong>典型场景</strong></a>
  ·
  <a href="#快速开始"><strong>快速开始</strong></a>
  ·
  <a href="docs/docker.md">Docker 文档</a>
  ·
  <a href="docs/DEMO_PROMPT.md">示例提问</a>
  ·
  <a href="CONTRIBUTING.md">开发</a>
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

<p>体验：粘贴 <a href="docs/DEMO_PROMPT.md">DEMO_PROMPT</a> 里的 Nginx 日志 · ROI 录屏 <a href="docs/quickstart-demo.md">quickstart-demo</a></p>

</details>

</td>
</tr>
</table>

<p align="center"><sub>停止：<code>docker compose down</code> · 日志：<code>docker compose logs -f deepticket</code> · 自检：<code>bash scripts/verify.sh</code></sub></p>

---

## 是什么

DeepTicket 跑在 OpenHands 上，主要干几件事：同步 Git 当知识库、工作台里多轮对话、按项目配 MCP 和 Ingress。回答时会去翻源码、日志、配置，而不是只检索几段文档。

和公司 Copilot 不冲突——通常是业务组自己 Docker 起一套，先在小范围试。

---

## 典型场景

<h3>产品 / 运营 / QA</h3>

<p>日志、配置接好，再挂几个 MCP（查配置、查发布、查内部文档都行），就可以给非研发开账号。常见问法：「这是 bug 吗？」「和设计一致吗？」「文档写的和线上为什么不一样？」</p>

<p>回答里会带上日志片段、配置项、代码位置，自己能对上就先关单；对不上再 @ 研发，比纯口述省很多来回。</p>

<h3>报表、指标</h3>

<p>接了报表或 BI 的 MCP 之后，可以问跨表的问题，比如活动 ROI 和日报对不上、某个渠道突然掉量。人要手工拉好几张表、对口径，很费时间。这里更适合先跑一轮关联和猜测，人只看最后几条要不要信。</p>

<p>垂类例子见 <a href="https://github.com/shanananana/ad_agent">ad_agent</a>（投放 ROI）；DeepTicket 本身只管接线和多项目配置。</p>

<h3>工单、告警</h3>

<p>内部工单或报警平台 HTTP 打进来，后台异步分析，结论用 Webhook 写回去——写到哪里、写不写，项目里配。值班先看一眼机器总结，再决定要不要升级叫人。</p>

<details>
<summary>和纯 RAG / 公司 Copilot 比一下</summary>

| | 纯 RAG | 平台 Copilot | DeepTicket |
|--|:--:|:--:|:--:|
| 读 Git 源码 | 片段 | 有限 | ✅ |
| 内网日志 / 配置 | 灌库 | 粗 | ✅ MCP / Skill |
| 工单 / 告警回写 | ❌ | 弱 | ✅ Ingress |
| 业务组自己部署 | 看情况 | 等平台 | ✅ Docker / yaml |

<p><a href="docs/assets/architecture.svg">架构图</a></p>

</details>

---

## 文档

<p><a href="docs/docker.md">Docker 部署</a> · <a href="docs/DEMO_PROMPT.md">示例提问</a> · <a href="docs/quickstart-demo.md">录屏 demo</a> · <a href="CONTRIBUTING.md">开发贡献</a></p>

<p>配置从 <code>deepticket.example.yaml</code> 复制；多项目、MCP、Ingress 在工作台侧栏或 <code>deepticket.yaml</code> 里改。管理员 API：<code>/api/admin/projects/{id}</code></p>

---

## 常见问题

<p><strong>和 OpenHands？</strong> OpenHands 跑 Agent；DeepTicket 是外面的工作台、知识库同步、工单接入。</p>

<p><strong>和公司 Copilot？</strong> 不冲突，一般是业务组自己起一套小的。</p>

<p><strong>最少要有什么？</strong> LLM Key；Git 仓库可选；日志、配置 MCP 用到再接。</p>

<p>本地开发：<code>pip install -e ".[dev]"</code> · <code>pytest -q</code> · <code>bash scripts/verify.sh --online</code></p>

---

<p align="center"><sub>⭐ 有帮助请 <a href="https://github.com/shanananana/deepticket">Star</a> · <a href="LICENSE">MIT</a></sub></p>
