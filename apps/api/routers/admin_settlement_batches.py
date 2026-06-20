from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services.fulfilment.settlement.batches import (
    add_settlement_to_batch,
    approve_batch,
    create_settlement_batch,
    execute_batch,
    get_settlement_batch,
    list_settlement_batches,
    submit_batch_for_approval,
)
from utils.security import require_finance_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/settlement/batches",
    tags=["Admin Settlement Batches"],
    dependencies=[Depends(require_admin_key)],
)


class CreateSettlementBatchRequest(BaseModel):
    tenant_code: str
    batch_reference: str
    batch_type: str = "REWARD_SETTLEMENT"
    created_by: str | None = None


class AddSettlementBatchItemRequest(BaseModel):
    settlement_id: str
    amount: Decimal = Field(gt=0)


class ApproveSettlementBatchRequest(BaseModel):
    approved_by: str


@router.post("")
async def create_batch(request: CreateSettlementBatchRequest):
    batch = await create_settlement_batch(
        tenant_code=request.tenant_code,
        batch_reference=request.batch_reference,
        batch_type=request.batch_type,
        created_by=request.created_by,
    )

    return {
        "status": "ok",
        "item": batch,
    }


@router.post("/{batch_id}/items")
async def add_item_to_batch(
    batch_id: str,
    request: AddSettlementBatchItemRequest,
):
    result = await add_settlement_to_batch(
        batch_id=batch_id,
        settlement_id=request.settlement_id,
        amount=request.amount,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Settlement batch not found or not editable",
        )

    return {
        "status": "ok",
        **result,
    }


@router.post("/{batch_id}/submit")
async def submit_batch(batch_id: str):
    batch = await submit_batch_for_approval(batch_id=batch_id)

    if not batch:
        raise HTTPException(
            status_code=400,
            detail="Settlement batch cannot be submitted",
        )

    return {
        "status": "ok",
        "item": batch,
    }


@router.post("/{batch_id}/approve")
async def approve_settlement_batch(
    batch_id: str,
    request: ApproveSettlementBatchRequest,
):
    batch = await approve_batch(
        batch_id=batch_id,
        approved_by=request.approved_by,
    )

    if not batch:
        raise HTTPException(
            status_code=400,
            detail="Settlement batch cannot be approved",
        )

    return {
        "status": "ok",
        "item": batch,
    }


@router.post("/{batch_id}/execute")
async def execute_settlement_batch(batch_id: str):
    batch = await execute_batch(batch_id=batch_id)

    if not batch:
        raise HTTPException(
            status_code=400,
            detail="Settlement batch cannot be executed",
        )

    return {
        "status": "ok",
        "item": batch,
    }


@router.get("")
async def get_batches(
    tenant_code: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    batches = await list_settlement_batches(
        tenant_code=tenant_code,
        status=status,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(batches),
        "items": batches,
    }


@router.get("/{batch_id}")
async def get_batch(batch_id: str):
    result = await get_settlement_batch(batch_id=batch_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Settlement batch not found",
        )

    return {
        "status": "ok",
        **result,
    }
