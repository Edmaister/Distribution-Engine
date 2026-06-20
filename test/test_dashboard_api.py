from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

import apps.api.routers.dashboard as dashboard_router
from utils.security import (
    require_admin_or_partner_key,
    require_admin_partner_or_consumer_key,
)


def _identity():
    return {"tenant_code": "FNB", "role": "tenant_user"}


def _client():
    app = FastAPI()
    app.include_router(dashboard_router.router)
    app.dependency_overrides[require_admin_or_partner_key] = _identity
    app.dependency_overrides[require_admin_partner_or_consumer_key] = _identity
    return TestClient(app, raise_server_exceptions=False)


def _reward_summary_for_referral(referral_track_id: str):
    return {
        "referralTrackId": referral_track_id,
        "currency": "ZAR",
        "generatedAt": "2026-04-09T10:00:00+00:00",
        "referrer": {
            "earned": 100,
            "pending": 200,
            "nextEligibleReward": 200,
            "totalPotential": 300,
        },
        "referee": {
            "earned": 0,
            "pending": 0,
            "nextEligibleReward": 0,
            "totalPotential": 0,
        },
        "count": 1,
        "items": [
            {
                "beneficiaryType": "REFERRER",
                "rewardType": "CASH",
                "rewardSource": "REFERRAL",
                "status": "EARNED",
                "amount": 100,
                "description": "Completed referral",
                "missionCode": None,
            }
        ],
        "disclosures": [],
        "compliance": {
            "isAdvice": False,
            "requiresDisclaimer": True,
            "disclaimerCodes": [],
            "regulatoryTags": [],
        },
    }


def _reward_summary_for_referrer():
    return {
        "currency": "ZAR",
        "generatedAt": "2026-04-09T10:00:00+00:00",
        "totals": {
            "earned": 100,
            "pending": 200,
            "nextEligibleReward": 200,
            "totalPotential": 300,
        },
        "referralsCount": 2,
        "completedReferralsCount": 1,
        "pendingBonusesCount": 1,
        "count": 3,
        "disclosures": [],
        "compliance": {
            "isAdvice": False,
            "requiresDisclaimer": True,
            "disclaimerCodes": ["GENERAL_INFO_ONLY"],
            "regulatoryTags": ["TCF"],
        },
    }


def _missions():
    return {
        "core": [],
        "boost": [],
        "milestone": [],
    }


def _badge():
    return {
        "badgeCode": "FAST_START",
        "badgeName": "Fast Start",
        "badgeDescription": "Completed quickly",
        "badgeCategory": "PROGRESS",
        "iconName": "star",
        "awardedAt": "2026-04-09T10:00:00+00:00",
        "awardReason": "Completed quickly",
        "metadata": {},
        "compliance": {
            "isAdvice": False,
            "requiresDisclaimer": False,
            "regulatoryTags": [],
            "blocked": False,
            "blockedReason": None,
        },
    }


def _leaderboard_entry():
    return {
        "leaderboard_code": "GLOBAL_TRANSACTIONAL",
        "display_name": "Ed",
        "total_score": 500,
        "referral_score": 300,
        "milestone_score": 100,
        "bonus_score": 100,
        "referrals_count": 2,
        "completed_referrals_count": 1,
        "last_event_at": None,
        "rank_position": 5,
        "rank_tier": "GOLD",
    }


def _next_rank():
    return {
        "next_rank_position": 4,
        "next_rank_score": 600,
        "points_to_next_rank": 100,
    }


def _progress(referral_track_id: str):
    return {
        "referral_track_id": referral_track_id,
        "referrer_ucn": "900010",
        "status": "FUNDED",
        "is_complete": False,
        "progress_percent": 80,
        "progress_band": "HIGH",
        "display_status": "Almost complete",
        "next_milestone": "DEBIT_ORDER_SWITCHED",
    }


def _referrals():
    return [
        {
            "referral_track_id": "track-1",
            "product": "TRANSACTIONAL",
            "sub_product": "GOLD",
            "progress_percent": 100,
            "progress_band": "COMPLETE",
            "display_status": "Complete",
            "next_milestone": None,
            "is_complete": True,
            "created_at": None,
            "updated_at": None,
        }
    ]


