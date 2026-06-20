from __future__ import annotations

import hashlib
import hmac
import asyncio
import base64
import csv
import io
import json
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
from fastapi import HTTPException, status

from apps.api.settings import get_settings
from services.admin_audit_service import try_write_admin_audit
from utils.db import db_connection
from utils.metrics import partner_webhook_delivery_observe


DEFAULT_TOKEN_TTL_SECONDS = 3600
WEBHOOK_MAX_ATTEMPTS = 3
WEBHOOK_BACKOFF_SECONDS = 60
PROTECTED_SECRET_PREFIX = "enc:v1:"
MANAGED_SECRET_PREFIX = "kms:v1:"
DEAD_LETTER_EXPORT_FIELDS = [
    "delivery_id",
    "webhook_id",
    "client_id",
    "tenant_code",
    "event_type",
    "delivery_status",
    "attempt_count",
    "last_error",
    "created_at",
    "updated_at",
]


def _normalize_secret_provider(value: str | None) -> str:
    normalized = (value or "APPLICATION_KEY").strip().upper().replace("-", "_")
    if normalized in {"KMS", "MANAGED_KMS", "AWS_KMS"}:
        return "MANAGED_KMS"
    if normalized in {"APPLICATION_KEY", "APP_KEY", "LOCAL"}:
        return "APPLICATION_KEY"
    return normalized


def _normalize_kms_backend(value: str | None) -> str:
    normalized = (value or "LOCAL_ENVELOPE").strip().upper().replace("-", "_")
    if normalized in {"AWS", "AWS_KMS", "KMS"}:
        return "AWS_KMS"
    return "LOCAL_ENVELOPE"


def _secret_provider_status() -> dict[str, Any]:
    settings = get_settings()
    app_env = str(getattr(settings, "app_env", "") or "").lower()
    provider = _normalize_secret_provider(
        getattr(settings, "partner_webhook_secret_provider", None)
    )
    configured_key = bool(getattr(settings, "partner_webhook_secret_key", None))
    kms_key_id = getattr(settings, "partner_webhook_kms_key_id", None)
    kms_backend = _normalize_kms_backend(
        getattr(settings, "partner_webhook_kms_backend", None)
    )

    if provider == "MANAGED_KMS":
        if kms_key_id:
            config_status = "READY"
            recommended_action = "Managed KMS key reference is configured for webhook signing-secret protection."
            if kms_backend == "LOCAL_ENVELOPE" and app_env not in {
                "local",
                "dev",
                "test",
            }:
                config_status = "ATTENTION"
                recommended_action = (
                    "Set PARTNER_WEBHOOK_KMS_BACKEND=AWS_KMS before production so managed webhook "
                    "signing-secret protection uses the physical KMS provider."
                )
            return {
                "provider": "MANAGED_KMS",
                "protection_mode": "MANAGED_KMS",
                "config_status": config_status,
                "kms_key_configured": True,
                "kms_backend": kms_backend,
                "key_reference": str(kms_key_id),
                "recommended_action": recommended_action,
            }
        return {
            "provider": "MANAGED_KMS",
            "protection_mode": "MANAGED_KMS",
            "config_status": "ATTENTION",
            "kms_key_configured": False,
            "kms_backend": kms_backend,
            "key_reference": None,
            "recommended_action": "Configure PARTNER_WEBHOOK_KMS_KEY_ID before using managed KMS secret protection.",
        }

    if configured_key:
        return {
            "provider": "APPLICATION_KEY",
            "protection_mode": "APPLICATION_KEY",
            "config_status": "READY",
            "kms_key_configured": False,
            "kms_backend": None,
            "key_reference": None,
            "recommended_action": "Application-key protection is configured for webhook signing secrets.",
        }

    if app_env in {"local", "dev", "test"}:
        return {
            "provider": "APPLICATION_KEY",
            "protection_mode": "LOCAL_DEV_FALLBACK",
            "config_status": "READY",
            "kms_key_configured": False,
            "kms_backend": None,
            "key_reference": None,
            "recommended_action": "Local development fallback is active. Configure a real secret provider before production.",
        }

    return {
        "provider": "APPLICATION_KEY",
        "protection_mode": "UNCONFIGURED",
        "config_status": "ATTENTION",
        "kms_key_configured": False,
        "kms_backend": None,
        "key_reference": None,
        "recommended_action": "Configure PARTNER_WEBHOOK_SECRET_KEY or PARTNER_WEBHOOK_SECRET_PROVIDER=MANAGED_KMS with PARTNER_WEBHOOK_KMS_KEY_ID before production.",
    }


def _alert_notification_provider_status() -> dict[str, Any]:
    settings = get_settings()
    app_env = str(getattr(settings, "app_env", "") or "").lower()
    notification_url = getattr(settings, "partner_webhook_alert_notification_url", None)
    notification_secret = getattr(
        settings, "partner_webhook_alert_notification_secret", None
    )
    configured = bool(notification_url)

    if configured:
        return {
            "status": "READY",
            "provider": "WEBHOOK",
            "configured": True,
            "signed": bool(notification_secret),
            "recommended_action": (
                "Physical partner alert notification endpoint is configured."
                if notification_secret
                else "Configure PARTNER_WEBHOOK_ALERT_NOTIFICATION_SECRET if the production alert endpoint requires signed payloads."
            ),
        }

    if app_env in {"local", "dev", "test"}:
        return {
            "status": "READY",
            "provider": "IN_APP",
            "configured": False,
            "signed": False,
            "recommended_action": "In-app notification evidence is active for local and test environments.",
        }

    return {
        "status": "ATTENTION",
        "provider": "WEBHOOK",
        "configured": False,
        "signed": False,
        "recommended_action": "Configure PARTNER_WEBHOOK_ALERT_NOTIFICATION_URL before production alert notifications use a physical provider.",
    }


