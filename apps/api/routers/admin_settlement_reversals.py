from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services.admin_audit_service import try_write_admin_audit
from services.fulfilment.settlement.reversals import (
    approve_settlement_reversal,
    create_settlement_reversal,
    execute_settlement_reversal,
    get_settlement_reversal,
    list_settlement_reversals,
)
from utils.security import require_finance_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/settlement/reversals",
    tags=["Admin Settlement Reversals"],
    dependencies=[Depends(require_admin_key)],
)


class CreateSettlementReversalRequest(BaseModel):
    settlement_id: str
    tenant_code: str
    reversal_reason: str
    amount: Decimal = Field(gt=0)
    requested_by: str
    correlation_id: str | None = None


class ApproveSettlementReversalRequest(BaseModel):
    approved_by: str


@router.post("")
async def create_reversal(
    request: CreateSettlementReversalRequest,
    identity: dict = Depends(require_admin_key),
):
    reversal = await create_settlement_reversal(
        settlement_id=request.settlement_id,
        tenant_code=request.tenant_code,
        reversal_reason=request.reversal_reason,
        amount=request.amount,
        requested_by=request.requested_by,
        correlation_id=request.correlation_id,
    )
    await try_write_admin_audit(
        action_type="SETTLEMENT_REVERSAL_CREATE",
        action_domain="FINANCE",
        identity=identity,
        tenant_code=request.tenant_code,
        target_type="settlement_reversal",
        target_id=reversal.get("reversal_id"),
        correlation_id=request.correlation_id,
        reason=request.reversal_reason,
        request_payload=request.model_dump(mode="json"),
        result_payload={
            "reversal_id": reversal.get("reversal_id"),
            "settlement_id": reversal.get("settlement_id"),
            "status": reversal.get("status"),
        },
    )

    return {
        "status": "ok",
        "item": reversal,
    }


@router.get("")
async def get_reversals(
    tenant_code: str | None = Query(default=None),
    settlement_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    reversals = await list_settlement_reversals(
        tenant_code=tenant_code,
        settlement_id=settlement_id,
        status=status,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(reversals),
        "items": reversals,
    }


@router.get("/{reversal_id}")
async def get_reversal(reversal_id: str):
    reversal = await get_settlement_reversal(reversal_id=reversal_id)

    if not reversal:
        raise HTTPException(
            status_code=404,
            detail="Settlement reversal not found",
        )

    return {
        "status": "ok",
        "item": reversal,
    }


@router.post("/{reversal_id}/approve")
async def approve_reversal(
    reversal_id: str,
    request: ApproveSettlementReversalRequest,
    identity: dict = Depends(require_admin_key),
):
    reversal = await approve_settlement_reversal(
        reversal_id=reversal_id,
        approved_by=request.approved_by,
    )

    if not reversal:
        raise HTTPException(
            status_code=400,
            detail="Settlement reversal cannot be approved",
        )

    await try_write_admin_audit(
        action_type="SETTLEMENT_REVERSAL_APPROVE",
        action_domain="FINANCE",
        identity=identity,
        tenant_code=reversal.get("tenant_code"),
        target_type="settlement_reversal",
        target_id=reversal_id,
        request_payload=request.model_dump(mode="json"),
        result_payload={
            "reversal_id": reversal.get("reversal_id"),
            "status": reversal.get("status"),
        },
    )

    return {
        "status": "ok",
        "item": reversal,
    }


@router.post("/{reversal_id}/execute")
async def execute_reversal(
    reversal_id: str,
    identity: dict = Depends(require_admin_key),
):
    reversal = await execute_settlement_reversal(reversal_id=reversal_id)

    if not reversal:
        raise HTTPException(
            status_code=400,
            detail="Settlement reversal cannot be executed",
        )

    await try_write_admin_audit(
        action_type="SETTLEMENT_REVERSAL_EXECUTE",
        action_domain="FINANCE",
        identity=identity,
        tenant_code=reversal.get("tenant_code"),
        target_type="settlement_reversal",
        target_id=reversal_id,
        result_payload={
            "reversal_id": reversal.get("reversal_id"),
            "status": reversal.get("status"),
        },
    )

    return {
        "status": "ok",
        "item": reversal,
    }
