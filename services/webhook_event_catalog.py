from __future__ import annotations

from typing import Final, Literal

WebhookEventFamily = Literal[
    "campaign",
    "outcome",
    "reward",
    "funding",
    "fulfilment",
    "settlement",
    "integration",
]

CAMPAIGN_PUBLISHED: Final = "CAMPAIGN_PUBLISHED"
CAMPAIGN_CLOSED: Final = "CAMPAIGN_CLOSED"
OUTCOME_COMPLETED: Final = "OUTCOME_COMPLETED"
OUTCOME_BLOCKED: Final = "OUTCOME_BLOCKED"
REWARD_APPLIED: Final = "REWARD_APPLIED"
REWARD_FULFILLED: Final = "REWARD_FULFILLED"
REWARD_FAILED: Final = "REWARD_FAILED"
REWARD_REVERSED: Final = "REWARD_REVERSED"
FUNDING_RESERVED: Final = "FUNDING_RESERVED"
FUNDING_RELEASED: Final = "FUNDING_RELEASED"
FUNDING_SETTLED: Final = "FUNDING_SETTLED"
FUNDING_REVERSED: Final = "FUNDING_REVERSED"
FULFILMENT_PENDING: Final = "FULFILMENT_PENDING"
FULFILMENT_PROCESSING: Final = "FULFILMENT_PROCESSING"
FULFILMENT_SUCCEEDED: Final = "FULFILMENT_SUCCEEDED"
FULFILMENT_FAILED: Final = "FULFILMENT_FAILED"
FULFILMENT_DUPLICATE_SKIPPED: Final = "FULFILMENT_DUPLICATE_SKIPPED"
SETTLEMENT_PENDING: Final = "SETTLEMENT_PENDING"
SETTLEMENT_SETTLED: Final = "SETTLEMENT_SETTLED"
SETTLEMENT_FAILED: Final = "SETTLEMENT_FAILED"
SETTLEMENT_REVERSED: Final = "SETTLEMENT_REVERSED"
SETTLEMENT_DISPUTED: Final = "SETTLEMENT_DISPUTED"
INTEGRATION_WEBHOOK_DELIVERY_FAILED: Final = "INTEGRATION_WEBHOOK_DELIVERY_FAILED"
INTEGRATION_WEBHOOK_DELIVERY_RETRY_QUEUED: Final = (
    "INTEGRATION_WEBHOOK_DELIVERY_RETRY_QUEUED"
)
INTEGRATION_WEBHOOK_SUBSCRIPTION_CHANGED: Final = (
    "INTEGRATION_WEBHOOK_SUBSCRIPTION_CHANGED"
)

EVENT_FAMILIES: Final[dict[str, WebhookEventFamily]] = {
    CAMPAIGN_PUBLISHED: "campaign",
    CAMPAIGN_CLOSED: "campaign",
    OUTCOME_COMPLETED: "outcome",
    OUTCOME_BLOCKED: "outcome",
    REWARD_APPLIED: "reward",
    REWARD_FULFILLED: "reward",
    REWARD_FAILED: "reward",
    REWARD_REVERSED: "reward",
    FUNDING_RESERVED: "funding",
    FUNDING_RELEASED: "funding",
    FUNDING_SETTLED: "funding",
    FUNDING_REVERSED: "funding",
    FULFILMENT_PENDING: "fulfilment",
    FULFILMENT_PROCESSING: "fulfilment",
    FULFILMENT_SUCCEEDED: "fulfilment",
    FULFILMENT_FAILED: "fulfilment",
    FULFILMENT_DUPLICATE_SKIPPED: "fulfilment",
    SETTLEMENT_PENDING: "settlement",
    SETTLEMENT_SETTLED: "settlement",
    SETTLEMENT_FAILED: "settlement",
    SETTLEMENT_REVERSED: "settlement",
    SETTLEMENT_DISPUTED: "settlement",
    INTEGRATION_WEBHOOK_DELIVERY_FAILED: "integration",
    INTEGRATION_WEBHOOK_DELIVERY_RETRY_QUEUED: "integration",
    INTEGRATION_WEBHOOK_SUBSCRIPTION_CHANGED: "integration",
}

CATALOG_EVENT_TYPES: Final[tuple[str, ...]] = tuple(EVENT_FAMILIES)
CATALOG_EVENT_TYPE_SET: Final[frozenset[str]] = frozenset(CATALOG_EVENT_TYPES)

UNSAFE_EVENT_NAME_PARTS: Final[tuple[str, ...]] = (
    "SECRET",
    "SIGNING",
    "TOKEN",
    "PASSWORD",
    "PROVIDER_PAYLOAD",
    "RAW",
    "DLQ_PAYLOAD",
    "AUDIT_PAYLOAD",
    "PARTNER_WEBHOOK_DELIVERIES",
    "PARTNER_WEBHOOK_SUBSCRIPTIONS",
)


def normalize_event_type(event_type: object) -> str:
    return str(event_type or "").strip().upper()


def is_catalog_event_type(event_type: object, *, strict: bool = True) -> bool:
    candidate = (
        str(event_type or "").strip() if strict else normalize_event_type(event_type)
    )
    return candidate in CATALOG_EVENT_TYPE_SET


def get_event_family(event_type: object, *, strict: bool = True) -> str | None:
    candidate = (
        str(event_type or "").strip() if strict else normalize_event_type(event_type)
    )
    return EVENT_FAMILIES.get(candidate)


def validate_event_type(
    event_type: object, *, strict: bool = True
) -> dict[str, object]:
    raw = str(event_type or "").strip()
    candidate = raw if strict else normalize_event_type(raw)
    family = EVENT_FAMILIES.get(candidate)
    unsafe_match = next(
        (part for part in UNSAFE_EVENT_NAME_PARTS if part in normalize_event_type(raw)),
        None,
    )

    if family:
        return {
            "valid": True,
            "event_type": candidate,
            "family": family,
            "code": None,
            "message": "Webhook event type is in the accepted catalog.",
        }

    if not raw:
        code = "EVENT_TYPE_REQUIRED"
        message = "event_type is required."
    elif unsafe_match:
        code = "UNSAFE_EVENT_TYPE"
        message = "event_type must not expose internal, secret, or raw source details."
    elif strict and raw != normalize_event_type(raw):
        code = "NON_CANONICAL_EVENT_TYPE"
        message = "event_type must use canonical uppercase snake case."
    else:
        code = "UNKNOWN_EVENT_TYPE"
        message = "event_type is not in the accepted webhook event catalog."

    return {
        "valid": False,
        "event_type": candidate or None,
        "family": None,
        "code": code,
        "message": message,
    }


def require_catalog_event_type(event_type: object, *, strict: bool = True) -> str:
    validation = validate_event_type(event_type, strict=strict)
    if validation["valid"] is True:
        return str(validation["event_type"])
    raise ValueError(str(validation["message"]))


def list_catalog_events() -> list[dict[str, str]]:
    return [
        {"event_type": event_type, "family": EVENT_FAMILIES[event_type]}
        for event_type in CATALOG_EVENT_TYPES
    ]
