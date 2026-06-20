from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.schemas.distribution.governance import (
    ComplianceReviewResponse,
    CompleteComplianceReviewRequest,
    CreateComplianceReviewRequest,
    CreateDisputeRequest,
    DisputeResponse,
    DistributorGovernanceActionRequest,
    DistributorGovernanceActionResponse,
    GovernanceAuditResponse,
    ResolveDisputeRequest,
)
from services.distribution.governance_service import (
    GovernanceError,
    GovernanceInvalidAction,
    GovernanceNotFound,
    apply_distributor_governance_action,
    complete_compliance_review,
    create_compliance_review,
    create_dispute,
    list_compliance_reviews,
    list_disputes,
    list_governance_audit,
    resolve_dispute,
)
from utils.security import require_distribution_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/distribution/governance",
    tags=["Admin Distribution Governance"],
    dependencies=[Depends(require_admin_key)],
)


def _handle_governance_error(exc: Exception) -> HTTPException:
    if isinstance(exc, GovernanceNotFound):
        return HTTPException(status_code=404, detail=str(exc))

    if isinstance(exc, GovernanceInvalidAction):
        return HTTPException(status_code=409, detail=str(exc))

    if isinstance(exc, GovernanceError):
        return HTTPException(status_code=400, detail=str(exc))

    return HTTPException(status_code=500, detail="Unexpected governance error")


@router.post("/compliance-reviews", response_model=ComplianceReviewResponse)
async def create_review(request: CreateComplianceReviewRequest) -> dict:
    try:
        return await create_compliance_review(
            distributor_id=request.distributor_id,
            review_type=request.review_type,
            reviewer=request.reviewer,
            notes=request.notes,
            metadata=request.metadata,
        )

    except Exception as exc:
        raise _handle_governance_error(exc) from exc


@router.get("/compliance-reviews", response_model=list[ComplianceReviewResponse])
async def list_reviews(
    tenant_code: str = Query(...),
    distributor_id: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    return await list_compliance_reviews(
        tenant_code=tenant_code,
        distributor_id=distributor_id,
        review_status=review_status,
        limit=limit,
    )


@router.post(
    "/compliance-reviews/{review_id}/complete",
    response_model=ComplianceReviewResponse,
)
async def complete_review(
    review_id: str,
    request: CompleteComplianceReviewRequest,
) -> dict:
    try:
        return await complete_compliance_review(
            review_id=review_id,
            review_result=request.review_result,
            reviewer=request.reviewer,
            notes=request.notes,
            metadata=request.metadata,
        )

    except Exception as exc:
        raise _handle_governance_error(exc) from exc


@router.post("/disputes", response_model=DisputeResponse)
async def create_marketplace_dispute(request: CreateDisputeRequest) -> dict:
    try:
        return await create_dispute(
            route_id=request.route_id,
            raised_by=request.raised_by,
            reason_code=request.reason_code,
            description=request.description,
            metadata=request.metadata,
        )

    except Exception as exc:
        raise _handle_governance_error(exc) from exc


@router.get("/disputes", response_model=list[DisputeResponse])
async def list_marketplace_disputes(
    tenant_code: str = Query(...),
    distributor_id: str | None = Query(default=None),
    opportunity_id: str | None = Query(default=None),
    dispute_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    return await list_disputes(
        tenant_code=tenant_code,
        distributor_id=distributor_id,
        opportunity_id=opportunity_id,
        dispute_status=dispute_status,
        limit=limit,
    )


@router.post("/disputes/{dispute_id}/resolve", response_model=DisputeResponse)
async def resolve_marketplace_dispute(
    dispute_id: str,
    request: ResolveDisputeRequest,
) -> dict:
    try:
        return await resolve_dispute(
            dispute_id=dispute_id,
            dispute_status=request.dispute_status,
            resolved_by=request.resolved_by,
            resolution_notes=request.resolution_notes,
            metadata=request.metadata,
        )

    except Exception as exc:
        raise _handle_governance_error(exc) from exc


@router.post(
    "/distributors/{distributor_id}/actions",
    response_model=DistributorGovernanceActionResponse,
)
async def apply_governance_action(
    distributor_id: str,
    request: DistributorGovernanceActionRequest,
) -> dict:
    try:
        return await apply_distributor_governance_action(
            distributor_id=distributor_id,
            action_type=request.action_type,
            reason_code=request.reason_code,
            actor=request.actor,
            notes=request.notes,
            operating_limits=request.operating_limits,
            metadata=request.metadata,
        )

    except Exception as exc:
        raise _handle_governance_error(exc) from exc


@router.get("/audit", response_model=list[GovernanceAuditResponse])
async def list_audit(
    tenant_code: str = Query(...),
    distributor_id: str | None = Query(default=None),
    action_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    return await list_governance_audit(
        tenant_code=tenant_code,
        distributor_id=distributor_id,
        action_type=action_type,
        limit=limit,
    )
