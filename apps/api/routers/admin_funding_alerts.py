from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from services.funding.alerts import (
    acknowledge_funding_alert,
    evaluate_funding_alerts,
    list_funding_alerts,
    resolve_funding_alert,
)
from utils.security import require_finance_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/funding/alerts",
    tags=["Admin Funding Alerts"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("")
async def get_funding_alerts(
    tenant_code: str | None = Query(default=None),
    account_id: str | None = Query(default=None),
    status: str | None = Query(default="OPEN"),
    limit: int = Query(default=100, ge=1, le=500),
):
    alerts = await list_funding_alerts(
        tenant_code=tenant_code,
        account_id=account_id,
        status=status,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(alerts),
        "items": alerts,
    }


@router.get("/{account_id}")
async def get_funding_alerts_for_account(
    account_id: str,
    status: str | None = Query(default="OPEN"),
    limit: int = Query(default=100, ge=1, le=500),
):
    alerts = await list_funding_alerts(
        account_id=account_id,
        status=status,
        limit=limit,
    )

    return {
        "status": "ok",
        "account_id": account_id,
        "count": len(alerts),
        "items": alerts,
    }


@router.post("/run")
async def run_funding_alert_evaluation(
    tenant_code: str | None = Query(default=None),
    burn_window_days: int = Query(default=30, ge=1, le=365),
    buffer_days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=100, ge=1, le=500),
    correlation_id: str | None = Query(default=None),
):
    return await evaluate_funding_alerts(
        tenant_code=tenant_code,
        burn_window_days=burn_window_days,
        buffer_days=buffer_days,
        limit=limit,
        correlation_id=correlation_id,
    )


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    alert = await acknowledge_funding_alert(alert_id=alert_id)

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Funding alert not found or not open",
        )

    return {
        "status": "ok",
        "item": alert,
    }


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    alert = await resolve_funding_alert(alert_id=alert_id)

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Funding alert not found or already resolved",
        )

    return {
        "status": "ok",
        "item": alert,
    }
