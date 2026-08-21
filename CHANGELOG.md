# 更新日志

本项目的所有重要变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

---

## [0.3.3] - 2026-08-21

### Added

- **用户可见 Token 用量**：`/usage` 页面、`GET /api/usage/summary`、`GET /api/usage/runs`；侧栏「我的用量」；会话列表与标题区展示 token
- **续聊上下文同步**：从 Redis 读取历史，在 OpenHands 与 Redis 不一致时注入 `<conversation_history>` 并重建会话（`conversation_history.py`）
- **开发自检**：`scripts/verify_continue_chat.py` 最小 token 连续对话验证

### Changed

- **默认存储后端改为 Redis**（`schema.py`、`env_loader.py`、`start_all.sh` / `start_server.sh`）；本地 `./data` 需显式 `STORAGE_BACKEND=local`
- **README** 产品介绍结构重写（中英文对齐）

### Fixed

- **老对话丢上下文**：修复 OpenHands `events/search` 与 `llm_message` 解析；避免 `kind=MessageEvent` 空会话 500 污染 HTTP 连接
- **SSE idle 文案**「仍在分析…」误入 Thinking 步骤（`streaming.py`、`app.js`）
- **Admin 面板叠层**：`hideAdminPanels` 仅隐藏传入 DOM 导致多面板同时展开（`app-shared.js`）
- **docker-compose**：Redis 端口绑定 `127.0.0.1:6379:6379`

---

## [0.3.2] - 2026-08-21

### Changed

- **服务层拆分**：Ingress 逻辑迁至 `ingress_runner.py`，聊天/工单编排迁至 `chat_orchestrator.py`；`DeepTicketService` 只做装配与委托
- **Skill 发布策略**：不再在每条聊天前 `publish_skills`；改为项目首次运行时缓存发布，Admin 保存项目配置（知识库 / MCP / extensions）时自动重载
- **SSE 长静默**：Agent 长时间无输出时注入 idle activity「仍在分析…」，降低网关断连概率（替代纯 ping 等待体验）
- **Admin 前端模块化**：工作台脚本拆为 `app-shared.js`、`admin-token.js`、`admin-llm.js`、`admin-projects.js`；`app.js` 聚焦聊天主流程

### 优化

- **聊天 Redis 读写**：`append_message` 不再全量 `get_thread` 读回；发消息 API 用 `get_thread_summary` 校验会话
- **前端轮询**：断连/后台恢复改用 `/status` + 指数退避；发送前 baseline 用 `message_count`，成功时仅一次全量拉历史
- **Redis 索引**：新增 `json_index.py`，Token run、Ingress job、conversation/ticket 计数用 ZSET 索引，避免 `SCAN` 全表
- **OpenHands 引擎**：按 MCP/agents.md/LLM 缓存 `agent_settings`；HTTP 活动轮询复用 `httpx` client

### Fixed

- Ingress 测试：`ChatOrchestrator._run_stream` mock 路径；webhook E2E 强制 local 存储，避免无 Redis 时失败
- `test_token_usage`：`chat_usage` 命名空间与 key 格式与生产一致

---

## [0.3.1] - 2026-08-16

### Added

- **看板娘品牌图标**：Web 侧栏、登录页、AI 聊天头像与 favicon（`mascot-icon*.png`）
- **标准 agents.md 默认模板**：`deepticket/config/agents_defaults.py`；yaml 兜底与项目配置「DeepTicket 标准（推荐）」

### Changed

- **Docker LLM 配置持久化**：`DEEPTICKET_CONFIG` 指向 data 卷内 `deepticket.yaml`（`docker-compose.yml` / `docker-compose.image.yml`）
- **公开 Git 仓库**：无 token 时可匿名 clone（`git_source.py`）
- README 介绍结构重写（简介 / 特性 / 亮点 / 对比表 / 文档索引）

---

### Added