def get_partner_seam_production_readiness() -> dict[str, Any]:
    settings = get_settings()
    app_env = str(getattr(settings, "app_env", "") or "local")
    secret_status = _secret_provider_status()
    alert_status = _alert_notification_provider_status()
    code_checks = [
        {
            "code": "CLIENT_CREDENTIALS",
            "label": "OAuth-style client credentials",
            "status": "READY",
            "owner": "Partner Integration",
            "recommended_action": "Partners can self-onboard tenant-scoped clients and exchange credentials for bearer tokens.",
        },
        {
            "code": "OUTBOUND_WEBHOOKS",
            "label": "Outbound webhook subscriptions",
            "status": "READY",
            "owner": "Partner Integration",
            "recommended_action": "Partners can create HTTPS subscriptions and rotate signing secrets from a client-scoped session.",
        },
        {
            "code": "DELIVERY_OPERATIONS",
            "label": "Delivery queue, retry, dead-letter export",
            "status": "READY",
            "owner": "Amplifi Admin",
            "recommended_action": "Admin and partner users can inspect, export, and retry failed delivery evidence.",
        },
        {
            "code": "SECRET_PROTECTION",
            "label": "Webhook signing-secret protection",
            "status": secret_status["config_status"],
            "owner": "Platform Operations",
            "recommended_action": secret_status["recommended_action"],
        },
        {
            "code": "ALERT_NOTIFICATIONS",
            "label": "Partner delivery-failure notifications",
            "status": alert_status["status"],
            "owner": "Platform Operations",
            "recommended_action": alert_status["recommended_action"],
        },
    ]
    attention_count = sum(1 for item in code_checks if item["status"] == "ATTENTION")
    deployment_status = "ATTENTION" if attention_count else "READY"

    return {
        "status": "READY",
        "code_status": "READY",
        "deployment_status": deployment_status,
        "app_env": app_env,
        "attention_count": attention_count,
        "code_complete": True,
        "production_ready": deployment_status == "READY",
        "secret_provider": secret_status,
        "alert_notification_provider": alert_status,
        "checks": code_checks,
        "recommended_action": (
            "Partner Seam is code-complete; resolve deployment attention items before production cutover."
            if attention_count
            else "Partner Seam is code-complete and production configuration is ready."
        ),
    }


def _hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _secret_protection_key() -> bytes:
    settings = get_settings()
    provider = _normalize_secret_provider(
        getattr(settings, "partner_webhook_secret_provider", None)
    )
    key_material = getattr(settings, "partner_webhook_secret_key", None)
    kms_key_id = getattr(settings, "partner_webhook_kms_key_id", None)
    app_env = str(getattr(settings, "app_env", "") or "").lower()

    if provider == "MANAGED_KMS":
        key_material = key_material or kms_key_id

    if not key_material and app_env not in {"local", "dev", "test"}:
        raise RuntimeError(
            "PARTNER_WEBHOOK_SECRET_KEY or PARTNER_WEBHOOK_KMS_KEY_ID must be configured"
        )

    key_material = key_material or "local-dev-partner-webhook-secret-key"
    return hashlib.sha256(key_material.encode("utf-8")).digest()


def _keystream(*, key: bytes, nonce: bytes, length: int) -> bytes:
    output = bytearray()
    counter = 0
    while len(output) < length:
        output.extend(
            hmac.new(
                key,
                nonce + counter.to_bytes(4, "big"),
                hashlib.sha256,
            ).digest()
        )
        counter += 1
    return bytes(output[:length])


def _xor_bytes(left: bytes, right: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(left, right))


def _aws_kms_client():
    settings = get_settings()
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError(
            "boto3 is required for PARTNER_WEBHOOK_KMS_BACKEND=AWS_KMS"
        ) from exc

    region = getattr(settings, "aws_region", None)
    return boto3.client("kms", region_name=region) if region else boto3.client("kms")


def _protect_secret_with_aws_kms(value: str, *, key_id: str) -> str:
    response = _aws_kms_client().encrypt(KeyId=key_id, Plaintext=value.encode("utf-8"))
    ciphertext = base64.urlsafe_b64encode(response["CiphertextBlob"]).decode("ascii")
    payload = base64.urlsafe_b64encode(
        json.dumps(
            {
                "backend": "AWS_KMS",
                "ciphertext": ciphertext,
            },
            separators=(",", ":"),
        ).encode("utf-8")
    ).decode("ascii")
    return f"{MANAGED_SECRET_PREFIX}{payload}"


def _unprotect_secret_with_aws_kms(payload: dict[str, Any]) -> str:
    ciphertext = base64.urlsafe_b64decode(payload["ciphertext"].encode("ascii"))
    response = _aws_kms_client().decrypt(CiphertextBlob=ciphertext)
    return response["Plaintext"].decode("utf-8")


def _decode_managed_secret_payload(encoded: str) -> dict[str, Any] | None:
    raw = base64.urlsafe_b64decode(encoded.encode("ascii"))
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _protect_secret(value: str) -> str:
    provider = _secret_provider_status()
    settings = get_settings()
    if (
        provider["protection_mode"] == "MANAGED_KMS"
        and provider.get("kms_backend") == "AWS_KMS"
    ):
        kms_key_id = getattr(settings, "partner_webhook_kms_key_id", None)
        if not kms_key_id:
            raise RuntimeError("PARTNER_WEBHOOK_KMS_KEY_ID must be configured")
        return _protect_secret_with_aws_kms(value, key_id=str(kms_key_id))

    key = _secret_protection_key()
    nonce = secrets.token_bytes(16)
    plaintext = value.encode("utf-8")
    ciphertext = _xor_bytes(
        plaintext, _keystream(key=key, nonce=nonce, length=len(plaintext))
    )
    tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()[:16]
    payload = base64.urlsafe_b64encode(nonce + tag + ciphertext).decode("ascii")
    if provider["protection_mode"] == "MANAGED_KMS":
        return f"{MANAGED_SECRET_PREFIX}{payload}"
    return f"{PROTECTED_SECRET_PREFIX}{payload}"


