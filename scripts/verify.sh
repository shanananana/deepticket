#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/python ]]; then
  echo "请先运行: bash scripts/setup.sh"
  exit 1
fi

# shellcheck disable=SC1091
source scripts/lib/export_config_env.sh
export_config_from_yaml "$ROOT"

# shellcheck disable=SC1091
source scripts/lib/env.sh
normalize_session_api_env

exec .venv/bin/deepticket-verify "$@"
