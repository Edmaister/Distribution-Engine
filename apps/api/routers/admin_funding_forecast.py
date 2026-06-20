from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from services.funding.forecasting import (
    DEFAULT_BUFFER_DAYS,
    DEFAULT_BURN_WINDOW_DAYS,
    get_funding_forecast,
    get_sponsor_funding_forecast,
    list_settlement_exposure_forecasts,
    list_funding_forecasts,
    list_sponsor_funding_forecasts,
)
from utils.security import require_finance_admin_key as require_admin_key

router = APIRouter(
    prefix="/admin/funding",
    tags=["Admin Funding Forecast"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("/forecast")
async def get_all_funding_forecasts(
    tenant_code: str | None = Query(default=None),
    burn_window_days: int = Query(default=DEFAULT_BURN_WINDOW_DAYS, ge=1, le=365),
    buffer_days: int = Query(default=DEFAULT_BUFFER_DAYS, ge=1, le=365),
    limit: int = Query(default=100, ge=1, le=500),
):
    forecasts = await list_funding_forecasts(
        tenant_code=tenant_code,
        burn_window_days=burn_window_days,
        buffer_days=buffer_days,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(forecasts),
        "items": forecasts,
    }


@router.get("/forecast/{account_id}")
async def get_single_funding_forecast(
    account_id: str,
    burn_window_days: int = Query(default=DEFAULT_BURN_WINDOW_DAYS, ge=1, le=365),
    buffer_days: int = Query(default=DEFAULT_BUFFER_DAYS, ge=1, le=365),
):
    forecast = await get_funding_forecast(
        account_id=account_id,
        burn_window_days=burn_window_days,
        buffer_days=buffer_days,
    )

    if not forecast:
        raise HTTPException(
            status_code=404,
            detail="Funding account not found",
        )

    return {
        "status": "ok",
        "item": forecast,
    }


@router.get("/sponsor-forecast")
async def get_all_sponsor_funding_forecasts(
    tenant_code: str | None = Query(default=None),
    sponsor_code: str | None = Query(default=None),
    currency: str = Query(default="ZAR"),
    burn_window_days: int = Query(default=DEFAULT_BURN_WINDOW_DAYS, ge=1, le=365),
    buffer_days: int = Query(default=DEFAULT_BUFFER_DAYS, ge=1, le=365),
    limit: int = Query(default=100, ge=1, le=500),
):
    forecasts = await list_sponsor_funding_forecasts(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        currency=currency,
        burn_window_days=burn_window_days,
        buffer_days=buffer_days,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(forecasts),
        "items": forecasts,
    }


@router.get("/sponsor-forecast/{tenant_code}/{sponsor_code}")
async def get_single_sponsor_funding_forecast(
    tenant_code: str,
    sponsor_code: str,
    currency: str = Query(default="ZAR"),
    burn_window_days: int = Query(default=DEFAULT_BURN_WINDOW_DAYS, ge=1, le=365),
    buffer_days: int = Query(default=DEFAULT_BUFFER_DAYS, ge=1, le=365),
):
    forecast = await get_sponsor_funding_forecast(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        currency=currency,
        burn_window_days=burn_window_days,
        buffer_days=buffer_days,
    )

    if not forecast:
        raise HTTPException(
            status_code=404,
            detail="Sponsor funding forecast not found",
        )

    return {
        "status": "ok",
        "item": forecast,
    }


@router.get("/settlement-exposure-forecast")
async def get_settlement_exposure_forecasts(
    tenant_code: str | None = Query(default=None),
    provider_key: str | None = Query(default=None),
    currency: str | None = Query(default=None),
    burn_window_days: int = Query(default=DEFAULT_BURN_WINDOW_DAYS, ge=1, le=365),
    buffer_days: int = Query(default=DEFAULT_BUFFER_DAYS, ge=1, le=365),
    limit: int = Query(default=100, ge=1, le=500),
):
    forecasts = await list_settlement_exposure_forecasts(
        tenant_code=tenant_code,
        provider_key=provider_key,
        currency=currency,
        burn_window_days=burn_window_days,
        buffer_days=buffer_days,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(forecasts),
        "items": forecasts,
    }
