from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from services.dlq_service import publish_to_dlq
from services.fulfilment.base import FulfilmentRequest
from services.fulfilment.service import fulfil_reward
from services.fulfilment_events import REWARD_FULFILMENT_REQUESTED
from services.journey_orchestrator import handle_referral_progress_recorded
from services.leaderboard_events import EVENT_TYPE_LEADERBOARD_REBUILD_REQUESTED
from services.leaderboard_service import rebuild_leaderboard_for_referrer

logger = logging.getLogger(__name__)

WORKER_SECRET = os.getenv("WORKER_SECRET")

router = APIRouter(tags=["Worker"])


SUPPORTED_EVENT_TYPES = {
    "REFERRAL_PROGRESS_RECORDED",
    EVENT_TYPE_LEADERBOARD_REBUILD_REQUESTED,
    REWARD_FULFILMENT_REQUESTED,
}


def _unwrap_sqsd_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if payload.get("eventType") in SUPPORTED_EVENT_TYPES:
        return payload

    for key in ("body", "Body", "Message", "message"):
        nested = payload.get(key)
        if nested is None:
            continue

        if isinstance(nested, dict):
            return nested

        if isinstance(nested, str):
            try:
                parsed = json.loads(nested)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                logger.warning("Failed to parse nested SQS payload field: %s", key)

    return payload


def _validate_worker_auth(incoming_secret: str | None, event_secret: str | None) -> None:
    if not WORKER_SECRET:
        logger.error("WORKER_SECRET is not configured")
        raise HTTPException(status_code=500, detail="Worker not configured")

    if incoming_secret == WORKER_SECRET or event_secret == WORKER_SECRET:
        return

    logger.warning("Unauthorized worker request")
    raise HTTPException(status_code=401, detail="Unauthorized")


def _get_event_value(
    event: Dict[str, Any],
    camel_key: str,
    snake_key: str,
):
    return event.get(camel_key) if event.get(camel_key) is not None else event.get(snake_key)


async def _process_reward_fulfilment_requested(
    *,
    event: Dict[str, Any],
    tenant_code: str,
):
    reward_id = _get_event_value(event, "rewardId", "reward_id")
    reward_type = _get_event_value(event, "rewardType", "reward_type")
    reward_value = _get_event_value(event, "rewardValue", "reward_value")

    if not reward_id:
        logger.error("Missing rewardId in fulfilment event")
        return {"status": "ignored", "reason": "missing rewardId"}

    if not reward_type:
        logger.error("Missing rewardType in fulfilment event")
        return {"status": "ignored", "reason": "missing rewardType"}

    if reward_value is None:
        logger.error("Missing rewardValue in fulfilment event")
        return {"status": "ignored", "reason": "missing rewardValue"}

    result = await fulfil_reward(
        FulfilmentRequest(
            tenant_code=tenant_code,
            reward_id=reward_id,
            reward_type=reward_type,
            reward_value=float(reward_value),
            recipient_ucn=_get_event_value(event, "recipientUcn", "recipient_ucn"),
            currency=event.get("currency"),
            journey_code=_get_event_value(event, "journeyCode", "journey_code"),
            milestone_code=_get_event_value(event, "milestoneCode", "milestone_code"),
            product_code=_get_event_value(event, "productCode", "product_code"),
            metadata=event.get("metadata") or {},
        )
    )

    return {
        "status": "ok",
        "processed": True,
        "eventType": REWARD_FULFILMENT_REQUESTED,
        "fulfilmentStatus": result.status,
        "providerReference": result.provider_reference,
    }


@router.post("/worker/referral-events")
async def process_referral_event(request: Request):
    incoming_secret = request.headers.get("x-worker-secret")
    raw = await request.body()

    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        logger.warning("Worker received invalid JSON payload")
        return {"status": "ignored", "reason": "invalid json"}

    event = _unwrap_sqsd_payload(payload)

    _validate_worker_auth(
        incoming_secret=incoming_secret,
        event_secret=event.get("secret"),
    )

    event_type = event.get("eventType")

    logger.info(
        "[WORKER] eventType=%s keys=%s",
        event_type,
        list(event.keys()),
    )

    tenant_code = event.get("tenant_code") or event.get("tenantCode")
    if not tenant_code:
        logger.error("Missing tenant_code in worker event")
        return {"status": "ignored", "reason": "missing tenant_code"}

    try:
        if event_type == "REFERRAL_PROGRESS_RECORDED":
            await handle_referral_progress_recorded(
                event,
                tenant_code=tenant_code,
            )

            return {"status": "ok", "processed": True}

        if event_type == EVENT_TYPE_LEADERBOARD_REBUILD_REQUESTED:
            referrer_ucn = event.get("referrerUcn") or event.get("referrer_ucn")

            if not referrer_ucn:
                logger.error("Missing referrerUcn in leaderboard rebuild event")
                return {"status": "ignored", "reason": "missing referrerUcn"}

            await run_in_threadpool(
                rebuild_leaderboard_for_referrer,
                tenant_code=tenant_code,
                referrer_ucn=referrer_ucn,
            )

            return {
                "status": "ok",
                "processed": True,
                "eventType": event_type,
            }

        if event_type == REWARD_FULFILMENT_REQUESTED:
            return await _process_reward_fulfilment_requested(
                event=event,
                tenant_code=tenant_code,
            )

        return {
            "status": "ok",
            "processed": False,
            "reason": f"unsupported or unrecognized event payload: keys={list(event.keys())}",
        }

    except Exception as exc:
        logger.exception("Worker failed processing event")

        await run_in_threadpool(
            publish_to_dlq,
            event=event,
            error=str(exc),
        )

        return {
            "status": "failed",
            "processed": False,
            "eventType": event_type,
        }