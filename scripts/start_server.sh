#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source scripts/lib/export_config_env.sh
export_config_from_yaml "$ROOT"

# shellcheck disable=SC1091
source scripts/lib/env.sh
normalize_session_api_env

HOST="${AGENT_SERVER_HOST:-127.0.0.1}"
PORT="${AGENT_SERVER_PORT:-8100}"
WEB_PORT="${WEB_PORT:-8600}"

export OPENHANDS_SUPPRESS_BANNER=1
export OH_ALLOW_CORS_ORIGINS_0="http://127.0.0.1:${WEB_PORT}"

mkdir -p workspace/project workspace/knowledge workspace/project/.openhands/skills
if [[ "${STORAGE_BACKEND:-local}" == "local" ]]; then
  mkdir -p data
fi

echo "启动 OpenHands Agent Server: http://${HOST}:${PORT}"
echo "健康检查: curl http://${HOST}:${PORT}/health"

exec .venv/bin/python -m openhands.agent_server --host "$HOST" --port "$PORT"
