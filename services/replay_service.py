from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from apps.core.logging_utils import log_event
from services.journey_definitions import (
    DEFAULT_JOURNEY_CODE,
    DEFAULT_JOURNEY_VERSION,
    get_journey_definition,
)
from services.journey_orchestrator import (
    normalize_event,
    apply_progress_event_to_instance,
    _derive_progress_snapshot,
)
from utils.db import db_connection


async def _load_events(conn, referral_track_id: str) -> List[Dict[str, Any]]:
    rows = await conn.fetch(
        """
        SELECT id, event_type, source_system, source_event_id,
               occurred_at, received_at, dedupe_key, meta
        FROM referral_progress_events
        WHERE referral_track_id = $1
        ORDER BY occurred_at ASC, received_at ASC, id ASC
        """,
        referral_track_id,
    )

    return [dict(row) for row in rows]



async def _load_instance(conn, referral_track_id: str) -> Dict[str, Any]:
    row = await conn.fetchrow(
        """
        SELECT *
        FROM referral_instances
        WHERE referral_track_id = $1
        """,
        referral_track_id,
    )

    if not row:
        raise ValueError(f"Referral instance not found: {referral_track_id}")

    return dict(row)


def _reset_instance_projection(
    instance: Dict[str, Any],
    *,
    journey_code: str,
    journey_version: str,
) -> None:
    instance["status"] = "VALIDATED"
    instance["ucn_captured_at"] = None
    instance["account_opened_at"] = None
    instance["account_activated_at"] = None
    instance["funded_at"] = None
    instance["debit_order_switched_at"] = None
    instance["salary_switched_at"] = None
    instance["first_transaction_completed_at"] = None

    snapshot = _derive_progress_snapshot(
        status="VALIDATED",
        journey_code=journey_code,
        journey_version=journey_version,
        is_complete=False,
    )

    instance.update(snapshot)
    instance["is_complete"] = False
    instance["completed_at"] = None
    instance["current_milestone"] = "VALIDATED"
    instance["platform_status"] = "IN_PROGRESS"

def _ensure_naive_utc(
    dt: datetime | None,
) -> datetime | None:
    if dt is None:
        return None

    if dt.tzinfo is not None:
        return (
            dt.astimezone(timezone.utc)
              .replace(tzinfo=None)
        )

    return dt

async def _update_instance(conn, instance: Dict[str, Any]) -> None:
    await conn.execute(
        """
        UPDATE referral_instances
        SET status = $1,
            ucn_captured_at = $2,
            account_opened_at = $3,
            account_activated_at = $4,
            funded_at = $5,
            debit_order_switched_at = $6,
            salary_switched_at = $7,
            first_transaction_completed_at = $8,
            progress_percent = $9,
            progress_band = $10,
            display_status = $11,
            next_milestone = $12,
            is_complete = $13,
            completed_at = $14,
            updated_at = NOW()
        WHERE referral_track_id = $15
        """,
        instance["status"],
        _ensure_naive_utc(instance.get("ucn_captured_at")),
        _ensure_naive_utc(instance.get("account_opened_at")),
        _ensure_naive_utc(instance.get("account_activated_at")),
        _ensure_naive_utc(instance.get("funded_at")),
        _ensure_naive_utc(instance.get("debit_order_switched_at")),
        _ensure_naive_utc(instance.get("salary_switched_at")),
        _ensure_naive_utc(instance.get("first_transaction_completed_at")),
        instance.get("progress_percent"),
        instance.get("progress_band"),
        instance.get("display_status"),
        instance.get("next_milestone"),
        instance.get("is_complete"),
        _ensure_naive_utc(instance.get("completed_at")),
        instance["referral_track_id"],
    )


