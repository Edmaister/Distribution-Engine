from __future__ import annotations

import os

os.environ.setdefault(
    "REFERRAL_CODE_SECRET",
    "test-secret-key-12345678901234567890",
)

import pytest
import services.composite_code_service as svc


def test_normalize_code():
    assert svc._normalize_code(None) == ""
    assert svc._normalize_code("") == ""
    assert svc._normalize_code(" fnb-abc123 ") == "FNB-ABC123"


def test_derive_tenant_code():
    assert svc._derive_tenant_code("") is None
    assert svc._derive_tenant_code("ABC123") is None
    assert svc._derive_tenant_code("fnb-abc123") == "FNB"
    assert svc._derive_tenant_code("-abc123") is None


@pytest.mark.asyncio
async def test_validate_composite_code_missing_code():
    body, status = await svc.validate_composite_code(
        composite_code="",
        tenant_code="FNB",
    )

    assert status == 422
    assert body["error_code"] == "VALIDATION_ERROR"
    assert body["detail"]["field"] == "composite_code"


@pytest.mark.asyncio
async def test_validate_composite_code_missing_tenant():
    body, status = await svc.validate_composite_code(
        composite_code="ABC123",
        tenant_code=None,
    )

    assert status == 422
    assert body["error_code"] == "VALIDATION_ERROR"
    assert body["detail"]["field"] == "tenant_code"


@pytest.mark.asyncio
async def test_validate_composite_code_success_with_explicit_tenant(monkeypatch):
    async def fake_campaign(**kwargs):
        assert kwargs["tenant_code"] == "FNB"
        assert kwargs["campaign_code"] == "ABC123"
        assert kwargs["metadata"] == {"alias": "Tester"}
        return {
            "valid": True,
            "campaignTrackId": "campaign-track-1",
            "message": "Campaign valid",
            "attributes": {"campaign": True},
        }, 200

    async def fake_referral(**kwargs):
        assert kwargs["tenant_code"] == "FNB"
        assert kwargs["referral_code"] == "ABC123"
        assert kwargs["accepted_terms"] is True
        assert kwargs["alias"] == "Tester"
        return {
            "valid": True,
            "referral_track_id": "referral-track-1",
            "message": "Referral valid",
            "attributes": {"referral": True},
        }, 200

    monkeypatch.setattr(svc, "validate_campaign_and_create_track", fake_campaign)
    monkeypatch.setattr(svc, "validate_referral_code", fake_referral)

    body, status = await svc.validate_composite_code(
        composite_code="abc123",
        tenant_code="fnb",
        attributes={"alias": "Tester"},
    )

    assert status == 200
    assert body["ok"] is True
    assert body["tenant_code"] == "FNB"
    assert body["composite_code"] == "ABC123"
    assert body["campaign"]["valid"] is True
    assert body["campaign"]["campaignTrackId"] == "campaign-track-1"
    assert body["referral"]["valid"] is True
    assert body["referral"]["referralTrackId"] == "referral-track-1"


@pytest.mark.asyncio
async def test_validate_composite_code_success_with_derived_tenant_and_camel_referral(monkeypatch):
    async def fake_campaign(**kwargs):
        return {
            "valid": True,
            "campaign_track_id": "campaign-track-2",
            "reason": "Campaign reason",
        }, 200

    async def fake_referral(**kwargs):
        assert kwargs["device_fingerprint"] == "device-1"
        assert kwargs["ip_address"] == "127.0.0.1"
        assert kwargs["qr_code"] == "qr-1"
        return {
            "valid": True,
            "referralTrackId": "referral-track-2",
            "message": "Referral valid",
        }, 200

    monkeypatch.setattr(svc, "validate_campaign_and_create_track", fake_campaign)
    monkeypatch.setattr(svc, "validate_referral_code", fake_referral)

    body, status = await svc.validate_composite_code(
        composite_code="fnb-abc123",
        tenant_code=None,
        attributes={
            "deviceFingerprint": "device-1",
            "ipAddress": "127.0.0.1",
            "qrCode": "qr-1",
        },
    )

    assert status == 200
    assert body["ok"] is True
    assert body["tenant_code"] == "FNB"
    assert body["campaign"]["campaignTrackId"] == "campaign-track-2"
    assert body["campaign"]["message"] == "Campaign reason"
    assert body["referral"]["referralTrackId"] == "referral-track-2"


@pytest.mark.asyncio
async def test_validate_composite_code_campaign_invalid(monkeypatch):
    async def fake_campaign(**kwargs):
        return {
            "valid": False,
            "reason": "Campaign code not found",
            "error_code": "CAMPAIGN_NOT_FOUND",
        }, 200

    async def fake_referral(**kwargs):
        return {
            "valid": True,
            "referral_track_id": "referral-track-1",
            "message": "Referral valid",
        }, 200

    monkeypatch.setattr(svc, "validate_campaign_and_create_track", fake_campaign)
    monkeypatch.setattr(svc, "validate_referral_code", fake_referral)

    body, status = await svc.validate_composite_code(
        composite_code="FNB-ABC123",
    )

    assert status == 200
    assert body["ok"] is False
    assert body["campaign"]["valid"] is False
    assert body["campaign"]["message"] == "Campaign code not found"
    assert body["campaign"]["errorCode"] == "CAMPAIGN_NOT_FOUND"
    assert body["referral"]["valid"] is True


@pytest.mark.asyncio
async def test_validate_composite_code_referral_invalid(monkeypatch):
    async def fake_campaign(**kwargs):
        return {
            "valid": True,
            "campaignTrackId": "campaign-track-1",
        }, 200

    async def fake_referral(**kwargs):
        return {
            "valid": False,
            "message": "Referral code not found",
            "error_code": "REFERRAL_CODE_NOT_FOUND",
        }, 404

    monkeypatch.setattr(svc, "validate_campaign_and_create_track", fake_campaign)
    monkeypatch.setattr(svc, "validate_referral_code", fake_referral)

    body, status = await svc.validate_composite_code(
        composite_code="FNB-ABC123",
    )

    assert status == 200
    assert body["ok"] is False
    assert body["campaign"]["valid"] is True
    assert body["referral"]["valid"] is False
    assert body["referral"]["message"] == "Referral code not found"
    assert body["referral"]["errorCode"] == "REFERRAL_CODE_NOT_FOUND"


@pytest.mark.asyncio
async def test_validate_composite_code_both_fail_when_status_400(monkeypatch):
    async def fake_campaign(**kwargs):
        return {"valid": True}, 500

    async def fake_referral(**kwargs):
        return {"valid": True}, 400

    monkeypatch.setattr(svc, "validate_campaign_and_create_track", fake_campaign)
    monkeypatch.setattr(svc, "validate_referral_code", fake_referral)

    body, status = await svc.validate_composite_code(
        composite_code="FNB-ABC123",
    )

    assert status == 200
    assert body["ok"] is False
    assert body["campaign"]["valid"] is False
    assert body["referral"]["valid"] is False