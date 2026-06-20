from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services.marketplace_funding.budget_governance_service import (
    BudgetAdjustmentContractNotFound,
    BudgetAdjustmentRequestInvalidState,
    BudgetExceptionContractNotFound,
    BudgetExceptionInvalidState,
    BudgetGovernanceError,
    BudgetTransferContractNotFound,
    BudgetTransferInsufficientBudget,
    BudgetTransferInvalid,
    BudgetTransferRequestInvalidState,
    approve_budget_adjustment_request,
    approve_budget_transfer_request,
    create_budget_approval_policy,
    create_budget_exception,
    create_budget_adjustment_request,
    create_budget_transfer_request,
    evaluate_budget_approval_policy,
    list_budget_approval_policies,
    list_budget_exceptions,
    list_budget_adjustment_requests,
    list_budget_transfer_requests,
    reject_budget_adjustment_request,
    reject_budget_transfer_request,
    resolve_budget_exception,
    waive_budget_exception,
)
from utils.security import require_finance_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/funding/budget-governance",
    tags=["Admin Funding Budget Governance"],
    dependencies=[Depends(require_admin_key)],
)


class CreateBudgetAdjustmentRequest(BaseModel):
    contract_id: str
    requested_amount: Decimal = Field(gt=0)
    reason: str | None = None
    requested_by: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] | None = None


class CreateBudgetTransferRequest(BaseModel):
    source_contract_id: str
    target_contract_id: str
    requested_amount: Decimal = Field(gt=0)
    reason: str | None = None
    requested_by: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] | None = None


class CreateBudgetExceptionRequest(BaseModel):
    tenant_code: str
    exception_type: str
    exception_message: str
    severity: str = "WARNING"
    sponsor_code: str | None = None
    contract_id: str | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    detected_by: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] | None = None


class CreateBudgetApprovalPolicyRequest(BaseModel):
    tenant_code: str
    request_type: str
    approval_level: str
    sponsor_code: str | None = None
    min_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    max_amount: Decimal | None = Field(default=None, gt=0)
    required_role: str | None = None
    priority: int = Field(default=100, ge=0)
    description: str | None = None
    metadata: dict[str, Any] | None = None


class EvaluateBudgetApprovalPolicyRequest(BaseModel):
    tenant_code: str
    request_type: str
    amount: Decimal = Field(gt=0)
    sponsor_code: str | None = None


class DecideBudgetAdjustmentRequest(BaseModel):
    decided_by: str | None = None
    decision_reason: str | None = None


class CloseBudgetExceptionRequest(BaseModel):
    resolved_by: str | None = None
    resolution_reason: str | None = None


def _handle_budget_governance_error(exc: Exception) -> HTTPException:
    if isinstance(
        exc,
        (
            BudgetAdjustmentContractNotFound,
            BudgetTransferContractNotFound,
            BudgetExceptionContractNotFound,
        ),
    ):
        return HTTPException(status_code=404, detail=str(exc))

    if isinstance(
        exc,
        (
            BudgetAdjustmentRequestInvalidState,
            BudgetTransferRequestInvalidState,
            BudgetTransferInsufficientBudget,
            BudgetExceptionInvalidState,
        ),
    ):
        return HTTPException(status_code=409, detail=str(exc))

    if isinstance(exc, BudgetTransferInvalid):
        return HTTPException(status_code=400, detail=str(exc))

    if isinstance(exc, BudgetGovernanceError):
        return HTTPException(status_code=400, detail=str(exc))

    return HTTPException(status_code=500, detail="Unexpected budget governance error")


@router.post("/requests")
async def create_adjustment_request(
    request: CreateBudgetAdjustmentRequest,
) -> dict[str, Any]:
    try:
        item = await create_budget_adjustment_request(
            contract_id=request.contract_id,
            requested_amount=request.requested_amount,
            reason=request.reason,
            requested_by=request.requested_by,
            correlation_id=request.correlation_id,
            metadata=request.metadata,
        )

        return {"status": "ok", "item": item}

    except Exception as exc:
        raise _handle_budget_governance_error(exc) from exc


