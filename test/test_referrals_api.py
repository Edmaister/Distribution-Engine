from __future__ import annotations

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault(
    "REFERRAL_CODE_SECRET",
    "test-referral-secret-123456789",
)

import apps.api.routers.referrals as mod


@pytest.fixture
def app():
    test_app = FastAPI()
    test_app.include_router(mod.public_router)
    test_app.include_router(mod.router)

    test_app.dependency_overrides[mod.require_partner_key] = lambda: {
        "authenticated": True,
        "tenant_code": "FNB",
        "role": "tenant_user",
    }

    return test_app


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


async def fake_require_valid_tenant(tenant: str) -> str:
    return tenant


def validate_payload(**overrides):
    payload = {
        "tenantCode": "FNB",
        "referralCode": "ABC123",
        "acceptedTerms": True,
        "alias": "test-alias",
        "deviceFingerprint": "device-1",
        "ipAddress": "127.0.0.1",
        "qrCode": "QR001",
    }
    payload.update(overrides)
    return payload


def issue_payload(**overrides):
    payload = {
        "referrer_ucn": "123456789",
        "sticker": "QR001",
        "tenant": "FNB",
        "segment": "PERSONAL",
        "preferred_handle": "edwin",
        "acceptedTerms": True,
    }
    payload.update(overrides)
    return payload


def capture_payload(**overrides):
    payload = {
        "referral_track_id": "track-1",
        "referee_ucn": "987654321",
    }
    payload.update(overrides)
    return payload


