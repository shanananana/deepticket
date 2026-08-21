<p align="center">
  <img src="docs/assets/banner-header.png" width="100%" alt="DeepTicket brand banner">
</p>

<p align="center">
  <a href="README.md">中文</a>
  ·
  <a href="CHANGELOG.en.md">Changelog</a>
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

<p align="center"><strong>An AI triage workbench that connects to your internal systems.</strong></p>

<p align="center"><strong>Start from a ticket, pull code, logs, and config together, and finish the first round of investigation.</strong></p>

<p align="center">It routes events from internal systems into an Agent, wires project source, logs, config, and internal tools into one analysis, then writes evidence-backed conclusions back to the source system.</p>

<p align="center">
  <a href="#what-it-is"><strong>What it is</strong></a>
  ·
  <a href="#demo"><strong>Demo</strong></a>
  ·
  <a href="#core-capabilities"><strong>Core capabilities</strong></a>
  ·
  <a href="#get-started-in-5-minutes"><strong>Get started</strong></a>
  ·
  <a href="#architecture"><strong>Architecture</strong></a>
  ·
  <a href="#docs"><strong>Docs</strong></a>
</p>

---

## What it is

DeepTicket is a **self-hosted AI ticket triage and Agent orchestration platform** deployed in your own environment.

It exposes a unified HTTP Ingress API and configurable Webhooks: internal ticketing, alerting, monitoring, or custom systems can integrate using a common event format as long as they can send or receive HTTP requests. DeepTicket provides generic integration capabilities—it does not ship vendor-specific adapters out of the box.

Tickets routed into DeepTicket are mapped to the right Git repos, log-query Skills, config-center MCPs, and other internal tools per project. After OpenHands completes multi-turn analysis, DeepTicket can write summaries, evidence, impact, root-cause hypotheses, and recommendations back via Webhook—or store results only without callback.

In one line: **DeepTicket turns internal tickets from “someone re-describes the problem” into “automated first-pass triage with full project context.”**

---

## Demo

<p align="center">
  <video src="https://github.com/user-attachments/assets/3bc7b913-f3a9-49c5-bbe7-1c15f1a0381b" width="720" controls autoplay muted loop playsinline></video>
</p>
<p align="center"><sub>ad-agent ROI attribution demo · log lookup and similar capabilities require real Skill / MCP wiring · some UI is enhanced for demo and may differ from your deployment</sub></p>

---

## Why DeepTicket

Many issues do not need engineering immediately—but they also cannot be closed with “please check the logs.”

DeepTicket puts everything needed for analysis in one workbench: project source, runtime logs, config, internal tools, and the original ticket. Support, ops, product, and engineering can collaborate on the same context. The Agent reads facts first, then explains cause, impact, and suggested next steps.

> **From “ask an AI” to “complete an investigation.”**
>
> The goal is not longer chat—it is conclusions backed by evidence.

### Who it is for

- Teams that want business units to deploy and wire internal data themselves
- Teams that need product, ops, QA, or on-call to run a first factual check before escalation
- Teams that already have Git, log platforms, config centers, or ITSM but lack a unified Agent entry point

### What it is not

DeepTicket is not a replacement for company-wide Copilot, nor a pure RAG stack that ingests all docs into a vector store. It is a **project-scoped triage and write-back orchestration layer**: hook real tools, bound by project, and make the Agent work against verifiable context.

---

## Core capabilities

### 01 · Connect real context

- **Git knowledge sync**: sync one or more repos into the Agent workspace; source, docs, and config searchable together
- **Logs and config lookup**: built-in Skill templates or MCP to existing platforms—no data pipeline rewrite required
- **Multi-project isolation**: per-project repos, MCP, Skills, <code>agents.md</code>, and membership

### 02 · Ground conclusions in evidence

- **Evidence first**: answers cite source paths, log snippets, config keys, and related files
- **Scoped access**: Git and internal systems use read-only tokens; <code>agents.md</code> adds analysis rules, citation, and uncertainty handling
- **Visible process**: workbench shows Agent steps, streaming replies, confidence, and chat history
- **Say when unsure**: missing evidence is stated explicitly—not filled with generic advice

### 03 · From ingress to write-back

- **Ingress**: HTTP API / Webhook for any internal ticket, ITSM, alert, or custom system
- **Async analysis**: background queue runs Agent jobs; callers need not hold a connection
- **Webhook write-back**: push conclusions to the source ticket system, or store only
- **Human in the loop**: machine gathers facts; people judge cause, impact, and action

### 04 · Easy to pilot, easy to govern

- **Docker one-liner**: Web, OpenHands Agent Server, and Redis via Compose
- **YAML + admin sidebar**: versioned config and runtime admin edits
- **Token and run observability**: Agent usage, run status, Ingress queue, Webhook success/failure
- **Self-hosted**: data, model config, and project wiring stay in your environment

---

## How an investigation runs

~~~text
Ticket / alert / user question
          ↓
       Ingress
          ↓
Route by project: Git + logs + config + MCP / Skill
          ↓
