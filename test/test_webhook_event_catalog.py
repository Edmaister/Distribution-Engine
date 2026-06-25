from __future__ import annotations

import pytest

from services import webhook_event_catalog as catalog

EXPECTED_EVENTS = {
    "CAMPAIGN_PUBLISHED": "campaign",
    "CAMPAIGN_CLOSED": "campaign",
    "OUTCOME_COMPLETED": "outcome",
    "OUTCOME_BLOCKED": "outcome",
    "REWARD_APPLIED": "reward",
    "REWARD_FULFILLED": "reward",
    "REWARD_FAILED": "reward",
    "REWARD_REVERSED": "reward",
    "FUNDING_RESERVED": "funding",
    "FUNDING_RELEASED": "funding",
    "FUNDING_SETTLED": "funding",
    "FUNDING_REVERSED": "funding",
    "FULFILMENT_PENDING": "fulfilment",
    "FULFILMENT_PROCESSING": "fulfilment",
    "FULFILMENT_SUCCEEDED": "fulfilment",
    "FULFILMENT_FAILED": "fulfilment",
    "FULFILMENT_DUPLICATE_SKIPPED": "fulfilment",
    "SETTLEMENT_PENDING": "settlement",
    "SETTLEMENT_SETTLED": "settlement",
    "SETTLEMENT_FAILED": "settlement",
    "SETTLEMENT_REVERSED": "settlement",
    "SETTLEMENT_DISPUTED": "settlement",
    "INTEGRATION_WEBHOOK_DELIVERY_FAILED": "integration",
    "INTEGRATION_WEBHOOK_DELIVERY_RETRY_QUEUED": "integration",
    "INTEGRATION_WEBHOOK_SUBSCRIPTION_CHANGED": "integration",
}


@pytest.mark.parametrize(("event_type", "family"), sorted(EXPECTED_EVENTS.items()))
def test_all_catalog_events_validate(event_type, family):
    result = catalog.validate_event_type(event_type)

    assert result == {
        "valid": True,
        "event_type": event_type,
        "family": family,
        "code": None,
        "message": "Webhook event type is in the accepted catalog.",
    }
    assert catalog.is_catalog_event_type(event_type) is True
    assert catalog.get_event_family(event_type) == family
    assert catalog.require_catalog_event_type(event_type) == event_type


def test_catalog_list_matches_constants():
    listed = catalog.list_catalog_events()

    assert {item["event_type"]: item["family"] for item in listed} == EXPECTED_EVENTS
    assert set(catalog.CATALOG_EVENT_TYPES) == set(EXPECTED_EVENTS)


def test_case_sensitive_validation_rejects_non_canonical_case():
    result = catalog.validate_event_type("outcome_completed")

    assert result["valid"] is False
    assert result["code"] == "NON_CANONICAL_EVENT_TYPE"
    assert catalog.is_catalog_event_type("outcome_completed") is False
    assert catalog.get_event_family("outcome_completed") is None


def test_non_strict_validation_can_normalize_for_callers():
    result = catalog.validate_event_type(" outcome_completed ", strict=False)

    assert result["valid"] is True
    assert result["event_type"] == "OUTCOME_COMPLETED"
    assert result["family"] == "outcome"
    assert catalog.is_catalog_event_type("outcome_completed", strict=False) is True
    assert catalog.get_event_family("outcome_completed", strict=False) == "outcome"
    assert catalog.require_catalog_event_type("outcome_completed", strict=False) == (
        "OUTCOME_COMPLETED"
    )


@pytest.mark.parametrize(
    ("event_type", "code"),
    [
        ("", "EVENT_TYPE_REQUIRED"),
        (None, "EVENT_TYPE_REQUIRED"),
        ("CUSTOMER_ACTIVATED", "UNKNOWN_EVENT_TYPE"),
        ("partner_webhook_deliveries_failed", "UNSAFE_EVENT_TYPE"),
        ("RAW_PROVIDER_PAYLOAD_FAILED", "UNSAFE_EVENT_TYPE"),
        ("SIGNING_SECRET_ROTATED", "UNSAFE_EVENT_TYPE"),
        ("ACCESS_TOKEN_CREATED", "UNSAFE_EVENT_TYPE"),
    ],
)
def test_unknown_or_unsafe_event_types_return_safe_invalid_result(event_type, code):
    result = catalog.validate_event_type(event_type, strict=False)

    assert result["valid"] is False
    assert result["family"] is None
    assert result["code"] == code
    assert "secret" not in result["message"].lower() or code == "UNSAFE_EVENT_TYPE"
    assert "provider payload" not in result["message"].lower()


def test_require_catalog_event_type_raises_safe_error():
    with pytest.raises(ValueError, match="not in the accepted webhook event catalog"):
        catalog.require_catalog_event_type("UNKNOWN_EVENT")


def test_helper_does_not_expose_internal_payload_or_secret_values():
    rendered = str(catalog.list_catalog_events()) + str(
        catalog.validate_event_type("RAW_PROVIDER_PAYLOAD_FAILED", strict=False)
    )

    assert "signing_secret" not in rendered
    assert "client_secret" not in rendered
    assert "provider_payload_value" not in rendered
    assert "partner_webhook_deliveries" not in rendered
