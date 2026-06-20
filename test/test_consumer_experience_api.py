from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routers.consumer_experience as consumer_experience
from utils.security import require_admin_partner_or_consumer_key


def _identity():
    return {"tenant_code": "FNB", "role": "CONSUMER"}


def _admin_identity():
    return {"tenant_code": "INTERNAL", "role": "ADMIN"}


def _client(identity=_identity):
    app = FastAPI()
    app.include_router(consumer_experience.router)
    app.dependency_overrides[require_admin_partner_or_consumer_key] = identity
    return TestClient(app, raise_server_exceptions=False)


def test_get_consumer_experience_returns_aggregate_payload(monkeypatch):
    async def fake_referrals(referrer_ucn, tenant_code):
        return [{"referral_track_id": "track-1", "tenant_code": tenant_code}]

    async def fake_rewards(referrer_ucn, tenant_code=None):
        return {"referrerUcn": referrer_ucn, "currency": "ZAR"}

    async def fake_missions(**kwargs):
        return {"core": [], "boost": [], "milestone": []}

    async def fake_leaderboard(code, referrer_ucn, tenant_code=None):
        return {"leaderboard_code": code, "rank_position": 3}

    async def fake_next_rank(code, referrer_ucn, tenant_code=None):
        return {"points_to_next_rank": 25}

    async def fake_insurance_proof(**kwargs):
        return {"status": "READY", "referral_track_id": kwargs["referral_track_id"]}

    monkeypatch.setattr(
        consumer_experience.dashboard_router,
        "_get_referrals_for_referrer",
        fake_referrals,
    )
    monkeypatch.setattr(
        consumer_experience,
        "get_reward_summary_for_referrer",
        fake_rewards,
    )
    monkeypatch.setattr(consumer_experience, "get_missions_for_referrer", fake_missions)
    monkeypatch.setattr(
        consumer_experience,
        "get_referrer_leaderboard_entry",
        fake_leaderboard,
    )
    monkeypatch.setattr(consumer_experience, "get_next_rank_info", fake_next_rank)
    monkeypatch.setattr(
        consumer_experience,
        "get_consumer_insurance_journey_proof",
        fake_insurance_proof,
    )

    response = _client().get(
        "/v1/experience/consumer",
        params={
            "referrer_ucn": "900010",
            "referral_track_id": "track-1",
            "include_insurance_proof": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["tenantCode"] == "FNB"
    assert body["sections"]["profile"]["data"][0]["referral_track_id"] == "track-1"
    assert body["sections"]["rewards"]["data"]["currency"] == "ZAR"
    assert body["sections"]["leaderboard"]["data"]["nextRank"]["points_to_next_rank"] == 25
    assert body["sections"]["insuranceProof"]["data"]["status"] == "READY"


def test_get_consumer_experience_reports_partial_sections(monkeypatch):
    async def fake_referrals(referrer_ucn, tenant_code):
        return []

    async def fake_rewards(referrer_ucn, tenant_code=None):
        raise RuntimeError("reward service unavailable")

    async def fake_missions(**kwargs):
        return {"core": [], "boost": [], "milestone": []}

    async def fake_leaderboard(code, referrer_ucn, tenant_code=None):
        return None

    monkeypatch.setattr(
        consumer_experience.dashboard_router,
        "_get_referrals_for_referrer",
        fake_referrals,
    )
    monkeypatch.setattr(
        consumer_experience,
        "get_reward_summary_for_referrer",
        fake_rewards,
    )
    monkeypatch.setattr(consumer_experience, "get_missions_for_referrer", fake_missions)
    monkeypatch.setattr(
        consumer_experience,
        "get_referrer_leaderboard_entry",
        fake_leaderboard,
    )

    response = _client().get(
        "/v1/experience/consumer",
        params={"referrer_ucn": "900010"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["sections"]["rewards"]["status"] == "unavailable"
    assert body["sections"]["rewards"]["degraded"] is True
    assert "rewards" in body["unavailableSections"]
    assert body["sections"]["leaderboard"]["status"] == "ok"
    assert body["sections"]["leaderboard"]["data"] is None
    assert body["sections"]["leaderboard"]["degraded"] is False


def test_get_consumer_experience_times_out_slow_sections(monkeypatch):
    async def fake_referrals(referrer_ucn, tenant_code):
        return []

    async def slow_rewards(referrer_ucn, tenant_code=None):
        await asyncio.sleep(0.2)
        return {"currency": "ZAR"}

    async def fake_missions(**kwargs):
        return {"core": []}

    async def fake_leaderboard(code, referrer_ucn, tenant_code=None):
        return None

    monkeypatch.setattr(
        consumer_experience.dashboard_router,
        "_get_referrals_for_referrer",
        fake_referrals,
    )
    monkeypatch.setattr(
        consumer_experience,
        "get_reward_summary_for_referrer",
        slow_rewards,
    )
    monkeypatch.setattr(consumer_experience, "get_missions_for_referrer", fake_missions)
    monkeypatch.setattr(
        consumer_experience,
        "get_referrer_leaderboard_entry",
        fake_leaderboard,
    )

    response = _client().get(
        "/v1/experience/consumer",
        params={"referrer_ucn": "900010", "section_timeout_seconds": 0.05},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["sections"]["profile"]["status"] == "ok"
    assert body["sections"]["missions"]["status"] == "ok"
    assert body["sections"]["rewards"]["status"] == "timeout"
    assert body["sections"]["rewards"]["degraded"] is True
    assert "timed out" in body["sections"]["rewards"]["error"]
    assert body["unavailableSections"] == ["rewards"]


def test_get_consumer_experience_records_aggregate_metrics(monkeypatch):
    section_metrics = []
    request_metrics = []

    async def fake_referrals(referrer_ucn, tenant_code):
        return []

    async def failing_rewards(referrer_ucn, tenant_code=None):
        raise RuntimeError("reward service unavailable")

    async def fake_missions(**kwargs):
        return {"core": []}

    async def fake_leaderboard(code, referrer_ucn, tenant_code=None):
        return None

    def fake_section_observe(**kwargs):
        section_metrics.append(kwargs)

    def fake_request_inc(**kwargs):
        request_metrics.append(kwargs)

    monkeypatch.setattr(
        consumer_experience.dashboard_router,
        "_get_referrals_for_referrer",
        fake_referrals,
    )
    monkeypatch.setattr(
        consumer_experience,
        "get_reward_summary_for_referrer",
        failing_rewards,
    )
    monkeypatch.setattr(consumer_experience, "get_missions_for_referrer", fake_missions)
    monkeypatch.setattr(
        consumer_experience,
        "get_referrer_leaderboard_entry",
        fake_leaderboard,
    )
    monkeypatch.setattr(
        consumer_experience,
        "bff_aggregate_section_observe",
        fake_section_observe,
    )
    monkeypatch.setattr(
        consumer_experience,
        "bff_aggregate_request_inc",
        fake_request_inc,
    )

    response = _client().get(
        "/v1/experience/consumer",
        params={"referrer_ucn": "900010"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "partial"
    assert request_metrics == [
        {"route": "consumer_experience", "tenant": "FNB", "status": "partial"}
    ]

    statuses_by_section = {
        metric["section"]: metric["status"] for metric in section_metrics
    }
    assert statuses_by_section == {
        "profile": "ok",
        "rewards": "unavailable",
        "missions": "ok",
        "leaderboard": "ok",
    }
    assert all(metric["route"] == "consumer_experience" for metric in section_metrics)
    assert all(metric["tenant"] == "FNB" for metric in section_metrics)
    assert all(metric["latency_seconds"] >= 0 for metric in section_metrics)


def test_get_consumer_experience_enforces_tenant_scope():
    response = _client().get(
        "/v1/experience/consumer",
        params={"tenant_code": "PNP", "referrer_ucn": "900010"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "API key is not authorised for this tenant"


def test_get_consumer_experience_allows_admin_tenant_override(monkeypatch):
    async def fake_referrals(referrer_ucn, tenant_code):
        return []

    async def fake_rewards(referrer_ucn, tenant_code=None):
        return {"currency": "ZAR"}

    async def fake_missions(**kwargs):
        return {}

    async def fake_leaderboard(code, referrer_ucn, tenant_code=None):
        return None

    monkeypatch.setattr(
        consumer_experience.dashboard_router,
        "_get_referrals_for_referrer",
        fake_referrals,
    )
    monkeypatch.setattr(
        consumer_experience,
        "get_reward_summary_for_referrer",
        fake_rewards,
    )
    monkeypatch.setattr(consumer_experience, "get_missions_for_referrer", fake_missions)
    monkeypatch.setattr(
        consumer_experience,
        "get_referrer_leaderboard_entry",
        fake_leaderboard,
    )

    response = _client(_admin_identity).get(
        "/v1/experience/consumer",
        params={"tenant_code": "PNP", "referrer_ucn": "900010"},
    )

    assert response.status_code == 200
    assert response.json()["tenantCode"] == "PNP"
