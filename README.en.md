<p align="center">
  <img src="docs/assets/banner-header.png" width="100%" alt="DeepTicket">
</p>

<p align="center">
  <a href="README.md">中文</a>
  ·
  <a href="CHANGELOG.en.md">Changelog</a>
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

<h3 align="center">Self-hosted SRE Agent orchestration for business teams</h3>

<p align="center">A thin layer on OpenHands: logs, config, MCP, tickets, alerts. Not a replacement for company Copilot.</p>

<p align="center">
  <a href="#use-cases"><strong>Use cases</strong></a>
  ·
  <a href="#quick-start"><strong>Quick start</strong></a>
  ·
  <a href="docs/docker.md">Docker docs</a>
  ·
  <a href="docs/DEMO_PROMPT.md">Sample prompts</a>
  ·
  <a href="CONTRIBUTING.md">Contributing</a>
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

<p><code>ghcr.io/shanananana/deepticket:v0.3.1</code> · see <a href="docs/docker.md">docs/docker.md</a></p>

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

DeepTicket sits on OpenHands: Git sync for knowledge, a chat workbench, per-project MCP and Ingress. Answers pull from source, logs, and config—not just retrieved doc chunks.

Meant for a business team to run themselves (often Docker on a small pilot). Coexists with company-wide Copilot.

---

## Use cases

<h3>Product, ops, QA</h3>

<p>Hook up logs and config, add a few MCP tools (config lookup, release history, internal docs), and give accounts to non-engineers. Typical questions: bug or not? matches the spec? prod vs doc mismatch?</p>

<p>Replies cite log lines, config keys, and code paths. Close it yourself if it checks out; ping engineering with context if not—fewer screenshot ping-pongs.</p>

<h3>Reports and metrics</h3>

<p>With a reporting/BI MCP, ask cross-sheet questions—campaign ROI vs daily report, which channel dropped. Humans spend hours aligning definitions; let the machine run the joins first, then you decide what to trust.</p>

<p>Vertical example: <a href="https://github.com/shanananana/ad_agent">ad_agent</a> (ad ROI). DeepTicket is the wiring and multi-project shell.</p>

<h3>Tickets and alerts</h3>

<p>HTTP from your ticket or alert system, async analysis in the background, conclusion out via Webhook (target is configurable). On-call reads the draft, then escalates or not.</p>

<details>
<summary>vs pure RAG / company Copilot</summary>

| | Pure RAG | Platform Copilot | DeepTicket |
|--|:--:|:--:|:--:|
| Read Git source | Chunks | Limited | ✅ |
| Internal logs / config | Ingest | Coarse | ✅ MCP / Skills |
| Ticket / alert write-back | ❌ | Weak | ✅ Ingress |
| Team self-host | Varies | Wait on platform | ✅ Docker / yaml |

<p><a href="docs/assets/architecture.svg">Architecture diagram</a></p>

</details>

---

## Docs

<p><a href="docs/docker.md">Docker</a> · <a href="docs/DEMO_PROMPT.md">Sample prompts</a> · <a href="docs/quickstart-demo.md">Demo recording</a> · <a href="CONTRIBUTING.md">Contributing</a></p>

<p>Copy <code>deepticket.example.yaml</code> to configure; multi-project, MCP, Ingress in the sidebar or yaml. Admin API: <code>/api/admin/projects/{id}</code></p>

---

## FAQ

<p><strong>vs OpenHands?</strong> OpenHands runs the agent; DeepTicket is the workbench, Git sync, and ticket hook.</p>

<p><strong>vs company Copilot?</strong> Coexists—usually a small team-owned deploy.</p>

<p><strong>Minimum setup?</strong> LLM key; Git repos optional; log/config MCP when needed.</p>

<p>Local dev: <code>pip install -e ".[dev]"</code> · <code>pytest -q</code> · <code>bash scripts/verify.sh --online</code></p>

---

<p align="center"><sub>⭐ <a href="https://github.com/shanananana/deepticket">Star</a> if useful · <a href="LICENSE">MIT</a></sub></p>
