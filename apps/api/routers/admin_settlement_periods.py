from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.fulfilment.settlement.periods import (
    close_settlement_period,
    create_settlement_period,
    get_current_open_period,
    get_settlement_period,
    list_settlement_periods,
    reopen_settlement_period,
)
from utils.security import require_finance_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/settlement/periods",
    tags=["Admin Settlement Periods"],
    dependencies=[Depends(require_admin_key)],
)


class CreateSettlementPeriodRequest(BaseModel):
    tenant_code: str
    period_code: str
    period_start: str
    period_end: str
    created_by: str | None = None


class CloseSettlementPeriodRequest(BaseModel):
    closed_by: str


@router.post("")
async def create_period(
    request: CreateSettlementPeriodRequest,
):
    period = await create_settlement_period(
        tenant_code=request.tenant_code,
        period_code=request.period_code,
        period_start=request.period_start,
        period_end=request.period_end,
        created_by=request.created_by,
    )

    return {
        "status": "ok",
        "item": period,
    }


@router.get("")
async def get_periods(
    tenant_code: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    periods = await list_settlement_periods(
        tenant_code=tenant_code,
        status=status,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(periods),
        "items": periods,
    }


@router.get("/current")
async def get_current_period(
    tenant_code: str | None = Query(default=None),
):
    period = await get_current_open_period(
        tenant_code=tenant_code,
    )

    if not period:
        raise HTTPException(
            status_code=404,
            detail="No open settlement period found",
        )

    return {
        "status": "ok",
        "item": period,
    }


@router.get("/{period_id}")
async def get_period(
    period_id: str,
):
    period = await get_settlement_period(
        period_id=period_id,
    )

    if not period:
        raise HTTPException(
            status_code=404,
            detail="Settlement period not found",
        )

    return {
        "status": "ok",
        "item": period,
    }


@router.post("/{period_id}/close")
async def close_period(
    period_id: str,
    request: CloseSettlementPeriodRequest,
):
    period = await close_settlement_period(
        period_id=period_id,
        closed_by=request.closed_by,
    )

    if not period:
        raise HTTPException(
            status_code=400,
            detail="Settlement period cannot be closed",
        )

    return {
        "status": "ok",
        "item": period,
    }


@router.post("/{period_id}/reopen")
async def reopen_period(
    period_id: str,
):
    period = await reopen_settlement_period(
        period_id=period_id,
    )

    if not period:
        raise HTTPException(
            status_code=400,
            detail="Settlement period cannot be reopened",
        )

    return {
        "status": "ok",
        "item": period,
    }