def _unprotect_secret(value: str) -> str:
    if value.startswith(MANAGED_SECRET_PREFIX):
        encoded = value[len(MANAGED_SECRET_PREFIX) :]
        managed_payload = _decode_managed_secret_payload(encoded)
        if managed_payload and managed_payload.get("backend") == "AWS_KMS":
            return _unprotect_secret_with_aws_kms(managed_payload)
    elif value.startswith(PROTECTED_SECRET_PREFIX):
        encoded = value[len(PROTECTED_SECRET_PREFIX) :]
    else:
        return value

    key = _secret_protection_key()
    raw = base64.urlsafe_b64decode(encoded.encode("ascii"))
    nonce = raw[:16]
    tag = raw[16:32]
    ciphertext = raw[32:]
    expected_tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()[:16]
    if not hmac.compare_digest(tag, expected_tag):
        raise RuntimeError("Protected webhook signing secret failed integrity check")

    plaintext = _xor_bytes(
        ciphertext, _keystream(key=key, nonce=nonce, length=len(ciphertext))
    )
    return plaintext.decode("utf-8")


def _webhook_signature(*, signing_secret: str, timestamp: int, body: str) -> str:
    message = f"{timestamp}.{body}".encode("utf-8")
    return hmac.new(signing_secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def _normalize_scopes(scopes: list[str] | str | None) -> list[str]:
    if scopes is None:
        return []
    if isinstance(scopes, str):
        parts = scopes.replace(",", " ").split()
    else:
        parts = scopes
    return sorted({part.strip() for part in parts if part and part.strip()})


def _json(value: dict[str, Any] | None) -> str:
    return json.dumps(value or {}, default=str)


def _serialize(row: Any, *, include_secret: str | None = None) -> dict[str, Any]:
    result = {
        key: (
            value.isoformat()
            if isinstance(value, datetime)
            else str(value) if key.endswith("_id") else value
        )
        for key, value in dict(row).items()
        if key
        not in {
            "client_secret_hash",
            "signing_secret_hash",
            "signing_secret_value",
            "access_token_hash",
        }
    }

    if isinstance(result.get("metadata"), str):
        result["metadata"] = json.loads(result["metadata"])

    if include_secret is not None:
        result["client_secret"] = include_secret

    return result


async def create_partner_client(
    *,
    tenant_code: str,
    client_name: str,
    scopes: list[str] | str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_tenant = tenant_code.strip().upper()
    if not normalized_tenant:
        raise ValueError("tenant_code is required")

    client_id = f"{normalized_tenant.lower()}_{secrets.token_urlsafe(12)}"
    client_secret = secrets.token_urlsafe(32)
    normalized_scopes = _normalize_scopes(scopes)

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO partner_clients (
                client_id,
                tenant_code,
                client_name,
                client_secret_hash,
                scopes,
                metadata
            )
            VALUES ($1, $2, $3, $4, $5::text[], $6::jsonb)
            RETURNING *
            """,
            client_id,
            normalized_tenant,
            client_name.strip(),
            _hash_secret(client_secret),
            normalized_scopes,
            _json(metadata),
        )

    return _serialize(row, include_secret=client_secret)


async def create_partner_client_for_identity(
    *,
    identity: dict[str, Any],
    client_name: str,
    scopes: list[str] | str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tenant_code = identity.get("tenant_code") or identity.get("tenant")
    if not tenant_code:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Partner tenant scope is required",
        )
    if identity.get("client_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant-scoped partner session is required for client onboarding",
        )

    return await create_partner_client(
        tenant_code=str(tenant_code),
        client_name=client_name,
        scopes=scopes,
        metadata=metadata,
    )


async def list_partner_clients(
    *,
    tenant_code: str | None = None,
    status_filter: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    normalized_tenant = tenant_code.strip().upper() if tenant_code else None
    normalized_status = status_filter.strip().upper() if status_filter else None

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM partner_clients
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::text IS NULL OR status = $2)
            ORDER BY created_at DESC
            LIMIT $3
            """,
            normalized_tenant,
            normalized_status,
            limit,
        )

    return [_serialize(row) for row in rows]


async def list_webhook_subscriptions(
    *,
    tenant_code: str | None = None,
    client_id: str | None = None,
    status_filter: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    normalized_tenant = tenant_code.strip().upper() if tenant_code else None
    normalized_status = status_filter.strip().upper() if status_filter else None

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                webhook_id,
                client_id,
                tenant_code,
                event_type,
                target_url,
                status,
                metadata,
                created_at,
                updated_at
            FROM partner_webhook_subscriptions
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::text IS NULL OR client_id = $2)
              AND ($3::text IS NULL OR status = $3)
            ORDER BY created_at DESC
            LIMIT $4
            """,
            normalized_tenant,
            client_id,
            normalized_status,
            limit,
        )

    return [_serialize(row) for row in rows]


async def issue_client_credentials_token(
    *,
    client_id: str,
    client_secret: str,
    scope: list[str] | str | None = None,
    ttl_seconds: int = DEFAULT_TOKEN_TTL_SECONDS,
) -> dict[str, Any]:
    requested_scopes = _normalize_scopes(scope)

    async with db_connection() as conn:
        client = await conn.fetchrow(
            """
            SELECT *
            FROM partner_clients
            WHERE client_id = $1
            """,
            client_id,
        )

        if not client or client["status"] != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid client credentials",
            )

        if client["client_secret_hash"] != _hash_secret(client_secret):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid client credentials",
            )

        allowed_scopes = set(client["scopes"] or [])
        effective_scopes = requested_scopes or sorted(allowed_scopes)
        if not set(effective_scopes).issubset(allowed_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Requested scope is not allowed for this client",
            )

        access_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        await conn.execute(
            """
            INSERT INTO partner_access_tokens (
                access_token_hash,
                client_id,
                tenant_code,
                scopes,
                expires_at
            )
            VALUES ($1, $2, $3, $4::text[], $5)
            """,
            _hash_secret(access_token),
            client_id,
            client["tenant_code"],
            effective_scopes,
            expires_at,
        )

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": ttl_seconds,
        "scope": " ".join(effective_scopes),
        "tenant_code": client["tenant_code"],
    }


async def authenticate_partner_access_token(
    authorization: str | None,
) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token",
        )

    token = authorization.split(" ", 1)[1].strip()
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT token.client_id, token.tenant_code, token.scopes, client.status
            FROM partner_access_tokens token
            JOIN partner_clients client ON client.client_id = token.client_id
            WHERE token.access_token_hash = $1
              AND token.revoked_at IS NULL
              AND token.expires_at > NOW()
            """,
            _hash_secret(token),
        )

    if not row or row["status"] != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired bearer token",
        )

    return {
        "authenticated": True,
        "role": "PARTNER",
        "tenant_code": row["tenant_code"],
        "tenant": row["tenant_code"],
        "client_id": row["client_id"],
        "scopes": list(row["scopes"] or []),
    }