- **Docker 一键启动**：`Dockerfile`、`docker-compose.yml`、`deepticket.docker.yaml`；单容器内 Web（8600）+ Agent Server + Compose Redis
- **Web LLM 配置**：无 API Key 可启动；管理员侧栏填写后写入 yaml 并热更新，无需重启
- **GHCR 发布**：打 `v*` tag 时 CI 自动 build/push `ghcr.io/shanananana/deepticket`；`docker-compose.image.yml` 支持拉预构建镜像
- **文档**： [docs/docker.md](docs/docker.md)

### Changed

- Docker / 本机启动不再强制预先配置 `llm.api_key`

---

## [0.2.3] - 2026-08-14

### 优化

- 聊天存储与轮询性能（Redis 读写更轻）
- 等待 Agent 回复时减少重复拉取历史消息

---

## [0.2.2] - 2026-08-14

### Added

- **工作台截图上传**：粘贴 / 点击上传 / 拖入输入框，本地保存后随对话发送，无需再填图片 URL

### Fixed

- **识图请求卡在「开始分析」**：Agent 秒结束（例如当前模型不支持视觉）时，等待逻辑未识别终态，界面空转；取消时 `asyncio.suppress` 崩溃
- **本地截图 Agent 拉不到**：上传图改为 data URL 内联，避免 `127.0.0.1` 被 OpenHands SSRF 拦截

---

## [0.2.1] - 2026-08-12

### Fixed

- **工作台聊天持久化**：SSE 与 Agent 执行解耦；用户关页或网络断连后，Agent 仍在后台完成并将 assistant 回复写入聊天历史
- **重新打开对话**：若上次 Agent 仍在运行（`agent_run_status: running`），工作台自动等待并展示完整回复；断连后也会轮询恢复
- **停止按钮**：仍通过 `/api/agent/cancel` 主动终止（与关页行为区分）；cancel 请求支持 `chat_id`

### Added

- **后台 Chat Run**：`ChatRunManager` 管理 Agent 任务与 SSE 订阅；聊天 API 返回 `agent_run_status`
- **测试**：`tests/test_chat_runs.py`（断连后仍持久化 assistant 消息）

---

## [0.2.0] - 2026-08-09

### Added

- **多团队 / 多项目**：一套服务接多个业务线；侧栏切换项目，每项目独立知识库、MCP、agents.md；Redis 存储运行时配置，`deepticket.yaml` 作兜底
- **管理端项目配置**：侧栏独立入口（与 Token 消耗并列）；新建项目、成员管理、分项保存基本信息 / Repos / MCP / agents.md（支持载入 yaml 默认）
- **Admin API**：`GET/PUT/PATCH /api/admin/projects/{id}` 及 `/knowledge`、`/mcp`、`/extensions`、`/members` 子路径

---

## [0.1.2] - 2026-08-06

### Added

- **分析置信度**：基于 Agent 步骤（读代码/日志/配置等）与回复内容估算 0–100 分，流式 `event: confidence` 推送并在工作台展示徽章；**纯聊天默认隐藏**，工单/Ingress 或有验证步骤时展示
- **SSE 心跳**：可配置 `web.sse_heartbeat_seconds`（默认 15s，`0` 关闭），周期性 `event: ping`，防止 Nginx/网关 idle 断连
- **测试**：`test_confidence`、`test_sse_streaming` 等，共 79 项用例

### Changed

- **思考过程 UI**：头部摘要 tab 支持横向滑动，步骤列表支持纵向滚动与增量渲染；完成后显示步数摘要

---

## [0.1.1] - 2026-08-04

### Added

- **Admin Token 消耗页**（仅管理员）：从 OpenHands Agent Server 读取精确 `prompt` / `completion` / `reasoning` token，关联**用户、对话、模型**；支持按对话累计与单次 Agent 运行明细
- **`GET /api/admin/token-usage`**：Token 用量查询 API
- **进程内可观测性**：Agent 运行次数/耗时、Webhook 成功失败、Ingress 队列积压告警（`/api/metrics`，管理员）
- **工作台增强**：对话全文搜索、截图 URL 输入、Agent 步骤持久化与回放、流式断线重连、服务端取消任务
- **Skill 脚本占位**：`log-query`、`config-query` 查询脚本模板
- **测试**：`test_stream_reply`、`test_token_usage` 等，共 72 项用例

