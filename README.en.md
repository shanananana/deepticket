# DeepTicket

<p align="right"><a href="README.md">中文</a> | <strong>English</strong></p>

**An intelligent Agent platform for production incidents and project Q&A** (OpenHands · LLM · SRE / AIOps · ticket analysis · root cause · MCP · Webhook). Built on the [OpenHands](https://github.com/OpenHands/OpenHands) Agent Server, it orchestrates LLM reasoning, real source code, logs, and configuration lookups into a practical triage and Q&A pipeline.

- **External input (Ingress)** — Monitoring, Jira, internal ticketing, and other systems push events over HTTP (`POST /api/ingress/events`) without user login; analysis starts automatically.
- **External output (Outbound)** — After analysis, results are delivered via Webhook to your ITSM/ticketing stack, or stored for later lookup, closing the loop with upstream systems.
- **Human workbench** — Engineers and on-call staff can also ask follow-up questions in the Web UI, paste logs, and attach screenshots.

**Once code repos, log platforms, and config centers are connected**, the Agent cross-references **source code + production logs + runtime configuration** to **answer project questions with high precision** (implementation details, root causes, whether config is effective, API behavior, etc.)—not by guessing from the model alone.

---

## Core Features

### Accurate answers backed by real data

After configuring the three integrations below in `deepticket.yaml`, DeepTicket grounds every answer in real data:

| Integration | Configuration | What you can ask |
|-------------|---------------|------------------|
| **Code repo** | `knowledge.repos` (read-only Git sync) | Implementation, call chains, config definitions, API behavior |
| **Log platform** | `log-query` Skill or MCP | Stack traces, trace IDs, production ERROR/WARN |
| **Config center** | `config-query` Skill or MCP | Feature flags, env diffs, misconfiguration |

With all three in place—whether someone asks in the workbench or an external system pushes a ticket via Ingress—the Agent gives **precise, verifiable conclusions for that project**. It will not pretend to have verified data you have not connected (e.g. it will not invent production errors if logs are not wired).

### Full conversation in the workbench

Multi-session Web UI with streaming replies and Markdown rendering. Describe symptoms, paste logs, attach screenshot URLs (`image_urls`), and iterate until the scope is clear—ideal for complex incidents and “why does this API behave this way?” questions, not just fire-and-forget automation.

### Real source code, not hallucinated code

Configure Git repos under `knowledge.repos`; DeepTicket read-only clones and mounts them under `workspace/project/<repo-id>/`. The Agent reads actual files and directory structure instead of inventing implementation details.

### Deep integration: logs, config, and more

- **log-query Skill** — Connect your log platform (traceId, time range, ERROR level, etc.); template included, swap in your API.
- **config-query Skill** — Connect Apollo / CMDB / internal config centers; check flags, env diffs, recent changes.
- **MCP** — Attach more internal APIs, databases, and ops scripts; synced to Agent Server on startup.

The underlying Agent can read files, run commands, and call tools; DeepTicket adds knowledge sync, Skill publishing, routing, and the Web UI.

### Ingress: connect tickets and alerts

Receive events from monitoring, ITSM, Jira, or custom systems via the Ingress API. Route by source and keywords in `ingress.routes` without embedding DeepTicket into every upstream system.

### Outbound: write results back

After analysis, structured results (root cause, suggestions, conversation ID, etc.) are POSTed to your ticketing platform via Webhook, or stored only for manual review. Both ingress and outbound are configurable per route.

---

## Project Layout

```
deepticket/
├── deepticket.yaml               # Local config (gitignored)
├── deepticket.example.yaml       # Template (safe to commit)
├── scripts/
│   ├── setup.sh                  # Install deps, create deepticket.yaml
│   ├── start_all.sh              # Start Agent Server + Web
│   └── verify.sh                 # Offline/online checks
├── deepticket/
│   ├── service.py                # Orchestration: chat, tickets, ingress
│   ├── config/                   # Config loading
│   ├── skills/                   # Built-in Skills
│   ├── api/routers/              # HTTP API
│   ├── layers/                   # Input / output / engine / knowledge / storage
│   └── web/                      # Login + workbench UI
└── workspace/                    # Runtime: Git cache + Agent workspace (gitignored)
    ├── knowledge/<repo-id>       # Read-only clone
    └── project/<repo-id>         # Symlink to knowledge
```

---

## Ingress & Outbound

External integration uses two HTTP paths: **Ingress (in)** and **Outbound (out)**. The workbench uses a separate path (login + `/api/chat`) and does not go through ingress routing.

### In: Ingress events

Any upstream system POSTs the same JSON shape to `POST /api/ingress/events`:

| Field | Meaning |
|-------|---------|
| `source` | Source id, e.g. `jira`, `alertmanager`, `internal-ticket` |
| `external_id` | Ticket/alert id in the upstream system (for outbound correlation) |
| `title` / `body` | Title and body (symptoms, stack traces, alert summary) |
| `type` | Optional; if set, **skips** auto-classification and uses that route |
| `repo_ids` | Optional; Git repo ids from `knowledge.repos` |
| `image_urls` | Optional; http/https image URLs; also via `metadata.image_urls` / `metadata.images` |
| `logs` / `metadata` | Optional; extra logs and custom fields |

No API key required: configure `ingress.routes` and POST directly (restrict network access on private deployments).

**Route matching:**

1. **Explicit** — `"type": "incident"` in the request; must exist in `ingress.routes`.
2. **Rules** — Match `sources`, then `title_keywords` / `body_keywords`, then the route with `default: true`.

Each route can set `prompt_suffix`, `repo_ids`, and outbound behavior.

### Out: Outbound delivery

| method | Behavior |
|--------|----------|
| `store_only` | Store in DeepTicket; query via `GET /api/ingress/jobs/{job_id}` |
| `webhook` | POST to `outbound.url` (set directly in yaml) |

Webhook body includes `job_id`, `route_type`, `source`, `external_id`, `status`, `reply`, `conversation_id`, `error`, `metadata`. Your ticketing system maps `external_id` back to the original ticket.

### Do I need to fork DeepTicket?

| Scenario | Typical approach |
|----------|------------------|
| Upstream can HTTP POST your JSON | Configure `ingress` in `deepticket.yaml` only |
| Upstream is Alertmanager / Grafana native format | Small adapter script → Ingress JSON → POST |
| Downstream accepts JSON Webhook | Set `outbound.url` in yaml |
| Proprietary ticket API | Middleware receives Webhook, calls your API; or extend outbound handlers |
| Manual triage only | Skip Ingress; use the Web workbench |

Skills and MCP for logs/config usually need **config or Skill/MCP services only**, not core code changes.

---

## Quick Start

```bash
git clone https://github.com/shanananana/deepticket.git
cd deepticket
bash scripts/setup.sh          # Creates deepticket.yaml and Python venv
```

Edit **`deepticket.yaml`** (structure and secrets; gitignored—do not commit). Use **`deepticket.example.yaml`** placeholders as a guide.

```bash
bash scripts/start_all.sh
```

Open http://127.0.0.1:8600 — default account `admin` / `admin` (created on first start; **change in production**).

### Scripts

| Command | Purpose | When to run separately |
|---------|---------|------------------------|
| `bash scripts/setup.sh` | Copy example yaml, install deps | First time or new machine |
| `bash scripts/start_all.sh` | **One command**: Agent Server (8100) + Web (8600); may start Docker Redis | **Daily use** |
| `bash scripts/redis.sh up` | Start Redis in Docker | If using redis and not started by `start_all.sh` |
| `bash scripts/start_server.sh` | Agent Server only | Debugging Agent |

All ports, storage, LLM keys, etc. live in **`deepticket.yaml`**.

### Why two ports?

| Port | Process | Role | You need it? |
|------|---------|------|--------------|
| **8600** | DeepTicket Web | Login, workbench, Ingress API | **Yes** — browser only |
| **8100** | OpenHands Agent Server | Agent runs tools, reads code | **No** — internal HTTP |

`start_all.sh` starts both; users only open **8600**. Single-process merge is not supported in this version.

---

## Configuration (`deepticket.yaml`)

Everything is in one file (copy from `deepticket.example.yaml`; local file with secrets is gitignored).

| Section | Contents |
|---------|----------|
| `llm` | Model, API key, base URL |
| `web` / `engine` | Web port, Agent Server port, session key |
| `storage` | local / redis, TTL, Docker Redis |
| `knowledge.repos` | Git repos |
| `ingress` | Ingress routes (no api_key) |
| `mcp.servers` | MCP tools |
| `extensions` | Skills directories |

Example webhook in yaml:

```yaml
ingress:
  routes:
    - type: ticket
      match:
        sources: [jira, internal-ticket]
      outbound:
        method: webhook
        url: http://your-itsm/internal/hook
      repo_ids: [my-service]
```

### LLM (required)

```yaml
llm:
  api_key: sk-your-key-here
  model: openai/deepseek-v4-flash
  base_url: https://api.deepseek.com/v1
```

### Storage

```yaml
storage:
  backend: redis
  redis:
    url: redis://127.0.0.1:6379/0
    username: ""
    password: ""              # empty for local Docker Redis
    key_prefix: "deepticket:"
    ttl_seconds: 31536000
```

With password:

```yaml
  redis:
    url: redis://redis.internal:6379/0
    password: your-redis-password
```

| Location | Under redis backend |
|----------|---------------------|
| Redis | Accounts, tokens, **full chat history**, ingress jobs, ticket metadata |
| `./data/` | **Not used** (may exist but empty) |
| `./workspace/` | Agent workspace + Git cache (runtime; re-sync after restart) |

```bash
bash scripts/redis.sh keys
bash scripts/redis.sh ping
```

### Knowledge (read-only Git)

Supports **GitHub** and **GitLab** (gitlab.com, `*.gitlab.com`, custom domains via `url_template`):

```yaml
knowledge:
  repos:
    - id: my-service
      url: https://github.com/your-org/your-service.git
      key: ghp_your_github_token
      branch: main
```

Sync via UI “Sync knowledge” or on startup; Agent reads `workspace/project/<repo-id>/`.

### Ingress API

```bash
curl -X POST http://127.0.0.1:8600/api/ingress/events \
  -H "Content-Type: application/json" \
  -d '{"source":"jira","external_id":"T-001","title":"API 500","body":"...","image_urls":["https://example.com/screen.png"]}'

bash scripts/test_ingress_e2e.sh
```

---

## Usage

### Web workbench

1. Log in → new chat  
2. Describe the issue; paste logs  
3. “Sync knowledge” before code-heavy questions  
4. Streaming replies; thinking UI from real OpenHands events  

### Authenticated API

| Endpoint | Purpose |
|----------|---------|
| `POST /api/chat` | Continue chat (SSE); optional `image_urls` |
| `POST /api/ticket` | One-shot ticket analysis (SSE); optional `image_urls` |
| `POST /api/chats` | Create/manage chats |

Bearer token from login.

---

## Development

```bash
pip install -e ".[dev]"
ruff check deepticket tests
pytest -q
bash scripts/verify.sh
bash scripts/verify.sh --online
```

---

## Requirements

- macOS / Linux, Python 3.11+
- Docker (optional, for `scripts/redis.sh`)
- Any **OpenAI-compatible** LLM endpoint

---

<p align="center">⭐ If this project helps you, please consider giving it a <a href="https://github.com/shanananana/deepticket">Star</a>!</p>

---

## License

[MIT](LICENSE)
