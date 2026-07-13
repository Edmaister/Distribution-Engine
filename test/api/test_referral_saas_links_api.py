from __future__ import annotations

import os

import pytest
from httpx import AsyncClient

os.environ.setdefault("REFERRAL_CODE_SECRET", "test-referral-secret-123456789")

from apps.api.main import app  # noqa: E402
from apps.api.routers import referral_saas_links  # noqa: E402

pytestmark = pytest.mark.asyncio

PARTNER_HEADERS = {"x-api-key": "test-partner-key"}
DISTRIBUTION_ADMIN_HEADERS = {"x-api-key": "test-distribution-admin-key"}


async def fake_require_valid_tenant(tenant: str) -> str:
    return tenant.upper()


def _operator_link_code(*, status: str = "ISSUED") -> dict:
    return {
        "link_code_id": "referrer_codes:code-1",
        "source_type": "REFERRAL_CODE",
        "source": "referrer_codes",
        "tenant_code": "FNB",
        "status": status,
        "code": "REF123",
        "campaign": {"campaign_code": "CAMP001", "campaign_track_id": None},
        "participant": {
            "participant_type": "REFERRER",
            "participant_ref": "SafeHandle",
            "source": "referrer_codes",
        },
        "attribution": {
            "referral_track_id": "track-1",
            "route_id": None,
            "opportunity_id": None,
        },
        "metadata": {},
        "evidence": {
            "referral_code": "REF123",
            "referrer_ucn": "[REDACTED]",
            "referrer_ucn_hash": "[REDACTED]",
        },
        "missing_evidence": [],
        "source_warnings": [],
        "redactions": ["referrer_ucn", "referrer_ucn_hash"],
        "created_at": "2026-06-25T00:00:00+00:00",
        "updated_at": "2026-06-25T00:00:00+00:00",
        "inspected_at": "2026-06-25T00:00:00+00:00",
    }


async def test_referral_saas_issue_wrapper_derives_tenant_and_redacts_response(monkeypatch):
    calls: list[dict] = []

    async def fake_get_or_create_referrer_code(**kwargs):
        calls.append(kwargs)
        return (
            {
                "referral_code": "REF123",
                "gaming_handle": "edwin",
                "created": True,
                "message": "Referral code created",
                "error_code": None,
                "referrer_ucn": "5555555555",
                "referrer_ucn_hash": "secret-hash",
            },
            201,
        )

    monkeypatch.setattr(
        referral_saas_links,
        "get_or_create_referrer_code",
        fake_get_or_create_referrer_code,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/referral-codes",
            json={
                "referrerUcn": "5555555555",
                "sticker": "QR001",
                "segment": "PERSONAL",
                "preferredHandle": "edwin",
                "acceptedTerms": True,
            },
        )

    assert response.status_code == 201
    body = response.json()
    assert body["issue"] == {
        "issueStatus": "CREATED",
        "referralCode": "REF123",
        "publicHandle": "edwin",
        "created": True,
        "sourceType": "REFERRAL_CODE",
        "errorCode": None,
        "message": "Referral code created",
    }
    assert body["account_scope"]["source"] == "identity_tenant"
    assert body["guardrail"].startswith("Referral SaaS issue wrapper")
    assert calls == [
        {
            "referrer_ucn": "5555555555",
            "tenant": "FNB",
            "sticker": "QR001",
            "segment": "PERSONAL",
            "preferred_handle": "edwin",
            "accepted_terms": True,
        }
    ]
    assert "5555555555" not in response.text
    assert "secret-hash" not in response.text


async def test_referral_saas_issue_wrapper_maps_terms_rejection(monkeypatch):
    async def fake_get_or_create_referrer_code(**kwargs):
        return (
            {
                "created": False,
                "message": "Accepted terms are required",
                "error_code": "ACCEPTED_TERMS_REQUIRED",
            },
            400,
        )

    monkeypatch.setattr(
        referral_saas_links,
        "get_or_create_referrer_code",
        fake_get_or_create_referrer_code,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/referral-codes",
            json={
                "referrerUcn": "5555555555",
                "sticker": "QR001",
                "segment": "PERSONAL",
                "acceptedTerms": False,
            },
        )

    assert response.status_code == 400
    assert response.json()["status"] == "rejected"
    assert response.json()["issue"]["issueStatus"] == "REJECTED_TERMS_REQUIRED"


