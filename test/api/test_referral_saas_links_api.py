from __future__ import annotations

import os

import pytest
from httpx import AsyncClient

os.environ.setdefault("REFERRAL_CODE_SECRET", "test-referral-secret-123456789")

from apps.api.main import app  # noqa: E402
from apps.api.routers import referral_saas_links  # noqa: E402

pytestmark = pytest.mark.asyncio

PARTNER_HEADERS = {"x-api-key": "test-partner-key"}


async def fake_require_valid_tenant(tenant: str) -> str:
    return tenant.upper()


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
