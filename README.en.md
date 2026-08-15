<p align="center">
  <a href="README.md">中文</a>
  ·
  <a href="CHANGELOG.en.md">Changelog</a>
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

<h3 align="center">Self-hosted SRE Agent orchestration for business teams</h3>

<p align="center">Wire MCP, logs, config, and ITSM on OpenHands — does not replace company Copilot platforms</p>

<p align="center">
  <a href="#quick-start"><strong>Quick start</strong></a>
  ·
  <a href="docs/docker.md">Docker docs</a>
  ·
  <a href="docs/DEMO_PROMPT.md">Sample prompts</a>
  ·
  <a href="docs/assets/architecture.svg">Architecture</a>
</p>

---

## Demo

<p align="center">
  <a href="docs/assets/demo.mp4"><img src="docs/assets/demo.gif" width="640" alt="DeepTicket demo"></a>
</p>

---

## Quick start

<p align="center">Open <strong>http://127.0.0.1:8600</strong> · default <code>admin / admin</code> · set LLM in sidebar <strong>LLM settings</strong></p>

<table>
<tr>
<td width="50%" valign="top">

<details open>
<summary><strong>🐳 Docker (remote image, recommended)</strong></summary>

<pre><code>mkdir deepticket &amp;&amp; cd deepticket
curl -LO https://raw.githubusercontent.com/shanananana/deepticket/main/docker-compose.image.yml
curl -LO https://raw.githubusercontent.com/shanananana/deepticket/main/.env.docker.example
cp .env.docker.example .env
docker compose -f docker-compose.image.yml up -d
</code></pre>

<p><code>ghcr.io/shanananana/deepticket:v0.3.0</code> · see <a href="docs/docker.md">docs/docker.md</a></p>

</details>

</td>
<td width="50%" valign="top">

<details>
<summary><strong>📦 Clone (development)</strong></summary>

<pre><code>git clone https://github.com/shanananana/deepticket.git
cd deepticket
bash scripts/setup.sh
bash scripts/start_all.sh
</code></pre>

<p>Try the Nginx log in <a href="docs/DEMO_PROMPT.md">DEMO_PROMPT.md</a> · ROI demo <a href="docs/quickstart-demo.md">quickstart-demo</a></p>

</details>

</td>
</tr>
</table>

<p align="center"><sub>Stop: <code>docker compose down</code> · Logs: <code>docker compose logs -f deepticket</code> · Verify: <code>bash scripts/verify.sh</code></sub></p>

---

## What it is

A **thin layer on OpenHands**: workbench, Git knowledge sync, Ingress/Webhook, and multi-project config — agents ground answers in **source + logs + config**, not RAG guesses alone.

<p align="center">
  <a href="docs/assets/architecture.svg"><img src="docs/assets/architecture.png" width="640" alt="Architecture"></a>
</p>

| | Pure RAG | Platform Copilot | **DeepTicket** |
|--|:--:|:--:|:--:|
| Read Git source | Chunks | Limited | ✅ |
| Internal logs / config | Ingest | Coarse | ✅ MCP / Skills |
| Ticket / alert loop | ❌ | Weak | ✅ Ingress |
| Team self-host pilot | Medium | Wait on platform | ✅ Docker / yaml |

---

## More

<details>
<summary><strong>Capabilities</strong></summary>

<ul>
<li><strong>Multi-project</strong> — Sidebar switch; per-project repos / MCP / agents.md (Redis, sectional admin saves)</li>
<li><strong>Workbench</strong> — Chat, Thinking steps, confidence, screenshot upload, background persistence</li>
<li><strong>Ingress</strong> — HTTP in → async analysis → Webhook out (<code>bash scripts/test_ingress_e2e.sh</code>)</li>
<li><strong>Example</strong> — Vertical agent: <a href="https://github.com/shanananana/ad_agent">ad_agent</a>; DeepTicket wires infra</li>
</ul>

</details>

<details>
<summary><strong>Configuration</strong></summary>

<p>Main file <code>deepticket.yaml</code> (from <code>deepticket.example.yaml</code>). Sections: <code>llm</code> · <code>knowledge.repos</code> · <code>ingress</code> · <code>storage</code> (Redis for multi-project) · <code>mcp</code></p>
<p>Admin API: <code>/api/admin/projects/{id}</code> · UI: sidebar Project settings</p>

</details>

<details>
<summary><strong>Development</strong></summary>

<pre><code>pip install -e ".[dev]"
pytest -q
bash scripts/verify.sh --online
</code></pre>
<p>See <a href="CONTRIBUTING.md">CONTRIBUTING.md</a> · Alpha — Stars and Issues welcome</p>

</details>

<details>
<summary><strong>FAQ</strong></summary>

<p><strong>vs OpenHands?</strong> OpenHands runs the agent; DeepTicket adds tickets, knowledge sync, and multi-user workbench.</p>
<p><strong>vs company Copilot?</strong> Coexists — a thin self-hosted team layer.</p>
<p><strong>Minimum to run?</strong> LLM key + optional Git repos; log/config MCP when you need them.</p>

</details>

---

<p align="center"><sub>⭐ <a href="https://github.com/shanananana/deepticket">Star</a> if useful · <a href="LICENSE">MIT</a></sub></p>
