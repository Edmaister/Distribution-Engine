from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
import uuid
from typing import Any

import requests
from fastapi import HTTPException, status

from apps.api.settings import get_settings
from services.channel_provider_adapters import adapter_for_channel
from utils.metrics import channel_dispatch_observe


TERMINAL_DELIVERY_STATUSES = {"SENT", "DELIVERED", "FAILED", "DEAD_LETTERED"}
OPT_OUT_KEYS = {"opt_out", "opted_out", "recipient_opted_out", "channel_opt_out"}
CONSENT_KEYS = {"consent_verified", "channel_consent", "recipient_consent"}
CHANNEL_DELIVERY_MAX_ATTEMPTS = 3

_CHANNEL_DELIVERIES: dict[str, dict[str, Any]] = {}
_CHANNEL_AUDIT: list[dict[str, Any]] = []
_CHANNEL_PREFERENCES: dict[tuple[str, str, str], dict[str, Any]] = {}


CHANNEL_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "channel_code": "EMAIL",
        "label": "Email",
        "adapter_type": "MESSAGING",
        "target_users": ["Admin", "Producer - Supply", "Distributor - Demand"],
        "supported_events": [
            "ACCOUNT_INVITATION",
            "MEMBERSHIP_INVITATION",
            "REPORT_READY",
        ],
        "provider_url_setting": "channel_email_provider_url",
        "provider_secret_setting": "channel_email_provider_secret",
        "recommended_action": "Configure the Email provider URL and signing secret before sending live account invitations.",
    },
    {
        "channel_code": "WHATSAPP",
        "label": "WhatsApp",
        "adapter_type": "MESSAGING",
        "target_users": ["Producer - Supply", "Distributor - Demand", "Consumer"],
        "supported_events": [
            "OPPORTUNITY_PUBLISHED",
            "ROUTE_ASSIGNED",
            "REFERRAL_STARTED",
            "OUTCOME_COMPLETED",
        ],
        "provider_url_setting": "channel_whatsapp_provider_url",
        "provider_secret_setting": "channel_whatsapp_provider_secret",
        "recommended_action": "Configure the WhatsApp provider URL and signing secret before sending live customer or distributor messages.",
    },
    {
        "channel_code": "SMS",
        "label": "SMS",
        "adapter_type": "MESSAGING",
        "target_users": ["Distributor - Demand", "Consumer"],
        "supported_events": [
            "ROUTE_ASSIGNED",
            "REFERRAL_STARTED",
            "OUTCOME_COMPLETED",
        ],
        "provider_url_setting": "channel_sms_provider_url",
        "provider_secret_setting": "channel_sms_provider_secret",
        "recommended_action": "Configure the SMS provider URL and signing secret before sending live notifications.",
    },
    {
        "channel_code": "USSD",
        "label": "USSD",
        "adapter_type": "SESSIONAL",
        "target_users": ["Distributor - Demand", "Consumer"],
        "supported_events": [
            "REFERRAL_STARTED",
            "IDENTIFIER_CAPTURED",
            "PROGRESS_CHECK",
        ],
        "provider_url_setting": "channel_ussd_provider_url",
        "provider_secret_setting": "channel_ussd_provider_secret",
        "recommended_action": "Configure the USSD gateway endpoint and shared secret before exposing live USSD sessions.",
    },
)

AUDIENCE_CHANNEL_PREFERENCE = {
    "PRODUCER": ["WHATSAPP", "SMS"],
    "DISTRIBUTOR": ["WHATSAPP", "SMS", "USSD"],
    "CONSUMER": ["WHATSAPP", "SMS", "USSD"],
    "ADMIN": ["EMAIL", "WHATSAPP", "SMS"],
}

EVENT_CHANNEL_PREFERENCE = {
    "ACCOUNT_INVITATION": ["EMAIL"],
    "MEMBERSHIP_INVITATION": ["EMAIL"],
    "REPORT_READY": ["EMAIL"],
    "OPPORTUNITY_PUBLISHED": ["WHATSAPP", "SMS"],
    "ROUTE_ASSIGNED": ["WHATSAPP", "SMS"],
    "REFERRAL_STARTED": ["USSD", "WHATSAPP", "SMS"],
    "IDENTIFIER_CAPTURED": ["USSD", "WHATSAPP"],
    "PROGRESS_CHECK": ["USSD", "WHATSAPP"],
    "OUTCOME_COMPLETED": ["WHATSAPP", "SMS"],
}


