from __future__ import annotations

import pytest

import services.reward_summary_service as svc


@pytest.mark.asyncio
async def test_get_reward_summary_missing(monkeypatch):
    async def fake_get_referral_row(referral_track_id, tenant_code=None):
        return None

    monkeypatch.setattr(svc, "_get_referral_row", fake_get_referral_row)

    result = await svc.get_reward_summary_for_referral("missing", tenant_code="FNB")

    assert result is None


@pytest.mark.asyncio
async def test_get_reward_summary(monkeypatch):
    async def fake_get_referral_row(referral_track_id, tenant_code=None):
        return {
            "referral_track_id": referral_track_id,
            "product": "TRANSACTIONAL",
            "sub_product": "GOLD",
            "referrer_ucn_hash": "ref-hash",
            "referee_ucn_hash": "refee-hash",
            "next_milestone": "SALARY_SWITCHED",
        }

    async def fake_get_reward_rows(referral_track_id, tenant_code=None):
        return [
            {
                "beneficiary_type": "REFERRER",
                "reward_type": "BASE",
                "reward_source": "BASE",
                "status": "APPLIED",
                "amount": 250,
                "mission_code": None,
            },
            {
                "beneficiary_type": "REFEREE",
                "reward_type": "WELCOME",
                "reward_source": "BASE",
                "status": "APPLIED",
                "amount": 100,
                "mission_code": None,
            },
        ]

    async def fake_get_pending_mission_bonus_rows(referral_track_id, tenant_code=None):
        return [
            {
                "beneficiary_type": "REFERRER",
                "mission_code": "FIRST_SALARY_SWITCH",
                "amount": 200,
            }
        ]

    async def fake_get_reward_disclosures(codes):
        return [f"DISCLOSURE::{code}" for code in codes]

    monkeypatch.setattr(svc, "_get_referral_row", fake_get_referral_row)
    monkeypatch.setattr(svc, "_get_reward_rows", fake_get_reward_rows)
    monkeypatch.setattr(
        svc,
        "_get_pending_mission_bonus_rows",
        fake_get_pending_mission_bonus_rows,
    )
    monkeypatch.setattr(svc, "_get_reward_disclosures", fake_get_reward_disclosures)

    result = await svc.get_reward_summary_for_referral("track-1", tenant_code="FNB")

    assert result is not None
    assert result["referrer"]["earned"] == 250
    assert result["referrer"]["pending"] == 200
    assert result["referrer"]["nextEligibleReward"] == 200
    assert result["referrer"]["totalPotential"] == 450
    assert result["referee"]["earned"] == 100
    assert result["count"] == 3