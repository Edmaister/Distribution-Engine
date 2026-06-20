from __future__ import annotations

import asyncio
from time import perf_counter
from typing import Any, Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services.funding.alerts import list_funding_alerts
from services.funding.forecasting import (
    DEFAULT_BUFFER_DAYS,
    DEFAULT_BURN_WINDOW_DAYS,
    get_sponsor_funding_forecast,
)
from services.channel_readiness_service import get_channel_readiness, recommend_channels
from services.distribution.opportunity_service import list_opportunities
from services.distribution.reporting_service import (
    get_marketplace_overview,
    list_opportunity_performance,
    list_producer_conversion_journeys,
)
from services.insurance_journey_proof_service import (
    get_producer_insurance_journey_proof,
)
from services.marketplace_funding.funding_contract_service import list_funding_contracts
from services.marketplace_funding.sponsor_billing_service import (
    get_sponsor_billing_dashboard,
    list_sponsor_invoices,
    list_sponsor_payment_receipts,
)
from services.marketplace_funding.sponsor_wallet_service import (
    get_sponsor_wallet_by_sponsor,
)
from services.outcome_money_reconciliation_service import (
    get_producer_outcome_money_review,
)
from utils.metrics import bff_aggregate_request_inc, bff_aggregate_section_observe
from utils.permissions import require_producer_scope
from utils.security import require_admin_partner_or_producer_key


router = APIRouter(
    prefix="/v1/experience/sponsor",
    tags=["Sponsor Experience"],
    dependencies=[Depends(require_admin_partner_or_producer_key)],
)

DEFAULT_SECTION_TIMEOUT_SECONDS = 2.0
ROUTE_METRIC = "sponsor"


class SponsorExperienceSection(BaseModel):
    status: str
    data: Any | None = None
    error: str | None = None
    degraded: bool = False


class SponsorExperienceResponse(BaseModel):
    status: str
    tenantCode: str
    sponsorCode: str
    sections: dict[str, SponsorExperienceSection] = Field(default_factory=dict)
    unavailableSections: list[str] = Field(default_factory=list)
    guardrail: str


async def _section(
    name: str,
    loader: Callable[[], Awaitable[Any]],
    *,
    tenant_code: str,
    timeout_seconds: float = DEFAULT_SECTION_TIMEOUT_SECONDS,
) -> tuple[str, SponsorExperienceSection]:
    start = perf_counter()
    status = "unavailable"
    try:
        status = "ok"
        return name, SponsorExperienceSection(
            status="ok",
            data=await asyncio.wait_for(loader(), timeout=timeout_seconds),
        )
    except TimeoutError:
        status = "timeout"
        return name, SponsorExperienceSection(
            status="timeout",
            error=f"{name} section timed out after {timeout_seconds:g}s",
            degraded=True,
        )
    except HTTPException as exc:
        status = "unavailable"
        return name, SponsorExperienceSection(
            status="unavailable",
            error=str(exc.detail),
            degraded=True,
        )
    except Exception as exc:  # pragma: no cover - defensive boundary
        status = "unavailable"
        return name, SponsorExperienceSection(
            status="unavailable",
            error=str(exc),
            degraded=True,
        )
    finally:
        bff_aggregate_section_observe(
            route=ROUTE_METRIC,
            tenant=tenant_code,
            section=name,
            status=status,
            latency_seconds=perf_counter() - start,
        )