def get_channel_readiness() -> dict[str, Any]:
    settings = get_settings()
    items = [_channel_status(settings, item) for item in CHANNEL_CATALOG]
    ready_count = sum(1 for item in items if item["status"] == "READY")
    attention_count = len(items) - ready_count
    return {
        "status": "READY" if attention_count == 0 else "ATTENTION",
        "configuration_source": "channel_catalog",
        "summary": {
            "count": len(items),
            "ready_count": ready_count,
            "attention_count": attention_count,
            "supported_channels": [item["channel_code"] for item in items],
        },
        "items": items,
        "guardrail": (
            "Channels are catalogued for routing and UX readiness. Live send/receive requires "
            "provider URL and secret configuration per channel."
        ),
    }


def recommend_channels(
    *,
    event_type: str,
    audience: str,
    target_channels: list[str] | None = None,
    distributor_channels: list[str] | None = None,
    channel_preferences: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_event = event_type.strip().upper()
    normalized_audience = audience.strip().upper()
    requested = _normalize_channel_set(target_channels)
    distributor_supported = _normalize_channel_set(distributor_channels)
    preferred_channels = _normalize_channel_set(
        (channel_preferences or {}).get("preferred_channels")
    )
    opt_out_channels = _normalize_channel_set(
        (channel_preferences or {}).get("opt_out_channels")
    )
    readiness = get_channel_readiness()
    readiness_by_code = {item["channel_code"]: item for item in readiness["items"]}
    event_preferred = EVENT_CHANNEL_PREFERENCE.get(normalized_event, [])
    audience_preferred = AUDIENCE_CHANNEL_PREFERENCE.get(normalized_audience, [])

    items = []
    for catalog_item in CHANNEL_CATALOG:
        channel_code = catalog_item["channel_code"]
        status = readiness_by_code[channel_code]
        score = 20
        reasons = []

        if normalized_event in catalog_item["supported_events"]:
            score += 30
            reasons.append(f"event: supports {normalized_event}")
        else:
            reasons.append(f"event: does not explicitly support {normalized_event}")

        if requested:
            if channel_code in requested:
                score += 20
                reasons.append("opportunity: targeted channel")
            else:
                score -= 15
                reasons.append("opportunity: not targeted")
        else:
            score += 5
            reasons.append("opportunity: channel wildcard")

        if distributor_supported:
            if channel_code in distributor_supported:
                score += 20
                reasons.append("distributor: supported channel")
            else:
                score -= 20
                reasons.append("distributor: not supported")

        if channel_code in event_preferred:
            score += max(0, 15 - (event_preferred.index(channel_code) * 5))
            reasons.append("event: preferred channel")

        if channel_code in audience_preferred:
            score += max(0, 10 - (audience_preferred.index(channel_code) * 3))
            reasons.append("audience: preferred channel")

        if preferred_channels:
            if channel_code in preferred_channels:
                score += 25
                reasons.append("preference: user preferred channel")
            else:
                score -= 10
                reasons.append("preference: not user preferred")

        if channel_code in opt_out_channels:
            score -= 100
            reasons.append("preference: opted out")

        if status["provider_configured"]:
            score += 10
            reasons.append("provider: configured")
        else:
            score -= 10
            reasons.append("provider: needs configuration")

        items.append(
            {
                "channel_code": channel_code,
                "label": catalog_item["label"],
                "adapter_type": catalog_item["adapter_type"],
                "recommendation_score": max(0, min(score, 100)),
                "provider_status": status["status"],
                "provider_configured": status["provider_configured"],
                "preference_status": (
                    "OPTED_OUT"
                    if channel_code in opt_out_channels
                    else "PREFERRED"
                    if channel_code in preferred_channels
                    else "AVAILABLE"
                ),
                "reasons": reasons,
                "recommended_action": _channel_recommendation_action(
                    channel_code=channel_code,
                    provider_configured=status["provider_configured"],
                    event_type=normalized_event,
                    audience=normalized_audience,
                ),
            }
        )

    items.sort(
        key=lambda item: (
            item["recommendation_score"],
            item["provider_configured"],
            item["channel_code"],
        ),
        reverse=True,
    )
    top = items[0] if items else None
    return {
        "status": "READY" if top and top["provider_configured"] else "ATTENTION",
        "event_type": normalized_event,
        "audience": normalized_audience,
        "preferences_applied": bool(channel_preferences),
        "top_channel": top,
        "items": items,
        "guardrail": (
            "Channel recommendations are explainable matching signals. They do not send messages "
            "or replace consent, eligibility, or provider configuration checks."
        ),
    }


def get_channel_preferences(
    *, tenant_code: str, audience: str, subject_id: str
) -> dict[str, Any]:
    key = _preference_key(
        tenant_code=tenant_code,
        audience=audience,
        subject_id=subject_id,
    )
    if key in _CHANNEL_PREFERENCES:
        return _preference_public_view(_CHANNEL_PREFERENCES[key])

    _, normalized_audience, normalized_subject = key
    default_channels = AUDIENCE_CHANNEL_PREFERENCE.get(normalized_audience, [])
    return _preference_public_view(
        {
            "tenant_code": key[0],
            "audience": normalized_audience,
            "subject_id": normalized_subject,
            "preferred_channels": default_channels,
            "consent_channels": [],
            "opt_out_channels": [],
            "updated_at": None,
        }
    )


def set_channel_preferences(
    *,
    tenant_code: str,
    audience: str,
    subject_id: str,
    preferred_channels: list[str] | None = None,
    consent_channels: list[str] | None = None,
    opt_out_channels: list[str] | None = None,
) -> dict[str, Any]:
    key = _preference_key(
        tenant_code=tenant_code,
        audience=audience,
        subject_id=subject_id,
    )
    preference = {
        "tenant_code": key[0],
        "audience": key[1],
        "subject_id": key[2],
        "preferred_channels": _known_channels(preferred_channels),
        "consent_channels": _known_channels(consent_channels),
        "opt_out_channels": _known_channels(opt_out_channels),
        "updated_at": int(time.time()),
    }
    _CHANNEL_PREFERENCES[key] = preference
    return _preference_public_view(preference)


def _normalize_channel_set(value: list[str] | None) -> set[str]:
    normalized = set()
    for item in value or []:
        for part in str(item).replace(",", " ").split():
            cleaned = part.strip().upper()
            if cleaned:
                normalized.add(cleaned)
    return normalized


def _known_channels(value: list[str] | None) -> list[str]:
    known = {item["channel_code"] for item in CHANNEL_CATALOG}
    return sorted(channel for channel in _normalize_channel_set(value) if channel in known)


def _preference_key(
    *, tenant_code: str, audience: str, subject_id: str
) -> tuple[str, str, str]:
    normalized_tenant = tenant_code.strip().upper()
    normalized_audience = audience.strip().upper()
    normalized_subject = subject_id.strip().upper()
    if normalized_audience not in {"CONSUMER", "DISTRIBUTOR"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Channel preferences support CONSUMER and DISTRIBUTOR audiences",
        )
    if not normalized_tenant or not normalized_subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_code and subject_id are required",
        )
    return normalized_tenant, normalized_audience, normalized_subject


