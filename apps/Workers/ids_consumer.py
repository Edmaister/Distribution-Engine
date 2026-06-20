"""Hogan/IDS enterprise event inbox consumer.

Stores raw enterprise events, normalizes qualifying events into platform progress
events, and queues them for the journey worker.
"""

from __future__ import annotations

import datetime
import hashlib
import inspect
import json
from typing import Any

from services.journey_definitions import (
    DEFAULT_JOURNEY_CODE,
    DEFAULT_JOURNEY_VERSION,
    JOURNEY_DEFINITIONS,
    get_journey_definition,
)
from services.vertical_identifier_service import validate_event_identifiers
from utils.db import get_async_connection
from utils.metrics import enterprise_event_ingested_inc
from utils.queue import enqueue_event


IDS_PROGRESS_EVENT_MAPPING = {
    "ACCOUNT_ACTIVATED": "ACCOUNT_ACTIVATED",
    "DEBIT_ORDER_SWITCHED": "DEBIT_ORDER_SWITCHED",
    "SALARY_DEPOSIT": "SALARY_SWITCHED",
    "SALARY_SWITCHED": "SALARY_SWITCHED",
    "POLICY_ACTIVATED": "POLICY_ISSUED",
    "QUOTE_CREATED": "QUOTE_REQUESTED",
    "QUOTE_REQUESTED": "QUOTE_REQUESTED",
    "QUOTE_ACCEPTED": "QUOTE_ACCEPTED",
    "POLICY_ISSUED": "POLICY_ISSUED",
    "FIRST_PREMIUM_PAID": "FIRST_PREMIUM_PAID",
}


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    return str(value)


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    )


def _payload_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _normalise_source_system(evt: dict[str, Any]) -> str:
    source = evt.get("source") or evt.get("sourceSystem") or evt.get("source_system") or "IDS"
    return str(source).strip().upper() or "IDS"


def _source_event_id(evt: dict[str, Any]) -> str | None:
    value = evt.get("sourceEventId") or evt.get("source_event_id") or evt.get("eventId")
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _tenant_code(evt: dict[str, Any]) -> str | None:
    value = evt.get("tenant") or evt.get("tenantCode") or evt.get("tenant_code")
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _normalise_journey_code(evt: dict[str, Any]) -> str | None:
    value = evt.get("journeyCode") or evt.get("journey_code")
    if value is None:
        return None
    cleaned = str(value).strip().upper()
    return cleaned or None


def _normalise_journey_version(evt: dict[str, Any]) -> str:
    value = evt.get("journeyVersion") or evt.get("journey_version") or "v1"
    cleaned = str(value).strip()
    return cleaned or "v1"


def _occurred_at(evt: dict[str, Any]) -> Any:
    value = evt.get("occurredAt") or evt.get("occurred_at")
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            try:
                return datetime.datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
            except ValueError:
                return datetime.datetime.utcnow()
    return value or datetime.datetime.utcnow()


def _dedupe_key(*, source_system: str, source_event_id: str | None, payload_hash: str) -> str:
    raw_key = f"{source_system}|{source_event_id}" if source_event_id else f"{source_system}|{payload_hash}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _supported_events_for_definition(journey_definition) -> set[str]:
    return set(journey_definition.core_sequence) | set(journey_definition.event_to_timestamp_field)


def _resolve_progress_routing(evt: dict[str, Any]) -> tuple[str, str, str] | None:
    source_event_type = str(evt.get("eventType") or "").strip().upper()
    progress_event_type = str(
        evt.get("progressEventType")
        or evt.get("progress_event_type")
        or IDS_PROGRESS_EVENT_MAPPING.get(source_event_type)
        or source_event_type
    ).strip().upper()

    if not progress_event_type:
        return None

    requested_journey_code = _normalise_journey_code(evt)
    requested_journey_version = _normalise_journey_version(evt)

    if requested_journey_code:
        try:
            journey_definition = get_journey_definition(requested_journey_code, requested_journey_version)
        except ValueError:
            return None
        if progress_event_type in _supported_events_for_definition(journey_definition):
            return progress_event_type, requested_journey_code, requested_journey_version
        return None

    matches: list[tuple[str, str]] = []
    for key, journey_definition in JOURNEY_DEFINITIONS.items():
        if progress_event_type in _supported_events_for_definition(journey_definition):
            journey_code, journey_version = key.split(":", 1)
            matches.append((journey_code, journey_version))

    if len(matches) == 1:
        journey_code, journey_version = matches[0]
        return progress_event_type, journey_code, journey_version

    if (DEFAULT_JOURNEY_CODE, DEFAULT_JOURNEY_VERSION) in matches:
        return progress_event_type, DEFAULT_JOURNEY_CODE, DEFAULT_JOURNEY_VERSION

    return None


