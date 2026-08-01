#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/python ]]; then
  bash scripts/setup.sh
fi

# shellcheck disable=SC1091
source scripts/lib/export_config_env.sh
export_config_from_yaml "$ROOT"

# shellcheck disable=SC1091
source scripts/lib/env.sh
normalize_session_api_env

if [[ "${STORAGE_BACKEND:-local}" == "redis" ]]; then
  _redis_url="${REDIS_URL:-redis://127.0.0.1:6379/0}"
  _start_docker="${REDIS_START_DOCKER:-auto}"
  _should_start=0
  if [[ "$_start_docker" == "1" ]]; then
    _should_start=1
  elif [[ "$_start_docker" != "0" && "$_redis_url" == redis://127.0.0.1:6379/* ]]; then
    _should_start=1
  fi
  if [[ "$_should_start" == "1" ]]; then
    bash scripts/redis.sh up
  fi
fi

HOST="${AGENT_SERVER_HOST:-127.0.0.1}"
PORT="${AGENT_SERVER_PORT:-8100}"
WEB_PORT="${WEB_PORT:-8600}"

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]]; then kill "$SERVER_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT

bash scripts/start_server.sh &
SERVER_PID=$!

echo "等待 Agent Server 就绪…"
for i in {1..60}; do
  if curl -sf "http://${HOST}:${PORT}/health" >/dev/null; then
    break
  fi
  sleep 1
done

if ! curl -sf "http://${HOST}:${PORT}/health" >/dev/null; then
  echo "Agent Server 启动失败"
  exit 1
fi

echo ""
echo "=========================================="
echo " DeepTicket Web UI: http://127.0.0.1:${WEB_PORT}"
echo " Agent Server:     http://${HOST}:${PORT}"
echo " 配置:             deepticket.yaml"
echo "=========================================="
echo ""

exec .venv/bin/python -m deepticket