def _preference_public_view(preference: dict[str, Any]) -> dict[str, Any]:
    opted_out = set(preference.get("opt_out_channels") or [])
    recommendation_channels = [
        channel
        for channel in preference.get("preferred_channels") or []
        if channel not in opted_out
    ]
    return {
        "tenant_code": preference["tenant_code"],
        "audience": preference["audience"],
        "subject_id": preference["subject_id"],
        "preferred_channels": preference.get("preferred_channels") or [],
        "consent_channels": preference.get("consent_channels") or [],
        "opt_out_channels": preference.get("opt_out_channels") or [],
        "recommendation_channels": recommendation_channels,
        "updated_at": preference.get("updated_at"),
        "guardrail": "Preferences shape recommendations and consent checks; opted-out channels are excluded from recommended live contact.",
    }


def _channel_recommendation_action(
    *,
    channel_code: str,
    provider_configured: bool,
    event_type: str,
    audience: str,
) -> str:
    if not provider_configured:
        return f"Configure {channel_code} provider settings before using it for {audience.lower()} {event_type.lower()} journeys."
    return f"Use {channel_code} first for {audience.lower()} {event_type.lower()} journeys, then monitor delivery and conversion evidence."


def _channel_status(settings: Any, item: dict[str, Any]) -> dict[str, Any]:
    provider_url = getattr(settings, item["provider_url_setting"], None)
    provider_secret = getattr(settings, item["provider_secret_setting"], None)
    missing = []
    if not provider_url:
        missing.append("provider_url")
    if not provider_secret:
        missing.append("provider_secret")

    return {
        "channel_code": item["channel_code"],
        "label": item["label"],
        "adapter_type": item["adapter_type"],
        "target_users": item["target_users"],
        "supported_events": item["supported_events"],
        "status": "READY" if not missing else "ATTENTION",
        "provider_configured": bool(provider_url and provider_secret),
        "provider_url_configured": bool(provider_url),
        "provider_secret_configured": bool(provider_secret),
        "missing_components": missing,
        "recommended_action": (
            "Provider connection is configured for live channel activation."
            if not missing
            else item["recommended_action"]
        ),
    }


