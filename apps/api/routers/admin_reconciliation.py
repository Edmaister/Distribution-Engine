from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from services.reconciliation_history_service import (
    get_reconciliation_results,
    get_reconciliation_run,
    list_reconciliation_runs,
)
from utils.security import require_admin_key

router = APIRouter(
    prefix="/admin/reconciliation",
    tags=["Admin - Reconciliation"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("/runs")
async def get_runs(
    tenant_code: Optional[str] = Query(default=None),
    provider_key: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    runs = await list_reconciliation_runs(
        tenant_code=tenant_code,
        provider_key=provider_key,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(runs),
        "items": runs,
    }


@router.get("/runs/{run_id}")
async def get_run(
    run_id: str,
):
    run = await get_reconciliation_run(
        run_id=run_id,
    )

    if not run:
        return {
            "status": "not_found",
            "run_id": run_id,
        }

    return {
        "status": "ok",
        "item": run,
    }


@router.get("/runs/{run_id}/results")
async def get_run_results(
    run_id: str,
):
    results = await get_reconciliation_results(
        run_id=run_id,
    )

    return {
        "status": "ok",
        "count": len(results),
        "items": results,
    }
