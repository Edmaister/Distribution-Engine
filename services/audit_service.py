from __future__ import annotations

import datetime
import json
from typing import Any, Dict, Optional

from utils.db import db_connection
from datetime import timezone

def _normalize_datetime(dt):
    if dt is None:
        return None

    # convert aware → naive UTC
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    return dt

def _to_json(value: Optional[Dict[str, Any]]) -> str:
    return json.dumps(value or {}, default=str)


async def write_processing_audit(
    *,
    referral_track_id=None,
    event_id=None,
    event_type=None,
    occurred_at=None,
    processing_status=None,
    reason=None,
    previous_status=None,
    new_status=None,
    metadata=None,
):
    async with db_connection() as conn:
        async with conn.transaction():

            await conn.execute(
                """
                INSERT INTO referral_processing_audit (
                    referral_track_id,
                    event_id,
                    event_type,
                    occurred_at,
                    processing_status,
                    reason,
                    previous_status,
                    new_status,
                    metadata
                )
                VALUES (
                    $1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb
                )
                """,
                referral_track_id,
                event_id,
                event_type,
                _normalize_datetime(occurred_at),   # FIX
                processing_status,
                reason,
                previous_status,
                new_status,
                _to_json(metadata),
            )