async def create_webhook_subscription(
    *,
    client_id: str,
    event_type: str,
    target_url: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not target_url.lower().startswith("https://"):
        raise ValueError("target_url must use https")

    signing_secret = secrets.token_urlsafe(32)

    async with db_connection() as conn:
        client = await conn.fetchrow(
            """
            SELECT client_id, tenant_code, status
            FROM partner_clients
            WHERE client_id = $1
            """,
            client_id,
        )
        if not client or client["status"] != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active partner client not found",
            )

        row = await conn.fetchrow(
            """
            INSERT INTO partner_webhook_subscriptions (
                client_id,
                tenant_code,
                event_type,
                target_url,
                signing_secret_value,
                signing_secret_hash,
                metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
            RETURNING *
            """,
            client_id,
            client["tenant_code"],
            event_type.strip().upper(),
            target_url.strip(),
            _protect_secret(signing_secret),
            _hash_secret(signing_secret),
            _json(metadata),
        )

    result = _serialize(row)
    result["signing_secret"] = signing_secret
    return result


def _require_client_scoped_partner(identity: dict[str, Any]) -> tuple[str, str]:
    tenant_code = identity.get("tenant_code") or identity.get("tenant")
    client_id = identity.get("client_id")
    if not tenant_code or not client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bearer partner client scope is required for this action",
        )
    return str(tenant_code).strip().upper(), str(client_id).strip()


async def create_partner_webhook_subscription(
    *,
    identity: dict[str, Any],
    event_type: str,
    target_url: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _tenant_code, client_id = _require_client_scoped_partner(identity)
    return await create_webhook_subscription(
        client_id=client_id,
        event_type=event_type,
        target_url=target_url,
        metadata=metadata,
    )


async def rotate_partner_webhook_signing_secret(
    *,
    identity: dict[str, Any],
    webhook_id: str,
) -> dict[str, Any]:
    tenant_code, client_id = _require_client_scoped_partner(identity)
    signing_secret = secrets.token_urlsafe(32)

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE partner_webhook_subscriptions
            SET signing_secret_value = $1,
                signing_secret_hash = $2,
                updated_at = NOW()
            WHERE webhook_id = $3::uuid
              AND client_id = $4
              AND tenant_code = $5
              AND status = 'ACTIVE'
            RETURNING *
            """,
            _protect_secret(signing_secret),
            _hash_secret(signing_secret),
            webhook_id,
            client_id,
            tenant_code,
        )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active webhook subscription not found for this partner client",
        )

    result = _serialize(row)
    result["signing_secret"] = signing_secret
    return result


async def rotate_partner_legacy_webhook_secrets(
    *,
    identity: dict[str, Any],
    limit: int = 25,
) -> dict[str, Any]:
    tenant_code = identity.get("tenant_code") or identity.get("tenant")
    client_id = identity.get("client_id")
    if not tenant_code:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Partner tenant scope is required",
        )

    normalized_tenant = str(tenant_code).strip().upper()
    protected_pattern = f"{PROTECTED_SECRET_PREFIX}%"
    managed_pattern = f"{MANAGED_SECRET_PREFIX}%"
    bounded_limit = max(1, min(limit, 100))

    async with db_connection() as conn:
        legacy_rows = await conn.fetch(
            """
            SELECT
                webhook_id,
                client_id,
                tenant_code,
                event_type,
                target_url,
                status
            FROM partner_webhook_subscriptions
            WHERE tenant_code = $1
              AND ($2::text IS NULL OR client_id = $2)
              AND signing_secret_value NOT LIKE $3
              AND signing_secret_value NOT LIKE $4
              AND status = 'ACTIVE'
            ORDER BY created_at ASC
            LIMIT $5
            """,
            normalized_tenant,
            client_id,
            protected_pattern,
            managed_pattern,
            bounded_limit,
        )

        rotated = []
        for legacy_row in legacy_rows:
            signing_secret = secrets.token_urlsafe(32)
            row = await conn.fetchrow(
                """
                UPDATE partner_webhook_subscriptions
                SET signing_secret_value = $1,
                    signing_secret_hash = $2,
                    updated_at = NOW()
                WHERE webhook_id = $3::uuid
                  AND tenant_code = $4
                  AND client_id = $5
                  AND status = 'ACTIVE'
                RETURNING *
                """,
                _protect_secret(signing_secret),
                _hash_secret(signing_secret),
                legacy_row["webhook_id"],
                legacy_row["tenant_code"],
                legacy_row["client_id"],
            )
            if row:
                serialized = _serialize(row)
                serialized["signing_secret"] = signing_secret
                rotated.append(serialized)

    return {
        "status": "rotated" if rotated else "noop",
        "tenant_code": normalized_tenant,
        "client_id": client_id,
        "rotated_count": len(rotated),
        "items": rotated,
        "guardrail": "Store returned signing_secret values securely. They are only returned once.",
    }


async def queue_webhook_deliveries(
    *,
    tenant_code: str,
    event_type: str,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    normalized_tenant = tenant_code.strip().upper()
    normalized_event = event_type.strip().upper()

    async with db_connection() as conn:
        subscriptions = await conn.fetch(
            """
            SELECT webhook_id, client_id
            FROM partner_webhook_subscriptions
            WHERE tenant_code = $1
              AND event_type = $2
              AND status = 'ACTIVE'
            """,
            normalized_tenant,
            normalized_event,
        )

        rows = []
        for subscription in subscriptions:
            row = await conn.fetchrow(
                """
                INSERT INTO partner_webhook_deliveries (
                    webhook_id,
                    client_id,
                    tenant_code,
                    event_type,
                    payload,
                    next_attempt_at
                )
                VALUES ($1, $2, $3, $4, $5::jsonb, NOW())
                RETURNING *
                """,
                subscription["webhook_id"],
                subscription["client_id"],
                normalized_tenant,
                normalized_event,
                _json(payload),
            )
            rows.append(row)

    return [_serialize(row) for row in rows]


async def get_webhook_delivery_summary(
    *,
    tenant_code: str | None = None,
    hours: int = 24,
) -> dict[str, Any]:
    normalized_tenant = tenant_code.strip().upper() if tenant_code else None

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT delivery_status, COUNT(*)::int AS count
            FROM partner_webhook_deliveries
            WHERE created_at >= NOW() - ($1::int * INTERVAL '1 hour')
              AND ($2::text IS NULL OR tenant_code = $2)
            GROUP BY delivery_status
            ORDER BY delivery_status
            """,
            hours,
            normalized_tenant,
        )

    counts = {row["delivery_status"]: int(row["count"] or 0) for row in rows}
    total = sum(counts.values())
    failed = counts.get("FAILED", 0)
    pending = counts.get("PENDING", 0)
    return {
        "window_hours": hours,
        "tenant_code": normalized_tenant,
        "total": total,
        "sent_count": counts.get("SENT", 0),
        "pending_count": pending,
        "failed_count": failed,
        "cancelled_count": counts.get("CANCELLED", 0),
        "status": "ATTENTION" if failed else "PENDING" if pending else "HEALTHY",
        "by_status": counts,
    }


