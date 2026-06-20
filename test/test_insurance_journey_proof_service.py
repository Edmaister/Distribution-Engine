from decimal import Decimal

import pytest

import services.insurance_journey_proof_service as svc


@pytest.mark.asyncio
async def test_insurance_journey_proof_ready(monkeypatch):
    async def fake_money_map(**kwargs):
        assert kwargs["tenant_code"] == "FNB"
        assert kwargs["sponsor_code"] == "INSURECO"
        assert kwargs["distributor_code"] == "DIST-INSURANCE-ADVOCATE"
        return {
            "items": [
                {
                    "referral_track_id": svc.CANONICAL_INSURANCE_PROOF["referral_track_id"],
                    "journey_code": "INSURANCE_POLICY",
                    "product": "INSURANCE",
                    "sponsor_code": "INSURECO",
                    "distributor_code": "DIST-INSURANCE-ADVOCATE",
                    "opportunity_title": "Funeral policy activation",
                    "money_status": "READY",
                    "reward_count": 1,
                    "commission_count": 1,
                    "wallet_movement_count": 1,
                    "invoice_count": 1,
                    "exception_count": 0,
                    "reward_amount": Decimal("250.00"),
                    "commission_amount": Decimal("35.00"),
                    "wallet_movement_amount": Decimal("35.00"),
                    "invoiced_amount": Decimal("250.00"),
                    "settled_amount": Decimal("250.00"),
                }
            ]
        }

    monkeypatch.setattr(svc, "get_outcome_money_map", fake_money_map)

    proof = await svc.get_insurance_journey_proof()

    assert proof["ready"] is True
    assert proof["status"] == "READY"
    assert {step["surface"] for step in proof["steps"]} == {
        "Producer - Supply",
        "Distributor - Demand",
        "Consumer Journey",
        "Amplifi Admin",
    }
    assert all(step["ready"] for step in proof["steps"])


@pytest.mark.asyncio
async def test_insurance_journey_proof_missing(monkeypatch):
    async def fake_money_map(**kwargs):
        return {"items": []}

    monkeypatch.setattr(svc, "get_outcome_money_map", fake_money_map)

    proof = await svc.get_insurance_journey_proof()

    assert proof["ready"] is False
    assert proof["status"] == "MISSING"
    assert proof["steps"][0]["status"] == "MISSING"
