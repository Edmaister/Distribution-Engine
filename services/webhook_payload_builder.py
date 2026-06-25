from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Final
from uuid import uuid4

from services.webhook_event_catalog import validate_event_type

WEBHOOK_PAYLOAD_SCHEMA_VERSION: Final = "2026-06-22"
UNSAFE_PAYLOAD_FIELD_PARTS: Final[tuple[str, ...]] = (
    "ACCESS_TOKEN",
    "AUDIT_PAYLOAD",
    "CLIENT_SECRET",
    "DLQ_PAYLOAD",
    "PASSWORD",
    "PARTNER_WEBHOOK_DELIVERIES",
    "PARTNER_WEBHOOK_SUBSCRIPTIONS",
    "PROVIDER_PAYLOAD",
    "RAW",
    "SECRET",
    "SIGNING",
    "TENANT_CODE",
    "TOKEN",
    "UCN",
)


def build_webhook_payload_envelope(
    *,
    event_type: object,
    external_tenant_ref: str,
    subject: Mapping[str, Any],
    data: Mapping[str, Any] | None = None,
    correlation: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
    source: Mapping[str, Any] | None = None,
    redactions: Sequence[str] | None = None,
    event_id: str | None = None,
    idempotency_key: str | None = None,
    occurred_at: datetime | str | None = None,
    strict_event_type: bool = True,
) -> dict[str, Any]:
    event = validate_event_type(event_type, strict=strict_event_type)
    if event["valid"] is not True:
        raise ValueError(str(event["message"]))

    tenant_ref = _required_text(
        external_tenant_ref,
        "external_tenant_ref is required for webhook payloads.",
    )
    safe_subject = _safe_mapping(subject, path="subject")
    if not safe_subject.get("type") or not safe_subject.get("id"):
        raise ValueError("subject.type and subject.id are required.")

    stable_event_id = _optional_text(event_id) or _optional_text(idempotency_key)
    safe_correlation = _safe_mapping(correlation or {}, path="correlation")
    if idempotency_key and not safe_correlation.get("idempotency_key"):
        safe_correlation["idempotency_key"] = idempotency_key.strip()

    envelope: dict[str, Any] = {
        "event_id": stable_event_id or str(uuid4()),
        "event_type": event["event_type"],
        "event_family": event["family"],
        "schema_version": WEBHOOK_PAYLOAD_SCHEMA_VERSION,
        "occurred_at": _format_occurred_at(occurred_at),
        "tenant": {
            "external_tenant_ref": tenant_ref,
        },
        "subject": safe_subject,
        "correlation": safe_correlation,
        "data": _safe_mapping(data or {}, path="data"),
        "metadata": _safe_mapping(metadata or {}, path="metadata"),
        "redactions": _safe_redactions(redactions),
    }

    if source:
        envelope["source"] = _safe_mapping(source, path="source")

    return envelope


def _required_text(value: object, message: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(message)
    return normalized


def _optional_text(value: object) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _format_occurred_at(value: datetime | str | None) -> str:
    if value is None:
        value = datetime.now(timezone.utc)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    normalized = value.strip()
    if not normalized:
        raise ValueError("occurred_at must not be blank.")
    return normalized


def _safe_mapping(value: Mapping[str, Any], *, path: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be an object.")
    return {
        str(key): _safe_value(item, path=f"{path}.{key}")
        for key, item in value.items()
        if _validate_safe_key(str(key), path=f"{path}.{key}")
    }


def _safe_sequence(value: Sequence[Any], *, path: str) -> list[Any]:
    return [
        _safe_value(item, path=f"{path}[{index}]") for index, item in enumerate(value)
    ]


def _safe_value(value: Any, *, path: str) -> Any:
    if isinstance(value, Mapping):
        return _safe_mapping(value, path=path)
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return _safe_sequence(value, path=path)
    if isinstance(value, (bytes, bytearray)):
        raise ValueError(f"{path} must not contain binary payload data.")
    return value


def _validate_safe_key(key: str, *, path: str) -> bool:
    normalized = key.strip().upper().replace("-", "_")
    if not normalized:
        raise ValueError(f"{path} must not be blank.")
    if any(part in normalized for part in UNSAFE_PAYLOAD_FIELD_PARTS):
        raise ValueError(
            "Webhook payload fields must not expose internal, secret, raw, or "
            "private identifiers."
        )
    return True


def _safe_redactions(redactions: Sequence[str] | None) -> list[str]:
    if redactions is None:
        return []
    return sorted({str(item).strip() for item in redactions if str(item).strip()})
