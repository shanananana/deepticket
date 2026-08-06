<p align="center">
  <a href="README.md">中文</a>
  ·
  <a href="CHANGELOG.en.md">Changelog</a>
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

**An intelligent Agent platform for production incidents and project Q&A** — an **Ingress / Webhook orchestration layer** on [OpenHands](https://github.com/OpenHands/OpenHands) so agents ground answers in **Git source + logs + config**, not RAG guesses alone.

Keywords: AIOps · SRE · on-call · incident triage · root cause analysis · LLM agent · MCP · FastAPI

- **Ingress** — HTTP events from monitoring / Jira / ITSM, async queue + API key
- **Outbound** — Webhook to ITSM or store-only
- **Workbench** — Multi-turn chat, log paste, Thinking steps, analysis confidence; SSE heartbeat for reverse proxies
- **Example** — Vertical agent reference: [ad_agent](https://github.com/shanananana/ad_agent) (Spring AI ad ops); DeepTicket is the ops orchestration layer

<p align="center">
  <a href="docs/quickstart-demo.md"><strong>5-minute quick start</strong></a>
  ·
  <a href="docs/DEMO_PROMPT.md">Sample prompts</a>
  ·
  <a href="https://github.com/shanananana/ad_agent">ad_agent demo</a>
</p>

---

## Demo

<p align="center">
  <a href="docs/assets/demo.mp4">
    <img src="docs/assets/demo.gif" width="720" alt="DeepTicket demo: OpenHands agent analyzes ad campaign ROI drop with Thinking steps and confidence badge">
  </a>
</p>

<p align="center"><sub>Click the GIF for the full MP4 (~67s) · GitHub does not render <code>&lt;video&gt;</code> in README</sub></p>

---

## 5-minute quick start

```bash
git clone https://github.com/shanananana/deepticket.git
cd deepticket
bash scripts/setup.sh
# Edit deepticket.yaml — set llm.api_key
bash scripts/start_all.sh
bash scripts/quickstart_demo.sh
```

Open http://127.0.0.1:8600 — default `admin` / `admin`. Paste the **Nginx log** sample from [docs/DEMO_PROMPT.md](docs/DEMO_PROMPT.md) (no Git repo required).

Full ROI demo (logs + code): [docs/quickstart-demo.md](docs/quickstart-demo.md).

---

## Why DeepTicket

Three common failure modes in incident triage and project Q&A:

1. **Chat-only / RAG-only** — Retrieves doc chunks but struggles with call chains, live logs, and runtime config; answers sound plausible but are hard to verify.  
2. **Traditional ticket AI** — Good at summaries and routing, rarely reads **real Git repos** or wires into internal log/config systems.  
3. **Raw OpenHands** — Powerful Agent runtime, but no Ingress/Webhook, routing, knowledge sync, or single-file ops config for ITSM loops.

DeepTicket is an **orchestration layer on OpenHands**: unified ingress, webhook outbound, Git knowledge base, and Skill/MCP extensions so the Agent grounds answers in **source + (optional) logs + (optional) config**.

> **Alpha honesty:** Log/config Skills ship as templates—you wire your APIs for full “three-source” verification. Git repos alone unlock code-level triage and Q&A.

---

## Comparison

| Capability | Pure RAG | Traditional ticket AI | **DeepTicket** |
|------------|:--------:|:-----------------------:|:--------------:|
| Read real Git / call chains | Stale chunks | Usually no | ✅ Read-only clone + Agent |
| Production logs | Manual ingest | Limited | ✅ log-query Skill / MCP (you configure) |
| Config center | Weak | Limited | ✅ config-query Skill / MCP (you configure) |
| Auto-trigger from alerts/tickets | ❌ | Partial | ✅ Ingress + async queue |
| Write back to ITSM | ❌ | Partial | ✅ Webhook outbound |
| Engineer multi-turn chat | Chat | Weak | ✅ Web workbench + SSE + analysis confidence |
| Out-of-the-box | Medium | Higher (SaaS) | ⚠️ yaml + LLM + integration (alpha) |

---

## Who uses it

| Scenario | Status |
|----------|--------|
| Author’s team internal pilot | 🟢 Ticket triage, project Q&A, Ingress integration tests |
| Public production stories | 🟡 None yet — share yours in [Issues](https://github.com/shanananana/deepticket/issues) (anonymous OK) |

---

## Architecture

<p align="center">
  <img src="docs/assets/architecture.svg" alt="DeepTicket architecture" width="720">
</p>

<p align="center"><sub>Users and upstream systems only hit <strong>8600</strong>; bind Agent Server <strong>8100</strong> to <code>127.0.0.1</code> in production</sub></p>

---

## Quick Start

See [5-minute quick start](#5-minute-quick-start) above. Common commands:

| Command | Purpose |
|---------|---------|
| `bash scripts/start_all.sh` | Daily startup |
| `bash scripts/quickstart_demo.sh` | Onboarding hints / optional ROI logs |
| `bash scripts/status.sh` | Health & queue check |
| `bash scripts/verify.sh` | Offline/online self-check |

Use **8600** in the browser only; **8100** is internal—bind to `127.0.0.1` in production.

---

## Configuration

Everything lives in **`deepticket.yaml`** (copy from `deepticket.example.yaml`; gitignored). Main sections:

| Section | Purpose |
|---------|---------|
| `llm` | Model and API key |
| `knowledge.repos` | Read-only Git repos |
| `ingress` | External tickets/alerts in, Webhook out |
| `storage` | Local or Redis |
| `web` | Workbench SSE heartbeat interval (`sse_heartbeat_seconds`) |
| `extensions` / `mcp` | Skills and MCP |

Wire logs/config via `log-query` / `config-query` Skill templates or MCP. See **`deepticket.example.yaml`** for field comments.

---

## Usage

**Web workbench** — Log in → new chat → describe the issue or paste logs → sync knowledge when needed → iterate. Enable **record mode** in settings to keep Agent steps expanded for demos. **Confidence** badges appear on analysis runs with verification steps (hidden for casual chat). Set **`web.sse_heartbeat_seconds`** in `deepticket.yaml` when deploying behind idle-timeout proxies.

**Automation** — Push events from monitoring/ITSM; DeepTicket analyzes asynchronously and callbacks via Webhook or store-only. Usually yaml only, no core code changes. Local test: `bash scripts/test_ingress_e2e.sh`.

---

## Development

```bash
pip install -e ".[dev]"
pytest -q
bash scripts/verify.sh --online
```

**Requirements:** macOS / Linux · Python 3.11+ · OpenAI-compatible LLM · Redis optional

---

## FAQ

<details>
<summary><strong>How is DeepTicket related to OpenHands?</strong></summary>
<p>OpenHands runs the agent (files, terminal, MCP). DeepTicket adds multi-user workbench, Git knowledge sync, Ingress tickets, Webhook outbound, and routing for SRE/on-call workflows.</p>
</details>

<details>
<summary><strong>How is this different from RAG or Spring AI agents like ad_agent?</strong></summary>
<p>RAG retrieves doc chunks; vertical agents like <a href="https://github.com/shanananana/ad_agent">ad_agent</a> focus on one business domain. DeepTicket targets <strong>Git + logs + config + ITSM loops</strong> for verifiable incident triage.</p>
</details>

<details>
<summary><strong>Can I integrate Jira or monitoring alerts?</strong></summary>
<p>Yes — HTTP POST to Ingress with API key; results via Webhook. See <code>deepticket.example.yaml</code> and <code>bash scripts/test_ingress_e2e.sh</code>.</p>
</details>

---

## Contributing

Stars, issues, and PRs welcome. First time? Read **[CONTRIBUTING.md](CONTRIBUTING.md)** and look for **`good first issue`**.

---

<p align="center">⭐ If this project helps you, please consider giving it a <a href="https://github.com/shanananana/deepticket">Star</a>!</p>

---

## License

[MIT](LICENSE)