### Changed

- 移除原「运维看板」（Ingress 路由/任务/系统信息等），收敛为 Token 消耗单一视图
- `/api/health` 公开化精简字段；知识库列表改由 `/api/knowledge/repos` 获取
- 「同步知识库 / 重载 Skills」对非管理员隐藏
- Ingress 任务失败自动标记；Agent WebSocket 不可用时降级 HTTP 轮询

### Fixed

- OpenHands 引擎 `ensure_ready` 语法与活动轮询日志问题
- 图片 URL、存储与 API 相关测试稳定性

---

## [0.1.0] - 2026-08-02

首个 **Alpha** 公开发布。

### Added

- **DeepTicket 编排层**：在 OpenHands Agent Server 之上统一 Ingress 进、Webhook 出、Git 知识库、Skill/MCP 扩展
- **统一配置** `deepticket.yaml`：LLM、Git 仓库、Ingress 路由、存储、Skill/MCP 单文件管理
- **OpenHands 引擎对接**：Conversation API + 事件 WebSocket；流式 SSE 输出至 Web 工作台
- **Ingress**：HTTP 事件接入（监控/工单/Jira 等）、异步队列、API Key 鉴权、路由分类（incident / ticket / consultation / default）
- **Outbound**：Webhook 回写 ITSM 或 `store_only` 仅存库
- **Web 工作台**：多用户登录、对话线程、多轮追问、实时 Markdown、Thinking/Activity 步骤展示
- **Git 知识库**：只读 clone/sync，`workspace/knowledge` + `workspace/project` 双目录
- **Skills**：`log-query`、`config-query`、`repo-workspace` 模板（日志/配置需按环境对接）
- **存储**：本地 JSON 或 Redis 后端
- **一键启动** `bash scripts/start_all.sh`：Web `:8600` + Agent Server `:8100`（本机内部）
- **双语 README**、架构图、ad_agent ROI 演示脚本与预生成日志
- **开发工具**：`pytest`、`scripts/verify.sh`、`scripts/test_ingress_e2e.sh`

### Changed

- 服务端部署 OpenHands 运行时，浏览器即可使用，无需每人本地装 Agent
- 工作台 UI 浅色主题、录屏模式、工单模板快捷插入

---

## 链接

- [English Changelog](CHANGELOG.en.md)
- [GitHub Releases](https://github.com/shanananana/deepticket/releases)
- [Unreleased 对比 v0.3.3](https://github.com/shanananana/deepticket/compare/v0.3.3...HEAD)

[Unreleased]: https://github.com/shanananana/deepticket/compare/v0.3.3...HEAD
[0.3.3]: https://github.com/shanananana/deepticket/releases/tag/v0.3.3
[0.3.2]: https://github.com/shanananana/deepticket/releases/tag/v0.3.2
[0.3.1]: https://github.com/shanananana/deepticket/releases/tag/v0.3.1
[0.3.0]: https://github.com/shanananana/deepticket/releases/tag/v0.3.0
[0.2.3]: https://github.com/shanananana/deepticket/releases/tag/v0.2.3
[0.2.2]: https://github.com/shanananana/deepticket/releases/tag/v0.2.2
[0.2.1]: https://github.com/shanananana/deepticket/releases/tag/v0.2.1
[0.2.0]: https://github.com/shanananana/deepticket/releases/tag/v0.2.0
[0.1.2]: https://github.com/shanananana/deepticket/releases/tag/v0.1.2
[0.1.1]: https://github.com/shanananana/deepticket/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/shanananana/deepticket/releases/tag/v0.1.0
