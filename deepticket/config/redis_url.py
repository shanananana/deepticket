from __future__ import annotations

from urllib.parse import quote, urlparse, urlunparse


def resolve_redis_url(
    url: str,
    *,
    username: str = "",
    password: str = "",
) -> str:
    """合并 url 与可选账号密码；url 已含 @ 鉴权时不覆盖。"""
    parsed = urlparse(url.strip())
    if parsed.username or parsed.password:
        return url.strip()

    user = username.strip()
    pwd = password.strip()
    if not user and not pwd:
        return url.strip()

    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 6379
    if pwd:
        auth = f"{quote(user, safe='')}:{quote(pwd, safe='')}@" if user else f":{quote(pwd, safe='')}@"
    else:
        auth = f"{quote(user, safe='')}@"
    netloc = f"{auth}{host}:{port}"
    return urlunparse(parsed._replace(netloc=netloc))


def redact_redis_url(url: str) -> str:
    """隐藏 URL 中的密码，供 /health 等对外展示。"""
    parsed = urlparse(url)
    if parsed.password is None:
        return url
    host = parsed.hostname or ""
    port = parsed.port
    hostport = f"{host}:{port}" if port else host
    user = parsed.username or ""
    auth = f"{user}:***@" if user else ":***@"
    return urlunparse(parsed._replace(netloc=f"{auth}{hostport}"))
