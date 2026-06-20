from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routers.composite_codes as mod


@pytest.fixture
def app():
    test_app = FastAPI()
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


def payload(**overrides):
    data = {
        "composite_code": "CMP123",
        "attributes": {"source": "qr"},
        "channel": "MOBILE",
    }
    data.update(overrides)
    return data


def test_validate_composite_code_success_with_channel(client, monkeypatch):
    calls = {}

    def fake_validate_composite_code(**kwargs):
        calls.update(kwargs)
        return (
            {
                "valid": True,
                "composite_code": "CMP123",
                "tenant_code": "FNB",
                "attributes": {"source": "qr", "channel": "APP"},  # ✅ FIXED
                "message": "OK",
                "error_code": None,
            },
            200,
        )

    monkeypatch.setattr(mod, "validate_composite_code", fake_validate_composite_code)

    res = client.post("/composite-codes/validate", json=payload())

    assert res.status_code == 200


def test_validate_composite_code_success_without_attributes_or_channel(client, monkeypatch):
    calls = {}

    def fake_validate_composite_code(**kwargs):
        calls.update(kwargs)
        return (
            {
                "ok": True,
                "tenant_code": "FNB",
                "composite_code": "CMP123456",
                "campaign": {
                    "valid": True,
                    "attributes": {}
                },
                "referral": {
                    "valid": True,
                    "attributes": {}
                },
            },
            200,
        )

    monkeypatch.setattr(mod, "validate_composite_code", fake_validate_composite_code)

    res = client.post(
        "/composite-codes/validate",
        json={
            "composite_code": "CMP999",
            "attributes": None,
            "channel": None,
        },
    )

    assert res.status_code == 200
    assert calls == {
        "composite_code": "CMP999",
        "tenant_code": "FNB",
        "attributes": {},
    }


def test_validate_composite_code_success_with_channel(client, monkeypatch):
    calls = {}

    def fake_validate_composite_code(**kwargs):
        calls.update(kwargs)
        return (
            {
                "ok": True,
                "tenant_code": "FNB",
                "composite_code": "CMP123456",
                "campaign": {"valid": True, "attributes": {}},
                "referral": {"valid": True, "attributes": {}},
            },
            200,
        )

    monkeypatch.setattr(mod, "validate_composite_code", fake_validate_composite_code)

    res = client.post(
        "/composite-codes/validate",
        json={
            "composite_code": "CMP123456",
            "attributes": {"source": "qr"},
            "channel": "APP",
        },
    )

    assert res.status_code == 200
    assert res.json()["ok"] is True


def test_validate_composite_code_error_returns_json_response(client, monkeypatch):
    monkeypatch.setattr(
        mod,
        "validate_composite_code",
        lambda **kwargs: (
            {
                "ok": False,
                "tenant_code": "FNB",
                "composite_code": "BAD123",
                "campaign": {"valid": False, "attributes": {}},
                "referral": {"valid": False, "attributes": {}},
            },
            400,
        ),
    )

    res = client.post(
        "/composite-codes/validate",
        json={
            "composite_code": "BAD123",
            "channel": "APP",
        },
    )

    assert res.status_code == 400
    assert res.json()["ok"] is False


def test_validate_composite_code_missing_required_body_returns_422(client):
    res = client.post("/composite-codes/validate", json={})

    assert res.status_code == 422