async def get_partner_integration_overview(identity: dict[str, Any]) -> dict[str, Any]:
    tenant_code = identity.get("tenant_code") or identity.get("tenant")
    client_id = identity.get("client_id")
    if not tenant_code:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Partner tenant scope is required",
        )

    clients = await list_partner_clients(
        tenant_code=tenant_code,
        status_filter="ACTIVE",
        limit=25,
    )
    if client_id:
        clients = [client for client in clients if client.get("client_id") == client_id]

    webhooks = await list_webhook_subscriptions(
        tenant_code=tenant_code,
        client_id=client_id,
        limit=25,
    )
    deliveries = await list_webhook_deliveries(
        tenant_code=tenant_code,
        client_id=client_id,
        limit=25,
    )
    summary = await get_webhook_delivery_summary(
        tenant_code=tenant_code,
        hours=24,
    )
    exceptions = await list_partner_webhook_exceptions(identity=identity, limit=25)
    alerts = await get_partner_webhook_delivery_alerts(identity=identity, limit=25)
    secret_readiness = await get_partner_webhook_secret_readiness(identity=identity)
    production_readiness = get_partner_seam_production_readiness()

    return {
        "identity": {
            "tenant_code": tenant_code,
            "client_id": client_id,
            "role": identity.get("role"),
            "scopes": identity.get("scopes", []),
        },
        "clients": clients,
        "webhooks": webhooks,
        "deliveries": deliveries,
        "exceptions": exceptions,
        "alerts": alerts,
        "secret_readiness": secret_readiness,
        "production_readiness": production_readiness,
        "summary": summary,
        "guardrails": [
            "Client secrets and webhook signing secrets are never shown after creation.",
            "Failed deliveries need platform support or partner endpoint correction before retry.",
            "Partner API-key sessions are tenant scoped; bearer-token sessions are client scoped.",
        ],
    }


async def get_partner_webhook_secret_readiness(
    identity: dict[str, Any]
) -> dict[str, Any]:
    tenant_code = identity.get("tenant_code") or identity.get("tenant")
    client_id = identity.get("client_id")
    if not tenant_code:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Partner tenant scope is required",
        )

    provider_status = _secret_provider_status()
    protection_mode = str(provider_status["protection_mode"])
    config_status = str(provider_status["config_status"])

    normalized_tenant = str(tenant_code).strip().upper()
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                COUNT(*)::int AS total_subscriptions,
                COUNT(*) FILTER (
                    WHERE signing_secret_value LIKE $3
                       OR signing_secret_value LIKE $4
                )::int AS protected_subscriptions,
                COUNT(*) FILTER (
                    WHERE signing_secret_value NOT LIKE $3
                      AND signing_secret_value NOT LIKE $4
                )::int AS legacy_plaintext_subscriptions
            FROM partner_webhook_subscriptions
            WHERE tenant_code = $1
              AND ($2::text IS NULL OR client_id = $2)
            """,
            normalized_tenant,
            client_id,
            f"{PROTECTED_SECRET_PREFIX}%",
            f"{MANAGED_SECRET_PREFIX}%",
        )

    total = int(row["total_subscriptions"] or 0) if row else 0
    protected_count = int(row["protected_subscriptions"] or 0) if row else 0
    legacy_count = int(row["legacy_plaintext_subscriptions"] or 0) if row else 0
    rotation_status = "ATTENTION" if legacy_count else "READY"
    status_value = (
        "ATTENTION" if config_status == "ATTENTION" or legacy_count else "READY"
    )

    return {
        "status": status_value,
        "tenant_code": normalized_tenant,
        "client_id": client_id,
        "provider": provider_status["provider"],
        "protection_mode": protection_mode,
        "config_status": config_status,
        "kms_key_configured": provider_status["kms_key_configured"],
        "kms_backend": provider_status["kms_backend"],
        "key_reference": provider_status["key_reference"],
        "rotation_status": rotation_status,
        "total_subscriptions": total,
        "protected_subscriptions": protected_count,
        "legacy_plaintext_subscriptions": legacy_count,
        "recommended_action": (
            provider_status["recommended_action"]
            if config_status == "ATTENTION"
            else (
                "Rotate legacy webhook signing secrets so every active subscription uses protected storage."
                if legacy_count
                else provider_status["recommended_action"]
            )
        ),
    }


async def list_partner_webhook_exceptions(
    *,
    identity: dict[str, Any],
    limit: int = 100,
) -> list[dict[str, Any]]:
    tenant_code = identity.get("tenant_code") or identity.get("tenant")
    client_id = identity.get("client_id")
    if not tenant_code:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Partner tenant scope is required",
        )

    normalized_tenant = str(tenant_code).strip().upper()
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM partner_webhook_deliveries
            WHERE tenant_code = $1
              AND ($2::text IS NULL OR client_id = $2)
              AND delivery_status IN ('FAILED', 'CANCELLED')
            ORDER BY updated_at DESC, created_at DESC
            LIMIT $3
            """,
            normalized_tenant,
            client_id,
            limit,
        )

    return [_serialize(row) for row in rows]


