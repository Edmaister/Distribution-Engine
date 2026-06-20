from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.schemas.producer_supply import (
    ProducerSupplyConversionListResponse,
    ProducerSupplyLaunchRequest,
)
from apps.api.schemas.distribution.opportunities import (
    OpportunityResponse,
    UpdateOpportunityRequest,
)
from apps.api.schemas.distribution.reporting import (
    MarketplaceOverviewResponse,
    OpportunityPerformanceResponse,
)
from services.admin_audit_service import try_write_admin_audit
from services.campaign_service import create_campaign
from services.distribution.opportunity_service import (
    OPPORTUNITY_STATUS_CLOSED,
    OPPORTUNITY_STATUS_DRAFT,
    OPPORTUNITY_STATUS_PUBLISHED,
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
from services.distribution.reporting_service import (
    get_marketplace_overview,
    list_opportunity_performance,
    list_producer_conversion_journeys,
)
from services.insurance_journey_proof_service import (
    get_producer_insurance_journey_proof,
)
from services.outcome_money_reconciliation_service import (
    get_producer_outcome_money_review,
)
from services.channel_readiness_service import get_channel_readiness, recommend_channels
from utils.security import (
    require_admin_or_partner_key,
    require_admin_partner_or_producer_key,
)
from utils.permissions import (
    require_partner_tenant_scope,
    require_producer_scope,
)


router = APIRouter(
    prefix="/v1/tenants/{tenant_code}/producers/{producer_code}/supply",
    tags=["Producer Supply"],
)


def _normalise_code(value: str) -> str:
    return value.strip().upper()


def _enforce_tenant_access(identity: dict[str, Any], tenant_code: str) -> None:
    require_partner_tenant_scope(identity, tenant_code)


def _enforce_producer_proof_access(
    identity: dict[str, Any],
    tenant_code: str,
    producer_code: str,
) -> None:
    require_producer_scope(
        identity,
        tenant_code=tenant_code,
        producer_code=producer_code,
    )


def _handle_supply_error(exc: Exception) -> HTTPException:
    if isinstance(exc, OpportunityNotFound):
        return HTTPException(status_code=404, detail=str(exc))

    if isinstance(exc, (OpportunityDuplicate, OpportunityInvalidState)):
        return HTTPException(status_code=409, detail=str(exc))

    if isinstance(exc, OpportunityError):
        return HTTPException(status_code=400, detail=str(exc))

    return HTTPException(status_code=500, detail="Unexpected producer supply error")


def _campaign_code_from_result(body: dict[str, Any]) -> str | None:
    return (
        body.get("campaign_code")
        or body.get("campaignCode")
        or (body.get("campaign") or {}).get("campaign_code")
        or (body.get("campaign") or {}).get("campaignCode")
    )


def _opportunity_code_from_campaign(campaign_code: str) -> str:
    return f"{campaign_code}-OPP"


def _producer_matches(
    opportunity: dict[str, Any], tenant_code: str, producer_code: str
) -> bool:
    return _normalise_code(str(opportunity.get("tenant_code", ""))) == _normalise_code(
        tenant_code
    ) and _normalise_code(str(opportunity.get("sponsor_code", ""))) == _normalise_code(
        producer_code
    )


async def _get_producer_opportunity(
    *,
    opportunity_id: str,
    tenant_code: str,
    producer_code: str,
) -> dict[str, Any]:
    opportunity = await get_opportunity(opportunity_id=opportunity_id)
    if not _producer_matches(opportunity, tenant_code, producer_code):
        raise OpportunityNotFound("Opportunity not found for producer")
    return opportunity


def _require_status(
    opportunity: dict[str, Any], allowed: set[str], action: str
) -> None:
    status = _normalise_code(str(opportunity.get("opportunity_status", "")))
    if status not in allowed:
        allowed_label = ", ".join(sorted(allowed))
        raise OpportunityInvalidState(
            f"Cannot {action} opportunity with status {status or 'UNKNOWN'}; expected {allowed_label}"
        )


async def _audit_producer_supply_action(
    *,
    action_type: str,
    identity: dict[str, Any],
    tenant_code: str,
    producer_code: str,
    opportunity_id: str,
    opportunity: dict[str, Any],
    request_payload: dict[str, Any] | None = None,
) -> None:
    await try_write_admin_audit(
        action_type=action_type,
        action_domain="PRODUCER_SUPPLY",
        identity=identity,
        tenant_code=_normalise_code(tenant_code),
        target_type="distribution_opportunity",
        target_id=opportunity_id,
        request_payload=request_payload,
        result_payload={
            "producer_code": _normalise_code(producer_code),
            "opportunity_id": str(opportunity.get("opportunity_id")),
            "opportunity_status": opportunity.get("opportunity_status"),
        },
    )


@router.post("/launches")
async def create_supply_launch(
    tenant_code: str,
    producer_code: str,
    request: ProducerSupplyLaunchRequest,
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)

    tenant = _normalise_code(tenant_code)
    producer = _normalise_code(producer_code)
    metadata = {
        **(request.metadata or {}),
        "source": "producer_supply_api",
        "producer_code": producer,
    }

    campaign_body, campaign_status = await create_campaign(
        tenant_code=tenant,
        segment=request.segment,
        name=request.campaign_name,
        campaign_code=request.campaign_code,
        starts_at=request.starts_at,
        ends_at=request.ends_at,
        attributes=metadata,
    )

    if campaign_body.get("ok") is False:
        raise HTTPException(
            status_code=campaign_status,
            detail=campaign_body.get("message", "Campaign creation failed"),
        )

    campaign_code = _campaign_code_from_result(campaign_body)
    if not campaign_code:
        raise HTTPException(status_code=500, detail="Campaign response invalid")

    try:
        opportunity = await create_opportunity(
            tenant_code=tenant,
            sponsor_code=producer,
            opportunity_code=request.opportunity_code
            or _opportunity_code_from_campaign(campaign_code),
            title=request.opportunity_title,
            description=request.description,
            campaign_code=campaign_code,
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
            metadata={
                **metadata,
                "campaign": campaign_body,
            },
        )

        if request.publish_now:
            opportunity = await publish_opportunity(
                opportunity_id=str(opportunity["opportunity_id"]),
            )

        await try_write_admin_audit(
            action_type="PRODUCER_SUPPLY_LAUNCH_CREATE",
            action_domain="PRODUCER_SUPPLY",
            identity=identity,
            tenant_code=tenant,
            target_type="distribution_opportunity",
            target_id=str(opportunity.get("opportunity_id")),
            request_payload=request.model_dump(mode="json"),
            result_payload={
                "producer_code": producer,
                "campaign_code": campaign_code,
                "opportunity_id": str(opportunity.get("opportunity_id")),
                "opportunity_status": opportunity.get("opportunity_status"),
            },
        )

        return {
            "status": "ok",
            "mode": "published" if request.publish_now else "draft",
            "tenant_code": tenant,
            "producer_code": producer,
            "campaign": {
                "campaign_code": campaign_code,
                "mode": campaign_body.get("mode"),
            },
            "opportunity": opportunity,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise _handle_supply_error(exc) from exc


@router.get("/opportunities", response_model=list[OpportunityResponse])
async def list_supply_opportunities(
    tenant_code: str,
    producer_code: str,
    campaign_code: str | None = Query(default=None),
    opportunity_status: str | None = Query(default=None),
    segment: str | None = Query(default=None),
    region: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    distributor_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> list[dict[str, Any]]:
    _enforce_tenant_access(identity, tenant_code)
    return await list_opportunities(
        tenant_code=_normalise_code(tenant_code),
        sponsor_code=_normalise_code(producer_code),
        campaign_code=campaign_code,
        opportunity_status=(
            _normalise_code(opportunity_status) if opportunity_status else None
        ),
        segment=_normalise_code(segment) if segment else None,
        region=_normalise_code(region) if region else None,
        channel=_normalise_code(channel) if channel else None,
        distributor_type=(
            _normalise_code(distributor_type) if distributor_type else None
        ),
        limit=limit,
    )


@router.get("/performance/overview", response_model=MarketplaceOverviewResponse)
async def get_supply_performance_overview(
    tenant_code: str,
    producer_code: str,
    campaign_code: str | None = Query(default=None),
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)
    return await get_marketplace_overview(
        tenant_code=_normalise_code(tenant_code),
        sponsor_code=_normalise_code(producer_code),
        campaign_code=_normalise_code(campaign_code) if campaign_code else None,
    )


@router.get(
    "/performance/opportunities", response_model=list[OpportunityPerformanceResponse]
)
async def list_supply_opportunity_performance(
    tenant_code: str,
    producer_code: str,
    campaign_code: str | None = Query(default=None),
    opportunity_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> list[dict[str, Any]]:
    _enforce_tenant_access(identity, tenant_code)
    return await list_opportunity_performance(
        tenant_code=_normalise_code(tenant_code),
        sponsor_code=_normalise_code(producer_code),
        campaign_code=_normalise_code(campaign_code) if campaign_code else None,
        opportunity_status=(
            _normalise_code(opportunity_status) if opportunity_status else None
        ),
        limit=limit,
    )


@router.get("/conversions", response_model=ProducerSupplyConversionListResponse)
async def list_supply_conversions(
    tenant_code: str,
    producer_code: str,
    campaign_code: str | None = Query(default=None),
    opportunity_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)
    return await list_producer_conversion_journeys(
        tenant_code=_normalise_code(tenant_code),
        sponsor_code=_normalise_code(producer_code),
        campaign_code=_normalise_code(campaign_code) if campaign_code else None,
        opportunity_id=opportunity_id,
        limit=limit,
    )


@router.get("/proof/insurance")
async def get_supply_insurance_proof(
    tenant_code: str,
    producer_code: str,
    identity: dict[str, Any] = Depends(require_admin_partner_or_producer_key),
) -> dict[str, Any]:
    _enforce_producer_proof_access(identity, tenant_code, producer_code)
    return await get_producer_insurance_journey_proof(
        tenant_code=_normalise_code(tenant_code),
        producer_code=_normalise_code(producer_code),
    )


@router.get("/outcome-money-review")
async def get_supply_outcome_money_review(
    tenant_code: str,
    producer_code: str,
    limit: int = Query(default=100, ge=1, le=250),
    identity: dict[str, Any] = Depends(require_admin_partner_or_producer_key),
) -> dict[str, Any]:
    _enforce_producer_proof_access(identity, tenant_code, producer_code)
    review = await get_producer_outcome_money_review(
        tenant_code=tenant_code,
        producer_code=producer_code,
        limit=limit,
    )
    return {
        "status": "ok",
        "review": review,
    }


@router.get("/channel-recommendations")
async def get_supply_channel_recommendations(
    tenant_code: str,
    producer_code: str,
    event_type: str = Query(default="OPPORTUNITY_PUBLISHED"),
    audience: str = Query(default="DISTRIBUTOR"),
    target_channels: list[str] | None = Query(default=None),
    identity: dict[str, Any] = Depends(require_admin_partner_or_producer_key),
) -> dict[str, Any]:
    _enforce_producer_proof_access(identity, tenant_code, producer_code)
    return {
        "status": "ok",
        "recommendations": recommend_channels(
            event_type=event_type,
            audience=audience,
            target_channels=target_channels,
        ),
    }


@router.get("/channel-readiness")
async def get_supply_channel_readiness(
    tenant_code: str,
    producer_code: str,
    identity: dict[str, Any] = Depends(require_admin_partner_or_producer_key),
) -> dict[str, Any]:
    _enforce_producer_proof_access(identity, tenant_code, producer_code)
    return {
        "status": "ok",
        "surface": "Producer - Supply",
        "tenant_code": _normalise_code(tenant_code),
        "producer_code": _normalise_code(producer_code),
        "readiness": get_channel_readiness(),
    }


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def get_supply_opportunity(
    tenant_code: str,
    producer_code: str,
    opportunity_id: str,
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)
    try:
        return await _get_producer_opportunity(
            opportunity_id=opportunity_id,
            tenant_code=tenant_code,
            producer_code=producer_code,
        )
    except Exception as exc:
        raise _handle_supply_error(exc) from exc


@router.patch("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def update_supply_opportunity(
    tenant_code: str,
    producer_code: str,
    opportunity_id: str,
    request: UpdateOpportunityRequest,
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)
    try:
        existing = await _get_producer_opportunity(
            opportunity_id=opportunity_id,
            tenant_code=tenant_code,
            producer_code=producer_code,
        )
        _require_status(existing, {OPPORTUNITY_STATUS_DRAFT}, "edit")
        opportunity = await update_opportunity(
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
            metadata=(
                {
                    **(request.metadata or {}),
                    "source": "producer_supply_api",
                    "producer_code": _normalise_code(producer_code),
                }
                if request.metadata is not None
                else None
            ),
        )
        await _audit_producer_supply_action(
            action_type="PRODUCER_SUPPLY_OPPORTUNITY_UPDATE",
            identity=identity,
            tenant_code=tenant_code,
            producer_code=producer_code,
            opportunity_id=opportunity_id,
            opportunity=opportunity,
            request_payload=request.model_dump(mode="json", exclude_none=True),
        )
        return opportunity
    except Exception as exc:
        raise _handle_supply_error(exc) from exc


@router.post(
    "/opportunities/{opportunity_id}/publish", response_model=OpportunityResponse
)
async def publish_supply_opportunity(
    tenant_code: str,
    producer_code: str,
    opportunity_id: str,
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)
    try:
        existing = await _get_producer_opportunity(
            opportunity_id=opportunity_id,
            tenant_code=tenant_code,
            producer_code=producer_code,
        )
        _require_status(existing, {OPPORTUNITY_STATUS_DRAFT}, "publish")
        opportunity = await publish_opportunity(opportunity_id=opportunity_id)
        await _audit_producer_supply_action(
            action_type="PRODUCER_SUPPLY_OPPORTUNITY_PUBLISH",
            identity=identity,
            tenant_code=tenant_code,
            producer_code=producer_code,
            opportunity_id=opportunity_id,
            opportunity=opportunity,
        )
        return opportunity
    except Exception as exc:
        raise _handle_supply_error(exc) from exc


@router.post(
    "/opportunities/{opportunity_id}/close", response_model=OpportunityResponse
)
async def close_supply_opportunity(
    tenant_code: str,
    producer_code: str,
    opportunity_id: str,
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)
    try:
        existing = await _get_producer_opportunity(
            opportunity_id=opportunity_id,
            tenant_code=tenant_code,
            producer_code=producer_code,
        )
        _require_status(existing, {OPPORTUNITY_STATUS_PUBLISHED}, "close")
        opportunity = await close_opportunity(opportunity_id=opportunity_id)
        await _audit_producer_supply_action(
            action_type="PRODUCER_SUPPLY_OPPORTUNITY_CLOSE",
            identity=identity,
            tenant_code=tenant_code,
            producer_code=producer_code,
            opportunity_id=opportunity_id,
            opportunity=opportunity,
        )
        return opportunity
    except Exception as exc:
        raise _handle_supply_error(exc) from exc


@router.post(
    "/opportunities/{opportunity_id}/reopen", response_model=OpportunityResponse
)
async def reopen_supply_opportunity(
    tenant_code: str,
    producer_code: str,
    opportunity_id: str,
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)
    try:
        existing = await _get_producer_opportunity(
            opportunity_id=opportunity_id,
            tenant_code=tenant_code,
            producer_code=producer_code,
        )
        _require_status(existing, {OPPORTUNITY_STATUS_CLOSED}, "reopen")
        opportunity = await reopen_opportunity(opportunity_id=opportunity_id)
        await _audit_producer_supply_action(
            action_type="PRODUCER_SUPPLY_OPPORTUNITY_REOPEN",
            identity=identity,
            tenant_code=tenant_code,
            producer_code=producer_code,
            opportunity_id=opportunity_id,
            opportunity=opportunity,
        )
        return opportunity
    except Exception as exc:
        raise _handle_supply_error(exc) from exc
