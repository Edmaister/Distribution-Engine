from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.schemas.distribution.opportunities import (
    CreateOpportunityRequest,
    OpportunityResponse,
    UpdateOpportunityRequest,
)
from services.admin_audit_service import try_write_admin_audit
from services.distribution.opportunity_service import (
    OpportunityDuplicate,
    OpportunityError,
    OpportunityInvalidState,
    OpportunityNotFound,
    close_opportunity,
    create_opportunity,
    get_opportunity,
    list_opportunities,
    publish_opportunity,
    reopen_opportunity,
    update_opportunity,
)
from utils.security import require_distribution_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/distribution/opportunities",
    tags=["Admin Distribution Opportunities"],
    dependencies=[Depends(require_admin_key)],
)


def _handle_opportunity_error(exc: Exception) -> HTTPException:
    if isinstance(exc, OpportunityNotFound):
        return HTTPException(status_code=404, detail=str(exc))

    if isinstance(exc, (OpportunityDuplicate, OpportunityInvalidState)):
        return HTTPException(status_code=409, detail=str(exc))

    if isinstance(exc, OpportunityError):
        return HTTPException(status_code=400, detail=str(exc))

    return HTTPException(status_code=500, detail="Unexpected opportunity error")


@router.post("", response_model=OpportunityResponse)
async def create(
    request: CreateOpportunityRequest,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        opportunity = await create_opportunity(
            tenant_code=request.tenant_code,
            sponsor_code=request.sponsor_code,
            opportunity_code=request.opportunity_code,
            title=request.title,
            description=request.description,
            campaign_code=request.campaign_code,
            funding_contract_id=request.funding_contract_id,
            product_code=request.product_code,
            product_name=request.product_name,
            target_segments=request.target_segments,
            target_regions=request.target_regions,
            target_channels=request.target_channels,
            distributor_types=request.distributor_types,
            commission_rule_id=request.commission_rule_id,
            estimated_reward_amount=request.estimated_reward_amount,
            estimated_commission_amount=request.estimated_commission_amount,
            total_budget=request.total_budget,
            max_allocations=request.max_allocations,
            starts_at=request.starts_at,
            ends_at=request.ends_at,
            metadata=request.metadata,
        )
        await try_write_admin_audit(
            action_type="DISTRIBUTION_OPPORTUNITY_CREATE",
            action_domain="DISTRIBUTION",
            identity=identity,
            tenant_code=request.tenant_code,
            target_type="distribution_opportunity",
            target_id=opportunity.get("opportunity_id"),
            request_payload=request.model_dump(mode="json"),
            result_payload={
                "opportunity_id": opportunity.get("opportunity_id"),
                "opportunity_code": opportunity.get("opportunity_code"),
                "opportunity_status": opportunity.get("opportunity_status"),
            },
        )
        return opportunity

    except Exception as exc:
        raise _handle_opportunity_error(exc) from exc


@router.get("", response_model=list[OpportunityResponse])
async def list_all(
    tenant_code: str = Query(...),
    sponsor_code: str | None = Query(default=None),
    campaign_code: str | None = Query(default=None),
    opportunity_status: str | None = Query(default=None),
    segment: str | None = Query(default=None),
    region: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    distributor_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    return await list_opportunities(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        campaign_code=campaign_code,
        opportunity_status=opportunity_status,
        segment=segment,
        region=region,
        channel=channel,
        distributor_type=distributor_type,
        limit=limit,
    )


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get(opportunity_id: str) -> dict:
    try:
        return await get_opportunity(opportunity_id=opportunity_id)

    except Exception as exc:
        raise _handle_opportunity_error(exc) from exc


@router.patch("/{opportunity_id}", response_model=OpportunityResponse)
async def update(opportunity_id: str, request: UpdateOpportunityRequest) -> dict:
    try:
        return await update_opportunity(
            opportunity_id=opportunity_id,
            title=request.title,
            description=request.description,
            product_code=request.product_code,
            product_name=request.product_name,
            target_segments=request.target_segments,
            target_regions=request.target_regions,
            target_channels=request.target_channels,
            distributor_types=request.distributor_types,
            commission_rule_id=request.commission_rule_id,
            estimated_reward_amount=request.estimated_reward_amount,
            estimated_commission_amount=request.estimated_commission_amount,
            total_budget=request.total_budget,
            max_allocations=request.max_allocations,
            starts_at=request.starts_at,
            ends_at=request.ends_at,
            metadata=request.metadata,
        )

    except Exception as exc:
        raise _handle_opportunity_error(exc) from exc


@router.post("/{opportunity_id}/publish", response_model=OpportunityResponse)
async def publish(
    opportunity_id: str,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        opportunity = await publish_opportunity(opportunity_id=opportunity_id)
        await _audit_opportunity_lifecycle(
            action_type="DISTRIBUTION_OPPORTUNITY_PUBLISH",
            identity=identity,
            opportunity_id=opportunity_id,
            opportunity=opportunity,
        )
        return opportunity

    except Exception as exc:
        raise _handle_opportunity_error(exc) from exc


@router.post("/{opportunity_id}/close", response_model=OpportunityResponse)
async def close(
    opportunity_id: str,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        opportunity = await close_opportunity(opportunity_id=opportunity_id)
        await _audit_opportunity_lifecycle(
            action_type="DISTRIBUTION_OPPORTUNITY_CLOSE",
            identity=identity,
            opportunity_id=opportunity_id,
            opportunity=opportunity,
        )
        return opportunity

    except Exception as exc:
        raise _handle_opportunity_error(exc) from exc


@router.post("/{opportunity_id}/reopen", response_model=OpportunityResponse)
async def reopen(
    opportunity_id: str,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        opportunity = await reopen_opportunity(opportunity_id=opportunity_id)
        await _audit_opportunity_lifecycle(
            action_type="DISTRIBUTION_OPPORTUNITY_REOPEN",
            identity=identity,
            opportunity_id=opportunity_id,
            opportunity=opportunity,
        )
        return opportunity

    except Exception as exc:
        raise _handle_opportunity_error(exc) from exc


async def _audit_opportunity_lifecycle(
    *,
    action_type: str,
    identity: dict,
    opportunity_id: str,
    opportunity: dict,
) -> None:
    await try_write_admin_audit(
        action_type=action_type,
        action_domain="DISTRIBUTION",
        identity=identity,
        tenant_code=opportunity.get("tenant_code"),
        target_type="distribution_opportunity",
        target_id=opportunity_id,
        result_payload={
            "opportunity_id": opportunity.get("opportunity_id"),
            "opportunity_status": opportunity.get("opportunity_status"),
        },
    )
