#!/usr/bin/env bash
# 外部工单 Ingress 进 / Outbound 出 — 本地联调
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/python ]]; then
  echo "请先 bash scripts/setup.sh" >&2
  exit 1
fi

WEB_PORT="$(.venv/bin/python - <<'PY'
from deepticket.config.loader import load_app_config
from deepticket.paths import PROJECT_ROOT
print(load_app_config(PROJECT_ROOT).web.port)
PY
)"

WEB="${WEB_PORT:-8600}"
BASE="http://127.0.0.1:${WEB}"

WH_PORT="${TEST_WEBHOOK_PORT:-8765}"
WH_FILE=$(mktemp)
python3 - <<PY &
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

OUT = "$WH_FILE"

class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        with open(OUT, "w", encoding="utf-8") as f:
            f.write(body.decode("utf-8"))
        print(f"[webhook] 收到回调 external_id={json.loads(body).get('external_id')}", flush=True)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

srv = HTTPServer(("127.0.0.1", $WH_PORT), H)
print(f"[webhook] listening :$WH_PORT", flush=True)
srv.serve_forever()
PY
WH_PID=$!
trap 'kill $WH_PID 2>/dev/null || true; rm -f "$WH_FILE"' EXIT
sleep 0.5

echo "提示: 在 deepticket.yaml 的 ingress.routes[ticket].outbound.url 设为:"
echo "  http://127.0.0.1:${WH_PORT}/callback"
echo "然后重启 DeepTicket，再运行本脚本。"
echo ""

ROUTES_CODE=$(curl -s -o /dev/null -w '%{http_code}' "${BASE}/api/ingress/routes" || true)
if [[ "$ROUTES_CODE" == "404" ]]; then
  echo "Ingress API 不存在 (404)。请用最新代码重启: bash scripts/start_all.sh" >&2
  exit 1
fi

echo "== 推送工单 =="
RESP=$(curl -s -w '\nHTTP_CODE:%{http_code}' -X POST "${BASE}/api/ingress/events" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "jira",
    "external_id": "DEMO-1001",
    "title": "接口超时排查",
    "body": "用户反馈下单接口 P99 超过 3s",
    "type": "ticket"
  }')
HTTP_CODE="${RESP##*HTTP_CODE:}"
BODY="${RESP%HTTP_CODE:*}"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
echo "HTTP $HTTP_CODE"

if [[ -s "$WH_FILE" ]]; then
  echo "== Webhook 回调 body =="
  python3 -m json.tool "$WH_FILE"
else
  echo "== 未收到 Webhook（请确认 yaml 中 ticket 路由 outbound.url 已指向 :${WH_PORT} 且已重启）=="
fi