async def get_partner_webhook_delivery_alerts(
    *,
    identity: dict[str, Any],
    limit: int = 100,
) -> list[dict[str, Any]]:
    tenant_code = identity.get("tenant_code") or identity.get("tenant")
    client_id = identity.get("client_id")
    if not tenant_code:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Partner tenant scope is required",
        )

    normalized_tenant = str(tenant_code).strip().upper()
    return await _get_partner_webhook_delivery_alerts(
        tenant_code=normalized_tenant,
        client_id=client_id,
        limit=limit,
    )


async def get_admin_partner_webhook_delivery_alerts(
    *,
    tenant_code: str | None = None,
    client_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    normalized_tenant = tenant_code.strip().upper() if tenant_code else None
    return await _get_partner_webhook_delivery_alerts(
        tenant_code=normalized_tenant,
        client_id=client_id,
        limit=limit,
    )


async def _get_partner_webhook_delivery_alerts(
    *,
    tenant_code: str | None,
    client_id: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                delivery.tenant_code,
                delivery.client_id,
                delivery.webhook_id,
                delivery.event_type,
                subscription.target_url,
                COUNT(DISTINCT delivery.delivery_id)::int AS failed_count,
                MAX(delivery.attempt_count)::int AS max_attempt_count,
                MAX(delivery.updated_at) AS last_failed_at,
                STRING_AGG(DISTINCT COALESCE(delivery.last_error, 'No error returned'), ' | ') AS failure_reasons,
                MAX(notification.created_at) AS last_notified_at,
                COUNT(DISTINCT notification.notification_id)::int AS notification_count,
                (
                    ARRAY_AGG(notification.notification_status ORDER BY notification.created_at DESC)
                    FILTER (WHERE notification.notification_id IS NOT NULL)
                )[1] AS last_notification_status
            FROM partner_webhook_deliveries delivery
            LEFT JOIN partner_webhook_subscriptions subscription
              ON subscription.webhook_id = delivery.webhook_id
            LEFT JOIN partner_webhook_alert_notifications notification
              ON notification.tenant_code = delivery.tenant_code
             AND notification.client_id = delivery.client_id
             AND notification.webhook_id = delivery.webhook_id
             AND notification.event_type = delivery.event_type
            WHERE ($1::text IS NULL OR delivery.tenant_code = $1)
              AND ($2::text IS NULL OR delivery.client_id = $2)
              AND delivery.delivery_status IN ('FAILED', 'CANCELLED')
            GROUP BY delivery.tenant_code, delivery.client_id, delivery.webhook_id, delivery.event_type, subscription.target_url
            HAVING COUNT(DISTINCT delivery.delivery_id) >= 1
            ORDER BY failed_count DESC, last_failed_at DESC
            LIMIT $3
            """,
            tenant_code,
            client_id,
            limit,
        )

    alerts = []
    for row in rows:
        item = _serialize(row)
        failed_count = int(item.get("failed_count") or 0)
        max_attempt_count = int(item.get("max_attempt_count") or 0)
        if failed_count >= 5 or max_attempt_count >= WEBHOOK_MAX_ATTEMPTS:
            severity = "CRITICAL"
        elif failed_count >= 2:
            severity = "WARNING"
        else:
            severity = "NOTICE"
        item["severity"] = severity
        item["recommended_action"] = (
            "Fix the endpoint or signing-secret handling, then retry the failed delivery."
            if severity == "NOTICE"
            else "Pause new webhook changes, fix the endpoint or signing-secret handling, export evidence if needed, then retry failed deliveries."
        )
        alerts.append(item)

    return alerts


async def notify_partner_webhook_delivery_alerts(
    *,
    tenant_code: str | None = None,
    client_id: str | None = None,
    limit: int = 25,
    channel: str = "IN_APP",
) -> dict[str, Any]:
    normalized_channel = channel.strip().upper()
    if normalized_channel not in {"IN_APP", "EMAIL", "SMS", "WEBHOOK"}:
        raise ValueError("Unsupported notification channel")
    settings = get_settings()
    notification_url = getattr(settings, "partner_webhook_alert_notification_url", None)
    notification_secret = getattr(
        settings, "partner_webhook_alert_notification_secret", None
    )

    alerts = await get_admin_partner_webhook_delivery_alerts(
        tenant_code=tenant_code,
        client_id=client_id,
        limit=limit,
    )

    notifications = []
    async with db_connection() as conn:
        for alert in alerts:
            severity = str(alert.get("severity") or "NOTICE")
            subject = f"{severity}: Partner webhook delivery failures"
            message = (
                f"{alert.get('event_type')} has {alert.get('failed_count')} failed or cancelled "
                f"deliveries for client {alert.get('client_id')}. Review endpoint handling, "
                "export evidence if needed, then retry failed rows."
            )
            metadata = {
                "failed_count": alert.get("failed_count"),
                "max_attempt_count": alert.get("max_attempt_count"),
                "target_url": alert.get("target_url"),
                "failure_reasons": alert.get("failure_reasons"),
            }
            notification_status = "SENT"
            if normalized_channel == "WEBHOOK":
                payload = {
                    "tenant_code": alert["tenant_code"],
                    "client_id": alert["client_id"],
                    "webhook_id": str(alert["webhook_id"]),
                    "event_type": alert["event_type"],
                    "severity": severity,
                    "subject": subject,
                    "message": message,
                    "metadata": metadata,
                }
                if not notification_url:
                    notification_status = "FAILED"
                    metadata["provider_error"] = (
                        "PARTNER_WEBHOOK_ALERT_NOTIFICATION_URL is not configured"
                    )
                else:
                    try:
                        response = await _post_alert_notification(
                            str(notification_url),
                            payload,
                            str(notification_secret) if notification_secret else None,
                        )
                        response_status = int(getattr(response, "status_code", 0) or 0)
                        metadata["provider_status"] = response_status
                        if not 200 <= response_status < 300:
                            notification_status = "FAILED"
                            metadata["provider_error"] = str(
                                getattr(response, "text", "") or ""
                            )[:300]
                    except Exception as exc:
                        notification_status = "FAILED"
                        metadata["provider_error"] = str(exc)[:300]
            row = await conn.fetchrow(
                """
                INSERT INTO partner_webhook_alert_notifications (
                    tenant_code,
                    client_id,
                    webhook_id,
                    event_type,
                    severity,
                    channel,
                    notification_status,
                    subject,
                    message,
                    metadata
                )
                VALUES ($1, $2, $3::uuid, $4, $5, $6, $7, $8, $9, $10::jsonb)
                RETURNING *
                """,
                alert["tenant_code"],
                alert["client_id"],
                alert["webhook_id"],
                alert["event_type"],
                severity,
                normalized_channel,
                notification_status,
                subject,
                message,
                _json(metadata),
            )
            notifications.append(_serialize(row))

    return {
        "status": "notified" if notifications else "noop",
        "channel": normalized_channel,
        "notified_count": len(notifications),
        "items": notifications,
        "guardrail": "Notification evidence is recorded for current failed or cancelled webhook delivery alerts.",
    }


def _csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str, separators=(",", ":"))
    return str(value)


async def export_partner_webhook_dead_letters(
    *,
    identity: dict[str, Any],
    limit: int = 500,
) -> dict[str, Any]:
    rows = await list_partner_webhook_exceptions(identity=identity, limit=limit)
    tenant_code = (
        str(identity.get("tenant_code") or identity.get("tenant") or "tenant")
        .strip()
        .lower()
    )
    client_id = identity.get("client_id")
    filename_scope = f"{tenant_code}-{client_id}" if client_id else tenant_code
    generated_at = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=DEAD_LETTER_EXPORT_FIELDS, extrasaction="ignore"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {field: _csv_value(row.get(field)) for field in DEAD_LETTER_EXPORT_FIELDS}
        )

    return {
        "filename": f"partner-webhook-dead-letters-{filename_scope}-{generated_at}.csv",
        "content_type": "text/csv",
        "count": len(rows),
        "csv": buffer.getvalue(),
        "guardrail": "Export contains failed and cancelled webhook delivery evidence only.",
    }


async def process_pending_webhook_deliveries(
    *,
    limit: int = 25,
    http_post=None,
) -> dict[str, Any]:
    post = http_post or _post_webhook

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                delivery.delivery_id,
                delivery.webhook_id,
                delivery.client_id,
                delivery.tenant_code,
                delivery.event_type,
                delivery.payload,
                delivery.attempt_count,
                subscription.target_url,
                subscription.signing_secret_value
            FROM partner_webhook_deliveries delivery
            JOIN partner_webhook_subscriptions subscription
              ON subscription.webhook_id = delivery.webhook_id
            WHERE delivery.delivery_status = 'PENDING'
              AND subscription.status = 'ACTIVE'
              AND (delivery.next_attempt_at IS NULL OR delivery.next_attempt_at <= NOW())
            ORDER BY delivery.created_at ASC
            LIMIT $1
            """,
            limit,
        )

        results = []
        for row in rows:
            result = await _deliver_webhook_row(conn=conn, row=row, http_post=post)
            results.append(result)

    return {
        "status": "processed",
        "processed_count": len(results),
        "sent_count": sum(1 for item in results if item["delivery_status"] == "SENT"),
        "pending_count": sum(
            1 for item in results if item["delivery_status"] == "PENDING"
        ),
        "failed_count": sum(
            1 for item in results if item["delivery_status"] == "FAILED"
        ),
        "items": results,
    }


async def mark_webhook_delivery_for_retry(
    *,
    delivery_id: str,
    identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE partner_webhook_deliveries
            SET delivery_status = 'PENDING',
                next_attempt_at = NOW(),
                last_error = NULL,
                updated_at = NOW()
            WHERE delivery_id = $1::uuid
              AND delivery_status IN ('FAILED', 'CANCELLED')
            RETURNING *
            """,
            delivery_id,
        )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retryable webhook delivery not found",
        )

    delivery = _serialize(row)
    await try_write_admin_audit(
        action_type="PARTNER_WEBHOOK_DELIVERY_RETRY",
        action_domain="PARTNER_WEBHOOK",
        action_status="SUCCESS",
        identity=identity,
        tenant_code=delivery.get("tenant_code"),
        target_type="partner_webhook_delivery",
        target_id=str(delivery.get("delivery_id")),
        metadata={
            "client_id": delivery.get("client_id"),
            "webhook_id": str(delivery.get("webhook_id")),
            "retry_scope": "admin",
        },
    )
    return delivery


async def mark_partner_webhook_delivery_for_retry(
    *,
    identity: dict[str, Any],
    delivery_id: str,
) -> dict[str, Any]:
    tenant_code, client_id = _require_client_scoped_partner(identity)

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE partner_webhook_deliveries
            SET delivery_status = 'PENDING',
                next_attempt_at = NOW(),
                last_error = NULL,
                updated_at = NOW()
            WHERE delivery_id = $1::uuid
              AND tenant_code = $2
              AND client_id = $3
              AND delivery_status IN ('FAILED', 'CANCELLED')
            RETURNING *
            """,
            delivery_id,
            tenant_code,
            client_id,
        )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retryable webhook delivery not found for this partner client",
        )

    delivery = _serialize(row)
    await try_write_admin_audit(
        action_type="PARTNER_WEBHOOK_DELIVERY_RETRY",
        action_domain="PARTNER_WEBHOOK",
        action_status="SUCCESS",
        identity=identity,
        tenant_code=delivery.get("tenant_code"),
        target_type="partner_webhook_delivery",
        target_id=str(delivery.get("delivery_id")),
        metadata={
            "client_id": delivery.get("client_id"),
            "webhook_id": str(delivery.get("webhook_id")),
            "retry_scope": "partner",
        },
    )
    return delivery


