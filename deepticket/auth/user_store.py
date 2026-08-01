from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from deepticket.auth.passwords import hash_password, verify_password
from deepticket.layers.storage.base import StorageBackend
from deepticket.utils.time import utc_now_iso

_NS_USERS = "users"
_NS_USERS_BY_NAME = "users_by_name"
_NS_AUTH_TOKENS = "auth_tokens"

_TOKEN_TTL_DAYS = 30
_USERNAME_MIN = 3
_USERNAME_MAX = 32
_PASSWORD_MIN = 6


@dataclass(frozen=True)
class AuthUser:
    uid: str
    username: str


class UserStore:
    """用户注册 / 登录 / Token 会话。"""

    def __init__(self, storage: StorageBackend) -> None:
        self.storage = storage

    def register(self, username: str, password: str) -> AuthUser:
        name = username.strip()
        if not (_USERNAME_MIN <= len(name) <= _USERNAME_MAX):
            raise ValueError(
                f"用户名长度需在 {_USERNAME_MIN}-{_USERNAME_MAX} 个字符之间"
            )
        if len(password) < _PASSWORD_MIN:
            raise ValueError(f"密码至少 {_PASSWORD_MIN} 个字符")

        lookup_key = name.lower()
        if self.storage.get_json(_NS_USERS_BY_NAME, lookup_key):
            raise ValueError("用户名已被占用")

        uid = uuid.uuid4().hex
        salt, password_hash = hash_password(password)
        now = utc_now_iso()
        self.storage.set_json(
            _NS_USERS,
            uid,
            {
                "uid": uid,
                "username": name,
                "salt": salt,
                "password_hash": password_hash,
                "created_at": now,
            },
        )
        self.storage.set_json(_NS_USERS_BY_NAME, lookup_key, {"uid": uid})
        return AuthUser(uid=uid, username=name)

    def login(self, username: str, password: str) -> tuple[AuthUser, str]:
        name = username.strip()
        lookup = self.storage.get_json(_NS_USERS_BY_NAME, name.lower())
        if not lookup:
            raise ValueError("用户名或密码错误")
        user_doc = self.storage.get_json(_NS_USERS, lookup["uid"])
        if not user_doc:
            raise ValueError("用户名或密码错误")
        if not verify_password(
            password, user_doc["salt"], user_doc["password_hash"]
        ):
            raise ValueError("用户名或密码错误")

        user = AuthUser(uid=user_doc["uid"], username=user_doc["username"])
        token = secrets.token_urlsafe(32)
        expires_at = (
            datetime.now(UTC) + timedelta(days=_TOKEN_TTL_DAYS)
        ).isoformat()
        self.storage.set_json(
            _NS_AUTH_TOKENS,
            token,
            {
                "uid": user.uid,
                "username": user.username,
                "created_at": utc_now_iso(),
                "expires_at": expires_at,
            },
        )
        return user, token

    def resolve_token(self, token: str) -> AuthUser | None:
        if not token.strip():
            return None
        doc = self.storage.get_json(_NS_AUTH_TOKENS, token.strip())
        if not doc:
            return None
        expires_at = doc.get("expires_at")
        if expires_at:
            try:
                expiry = datetime.fromisoformat(expires_at)
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=UTC)
                if datetime.now(UTC) >= expiry:
                    self.storage.delete(_NS_AUTH_TOKENS, token.strip())
                    return None
            except ValueError:
                pass
        user_doc = self.storage.get_json(_NS_USERS, doc["uid"])
        if not user_doc:
            return None
        return AuthUser(uid=user_doc["uid"], username=user_doc["username"])

    def logout(self, token: str) -> None:
        self.storage.delete(_NS_AUTH_TOKENS, token.strip())

    def get_user(self, uid: str) -> AuthUser | None:
        doc = self.storage.get_json(_NS_USERS, uid)
        if not doc:
            return None
        return AuthUser(uid=doc["uid"], username=doc["username"])

    def ensure_bootstrap_user(self, username: str, password: str) -> AuthUser | None:
        """首次启动创建内置账户（若不存在）。"""
        name = username.strip()
        lookup_key = name.lower()
        if self.storage.get_json(_NS_USERS_BY_NAME, lookup_key):
            existing = self.storage.get_json(_NS_USERS_BY_NAME, lookup_key)
            if existing:
                user_doc = self.storage.get_json(_NS_USERS, existing["uid"])
                if user_doc:
                    return AuthUser(uid=user_doc["uid"], username=user_doc["username"])
            return None

        uid = uuid.uuid4().hex
        salt, password_hash = hash_password(password)
        now = utc_now_iso()
        self.storage.set_json(
            _NS_USERS,
            uid,
            {
                "uid": uid,
                "username": name,
                "salt": salt,
                "password_hash": password_hash,
                "created_at": now,
                "bootstrap": True,
            },
        )
        self.storage.set_json(_NS_USERS_BY_NAME, lookup_key, {"uid": uid})
        return AuthUser(uid=uid, username=name)
