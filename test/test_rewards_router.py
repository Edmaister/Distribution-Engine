from __future__ import annotations

from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routers.rewards as rewards_router
from services.reward_service import RewardInstruction
from utils.security import require_partner_key


def _identity():
    return {
        "role": "partner",
        "tenant_code": "FNB",
        "partner": "test",
    }


def _payload():
    return {
        "referral_track_id": "track-123",
        "beneficiary_type": "REFERRER",
        "beneficiary_ref": "ucn-hash-123",
        "reward_type": "CASH",
        "product": "TRANSACTIONAL",
        "sub_product": "DDA",
        "amount": "100.00",
    }


def _client():
    app = FastAPI()
    app.include_router(rewards_router.router)
    app.dependency_overrides[require_partner_key] = _identity
    return TestClient(app, raise_server_exceptions=False)


def test_apply_reward_api_success(monkeypatch):
    captured = {}

    async def fake_apply_reward(instruction: RewardInstruction):
        captured["instruction"] = instruction
        return {
            "id": 123,
            "tenant_code": "FNB",
            "referral_track_id": "track-123",
            "beneficiary_type": "REFERRER",
            "beneficiary_ref": "ucn-hash-123",
            "product": "TRANSACTIONAL",
            "sub_product": "DDA",
            "reward_type": "CASH",
            "amount": 100.0,
            "status": "APPLIED",
            "reward_source": "BASE",
            "mission_code": None,
        }

    monkeypatch.setattr(rewards_router, "apply_reward", fake_apply_reward)

    res = _client().post("/rewards/apply", json=_payload())

    assert res.status_code == 200
    assert res.json()["id"] == 123

    instruction = captured["instruction"]
    assert instruction == RewardInstruction(
        tenant_code="FNB",
        referral_track_id="track-123",
        beneficiary_type="REFERRER",
        beneficiary_ref="ucn-hash-123",
        product="TRANSACTIONAL",
        sub_product="DDA",
        reward_type="CASH",
        amount=instruction.amount,
    )
    assert str(instruction.amount) == "100.00"


def test_apply_reward_api_returns_400_for_invalid_instruction(monkeypatch):
    apply_reward = AsyncMock(side_effect=ValueError("amount must be > 0"))
    monkeypatch.setattr(rewards_router, "apply_reward", apply_reward)

    payload = _payload()
    payload["amount"] = "0"

    res = _client().post("/rewards/apply", json=payload)

    assert res.status_code == 400
    assert res.json()["detail"] == "amount must be > 0"


def test_apply_reward_api_requires_instruction_fields():
    payload = _payload()
    del payload["beneficiary_ref"]

    res = _client().post("/rewards/apply", json=payload)

    assert res.status_code == 422
