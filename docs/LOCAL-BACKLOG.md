# DeepTicket 本地待办 / 新方向清单

> **用途：** 本地备忘，供后续逐项确认是否做、何时做、是否进 CHANGELOG。  
> **维护：** 你确认后把条目移到 `CHANGELOG.md` / 正式 Roadmap，或删掉不做的项。  
> **最后更新：** 2026-08-21（性能优化落地 + 下一批四项待办规格）

---

## 图例

| 标记 | 含义 |
|------|------|
| ✅ | 已实现（本地），等你确认是否 commit / 发布 |
| 🟡 | 进行中或半成品 |
| ⬜ | 候选，尚未动手 |
| 🔵 | 传播 / 文档类 |
| ⚙️ | 工程 / 运维类 |
| 🎨 | 体验 / UI |
| 🚀 | 产品亮点 |

---

## 一、已实现 · 待你确认发布

### ✅ Docker 一键启动（⚙️ 🚀）

- **内容：** `Dockerfile`、`docker-compose.yml`（Redis + DeepTicket）、`deepticket.docker.yaml`、`.env.docker.example`、`scripts/docker/entrypoint.sh`、`docs/docker.md`；README 快速开始已含 Docker 入口；GHCR `ghcr.io/shanananana/deepticket:v0.3.0`。
- **用法：** `cp .env.docker.example .env` → 可选填 `LLM_API_KEY` → `docker compose up -d --build`（或 `docker-compose.image.yml` 拉镜像）→ http://127.0.0.1:8600；LLM 也可在 Web **LLM 配置** 填写。
- **状态：** 已 **v0.3.0** 发布（2026-08-15）。
- **待你决定：**
  - [x] commit + push + 打 tag → **v0.3.0** 已完成
  - [ ] Compose 默认端口是否保持 `127.0.0.1:8600`（仅本机）还是改为 `0.0.0.0` 方便内网同事访问？
  - [x] Release 页 Docker Quick Start → 见 README / `docs/docker.md`

### ✅ 工作台 UI（Sleek 设计 token）（🎨）

- v0.2.3 后已 push：去 Google Fonts、项目配置页去脏阴影、favicon、`style.css?v=30`。
- **待你决定：**
  - [ ] 是否再录一版 GIF 替换 README Demo（新 UI）？
  - [ ] 深色模式是否需要（当前未做）？

---

## 二、传播与文档（🔵）

### ⬜ 掘金 / 知乎 / InfoQ 发文

- 素材已有：`docs/promotion/`（HTML 正文、掘金 draft、封面 SVG v1–v4）。
- **待你决定：**
  - [ ] 先发掘金还是知乎？
  - [ ] 封面用哪版（v1–v4）？
  - [ ] 文末是否强调 Docker 一键启动作为新卖点？

### ⬜ GitHub 仓库完善

- About 中文简介已改。
- **候选：**
  - [ ] Topics：`sre` `aiops` `openhands` `mcp` `fastapi` `docker` …
  - [ ] Release 说明与 CHANGELOG 中英同步检查
  - [ ] Social preview 图（og:image）— 可用 `docs/assets/banner.svg` 或新做 1280×640

### ⬜ 排障报告导出 Markdown（🚀 🎨）

- 对话结束后一键导出：问题摘要、Thinking 步骤、置信度、引用日志/配置片段。
- **价值：** 值班交接、工单附件、内部分享；比截图可检索。
- **复杂度：** 中（前端按钮 + 后端聚合已有 chat history）

---

## 三、产品亮点 · 新方向（🚀）

### ⬜ Helm Chart / K8s 部署清单（⚙️）

- Docker 之上再包一层：Deployment + Service + Ingress + Redis（或外置 Redis）。
- **适合：** 大厂内网已有 K8s 的团队；与 Docker 文档并列。

### ⬜ 开箱 Demo 栈（ad_agent 一键联动）（🚀）

- Compose profile：`deepticket` + 可选 `ad_agent` 仓库挂载 + 预置 ROI demo 项目配置。
- **价值：** Star 后 5 分钟看到「像真排障」的完整链路，降低冷启动门槛。

### ⬜ 企业 IM Ingress（钉钉 / 飞书 / 企业微信 / Slack）（🚀）

- 告警或 @机器人 → 转 Ingress → 分析结果回频道或卡片。
- **注意：** 各平台 webhook 鉴权、消息格式差异大；可先做一个平台做 MVP。

