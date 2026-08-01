#!/usr/bin/env bash
# Shared .env helpers for DeepTicket shell scripts.

# OpenHands treats OH_SESSION_API_KEYS_0= (empty) as a valid key list [""],
# which enables auth but rejects requests without X-Session-API-Key.
normalize_session_api_env() {
  if [[ -z "${OH_SESSION_API_KEYS_0:-}" ]]; then
    unset OH_SESSION_API_KEYS_0
  fi
  if [[ -z "${SESSION_API_KEY:-}" ]]; then
    unset SESSION_API_KEY
  fi
}

ensure_session_api_key_in_env_file() {
  local env_file="${1:-.env}"
  [[ -f "$env_file" ]] || return 0

  local current=""
  if grep -q '^OH_SESSION_API_KEYS_0=' "$env_file"; then
    current="$(grep '^OH_SESSION_API_KEYS_0=' "$env_file" | head -1 | cut -d= -f2-)"
  fi
  if [[ -n "$current" ]]; then
    return 0
  fi

  local key=""
  if command -v openssl >/dev/null 2>&1; then
    key="$(openssl rand -hex 16)"
  else
    key="$(python3 -c "import secrets; print(secrets.token_hex(16))")"
  fi

  if grep -q '^OH_SESSION_API_KEYS_0=' "$env_file"; then
    sed -i '' "s|^OH_SESSION_API_KEYS_0=.*|OH_SESSION_API_KEYS_0=${key}|" "$env_file"
  else
    printf '\nOH_SESSION_API_KEYS_0=%s\n' "$key" >>"$env_file"
  fi
  echo "已生成 OH_SESSION_API_KEYS_0（Agent Server 与 DeepTicket 共用）"
}
