from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def _headers():
    return {"x-api-key": "test-partner-key"}


def _mission_item():
    return {
        "missionCode": "FIRST_SALARY_SWITCH",
        "category": "BOOST",
        "scope": "REFERRAL",
        "displayOrder": 1,
        "beneficiaryType": "REFERRER",
        "beneficiaryRef": "ref-hash",
        "title": "Optional mission: first salary switch",
        "body": "If you choose to complete a successful salary switch, you may qualify for a bonus reward.",
        "progressCount": 0,
        "goalCount": 1,
        "progressLabel": "0 / 1",
        "status": "AVAILABLE",
        "isComplete": False,
        "completedAt": None,
        "bonusRewardAmount": 200,
        "rewardLabel": "+ZAR 200",
        "currency": "ZAR",
        "associatedReferralTrackIds": ["track-1"],
        "disclosures": ["General info", "Reward conditional"],
        "compliance": {
            "isAdvice": False,
            "isCreditRelated": False,
            "requiresDisclaimer": True,
            "disclaimerCodes": ["GENERAL_INFO_ONLY", "REWARD_CONDITIONAL"],
            "regulatoryTags": ["TCF", "FAIS"],
            "blocked": False,
            "blockedReason": None,
        },
    }


def test_get_missions_success(monkeypatch):
    from apps.api.routers import missions as router

    async def fake_get_missions_for_referral(
        referral_track_id,
        tenant_code=None,
        channel="API",
        audit=True,
        grouped=False,
    ):
        return [_mission_item()]

    monkeypatch.setattr(
        router,
        "get_missions_for_referral",
        fake_get_missions_for_referral,
    )

    response = client.get("/v1/missions/track-1", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["referralTrackId"] == "track-1"
    assert body["count"] == 1
    assert body["items"][0]["missionCode"] == "FIRST_SALARY_SWITCH"


def test_get_missions_grouped_success(monkeypatch):
    from apps.api.routers import missions as router

    async def fake_get_missions_for_referral(
        referral_track_id,
        tenant_code=None,
        channel="API",
        audit=True,
        grouped=False,
    ):
        return {
            "core": [],
            "boost": [_mission_item()],
            "milestone": [],
        }

    monkeypatch.setattr(
        router,
        "get_missions_for_referral",
        fake_get_missions_for_referral,
    )

    response = client.get(
        "/v1/missions/track-1?grouped=true",
        headers=_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["totalCount"] == 1
    assert body["boost"][0]["missionCode"] == "FIRST_SALARY_SWITCH"


def test_get_missions_404(monkeypatch):
    from apps.api.routers import missions as router

    async def fake_get_missions_for_referral(
        referral_track_id,
        tenant_code=None,
        channel="API",
        audit=True,
        grouped=False,
    ):
        return []

    monkeypatch.setattr(
        router,
        "get_missions_for_referral",
        fake_get_missions_for_referral,
    )

    response = client.get("/v1/missions/missing", headers=_headers())

    assert response.status_code == 404


def test_get_missions_by_referrer(monkeypatch):
    from apps.api.routers import missions as router

    async def fake_get_missions_for_referrer(
        referrer_ucn,
        tenant_code=None,
        channel="API",
        audit=True,
        grouped=True,
    ):
        return {
            "core": [],
            "boost": [_mission_item()],
            "milestone": [],
        }

    monkeypatch.setattr(
        router,
        "get_missions_for_referrer",
        fake_get_missions_for_referrer,
    )

    response = client.get("/v1/missions/referrer/123", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["referrerUCN"] == "123"
    assert body["totalCount"] == 1
    assert body["boost"][0]["missionCode"] == "FIRST_SALARY_SWITCH"