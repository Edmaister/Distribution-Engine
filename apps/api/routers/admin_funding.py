from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from services.funding.exposure import list_funding_exposure
from services.funding.limits import (
    create_funding_limit,
    list_funding_limits,
    update_funding_limit,
)
from services.funding.dashboard import (
    get_account_funding_summary,
    get_funding_summary,
    get_tenant_funding_summary,
)
from utils.security import require_finance_admin_key as require_admin_key

router = APIRouter(
    prefix="/admin/funding",
    tags=["admin-funding"],
    dependencies=[Depends(require_admin_key)],
)


class FundingLimitCreateRequest(BaseModel):
    tenant_code: str = Field(..., min_length=1)
    account_id: UUID
    daily_limit: Decimal
    monthly_limit: Decimal
    exposure_limit: Decimal


class FundingLimitUpdateRequest(BaseModel):
    daily_limit: Decimal | None = None
    monthly_limit: Decimal | None = None
    exposure_limit: Decimal | None = None
    is_active: bool | None = None


@router.get("/exposure")
async def get_funding_exposure(
    tenant_code: str | None = None,
    account_id: UUID | None = None,
    limit: int = 100,
) -> dict:
    items = await list_funding_exposure(
        tenant_code=tenant_code,
        account_id=account_id,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(items),
        "items": items,
    }


@router.get("/limits")
async def get_funding_limits(
    tenant_code: str | None = None,
    account_id: UUID | None = None,
    active_only: bool = True,
    limit: int = 100,
) -> dict:
    items = await list_funding_limits(
        tenant_code=tenant_code,
        account_id=account_id,
        active_only=active_only,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(items),
        "items": items,
    }


@router.post("/limits")
async def post_funding_limit(payload: FundingLimitCreateRequest) -> dict:
    item = await create_funding_limit(
        tenant_code=payload.tenant_code,
        account_id=payload.account_id,
        daily_limit=payload.daily_limit,
        monthly_limit=payload.monthly_limit,
        exposure_limit=payload.exposure_limit,
    )

    return {
        "status": "created",
        "item": item,
    }


@router.put("/limits/{limit_id}")
async def put_funding_limit(
    limit_id: UUID,
    payload: FundingLimitUpdateRequest,
) -> dict:
    item = await update_funding_limit(
        limit_id=limit_id,
        daily_limit=payload.daily_limit,
        monthly_limit=payload.monthly_limit,
        exposure_limit=payload.exposure_limit,
        is_active=payload.is_active,
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Funding limit not found",
        )

    return {
        "status": "updated",
        "item": item,
    }

@router.get("/dashboard")
async def funding_dashboard() -> dict:
    summary = await get_funding_summary()

    return {
        "status": "ok",
        "summary": summary,
    }

@router.get("/dashboard/{tenant_code}")
async def tenant_funding_dashboard(
    tenant_code: str,
) -> dict:
    summary = await get_tenant_funding_summary(
        tenant_code=tenant_code,
    )

    return {
        "status": "ok",
        "summary": summary,
    }

@router.get("/dashboard/{tenant_code}/{account_id}")
async def account_funding_dashboard(
    tenant_code: str,
    account_id: UUID,
) -> dict:
    summary = await get_account_funding_summary(
        tenant_code=tenant_code,
        account_id=account_id,
    )

    return {
        "status": "ok",
        "summary": summary,
    }
