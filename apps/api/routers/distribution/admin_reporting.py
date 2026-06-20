from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from apps.api.schemas.distribution.reporting import (
    AttributionExceptionListResponse,
    DistributorPerformanceResponse,
    GovernanceReportResponse,
    MarketplaceOverviewResponse,
    OpportunityPerformanceResponse,
)
from services.distribution.reporting_service import (
    get_governance_report,
    get_marketplace_overview,
    list_attribution_exceptions,
    list_distributor_performance,
    list_opportunity_performance,
)
from utils.security import require_distribution_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/distribution/reporting",
    tags=["Admin Distribution Reporting"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("/overview", response_model=MarketplaceOverviewResponse)
async def overview(
    tenant_code: str = Query(...),
    sponsor_code: str | None = Query(default=None),
    campaign_code: str | None = Query(default=None),
) -> dict:
    return await get_marketplace_overview(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        campaign_code=campaign_code,
    )


@router.get("/opportunities", response_model=list[OpportunityPerformanceResponse])
async def opportunities(
    tenant_code: str = Query(...),
    sponsor_code: str | None = Query(default=None),
    campaign_code: str | None = Query(default=None),
    opportunity_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    return await list_opportunity_performance(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        campaign_code=campaign_code,
        opportunity_status=opportunity_status,
        limit=limit,
    )


@router.get("/distributors", response_model=list[DistributorPerformanceResponse])
async def distributors(
    tenant_code: str = Query(...),
    distributor_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    return await list_distributor_performance(
        tenant_code=tenant_code,
        distributor_type=distributor_type,
        status=status,
        limit=limit,
    )


@router.get("/attribution-exceptions", response_model=AttributionExceptionListResponse)
async def attribution_exceptions(
    tenant_code: str = Query(...),
    limit: int = Query(default=25, ge=1, le=200),
) -> dict:
    return await list_attribution_exceptions(
        tenant_code=tenant_code,
        limit=limit,
    )


@router.get("/governance", response_model=GovernanceReportResponse)
async def governance(tenant_code: str = Query(...)) -> dict:
    return await get_governance_report(tenant_code=tenant_code)