async def dispatch_channel_message(
    *,
    channel_code: str,
    recipient: str,
    message: str,
    tenant_code: str | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    channel = _catalog_item(channel_code)
    settings = get_settings()
    provider_url = getattr(settings, channel["provider_url_setting"], None)
    provider_secret = getattr(settings, channel["provider_secret_setting"], None)
    if not provider_url or not provider_secret:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{channel['channel_code']} provider is not configured",
        )

    normalized_recipient = recipient.strip()
    if not normalized_recipient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="recipient is required"
        )
    normalized_message = message.strip()
    if not normalized_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="message is required"
        )
    normalized_context = context or {}
    _assert_channel_consent(
        channel_code=channel["channel_code"],
        adapter_type=channel["adapter_type"],
        context=normalized_context,
    )

    payload = {
        "channel_code": channel["channel_code"],
        "tenant_code": tenant_code.strip().upper() if tenant_code else None,
        "recipient": normalized_recipient,
        "message": normalized_message,
        "context": normalized_context,
        "sent_at": int(time.time()),
    }
    delivery = _queue_channel_delivery(channel=channel, payload=payload)
    started_at = time.perf_counter()
    response = await _post_channel_payload(
        str(provider_url),
        payload,
        str(provider_secret),
    )
    latency_seconds = time.perf_counter() - started_at
    response_status = int(getattr(response, "status_code", 0) or 0)
    provider_text = str(getattr(response, "text", "") or "")
    delivered = 200 <= response_status < 300
    delivery_status = "SENT" if delivered else "FAILED"
    updated_delivery = _update_channel_delivery(
        delivery_id=delivery["delivery_id"],
        status=delivery_status,
        provider_status=response_status,
        provider_response=provider_text,
        latency_seconds=latency_seconds,
    )
    channel_dispatch_observe(
        tenant=payload["tenant_code"],
        channel=channel["channel_code"],
        adapter=channel["adapter_type"],
        delivery_status=delivery_status,
        provider_status=response_status,
        latency_seconds=latency_seconds,
    )
    return {
        "status": updated_delivery["status"] if updated_delivery else delivery_status,
        "delivery_id": delivery["delivery_id"],
        "channel_code": channel["channel_code"],
        "adapter_type": channel["adapter_type"],
        "recipient": normalized_recipient,
        "recipient_ref": delivery["recipient_ref"],
        "provider_status": response_status,
        "provider_response": provider_text[:300],
        "guardrail": "Provider response is recorded without exposing provider secrets or raw recipient data in operational views.",
    }


async def retry_channel_delivery(*, delivery_id: str) -> dict[str, Any]:
    delivery = _CHANNEL_DELIVERIES.get(delivery_id)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel delivery was not found",
        )
    if delivery["status"] not in {"FAILED", "DEAD_LETTERED"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only failed or dead-lettered channel deliveries can be retried",
        )
    if not delivery.get("retryable"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Channel delivery is not retryable",
        )
    if int(delivery.get("attempt_count") or 0) >= CHANNEL_DELIVERY_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Channel delivery retry attempts are exhausted",
        )

    payload = delivery.get("_payload")
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Channel delivery payload is not available for retry",
        )

    channel = _catalog_item(delivery["channel_code"])
    settings = get_settings()
    provider_url = getattr(settings, channel["provider_url_setting"], None)
    provider_secret = getattr(settings, channel["provider_secret_setting"], None)
    if not provider_url or not provider_secret:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{channel['channel_code']} provider is not configured",
        )

    delivery.update(
        {
            "status": "QUEUED",
            "retry_requested_at": int(time.time()),
            "updated_at": int(time.time()),
        }
    )
    _record_channel_audit(delivery=delivery, event_type="RETRY_QUEUED")

    started_at = time.perf_counter()
    response = await _post_channel_payload(
        str(provider_url),
        payload,
        str(provider_secret),
    )
    latency_seconds = time.perf_counter() - started_at
    response_status = int(getattr(response, "status_code", 0) or 0)
    provider_text = str(getattr(response, "text", "") or "")
    delivered = 200 <= response_status < 300
    delivery_status = "SENT" if delivered else "FAILED"
    updated = _update_channel_delivery(
        delivery_id=delivery_id,
        status=delivery_status,
        provider_status=response_status,
        provider_response=provider_text,
        latency_seconds=latency_seconds,
    )
    channel_dispatch_observe(
        tenant=payload["tenant_code"],
        channel=channel["channel_code"],
        adapter=channel["adapter_type"],
        delivery_status=updated["status"] if updated else delivery_status,
        provider_status=response_status,
        latency_seconds=latency_seconds,
    )
    return {
        "status": updated["status"] if updated else delivery_status,
        "delivery": _delivery_public_view(updated or delivery),
        "guardrail": "Retries are limited to recoverable failed channel deliveries and retain sanitized audit evidence.",
    }


