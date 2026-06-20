from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from apps.core.logging_utils import log_event
from utils.db import get_async_connection
from utils.metrics import enterprise_event_inbox_current_set, enterprise_event_replay_inc
from utils.queue import enqueue_event


def _json_payload(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else None
    return dict(value)


def _record_replay_metric(*, event_type: str | None, status: str) -> None:
    try:
        enterprise_event_replay_inc(event_type=event_type, status=status)
    except Exception:
        return


def _set_inbox_current_metric(*, processing_status: str | None, value: int) -> None:
    try:
        enterprise_event_inbox_current_set(
            processing_status=processing_status,
            value=value,
        )
    except Exception:
        return


async def get_enterprise_event_summary() -> Dict[str, Any]:
    async with get_async_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT processing_status, COUNT(*) AS event_count
            FROM enterprise_event_inbox
            GROUP BY processing_status
            ORDER BY processing_status
            """
        )

    items = [
        {
            "processingStatus": row["processing_status"],
            "eventCount": int(row["event_count"] or 0),
        }
        for row in rows
    ]

    for item in items:
        _set_inbox_current_metric(
            processing_status=item["processingStatus"],
            value=item["eventCount"],
        )

    return {
        "status": "ok",
        "total": sum(item["eventCount"] for item in items),
        "items": items,
    }


async def list_enterprise_events(
    *,
    processing_status: Optional[str] = None,
    source_system: Optional[str] = None,
    referral_track_id: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    sql = """
        SELECT
            inbox_event_id,
            tenant_code,
            source_system,
            source_event_id,
            correlation_id,
            referral_track_id::text AS referral_track_id,
            event_type,
            occurred_at,
            received_at,
            processing_status,
            processed_at,
            error_message,
            normalized_payload IS NOT NULL AS has_normalized_payload
        FROM enterprise_event_inbox
        WHERE 1=1
    """

    params: list[Any] = []

    if processing_status:
        params.append(processing_status)
        sql += f" AND processing_status = ${len(params)}"

    if source_system:
        params.append(source_system)
        sql += f" AND source_system = ${len(params)}"

    if referral_track_id:
        params.append(referral_track_id)
        sql += f" AND referral_track_id = ${len(params)}"

    params.append(limit)
    sql += f" ORDER BY received_at DESC LIMIT ${len(params)}"

    async with get_async_connection() as conn:
        rows = await conn.fetch(sql, *params)

    items = [
        {
            "inboxEventId": str(row["inbox_event_id"]),
            "tenantCode": row["tenant_code"],
            "sourceSystem": row["source_system"],
            "sourceEventId": row["source_event_id"],
            "correlationId": row["correlation_id"],
            "referralTrackId": row["referral_track_id"],
            "eventType": row["event_type"],
            "occurredAt": row["occurred_at"],
            "receivedAt": row["received_at"],
            "processingStatus": row["processing_status"],
            "processedAt": row["processed_at"],
            "errorMessage": row["error_message"],
            "hasNormalizedPayload": bool(row["has_normalized_payload"]),
        }
        for row in rows
    ]

    return {
        "status": "ok",
        "count": len(items),
        "items": items,
    }


async def get_enterprise_event_dashboard(
    *,
    tenant_code: Optional[str] = None,
    days: int = 7,
    problem_limit: int = 25,
) -> Dict[str, Any]:
    params: list[Any] = []
    tenant_filter = ""

    if tenant_code:
        params.append(tenant_code)
        tenant_filter = f" AND tenant_code = ${len(params)}"

    params.append(days)
    days_placeholder = f"${len(params)}"

    async with get_async_connection() as conn:
        status_rows = await conn.fetch(
            f"""
            SELECT processing_status, COUNT(*) AS event_count
            FROM enterprise_event_inbox
            WHERE received_at >= NOW() - ({days_placeholder}::int * INTERVAL '1 day')
            {tenant_filter}
            GROUP BY processing_status
            ORDER BY processing_status
            """,
            *params,
        )

        source_rows = await conn.fetch(
            f"""
            SELECT source_system, COUNT(*) AS event_count
            FROM enterprise_event_inbox
            WHERE received_at >= NOW() - ({days_placeholder}::int * INTERVAL '1 day')
            {tenant_filter}
            GROUP BY source_system
            ORDER BY event_count DESC, source_system
            """,
            *params,
        )

        type_rows = await conn.fetch(
            f"""
            SELECT event_type, COUNT(*) AS event_count
            FROM enterprise_event_inbox
            WHERE received_at >= NOW() - ({days_placeholder}::int * INTERVAL '1 day')
            {tenant_filter}
            GROUP BY event_type
            ORDER BY event_count DESC, event_type
            """,
            *params,
        )

        problem_params = list(params)
        problem_params.append(problem_limit)
        problem_limit_placeholder = f"${len(problem_params)}"

        problem_rows = await conn.fetch(
            f"""
            SELECT
                inbox_event_id,
                tenant_code,
                source_system,
                source_event_id,
                referral_track_id::text AS referral_track_id,
                event_type,
                processing_status,
                error_message,
                received_at,
                normalized_payload IS NOT NULL AS has_normalized_payload
            FROM enterprise_event_inbox
            WHERE received_at >= NOW() - ({days_placeholder}::int * INTERVAL '1 day')
              AND processing_status IN ('IGNORED', 'FAILED', 'DUPLICATE')
            {tenant_filter}
            ORDER BY received_at DESC
            LIMIT {problem_limit_placeholder}
            """,
            *problem_params,
        )

    by_status = [
        {
            "processingStatus": row["processing_status"],
            "eventCount": int(row["event_count"] or 0),
        }
        for row in status_rows
    ]

    by_source_system = [
        {
            "sourceSystem": row["source_system"],
            "eventCount": int(row["event_count"] or 0),
        }
        for row in source_rows
    ]

    by_event_type = [
        {
            "eventType": row["event_type"],
            "eventCount": int(row["event_count"] or 0),
        }
        for row in type_rows
    ]

    recent_problem_events = [
        {
            "inboxEventId": str(row["inbox_event_id"]),
            "tenantCode": row["tenant_code"],
            "sourceSystem": row["source_system"],
            "sourceEventId": row["source_event_id"],
            "referralTrackId": row["referral_track_id"],
            "eventType": row["event_type"],
            "processingStatus": row["processing_status"],
            "errorMessage": row["error_message"],
            "receivedAt": row["received_at"],
            "hasNormalizedPayload": bool(row["has_normalized_payload"]),
        }
        for row in problem_rows
    ]

    return {
        "status": "ok",
        "tenantCode": tenant_code,
        "windowDays": days,
        "total": sum(item["eventCount"] for item in by_status),
        "byStatus": by_status,
        "bySourceSystem": by_source_system,
        "byEventType": by_event_type,
        "recentProblemEvents": recent_problem_events,
    }


async def replay_enterprise_event(
    *,
    inbox_event_id: str,
    dry_run: bool = True,
) -> Dict[str, Any]:
    async with get_async_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                inbox_event_id,
                tenant_code,
                source_system,
                source_event_id,
                referral_track_id::text AS referral_track_id,
                event_type,
                normalized_payload,
                processing_status
            FROM enterprise_event_inbox
            WHERE inbox_event_id = $1
            """,
            inbox_event_id,
        )

    if not row:
        _record_replay_metric(event_type=None, status="not_found")
        raise ValueError("Enterprise inbox event not found")

    payload = _json_payload(row["normalized_payload"])
    if not payload:
        _record_replay_metric(event_type=row["event_type"], status="skipped")
        return {
            "status": "skipped",
            "reason": "no_normalized_payload",
            "inboxEventId": str(row["inbox_event_id"]),
            "eventType": row["event_type"],
            "processingStatus": row["processing_status"],
            "dryRun": dry_run,
            "queued": False,
        }

    if dry_run:
        _record_replay_metric(event_type=row["event_type"], status="replayable")
        return {
            "status": "replayable",
            "inboxEventId": str(row["inbox_event_id"]),
            "eventType": row["event_type"],
            "progressEventType": payload.get("progressEventType"),
            "referralTrackId": payload.get("referralTrackId"),
            "tenantCode": payload.get("tenantCode"),
            "dryRun": True,
            "queued": False,
        }

    await enqueue_event(payload)

    async with get_async_connection() as conn:
        await conn.execute(
            """
            UPDATE enterprise_event_inbox
            SET processing_status = 'QUEUED',
                processed_at = NOW(),
                error_message = NULL,
                updated_at = NOW()
            WHERE inbox_event_id = $1
            """,
            inbox_event_id,
        )

    log_event(
        level="INFO",
        component="enterprise_event_inbox",
        message="enterprise_event_replay_queued",
        referral_track_id=payload.get("referralTrackId"),
        extra={
            "inbox_event_id": str(row["inbox_event_id"]),
            "source_system": row["source_system"],
            "source_event_id": row["source_event_id"],
            "event_type": row["event_type"],
        },
    )

    _record_replay_metric(event_type=row["event_type"], status="replay_queued")

    return {
        "status": "replay_queued",
        "inboxEventId": str(row["inbox_event_id"]),
        "eventType": row["event_type"],
        "progressEventType": payload.get("progressEventType"),
        "referralTrackId": payload.get("referralTrackId"),
        "tenantCode": payload.get("tenantCode"),
        "dryRun": False,
        "queued": True,
    }
