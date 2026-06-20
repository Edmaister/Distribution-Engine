from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.admin_audit_service import try_write_admin_audit
from services.fulfilment.settlement.approvals import (
    approve_batch_request,
    get_batch_approvals,
    reject_batch_request,
    request_batch_approval,
)
from utils.security import require_finance_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/settlement",
    tags=["Admin Settlement Approvals"],
    dependencies=[Depends(require_admin_key)],
)


class RequestBatchApprovalRequest(BaseModel):
    approval_type: str = "SETTLEMENT_BATCH_APPROVAL"
    requested_by: str
    comments: str | None = None


class ApproveBatchRequest(BaseModel):
    approved_by: str
    comments: str | None = None


class RejectBatchRequest(BaseModel):
    rejected_by: str
    comments: str | None = None


@router.post("/batches/{batch_id}/approval/request")
async def request_approval(
    batch_id: str,
    request: RequestBatchApprovalRequest,
    identity: dict = Depends(require_admin_key),
):
    approval = await request_batch_approval(
        batch_id=batch_id,
        approval_type=request.approval_type,
        requested_by=request.requested_by,
        comments=request.comments,
    )

    if not approval:
        raise HTTPException(
            status_code=400,
            detail="Settlement batch approval cannot be requested",
        )

    await try_write_admin_audit(
        action_type="SETTLEMENT_APPROVAL_REQUEST",
        action_domain="FINANCE",
        identity=identity,
        target_type="settlement_batch",
        target_id=batch_id,
        request_payload=request.model_dump(mode="json"),
        result_payload={
            "approval_id": approval.get("approval_id"),
            "approval_status": approval.get("approval_status"),
        },
    )

    return {
        "status": "ok",
        "item": approval,
    }


@router.post("/approvals/{approval_id}/approve")
async def approve_approval(
    approval_id: str,
    request: ApproveBatchRequest,
    identity: dict = Depends(require_admin_key),
):
    approval = await approve_batch_request(
        approval_id=approval_id,
        approved_by=request.approved_by,
        comments=request.comments,
    )

    if not approval:
        raise HTTPException(
            status_code=400,
            detail="Settlement approval cannot be approved",
        )

    await try_write_admin_audit(
        action_type="SETTLEMENT_APPROVAL_APPROVE",
        action_domain="FINANCE",
        identity=identity,
        target_type="settlement_approval",
        target_id=approval_id,
        request_payload=request.model_dump(mode="json"),
        result_payload={
            "approval_id": approval.get("approval_id"),
            "approval_status": approval.get("approval_status"),
        },
    )

    return {
        "status": "ok",
        "item": approval,
    }


@router.post("/approvals/{approval_id}/reject")
async def reject_approval(
    approval_id: str,
    request: RejectBatchRequest,
    identity: dict = Depends(require_admin_key),
):
    approval = await reject_batch_request(
        approval_id=approval_id,
        rejected_by=request.rejected_by,
        comments=request.comments,
    )

    if not approval:
        raise HTTPException(
            status_code=400,
            detail="Settlement approval cannot be rejected",
        )

    await try_write_admin_audit(
        action_type="SETTLEMENT_APPROVAL_REJECT",
        action_domain="FINANCE",
        identity=identity,
        target_type="settlement_approval",
        target_id=approval_id,
        request_payload=request.model_dump(mode="json"),
        result_payload={
            "approval_id": approval.get("approval_id"),
            "approval_status": approval.get("approval_status"),
        },
    )

    return {
        "status": "ok",
        "item": approval,
    }


@router.get("/batches/{batch_id}/approvals")
async def get_approvals(batch_id: str):
    approvals = await get_batch_approvals(batch_id=batch_id)

    return {
        "status": "ok",
        "count": len(approvals),
        "items": approvals,
    }