async def process_inbound_channel_webhook(
    *,
    channel_code: str,
    raw_body: bytes,
    signature: str | None,
) -> dict[str, Any]:
    channel = _catalog_item(channel_code)
    settings = get_settings()
    provider_secret = getattr(settings, channel["provider_secret_setting"], None)
    if not provider_secret:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{channel['channel_code']} inbound provider secret is not configured",
        )
    expected = hmac.new(
        str(provider_secret).encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    if not signature or not hmac.compare_digest(signature, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid channel signature"
        )

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid channel payload"
        ) from exc

    normalized = _normalize_inbound_payload(channel, payload)
    delivery_update = _capture_callback_delivery_status(channel, payload, normalized)
    return {
        "status": "accepted",
        "channel_code": channel["channel_code"],
        "adapter_type": channel["adapter_type"],
        "inbound": normalized,
        "delivery_update": delivery_update,
        "guardrail": "Inbound channel payload was signature-verified and normalized before downstream processing.",
    }


def list_channel_deliveries(
    *, status_filter: str | None = None, limit: int = 50
) -> dict[str, Any]:
    normalized_filter = status_filter.strip().upper() if status_filter else None
    capped_limit = max(1, min(int(limit or 50), 200))
    deliveries = [
        _delivery_public_view(item)
        for item in sorted(
            _CHANNEL_DELIVERIES.values(),
            key=lambda item: item["updated_at"],
            reverse=True,
        )
        if not normalized_filter or item["status"] == normalized_filter
    ][:capped_limit]
    return {
        "status": "ok",
        "summary": {
            "count": len(_CHANNEL_DELIVERIES),
            "queued": sum(
                1 for item in _CHANNEL_DELIVERIES.values() if item["status"] == "QUEUED"
            ),
            "sent": sum(
                1 for item in _CHANNEL_DELIVERIES.values() if item["status"] == "SENT"
            ),
            "delivered": sum(
                1
                for item in _CHANNEL_DELIVERIES.values()
                if item["status"] == "DELIVERED"
            ),
            "failed": sum(
                1 for item in _CHANNEL_DELIVERIES.values() if item["status"] == "FAILED"
            ),
            "dead_lettered": sum(
                1
                for item in _CHANNEL_DELIVERIES.values()
                if item["status"] == "DEAD_LETTERED"
            ),
        },
        "items": deliveries,
        "guardrail": "Delivery operations expose recipient references only, not raw message content or provider secrets.",
    }


def list_channel_audit(limit: int = 50) -> dict[str, Any]:
    capped_limit = max(1, min(int(limit or 50), 200))
    recent_items = _CHANNEL_AUDIT[-capped_limit:]
    return {
        "status": "ok",
        "items": recent_items,
        "guardrail": "Channel audit records are append-only operational evidence with sensitive values redacted.",
    }


def _catalog_item(channel_code: str) -> dict[str, Any]:
    normalized = channel_code.strip().upper()
    for item in CHANNEL_CATALOG:
        if item["channel_code"] == normalized:
            return item
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Channel is not configured"
    )


async def _post_channel_payload(url: str, payload: dict[str, Any], secret: str):
    provider_request = adapter_for_channel(str(payload["channel_code"])).build_request(
        payload, secret
    )
    return await asyncio.to_thread(
        requests.post,
        url,
        data=provider_request.body,
        headers=provider_request.headers,
        timeout=10,
    )


