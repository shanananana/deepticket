from __future__ import annotations

import os


def resolve_outbound_url(outbound_url: str, url_env: str) -> str:
    if outbound_url.strip():
        return outbound_url.strip()
    env_name = url_env.strip()
    if not env_name:
        return ""
    return os.environ.get(env_name, "").strip()
