# Docker 一键启动

无需本地 Python / venv，容器内同时运行 **Web（8600）**、**OpenHands Agent Server** 与 **Redis**。

## 前提

- 已安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)（或 Docker Engine + Compose v2）
- LLM API Key 可在启动前写入 `.env`，也可启动后在 Web **LLM 配置** 页填写（管理员）

## 三步启动

```bash
git clone https://github.com/shanananana/deepticket.git
cd deepticket

cp .env.docker.example .env
# 可选：编辑 .env 填写 LLM_API_KEY=sk-...

docker compose up -d --build
```

浏览器打开 **http://127.0.0.1:8600**，默认账户 `admin` / `admin`。若未配置 LLM，登录后会引导至 **LLM 配置**。

## 常用命令

```bash
docker compose logs -f deepticket   # 看日志
docker compose down                 # 停止
docker compose down -v              # 停止并清空数据卷
```

## 架构说明

| 组件 | 说明 |
|------|------|
| `deepticket` 容器 | 单容器内：Agent Server（127.0.0.1:8100）+ DeepTicket Web（0.0.0.0:8600） |
| `redis` 容器 | 聊天 / 项目配置存储（与 `deepticket.docker.yaml` 一致） |
| 数据卷 | `deepticket_data`、`deepticket_workspace` 持久化 |

默认读 **`deepticket.docker.yaml`**（仓库内，适合 Docker 网络：`redis://redis:6379`、监听 `0.0.0.0`）。

## 使用本地 deepticket.yaml

若已按文档生成 `deepticket.yaml`，在 `docker-compose.yml` 的 `deepticket` 服务中：

1. 取消 `./deepticket.yaml` 挂载注释  
2. 设置 `DEEPTICKET_CONFIG=/app/deepticket.yaml`  
3. 将 yaml 里 `storage.redis.url` 改为 `redis://redis:6379/0`，`web.host` 改为 `0.0.0.0`，`redis_start_docker: false`

## 与脚本启动的区别

| | `bash scripts/start_all.sh` | `docker compose up` |
|--|------------------------------|---------------------|
| 依赖 | 本机 Python 3.11+ venv | 仅 Docker |
| Agent + Web | 本机两进程 | 单容器两进程 |
| Redis | 可选自动起 Docker Redis | Compose 自带 |
| 改代码热更新 | 方便 | 需 rebuild |

开发调试仍推荐脚本启动；对外演示、内网试点可用 Docker。

## 方式 B：拉 GHCR 预构建镜像（无需 clone / build）

发布版本后，镜像位于 **`ghcr.io/shanananana/deepticket`**（打 `v*` tag 时 CI 自动 push，并设为 Public）。

```bash
curl -LO https://raw.githubusercontent.com/shanananana/deepticket/main/docker-compose.image.yml
curl -LO https://raw.githubusercontent.com/shanananana/deepticket/main/.env.docker.example
cp .env.docker.example .env

docker compose -f docker-compose.image.yml up -d
```

固定版本（推荐生产）：编辑 `docker-compose.image.yml`，将 `image` 改为例如 `ghcr.io/shanananana/deepticket:v0.2.4`。

## 维护者：发布公开镜像

1. 更新 `CHANGELOG.md`，提交并打 tag：`git tag v0.2.4 && git push origin v0.2.4`
2. GitHub Actions **Docker Publish** 工作流会自动 build → push 到 GHCR → 将包设为 **Public**
3. 首次可在 [Packages](https://github.com/users/shanananana/packages) 确认 `deepticket` 可见且为公开

手动 push（可选）：

```bash
echo "$(gh auth token)" | docker login ghcr.io -u shanananana --password-stdin
docker build -t ghcr.io/shanananana/deepticket:latest .
docker push ghcr.io/shanananana/deepticket:latest
gh api --method PATCH /user/packages/container/deepticket/visibility -f visibility=public
```