def _assert_channel_consent(
    *, channel_code: str, adapter_type: str, context: dict[str, Any]
) -> None:
    if adapter_type != "MESSAGING":
        return

    if any(_truthy(context.get(key)) for key in OPT_OUT_KEYS):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{channel_code} recipient has opted out",
        )

    if not any(_truthy(context.get(key)) for key in CONSENT_KEYS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{channel_code} consent is required before sending customer or distributor messages",
        )


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "accepted"}


def _queue_channel_delivery(
    *, channel: dict[str, Any], payload: dict[str, Any]
) -> dict[str, Any]:
    now = int(time.time())
    delivery_id = f"CHD-{uuid.uuid4().hex[:12].upper()}"
    delivery = {
        "delivery_id": delivery_id,
        "status": "QUEUED",
        "channel_code": channel["channel_code"],
        "adapter_type": channel["adapter_type"],
        "tenant_code": payload["tenant_code"],
        "recipient_ref": _recipient_ref(payload["recipient"]),
        "message_ref": _message_ref(payload["message"]),
        "context": _redact_context(payload.get("context") or {}),
        "provider_status": None,
        "provider_response": None,
        "attempt_count": 0,
        "max_attempts": CHANNEL_DELIVERY_MAX_ATTEMPTS,
        "retryable": False,
        "next_retry_at": None,
        "dead_letter_reason": None,
        "latency_seconds": None,
        "created_at": now,
        "updated_at": now,
        "_payload": dict(payload),
    }
    _CHANNEL_DELIVERIES[delivery_id] = delivery
    _record_channel_audit(delivery=delivery, event_type="QUEUED")
    return delivery


def _update_channel_delivery(
    *,
    delivery_id: str,
    status: str,
    provider_status: int | None = None,
    provider_response: str | None = None,
    latency_seconds: float | None = None,
) -> dict[str, Any] | None:
    delivery = _CHANNEL_DELIVERIES.get(delivery_id)
    if not delivery:
        return None

    normalized_status = status.strip().upper()
    attempt_count = int(delivery.get("attempt_count") or 0) + 1
    retryable = _is_retryable_provider_status(provider_status)
    dead_letter_reason = None
    if normalized_status == "FAILED":
        if not retryable:
            dead_letter_reason = "non_retryable_provider_status"
            normalized_status = "DEAD_LETTERED"
        elif attempt_count >= CHANNEL_DELIVERY_MAX_ATTEMPTS:
            dead_letter_reason = "max_attempts_exhausted"
            normalized_status = "DEAD_LETTERED"
    delivery.update(
        {
            "status": normalized_status,
            "provider_status": provider_status,
            "provider_response": (provider_response or "")[:300],
            "latency_seconds": latency_seconds,
            "attempt_count": attempt_count,
            "retryable": retryable and normalized_status == "FAILED",
            "next_retry_at": (
                int(time.time()) + _retry_delay_seconds(attempt_count)
                if retryable and normalized_status == "FAILED"
                else None
            ),
            "dead_letter_reason": dead_letter_reason,
            "updated_at": int(time.time()),
        }
    )
    if status.strip().upper() == "FAILED" and normalized_status == "DEAD_LETTERED":
        _record_channel_audit(
            delivery=delivery,
            event_type="FAILED",
            details={"dead_letter_reason": dead_letter_reason},
        )
    _record_channel_audit(delivery=delivery, event_type=normalized_status)
    return delivery


def _capture_callback_delivery_status(
    channel: dict[str, Any], payload: dict[str, Any], normalized: dict[str, Any]
) -> dict[str, Any] | None:
    delivery_id = (
        payload.get("delivery_id")
        or payload.get("deliveryId")
        or (payload.get("metadata") or {}).get("delivery_id")
        or (normalized.get("context") or {}).get("delivery_id")
    )
    raw_status = (
        payload.get("delivery_status")
        or payload.get("deliveryStatus")
        or payload.get("status")
        or (payload.get("metadata") or {}).get("status")
    )
    if not delivery_id or not raw_status:
        return None

    delivery_status = _normalize_delivery_status(str(raw_status))
    delivery = _update_channel_delivery(
        delivery_id=str(delivery_id),
        status=delivery_status,
        provider_status=_int_or_none(payload.get("provider_status")),
        provider_response=payload.get("provider_response") or payload.get("reason"),
    )
    if not delivery:
        return {
            "status": "unmatched",
            "delivery_id": str(delivery_id),
            "channel_code": channel["channel_code"],
        }
    return _delivery_public_view(delivery)


