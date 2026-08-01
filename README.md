# DeepTicket

<p align="right"><strong>中文</strong> | <a href="README.en.md">English</a></p>

**面向线上故障与项目答疑的智能 Agent 平台。** 基于 [OpenHands](https://github.com/OpenHands/OpenHands) Agent Server 构建，把 LLM 推理、真实源码、日志与配置查询编排成一条可落地的排查与答疑流水线。

- **外部系统输入（Ingress）** — 监控、Jira、内部工单等通过 HTTP 推送事件（`POST /api/ingress/events`），无需人工登录，自动触发分析。
- **外部系统输出（Outbound）** — 分析完成后按路由 Webhook 回写工单/ITSM，或仅存库供查询，与上游系统闭环。
- **人机工作台** — 工程师和一线同学也可在 Web 里多轮追问、贴日志、带截图。

**接入代码仓库、日志中心与配置中心后**，Agent 可以交叉对照「源码 + 线上日志 + 运行时配置」作答，**非常精准地回答所有关于该项目的问题**（实现细节、故障根因、配置是否生效、接口行为等），而不是凭模型猜测。

---

## 核心特色

### 答得准：项目问题，有据可查

在 `deepticket.yaml` 中完成三类接入后，DeepTicket 会把回答建立在真实数据上：

| 接入项 | 配置方式 | 能回答什么 |
|--------|----------|------------|
| **代码仓库** | `knowledge.repos`（Git 只读同步） | 实现逻辑、调用链、配置定义、接口行为 |
| **日志中心** | `log-query` Skill 或 MCP | 报错堆栈、trace 链路、线上 ERROR/WARN |
| **配置中心** | `config-query` Skill 或 MCP | 开关/feature flag、环境差异、配置是否配错 |

三者齐备时，无论是值班同学在工作台提问，还是外部系统经 Ingress 推工单，Agent 都能**针对该项目**给出精准、可复核的结论；未接入的部分则不会假装已验证（例如未接日志时不会编造线上报错）。

### 问得全：人机协作工作台

Web 工作台支持多会话、流式回复与 Markdown 排版。可以描述现象、粘贴日志、附带截图 URL（`image_urls`），多轮追问直到缩小范围——适合复杂故障与「这个接口为什么这样」类答疑，而不只是「推一条等结果」。

### 看得真：基于真实源码，不是猜代码

在 `knowledge.repos` 配置 Git 仓库后，DeepTicket 只读拉取并挂载到 Agent 工作区（`workspace/project/<repo-id>/`）。分析直接读仓库里的文件与目录结构，而不是让模型凭空编造实现细节。

### 接得深：日志中心 + 配置中心 + 更多内部能力

- **log-query Skill** — 对接公司日志平台（按 traceId、时间范围查 ERROR 等）；内置模板，替换为你们 API 即可用。
- **config-query Skill** — 对接 Apollo / CMDB / 内部配置中心；查开关、环境差异、配置变更。
- **MCP** — 挂载更多内部 API、数据库、运维脚本；启动时自动同步到 Agent Server。

底层 Agent 具备读文件、执行命令、调用工具等完整能力；DeepTicket 在其上封装知识库同步、Skill 发布、路由分发与 Web UI。

### 进得去：对接内部工单与告警

通过 Ingress API 接收监控、ITSM、Jira 或自研系统推送的事件。在 `deepticket.yaml` 的 `ingress.routes` 里按来源、关键词配置路由规则，自动识别故障类型并触发分析，无需把 DeepTicket 嵌进每个上游系统。

### 出得去：结论回写内部系统

分析完成后，按事件类型将结构化结果（根因、建议、会话 ID 等）通过 Webhook 回调到你的工单平台；也可仅落库，供后续人工复核。进、出两端都可配置，适配不同团队的闭环流程。

---

## 项目结构

```
deepticket/
├── deepticket.yaml               # 本地统一配置（gitignore）
├── deepticket.example.yaml       # 配置模板（可提交）
├── scripts/
│   ├── setup.sh                  # 安装依赖、生成 deepticket.yaml
│   ├── start_all.sh              # 一键启动 Agent Server + Web
│   └── verify.sh                 # 离线/在线自检
├── deepticket/
│   ├── service.py                # 编排：聊天、工单、外部接入
│   ├── config/                   # 配置加载
│   ├── skills/                   # 内置 Skill（可提交）
│   ├── api/routers/              # HTTP API
│   ├── layers/                   # 输入 / 输出 / 引擎 / 知识 / 存储
│   └── web/                      # 登录页 + 工作台 UI
└── workspace/                    # 运行时：Git 缓存 + Agent 工作区（gitignore）
    ├── knowledge/<repo-id>       # 只读 clone
    └── project/<repo-id>         # 指向 knowledge 的 symlink
```

---

## 事件进出说明

DeepTicket 里和「外部系统对接」相关的，是两条 HTTP 通路：**Ingress（进）** 与 **Outbound（出）**。工作台对话走的是另一条路（登录 + `/api/chat`），不经过这套路由。

### 进：Ingress 事件（统一输入）

任意上游系统向 `POST /api/ingress/events` 推送 **同一份 JSON 结构**（`IngressEvent`）：

| 字段 | 含义 |
|------|------|
| `source` | 来源标识，如 `jira`、`alertmanager`、`internal-ticket` |
| `external_id` | 对方系统里的工单/告警 ID，用于回写时对账 |
| `title` / `body` | 标题与正文（现象、堆栈、告警摘要等） |
| `type` | 可选；填了则 **直接** 走该路由，跳过自动分类 |
| `repo_ids` | 可选；指定要分析的 Git 仓库 id（对应 `deepticket.yaml` 里 `knowledge.repos`） |
| `image_urls` | 可选；附件图片 URL 列表（http/https）；也可放在 `metadata.image_urls` / `metadata.images` |
| `logs` / `metadata` | 可选；附加日志与自定义字段 |

无需鉴权：配置好 `ingress.routes` 后，外部系统直接 `POST /api/ingress/events` 即可（内网部署请自行限制网络访问）。

**如何区分事件类型？** 两种方式，可混用：

1. **显式指定** — 请求里带 `"type": "incident"`，必须在 `deepticket.yaml` 的 `ingress.routes` 里有同名路由。
2. **规则匹配** — 不带 `type` 时，按 `ingress.routes` 里每条规则的 `match` 依次匹配：
   `sources`（来源）→ `title_keywords` / `body_keywords`（关键词）→ 最后命中 `default: true` 的默认路由。

每种路由类型（如 `incident`、`ticket`、`consultation`）可配置不同的 `prompt_suffix`、`repo_ids`、出口方式。

### 出：Outbound 结果（统一输出）

Agent 分析完成后，DeepTicket 构造 **OutboundPayload**，按该路由的 `outbound.method` 投递：

| method | 行为 |
|--------|------|
| `store_only` | 只写入 DeepTicket 存储；用 `GET /api/ingress/jobs/{job_id}` 查询 |
| `webhook` | `POST` 到 `outbound.url`（在 yaml 直接写回调地址） |

Webhook 请求体示例字段：`job_id`、`route_type`、`source`、`external_id`、`status`、`reply`（分析正文）、`conversation_id`、`error`、`metadata`。

你的工单系统收到后，用 `external_id` 把结论写回原工单即可。

### 需要二次开发吗？

| 场景 | 通常做法 |
|------|----------|
| 上游能 HTTP POST，且愿意转成上述 JSON | **不用改 DeepTicket**，配 `deepticket.yaml` 的 `ingress` 区块 |
| 上游是 Alertmanager / Grafana 等固定格式 | **写一层小适配器**（几十行脚本或 Zapier/自研网关），转成 Ingress JSON 再 POST |
| 回写地址能收 JSON Webhook | **不用改 DeepTicket**，在路由 `outbound.url` 直接写回调地址 |
| 工单 API 是专有协议（非简单 Webhook） | **中间服务**接收 DeepTicket 的 Webhook，再调你们工单 API；或 fork 扩展 `outbound` 处理器 |
| 只想人工排查、不接外部系统 | **不用配 Ingress**，直接用 Web 工作台即可 |

Skill / MCP 扩展内部能力（查日志、查配置）一般 **只改配置或写 Skill/MCP 服务**，不必动 DeepTicket 主代码。

---

## 快速开始

```bash
git clone https://github.com/shanananana/deepticket.git
cd deepticket
bash scripts/setup.sh          # 创建 deepticket.yaml、Python 虚拟环境
```

编辑 **`deepticket.yaml`**（结构与密钥均在此文件，已 gitignore，勿提交）。参考 **`deepticket.example.yaml`** 中的占位示例填写。

```bash
bash scripts/start_all.sh      # 见下方「启动脚本说明」
```

浏览器打开 http://127.0.0.1:8600 ，默认账号 `admin` / `admin`（首次自动创建，**生产环境请尽快改密码**）。

### 启动脚本说明

| 命令 | 做什么 | 何时需要单独跑 |
|------|--------|----------------|
| `bash scripts/setup.sh` | 复制 `deepticket.example.yaml` → `deepticket.yaml`、安装依赖 | 仅首次或换机器 |
| `bash scripts/start_all.sh` | **一键启动**：后台 OpenHands Agent Server（8100）+ 前台 DeepTicket Web（8600）；仅当 `REDIS_START_DOCKER=1` 或本机默认 Redis 地址时才会 Docker 起 Redis | **日常启动用这个即可** |
| `bash scripts/redis.sh up` | Docker 启动 Redis（对话/账号存储） | 仅当用 redis 且未通过 `start_all.sh` 启动时 |
| `bash scripts/start_server.sh` | 只起 Agent Server | 调试 Agent 时 |

端口、存储、LLM、密钥等均在 **`deepticket.yaml`** 修改。常用项示例：

```yaml
web:
  port: 8600
engine:
  agent_server_port: 8100
storage:
  backend: redis          # 或 local
  redis_start_docker: false   # 接公司 Redis 时 false
  redis:
    url: redis://127.0.0.1:6379/0
```

### 为什么有两个端口？能合成一个吗？

| 端口 | 进程 | 作用 | 你需要访问吗 |
|------|------|------|--------------|
| **8600** | DeepTicket Web | 登录、工作台、Ingress API | **是**，浏览器只开这个 |
| **8100** | OpenHands Agent Server | Agent 执行读代码、跑命令、调 MCP | **否**，DeepTicket 内部 HTTP 调用 |

这是 OpenHands 架构决定的：Agent 运行在独立服务里，DeepTicket 做编排和 UI。`start_all.sh` 会一起拉起，**用户只面对 8600**。短期内合并成单进程需要改引擎集成方式，当前版本不支持。

---

## 配置说明（统一文件）

**所有配置集中在 `deepticket.yaml`**（从 `deepticket.example.yaml` 复制；含密钥的本地副本已 gitignore）。

```bash
cp deepticket.example.yaml deepticket.yaml   # setup.sh 会自动做
```

| 区块 | 内容 |
|------|------|
| `llm` | 模型、API Key、Base URL |
| `web` / `engine` | Web 端口、Agent Server 端口、session 密钥 |
| `storage` | local / redis、TTL、是否 Docker 起 Redis |
| `knowledge.repos` | Git 仓库列表 |
| `ingress` | 外部 Ingress 路由规则（无需 api_key） |
| `mcp.servers` | MCP 工具 |
| `extensions` | Skills 目录 |

Webhook 可直接写在路由里，不必再配分散的环境变量：

```yaml
ingress:
  routes:
    - type: ticket
      match:
        sources: [jira, internal-ticket]
      outbound:
        method: webhook
        url: http://your-itsm/internal/hook   # 直接写 URL
      repo_ids: [my-service]
```

---

## 配置清单（deepticket.yaml 字段）

### 1. LLM（必填）

```yaml
llm:
  api_key: sk-xxx
  model: openai/deepseek-v4-flash
  base_url: https://api.deepseek.com/v1
```

### 2. 引擎与会话密钥

```yaml
engine:
  session_api_key: ""   # 留空时 setup.sh 自动生成并写回 yaml
  llm_profile: deepseek-v4-flash
web:
  port: 8600
```

### 3. 存储

```yaml
storage:
  backend: redis          # 或 local
  redis_start_docker: false   # 接公司 Redis 时 false
  redis:
    url: redis://127.0.0.1:6379/0
    username: ""              # 可选；Redis 6 ACL
    password: ""              # 可选；本地无密码留空
    key_prefix: "deepticket:"
    ttl_seconds: 31536000   # 365 天；0 = 永不过期
```

有密码的 Redis 示例：

```yaml
  redis:
    url: redis://redis.internal:6379/0
    password: your-redis-password
```

或直接写在 URL：`redis://:your-password@host:6379/0`（`/health` 展示时会打码）。

本地 Docker Redis（`scripts/redis.sh up`）**默认无密码**，`username` / `password` 留空即可。

| 位置 | redis 模式下 |
|------|----------------|
| Redis | 账号、登录 token、**对话全文**、Ingress 任务、工单元数据 |
| `./data/` | **不写**（即使目录存在也为空） |
| `./workspace/` | Agent 工作区 + Git 只读缓存（运行时文件，不是业务存储；重启服务后 Git 可重新 sync） |

**接公司 Redis 有没有影响？** 一般没有。DeepTicket 只用 `deepticket:` 前缀下的 JSON 键，不会去读你们业务系统在 Redis 里的其他 key。同一 Redis 实例、不同 db 号或不同 prefix 即可共存。

查看数据（无需本机安装 redis-cli）：

```bash
bash scripts/redis.sh keys
bash scripts/redis.sh ping
```

### 4. 知识库（Git 只读）

支持 **GitHub** 与 **GitLab**（含 gitlab.com / 自建 `*.gitlab.com`）：

```yaml
knowledge:
  repos:
    - id: my-service
      url: https://github.com/your-org/your-service.git
      key: ghp_your_github_token
      branch: main
    - id: gitlab-service
      url: https://gitlab.com/your-group/your-project.git
      key: glpat_your_gitlab_token
      branch: main
```

自建 GitLab 若域名非常规，用 `url_template` 自定义 clone 地址：

```yaml
    - id: corp-gitlab
      url: https://gitlab.corp.com/group/project.git
      key: glpat_your_gitlab_token
      url_template: https://oauth2:{key}@gitlab.corp.com/group/project.git
```

启动后或在 UI「⋯ → 同步知识库」执行 `git pull`，Agent 通过 `workspace/project/<repo-id>` 只读访问代码。

### 5. Skills 与 MCP

```yaml
extensions:
  skills_dir: deepticket/skills
  user_skills_dir: ""

mcp:
  servers:
    my-tool:
      transport: stdio
      command: python
      args: ["-m", "my_mcp_server"]
```

在 `deepticket/skills/<name>/SKILL.md` 编写排查套路，UI 点「重载 Skills」生效。

### 6. 外部接入（Ingress）

用于监控、工单系统等 **无登录态** 推送事件。配置 `ingress.routes` 后重启即可接收外部 POST。

在 `deepticket.yaml` 配置：

```yaml
ingress:
  routes:
    - type: ticket
      match:
        sources: [jira]
      outbound:
        method: webhook
        url: http://your-itsm/hook
```

`outbound.method`：`store_only`（只存库）或 `webhook`（POST 到 `outbound.url`）。

**API：**

```bash
curl -X POST http://127.0.0.1:8600/api/ingress/events \
  -H "Content-Type: application/json" \
  -d '{"source":"jira","external_id":"T-001","title":"API 500","body":"...","image_urls":["https://example.com/screen.png"]}'

bash scripts/test_ingress_e2e.sh   # 本地联调
```

---

## 使用方式

### Web 工作台（人工排查）

1. 登录 → 新建对话
2. 描述现象，可粘贴日志
3. 需要时代码分析前点「同步知识库」
4. Agent 流式回复；思考过程来自真实 OpenHands 活动事件

### 已登录 API（与 UI 相同能力）

| 端点 | 用途 |
|------|------|
| `POST /api/chat` | 会话内续聊（SSE）；可选 `image_urls` |
| `POST /api/ticket` | 一次性工单分析（SSE）；可选 `image_urls` |
| `POST /api/chats` | 创建/管理对话 |

需 Bearer Token（登录接口获取）。

### 外部 Ingress（自动化）

见上文「外部接入」。事件经 `ingress.routes` 分类 → Agent 分析 → webhook 或仅存库。

---

## 开发与验证

```bash
pip install -e ".[dev]"
ruff check deepticket tests
pytest -q
bash scripts/verify.sh          # 离线检查
bash scripts/verify.sh --online # 含 Agent Server / Web 在线检查
```

---

## 系统要求

- macOS / Linux，Python 3.11+
- Docker（可选，用于 `scripts/redis.sh` 起 Redis）
- 任意 **OpenAI 兼容** LLM 端点

---

## License

[MIT](LICENSE)