@router.get("/requests")
async def list_adjustment_requests(
    tenant_code: str | None = Query(default=None),
    sponsor_code: str | None = Query(default=None),
    contract_id: str | None = Query(default=None),
    request_status: str | None = Query(default="PENDING"),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    items = await list_budget_adjustment_requests(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        contract_id=contract_id,
        request_status=request_status,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(items),
        "items": items,
    }


@router.post("/requests/{request_id}/approve")
async def approve_adjustment_request(
    request_id: str,
    request: DecideBudgetAdjustmentRequest,
) -> dict[str, Any]:
    try:
        result = await approve_budget_adjustment_request(
            request_id=request_id,
            decided_by=request.decided_by,
            decision_reason=request.decision_reason,
        )

        return {"status": "ok", **result}

    except Exception as exc:
        raise _handle_budget_governance_error(exc) from exc


@router.post("/requests/{request_id}/reject")
async def reject_adjustment_request(
    request_id: str,
    request: DecideBudgetAdjustmentRequest,
) -> dict[str, Any]:
    try:
        item = await reject_budget_adjustment_request(
            request_id=request_id,
            decided_by=request.decided_by,
            decision_reason=request.decision_reason,
        )

        return {"status": "ok", "item": item}

    except Exception as exc:
        raise _handle_budget_governance_error(exc) from exc


@router.post("/transfer-requests")
async def create_transfer_request(
    request: CreateBudgetTransferRequest,
) -> dict[str, Any]:
    try:
        item = await create_budget_transfer_request(
            source_contract_id=request.source_contract_id,
            target_contract_id=request.target_contract_id,
            requested_amount=request.requested_amount,
            reason=request.reason,
            requested_by=request.requested_by,
            correlation_id=request.correlation_id,
            metadata=request.metadata,
        )

        return {"status": "ok", "item": item}

    except Exception as exc:
        raise _handle_budget_governance_error(exc) from exc


@router.get("/transfer-requests")
async def list_transfer_requests(
    tenant_code: str | None = Query(default=None),
    source_contract_id: str | None = Query(default=None),
    target_contract_id: str | None = Query(default=None),
    request_status: str | None = Query(default="PENDING"),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    items = await list_budget_transfer_requests(
        tenant_code=tenant_code,
        source_contract_id=source_contract_id,
        target_contract_id=target_contract_id,
        request_status=request_status,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(items),
        "items": items,
    }


@router.post("/transfer-requests/{request_id}/approve")
async def approve_transfer_request(
    request_id: str,
    request: DecideBudgetAdjustmentRequest,
) -> dict[str, Any]:
    try:
        result = await approve_budget_transfer_request(
            request_id=request_id,
            decided_by=request.decided_by,
            decision_reason=request.decision_reason,
        )

        return {"status": "ok", **result}

    except Exception as exc:
        raise _handle_budget_governance_error(exc) from exc


@router.post("/transfer-requests/{request_id}/reject")
async def reject_transfer_request(
    request_id: str,
    request: DecideBudgetAdjustmentRequest,
) -> dict[str, Any]:
    try:
        item = await reject_budget_transfer_request(
            request_id=request_id,
            decided_by=request.decided_by,
            decision_reason=request.decision_reason,
        )

        return {"status": "ok", "item": item}

    except Exception as exc:
        raise _handle_budget_governance_error(exc) from exc


@router.post("/exceptions")
async def create_exception(
    request: CreateBudgetExceptionRequest,
) -> dict[str, Any]:
    try:
        item = await create_budget_exception(
            tenant_code=request.tenant_code,
            sponsor_code=request.sponsor_code,
            contract_id=request.contract_id,
            exception_type=request.exception_type,
            severity=request.severity,
            exception_message=request.exception_message,
            amount=request.amount,
            detected_by=request.detected_by,
            correlation_id=request.correlation_id,
            metadata=request.metadata,
        )

        return {"status": "ok", "item": item}

    except Exception as exc:
        raise _handle_budget_governance_error(exc) from exc


@router.post("/approval-policies")
async def create_approval_policy(
    request: CreateBudgetApprovalPolicyRequest,
) -> dict[str, Any]:
    try:
        item = await create_budget_approval_policy(
            tenant_code=request.tenant_code,
            sponsor_code=request.sponsor_code,
            request_type=request.request_type,
            min_amount=request.min_amount,
            max_amount=request.max_amount,
            approval_level=request.approval_level,
            required_role=request.required_role,
            priority=request.priority,
            description=request.description,
            metadata=request.metadata,
        )

        return {"status": "ok", "item": item}

    except Exception as exc:
        raise _handle_budget_governance_error(exc) from exc


@router.get("/approval-policies")
async def list_approval_policies(
    tenant_code: str | None = Query(default=None),
    sponsor_code: str | None = Query(default=None),
    request_type: str | None = Query(default=None),
    policy_status: str | None = Query(default="ACTIVE"),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    items = await list_budget_approval_policies(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        request_type=request_type,
        policy_status=policy_status,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(items),
        "items": items,
    }


@router.post("/approval-policies/evaluate")
async def evaluate_approval_policy(
    request: EvaluateBudgetApprovalPolicyRequest,
) -> dict[str, Any]:
    result = await evaluate_budget_approval_policy(
        tenant_code=request.tenant_code,
        sponsor_code=request.sponsor_code,
        request_type=request.request_type,
        amount=request.amount,
    )

    return {"status": "ok", "result": result}


@router.get("/exceptions")
async def list_exceptions(
    tenant_code: str | None = Query(default=None),
    sponsor_code: str | None = Query(default=None),
    contract_id: str | None = Query(default=None),
    exception_status: str | None = Query(default="OPEN"),
    exception_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    items = await list_budget_exceptions(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        contract_id=contract_id,
        exception_status=exception_status,
        exception_type=exception_type,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(items),
        "items": items,
    }


@router.post("/exceptions/{exception_id}/resolve")
async def resolve_exception(
    exception_id: str,
    request: CloseBudgetExceptionRequest,
) -> dict[str, Any]:
    try:
        item = await resolve_budget_exception(
            exception_id=exception_id,
            resolved_by=request.resolved_by,
            resolution_reason=request.resolution_reason,
        )

        return {"status": "ok", "item": item}

    except Exception as exc:
        raise _handle_budget_governance_error(exc) from exc


@router.post("/exceptions/{exception_id}/waive")
async def waive_exception(
    exception_id: str,
    request: CloseBudgetExceptionRequest,
) -> dict[str, Any]:
    try:
        item = await waive_budget_exception(
            exception_id=exception_id,
            resolved_by=request.resolved_by,
            resolution_reason=request.resolution_reason,
        )

        return {"status": "ok", "item": item}

    except Exception as exc:
        raise _handle_budget_governance_error(exc) from exc
