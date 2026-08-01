#!/usr/bin/env bash
# 从 deepticket.yaml 导出 shell 所需环境变量（供 start_all.sh / start_server.sh 使用）

export_config_from_yaml() {
  local root="${1:-.}"
  if [[ ! -x "$root/.venv/bin/python" ]]; then
    echo "export_config_from_yaml: 未找到 $root/.venv/bin/python" >&2
    return 1
  fi
  # shellcheck disable=SC1090
  eval "$(cd "$root" && .venv/bin/python - <<'PY'
from deepticket.config.loader import load_app_config
from deepticket.config.redis_url import resolve_redis_url
from deepticket.paths import PROJECT_ROOT

c = load_app_config(PROJECT_ROOT)
redis_url = resolve_redis_url(
    c.storage.redis.url,
    username=c.storage.redis.username,
    password=c.storage.redis.password,
)
print(f"export WEB_HOST={c.web.host!r}")
print(f"export WEB_PORT={c.web.port!r}")
print(f"export AGENT_SERVER_HOST={c.engine.agent_server_host!r}")
print(f"export AGENT_SERVER_PORT={c.engine.agent_server_port!r}")
print(f"export STORAGE_BACKEND={c.storage.backend!r}")
print(f"export REDIS_URL={redis_url!r}")
print(f"export REDIS_START_DOCKER={'1' if c.storage.redis_start_docker else '0'}")
if c.engine.session_api_key:
    print(f"export OH_SESSION_API_KEYS_0={c.engine.session_api_key!r}")
PY
)"
}
