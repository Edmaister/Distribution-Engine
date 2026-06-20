from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.fulfilment.settlement.exceptions import (
    get_settlement_exception,
    list_settlement_exceptions,
    resolve_settlement_exception,
)
from utils.security import require_finance_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/settlement/exceptions",
    tags=["Admin Settlement Exceptions"],
    dependencies=[Depends(require_admin_key)],
)


class ResolveSettlementExceptionRequest(BaseModel):
    resolved_by: str


@router.get("")
async def get_settlement_exceptions(
    batch_id: str | None = Query(default=None),
    settlement_id: str | None = Query(default=None),
    status: str | None = Query(default="OPEN"),
    severity: str | None = Query(default=None),
    exception_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    exceptions = await list_settlement_exceptions(
        batch_id=batch_id,
        settlement_id=settlement_id,
        status=status,
        severity=severity,
        exception_type=exception_type,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(exceptions),
        "items": exceptions,
    }


@router.get("/{exception_id}")
async def get_exception(exception_id: str):
    exception = await get_settlement_exception(exception_id=exception_id)

    if not exception:
        raise HTTPException(
            status_code=404,
            detail="Settlement exception not found",
        )

    return {
        "status": "ok",
        "item": exception,
    }


@router.post("/{exception_id}/resolve")
async def resolve_exception(
    exception_id: str,
    request: ResolveSettlementExceptionRequest,
):
    exception = await resolve_settlement_exception(
        exception_id=exception_id,
        resolved_by=request.resolved_by,
    )

    if not exception:
        raise HTTPException(
            status_code=404,
            detail="Settlement exception not found or already resolved",
        )

    return {
        "status": "ok",
        "item": exception,
    }
