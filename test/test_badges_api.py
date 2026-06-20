from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app
from utils.security import require_admin_or_partner_key

app.dependency_overrides[require_admin_or_partner_key] = lambda: {
    "tenant_code": "FNB",
    "role": "tenant_user",
}

client = TestClient(app)


def _headers():
    return {"x-api-key": "dev-fnb-key-123"}


def test_get_badges_for_referral_returns_404_when_referral_missing(monkeypatch):
    from apps.api.routers import badges as router

    monkeypatch.setattr(router, "_get_referral_row", lambda referral_track_id: None)

    response = client.get("/v1/referrals/missing-track/badges", headers=_headers())

    assert response.status_code == 404
    assert response.json()["detail"] == "Referral track not found"


def test_get_badges_for_referral_returns_badges(monkeypatch):
    from apps.api.routers import badges as router

    monkeypatch.setattr(
        router,
        "_get_referral_row",
        lambda referral_track_id: {
            "referral_track_id": referral_track_id,
            "referrer_ucn": "900008",
        },
    )

    monkeypatch.setattr(
        router,
        "list_badges_for_referral",
        lambda referral_track_id, tenant_code=None: [
            {
                "badgeCode": "FIRST_REFERRAL_CREATED",
                "badgeName": "First Referral Created",
                "badgeDescription": "Created your first referral.",
                "badgeCategory": "REFERRAL_OUTCOME",
                "iconName": "icon-first-referral-created",
                "awardedAt": "2026-04-09T10:00:00+00:00",
                "awardReason": "First referral created",
                "metadata": {},
                "compliance": {
                    "isAdvice": False,
                    "requiresDisclaimer": False,
                    "regulatoryTags": ["TCF", "FAIS", "MARKET_CONDUCT"],
                    "blocked": False,
                    "blockedReason": None,
                },
            }
        ],
    )

    response = client.get("/v1/referrals/track-1/badges", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["badgeCode"] == "FIRST_REFERRAL_CREATED"


def test_get_badges_for_referrer_returns_user_level_badges(monkeypatch):
    from apps.api.routers import badges as router

    monkeypatch.setattr(
        router,
        "list_badges_for_referrer",
        lambda referrer_ucn, tenant_code=None: [
            {
                "badgeCode": "FIRST_SUCCESSFUL_REFERRAL",
                "badgeName": "First Successful Referral",
                "badgeDescription": "Completed your first referral.",
                "badgeCategory": "REFERRAL_OUTCOME",
                "iconName": "icon-first-successful-referral",
                "awardedAt": "2026-04-09T10:00:00+00:00",
                "awardReason": "First successful referral",
                "metadata": {},
                "compliance": {
                    "isAdvice": False,
                    "requiresDisclaimer": False,
                    "regulatoryTags": ["TCF", "FAIS", "MARKET_CONDUCT"],
                    "blocked": False,
                    "blockedReason": None,
                },
            }
        ],
    )

    response = client.get("/v1/users/900008/badges", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["badgeCode"] == "FIRST_SUCCESSFUL_REFERRAL"