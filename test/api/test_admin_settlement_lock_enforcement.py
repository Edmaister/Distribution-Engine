from __future__ import annotations

import pytest
from fastapi import HTTPException

import apps.api.routers.admin_settlement_lock_enforcement as mod
from services.fulfilment.settlement.lock_enforcement import (
    SettlementPeriodClosedError,
    SettlementPeriodNotFoundError,
)


@pytest.mark.asyncio
async def test_get_lock_status_found(monkeypatch):
    async def fake_get_period_lock_status(period_id: str):
        return {
            "period_id": period_id,
            "status": "OPEN",
            "can_modify": True,
        }

    monkeypatch.setattr(
        mod,
        "get_period_lock_status",
        fake_get_period_lock_status,
    )

    result = await mod.get_lock_status("period-123")

    assert result["period_id"] == "period-123"
    assert result["status"] == "OPEN"
    assert result["can_modify"] is True


@pytest.mark.asyncio
async def test_get_lock_status_not_found(monkeypatch):
    async def fake_get_period_lock_status(period_id: str):
        raise SettlementPeriodNotFoundError(
            f"Settlement period not found: {period_id}"
        )

    monkeypatch.setattr(
        mod,
        "get_period_lock_status",
        fake_get_period_lock_status,
    )

    with pytest.raises(HTTPException) as exc:
        await mod.get_lock_status("missing-period")

    assert exc.value.status_code == 404
    assert exc.value.detail == "Settlement period not found: missing-period"


@pytest.mark.asyncio
async def test_validate_period_modifiable_open(monkeypatch):
    async def fake_ensure_period_not_closed(period_id: str):
        return True

    monkeypatch.setattr(
        mod,
        "ensure_period_not_closed",
        fake_ensure_period_not_closed,
    )

    result = await mod.validate_period_modifiable("period-123")

    assert result == {
        "period_id": "period-123",
        "can_modify": True,
        "message": "Settlement period is modifiable.",
    }


@pytest.mark.asyncio
async def test_validate_period_modifiable_not_found(monkeypatch):
    async def fake_ensure_period_not_closed(period_id: str):
        raise SettlementPeriodNotFoundError(
            f"Settlement period not found: {period_id}"
        )

    monkeypatch.setattr(
        mod,
        "ensure_period_not_closed",
        fake_ensure_period_not_closed,
    )

    with pytest.raises(HTTPException) as exc:
        await mod.validate_period_modifiable("missing-period")

    assert exc.value.status_code == 404
    assert exc.value.detail == "Settlement period not found: missing-period"


@pytest.mark.asyncio
async def test_validate_period_modifiable_closed(monkeypatch):
    async def fake_ensure_period_not_closed(period_id: str):
        raise SettlementPeriodClosedError(
            f"Settlement period {period_id} is CLOSED"
        )

    monkeypatch.setattr(
        mod,
        "ensure_period_not_closed",
        fake_ensure_period_not_closed,
    )

    with pytest.raises(HTTPException) as exc:
        await mod.validate_period_modifiable("period-123")

    assert exc.value.status_code == 409
    assert exc.value.detail == "Settlement period period-123 is CLOSED"