from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
import services.reward_summary_service as svc

client = TestClient(app)


@pytest.mark.asyncio
async def test_get_reward_summary_success(monkeypatch):
    from apps.api.routers import reward_summary as router

    async def fake_get_reward_summary_for_referral(referral_track_id, tenant_code=None):
        return {
            "referralTrackId": referral_track_id,
            "currency": "ZAR",
            "generatedAt": "2026-04-08T10:00:00Z",
            "referrer": {
                "earned": 250,
                "pending": 200,
                "nextEligibleReward": 200,
                "totalPotential": 450,
            },
            "referee": {
                "earned": 100,
                "pending": 0,
                "nextEligibleReward": 0,
                "totalPotential": 100,
            },
            "count": 3,
            "items": [
                {
                    "beneficiaryType": "REFERRER",
                    "rewardType": "BASE",
                    "rewardSource": "BASE",
                    "status": "APPLIED",
                    "amount": 250,
                    "description": "Base referral reward",
                    "missionCode": None,
                }
            ],
            "disclosures": ["General info", "Reward conditional"],
            "compliance": {
                "isAdvice": False,
                "requiresDisclaimer": True,
                "disclaimerCodes": ["GENERAL_INFO_ONLY", "REWARD_CONDITIONAL"],
                "regulatoryTags": ["TCF", "FAIS"],
            },
        }

    monkeypatch.setattr(
        router,
        "get_reward_summary_for_referral",
        fake_get_reward_summary_for_referral,
    )

    response = client.get(
        "/v1/rewards/summary/track-1",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["referralTrackId"] == "track-1"
    assert body["referrer"]["earned"] == 250
    assert body["referee"]["earned"] == 100


@pytest.mark.asyncio
async def test_get_reward_summary_404(monkeypatch):
    from apps.api.routers import reward_summary as router

    async def fake_get_reward_summary_for_referral(referral_track_id, tenant_code=None):
        return None

    monkeypatch.setattr(
        router,
        "get_reward_summary_for_referral",
        fake_get_reward_summary_for_referral,
    )

    response = client.get(
        "/v1/rewards/summary/missing",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_reward_summary_for_referrer(monkeypatch):
    async def fake_get_reward_rows_for_referrer(referrer_ucn, tenant_code=None):
        return [
            {
                "beneficiary_type": "REFERRER",
                "reward_type": "BASE",
                "reward_source": "BASE",
                "status": "APPLIED",
                "amount": 300,
                "mission_code": None,
            }
        ]

    async def fake_get_pending_mission_bonus_rows_for_referrer(
        referrer_ucn,
        tenant_code=None,
    ):
        return [
            {
                "beneficiary_type": "REFERRER",
                "mission_code": "COMPLETE_1_REFERRAL",
                "amount": 150,
            }
        ]

    async def fake_get_referral_counts_for_referrer(referrer_ucn, tenant_code=None):
        return {
            "referralsCount": 4,
            "completedReferralsCount": 2,
        }

    async def fake_get_reward_disclosures(codes):
        return [f"DISCLOSURE::{code}" for code in codes]

    monkeypatch.setattr(
        svc,
        "_get_reward_rows_for_referrer",
        fake_get_reward_rows_for_referrer,
    )
    monkeypatch.setattr(
        svc,
        "_get_pending_mission_bonus_rows_for_referrer",
        fake_get_pending_mission_bonus_rows_for_referrer,
    )
    monkeypatch.setattr(
        svc,
        "_get_referral_counts_for_referrer",
        fake_get_referral_counts_for_referrer,
    )
    monkeypatch.setattr(
        svc,
        "_get_reward_disclosures",
        fake_get_reward_disclosures,
    )

    result = await svc.get_reward_summary_for_referrer("123", tenant_code="FNB")

    assert result["totals"]["earned"] == 300
    assert result["totals"]["pending"] == 150
    assert result["totals"]["nextEligibleReward"] == 150
    assert result["totals"]["totalPotential"] == 450
    assert result["referralsCount"] == 4
    assert result["completedReferralsCount"] == 2
    assert result["pendingBonusesCount"] == 1
    assert result["count"] == 2


def test_build_description_variants():
    assert (
        svc._build_description(
            {"reward_source": "MISSION_BONUS", "beneficiary_type": "REFERRER"}
        )
        == "Optional mission bonus reward"
    )

    assert (
        svc._build_description(
            {"reward_source": "BASE", "beneficiary_type": "REFEREE"}
        )
        == "Referee reward"
    )

    assert (
        svc._build_description(
            {"reward_source": "BASE", "beneficiary_type": "REFERRER"}
        )
        == "Base referral reward"
    )


def test_blank_totals():
    assert svc._blank_totals() == {
        "earned": 0,
        "pending": 0,
        "nextEligibleReward": 0,
        "totalPotential": 0,
    }


def test_compliance_payload():
    payload = svc._build_compliance_payload()

    assert payload["isAdvice"] is False
    assert payload["requiresDisclaimer"] is True
    assert "GENERAL_INFO_ONLY" in payload["disclaimerCodes"]


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

    monkeypatch.setattr(svc, "get_async_connection", fake_get_async_connection)


@pytest.mark.asyncio
async def test_get_reward_rows(monkeypatch):
    rows = [{"beneficiary_type": "REFERRER", "amount": 100}]
    conn = FakeAsyncConnection(fetch_value=rows)
    patch_async_db(monkeypatch, conn)

    result = await svc._get_reward_rows("track-1", tenant_code="FNB")

    assert result == rows


@pytest.mark.asyncio
async def test_get_referral_row(monkeypatch):
    row = {"referral_track_id": "track-1", "referrer_ucn": "123"}
    conn = FakeAsyncConnection(fetchrow_value=row)
    patch_async_db(monkeypatch, conn)

    result = await svc._get_referral_row("track-1", tenant_code="FNB")

    assert result == row


@pytest.mark.asyncio
async def test_get_pending_mission_bonus_rows(monkeypatch):
    rows = [{"beneficiary_type": "REFERRER", "mission_code": "M1", "amount": 50}]
    conn = FakeAsyncConnection(fetch_value=rows)
    patch_async_db(monkeypatch, conn)

    result = await svc._get_pending_mission_bonus_rows("track-1", tenant_code="FNB")

    assert result == rows


@pytest.mark.asyncio
async def test_get_reward_rows_for_referrer(monkeypatch):
    rows = [
        {
            "referral_track_id": "track-1",
            "beneficiary_type": "REFERRER",
            "amount": 100,
        }
    ]
    conn = FakeAsyncConnection(fetch_value=rows)
    patch_async_db(monkeypatch, conn)

    result = await svc._get_reward_rows_for_referrer("123", tenant_code="FNB")

    assert result == rows


@pytest.mark.asyncio
async def test_get_pending_mission_bonus_rows_for_referrer(monkeypatch):
    rows = [{"referral_track_id": "track-1", "mission_code": "M1", "amount": 50}]
    conn = FakeAsyncConnection(fetch_value=rows)
    patch_async_db(monkeypatch, conn)

    result = await svc._get_pending_mission_bonus_rows_for_referrer(
        "123",
        tenant_code="FNB",
    )

    assert result == rows


@pytest.mark.asyncio
async def test_get_referral_counts_for_referrer(monkeypatch):
    conn = FakeAsyncConnection(
        fetchrow_value={
            "referrals_count": 5,
            "completed_referrals_count": 3,
        }
    )
    patch_async_db(monkeypatch, conn)

    result = await svc._get_referral_counts_for_referrer("123", tenant_code="FNB")

    assert result == {
        "referralsCount": 5,
        "completedReferralsCount": 3,
    }


@pytest.mark.asyncio
async def test_get_reward_disclosures_empty():
    assert await svc._get_reward_disclosures([]) == []


@pytest.mark.asyncio
async def test_get_reward_disclosures(monkeypatch):
    rows = [
        {"disclosure_code": "A", "disclosure_text": "Disclosure A"},
        {"disclosure_code": "B", "disclosure_text": "Disclosure B"},
    ]
    conn = FakeAsyncConnection(fetch_value=rows)
    patch_async_db(monkeypatch, conn)

    result = await svc._get_reward_disclosures(["B", "A"])

    assert result == ["Disclosure B", "Disclosure A"]