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

python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -e .

# 从 yaml 同步 session / ingress key（若 yaml 中为空则写入 yaml）
.venv/bin/python - <<'PY' || true
from pathlib import Path
import secrets
import yaml
from deepticket.paths import PROJECT_ROOT

path = PROJECT_ROOT / "deepticket.yaml"
if not path.is_file():
    raise SystemExit(0)
data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
engine = data.setdefault("engine", {})
ingress = data.setdefault("ingress", {})
changed = False
if not engine.get("session_api_key"):
    engine["session_api_key"] = secrets.token_hex(16)
    changed = True
    print("已生成 engine.session_api_key 并写入 deepticket.yaml")
if not ingress.get("api_key"):
    ingress["api_key"] = secrets.token_hex(16)
    changed = True
    print("已生成 ingress.api_key 并写入 deepticket.yaml")
if changed:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
PY

echo "安装完成。请编辑 deepticket.yaml 后运行："
echo "  bash scripts/start_all.sh"
echo "  bash scripts/quickstart_demo.sh   # 5 分钟上手提示"