@router.get("", response_model=SponsorExperienceResponse)
async def get_sponsor_experience(
    tenant_code: str = Query(..., min_length=2),
    sponsor_code: str = Query(..., min_length=2),
    currency: str = Query(default="ZAR", min_length=3, max_length=3),
    limit: int = Query(default=25, ge=1, le=100),
    section_timeout_seconds: float = Query(
        DEFAULT_SECTION_TIMEOUT_SECONDS,
        ge=0.05,
        le=10,
        include_in_schema=False,
    ),
    identity: dict = Depends(require_admin_partner_or_producer_key),
) -> SponsorExperienceResponse:
    resolved_tenant = tenant_code.strip().upper()
    resolved_sponsor = sponsor_code.strip().upper()
    resolved_currency = currency.strip().upper()
    require_producer_scope(
        identity,
        tenant_code=resolved_tenant,
        producer_code=resolved_sponsor,
    )

    loaders: list[tuple[str, Callable[[], Awaitable[Any]]]] = [
        (
            "billing",
            lambda: get_sponsor_billing_dashboard(
                tenant_code=resolved_tenant,
                sponsor_code=resolved_sponsor,
                currency=resolved_currency,
                limit=limit,
            ),
        ),
        (
            "invoices",
            lambda: list_sponsor_invoices(
                tenant_code=resolved_tenant,
                sponsor_code=resolved_sponsor,
                limit=limit,
            ),
        ),
        (
            "receipts",
            lambda: list_sponsor_payment_receipts(
                tenant_code=resolved_tenant,
                sponsor_code=resolved_sponsor,
                limit=limit,
            ),
        ),
        (
            "wallet",
            lambda: _wallet_payload(
                tenant_code=resolved_tenant,
                sponsor_code=resolved_sponsor,
            ),
        ),
        (
            "contracts",
            lambda: list_funding_contracts(
                tenant_code=resolved_tenant,
                sponsor_code=resolved_sponsor,
                limit=limit,
            ),
        ),
        (
            "forecast",
            lambda: _forecast_payload(
                tenant_code=resolved_tenant,
                sponsor_code=resolved_sponsor,
                currency=resolved_currency,
            ),
        ),
        (
            "alerts",
            lambda: _alerts_payload(tenant_code=resolved_tenant, limit=limit),
        ),
        (
            "opportunities",
            lambda: list_opportunities(
                tenant_code=resolved_tenant,
                sponsor_code=resolved_sponsor,
                limit=limit,
            ),
        ),
        (
            "performanceOverview",
            lambda: get_marketplace_overview(
                tenant_code=resolved_tenant,
                sponsor_code=resolved_sponsor,
            ),
        ),
        (
            "opportunityPerformance",
            lambda: list_opportunity_performance(
                tenant_code=resolved_tenant,
                sponsor_code=resolved_sponsor,
                limit=limit,
            ),
        ),
        (
            "conversions",
            lambda: list_producer_conversion_journeys(
                tenant_code=resolved_tenant,
                sponsor_code=resolved_sponsor,
                limit=limit,
            ),
        ),
        (
            "outcomeMoney",
            lambda: get_producer_outcome_money_review(
                tenant_code=resolved_tenant,
                producer_code=resolved_sponsor,
                limit=limit,
            ),
        ),
        (
            "proof",
            lambda: get_producer_insurance_journey_proof(
                tenant_code=resolved_tenant,
                producer_code=resolved_sponsor,
            ),
        ),
        (
            "channels",
            lambda: _channel_guidance(producer_code=resolved_sponsor),
        ),
    ]

    resolved_sections = await asyncio.gather(
        *[
            _section(
                name,
                loader,
                tenant_code=resolved_tenant,
                timeout_seconds=section_timeout_seconds,
            )
            for name, loader in loaders
        ]
    )
    sections = dict(resolved_sections)
    unavailable = [
        name for name, section in sections.items() if section.status != "ok"
    ]

    response_status = "partial" if unavailable else "ok"
    bff_aggregate_request_inc(
        route=ROUTE_METRIC,
        tenant=resolved_tenant,
        status=response_status,
    )

    return SponsorExperienceResponse(
        status=response_status,
        tenantCode=resolved_tenant,
        sponsorCode=resolved_sponsor,
        sections=sections,
        unavailableSections=unavailable,
        guardrail=(
            "Sponsor BFF response is read-only. Invoice generation, payment "
            "allocation, contract budget movements, and alert actions remain "
            "on explicit command endpoints."
        ),
    )


async def _wallet_payload(*, tenant_code: str, sponsor_code: str) -> dict[str, Any]:
    wallet = await get_sponsor_wallet_by_sponsor(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
    )
    if not wallet:
        raise HTTPException(status_code=404, detail="Sponsor wallet not found")
    return {"wallet": wallet}


async def _forecast_payload(
    *,
    tenant_code: str,
    sponsor_code: str,
    currency: str,
) -> dict[str, Any]:
    forecast = await get_sponsor_funding_forecast(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        currency=currency,
        burn_window_days=DEFAULT_BURN_WINDOW_DAYS,
        buffer_days=DEFAULT_BUFFER_DAYS,
    )
    if not forecast:
        raise HTTPException(status_code=404, detail="Sponsor funding forecast not found")
    return {"forecast": forecast}


async def _alerts_payload(*, tenant_code: str, limit: int) -> dict[str, Any]:
    alerts = await list_funding_alerts(tenant_code=tenant_code, limit=limit)
    return {"count": len(alerts), "items": alerts}


async def _channel_guidance(*, producer_code: str) -> dict[str, Any]:
    return {
        "readiness": get_channel_readiness(),
        "recommendations": recommend_channels(
            event_type="OPPORTUNITY_PUBLISHED",
            audience="DISTRIBUTOR",
            target_channels=None,
        ),
        "producerCode": producer_code,
    }
