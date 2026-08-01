from __future__ import annotations

from deepticket.layers.storage.redis_store import RedisStorage


class _FakeRedis:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, int | None]] = []

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.calls.append((key, value, ex))


def test_set_json_applies_ttl():
    fake = _FakeRedis()
    storage = RedisStorage("redis://127.0.0.1:6379/0", ttl_seconds=3600)
    storage.client = fake  # type: ignore[assignment]

    storage.set_json("chat_threads", "u1:c1", {"hello": "world"})

    assert len(fake.calls) == 1
    key, _value, ex = fake.calls[0]
    assert key == "deepticket:chat_threads:u1:c1"
    assert ex == 3600


def test_set_json_no_ttl_when_zero():
    fake = _FakeRedis()
    storage = RedisStorage("redis://127.0.0.1:6379/0", ttl_seconds=0)
    storage.client = fake  # type: ignore[assignment]

    storage.set_json("users", "uid1", {"username": "admin"})

    assert fake.calls[0][2] is None
