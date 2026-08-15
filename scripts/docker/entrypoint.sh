#!/usr/bin/env bash
set -euo pipefail

cd /app

export DEEPTICKET_CONFIG="${DEEPTICKET_CONFIG:-/app/deepticket.docker.yaml}"
export OPENHANDS_SUPPRESS_BANNER=1
export WEB_PORT="${WEB_PORT:-8600}"
export AGENT_SERVER_HOST="${AGENT_SERVER_HOST:-127.0.0.1}"
export AGENT_SERVER_PORT="${AGENT_SERVER_PORT:-8100}"

if [[ -z "${DEEPTICKET_SESSION_API_KEY:-}" ]]; then
  export DEEPTICKET_SESSION_API_KEY="$(python -c 'import secrets; print(secrets.token_hex(16))')"
fi
if [[ -z "${DEEPTICKET_INGRESS_API_KEY:-}" ]]; then
  export DEEPTICKET_INGRESS_API_KEY="$(python -c 'import secrets; print(secrets.token_hex(16))')"
fi

export OH_ALLOW_CORS_ORIGINS_0="http://127.0.0.1:${WEB_PORT}"
export OH_ALLOW_CORS_ORIGINS_1="http://localhost:${WEB_PORT}"
if [[ -n "${OH_SESSION_API_KEYS_0:-}" ]]; then
  :
else
  export OH_SESSION_API_KEYS_0="${DEEPTICKET_SESSION_API_KEY}"
fi

mkdir -p workspace/project workspace/knowledge workspace/project/.openhands/skills data

python - <<'PY'
import os
import time

import redis

url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
deadline = time.time() + 60
last_err = None
while time.time() < deadline:
    try:
        if redis.from_url(url, decode_responses=True).ping():
            break
    except redis.RedisError as exc:
        last_err = exc
        time.sleep(1)
else:
    raise SystemExit(f"Redis 未就绪 ({url}): {last_err}")
PY

echo "启动 OpenHands Agent Server: http://${AGENT_SERVER_HOST}:${AGENT_SERVER_PORT}"
python -m openhands.agent_server --host "$AGENT_SERVER_HOST" --port "$AGENT_SERVER_PORT" &
AGENT_PID=$!

cleanup() {
  kill "$AGENT_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

for _ in $(seq 1 90); do
  if curl -sf "http://${AGENT_SERVER_HOST}:${AGENT_SERVER_PORT}/health" >/dev/null; then
    break
  fi
  sleep 1
done

if ! curl -sf "http://${AGENT_SERVER_HOST}:${AGENT_SERVER_PORT}/health" >/dev/null; then
  echo "Agent Server 启动失败" >&2
  exit 1
fi

echo ""
echo "=========================================="
echo " DeepTicket Web UI: http://127.0.0.1:${WEB_PORT}"
echo " 默认账户: admin / admin"
echo " 配置: ${DEEPTICKET_CONFIG}"
echo "=========================================="
echo ""

exec python -m deepticket
