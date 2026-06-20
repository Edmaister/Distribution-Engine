from __future__ import annotations

from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_worker_rejects_missing_secret():
    response = client.post(
        "/worker/referral-events",
        json={"eventType": "REFERRAL_PROGRESS_RECORDED"},
    )

    assert response.status_code in (401, 403)
    body = response.json()
    assert "secret" not in str(body).lower() or "unauthorized" in str(body).lower()


def test_worker_rejects_wrong_secret():
    response = client.post(
        "/worker/referral-events",
        json={
            "eventType": "REFERRAL_PROGRESS_RECORDED",
            "secret": "wrong-secret",
        },
    )

    assert response.status_code in (401, 403)


def test_public_error_does_not_expose_raw_exception(monkeypatch):
    from apps.api.routers import dashboard as dashboard_router

    def boom(referral_track_id):
        raise Exception("database password leaked here")

    monkeypatch.setattr(dashboard_router, "_get_referral_progress", boom)

    response = client.get(
        "/v1/referrals/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/dashboard",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 500
    body = response.json()

    assert "database password leaked here" not in str(body)
    assert "INTERNAL_ERROR" in str(body)
    assert "correlation_id" in body or "correlationId" in body


def test_public_api_does_not_leak_internal_ucn_hashes(monkeypatch):
    from apps.api.routers import recommendations as router

    monkeypatch.setattr(
        router,
        "generate_recommendations_for_referral",
        lambda referral_track_id, channel="API", audit=True, tenant_code=None: [
            {
                "recommendationId": "progress_info",
                "category": "INFO",
                "title": "Your referral progress is available",
                "body": "You can view your current progress and reward conditions.",
                "ctaLabel": "View progress",
                "ctaAction": "VIEW_PROGRESS",
                "priority": 10,
                "rewardPreview": None,
                "disclosures": [],
                "compliance": {
                    "isAdvice": False,
                    "isCreditRelated": False,
                    "requiresDisclaimer": True,
                    "disclaimerCodes": ["GENERAL_INFO_ONLY"],
                    "regulatoryTags": ["TCF"],
                    "pressureScore": 0,
                    "fairnessScore": 100,
                    "transparencyScore": 98,
                    "blocked": False,
                    "blockedReason": None,
                },
                "templateCode": "PROGRESS_INFO",
                "templateVersion": "v1.0",
                "policyVersion": "2026-04-08",
            }
        ],
    )

    response = client.get(
        "/v1/recommendations/track-456",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 200
    text = response.text.lower()

    assert "ucn_hash" not in text
    assert "referrer_ucn_hash" not in text
    assert "referee_ucn_hash" not in text
    assert "account_hash" not in text