def test_get_referral_dashboard_returns_full_payload(monkeypatch):
    referral_track_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

    async def fake_get_referral_progress(referral_track_id, tenant_code=None):
        return _progress(referral_track_id)

    async def fake_get_reward_summary_for_referral(referral_track_id, tenant_code=None):
        return _reward_summary_for_referral(referral_track_id)

    async def fake_get_missions_for_referral(
        referral_track_id,
        tenant_code=None,
        audit=False,
        grouped=True,
    ):
        return _missions()

    monkeypatch.setattr(dashboard_router, "_get_referral_progress", fake_get_referral_progress)
    monkeypatch.setattr(
        dashboard_router,
        "get_reward_summary_for_referral",
        fake_get_reward_summary_for_referral,
    )
    monkeypatch.setattr(dashboard_router, "get_missions_for_referral", fake_get_missions_for_referral)

    response = _client().get(f"/v1/referrals/{referral_track_id}/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["referralTrackId"] == referral_track_id
    assert body["referrerUcn"] == "900010"
    assert body["progress"]["status"] == "FUNDED"
    assert body["rewards"]["currency"] == "ZAR"
    assert len(body["rewards"]["items"]) == 1


def test_get_referral_dashboard_returns_404_for_missing_referral(monkeypatch):
    async def fake_get_referral_progress(referral_track_id, tenant_code=None):
        return None

    monkeypatch.setattr(dashboard_router, "_get_referral_progress", fake_get_referral_progress)

    response = _client().get(
        "/v1/referrals/ffffffff-ffff-ffff-ffff-ffffffffffff/dashboard"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Referral track not found"


def test_get_referral_dashboard_returns_404_when_reward_summary_missing(monkeypatch):
    referral_track_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    async def fake_get_referral_progress(referral_track_id, tenant_code=None):
        return _progress(referral_track_id)

    async def fake_get_reward_summary_for_referral(referral_track_id, tenant_code=None):
        return None

    async def fake_get_missions_for_referral(
        referral_track_id,
        tenant_code=None,
        audit=False,
        grouped=True,
    ):
        return _missions()

    monkeypatch.setattr(dashboard_router, "_get_referral_progress", fake_get_referral_progress)
    monkeypatch.setattr(
        dashboard_router,
        "get_reward_summary_for_referral",
        fake_get_reward_summary_for_referral,
    )
    monkeypatch.setattr(dashboard_router, "get_missions_for_referral", fake_get_missions_for_referral)

    response = _client().get(f"/v1/referrals/{referral_track_id}/dashboard")

    assert response.status_code == 404
    assert response.json()["detail"] in {
        "Reward summary not found",
        "Reward summary not found for referral track",
    }


def test_get_referrer_dashboard_returns_full_payload_with_leaderboard(monkeypatch):
    async def fake_get_referrals_for_referrer(referrer_ucn, tenant_code):
        return _referrals()

    async def fake_get_reward_summary_for_referrer(referrer_ucn, tenant_code=None):
        return _reward_summary_for_referrer()

    async def fake_get_missions_for_referrer(
        referrer_ucn,
        tenant_code=None,
        audit=False,
        grouped=True,
    ):
        return _missions()

    async def fake_list_badges_for_referrer(referrer_ucn, tenant_code=None):
        return [_badge()]

    async def fake_get_referrer_leaderboard_entry(code, referrer_ucn, tenant_code=None):
        return _leaderboard_entry()

    async def fake_get_next_rank_info(code, referrer_ucn, tenant_code=None):
        return _next_rank()

    monkeypatch.setattr(dashboard_router, "_get_referrals_for_referrer", fake_get_referrals_for_referrer)
    monkeypatch.setattr(
        dashboard_router,
        "get_reward_summary_for_referrer",
        fake_get_reward_summary_for_referrer,
    )
    monkeypatch.setattr(dashboard_router, "get_missions_for_referrer", fake_get_missions_for_referrer)
    monkeypatch.setattr(dashboard_router, "list_badges_for_referrer", fake_list_badges_for_referrer)
    monkeypatch.setattr(
        dashboard_router,
        "get_referrer_leaderboard_entry",
        fake_get_referrer_leaderboard_entry,
    )
    monkeypatch.setattr(dashboard_router, "get_next_rank_info", fake_get_next_rank_info)

    response = _client().get("/v1/referrers/900010/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["referrerUcn"] == "900010"
    assert body["summary"]["totalEarned"] == 100
    assert body["summary"]["badgeCount"] == 1
    assert body["summary"]["leaderboardRank"] == 5
    assert body["summary"]["pointsToNextRank"] == 100


def test_get_referrer_dashboard_returns_full_payload_without_leaderboard(monkeypatch):
    async def fake_get_referrals_for_referrer(referrer_ucn, tenant_code):
        rows = _referrals()
        rows[0]["progress_percent"] = None
        return rows

    async def fake_get_reward_summary_for_referrer(referrer_ucn, tenant_code=None):
        return _reward_summary_for_referrer()

    async def fake_get_missions_for_referrer(
        referrer_ucn,
        tenant_code=None,
        audit=False,
        grouped=True,
    ):
        return {}

    async def fake_list_badges_for_referrer(referrer_ucn, tenant_code=None):
        return []

    async def fake_get_referrer_leaderboard_entry(code, referrer_ucn, tenant_code=None):
        return None

    monkeypatch.setattr(dashboard_router, "_get_referrals_for_referrer", fake_get_referrals_for_referrer)
    monkeypatch.setattr(
        dashboard_router,
        "get_reward_summary_for_referrer",
        fake_get_reward_summary_for_referrer,
    )
    monkeypatch.setattr(dashboard_router, "get_missions_for_referrer", fake_get_missions_for_referrer)
    monkeypatch.setattr(dashboard_router, "list_badges_for_referrer", fake_list_badges_for_referrer)
    monkeypatch.setattr(
        dashboard_router,
        "get_referrer_leaderboard_entry",
        fake_get_referrer_leaderboard_entry,
    )

    response = _client().get("/v1/referrers/900010/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["leaderboardRank"] is None
    assert body["leaderboard"]["leaderboardCode"] is None
    assert body["referrals"][0]["progressPercent"] == 0


def test_get_referrer_dashboard_returns_404_when_no_referrals(monkeypatch):
    async def fake_get_referrals_for_referrer(referrer_ucn, tenant_code):
        return []

    monkeypatch.setattr(dashboard_router, "_get_referrals_for_referrer", fake_get_referrals_for_referrer)

    response = _client().get("/v1/referrers/900010/dashboard")

    assert response.status_code == 404
    assert response.json()["detail"] == "No referrals found for referrer"


def test_get_consumer_insurance_proof(monkeypatch):
    calls = {}

    async def fake_get_consumer_insurance_journey_proof(**kwargs):
        calls.update(kwargs)
        return {
            "scope": "consumer",
            "surface": "Consumer Journey",
            "tenant_code": kwargs["tenant_code"],
            "referral_track_id": kwargs["referral_track_id"],
            "status": "READY",
            "reward_amount": "100.00",
            "steps": [{"surface": "Consumer Journey", "status": "READY"}],
        }

    monkeypatch.setattr(
        dashboard_router,
        "get_consumer_insurance_journey_proof",
        fake_get_consumer_insurance_journey_proof,
    )

    response = _client().get(
        "/v1/tenants/FNB/consumer/proof/insurance",
        params={"referral_track_id": "track-123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scope"] == "consumer"
    assert payload["surface"] == "Consumer Journey"
    assert payload["tenant_code"] == "FNB"
    assert payload["referral_track_id"] == "track-123"
    assert payload["steps"][0]["surface"] == "Consumer Journey"
    assert calls == {"tenant_code": "FNB", "referral_track_id": "track-123"}


class FakeAsyncConnection:
    def __init__(self, fetchrow_value=None, fetch_value=None):
        self.fetchrow_value = fetchrow_value
        self.fetch_value = fetch_value or []
        self.executed = []

    async def fetchrow(self, sql, *params):
        self.executed.append(("fetchrow", sql, params))
        return self.fetchrow_value

    async def fetch(self, sql, *params):
        self.executed.append(("fetch", sql, params))
        return self.fetch_value


class FakeAsyncConnectionContext:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


def patch_async_db(monkeypatch, conn):
    def fake_get_async_connection():
        return FakeAsyncConnectionContext(conn)

    monkeypatch.setattr(dashboard_router, "get_async_connection", fake_get_async_connection)


@pytest.mark.asyncio
async def test_get_referrals_for_referrer_queries_db(monkeypatch):
    rows = [{"referral_track_id": "track-1"}]
    conn = FakeAsyncConnection(fetch_value=rows)
    patch_async_db(monkeypatch, conn)

    result = await dashboard_router._get_referrals_for_referrer("900010", "FNB")

    action, sql, params = conn.executed[0]

    assert result == rows
    assert action == "fetch"
    assert "FROM referral_instances" in sql
    assert params == ("900010", "FNB")


@pytest.mark.asyncio
async def test_get_referrals_for_referrer_returns_empty_list_when_db_returns_none(monkeypatch):
    conn = FakeAsyncConnection(fetch_value=[])
    patch_async_db(monkeypatch, conn)

    result = await dashboard_router._get_referrals_for_referrer("900010", "FNB")

    assert result == []


@pytest.mark.asyncio
async def test_get_referral_progress_queries_db(monkeypatch):
    row = {"referral_track_id": "track-1"}
    conn = FakeAsyncConnection(fetchrow_value=row)
    patch_async_db(monkeypatch, conn)

    result = await dashboard_router._get_referral_progress("track-1", "FNB")

    action, sql, params = conn.executed[0]

    assert result == row
    assert action == "fetchrow"
    assert "FROM referral_instances" in sql
    assert params == ("track-1", "FNB")
