from __future__ import annotations

import pytest
from httpx import AsyncClient

from apps.api.main import app
from services import webhook_event_catalog as catalog

pytestmark = pytest.mark.asyncio

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}
SYSTEM_ADMIN_HEADERS = {"x-api-key": "test-system-admin-key"}


async def test_admin_can_list_webhook_event_catalog():
    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get("/admin/webhooks/event-catalog")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["catalog"]["schema_version"] == "2026-06-22"
    assert body["catalog"]["family_filter"] is None
    assert body["catalog"]["event_count"] == len(catalog.CATALOG_EVENT_TYPES)
    assert "campaign" in body["catalog"]["families"]
    assert "OUTCOME_COMPLETED" in {
        event["event_type"] for event in body["catalog"]["events"]
    }
    assert "outcome" in body["catalog"]["events_by_family"]
    assert body["guardrail"].startswith("Read-only webhook event catalog")


async def test_admin_can_filter_webhook_event_catalog_by_family():
    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/webhooks/event-catalog",
            params={"family": " fulfilment "},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["catalog"]["family_filter"] == "fulfilment"
    assert body["catalog"]["event_count"] > 0
    assert set(body["catalog"]["events_by_family"]) == {"fulfilment"}
    assert {event["family"] for event in body["catalog"]["events"]} == {"fulfilment"}


async def test_webhook_event_catalog_rejects_unknown_family():
    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/webhooks/event-catalog",
            params={"family": "raw_payload"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "validation_error",
        "message": "Unsupported webhook event family: raw_payload",
    }


async def test_webhook_event_catalog_returns_401_without_credentials():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/admin/webhooks/event-catalog")

    assert response.status_code == 401


async def test_webhook_event_catalog_rejects_partner_identity():
    async with AsyncClient(
        app=app, base_url="http://test", headers={"x-api-key": "test-partner-key"}
    ) as client:
        response = await client.get("/admin/webhooks/event-catalog")

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "code": "permission_denied",
        "message": "API key is not authorised for webhook catalog access.",
    }


def test_webhook_event_catalog_api_fixture_has_no_unsafe_names():
    rendered = str(catalog.list_catalog_events())

    assert "SIGNING_SECRET" not in rendered
    assert "ACCESS_TOKEN" not in rendered
    assert "RAW_PROVIDER_PAYLOAD" not in rendered
    assert "PARTNER_WEBHOOK_DELIVERIES" not in rendered


async def test_admin_can_preview_campaign_webhook_payload():
    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/webhooks/payload-preview",
            params={
                "event_type": catalog.CAMPAIGN_PUBLISHED,
                "external_tenant_ref": "partner-fnb",
                "subject_id": "campaign-safe-1",
                "correlation_id": "corr-1",
                "source_event_id": "source-1",
                "idempotency_key": "campaign-preview-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["delivery_mode"] == "preview_only"
    assert body["payload"]["event_type"] == catalog.CAMPAIGN_PUBLISHED
    assert body["payload"]["event_family"] == "campaign"
    assert body["payload"]["tenant"] == {"external_tenant_ref": "partner-fnb"}
    assert body["payload"]["subject"] == {
        "type": "campaign",
        "id": "campaign-safe-1",
    }
    assert body["payload"]["correlation"]["correlation_id"] == "corr-1"
    assert body["payload"]["correlation"]["source_event_id"] == "source-1"
    assert body["payload"]["correlation"]["idempotency_key"] == "campaign-preview-1"
    assert body["payload"]["metadata"] == {
        "preview": True,
        "delivery": "none",
        "surface": "admin_webhook_payload_preview",
    }
    assert body["guardrail"].startswith("Non-delivering webhook payload preview")
    assert "tenant_code" not in str(body).lower()


async def test_admin_can_preview_outcome_webhook_payload_with_redactions():
    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/webhooks/payload-preview",
            params=[
                ("event_type", catalog.OUTCOME_COMPLETED),
                ("external_tenant_ref", "partner-fnb"),
                ("subject_id", "outcome-safe-1"),
                ("redactions", "ucn"),
                ("redactions", "raw_provider_payload"),
            ],
        )

    assert response.status_code == 200
    body = response.json()
    assert body["payload"]["event_type"] == catalog.OUTCOME_COMPLETED
    assert body["payload"]["event_family"] == "outcome"
    assert body["payload"]["subject"] == {
        "type": "outcome",
        "id": "outcome-safe-1",
    }
    assert body["payload"]["redactions"] == ["raw_provider_payload", "ucn"]


@pytest.mark.parametrize(
    "event_type",
    [
        catalog.REWARD_APPLIED,
        catalog.FULFILMENT_SUCCEEDED,
        "UNKNOWN_EVENT",
        "RAW_PROVIDER_PAYLOAD_FAILED",
    ],
)
async def test_webhook_payload_preview_rejects_unsupported_or_unsafe_events(
    event_type,
):
    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/webhooks/payload-preview",
            params={
                "event_type": event_type,
                "external_tenant_ref": "partner-fnb",
                "subject_id": "safe-subject-1",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "validation_error",
        "message": (
            "Webhook payload preview only supports campaign and outcome events."
        ),
    }


async def test_webhook_payload_preview_rejects_missing_external_tenant_ref():
    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/webhooks/payload-preview",
            params={
                "event_type": catalog.OUTCOME_COMPLETED,
                "external_tenant_ref": " ",
                "subject_id": "outcome-safe-1",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "validation_error",
        "message": "external_tenant_ref is required for webhook payloads.",
    }


async def test_webhook_payload_preview_returns_401_without_credentials():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/admin/webhooks/payload-preview",
            params={
                "event_type": catalog.OUTCOME_COMPLETED,
                "external_tenant_ref": "partner-fnb",
                "subject_id": "outcome-safe-1",
            },
        )

    assert response.status_code == 401


async def test_webhook_payload_preview_rejects_partner_identity():
    async with AsyncClient(
        app=app, base_url="http://test", headers={"x-api-key": "test-partner-key"}
    ) as client:
        response = await client.get(
            "/admin/webhooks/payload-preview",
            params={
                "event_type": catalog.OUTCOME_COMPLETED,
                "external_tenant_ref": "partner-fnb",
                "subject_id": "outcome-safe-1",
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "code": "permission_denied",
        "message": "API key is not authorised for webhook catalog access.",
    }
