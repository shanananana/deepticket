from deepticket.config.redis_url import redact_redis_url, resolve_redis_url


def test_resolve_redis_url_no_auth() -> None:
    assert (
        resolve_redis_url("redis://127.0.0.1:6379/0")
        == "redis://127.0.0.1:6379/0"
    )


def test_resolve_redis_url_password_only() -> None:
    url = resolve_redis_url(
        "redis://redis.internal:6379/2",
        password="secret",
    )
    assert url == "redis://:secret@redis.internal:6379/2"


def test_resolve_redis_url_username_and_password() -> None:
    url = resolve_redis_url(
        "redis://127.0.0.1:6379/0",
        username="deepticket",
        password="secret",
    )
    assert url == "redis://deepticket:secret@127.0.0.1:6379/0"


def test_resolve_redis_url_keeps_existing_auth() -> None:
    original = "redis://user:pass@host:6379/0"
    assert resolve_redis_url(original, password="ignored") == original


def test_redact_redis_url() -> None:
    assert (
        redact_redis_url("redis://deepticket:secret@127.0.0.1:6379/0")
        == "redis://deepticket:***@127.0.0.1:6379/0"
    )
    assert redact_redis_url("redis://:secret@127.0.0.1:6379/0") == "redis://:***@127.0.0.1:6379/0"
