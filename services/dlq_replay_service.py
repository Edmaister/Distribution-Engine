from __future__ import annotations

import asyncio
import inspect
from typing import Any, Dict

from services.journey_orchestrator import handle_referral_progress_recorded
from services.leaderboard_events import EVENT_TYPE_LEADERBOARD_REBUILD_REQUESTED
from services.leaderboard_service import rebuild_leaderboard_for_referrer


EVENT_TYPE_REFERRAL_PROGRESS_RECORDED = "REFERRAL_PROGRESS_RECORDED"


def replay_dlq_event(dlq_payload: Dict[str, Any]) -> Dict[str, Any]:
    original_event = dlq_payload.get("originalEvent")

    if not isinstance(original_event, dict):
        raise ValueError("Missing or invalid originalEvent")

    event_type = original_event.get("eventType")
    tenant_code = original_event.get("tenantCode") or original_event.get("tenant_code")

    if not tenant_code:
        raise ValueError("Missing tenantCode or tenant_code")

    if event_type == EVENT_TYPE_REFERRAL_PROGRESS_RECORDED:
        result = handle_referral_progress_recorded(
            original_event,
            tenant_code=tenant_code,
        )
        if inspect.isawaitable(result):
            asyncio.run(result)

        return {
            "status": "replayed",
            "eventType": event_type,
            "tenantCode": tenant_code,
        }

    if event_type == EVENT_TYPE_LEADERBOARD_REBUILD_REQUESTED:
        referrer_ucn = original_event.get("referrerUcn") or original_event.get("referrer_ucn")

        if not referrer_ucn:
            raise ValueError("Missing referrerUcn or referrer_ucn")

        rebuild_leaderboard_for_referrer(
            tenant_code=tenant_code,
            referrer_ucn=referrer_ucn,
        )

        return {
            "status": "replayed",
            "eventType": event_type,
            "tenantCode": tenant_code,
            "referrerUcn": referrer_ucn,
        }

    raise ValueError(f"Unsupported DLQ event type: {event_type}")