def _normalize_delivery_status(value: str) -> str:
    normalized = value.strip().upper().replace("-", "_")
    if normalized in {"DELIVERED", "READ"}:
        return "DELIVERED"
    if normalized in {"SENT", "ACCEPTED", "QUEUED"}:
        return "SENT"
    if normalized in {"FAILED", "BOUNCED", "REJECTED", "UNDELIVERABLE"}:
        return "FAILED"
    if normalized in TERMINAL_DELIVERY_STATUSES:
        return normalized
    return "SENT"


def _delivery_public_view(delivery: dict[str, Any]) -> dict[str, Any]:
    return {
        "delivery_id": delivery["delivery_id"],
        "status": delivery["status"],
        "channel_code": delivery["channel_code"],
        "adapter_type": delivery["adapter_type"],
        "tenant_code": delivery["tenant_code"],
        "recipient_ref": delivery["recipient_ref"],
        "message_ref": delivery["message_ref"],
        "context": delivery["context"],
        "provider_status": delivery["provider_status"],
        "attempt_count": delivery["attempt_count"],
        "max_attempts": delivery["max_attempts"],
        "retryable": delivery["retryable"],
        "next_retry_at": delivery["next_retry_at"],
        "dead_letter_reason": delivery["dead_letter_reason"],
        "latency_seconds": delivery["latency_seconds"],
        "created_at": delivery["created_at"],
        "updated_at": delivery["updated_at"],
    }


def _record_channel_audit(
    *, delivery: dict[str, Any], event_type: str, details: dict[str, Any] | None = None
) -> None:
    _CHANNEL_AUDIT.append(
        {
            "audit_id": f"CHA-{uuid.uuid4().hex[:12].upper()}",
            "delivery_id": delivery["delivery_id"],
            "event_type": event_type,
            "status": delivery["status"],
            "channel_code": delivery["channel_code"],
            "adapter_type": delivery["adapter_type"],
            "tenant_code": delivery["tenant_code"],
            "recipient_ref": delivery["recipient_ref"],
            "provider_status": delivery.get("provider_status"),
            "details": details or {},
            "created_at": int(time.time()),
        }
    )


def _recipient_ref(value: str) -> str:
    return f"recipient:{hashlib.sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _message_ref(value: str) -> str:
    return f"message:{hashlib.sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _redact_context(context: dict[str, Any]) -> dict[str, Any]:
    sensitive = {"message", "recipient", "phone", "msisdn", "email", "secret", "token"}
    return {
        key: ("[redacted]" if key.lower() in sensitive else value)
        for key, value in context.items()
    }


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _is_retryable_provider_status(provider_status: int | None) -> bool:
    if provider_status is None or provider_status == 0:
        return True
    return provider_status == 429 or provider_status >= 500


def _retry_delay_seconds(attempt_count: int) -> int:
    return min(60 * (2 ** max(attempt_count - 1, 0)), 900)


def _reset_channel_delivery_state_for_tests() -> None:
    _CHANNEL_DELIVERIES.clear()
    _CHANNEL_AUDIT.clear()
    _CHANNEL_PREFERENCES.clear()


def _normalize_inbound_payload(
    channel: dict[str, Any], payload: dict[str, Any]
) -> dict[str, Any]:
    if channel["channel_code"] == "USSD":
        session_text = str(payload.get("text") or payload.get("message") or "").strip()
        return {
            "session_id": payload.get("session_id") or payload.get("sessionId"),
            "from": payload.get("from") or payload.get("msisdn"),
            "message": session_text,
            "session_state": "CONTINUE" if session_text else "START",
            "reply": _ussd_reply(session_text),
            "context": payload.get("context") or {},
        }

    return {
        "message_id": payload.get("message_id") or payload.get("messageId"),
        "from": payload.get("from") or payload.get("msisdn"),
        "message": payload.get("message") or payload.get("text"),
        "context": payload.get("context") or {},
    }


def _ussd_reply(session_text: str) -> str:
    if not session_text:
        return "1. Check referral progress\n2. Get help"
    if session_text == "1":
        return "Your referral progress request has been received."
    if session_text == "2":
        return "A support prompt has been recorded."
    return "Invalid option. Reply 1 for progress or 2 for help."
