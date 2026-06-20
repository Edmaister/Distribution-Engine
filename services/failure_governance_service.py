from __future__ import annotations

import json
from typing import Any, Dict, Optional

from utils.db import get_async_connection


def classify_processing_failure(exc: Exception) -> str:
    msg = str(exc).lower()

    if "timeout" in msg or "connection" in msg or "tempor" in msg:
        return "TRANSIENT"

    if "invalid transition" in msg or "out_of_order" in msg or "backward" in msg:
        return "BUSINESS_RULE"

    if "missing" in msg or "payload" in msg or "json" in msg:
        return "DATA_QUALITY"

    return "SYSTEM_BUG"


async def record_event_failure(
    *,
    event: Optional[Dict[str, Any]],
    message_id: Optional[str],
    failure_category: str,
    failure_reason: str,
) -> None:
    referral_track_id = None
    event_type = None
    source_event_id = message_id
    source_system = "sqs"
    dedupe_key = None
    payload_json = None

    if event:
        referral_track_id = event.get("referralTrackId") or event.get("referral_track_id")
        event_type = event.get("eventType")
        source_event_id = (
            event.get("sourceEventId")
            or event.get("source_event_id")
            or message_id
        )
        source_system = event.get("sourceSystem") or event.get("source_system") or "sqs"
        dedupe_key = event.get("dedupeKey") or event.get("dedupe_key")
        payload_json = json.dumps(event)

    async with get_async_connection() as conn:
        if source_event_id:
            await conn.execute(
                """
                INSERT INTO referral_event_failures (
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
                    last_failed_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, 'OPEN', 1, $8::jsonb, NOW(), NOW())
                ON CONFLICT (source_system, source_event_id)
                DO UPDATE SET
                    referral_track_id = COALESCE(EXCLUDED.referral_track_id, referral_event_failures.referral_track_id),
                    event_type = COALESCE(EXCLUDED.event_type, referral_event_failures.event_type),
                    dedupe_key = COALESCE(EXCLUDED.dedupe_key, referral_event_failures.dedupe_key),
                    failure_category = EXCLUDED.failure_category,
                    failure_reason = EXCLUDED.failure_reason,
                    status = 'OPEN',
                    retry_count = referral_event_failures.retry_count + 1,
                    payload_json = COALESCE(EXCLUDED.payload_json, referral_event_failures.payload_json),
                    last_failed_at = NOW()
                """,
                referral_track_id,
                event_type,
                source_system,
                source_event_id,
                dedupe_key,
                failure_category,
                failure_reason,
                payload_json,
            )
            return

        if dedupe_key:
            await conn.execute(
                """
                INSERT INTO referral_event_failures (
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
                    last_failed_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, 'OPEN', 1, $8::jsonb, NOW(), NOW())
                ON CONFLICT (dedupe_key)
                DO UPDATE SET
                    referral_track_id = COALESCE(EXCLUDED.referral_track_id, referral_event_failures.referral_track_id),
                    event_type = COALESCE(EXCLUDED.event_type, referral_event_failures.event_type),
                    source_system = COALESCE(EXCLUDED.source_system, referral_event_failures.source_system),
                    source_event_id = COALESCE(EXCLUDED.source_event_id, referral_event_failures.source_event_id),
                    failure_category = EXCLUDED.failure_category,
                    failure_reason = EXCLUDED.failure_reason,
                    status = 'OPEN',
                    retry_count = referral_event_failures.retry_count + 1,
                    payload_json = COALESCE(EXCLUDED.payload_json, referral_event_failures.payload_json),
                    last_failed_at = NOW()
                """,
                referral_track_id,
                event_type,
                source_system,
                source_event_id,
                dedupe_key,
                failure_category,
                failure_reason,
                payload_json,
            )
            return

        await conn.execute(
            """
            INSERT INTO referral_event_failures (
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
                last_failed_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'OPEN', 1, $8::jsonb, NOW(), NOW())
            """,
            referral_track_id,
            event_type,
            source_system,
            source_event_id,
            dedupe_key,
            failure_category,
            failure_reason,
            payload_json,
        )