from __future__ import annotations

from typing import Any

from services.fulfilment.settlement.periods import get_settlement_period


class SettlementPeriodNotFoundError(Exception):
    pass


class SettlementPeriodClosedError(Exception):
    pass


async def get_period_lock_status(
    period_id: str,
) -> dict[str, Any]:
    period = await get_settlement_period(
        period_id=period_id,
    )

    if not period:
        raise SettlementPeriodNotFoundError(
            f"Settlement period not found: {period_id}"
        )

    status = period["status"]

    return {
        "period_id": str(period["period_id"]),
        "tenant_code": period["tenant_code"],
        "period_code": period["period_code"],
        "status": status,
        "is_open": status == "OPEN",
        "is_closed": status == "CLOSED",
        "is_locked": status == "CLOSED",
        "can_modify": status != "CLOSED",
    }


async def ensure_period_open(
    period_id: str,
) -> dict[str, Any]:
    lock_status = await get_period_lock_status(period_id)

    if lock_status["is_closed"]:
        raise SettlementPeriodClosedError(
            f"Settlement period {period_id} is CLOSED"
        )

    return lock_status


async def ensure_period_not_closed(
    period_id: str,
) -> bool:
    await ensure_period_open(period_id)
    return True