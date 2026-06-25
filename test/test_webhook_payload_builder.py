from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from services import webhook_event_catalog as catalog
from services.webhook_payload_builder import (
    WEBHOOK_PAYLOAD_SCHEMA_VERSION,
    build_webhook_payload_envelope,
)


def test_builds_required_webhook_envelope_fields():
    occurred_at = datetime(2026, 6, 25, 8, 30, tzinfo=timezone.utc)

    envelope = build_webhook_payload_envelope(
        event_type=catalog.OUTCOME_COMPLETED,
        external_tenant_ref="partner-fnb",
        event_id="evt-outcome-1",
        occurred_at=occurred_at,
        subject={"type": "outcome", "id": "outcome-safe-1"},
        correlation={
            "correlation_id": "corr-1",
            "source_event_id": "source-1",
        },
        data={"status": "COMPLETED"},
        metadata={"producer_ref": "producer-1"},
        redactions=["raw_provider_payload", "raw_provider_payload", "ucn"],
    )

    assert envelope == {
        "event_id": "evt-outcome-1",
        "event_type": catalog.OUTCOME_COMPLETED,
        "event_family": "outcome",
        "schema_version": WEBHOOK_PAYLOAD_SCHEMA_VERSION,
        "occurred_at": "2026-06-25T08:30:00+00:00",
        "tenant": {
            "external_tenant_ref": "partner-fnb",
        },
        "subject": {
            "type": "outcome",
            "id": "outcome-safe-1",
        },
        "correlation": {
            "correlation_id": "corr-1",
            "source_event_id": "source-1",
        },
        "data": {
            "status": "COMPLETED",
        },
        "metadata": {
            "producer_ref": "producer-1",
        },
        "redactions": ["raw_provider_payload", "ucn"],
    }


@pytest.mark.parametrize("event_type", catalog.CATALOG_EVENT_TYPES)
def test_builder_accepts_catalog_event_types(event_type):
    envelope = build_webhook_payload_envelope(
        event_type=event_type,
        external_tenant_ref="partner-fnb",
        subject={"type": "catalog", "id": event_type.lower()},
    )

    assert envelope["event_type"] == event_type
    assert envelope["event_family"] == catalog.get_event_family(event_type)


def test_builder_can_normalize_event_type_when_caller_opts_in():
    envelope = build_webhook_payload_envelope(
        event_type=" outcome_completed ",
        strict_event_type=False,
        external_tenant_ref="partner-fnb",
        subject={"type": "outcome", "id": "outcome-safe-1"},
    )

    assert envelope["event_type"] == catalog.OUTCOME_COMPLETED


@pytest.mark.parametrize(
    "event_type",
    [
        "UNKNOWN_EVENT",
        "RAW_PROVIDER_PAYLOAD_FAILED",
        "SIGNING_SECRET_ROTATED",
    ],
)
def test_builder_rejects_unknown_or_unsafe_event_types(event_type):
    with pytest.raises(ValueError):
        build_webhook_payload_envelope(
            event_type=event_type,
            strict_event_type=False,
            external_tenant_ref="partner-fnb",
            subject={"type": "outcome", "id": "outcome-safe-1"},
        )


def test_builder_uses_external_tenant_ref_without_internal_tenant_code():
    envelope = build_webhook_payload_envelope(
        event_type=catalog.CAMPAIGN_PUBLISHED,
        external_tenant_ref="org-ext-1",
        subject={"type": "campaign", "id": "campaign-safe-1"},
    )

    assert envelope["tenant"] == {"external_tenant_ref": "org-ext-1"}
    assert "tenant_code" not in str(envelope).lower()


def test_builder_rejects_internal_tenant_code_and_private_fields():
    with pytest.raises(ValueError, match="must not expose"):
        build_webhook_payload_envelope(
            event_type=catalog.OUTCOME_COMPLETED,
            external_tenant_ref="partner-fnb",
            subject={"type": "outcome", "id": "outcome-safe-1"},
            data={"tenant_code": "FNB"},
        )

    with pytest.raises(ValueError, match="must not expose"):
        build_webhook_payload_envelope(
            event_type=catalog.OUTCOME_COMPLETED,
            external_tenant_ref="partner-fnb",
            subject={"type": "outcome", "id": "outcome-safe-1"},
            metadata={"signing_secret": "secret"},
        )

    with pytest.raises(ValueError, match="must not expose"):
        build_webhook_payload_envelope(
            event_type=catalog.OUTCOME_COMPLETED,
            external_tenant_ref="partner-fnb",
            subject={"type": "outcome", "id": "outcome-safe-1"},
            correlation={"raw_ucn": "900007"},
        )


def test_builder_preserves_safe_idempotency_and_source_references():
    envelope = build_webhook_payload_envelope(
        event_type=catalog.REWARD_APPLIED,
        external_tenant_ref="partner-fnb",
        idempotency_key="reward-applied-source-1",
        subject={"type": "reward", "id": "reward-safe-1"},
        source={"type": "reward", "id": "reward-source-safe-1"},
    )

    assert envelope["event_id"] == "reward-applied-source-1"
    assert envelope["correlation"]["idempotency_key"] == "reward-applied-source-1"
    assert envelope["source"] == {"type": "reward", "id": "reward-source-safe-1"}


def test_builder_generates_event_id_when_not_provided():
    envelope = build_webhook_payload_envelope(
        event_type=catalog.FULFILMENT_PENDING,
        external_tenant_ref="partner-fnb",
        subject={"type": "fulfilment", "id": "fulfilment-safe-1"},
    )

    assert envelope["event_id"]
    assert isinstance(envelope["event_id"], str)


def test_builder_requires_subject_type_and_id():
    with pytest.raises(ValueError, match="subject.type and subject.id"):
        build_webhook_payload_envelope(
            event_type=catalog.OUTCOME_COMPLETED,
            external_tenant_ref="partner-fnb",
            subject={"type": "outcome"},
        )


def test_builder_serializes_safe_json_values():
    envelope = build_webhook_payload_envelope(
        event_type=catalog.SETTLEMENT_SETTLED,
        external_tenant_ref="partner-fnb",
        subject={"type": "settlement", "id": "settlement-safe-1"},
        data={
            "amount_band": Decimal("100.50"),
            "settled_at": datetime(2026, 6, 25, 9, 0),
            "items": [{"status": "SETTLED"}],
        },
    )

    assert envelope["data"]["amount_band"] == "100.50"
    assert envelope["data"]["settled_at"] == "2026-06-25T09:00:00+00:00"
    assert envelope["data"]["items"] == [{"status": "SETTLED"}]


def test_builder_does_not_render_secret_or_raw_values_after_rejection():
    with pytest.raises(ValueError) as exc:
        build_webhook_payload_envelope(
            event_type=catalog.INTEGRATION_WEBHOOK_SUBSCRIPTION_CHANGED,
            external_tenant_ref="partner-fnb",
            subject={"type": "webhook_subscription", "id": "webhook-safe-1"},
            source={"partner_webhook_subscriptions": "internal-table"},
        )

    rendered = str(exc.value).lower()
    assert "internal-table" not in rendered
    assert "partner_webhook_subscriptions" not in rendered
