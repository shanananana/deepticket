#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f deepticket.yaml ]]; then
  cp deepticket.example.yaml deepticket.yaml
  echo "已创建 deepticket.yaml（统一配置，已 gitignore）"
fi

# shellcheck disable=SC1091
source scripts/lib/env.sh

# 从 yaml 同步 session key（若 yaml 中为空则写入 yaml）
if [[ -x .venv/bin/python ]]; then
  .venv/bin/python - <<'PY' || true
from pathlib import Path
import yaml
from deepticket.paths import PROJECT_ROOT

path = PROJECT_ROOT / "deepticket.yaml"
if not path.is_file():
    raise SystemExit(0)
data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
engine = data.setdefault("engine", {})
if engine.get("session_api_key"):
    raise SystemExit(0)
import secrets
key = secrets.token_hex(16)
engine["session_api_key"] = key
path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
print(f"已生成 engine.session_api_key 并写入 deepticket.yaml")
PY
fi

python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -e .
echo "安装完成。请编辑 deepticket.yaml 后运行 bash scripts/start_all.sh"