def _build_progress_event(
    *,
    evt: dict[str, Any],
    source_system: str,
    source_event_id: str | None,
    occurred_at: Any,
    tenant_code: str,
    dedupe_key: str,
) -> dict[str, Any] | None:
    event_type = evt.get("eventType")
    progress_routing = _resolve_progress_routing(evt)
    referral_track_id = evt.get("referralTrackId") or evt.get("referral_track_id")

    if not progress_routing or not referral_track_id:
        return None

    progress_event_type, journey_code, journey_version = progress_routing
    identifiers_ok, _identifier_errors = validate_event_identifiers(
        journey_code=journey_code,
        journey_version=journey_version,
        event_type=progress_event_type,
        payload=evt,
    )
    if not identifiers_ok:
        return None

    return {
        **evt,
        "eventType": "REFERRAL_PROGRESS_RECORDED",
        "progressEventType": progress_event_type,
        "journeyCode": journey_code,
        "journeyVersion": journey_version,
        "sourceEventType": event_type,
        "sourceSystem": source_system,
        "sourceEventId": source_event_id,
        "correlationId": evt.get("correlationId") or evt.get("correlation_id") or referral_track_id,
        "tenantCode": tenant_code,
        "referralTrackId": referral_track_id,
        "occurredAt": occurred_at,
        "dedupeKey": dedupe_key,
    }


async def _maybe_enqueue(payload: dict[str, Any]) -> None:
    result = enqueue_event(payload)
    if inspect.isawaitable(result):
        await result


def _record_ingest_metric(
    *,
    source_system: str,
    event_type: str,
    processing_status: str,
) -> None:
    try:
        enterprise_event_ingested_inc(
            source_system=source_system,
            event_type=event_type,
            processing_status=processing_status,
        )
    except Exception:
        return


async def ingest_event(evt: dict[str, Any]) -> dict[str, Any]:
    occurred_at = _occurred_at(evt)
    source_system = _normalise_source_system(evt)
    source_event_id = _source_event_id(evt)
    tenant_code = _tenant_code(evt)
    event_type = str(evt.get("eventType") or "")
    referral_track_id = evt.get("referralTrackId") or evt.get("referral_track_id")
    payload_hash = _payload_hash(evt)
    dedupe_key = _dedupe_key(
        source_system=source_system,
        source_event_id=source_event_id,
        payload_hash=payload_hash,
    )

    progress_event = (
        _build_progress_event(
            evt=evt,
            source_system=source_system,
            source_event_id=source_event_id,
            occurred_at=occurred_at,
            tenant_code=tenant_code,
            dedupe_key=dedupe_key,
        )
        if tenant_code
        else None
    )

    status = "QUEUED" if progress_event else "IGNORED"
    error_message = None if progress_event else "Event is not eligible for referral progress routing"

    async with get_async_connection() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO enterprise_event_inbox (
                    tenant_code,
                    source_system,
                    source_event_id,
                    correlation_id,
                    referral_track_id,
                    event_type,
                    occurred_at,
                    raw_payload,
                    normalized_payload,
                    payload_hash,
                    dedupe_key,
                    processing_status,
                    processed_at,
                    error_message
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7,
                    $8::jsonb, $9::jsonb, $10, $11, $12,
                    CASE WHEN $12 IN ('QUEUED', 'IGNORED') THEN NOW() ELSE NULL END,
                    $13
                )
                ON CONFLICT (dedupe_key) DO NOTHING
                RETURNING inbox_event_id
                """,
                tenant_code,
                source_system,
                source_event_id,
                evt.get("correlationId") or evt.get("correlation_id") or referral_track_id,
                referral_track_id,
                event_type,
                occurred_at,
                json.dumps(evt, default=_json_default),
                json.dumps(progress_event, default=_json_default) if progress_event else None,
                payload_hash,
                dedupe_key,
                status,
                error_message,
            )

    if not row:
        _record_ingest_metric(
            source_system=source_system,
            event_type=event_type,
            processing_status="DUPLICATE",
        )
        return {
            "status": "duplicate",
            "processingStatus": "DUPLICATE",
            "eventType": event_type,
            "dedupeKey": dedupe_key,
            "queued": False,
        }

    if progress_event:
        try:
            await _maybe_enqueue(progress_event)
        except Exception as exc:
            async with get_async_connection() as conn:
                await conn.execute(
                    """
                    UPDATE enterprise_event_inbox
                    SET processing_status = 'FAILED',
                        error_message = $2,
                        updated_at = NOW()
                    WHERE dedupe_key = $1
                    """,
                    dedupe_key,
                    str(exc),
                )
            _record_ingest_metric(
                source_system=source_system,
                event_type=event_type,
                processing_status="FAILED",
            )
            raise

    _record_ingest_metric(
        source_system=source_system,
        event_type=event_type,
        processing_status=status,
    )

    return {
        "status": "ok",
        "processingStatus": status,
        "eventType": event_type,
        "progressEventType": progress_event.get("progressEventType") if progress_event else None,
        "journeyCode": progress_event.get("journeyCode") if progress_event else None,
        "journeyVersion": progress_event.get("journeyVersion") if progress_event else None,
        "dedupeKey": dedupe_key,
        "queued": bool(progress_event),
    }