### ⬜ Skill / MCP 连接器目录页（🚀）

- Admin 里展示「可一键启用的内网 MCP 模板」（日志、配置、CMDB、ITSM…），附 yaml 片段复制。
- **价值：** 降低多项目配置成本；突出「接基建」定位。

### ⬜ Runbook 模式（🚀）

- 从一次成功排障对话生成可复用 Runbook（步骤 + 检查命令 + 预期输出），下次同类告警半自动执行。
- **与 ad_agent 垂类 Demo 可形成「通用层 + 垂类层」故事。

### ⬜ 多模型路由 / 降级（🚀 ⚙️）

- 视觉任务走 vision 模型；纯文本走便宜模型；主模型失败自动 fallback。
- **关联：** v0.2.2 已修「不支持视觉却秒结束」；可产品化为配置项 + UI 提示。

### ⬜ SSO（LDAP / OAuth2 / 公司统一登录）（⚙️）

- 内网试点常见诉求；当前 admin 固定账号适合 Demo，不适合生产。

### ⬜ 用户级 · 跨会话向量记忆（Context / RAG on History）（🚀 ⚙️）

- **含义（我的理解）：** 按 **用户 uid**（可选再按 **project_id** 隔离）把历史对话中的有价值片段向量化；新建/继续对话时，用当前问题 **检索相关旧会话**，把 Top-K 摘要或原文片段 **注入 Agent 上下文**，而不是只靠「当前 chat 的 Redis history + Git 源码」。
- **与现状区别：**
  - 现在：单会话 history 在 Redis；跨会话互不相见。
  - Git 知识库：读 **代码/配置**，不是读「你上周怎么排障的」。
  - 本项：** episodic memory** — 「你上次 ROI 归因怎么查的」「某服务 502 的结论」可被召回。
- **候选范围（待你拍板）：**
  - [ ] 索引对象：user/assistant 消息？仅 assistant 结论 + Thinking 关键步骤？Ingress 工单结论？
  - [ ] 隔离：仅同 project？还是用户跨 project 可搜（内网 pilot 常见「同一人看多条线」）？
  - [ ] 存储：Redis + 外挂向量库（Qdrant / pgvector / Redis Stack）vs 轻量本地 embedding 文件。
  - [ ] 注入方式：`system_message_suffix` / 首条 hidden context / Skill 式「memory-query」。
  - [ ] 隐私：仅本人可见；管理员不可默认读全文（自托管合规）。
- **复杂度：** 中高（embedding 管线 + 增量索引 + 检索质量 + token 预算）。
- **价值：** 长周期 on-call、重复类告警、新人接手旧对话 — 显著减「从头讲一遍」。

### ⬜ 平台级 · Dream（离线巩固 / 后台「做梦」）（🚀 ⚙️）

- **含义（我的理解）：** **DeepTicket 实例级** 在低负载或定时任务里跑的 **后台巩固**，不占用用户当前对话的 Agent 配额；类似「平台睡着时整理白天碎片」— 不是用户前台聊天功能，而是 **运维/编排层自己的 maintenance + 智能批处理**。
- **候选能力（可分期，不必一次全做）：**
  - [ ] **Dream.Index** — 知识库 Git sync 后异步 chunk + embed（补全「代码向量索引」，与用户会话向量分开）。
  - [ ] **Dream.Consolidate** — 批量扫描近期已结束对话 / Ingress 工单，生成 **项目级摘要**（「本周高频根因」「未闭环假设」）供管理员或下次检索。
  - [ ] **Dream.Replay** — 对失败/低置信度 run 离线重放或规则校验（可选，耗 LLM）。
  - [ ] **Dream.Schedule** — cron / 队列 worker（可复用 ingress queue 模式）；Web 管理页看上次 Dream 运行状态。
- **与用户级向量的边界：**
  - **用户级** = 实时检索 **「我的历史」** 补当前 prompt。
  - **平台 Dream** = **实例级** 定时写索引/摘要/缓存，全员受益或仅管理员可见。
- **复杂度：** 高（调度、幂等、存储、与 OpenHands 解耦）。
- **价值：** 从「每次从零读 repo」进化到「平台越用越厚」；对内网自托管故事好讲（数据不出域）。

---

