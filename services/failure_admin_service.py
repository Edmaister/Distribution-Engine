from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from apps.core.logging_utils import log_event
from services.journey_orchestrator import (
    handle_referral_progress_recorded,
)
from utils.db import get_async_connection


async def list_failures(
    *,
    status: Optional[str] = "OPEN",
    failure_category: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:

    sql = """
        SELECT
            id,
            referral_track_id,
            event_type,
            source_system,
            source_event_id,
            dedupe_key,
            failure_category,
            failure_reason,
            status,
            retry_count,
            payload_json,
            first_failed_at,
            last_failed_at,
            resolved_at,
            resolution_note
        FROM referral_event_failures
        WHERE 1=1
    """

    params: list[Any] = []
    idx = 1

    if status:
        sql += f" AND status = ${idx}"
        params.append(status)
        idx += 1

    if failure_category:
        sql += f" AND failure_category = ${idx}"
        params.append(failure_category)
        idx += 1

    sql += f" ORDER BY last_failed_at DESC LIMIT ${idx}"
    params.append(limit)

    async with get_async_connection() as conn:
        rows = await conn.fetch(sql, *params)

    return [dict(row) for row in rows]


async def get_failure_summary() -> Dict[str, Any]:

    async with get_async_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                status,
                failure_category,
                COUNT(*) AS failure_count
            FROM referral_event_failures
            GROUP BY status, failure_category
            ORDER BY status, failure_category
            """
        )

    items = [
        {
            "status": row["status"],
            "failure_category": row["failure_category"],
            "failure_count": row["failure_count"],
        }
        for row in rows
    ]

    return {
        "count": len(items),
        "items": items,
    }


async def resolve_failure(
    *,
    failure_id: int,
    resolution_note: Optional[str] = None,
) -> bool:

    async with get_async_connection() as conn:
        result = await conn.execute(
            """
            UPDATE referral_event_failures
            SET
                status = 'RESOLVED',
                resolved_at = NOW(),
                resolution_note = $1
            WHERE id = $2
              AND status NOT IN (
                  'RESOLVED',
                  'REPROCESSED'
              )
            """,
            resolution_note,
            failure_id,
        )

    updated = result.endswith("1")

    if updated:
        log_event(
            level="INFO",
            component="failure_admin_service",
            message="failure_resolved",
            correlation_id=f"failure-{failure_id}",
            extra={
                "failure_id": failure_id,
                "resolution_note": resolution_note,
            },
        )

    return updated


async def get_failure_by_id(
    *,
    failure_id: int,
) -> Optional[Dict[str, Any]]:

    async with get_async_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                id,
                referral_track_id,
                event_type,
                source_system,
                source_event_id,
                dedupe_key,
                failure_category,
                failure_reason,
                status,
                retry_count,
                payload_json,
                first_failed_at,
                last_failed_at,
                resolved_at,
                resolution_note
            FROM referral_event_failures
            WHERE id = $1
            """,
            failure_id,
        )

    return dict(row) if row else None


async def mark_failure_reprocessed(
    *,
    failure_id: int,
    resolution_note: Optional[str] = None,
) -> bool:

    async with get_async_connection() as conn:
        result = await conn.execute(
            """
            UPDATE referral_event_failures
            SET
                status = 'REPROCESSED',
                resolved_at = NOW(),
                resolution_note = $1
            WHERE id = $2
              AND status <> 'REPROCESSED'
            """,
            resolution_note,
            failure_id,
        )

    updated = result.endswith("1")

    if updated:
        log_event(
            level="INFO",
            component="failure_admin_service",
            message="failure_reprocessed",
            correlation_id=f"failure-{failure_id}",
            extra={
                "failure_id": failure_id,
                "resolution_note": resolution_note,
            },
        )

    return updated


async def reprocess_failure(
    *,
    failure_id: int,
) -> Dict[str, Any]:

    failure = await get_failure_by_id(
        failure_id=failure_id
    )

    if not failure:
        raise ValueError(
            "Failure not found"
        )

    if failure.get("status") in (
        "RESOLVED",
        "REPROCESSED",
    ):
        raise ValueError(
            (
                "Failure is already closed "
                f"with status "
                f"{failure.get('status')}"
            )
        )

    payload = failure.get(
        "payload_json"
    )

    if not payload:
        raise ValueError(
            (
                "Failure payload "
                "is empty; "
                "cannot reprocess"
            )
        )

    if isinstance(payload, str):
        payload = json.loads(
            payload
        )

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(
            (
                "Failure payload "
                "is not valid JSON"
            )
        )

    event_type = payload.get(
        "eventType"
    )

    if (
        event_type
        != "REFERRAL_PROGRESS_RECORDED"
    ):
        raise ValueError(
            (
                "Unsupported payload "
                f"eventType "
                f"for reprocess: "
                f"{event_type}"
            )
        )

    await handle_referral_progress_recorded(
        payload
    )

    updated = await mark_failure_reprocessed(
        failure_id=failure_id,
        resolution_note=(
            "Event reprocessed "
            "successfully"
        ),
    )

    if not updated:
        raise ValueError(
            (
                "Failure could "
                "not be marked "
                "as REPROCESSED"
            )
        )

    return {
        "failureId": failure_id,
        "status": "ok",
        "reprocessed": True,
    }