from __future__ import annotations

import datetime

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import apps.api.routers.leaderboards as leaderboard_router


def create_client():
    app = FastAPI()
    app.include_router(leaderboard_router.router)
    return TestClient(app)


def _entry(
    *,
    leaderboard_code: str = "GLOBAL_OVERALL",
    display_name: str = "Stormers1",
    rank_position: int | None = 1,
    rank_tier: str = "Platinum",
):
    return {
        "leaderboard_code": leaderboard_code,
        "display_name": display_name,
        "total_score": 220,
        "referral_score": 220,
        "milestone_score": 195,
        "bonus_score": 25,
        "referrals_count": 3,
        "completed_referrals_count": 1,
        "last_event_at": datetime.datetime(
            2026, 4, 6, 17, 41, tzinfo=datetime.timezone.utc
        ),
        "rank_position": rank_position,
        "rank_tier": rank_tier,
    }


def test_enforce_tenant_access_admin_allowed():
    leaderboard_router._enforce_tenant_access(
        {"role": "ADMIN", "tenant_code": "INTERNAL"},
        "FNB",
    )


@pytest.mark.parametrize(
    "identity",
    [
        {"role": "PARTNER", "tenant_code": "PNP"},
        {"role": "PARTNER", "tenant_code": ""},
        {"role": "UNKNOWN", "tenant_code": "FNB"},
    ],
)
def test_enforce_tenant_access_forbidden(identity):
    with pytest.raises(HTTPException) as exc:
        leaderboard_router._enforce_tenant_access(identity, "FNB")

    assert exc.value.status_code == 403
    assert exc.value.detail == "API key is not authorised for this tenant"


