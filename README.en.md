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

<h3 align="center">Self-hosted Agent orchestration for business teams</h3>

<p align="center"><strong>Let frontline staff find evidence before escalating to engineering</strong></p>

<p align="center">Runs on OpenHands · Git / logs / config / MCP · tickets &amp; alerts · not a company Copilot replacement</p>

<p align="center">
  <a href="#overview"><strong>Overview</strong></a>
  ·
  <a href="#features"><strong>Features</strong></a>
  ·
  <a href="#use-cases"><strong>Use cases</strong></a>
  ·
  <a href="#quick-start"><strong>Quick start</strong></a>
  ·
  <a href="#docs"><strong>Docs</strong></a>
</p>

---

## Overview

DeepTicket is a **team-owned Agent orchestration layer**: Git knowledge, internal logs and config, MCP tools, and ticket/alert hooks in one workbench, with multi-turn investigation on OpenHands.

The goal is not “chat more”—it is **evidence before close or escalate**: source paths, log lines, config keys—not just retrieved doc chunks. Engineering keeps Copilot; business teams usually pilot with Docker on their own infra.

---

## Features

<h3>Connect</h3>

<ul>
<li><strong>Multi-project</strong> — sidebar switch; per-project repos, MCP, agents.md</li>
<li><strong>Ingress</strong> — tickets/alerts over HTTP, async analysis in the background</li>
<li><strong>Per-project MCP</strong> — config lookup, release history, internal docs—scoped per team</li>
</ul>

<h3>Investigate</h3>

<ul>
<li><strong>Git sync</strong> — code in workspace; the agent can read source</li>
<li><strong>Logs / config</strong> — Skill templates or MCP wired to your platforms</li>
<li><strong>Evidence in replies</strong> — paths, snippets, keys; agents.md enforces read-only and cite-first</li>
</ul>

<h3>Deliver</h3>

<ul>
<li><strong>Webhook write-back</strong> — conclusions to ticket/ITSM; target is per-project</li>
<li><strong>Human in the loop</strong> — close if it checks out; escalate with context if not</li>
<li><strong>yaml + sidebar</strong> — versioned config or runtime edits</li>
</ul>

---

## Highlight

<h3>Evidence first, not empty chat</h3>

<p>DeepTicket pushes the agent to search the workspace before concluding—not generic advice. Project <code>agents.md</code> sets read-only rules, paths, and “say when unsure.”</p>

<blockquote>
<p>Frontline needs “can I close this?” Engineering needs “escalation with context.” DeepTicket sits in between.</p>
</blockquote>

---

## vs pure RAG / company Copilot

<p>Pick your category: ingested Q&amp;A, company-wide Copilot, or a team-owned layer that hooks internal systems and writes back to tickets.</p>

| | Pure RAG | Platform Copilot | DeepTicket |
|--|:--:|:--:|:--:|
| Read Git source | Chunks | Limited | ✅ |
| Internal logs / config | Ingest | Coarse | ✅ MCP / Skills |
| Ticket / alert write-back | ❌ | Weak | ✅ Ingress |
| Team self-host | Varies | Wait on platform | ✅ Docker / yaml |

<p><strong>vs OpenHands:</strong> OpenHands runs the agent engine; DeepTicket is the workbench, Git sync, and ticket ingress.</p>

---

## Use cases

<h3>Product, ops, QA</h3>

<p>Wire logs and config, add a few MCP tools, give accounts to non-engineers. Typical questions: bug or not? matches spec? prod vs doc?</p>

<p>Replies cite log lines, config keys, and code paths—close yourself or ping engineering with context.</p>

<h3>Reports and metrics</h3>

<p>With a reporting/BI MCP, ask cross-sheet questions (e.g. campaign ROI vs daily report). Let the machine run joins first; you decide what to trust.</p>

<p>Vertical example: <a href="https://github.com/shanananana/ad_agent">ad_agent</a> (ad ROI). DeepTicket is the wiring and multi-project shell.</p>

<h3>Tickets and alerts</h3>

<p>HTTP from your ticket or alert system, async analysis, conclusion out via Webhook. On-call reads the draft, then escalates or not.</p>

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

## Architecture

<p align="center">
  <a href="docs/assets/architecture.svg"><img src="docs/assets/architecture.png" width="640" alt="Five-layer architecture"></a>
</p>

---

## Docs

| Doc | Description |
|-----|-------------|
| [docs/docker.md](docs/docker.md) | Docker deploy, GHCR image, persisted config |
| [docs/DEMO_PROMPT.md](docs/DEMO_PROMPT.md) | Copy-paste sample prompts (Nginx logs, etc.) |
| [docs/quickstart-demo.md](docs/quickstart-demo.md) | Recorded demo and ROI walkthrough |
| [deepticket.example.yaml](deepticket.example.yaml) | Config template (copy to deepticket.yaml) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Local dev, tests, contributing |
| [CHANGELOG.en.md](CHANGELOG.en.md) | Release notes |

<p>Multi-project, MCP, Ingress, and agents.md: sidebar in the workbench or admin API <code>/api/admin/projects/{id}</code></p>

---

## FAQ

<p><strong>Minimum setup?</strong> LLM key; Git repos optional; log/config MCP when needed.</p>

<p><strong>vs company Copilot?</strong> Coexists—usually a small team-owned deploy.</p>

<p><strong>Stage?</strong> Alpha (v0.3.1)—Stars and Issues welcome.</p>

<p>Local dev: <code>pip install -e ".[dev]"</code> · <code>pytest -q</code> · <code>bash scripts/verify.sh --online</code></p>

---

<p align="center"><sub>⭐ <a href="https://github.com/shanananana/deepticket">Star</a> if useful · <a href="LICENSE">MIT</a></sub></p>