## 四、体验优化（🎨）

### ⬜ 工作台移动端 / 窄屏适配

- 侧栏、Thinking 面板、输入框在小屏下的折叠策略。

### ⬜ 截图上传增强

- 不支持 vision 的模型：上传前检测并提示，或走 OCR 预处理（本地 Tesseract / 云端 OCR）。
- 多图上传、图片预览放大。

### ⬜ 项目配置页

- 继续统一 Sleek 风格；大表单分步向导 vs 当前分项保存。
- Repos / MCP 测试连接按钮（保存前 ping 一下）。

### ⬜ 聊天列表与搜索

- 按项目、关键词、时间筛选历史对话；置顶常用对话。

### ⬜ 置信度与 Thinking 的可解释性

- 点击置信度徽章展开「因哪些步骤加分/减分」；步骤可折叠分组（读代码 / 查日志 / 写结论）。

### ⬜ 停止 / 重试 / 续跑 UX

- Agent 失败后「用同上下文重试」；停止后保留 partial 步骤。

---

## 五、工程与质量（⚙️）

### ⬜ Docker 相关后续

- [ ] `docker compose up` 端到端冒烟（health + 发一条 demo 消息）— 本地 build 已通过，完整 up 待测。
- [ ] 多架构镜像（`linux/amd64` + `arm64`）— Mac 开发 vs  Linux 服务器。
- [ ] 开发用 compose override：挂载源码 hot reload，避免每次 rebuild。

### ⬜ CI

- GitHub Actions：`pytest` + Docker build（不 push）+ 可选 lint。
- Release 时自动 attach `deepticket.example.yaml`、Docker 说明链接。

### ⬜ E2E 测试

- Playwright：登录 → 新建对话 → SSE 收到 assistant（mock LLM 或录制 fixture）。

### ⬜ 可观测性增强

- 已有 `/api/metrics`、Token 消耗页。
- **候选：** Prometheus scrape 格式；Grafana dashboard json；Webhook 失败重试队列可视化。

### ⬜ 安全加固清单（内网试点前）

- Session / Ingress API Key 轮换文档；CORS 生产配置说明；上传文件大小与类型限制审计；依赖漏洞扫描（pip-audit）。

### ⬜ 性能

- v0.2.3 已优化 Redis 聊天读写与 `/status` 轮询。
- **候选：** 大 history 分页；SSE 断连重连策略文档化；Redis pipeline 批量读。

---

## 六、版本与发布节奏（备忘）

| 版本 | 建议内容 | 状态 |
|------|----------|------|
| v0.3.0 | Docker 一键启动 + Web LLM 配置 + GHCR | ✅ 已发布 |
| v0.3.1 | 排障报告导出 或 IM Ingress MVP 或 Demo GIF 更新 | ⬜ 待选 |
| v0.4.0 | K8s/Helm 或 SSO 其一 + 破坏性配置变更时再 bump minor | ⬜ |
| v0.5.0+ | 用户级跨会话向量记忆 **或** 平台 Dream.Index MVP（二选一先行） | ⬜ 远期 |

---

## 七、明确不做 / 低优先级（除非你改主意）

- **做成 SaaS 多租户云平台** — 与「业务组自托管薄编排层」定位冲突。
- **自研替代 OpenHands** — 维护成本过高，继续跟 OpenHands 版本对齐（当前 1.39.1）。
- **内置日志/监控存储** — 坚持接现有 ELK/Loki/MCP，不重复造轮子。
- **推广目录进主仓库默认 clone** — `docs/promotion/`、`node_modules` 等保持本地或 .gitignore，避免污染 release 包。

---

## 九、下一批待做（详细规格 · 2026-08-21）

> 以下四项已写入待办，**尚未实现**；实现时需按规格验收。

### 🟡 用户可见 Token 用量页（🎨 🚀）

- **现状：** 仅管理员侧栏内嵌「Token 消耗」看板（`/api/admin/token-usage`），普通用户无法自查。
- **目标：**
  - 新增独立页面 `usage.html` + `usage.js`（可参考 mikkelive `web/usage.html`）。
  - 新增用户 API：`GET /api/usage/summary`（当前 uid）、`GET /api/usage/runs?limit=20`（本人最近 run）。
  - 权限：仅返回**当前登录用户**数据；管理员仍走现有 admin API。
  - UI：累计 Prompt/Completion/Total、最近 20 次 run 表格；侧栏入口「我的用量」（非 admin 也可见）。
