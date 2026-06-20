from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from services.funding.reconciliation import (
    get_funding_reconciliation_run,
    list_funding_reconciliation_exceptions,
    list_funding_reconciliation_runs,
    resolve_funding_reconciliation_exception,
    run_funding_reconciliation,
)
from utils.security import require_finance_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/funding/reconciliation",
    tags=["Admin Funding Reconciliation"],
    dependencies=[Depends(require_admin_key)],
)


@router.post("/run")
async def run_reconciliation(
    tenant_code: str = Query(...),
    correlation_id: str | None = Query(default=None),
):
    return await run_funding_reconciliation(
        tenant_code=tenant_code,
        correlation_id=correlation_id,
    )


@router.get("")
async def get_reconciliation_runs(
    tenant_code: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    runs = await list_funding_reconciliation_runs(
        tenant_code=tenant_code,
        status=status,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(runs),
        "items": runs,
    }


@router.get("/exceptions")
async def get_reconciliation_exceptions(
    tenant_code: str | None = Query(default=None),
    status: str | None = Query(default="OPEN"),
    limit: int = Query(default=100, ge=1, le=500),
):
    exceptions = await list_funding_reconciliation_exceptions(
        tenant_code=tenant_code,
        status=status,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(exceptions),
        "items": exceptions,
    }


@router.get("/{run_id}")
async def get_reconciliation_run(run_id: str):
    result = await get_funding_reconciliation_run(run_id=run_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Funding reconciliation run not found",
        )

    return {
        "status": "ok",
        **result,
    }


@router.post("/exceptions/{exception_id}/resolve")
async def resolve_reconciliation_exception(exception_id: str):
    exception = await resolve_funding_reconciliation_exception(
        exception_id=exception_id,
    )

    if not exception:
        raise HTTPException(
            status_code=404,
            detail="Funding reconciliation exception not found or already resolved",
        )

    return {
        "status": "ok",
        "item": exception,
    }