OpenHands Agent multi-turn analysis
          ↓
Evidence-backed output: summary · hypothesis · impact · recommendations
          ↓
Workbench review / human confirm / Webhook write-back
~~~

### vs pure RAG and company Copilot

| Capability | Pure RAG | Company Copilot | DeepTicket |
|---|:---:|:---:|:---:|
| Read project source | Doc chunks | Varies | ✅ Git workspace |
| Internal logs / config | Ingest first | Often coarse | ✅ MCP / Skill |
| Multi-project isolation | Limited | Central platform | ✅ Per-project config |
| Ingest tickets / alerts | ❌ | Varies | ✅ HTTP API / Webhook |
| Write back to source system | ❌ | Varies | ✅ Webhook |
| Business team self-host | Varies | Usually no | ✅ Docker / YAML |

**Relationship to OpenHands:** OpenHands runs the Agent; DeepTicket provides the workbench, project config, knowledge sync, Ingress, and write-back.

---

## Typical scenarios

### Product / ops / QA: is this a bug?

After wiring logs and config, support, ops, and product can ask directly:

> “Does this behavior match the requirement?”
>
> “Why does prod config differ from the doc?”
>
> “Data issue, config issue, or code issue?”

Answers include logs, config keys, and code locations so teams can decide next steps together.

### On-call and alerts: triage before paging

Any HTTP-capable ticket or alert system can push events. DeepTicket correlates the project, reads code and config, summarizes impact, and writes back via Webhook. On-call gets a reviewable draft—not an isolated error line.

### Reports and metrics: cross-system reasoning

With a reporting or BI MCP, analyze mismatches between campaign ROI, daily reports, and delivery logs. Vertical example: [ad_agent](https://github.com/shanananana/ad_agent); DeepTicket handles isolation, tooling, and orchestration—not a fixed domain.

---

## Get started in 5 minutes

### Option 1: Pre-built image (recommended)

Prerequisites: Docker Desktop or Docker Engine + Compose v2.

~~~bash
mkdir deepticket && cd deepticket
curl -LO https://raw.githubusercontent.com/shanananana/deepticket/main/docker-compose.image.yml
curl -LO https://raw.githubusercontent.com/shanananana/deepticket/main/.env.docker.example
cp .env.docker.example .env
docker compose -f docker-compose.image.yml up -d
~~~

Open **http://127.0.0.1:8600** and sign in with <code>admin / admin</code>. Set your LLM key in <code>.env</code> before start, or in the sidebar **LLM settings** after login.

> ⚠️ Default credentials are for local trial only. Change password, auth, and persistence before internal or production deployment.

### Option 2: Clone and run (development)

~~~bash
git clone https://github.com/shanananana/deepticket.git
cd deepticket
bash scripts/setup.sh
bash scripts/start_all.sh
~~~

Copy the Nginx log prompt from [DEMO_PROMPT.md](docs/DEMO_PROMPT.md) for a first chat; for the full “logs → config / code → ROI” flow see [Quick start & ROI demo](docs/quickstart-demo.md).

Common commands:

~~~bash
docker compose logs -f deepticket  # tail logs
docker compose down                 # stop
bash scripts/verify.sh              # local self-check
~~~

---

## Architecture

<p align="center">
  <a href="docs/assets/architecture.svg"><img src="docs/assets/architecture.png" width="720" alt="DeepTicket five-layer architecture"></a>
</p>

DeepTicket is split into input, knowledge, engine, output, and storage layers: input handles chat and Ingress; knowledge handles Git / Skill / MCP; OpenHands runs analysis; output handles streaming UI and Webhook write-back; storage holds chats, project config, and run records.

---

## Docs

| Doc | When to read |
|---|---|
| [docs/docker.md](docs/docker.md) | Docker deploy, GHCR image, volumes, internal pilot |
| [docs/quickstart-demo.md](docs/quickstart-demo.md) | Demo and ROI walkthrough from scratch |
| [docs/DEMO_PROMPT.md](docs/DEMO_PROMPT.md) | Copy-paste Nginx / ROI sample prompts |
| [deepticket.example.yaml](deepticket.example.yaml) | Full config and integration examples |
| [deepticket/skills/README.md](deepticket/skills/README.md) | Authoring and mounting project Skills |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Local dev, tests, contributing |
| [CHANGELOG.en.md](CHANGELOG.en.md) | Release notes and known limits |

Multi-project, MCP, Ingress, and <code>agents.md</code> are configurable in the workbench sidebar or via admin API <code>/api/admin/projects/{id}</code>.

---

## Current status

DeepTicket is in **Alpha (v0.3.3)**. Core flows cover project management, Git knowledge base, Skill / MCP, OpenHands Agent, workbench chat, Ingress async analysis, Webhook write-back, and run observability.

If this direction helps you, please [Star](https://github.com/shanananana/deepticket), open an [Issue](https://github.com/shanananana/deepticket/issues), or share your integration story.

<p align="center"><sub>DeepTicket · Evidence before escalation · MIT License</sub></p>