async def test_referral_saas_operator_link_inspect_wraps_read_only_primitive(monkeypatch):
    calls: list[dict] = []

    async def fake_inspect_link_code(**kwargs):
        calls.append(kwargs)
        return _operator_link_code()

    monkeypatch.setattr(
        referral_saas_links,
        "inspect_link_code",
        fake_inspect_link_code,
    )

    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers=DISTRIBUTION_ADMIN_HEADERS,
    ) as client:
        response = await client.get(
            "/v1/referral-saas/operator/links/inspect",
            params={
                "tenant_code": "fnb",
                "source_type": "REFERRAL_CODE",
                "code_or_ref": "REF123",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["inspection"]["inspectionStatus"] == "ISSUED"
    assert body["inspection"]["linkCode"]["status"] == "ISSUED"
    assert body["inspection"]["linkCode"]["evidence"]["referrer_ucn"] == "[REDACTED]"
    assert body["inspection"]["nextDiagnostics"] == [
        {
            "type": "CAMPAIGN_READINESS",
            "label": "Inspect campaign readiness",
            "targetRef": "CAMP001",
        },
        {
            "type": "ATTRIBUTION_TRACE",
            "label": "Inspect attribution trace",
            "targetRef": "track-1",
        },
    ]
    assert body["operator_scope"]["tenant_code"] == "FNB"
    assert body["guardrail"].startswith("Referral SaaS operator link/code inspection")
    assert "mutate" in body["guardrail"]
    assert "replay" in body["guardrail"]
    assert calls == [
        {
            "tenant_code": "FNB",
            "source_type": "REFERRAL_CODE",
            "link_code_id": None,
            "code_or_ref": "REF123",
            "include_evidence": True,
        }
    ]
    assert "900001" not in response.text
    assert "secret" not in response.text.lower()


async def test_referral_saas_operator_link_inspect_preserves_missing_evidence_and_warnings(
    monkeypatch,
):
    async def fake_inspect_link_code(**kwargs):
        result = _operator_link_code(status="UNKNOWN")
        result["campaign"] = {"campaign_code": None, "campaign_track_id": None}
        result["attribution"] = {
            "referral_track_id": None,
            "route_id": None,
            "opportunity_id": None,
        }
        result["missing_evidence"] = [
            {
                "code": "SOURCE_NOT_FOUND",
                "severity": "BLOCKER",
                "source": "referrer_codes",
                "message": "Source evidence was not found for the requested tenant.",
            }
        ]
        result["source_warnings"] = [
            {
                "code": "SOURCE_UNAVAILABLE",
                "severity": "WARNING",
                "source": "referrer_codes",
                "message": "Source evidence could not be inspected safely.",
            }
        ]
        return result

    monkeypatch.setattr(
        referral_saas_links,
        "inspect_link_code",
        fake_inspect_link_code,
    )

    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers=DISTRIBUTION_ADMIN_HEADERS,
    ) as client:
        response = await client.get(
            "/v1/referral-saas/operator/links/inspect",
            params={
                "tenant_code": "FNB",
                "source_type": "REFERRAL_CODE",
                "code_or_ref": "MISSING",
            },
        )

    assert response.status_code == 200
    inspection = response.json()["inspection"]
    assert inspection["inspectionStatus"] == "UNKNOWN"
    assert inspection["linkCode"]["missing_evidence"][0]["code"] == "SOURCE_NOT_FOUND"
    assert inspection["linkCode"]["source_warnings"][0]["code"] == "SOURCE_UNAVAILABLE"
    assert inspection["nextDiagnostics"] == [
        {
            "type": "SUPPORT_TRIAGE",
            "label": "Review missing evidence",
            "targetRef": "referrer_codes:code-1",
        },
        {
            "type": "SOURCE_WARNING",
            "label": "Review source warnings",
            "targetRef": "referrer_codes:code-1",
        },
    ]


async def test_referral_saas_operator_link_inspect_forwards_link_id_and_evidence_flag(
    monkeypatch,
):
    calls: list[dict] = []

    async def fake_inspect_link_code(**kwargs):
        calls.append(kwargs)
        result = _operator_link_code(status="ACTIVE")
        result["evidence"] = None
        return result

    monkeypatch.setattr(
        referral_saas_links,
        "inspect_link_code",
        fake_inspect_link_code,
    )

    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers=DISTRIBUTION_ADMIN_HEADERS,
    ) as client:
        response = await client.get(
            "/v1/referral-saas/operator/links/inspect",
            params={
                "tenant_code": "FNB",
                "source_type": "ROUTE_REFERRAL_LINK",
                "link_code_id": "route-1:track-1",
                "include_evidence": "false",
            },
        )

    assert response.status_code == 200
    assert response.json()["inspection"]["linkCode"]["evidence"] is None
    assert calls == [
        {
            "tenant_code": "FNB",
            "source_type": "ROUTE_REFERRAL_LINK",
            "link_code_id": "route-1:track-1",
            "code_or_ref": None,
            "include_evidence": False,
        }
    ]


