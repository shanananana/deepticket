# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.2]: https://github.com/shanananana/deepticket/releases/tag/v0.1.2
[0.1.1]: https://github.com/shanananana/deepticket/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/shanananana/deepticket/releases/tag/v0.1.0