async def rebuild_referral_instance(
    referral_track_id: str,
    *,
    dry_run: bool = True,
) -> Dict[str, Any]:
    log_event(
        level="INFO",
        component="replay",
        message="REFERRAL_REPLAY_STARTED",
        referral_track_id=referral_track_id,
        extra={"dryRun": dry_run},
    )

    try:
        async with db_connection() as conn:
            if dry_run:
                instance = await _load_instance(conn, referral_track_id)
                original_snapshot = dict(instance)

                journey_code = instance.get("journey_code") or DEFAULT_JOURNEY_CODE
                journey_version = instance.get("journey_version") or DEFAULT_JOURNEY_VERSION

                journey_definition = get_journey_definition(
                    journey_code,
                    journey_version,
                )

                _reset_instance_projection(
                    instance,
                    journey_code=journey_code,
                    journey_version=journey_version,
                )

                events = await _load_events(conn, referral_track_id)

                applied = 0
                ignored = 0
                ignored_events: List[Dict[str, Any]] = []

                for event in events:
                    normalized = normalize_event(
                        {
                            "eventType": "REFERRAL_PROGRESS_RECORDED",
                            "progressEventType": event["event_type"],
                            "occurredAt": event["occurred_at"].isoformat(),
                        }
                    )

                    incoming_event = normalized["normalizedEventType"]
                    occurred_at = event["occurred_at"]

                    transition = apply_progress_event_to_instance(
                        instance=instance,
                        incoming_event=incoming_event,
                        occurred_at=occurred_at,
                        journey_definition=journey_definition,
                        journey_code=journey_code,
                        journey_version=journey_version,
                        replay_mode=True,
                    )

                    if transition != "valid":
                        ignored += 1
                        ignored_events.append(
                            {
                                "eventType": event["event_type"],
                                "normalizedEventType": incoming_event,
                                "transition": transition,
                                "occurredAt": occurred_at.isoformat(),
                            }
                        )
                        continue

                    applied += 1
            else:
                async with conn.transaction():
                    instance = await _load_instance(conn, referral_track_id)
                    original_snapshot = dict(instance)

                    journey_code = instance.get("journey_code") or DEFAULT_JOURNEY_CODE
                    journey_version = instance.get("journey_version") or DEFAULT_JOURNEY_VERSION

                    journey_definition = get_journey_definition(
                        journey_code,
                        journey_version,
                    )

                    _reset_instance_projection(
                        instance,
                        journey_code=journey_code,
                        journey_version=journey_version,
                    )

                    events = await _load_events(conn, referral_track_id)

                    applied = 0
                    ignored = 0
                    ignored_events: List[Dict[str, Any]] = []

                    for event in events:
                        normalized = normalize_event(
                            {
                                "eventType": "REFERRAL_PROGRESS_RECORDED",
                                "progressEventType": event["event_type"],
                                "occurredAt": event["occurred_at"].isoformat(),
                            }
                        )

                        incoming_event = normalized["normalizedEventType"]
                        occurred_at = event["occurred_at"]

                        transition = apply_progress_event_to_instance(
                            instance=instance,
                            incoming_event=incoming_event,
                            occurred_at=occurred_at,
                            journey_definition=journey_definition,
                            journey_code=journey_code,
                            journey_version=journey_version,
                            replay_mode=True,
                        )

                        if transition != "valid":
                            ignored += 1
                            ignored_events.append(
                                {
                                    "eventType": event["event_type"],
                                    "normalizedEventType": incoming_event,
                                    "transition": transition,
                                    "occurredAt": occurred_at.isoformat(),
                                }
                            )
                            continue

                        applied += 1

                    await _update_instance(conn, instance)

        result = {
            "referralTrackId": referral_track_id,
            "eventsProcessed": len(events),
            "applied": applied,
            "ignored": ignored,
            "dryRun": dry_run,
            "before": {
                "status": original_snapshot.get("status"),
                "is_complete": original_snapshot.get("is_complete"),
                "progress_percent": original_snapshot.get("progress_percent"),
                "progress_band": original_snapshot.get("progress_band"),
                "display_status": original_snapshot.get("display_status"),
                "next_milestone": original_snapshot.get("next_milestone"),
            },
            "after": {
                "status": instance.get("status"),
                "is_complete": instance.get("is_complete"),
                "progress_percent": instance.get("progress_percent"),
                "progress_band": instance.get("progress_band"),
                "display_status": instance.get("display_status"),
                "next_milestone": instance.get("next_milestone"),
                "completed_at": (
                    instance.get("completed_at").isoformat()
                    if instance.get("completed_at")
                    else None
                ),
            },
            "ignoredEvents": ignored_events,
        }

        log_event(
            level="INFO",
            component="replay",
            message="REFERRAL_REPLAY_COMPLETED",
            referral_track_id=referral_track_id,
            extra={
                "dryRun": dry_run,
                "eventsProcessed": len(events),
                "applied": applied,
                "ignored": ignored,
                "finalStatus": instance.get("status"),
                "isComplete": instance.get("is_complete"),
            },
        )

        return result

    except Exception as exc:
        log_event(
            level="ERROR",
            component="replay",
            message="REFERRAL_REPLAY_FAILED",
            referral_track_id=referral_track_id,
            extra={
                "dryRun": dry_run,
                "error": str(exc),
            },
        )
        raise
