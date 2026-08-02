#!/usr/bin/env bash
# 一键检查 DeepTicket / Agent Server / Redis 状态
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/python ]]; then
  echo "未安装：请先 bash scripts/setup.sh" >&2
  exit 1
fi

read -r WEB_HOST WEB_PORT AGENT_HOST AGENT_PORT INGRESS_KEY <<EOF
$(.venv/bin/python - <<'PY'
from deepticket.config.loader import load_app_config
from deepticket.paths import PROJECT_ROOT

c = load_app_config(PROJECT_ROOT)
print(c.web.host, c.web.port, c.engine.agent_server_host, c.engine.agent_server_port, c.ingress.api_key)
PY
)
EOF

WEB_URL="http://${WEB_HOST}:${WEB_PORT}"
AGENT_URL="http://${AGENT_HOST}:${AGENT_PORT}"

check_url() {
  local name="$1"
  local url="$2"
  if curl -sf "$url" >/dev/null 2>&1; then
    echo "[OK]   $name  $url"
    return 0
  fi
  echo "[FAIL] $name  $url"
  return 1
}

FAIL=0
check_url "DeepTicket Web" "${WEB_URL}/api/health" || FAIL=1
check_url "Agent Server" "${AGENT_URL}/health" || FAIL=1

if [[ "${STORAGE_BACKEND:-}" == "redis" ]] || .venv/bin/python - <<'PY'
from deepticket.config.loader import load_app_config
from deepticket.paths import PROJECT_ROOT
print(load_app_config(PROJECT_ROOT).storage.backend)
PY
| grep -q redis; then
  REDIS_URL="$(.venv/bin/python - <<'PY'
from deepticket.config.loader import load_app_config
from deepticket.config.redis_url import resolve_redis_url
from deepticket.paths import PROJECT_ROOT
c = load_app_config(PROJECT_ROOT)
print(resolve_redis_url(c.storage.redis.url, username=c.storage.redis.username, password=c.storage.redis.password))
PY
)"
  if command -v redis-cli >/dev/null 2>&1; then
    if redis-cli -u "$REDIS_URL" ping 2>/dev/null | grep -q PONG; then
      echo "[OK]   Redis   $REDIS_URL"
    else
      echo "[FAIL] Redis   $REDIS_URL"
      FAIL=1
    fi
  else
    echo "[SKIP] Redis   (未安装 redis-cli，跳过 ping)"
  fi
fi

HEALTH="$(curl -sf "${WEB_URL}/api/health" 2>/dev/null || true)"
if [[ -n "$HEALTH" ]]; then
  echo ""
  echo "== Ingress 队列 =="
  echo "$HEALTH" | .venv/bin/python - <<'PY'
import json, sys
data = json.load(sys.stdin)
ingress = data.get("ingress", {})
queue = ingress.get("queue", {})
print(f"  auth configured: {ingress.get('auth')}")
print(f"  workers:         {queue.get('workers')}")
print(f"  pending:         {queue.get('pending')}")
PY
fi

echo ""
if [[ -n "$INGRESS_KEY" ]]; then
  echo "Ingress 鉴权: 请求头 X-Ingress-API-Key: <见 deepticket.yaml ingress.api_key>"
else
  echo "Ingress 鉴权: 未配置 api_key（运行 setup.sh 可自动生成）"
fi
echo "Web:    ${WEB_URL}"
echo "Agent:  ${AGENT_URL} (内部，无需浏览器访问)"

exit "$FAIL"
