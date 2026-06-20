import os
import hmac
import hashlib
import base64
from typing import Optional


_SECRET_VALUE = os.getenv("REFERRAL_CODE_SECRET")

if not _SECRET_VALUE:
    raise RuntimeError("REFERRAL_CODE_SECRET must be set")

_SECRET = _SECRET_VALUE.encode("utf-8")


IDENTITY_SCHEME = "HMAC_SHA256_HEX_V1"


def _clean(value: Optional[str]) -> str:
    return (value or "").strip()


def _hmac_sha256_digest(value: str) -> bytes:
    msg = _clean(value).encode("utf-8")
    return hmac.new(_SECRET, msg, hashlib.sha256).digest()


def _hmac_sha256_hex(value: str) -> str:
    return _hmac_sha256_digest(value).hex().upper()


def ucn_lookup_key(value: str, length: int = 64) -> str:
    return _hmac_sha256_hex(value)[:length]


def account_lookup_key(value: str, length: int = 64) -> str:
    return _hmac_sha256_hex(value)[:length]


def hmac_key(value: str, length: int = 64) -> str:
    return _hmac_sha256_hex(value)[:length]


def hmac_token(value: str, length: int = 12) -> str:
    digest = _hmac_sha256_digest(value)
    token = base64.b32encode(digest).decode("utf-8").replace("=", "")
    token = (
        token.replace("2", "A")
        .replace("3", "B")
        .replace("4", "C")
        .replace("5", "D")
        .replace("6", "E")
        .replace("7", "F")
    )
    return token[:length].upper()


def sha256_hex(value: str) -> str:
    cleaned = _clean(value).encode("utf-8")
    return hashlib.sha256(cleaned).hexdigest()


def mask_account(value: str) -> str:
    s = _clean(value)
    if len(s) <= 4:
        return "*" * len(s)
    return ("*" * (len(s) - 4)) + s[-4:]

def hash_value(value: str | None, length: int = 64) -> str:
    """
    Generic secure hash helper used by privacy/erasure flows.
    Uses the same HMAC_SHA256_HEX_V1 scheme as identity lookup keys.
    """
    return _hmac_sha256_hex(value or "")[:length]