def test_read_leaderboard_success(monkeypatch):
    async def fake_get_leaderboard_definition(
        leaderboard_code=None,
        tenant_code=None,
    ):
        return {
            "leaderboard_code": leaderboard_code,
            "tenant_code": tenant_code,
        }

    async def fake_get_leaderboard(
        leaderboard_code=None,
        tenant_code=None,
        limit=10,
        offset=0,
    ):
        return [_entry(leaderboard_code=leaderboard_code)]

    async def fake_get_leaderboard_count(
        leaderboard_code=None,
        tenant_code=None,
    ):
        return 8

    monkeypatch.setattr(
        leaderboard_router,
        "get_leaderboard_definition",
        fake_get_leaderboard_definition,
    )
    monkeypatch.setattr(
        leaderboard_router,
        "get_leaderboard",
        fake_get_leaderboard,
    )
    monkeypatch.setattr(
        leaderboard_router,
        "get_leaderboard_count",
        fake_get_leaderboard_count,
    )

    client = create_client()
    response = client.get(
        "/v1/tenants/FNB/leaderboards/GLOBAL_OVERALL?limit=1&offset=0",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["leaderboardCode"] == "GLOBAL_OVERALL"
    assert body["count"] == 1
    assert body["totalCount"] == 8
    assert body["offset"] == 0
    assert body["limit"] == 1
    assert "generatedAt" in body

    item = body["items"][0]
    assert item["displayName"] == "Stormers1"
    assert item["rankPosition"] == 1
    assert item["rankedTier"] == "Platinum"
    assert "display_name" not in item
    assert "referrer_ucn_hash" not in item


def test_read_leaderboard_success_admin_cross_tenant(monkeypatch):
    async def fake_get_leaderboard_definition(
        leaderboard_code=None,
        tenant_code=None,
    ):
        return {
            "leaderboard_code": leaderboard_code,
            "tenant_code": tenant_code,
        }

    async def fake_get_leaderboard(
        leaderboard_code=None,
        tenant_code=None,
        limit=10,
        offset=0,
    ):
        return [
            _entry(
                leaderboard_code=leaderboard_code,
                display_name="AdminView",
            )
        ]

    async def fake_get_leaderboard_count(
        leaderboard_code=None,
        tenant_code=None,
    ):
        return 1

    monkeypatch.setattr(
        leaderboard_router,
        "get_leaderboard_definition",
        fake_get_leaderboard_definition,
    )
    monkeypatch.setattr(
        leaderboard_router,
        "get_leaderboard",
        fake_get_leaderboard,
    )
    monkeypatch.setattr(
        leaderboard_router,
        "get_leaderboard_count",
        fake_get_leaderboard_count,
    )

    client = create_client()
    response = client.get(
        "/v1/tenants/PNP/leaderboards/GLOBAL_OVERALL?limit=1&offset=0",
        headers={"x-api-key": "test-admin-key"},
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["displayName"] == "AdminView"


def test_read_leaderboard_not_found(monkeypatch):
    async def fake_get_leaderboard_definition(
        leaderboard_code=None,
        tenant_code=None,
    ):
        return None

    monkeypatch.setattr(
        leaderboard_router,
        "get_leaderboard_definition",
        fake_get_leaderboard_definition,
    )

    client = create_client()
    response = client.get(
        "/v1/tenants/FNB/leaderboards/UNKNOWN",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Leaderboard not found"


def test_read_leaderboard_tenant_mismatch_forbidden():
    client = create_client()
    response = client.get(
        "/v1/tenants/PNP/leaderboards/GLOBAL_OVERALL",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "API key is not authorised for this tenant"


def test_read_leaderboard_missing_api_key_unauthorized():
    client = create_client()
    response = client.get(
        "/v1/tenants/FNB/leaderboards/GLOBAL_OVERALL",
    )

    assert response.status_code == 401


def test_read_my_leaderboard_position_success(monkeypatch):
    async def fake_get_leaderboard_definition(
        leaderboard_code=None,
        tenant_code=None,
    ):
        return {
            "leaderboard_code": leaderboard_code,
            "tenant_code": tenant_code,
        }

    async def fake_get_referrer_leaderboard_entry(
        leaderboard_code=None,
        referrer_ucn=None,
        tenant_code=None,
    ):
        return _entry(
            leaderboard_code=leaderboard_code,
            display_name="Lenovo100",
            rank_position=3,
            rank_tier="Bronze",
        )

    async def fake_get_next_rank_info(
        leaderboard_code=None,
        referrer_ucn=None,
        tenant_code=None,
    ):
        return {
            "next_rank_position": 2,
            "next_rank_score": 200,
            "points_to_next_rank": 170,
        }

    monkeypatch.setattr(
        leaderboard_router,
        "get_leaderboard_definition",
        fake_get_leaderboard_definition,
    )
    monkeypatch.setattr(
        leaderboard_router,
        "get_referrer_leaderboard_entry",
        fake_get_referrer_leaderboard_entry,
    )
    monkeypatch.setattr(
        leaderboard_router,
        "get_next_rank_info",
        fake_get_next_rank_info,
    )

    client = create_client()
    response = client.get(
        "/v1/tenants/FNB/leaderboards/GLOBAL_OVERALL/me?referrer_ucn=20260406191654",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["displayName"] == "Lenovo100"
    assert body["rankPosition"] == 3
    assert body["rankedTier"] == "Bronze"
    assert body["nextRankPosition"] == 2
    assert body["nextRankScore"] == 200
    assert body["pointsToNextRank"] == 170
    assert "referrer_ucn_hash" not in body


def test_read_my_leaderboard_position_without_next_info(monkeypatch):
    async def fake_get_leaderboard_definition(
        leaderboard_code=None,
        tenant_code=None,
    ):
        return {
            "leaderboard_code": leaderboard_code,
            "tenant_code": tenant_code,
        }

    async def fake_get_referrer_leaderboard_entry(
        leaderboard_code=None,
        referrer_ucn=None,
        tenant_code=None,
    ):
        return _entry(
            leaderboard_code=leaderboard_code,
            display_name="Stormers1",
        )

    async def fake_get_next_rank_info(
        leaderboard_code=None,
        referrer_ucn=None,
        tenant_code=None,
    ):
        return None

    monkeypatch.setattr(
        leaderboard_router,
        "get_leaderboard_definition",
        fake_get_leaderboard_definition,
    )
    monkeypatch.setattr(
        leaderboard_router,
        "get_referrer_leaderboard_entry",
        fake_get_referrer_leaderboard_entry,
    )
    monkeypatch.setattr(
        leaderboard_router,
        "get_next_rank_info",
        fake_get_next_rank_info,
    )

    client = create_client()
    response = client.get(
        "/v1/tenants/FNB/leaderboards/GLOBAL_OVERALL/me?referrer_ucn=top-user",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["displayName"] == "Stormers1"
    assert body["nextRankPosition"] is None
    assert body["nextRankScore"] is None
    assert body["pointsToNextRank"] is None


def test_read_my_leaderboard_position_leaderboard_not_found(monkeypatch):
    async def fake_get_leaderboard_definition(
        leaderboard_code=None,
        tenant_code=None,
    ):
        return None

    monkeypatch.setattr(
        leaderboard_router,
        "get_leaderboard_definition",
        fake_get_leaderboard_definition,
    )

    client = create_client()
    response = client.get(
        "/v1/tenants/FNB/leaderboards/UNKNOWN/me?referrer_ucn=123",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Leaderboard not found"


def test_read_my_leaderboard_position_entry_not_found(monkeypatch):
    async def fake_get_leaderboard_definition(
        leaderboard_code=None,
        tenant_code=None,
    ):
        return {
            "leaderboard_code": leaderboard_code,
            "tenant_code": tenant_code,
        }

    async def fake_get_referrer_leaderboard_entry(
        leaderboard_code=None,
        referrer_ucn=None,
        tenant_code=None,
    ):
        return None

    monkeypatch.setattr(
        leaderboard_router,
        "get_leaderboard_definition",
        fake_get_leaderboard_definition,
    )
    monkeypatch.setattr(
        leaderboard_router,
        "get_referrer_leaderboard_entry",
        fake_get_referrer_leaderboard_entry,
    )

    client = create_client()
    response = client.get(
        "/v1/tenants/FNB/leaderboards/GLOBAL_OVERALL/me?referrer_ucn=123",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Leaderboard entry not found"


def test_read_my_leaderboard_position_missing_referrer_ucn(monkeypatch):
    async def fake_get_leaderboard_definition(
        leaderboard_code=None,
        tenant_code=None,
    ):
        return {
            "leaderboard_code": leaderboard_code,
            "tenant_code": tenant_code,
        }

    monkeypatch.setattr(
        leaderboard_router,
        "get_leaderboard_definition",
        fake_get_leaderboard_definition,
    )

    client = create_client()
    response = client.get(
        "/v1/tenants/FNB/leaderboards/GLOBAL_OVERALL/me",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 422


def test_read_my_leaderboard_position_tenant_mismatch_forbidden():
    client = create_client()
    response = client.get(
        "/v1/tenants/PNP/leaderboards/GLOBAL_OVERALL/me?referrer_ucn=123",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 403