- **依赖：** `TokenUsageStore` / `chat_history.set_token_usage` 已有数据；需按 uid 过滤索引。
- **验收：** 普通用户登录可见本人用量；切换项目不影响 uid 维度统计。

### 🟡 结构化日志 + 容器健康检查（⚙️）

- **现状：** `basicConfig` 仅 stdout；`docker-compose.yml` 中 deepticket 服务无 healthcheck。
- **目标：**
  - 移植/改写 mikkelive `core/logging_config.py`：`LOGPATH` 环境变量、RotatingFileHandler（50MB×5）、按 logger 级别。
  - `create_app` 启动时调用 `configure_logging()`；保留控制台 handler 便于 `docker logs`。
  - Compose：`healthcheck` 调 `GET /api/health`，`interval 30s`，`retries 3`；`depends_on: redis: condition: service_healthy`。
  - 文档：`docs/docker.md` 补充 `LOGPATH`、健康检查说明。
- **验收：** 容器 `healthy` 后 Web 可访问；日志文件轮转正常。

### 🟡 Ingress / 工单 Outbound 格式化（🚀 ⚙️）

- **现状：** Webhook 出站为 Agent 裸 `reply`；置信度仅在 SSE/聊天 UI 展示。
- **目标：**
  - 新增 `layers/output/outbound_formatter.py`（或按 route_type 注册）：在 **ingress 进入分析前** 注入 `prompt_suffix`（已有 routing），在 **出站前** 格式化 `reply`。
  - 默认模板（可配置）：纯文本块 — 【结论】【关键证据】【建议动作】；可选附加【置信度】块（score/level/reasons）。
  - 参考 mikkelive `live110_formatter.py`，但保持 **通用**（不绑 Live110 域名）；`route.outbound.format: structured | raw`。
  - 工单 ingress **进入**时：若 route 配置了 `prompt_suffix`，确保 classifier/adapter 已写入 ticket metadata（现有逻辑核对并补测试）。
- **验收：** webhook payload 的 `reply` 为结构化纯文本；`test_ingress_webhook` 断言格式字段。

### 🟡 排障报告导出 Markdown（🚀 🎨）

- **现状：** `docs/LOCAL-BACKLOG` 候选；聊天历史 + Thinking + 置信度已在 Redis，无导出。
- **目标：**
  - 后端：`GET /api/chats/{id}/export.md` 或 `POST /api/chats/{id}/export` 返回 `text/markdown`。
  - 内容：标题、项目、时间线、用户问题、Thinking 步骤列表、assistant 结论、置信度与 reasons、token 用量（若有）。
  - 前端：assistant 消息 toolbar 增加「导出 Markdown」；下载 `{chat_title}-{date}.md`。
  - 可选：Ingress 完成 job 同样导出（`/api/ingress/jobs/{id}/export.md`）。
- **验收：** 导出文件可在 VS Code 预览；含真实 activities 与 confidence JSON 转可读列表。

---

## 十、已完成的性能/架构优化（2026-08-21 · 本地）

### ✅ Quick Wins

- `chat_history.append_message` 不再全量 `get_thread` 读回。
- `apply_project_runtime` 去掉每条聊天 `publish_skills`；改为项目首次运行时 + Admin 保存配置时发布。
- `pollChatForReply`：/status 轮询 + 指数退避；发送前 baseline 改用 `/status` message_count。

### ✅ 中期架构

- 拆分 `IngressRunner`（`ingress_runner.py`）、`ChatOrchestrator`（`chat_orchestrator.py`）。
- Redis ZSET 索引：`json_index.py` 用于 token runs、ingress jobs、conversation/ticket 计数。
- `openhands_engine`：`_load_agent_settings_cached`、HTTP poll 复用 client。
- SSE：`streaming.py` idle activity 心跳「仍在分析…」。
- 前端：`app-shared.js`、`admin-token.js`、`admin-llm.js`、`admin-projects.js`；`app.js` 瘦身。

---

## 八、你的确认区（可直接在文件里打勾 / 写备注）

```
优先级（你填）：P0 ______  P1 ______  P2 ______

下一版必做（最多 2 项）：
1. 
2. 

暂缓 / 不做：
- 

其他想法：
- 
```
