"""
Utilitaires cryptographiques du domaine Mon compte.

- Argon2 : mots de passe, codes privés, codes de récupération.
- SHA-256 : jetons opaques à forte entropie stockés en base.
- Fernet : chiffrement réversible du secret TOTP.
- TOTP : implémentation RFC 6238 avec la bibliothèque standard.

Le secret MFA n'est jamais journalisé et ne doit jamais être renvoyé après
la phase d'enrôlement.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken

from app.config.settings import settings


_password_hasher = PasswordHasher()


def hash_secret(value: str) -> str:
    return _password_hasher.hash(value)


def verify_secret(stored_hash: str | None, value: str) -> bool:
    if not stored_hash:
        return False
    try:
        return _password_hasher.verify(stored_hash, value)
    except VerifyMismatchError:
        return False


def token_hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_opaque_token(bytes_length: int = 32) -> str:
    return secrets.token_urlsafe(bytes_length)


def _fernet() -> Fernet:
    key = settings.mfa_fernet_key
    if not key:
        raise RuntimeError(
            "MFA_FERNET_KEY non configurée dans les settings."
        )
    if isinstance(key, str):
        key = key.encode("ascii")
    try:
        return Fernet(key)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "MFA_FERNET_KEY invalide : une clé Fernet URL-safe "
            "de 32 octets encodée en Base64 est requise."
        ) from exc


def encrypt_mfa_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode("ascii")).decode("ascii")


def decrypt_mfa_secret(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode("ascii")).decode("ascii")
    except InvalidToken as exc:
        raise RuntimeError(
            "Impossible de déchiffrer le secret MFA."
        ) from exc


def generate_totp_secret() -> str:
    raw = secrets.token_bytes(20)
    return base64.b32encode(raw).decode("ascii").rstrip("=")


def _decode_base32(secret: str) -> bytes:
    padding = "=" * ((8 - len(secret) % 8) % 8)
    return base64.b32decode(secret + padding, casefold=True)


def totp_code(
    secret: str,
    *,
    for_time: int | None = None,
    period: int = 30,
    digits: int = 6,
) -> str:
    timestamp = int(for_time if for_time is not None else time.time())
    counter = timestamp // period

    digest = hmac.new(
        _decode_base32(secret),
        struct.pack(">Q", counter),
        hashlib.sha1,
    ).digest()

    offset = digest[-1] & 0x0F
    binary = (
        ((digest[offset] & 0x7F) << 24)
        | ((digest[offset + 1] & 0xFF) << 16)
        | ((digest[offset + 2] & 0xFF) << 8)
        | (digest[offset + 3] & 0xFF)
    )
    value = binary % (10 ** digits)
    return str(value).zfill(digits)


def verify_totp_code(
    secret: str,
    code: str,
    *,
    window: int = 1,
    period: int = 30,
) -> bool:
    candidate = "".join(ch for ch in code.strip() if ch.isdigit())
    if len(candidate) != 6:
        return False

    now = int(time.time())
    for step in range(-window, window + 1):
        expected = totp_code(
            secret,
            for_time=now + step * period,
            period=period,
        )
        if hmac.compare_digest(expected, candidate):
            return True
    return False


def provisioning_uri(
    *,
    secret: str,
    email: str,
    issuer: str = "HAUQE Certif",
) -> str:
    label = f"{issuer}:{email}"
    return (
        f"otpauth://totp/{quote(label)}"
        f"?secret={quote(secret)}"
        f"&issuer={quote(issuer)}"
        "&algorithm=SHA1"
        "&digits=6"
        "&period=30"
    )


def generate_recovery_codes(count: int = 8) -> list[str]:
    codes = []
    for _ in range(count):
        value = secrets.token_hex(5).upper()
        codes.append(f"{value[:5]}-{value[5:]}")
    return codes
