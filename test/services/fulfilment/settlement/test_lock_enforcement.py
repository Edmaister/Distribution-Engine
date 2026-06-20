from __future__ import annotations

import pytest

from services.fulfilment.settlement.lock_enforcement import (
    SettlementPeriodClosedError,
    SettlementPeriodNotFoundError,
    ensure_period_not_closed,
    ensure_period_open,
    get_period_lock_status,
)


def period(status: str = "OPEN") -> dict:
    return {
        "period_id": "period-123",
        "tenant_code": "FNB",
        "period_code": "2026-01",
        "status": status,
    }


@pytest.mark.asyncio
async def test_get_period_lock_status_open(monkeypatch):
    async def fake_get_settlement_period(period_id: str):
        return period("OPEN")

    monkeypatch.setattr(
        "services.fulfilment.settlement.lock_enforcement.get_settlement_period",
        fake_get_settlement_period,
    )

    result = await get_period_lock_status("period-123")

    assert result["period_id"] == "period-123"
    assert result["tenant_code"] == "FNB"
    assert result["period_code"] == "2026-01"
    assert result["status"] == "OPEN"
    assert result["is_open"] is True
    assert result["is_closed"] is False
    assert result["is_locked"] is False
    assert result["can_modify"] is True


@pytest.mark.asyncio
async def test_get_period_lock_status_certified(monkeypatch):
    async def fake_get_settlement_period(period_id: str):
        return period("CERTIFIED")

    monkeypatch.setattr(
        "services.fulfilment.settlement.lock_enforcement.get_settlement_period",
        fake_get_settlement_period,
    )

    result = await get_period_lock_status("period-123")

    assert result["status"] == "CERTIFIED"
    assert result["is_open"] is False
    assert result["is_closed"] is False
    assert result["is_locked"] is False
    assert result["can_modify"] is True


@pytest.mark.asyncio
async def test_get_period_lock_status_closed(monkeypatch):
    async def fake_get_settlement_period(period_id: str):
        return period("CLOSED")

    monkeypatch.setattr(
        "services.fulfilment.settlement.lock_enforcement.get_settlement_period",
        fake_get_settlement_period,
    )

    result = await get_period_lock_status("period-123")

    assert result["status"] == "CLOSED"
    assert result["is_open"] is False
    assert result["is_closed"] is True
    assert result["is_locked"] is True
    assert result["can_modify"] is False


@pytest.mark.asyncio
async def test_get_period_lock_status_missing(monkeypatch):
    async def fake_get_settlement_period(period_id: str):
        return None

    monkeypatch.setattr(
        "services.fulfilment.settlement.lock_enforcement.get_settlement_period",
        fake_get_settlement_period,
    )

    with pytest.raises(SettlementPeriodNotFoundError) as exc:
        await get_period_lock_status("missing-period")

    assert "Settlement period not found" in str(exc.value)


@pytest.mark.asyncio
async def test_ensure_period_open_allows_open_period(monkeypatch):
    async def fake_get_period_lock_status(period_id: str):
        return {
            "period_id": period_id,
            "is_closed": False,
            "can_modify": True,
        }

    monkeypatch.setattr(
        "services.fulfilment.settlement.lock_enforcement.get_period_lock_status",
        fake_get_period_lock_status,
    )

    result = await ensure_period_open("period-123")

    assert result["period_id"] == "period-123"
    assert result["can_modify"] is True


@pytest.mark.asyncio
async def test_ensure_period_open_rejects_closed_period(monkeypatch):
    async def fake_get_period_lock_status(period_id: str):
        return {
            "period_id": period_id,
            "is_closed": True,
            "can_modify": False,
        }

    monkeypatch.setattr(
        "services.fulfilment.settlement.lock_enforcement.get_period_lock_status",
        fake_get_period_lock_status,
    )

    with pytest.raises(SettlementPeriodClosedError) as exc:
        await ensure_period_open("period-123")

    assert "Settlement period period-123 is CLOSED" in str(exc.value)


@pytest.mark.asyncio
async def test_ensure_period_not_closed_returns_true(monkeypatch):
    async def fake_ensure_period_open(period_id: str):
        return {
            "period_id": period_id,
            "is_closed": False,
        }

    monkeypatch.setattr(
        "services.fulfilment.settlement.lock_enforcement.ensure_period_open",
        fake_ensure_period_open,
    )

    result = await ensure_period_not_closed("period-123")

    assert result is True