from fastapi.testclient import TestClient

from apps.api.main import app
import apps.api.routers.referral_bootstrap as rb


def build_test_client():
    return TestClient(app, raise_server_exceptions=False)


def override_partner_key():
    return {
        "authenticated": True,
        "tenant_code": "DEFAULT",
        "role": "tenant_user",
    }


def setup_auth_override():
    app.dependency_overrides[rb.require_partner_key] = override_partner_key


def teardown_auth_override():
    app.dependency_overrides.clear()


def bootstrap_payload(referrer_ucn="12345678901"):
    return {
        "referrerUcn": referrer_ucn,
        "tenantCode": "DEFAULT",
    }


def test_bootstrap_endpoint_returns_existing_referrer(monkeypatch):
    setup_auth_override()
    client = build_test_client()

    async def fake_bootstrap_referrer_profile(referrer_ucn: str, tenant_code: str):
        assert referrer_ucn == "12345678901"
        assert tenant_code == "DEFAULT"
        return {
            "referrerUcn": "12345678901",
            "tenantCode": "DEFAULT",
            "exists": True,
            "referralCode": "ABC12345",
            "alias": "Stormers1",
            "acceptedTerms": True,
            "requiresTermsAcceptance": False,
            "qrEligible": True,
            "message": "Existing referrer profile found",
        }

    monkeypatch.setattr(
        rb,
        "bootstrap_referrer_profile",
        fake_bootstrap_referrer_profile,
    )

    response = client.post("/referrals/bootstrap", json=bootstrap_payload())

    teardown_auth_override()

    assert response.status_code == 200
    body = response.json()
    assert body["exists"] is True
    assert body["alias"] == "Stormers1"


def test_bootstrap_endpoint_creates_new_referrer(monkeypatch):
    setup_auth_override()
    client = build_test_client()

    async def fake_bootstrap_referrer_profile(referrer_ucn: str, tenant_code: str):
        return {
            "referrerUcn": referrer_ucn,
            "tenantCode": tenant_code,
            "exists": False,
            "referralCode": None,
            "alias": None,
            "acceptedTerms": False,
            "requiresTermsAcceptance": False,
            "qrEligible": False,
            "message": "Referrer profile does not exist",
        }

    monkeypatch.setattr(
        rb,
        "bootstrap_referrer_profile",
        fake_bootstrap_referrer_profile,
    )

    response = client.post(
        "/referrals/bootstrap",
        json=bootstrap_payload("99999999999"),
    )

    teardown_auth_override()

    assert response.status_code == 200
    body = response.json()
    assert body["exists"] is False
    assert body["qrEligible"] is False


def test_bootstrap_endpoint_returns_400_on_bootstrap_error(monkeypatch):
    setup_auth_override()
    client = build_test_client()

    async def fake_bootstrap_referrer_profile(referrer_ucn: str, tenant_code: str):
        raise rb.ReferralBootstrapError("bad request")

    monkeypatch.setattr(
        rb,
        "bootstrap_referrer_profile",
        fake_bootstrap_referrer_profile,
    )

    response = client.post("/referrals/bootstrap", json=bootstrap_payload())

    teardown_auth_override()

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid request"


def test_bootstrap_endpoint_returns_500_on_unexpected_error(monkeypatch):
    setup_auth_override()
    client = build_test_client()

    async def fake_bootstrap_referrer_profile(referrer_ucn: str, tenant_code: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        rb,
        "bootstrap_referrer_profile",
        fake_bootstrap_referrer_profile,
    )

    response = client.post(
        "/referrals/bootstrap",
        json=bootstrap_payload(),
        headers={"X-Request-ID": "cid-bootstrap"},
    )

    teardown_auth_override()

    assert response.status_code == 500
    body = response.json()
    assert body["detail"]["error"] == "INTERNAL_ERROR"
    assert body["detail"]["correlation_id"] in {"cid-bootstrap", "unknown"}


def test_bootstrap_endpoint_missing_body_returns_422():
    setup_auth_override()
    client = build_test_client()

    response = client.post("/referrals/bootstrap", json={})

    teardown_auth_override()

    assert response.status_code == 422


def test_accept_terms_success(monkeypatch):
    setup_auth_override()
    client = build_test_client()

    async def fake_accept_terms(referrer_ucn: str, tenant_code: str):
        assert referrer_ucn == "12345678901"
        assert tenant_code == "DEFAULT"
        return {
            "referrerUcn": "12345678901",
            "tenantCode": "DEFAULT",
            "acceptedTerms": True,
            "acceptedTermsAt": "2026-05-04T10:00:00",
            "message": "Terms accepted successfully",
        }

    monkeypatch.setattr(
        rb,
        "accept_terms",
        fake_accept_terms,
    )

    response = client.post(
        "/referrals/accept-terms",
        json=bootstrap_payload(),
    )

    teardown_auth_override()

    assert response.status_code == 200
    body = response.json()
    assert body["acceptedTerms"] is True
    assert body["message"] == "Terms accepted successfully"


def test_accept_terms_returns_404_on_bootstrap_error(monkeypatch):
    setup_auth_override()
    client = build_test_client()

    async def fake_accept_terms(referrer_ucn: str, tenant_code: str):
        raise rb.ReferralBootstrapError("not found")

    monkeypatch.setattr(
        rb,
        "accept_terms",
        fake_accept_terms,
    )

    response = client.post(
        "/referrals/accept-terms",
        json=bootstrap_payload(),
    )

    teardown_auth_override()

    assert response.status_code == 404
    assert response.json()["detail"] == "Not found"


def test_accept_terms_returns_500_on_unexpected_error(monkeypatch):
    setup_auth_override()
    client = build_test_client()

    async def fake_accept_terms(referrer_ucn: str, tenant_code: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        rb,
        "accept_terms",
        fake_accept_terms,
    )

    response = client.post(
        "/referrals/accept-terms",
        json=bootstrap_payload(),
        headers={"X-Request-ID": "cid-accept"},
    )

    teardown_auth_override()

    assert response.status_code == 500
    body = response.json()
    assert body["detail"]["error"] == "INTERNAL_ERROR"
    assert body["detail"]["correlation_id"] in {"cid-accept", "unknown"}


def test_accept_terms_missing_body_returns_422():
    setup_auth_override()
    client = build_test_client()

    response = client.post("/referrals/accept-terms", json={})

    teardown_auth_override()

    assert response.status_code == 422