async def test_referral_saas_operator_link_inspect_rejects_missing_credentials(
    monkeypatch,
):
    async def fake_inspect_link_code(**kwargs):  # pragma: no cover
        raise AssertionError("service should not be called")

    monkeypatch.setattr(
        referral_saas_links,
        "inspect_link_code",
        fake_inspect_link_code,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/v1/referral-saas/operator/links/inspect",
            params={
                "tenant_code": "FNB",
                "source_type": "REFERRAL_CODE",
                "code_or_ref": "REF123",
            },
        )

    assert response.status_code == 401


async def test_referral_saas_operator_link_inspect_rejects_adjacent_admin_role(
    monkeypatch,
):
    async def fake_inspect_link_code(**kwargs):  # pragma: no cover
        raise AssertionError("service should not be called")

    monkeypatch.setattr(
        referral_saas_links,
        "inspect_link_code",
        fake_inspect_link_code,
    )

    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={"x-api-key": "test-finance-admin-key"},
    ) as client:
        response = await client.get(
            "/v1/referral-saas/operator/links/inspect",
            params={
                "tenant_code": "FNB",
                "source_type": "REFERRAL_CODE",
                "code_or_ref": "REF123",
            },
        )

    assert response.status_code == 403


async def test_referral_saas_operator_link_inspect_returns_safe_validation_error(
    monkeypatch,
):
    async def fake_inspect_link_code(**kwargs):
        raise ValueError("Unsupported link/code source_type: BAD_SOURCE")

    monkeypatch.setattr(
        referral_saas_links,
        "inspect_link_code",
        fake_inspect_link_code,
    )

    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers=DISTRIBUTION_ADMIN_HEADERS,
    ) as client:
        response = await client.get(
            "/v1/referral-saas/operator/links/inspect",
            params={
                "tenant_code": "FNB",
                "source_type": "BAD_SOURCE",
                "code_or_ref": "REF123",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "validation_error",
        "message": "Unsupported link/code source_type: BAD_SOURCE",
    }


async def test_referral_saas_public_validation_wrapper_maps_safe_success(monkeypatch):
    calls: list[dict] = []

    monkeypatch.setattr(
        referral_saas_links,
        "require_valid_tenant",
        fake_require_valid_tenant,
    )

    async def fake_validate_referral_code(**kwargs):
        calls.append(kwargs)
        return (
            {
                "valid": True,
                "validation_outcome": "VALIDATED",
                "referral_track_id": "track-1",
                "alias": "customer-alias",
                "message": "Referral code validated",
                "error_code": None,
                "attributes": {
                    "tenant_code": "FNB",
                    "referrer_ucn": "5555555555",
                    "referrer_ucn_hash": "secret-hash",
                },
            },
            200,
        )

    monkeypatch.setattr(
        referral_saas_links,
        "validate_referral_code",
        fake_validate_referral_code,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/v1/referral-saas/public/referrals/validate",
            json={
                "tenantCode": "fnb",
                "referralCode": "REF123",
                "acceptedTerms": True,
                "alias": "customer-alias",
                "deviceFingerprint": "device-1",
                "ipAddress": "127.0.0.1",
                "qrCode": "QR001",
            },
        )

    assert response.status_code == 200
    assert response.json()["validation"] == {
        "validationStatus": "VALIDATED",
        "valid": True,
        "referralTrackId": "track-1",
        "alias": "customer-alias",
        "errorCode": None,
        "message": "Referral code validated",
        "recovery": None,
        "idempotency": {
            "validationAttemptPolicy": "NEW_JOURNEY_PER_SUCCESSFUL_VALIDATION",
            "duplicateSubmitGuarantee": "NOT_IDEMPOTENT",
            "idempotencyKeySupported": False,
            "safeMessage": (
                "Successful public validation currently records a new referral "
                "journey for each submit. Do not treat repeated validation submits "
                "as idempotent until a schema-backed idempotency key or duplicate "
                "reuse contract is implemented."
            ),
        },
    }
    assert calls == [
        {
            "referral_code": "REF123",
            "tenant_code": "FNB",
            "accepted_terms": True,
            "alias": "customer-alias",
            "device_fingerprint": "device-1",
            "ip_address": "127.0.0.1",
            "qr_code": "QR001",
        }
    ]
    assert "attributes" not in response.json()["validation"]
    assert "5555555555" not in response.text
    assert "secret-hash" not in response.text


async def test_referral_saas_public_validation_wrapper_maps_recovery_state(monkeypatch):
    monkeypatch.setattr(
        referral_saas_links,
        "require_valid_tenant",
        fake_require_valid_tenant,
    )

    async def fake_validate_referral_code(**kwargs):
        return (
            {
                "valid": True,
                "validation_outcome": "FAILED",
                "message": "Referral logging failed",
                "error_code": "REFERRAL_LOG_FAILED",
            },
            200,
        )

    monkeypatch.setattr(
        referral_saas_links,
        "validate_referral_code",
        fake_validate_referral_code,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/v1/referral-saas/public/referrals/validate",
            json={
                "tenantCode": "FNB",
                "referralCode": "REF123",
                "acceptedTerms": True,
                "alias": "customer-alias",
            },
        )

    assert response.status_code == 200
    validation = response.json()["validation"]
    assert validation["validationStatus"] == "RECOVERY_REQUIRED_LOGGING"
    assert validation["valid"] is False
    assert validation["recovery"] == {
        "action": "RETRY_VALIDATION_OR_CONTACT_SUPPORT",
        "safeMessage": "We could not finish setting up this referral. Try again or contact support.",
    }


async def test_referral_saas_referee_ucn_capture_wrapper_derives_tenant_and_redacts(
    monkeypatch,
):
    calls: list[dict] = []

    async def fake_capture_referee_ucn(**kwargs):
        calls.append(kwargs)
        return (
            {
                "referral_track_id": "track-1",
                "message": "Referee UCN captured",
                "error_code": None,
                "referee_ucn": "7777777777",
                "referee_ucn_hash": "secret-hash",
            },
            200,
        )

    monkeypatch.setattr(
        referral_saas_links,
        "capture_referee_ucn",
        fake_capture_referee_ucn,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/referrals/track-1/referee-ucn",
            json={"refereeUcn": "7777777777"},
        )

    assert response.status_code == 200
    assert response.json()["identityCapture"] == {
        "captureStatus": "CAPTURED",
        "referralTrackId": "track-1",
        "errorCode": None,
        "message": "Referee UCN captured",
    }
    assert calls == [
        {
            "referral_track_id": "track-1",
            "referee_ucn": "7777777777",
            "tenant_code": "FNB",
        }
    ]
    assert "7777777777" not in response.text
    assert "secret-hash" not in response.text


async def test_referral_saas_referee_ucn_capture_wrapper_maps_progress_recovery(
    monkeypatch,
):
    async def fake_capture_referee_ucn(**kwargs):
        return (
            {
                "referral_track_id": "track-1",
                "message": "Progress event failed",
                "error_code": "REFEREE_UCN_PROGRESS_EVENT_FAILED",
            },
            500,
        )

    monkeypatch.setattr(
        referral_saas_links,
        "capture_referee_ucn",
        fake_capture_referee_ucn,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/referrals/track-1/referee-ucn",
            json={"refereeUcn": "7777777777"},
        )

    assert response.status_code == 500
    assert response.json()["identityCapture"]["captureStatus"] == "RECOVERY_REQUIRED_PROGRESS_EVENT"
