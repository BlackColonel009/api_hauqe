from __future__ import annotations

import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)


password_hasher = PasswordHasher()


def verify_password(
    plain_password: str,
    password_hash: str | None,
) -> bool:
    if not password_hash:
        return False

    try:
        return password_hasher.verify(
            password_hash,
            plain_password,
        )
    except (
        VerifyMismatchError,
        VerificationError,
        InvalidHashError,
    ):
        return False


def generate_access_token() -> str:
    """
    Le token brut est envoyé uniquement au client.
    Il n'est jamais enregistré en base.
    """
    return secrets.token_urlsafe(48)


def hash_access_token(token: str) -> str:
    """
    64 caractères hexadécimaux.
    Compatible avec VARCHAR(255).
    """
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()