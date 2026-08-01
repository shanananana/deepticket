#!/usr/bin/env bash
# DeepTicket Redis（Docker，国内镜像）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# 国内镜像前缀（DaoCloud 公共代理，无需登录）
REDIS_IMAGE="${REDIS_IMAGE:-docker.m.daocloud.io/library/redis:7-alpine}"

cmd="${1:-up}"

case "$cmd" in
  up|start)
    echo "拉取 Redis 镜像（国内源）: $REDIS_IMAGE"
    docker pull "$REDIS_IMAGE"
    docker compose up -d redis
    echo "等待 Redis 就绪…"
    for _ in $(seq 1 30); do
      if docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
        echo "Redis 已启动: redis://127.0.0.1:6379/0"
        exit 0
      fi
      sleep 1
    done
    echo "Redis 启动超时，请检查: docker compose logs redis" >&2
    exit 1
    ;;
  down|stop)
    docker compose stop redis
    echo "Redis 已停止（数据卷保留）"
    ;;
  restart)
    docker compose restart redis
    ;;
  logs)
    docker compose logs -f redis
    ;;
  ping)
    docker compose exec -T redis redis-cli ping
    ;;
  keys)
    echo "统计 deepticket:* 键"
    docker compose exec -T redis redis-cli --scan --pattern 'deepticket:*' | wc -l | awk '{print "total:", $1}'
    echo "按类型:"
    docker compose exec -T redis redis-cli --scan --pattern 'deepticket:*' \
      | sed 's/^deepticket://' | cut -d: -f1 | sort | uniq -c | sort -rn
    ;;
  status)
    docker compose ps redis
    ;;
  *)
    echo "用法: $0 {up|down|restart|logs|ping|keys|status}" >&2
    exit 1
    ;;
esac
