from __future__ import annotations

import asyncio
from time import perf_counter
from typing import Any, Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services.channel_readiness_service import get_channel_readiness, recommend_channels
from services.distribution.distributor_portal_service import (
    list_portal_conversions,
    list_portal_offers,
    list_portal_wallets,
    get_portal_distributor,
    get_portal_performance,
)
from services.insurance_journey_proof_service import (
    get_distributor_insurance_journey_proof,
)
from services.outcome_money_reconciliation_service import (
    get_distributor_outcome_money_review,
)
from utils.metrics import bff_aggregate_request_inc, bff_aggregate_section_observe
from utils.permissions import require_distributor_scope
from utils.security import require_admin_partner_or_distributor_key


router = APIRouter(
    prefix="/v1/experience/distributor",
    tags=["Distributor Experience"],
    dependencies=[Depends(require_admin_partner_or_distributor_key)],
)

DEFAULT_SECTION_TIMEOUT_SECONDS = 2.0
ROUTE_METRIC = "distributor"


class DistributorExperienceSection(BaseModel):
    status: str
    data: Any | None = None
    error: str | None = None
    degraded: bool = False


class DistributorExperienceResponse(BaseModel):
    status: str
    tenantCode: str
    distributorCode: str
    sections: dict[str, DistributorExperienceSection] = Field(default_factory=dict)
    unavailableSections: list[str] = Field(default_factory=list)
    guardrail: str


async def _section(
    name: str,
    loader: Callable[[], Awaitable[Any]],
    *,
    tenant_code: str,
    timeout_seconds: float = DEFAULT_SECTION_TIMEOUT_SECONDS,
) -> tuple[str, DistributorExperienceSection]:
    start = perf_counter()
    status = "unavailable"
    try:
        status = "ok"
        return name, DistributorExperienceSection(
            status="ok",
            data=await asyncio.wait_for(loader(), timeout=timeout_seconds),
        )
    except TimeoutError:
        status = "timeout"
        return name, DistributorExperienceSection(
            status="timeout",
            error=f"{name} section timed out after {timeout_seconds:g}s",
            degraded=True,
        )
    except HTTPException as exc:
        status = "unavailable"
        return name, DistributorExperienceSection(
            status="unavailable",
            error=str(exc.detail),
            degraded=True,
        )
    except Exception as exc:  # pragma: no cover - defensive boundary
        status = "unavailable"
        return name, DistributorExperienceSection(
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


@router.get("", response_model=DistributorExperienceResponse)
async def get_distributor_experience(
    tenant_code: str = Query(..., min_length=2),
    distributor_code: str = Query(..., min_length=2),
    limit: int = Query(default=25, ge=1, le=100),
    section_timeout_seconds: float = Query(
        DEFAULT_SECTION_TIMEOUT_SECONDS,
        ge=0.05,
        le=10,
        include_in_schema=False,
    ),
    identity: dict = Depends(require_admin_partner_or_distributor_key),
) -> DistributorExperienceResponse:
    resolved_tenant = tenant_code.strip().upper()
    resolved_distributor = distributor_code.strip().upper()
    require_distributor_scope(
        identity,
        tenant_code=resolved_tenant,
        distributor_code=resolved_distributor,
    )

    loaders: list[tuple[str, Callable[[], Awaitable[Any]]]] = [
        (
            "profile",
            lambda: get_portal_distributor(
                tenant_code=resolved_tenant,
                distributor_code=resolved_distributor,
            ),
        ),
        (
            "opportunities",
            lambda: list_portal_offers(
                tenant_code=resolved_tenant,
                distributor_code=resolved_distributor,
                limit=limit,
            ),
        ),
        (
            "wallet",
            lambda: list_portal_wallets(
                tenant_code=resolved_tenant,
                distributor_code=resolved_distributor,
                limit=limit,
            ),
        ),
        (
            "conversions",
            lambda: list_portal_conversions(
                tenant_code=resolved_tenant,
                distributor_code=resolved_distributor,
                limit=limit,
            ),
        ),
        (
            "performance",
            lambda: get_portal_performance(
                tenant_code=resolved_tenant,
                distributor_code=resolved_distributor,
            ),
        ),
        (
            "outcomeMoney",
            lambda: get_distributor_outcome_money_review(
                tenant_code=resolved_tenant,
                distributor_code=resolved_distributor,
                limit=limit,
            ),
        ),
        (
            "proof",
            lambda: get_distributor_insurance_journey_proof(
                tenant_code=resolved_tenant,
                distributor_code=resolved_distributor,
            ),
        ),
        (
            "channels",
            lambda: _channel_guidance(distributor_code=resolved_distributor),
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

    return DistributorExperienceResponse(
        status=response_status,
        tenantCode=resolved_tenant,
        distributorCode=resolved_distributor,
        sections=sections,
        unavailableSections=unavailable,
        guardrail=(
            "Distributor BFF response is read-only. Route accept/decline, "
            "referral linking, wallet mutations, and channel sends remain on "
            "their explicit command endpoints."
        ),
    )


async def _channel_guidance(*, distributor_code: str) -> dict[str, Any]:
    return {
        "readiness": get_channel_readiness(),
        "recommendations": recommend_channels(
            event_type="ROUTE_ASSIGNED",
            audience="DISTRIBUTOR",
            distributor_channels=None,
        ),
        "distributorCode": distributor_code,
    }