def test_validate_success_full_body(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", fake_require_valid_tenant)

    async def fake_validate_referral_code(**kwargs):
        return (
            {
                "valid": True,
                "referral_track_id": "track-1",
                "error_code": None,
                "attributes": {"segment": "PERSONAL"},
                "message": "Referral code validated",
                "validation_outcome": "VALIDATED",
                "alias": "test-alias",
            },
            200,
        )

    monkeypatch.setattr(mod, "validate_referral_code", fake_validate_referral_code)

    res = client.post("/public/referrals/validate", json=validate_payload())

    assert res.status_code == 200
    assert res.json() == {
        "valid": True,
        "referralTrackId": "track-1",
        "message": "Referral code validated",
        "errorCode": None,
        "validationOutcome": "VALIDATED",
        "alias": "test-alias",
        "attributes": {"segment": "PERSONAL"},
    }


def test_validate_adds_default_fields_for_success(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", fake_require_valid_tenant)

    async def fake_validate_referral_code(**kwargs):
        return (
            {
                "referral_track_id": "track-2",
                "alias_value": "alias-from-service",
            },
            201,
        )

    monkeypatch.setattr(mod, "validate_referral_code", fake_validate_referral_code)

    res = client.post("/public/referrals/validate", json=validate_payload())

    assert res.status_code == 201
    body = res.json()
    assert body["valid"] is False
    assert body["referralTrackId"] == "track-2"
    assert body["errorCode"] is None
    assert body["attributes"] == {}
    assert body["message"] == "OK"
    assert body["validationOutcome"] == "FAILED"
    assert body["alias"] == "alias-from-service"


def test_validate_adds_default_fields_for_error(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", fake_require_valid_tenant)

    async def fake_validate_referral_code(**kwargs):
        return (
            {
                "error_code": "INVALID_CODE",
                "attributes": None,
                "message": "",
                "validationOutcome": "",
            },
            400,
        )

    monkeypatch.setattr(mod, "validate_referral_code", fake_validate_referral_code)

    res = client.post("/public/referrals/validate", json=validate_payload())

    assert res.status_code == 400
    body = res.json()
    assert body["valid"] is False
    assert body["errorCode"] == "INVALID_CODE"
    assert body["attributes"] == {}
    assert body["message"] == "Validation failed"
    assert body["validationOutcome"] == "FAILED"


def test_validate_calls_service_with_expected_arguments(client, monkeypatch):
    calls = {}

    async def fake_require_tenant(tenant: str) -> str:
        return "FNB"

    monkeypatch.setattr(mod, "require_valid_tenant", fake_require_tenant)

    async def fake_validate_referral_code(**kwargs):
        calls.update(kwargs)
        return (
            {
                "valid": True,
                "referral_track_id": "track-3",
                "error_code": None,
                "attributes": {},
                "message": "Referral code validated",
                "validation_outcome": "VALIDATED",
                "alias": "alias",
            },
            200,
        )

    monkeypatch.setattr(mod, "validate_referral_code", fake_validate_referral_code)

    res = client.post("/public/referrals/validate", json=validate_payload())

    assert res.status_code == 200
    assert calls == {
        "referral_code": "ABC123",
        "tenant_code": "FNB",
        "accepted_terms": True,
        "alias": "test-alias",
        "device_fingerprint": "device-1",
        "ip_address": "127.0.0.1",
        "qr_code": "QR001",
    }


def test_issue_code_success(client, monkeypatch):
    calls = {}

    async def fake_get_or_create_referrer_code(**kwargs):
        calls.update(kwargs)
        return (
            {
                "referral_code": "ABC123",
                "gaming_handle": "edwin",
                "created": True,
                "message": "created",
                "error_code": None,
            },
            201,
        )

    monkeypatch.setattr(mod, "get_or_create_referrer_code", fake_get_or_create_referrer_code)

    res = client.post("/referrals/codes", json=issue_payload())

    assert res.status_code == 201
    assert res.json()["referral_code"] == "ABC123"
    assert res.json()["gaming_handle"] == "edwin"
    assert calls == {
        "referrer_ucn": "123456789",
        "tenant": "FNB",
        "sticker": "QR001",
        "segment": "PERSONAL",
        "preferred_handle": "edwin",
        "accepted_terms": True,
    }


def test_issue_code_service_status_is_used(client, monkeypatch):
    async def fake_get_or_create_referrer_code(**kwargs):
        return (
            {
                "referral_code": "ABC123",
                "gaming_handle": "edwin",
                "created": False,
                "message": None,
                "error_code": None,
            },
            200,
        )

    monkeypatch.setattr(
        mod,
        "get_or_create_referrer_code",
        fake_get_or_create_referrer_code,
    )

    res = client.post("/referrals/codes", json=issue_payload())

    assert res.status_code == 200
    assert res.json()["created"] is False


def test_capture_ucn_success_full_body(client, monkeypatch):
    calls = {}

    async def fake_capture_referee_ucn(**kwargs):
        calls.update(kwargs)
        return (
            {
                "referral_track_id": "track-1",
                "message": "Referee UCN captured",
                "error_code": None,
            },
            200,
        )

    monkeypatch.setattr(
        mod,
        "capture_referee_ucn",
        fake_capture_referee_ucn,
    )

    res = client.post(
        "/referrals/referees/ucn",
        json=capture_payload(),
    )

    assert res.status_code == 200
    assert res.json() == {
        "referral_track_id": "track-1",
        "message": "Referee UCN captured",
        "error_code": None,
    }
    assert calls == {
        "referral_track_id": "track-1",
        "referee_ucn": "987654321",
        "tenant_code": "FNB",
    }


def test_capture_ucn_adds_default_success_message(client, monkeypatch):
    async def fake_capture_referee_ucn(**kwargs):
        return (
            {
                "referral_track_id": "track-2",
            },
            200,
        )

    monkeypatch.setattr(
        mod,
        "capture_referee_ucn",
        fake_capture_referee_ucn,
    )

    res = client.post(
        "/referrals/referees/ucn",
        json=capture_payload(referral_track_id="track-2"),
    )

    assert res.status_code == 200
    assert res.json()["referral_track_id"] == "track-2"
    assert res.json()["message"] == "OK"
    assert res.json()["error_code"] is None


def test_capture_ucn_adds_default_error_message(client, monkeypatch):
    async def fake_capture_referee_ucn(**kwargs):
        return (
            {
                "referral_track_id": "track-3",
                "error_code": "REFERRAL_TRACK_NOT_FOUND",
                "message": "",
            },
            404,
        )

    monkeypatch.setattr(
        mod,
        "capture_referee_ucn",
        fake_capture_referee_ucn,
    )

    res = client.post(
        "/referrals/referees/ucn",
        json=capture_payload(referral_track_id="track-3"),
    )

    assert res.status_code == 404
    assert res.json()["error_code"] == "REFERRAL_TRACK_NOT_FOUND"
    assert res.json()["message"] == "Update failed"


def test_capture_ucn_service_status_is_used(client, monkeypatch):
    async def fake_capture_referee_ucn(**kwargs):
        return (
            {
                "referral_track_id": "track-4",
                "message": "OK",
                "error_code": None,
            },
            201,
        )

    monkeypatch.setattr(
        mod,
        "capture_referee_ucn",
        fake_capture_referee_ucn,
    )

    res = client.post(
        "/referrals/referees/ucn",
        json=capture_payload(referral_track_id="track-4"),
    )

    assert res.status_code == 201
    assert res.json()["referral_track_id"] == "track-4"