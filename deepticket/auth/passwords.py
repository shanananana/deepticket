from __future__ import annotations

import hashlib
import hmac
import secrets

_PBKDF2_ITERATIONS = 120_000


def hash_password(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _PBKDF2_ITERATIONS,
    )
    return salt, digest.hex()


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _PBKDF2_ITERATIONS,
    )
    return hmac.compare_digest(digest.hex(), password_hash)
