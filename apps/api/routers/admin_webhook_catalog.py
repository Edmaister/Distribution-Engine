from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from services.webhook_event_catalog import EVENT_FAMILIES, list_catalog_events
from services.webhook_payload_builder import build_webhook_payload_envelope
from utils.security import require_session_key

router = APIRouter(
    prefix="/admin/webhooks",
    tags=["Admin Webhook Catalog"],
)

WEBHOOK_CATALOG_SCHEMA_VERSION = "2026-06-22"
WEBHOOK_CATALOG_ADMIN_ROLES = {
    "ADMIN",
    "SYSTEM_ADMIN",
    "PLATFORM_ADMIN",
}
PAYLOAD_PREVIEW_FAMILIES = {"campaign", "outcome"}


def _require_webhook_catalog_admin(identity: dict[str, Any]) -> dict[str, Any]:
    role = str(identity.get("role") or "").upper()
    if role not in WEBHOOK_CATALOG_ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": "API key is not authorised for webhook catalog access.",
            },
        )
    return identity


def _catalog_families() -> list[str]:
    return sorted(set(EVENT_FAMILIES.values()))


def _normalise_family(family: str | None) -> str | None:
    if family is None or not family.strip():
        return None

    resolved = family.strip().lower()
    if resolved not in _catalog_families():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": f"Unsupported webhook event family: {family}",
            },
        )
    return resolved


def _group_by_family(events: list[dict[str, str]]) -> dict[str, list[str]]:
    grouped = {family: [] for family in _catalog_families()}
    for event in events:
        grouped[event["family"]].append(event["event_type"])
    return {
        family: sorted(event_types)
        for family, event_types in grouped.items()
        if event_types
    }


def _preview_subject_type(event_family: str) -> str:
    if event_family == "campaign":
        return "campaign"
    if event_family == "outcome":
        return "outcome"
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "code": "validation_error",
            "message": (
                "Webhook payload preview only supports campaign and outcome events."
            ),
        },
    )


@router.get("/event-catalog")
async def get_admin_webhook_event_catalog(
    family: str | None = Query(default=None),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_webhook_catalog_admin(identity)
    resolved_family = _normalise_family(family)
    events = list_catalog_events()
    if resolved_family:
        events = [event for event in events if event.get("family") == resolved_family]

    return {
        "status": "ok",
        "catalog": {
            "schema_version": WEBHOOK_CATALOG_SCHEMA_VERSION,
            "family_filter": resolved_family,
            "families": _catalog_families(),
            "event_count": len(events),
            "events": events,
            "events_by_family": _group_by_family(events),
        },
        "guardrail": (
            "Read-only webhook event catalog. This endpoint does not validate "
            "subscriptions, dispatch, queue, sign, retry, replay, deliver, "
            "persist webhook records, or build webhook payloads."
        ),
    }


@router.get("/payload-preview")
async def preview_admin_webhook_payload(
    event_type: str = Query(..., min_length=1),
    external_tenant_ref: str = Query(..., min_length=1),
    subject_id: str = Query(..., min_length=1),
    correlation_id: str | None = Query(default=None),
    source_event_id: str | None = Query(default=None),
    idempotency_key: str | None = Query(default=None),
    redactions: list[str] | None = Query(default=None),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_webhook_catalog_admin(identity)

    resolved_event_type = event_type.strip()
    event_family = EVENT_FAMILIES.get(resolved_event_type)
    if event_family not in PAYLOAD_PREVIEW_FAMILIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": (
                    "Webhook payload preview only supports campaign and outcome "
                    "events."
                ),
            },
        )

    correlation = {
        key: value
        for key, value in {
            "correlation_id": correlation_id,
            "source_event_id": source_event_id,
        }.items()
        if value is not None and value.strip()
    }

    try:
        envelope = build_webhook_payload_envelope(
            event_type=resolved_event_type,
            external_tenant_ref=external_tenant_ref,
            subject={
                "type": _preview_subject_type(event_family),
                "id": subject_id,
            },
            correlation=correlation,
            metadata={
                "preview": True,
                "delivery": "none",
                "surface": "admin_webhook_payload_preview",
            },
            redactions=redactions,
            idempotency_key=idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": str(exc),
            },
        ) from exc

    return {
        "status": "ok",
        "delivery_mode": "preview_only",
        "payload": envelope,
        "guardrail": (
            "Non-delivering webhook payload preview. This endpoint does not "
            "dispatch, queue, sign, retry, replay, deliver, persist webhook "
            "records, or build partner deliveries."
        ),
    }
