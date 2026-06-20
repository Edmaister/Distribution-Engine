from __future__ import annotations

import asyncio
from time import perf_counter
from typing import Any, Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from apps.api.routers import dashboard as dashboard_router
from services.insurance_journey_proof_service import (
    get_consumer_insurance_journey_proof,
)
from services.leaderboard_service import (
    get_next_rank_info,
    get_referrer_leaderboard_entry,
)
from services.mission_service import get_missions_for_referrer
from services.reward_summary_service import get_reward_summary_for_referrer
from utils.permissions import require_consumer_scope
from utils.security import require_admin_partner_or_consumer_key
from utils.metrics import (
    bff_aggregate_request_inc,
    bff_aggregate_section_observe,
)


router = APIRouter(
    prefix="/v1/experience/consumer",
    tags=["Consumer Experience"],
    dependencies=[Depends(require_admin_partner_or_consumer_key)],
)

DEFAULT_LEADERBOARD_CODE = "GLOBAL_OVERALL"
DEFAULT_SECTION_TIMEOUT_SECONDS = 2.0


class ExperienceSection(BaseModel):
    status: str
    data: Any | None = None
    error: str | None = None
    degraded: bool = False


class ConsumerExperienceResponse(BaseModel):
    status: str
    tenantCode: str
    referrerUcn: str
    referralTrackId: str | None = None
    leaderboardCode: str
    sections: dict[str, ExperienceSection] = Field(default_factory=dict)
    unavailableSections: list[str] = Field(default_factory=list)
    guardrail: str


async def _section(
    name: str,
    loader: Callable[[], Awaitable[Any]],
    *,
    tenant_code: str,
    timeout_seconds: float = DEFAULT_SECTION_TIMEOUT_SECONDS,
) -> tuple[str, ExperienceSection]:
    route = "consumer_experience"
    start = perf_counter()
    status = "unavailable"
    try:
        status = "ok"
        return name, ExperienceSection(
            status="ok",
            data=await asyncio.wait_for(loader(), timeout=timeout_seconds),
        )
    except TimeoutError:
        status = "timeout"
        return name, ExperienceSection(
            status="timeout",
            error=f"{name} section timed out after {timeout_seconds:g}s",
            degraded=True,
        )
    except HTTPException as exc:
        status = "unavailable"
        return name, ExperienceSection(
            status="unavailable",
            error=str(exc.detail),
            degraded=True,
        )
    except Exception as exc:  # pragma: no cover - defensive boundary
        status = "unavailable"
        return name, ExperienceSection(
            status="unavailable",
            error=str(exc),
            degraded=True,
        )
    finally:
        bff_aggregate_section_observe(
            route=route,
            tenant=tenant_code,
            section=name,
            status=status,
            latency_seconds=perf_counter() - start,
        )


async def _leaderboard_payload(
    *,
    leaderboard_code: str,
    referrer_ucn: str,
    tenant_code: str,
) -> dict[str, Any] | None:
    entry = await get_referrer_leaderboard_entry(
        leaderboard_code,
        referrer_ucn,
        tenant_code=tenant_code,
    )
    if not entry:
        return None

    next_rank = await get_next_rank_info(
        leaderboard_code,
        referrer_ucn,
        tenant_code=tenant_code,
    )
    return {
        "entry": entry,
        "nextRank": next_rank,
    }


@router.get("", response_model=ConsumerExperienceResponse)
async def get_consumer_experience(
    referrer_ucn: str = Query(..., min_length=1),
    tenant_code: str | None = Query(default=None, min_length=2),
    referral_track_id: str | None = Query(default=None, min_length=1),
    leaderboard_code: str = Query(DEFAULT_LEADERBOARD_CODE, min_length=1),
    include_insurance_proof: bool = Query(False),
    section_timeout_seconds: float = Query(
        DEFAULT_SECTION_TIMEOUT_SECONDS,
        ge=0.05,
        le=10,
        include_in_schema=False,
    ),
    identity: dict[str, Any] = Depends(require_admin_partner_or_consumer_key),
) -> ConsumerExperienceResponse:
    resolved_tenant = (
        tenant_code
        or str(identity.get("tenant_code") or identity.get("tenant") or "FNB")
    ).upper()
    require_consumer_scope(identity, tenant_code=resolved_tenant)

    loaders: list[tuple[str, Callable[[], Awaitable[Any]]]] = [
        (
            "profile",
            lambda: dashboard_router._get_referrals_for_referrer(
                referrer_ucn,
                resolved_tenant,
            ),
        ),
        (
            "rewards",
            lambda: get_reward_summary_for_referrer(
                referrer_ucn,
                tenant_code=resolved_tenant,
            ),
        ),
        (
            "missions",
            lambda: get_missions_for_referrer(
                referrer_ucn=referrer_ucn,
                tenant_code=resolved_tenant,
                channel="BFF",
                audit=False,
                grouped=True,
            ),
        ),
        (
            "leaderboard",
            lambda: _leaderboard_payload(
                leaderboard_code=leaderboard_code,
                referrer_ucn=referrer_ucn,
                tenant_code=resolved_tenant,
            ),
        ),
    ]

    if referral_track_id and include_insurance_proof:
        loaders.append(
            (
                "insuranceProof",
                lambda: get_consumer_insurance_journey_proof(
                    tenant_code=resolved_tenant,
                    referral_track_id=referral_track_id,
                ),
            )
        )

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
        route="consumer_experience",
        tenant=resolved_tenant,
        status=response_status,
    )

    return ConsumerExperienceResponse(
        status=response_status,
        tenantCode=resolved_tenant,
        referrerUcn=referrer_ucn,
        referralTrackId=referral_track_id,
        leaderboardCode=leaderboard_code,
        sections=sections,
        unavailableSections=unavailable,
        guardrail=(
            "Consumer experience BFF response aggregates read-only consumer "
            "sections. It does not create referrals, issue rewards, or send "
            "channel messages."
        ),
    )
