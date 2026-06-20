from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from services.fulfilment.settlement.lock_enforcement import (
    SettlementPeriodClosedError,
    SettlementPeriodNotFoundError,
    ensure_period_not_closed,
    get_period_lock_status,
)
from utils.security import require_finance_admin_key as require_admin_key

router = APIRouter(
    prefix="/admin/settlement/lock-enforcement",
    tags=["Admin Settlement Lock Enforcement"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("/periods/{period_id}")
async def get_lock_status(
    period_id: str,
):
    try:
        return await get_period_lock_status(period_id)
    except SettlementPeriodNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.post("/periods/{period_id}/validate")
async def validate_period_modifiable(
    period_id: str,
):
    try:
        result = await ensure_period_not_closed(period_id)

        return {
            "period_id": period_id,
            "can_modify": result,
            "message": "Settlement period is modifiable.",
        }

    except SettlementPeriodNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except SettlementPeriodClosedError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
