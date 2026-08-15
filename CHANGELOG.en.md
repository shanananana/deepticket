# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.3.0] - 2026-08-15

### Added

- **Docker one-command start**: `Dockerfile`, `docker-compose.yml`, `deepticket.docker.yaml`; Web (8600) + Agent Server + Redis via Compose
- **Web LLM settings**: start without an API key; admins configure in the sidebar, persisted to yaml with hot reload
- **GHCR publish**: CI builds and pushes `ghcr.io/shanananana/deepticket` on `v*` tags; `docker-compose.image.yml` for prebuilt images
- **Docs**: [docs/docker.md](docs/docker.md)

### Changed

- Docker / local start no longer requires `llm.api_key` upfront

---

## [0.2.3] - 2026-08-14

### Improved

- Chat storage and polling performance (lighter Redis usage)
- Less redundant history fetching while waiting for agent replies

---

## [0.2.2] - 2026-08-14

### Added

- **Workbench screenshot upload**: paste, click, or drop images into the composer; files are stored locally and sent with the chat (no image URL required)

### Fixed

- **Chat stuck on “starting analysis”**: fast-finished agent turns (e.g. model has no vision) were not treated as complete, so the UI spun forever; cancel also crashed on `asyncio.suppress`
- **Local screenshots unreachable to the agent**: uploaded images are inlined as data URLs so OpenHands does not block `127.0.0.1` as SSRF

---

## [0.2.1] - 2026-08-12

### Fixed

- **Workbench chat persistence**: SSE decoupled from agent execution—closing the tab or losing the stream no longer drops in-progress replies; the agent finishes in the background and persists the assistant message
- **Reopen conversation**: if the agent is still running (`agent_run_status: running`), the workbench waits and shows the full reply; polling also recovers after disconnect
- **Stop button**: still cancels via `/api/agent/cancel` (distinct from closing the tab); cancel accepts `chat_id`

### Added

- **Background chat runs**: `ChatRunManager` runs agents independently of SSE subscribers; chat API exposes `agent_run_status`
- **Tests**: `tests/test_chat_runs.py` (assistant message persisted after subscriber disconnect)

---

## [0.2.0] - 2026-08-09

### Added

- **Multi-team / multi-project**: one instance for multiple teams; sidebar project switch; per-project knowledge base, MCP, and agents.md; Redis runtime config with yaml fallback
- **Admin project settings**: dedicated sidebar entry alongside Token usage; create projects, manage members, sectional save for meta / repos / MCP / agents.md (load yaml defaults per section)
- **Admin API**: `GET/PUT/PATCH /api/admin/projects/{id}` plus `/knowledge`, `/mcp`, `/extensions`, `/members`

---

## [0.1.2] - 2026-08-06

### Added

- **Analysis confidence**: heuristic score (0–100) from agent steps (code/log/config reads, etc.) and reply text; streamed via `event: confidence` with a workbench badge; **hidden for pure chat**, shown for tickets/Ingress or when verification steps exist
- **SSE heartbeat**: configurable `web.sse_heartbeat_seconds` (default 15s, `0` to disable) sends periodic `event: ping` to survive idle timeouts behind reverse proxies
- **Tests**: `test_confidence`, `test_sse_streaming`, etc. (79 cases total)

### Changed

- **Thinking panel UX**: horizontally scrollable summary tab, vertically scrollable step list, incremental step rendering, step-count summary when done

---

## [0.1.1] - 2026-08-04

### Added

- **Admin token usage panel** (admin only): precise OpenHands `prompt` / `completion` / `reasoning` tokens linked to **user, conversation, and model**; per-chat totals and per-run deltas
- **`GET /api/admin/token-usage`** API
- **In-process observability**: agent run counts/latency, webhook success/failure, ingress queue backlog alerts (`/api/metrics`, admin)
- **Workbench UX**: full-text chat search, screenshot URL input, persisted agent activities, stream reconnect, server-side cancel
- **Skill script stubs** for `log-query` and `config-query`
- **Tests**: `test_stream_reply`, `test_token_usage`, etc. (72 cases total)

### Changed

- Removed the old ops dashboard (ingress routes/jobs/system info) in favor of a focused token view
- Slimmed public `/api/health`; knowledge repos moved to `/api/knowledge/repos`
- Hide “sync knowledge / reload skills” from non-admins
- Ingress jobs marked failed on error; WebSocket falls back to HTTP polling when unavailable

### Fixed

- OpenHands engine `ensure_ready` syntax and activity polling logs
- Image URL, storage, and API test stability

---

## [0.1.0] - 2026-08-02

First public **Alpha** release.

### Added

- **DeepTicket orchestration layer** on OpenHands Agent Server: ingress, webhook outbound, Git knowledge base, Skill/MCP extensions
- **Unified config** `deepticket.yaml`: LLM, Git repos, ingress routes, storage, skills/MCP in one file
- **OpenHands engine**: Conversation API + event WebSocket; SSE streaming to the web workbench
- **Ingress**: HTTP events (monitoring/ITSM/Jira), async queue, API key auth, route types (incident / ticket / consultation / default)
- **Outbound**: ITSM webhook or `store_only`
- **Web workbench**: multi-user auth, chat threads, multi-turn Q&A, live Markdown, Thinking/Activity steps
- **Git knowledge base**: read-only clone/sync via `workspace/knowledge` and `workspace/project`
- **Skills**: `log-query`, `config-query`, `repo-workspace` templates (wire your log/config APIs)
- **Storage**: local JSON or Redis
- **One-command start** `bash scripts/start_all.sh`: Web `:8600` + Agent Server `:8100` (localhost)
- **Bilingual README**, architecture diagram, ad_agent ROI demo scripts and pre-generated logs
- **Dev tooling**: `pytest`, `scripts/verify.sh`, `scripts/test_ingress_e2e.sh`

### Changed

- Server-side OpenHands runtime so browsers suffice—no per-user local Agent setup
- Light workbench theme, recording mode, ticket template shortcuts

---

## Links

- [中文更新日志](CHANGELOG.md)
- [GitHub Releases](https://github.com/shanananana/deepticket/releases)
- [Unreleased vs v0.3.0](https://github.com/shanananana/deepticket/compare/v0.3.0...HEAD)

[Unreleased]: https://github.com/shanananana/deepticket/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/shanananana/deepticket/releases/tag/v0.3.0
[0.2.3]: https://github.com/shanananana/deepticket/releases/tag/v0.2.3
[0.2.2]: https://github.com/shanananana/deepticket/releases/tag/v0.2.2
[0.2.1]: https://github.com/shanananana/deepticket/releases/tag/v0.2.1
[0.2.0]: https://github.com/shanananana/deepticket/releases/tag/v0.2.0
[0.1.2]: https://github.com/shanananana/deepticket/releases/tag/v0.1.2
[0.1.1]: https://github.com/shanananana/deepticket/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/shanananana/deepticket/releases/tag/v0.1.0