async def _deliver_webhook_row(*, conn, row: Any, http_post) -> dict[str, Any]:
    payload = row["payload"]
    body = (
        payload
        if isinstance(payload, str)
        else json.dumps(payload or {}, default=str, separators=(",", ":"))
    )
    timestamp = int(time.time())
    signature = _webhook_signature(
        signing_secret=_unprotect_secret(row["signing_secret_value"]),
        timestamp=timestamp,
        body=body,
    )
    attempt_no = int(row["attempt_count"] or 0) + 1

    headers = {
        "Content-Type": "application/json",
        "X-Amplifi-Webhook-Id": str(row["webhook_id"]),
        "X-Amplifi-Delivery-Id": str(row["delivery_id"]),
        "X-Amplifi-Event-Type": row["event_type"],
        "X-Amplifi-Timestamp": str(timestamp),
        "X-Amplifi-Signature": signature,
    }

    try:
        started_at = time.perf_counter()
        response = await http_post(row["target_url"], body, headers)
        response_status = int(getattr(response, "status_code", 0) or 0)
        response_text = str(getattr(response, "text", "") or "")
    except Exception as exc:
        response_status = 0
        response_text = str(exc)
    finally:
        latency_seconds = time.perf_counter() - started_at

    sent = 200 <= response_status < 300
    retryable = response_status == 0 or response_status == 429 or response_status >= 500
    can_retry = retryable and attempt_no < WEBHOOK_MAX_ATTEMPTS

    if sent:
        delivery_status = "SENT"
        next_attempt_at = None
        last_error = None
        delivered_at_sql = "NOW()"
    elif can_retry:
        delivery_status = "PENDING"
        next_attempt_at = f"{WEBHOOK_BACKOFF_SECONDS * attempt_no} seconds"
        last_error = f"HTTP {response_status}: {response_text[:300]}"
        delivered_at_sql = "NULL"
    else:
        delivery_status = "FAILED"
        next_attempt_at = None
        last_error = f"HTTP {response_status}: {response_text[:300]}"
        delivered_at_sql = "NULL"

    updated = await conn.fetchrow(
        f"""
        UPDATE partner_webhook_deliveries
        SET delivery_status = $1,
            attempt_count = $2,
            last_error = $3,
            next_attempt_at = CASE
                WHEN $4::text IS NULL THEN NULL
                ELSE NOW() + ($4::text)::interval
            END,
            delivered_at = {delivered_at_sql},
            updated_at = NOW()
        WHERE delivery_id = $5
        RETURNING *
        """,
        delivery_status,
        attempt_no,
        last_error,
        next_attempt_at,
        row["delivery_id"],
    )

    result = _serialize(updated)
    result["http_status"] = response_status
    partner_webhook_delivery_observe(
        tenant=row["tenant_code"],
        client_id=row["client_id"],
        event_type=row["event_type"],
        delivery_status=delivery_status,
        http_status=response_status,
        latency_seconds=latency_seconds,
    )
    return result


