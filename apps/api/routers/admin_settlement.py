from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from services.fulfilment.settlement.service import (
    get_provider_exposure,
    get_settlement_by_id,
    list_settlements,
)
from services.fulfilment.settlement.status import SettlementStatus
from utils.security import require_finance_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/settlements",
    tags=["Admin - Settlements"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("")
async def get_settlements(
    tenant_code: Optional[str] = Query(default=None),
    provider_key: Optional[str] = Query(default=None),
    status: Optional[SettlementStatus] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    settlements = await list_settlements(
        tenant_code=tenant_code,
        provider_key=provider_key,
        status=status,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(settlements),
        "items": settlements,
    }


@router.get("/exposure")
async def get_settlement_exposure(
    tenant_code: Optional[str] = Query(default=None),
    provider_key: Optional[str] = Query(default=None),
):
    exposure = await get_provider_exposure(
        tenant_code=tenant_code,
        provider_key=provider_key,
    )

    return {
        "status": "ok",
        "count": len(exposure),
        "items": exposure,
    }


@router.get("/{settlement_id}")
async def get_settlement(
    settlement_id: str,
):
    settlement = await get_settlement_by_id(
        settlement_id=settlement_id,
    )

    if not settlement:
        return {
            "status": "not_found",
            "settlement_id": settlement_id,
        }

    return {
        "status": "ok",
        "item": settlement,
    }