async def _post_webhook(url: str, body: str, headers: dict[str, str]):
    return await asyncio.to_thread(
        requests.post,
        url,
        data=body,
        headers=headers,
        timeout=10,
    )


async def _post_alert_notification(
    url: str, payload: dict[str, Any], secret: str | None
):
    body = json.dumps(payload, default=str, separators=(",", ":"))
    headers = {
        "Content-Type": "application/json",
        "X-Amplifi-Notification-Type": "partner_webhook_delivery_alert",
    }
    if secret:
        headers["X-Amplifi-Signature"] = hmac.new(
            secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    return await asyncio.to_thread(
        requests.post,
        url,
        data=body,
        headers=headers,
        timeout=10,
    )


async def list_webhook_deliveries(
    *,
    tenant_code: str | None = None,
    client_id: str | None = None,
    delivery_status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    normalized_tenant = tenant_code.strip().upper() if tenant_code else None
    normalized_status = delivery_status.strip().upper() if delivery_status else None

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM partner_webhook_deliveries
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::text IS NULL OR client_id = $2)
              AND ($3::text IS NULL OR delivery_status = $3)
            ORDER BY created_at DESC
            LIMIT $4
            """,
            normalized_tenant,
            client_id,
            normalized_status,
            limit,
        )

    return [_serialize(row) for row in rows]
