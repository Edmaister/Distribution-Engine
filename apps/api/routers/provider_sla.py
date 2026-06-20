from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from services.provider_sla_service import (
    get_provider_sla_metrics,
    list_provider_sla_metrics,
)

from services.provider_scorecard_service import (
    calculate_provider_scorecard,
    calculate_provider_scorecards,
)
from services.provider_ranking_service import rank_providers
from utils.security import require_admin_key

router = APIRouter(
    prefix="/admin/providers",
    tags=["Admin Provider SLA"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("/sla")
async def get_all_provider_sla_metrics():
    items = await list_provider_sla_metrics()

    return {
        "status": "ok",
        "count": len(items),
        "items": items,
    }


@router.get("/scorecards")
async def get_all_provider_scorecards():
    metrics = await list_provider_sla_metrics()

    scorecards = calculate_provider_scorecards(
        metrics=metrics,
    )

    return {
        "status": "ok",
        "count": len(scorecards),
        "items": scorecards,
    }


@router.get("/{provider_key}/sla")
async def get_provider_sla(
    provider_key: str,
):
    metrics = await get_provider_sla_metrics(
        provider_key=provider_key,
    )

    if metrics is None:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider_key}' not found",
        )

    return {
        "status": "ok",
        "item": metrics,
    }


@router.get("/{provider_key}/scorecard")
async def get_provider_scorecard(
    provider_key: str,
):
    metrics = await get_provider_sla_metrics(
        provider_key=provider_key,
    )

    if metrics is None:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider_key}' not found",
        )

    scorecard = calculate_provider_scorecard(
        metrics=metrics,
    )

    return {
        "status": "ok",
        "item": scorecard,
    }

@router.get("/rankings")
async def get_provider_rankings():
    metrics = await list_provider_sla_metrics()

    scorecards = calculate_provider_scorecards(
        metrics=metrics,
    )

    rankings = rank_providers(
        scorecards=scorecards,
    )

    return {
        "status": "ok",
        "count": len(scorecards),
        **rankings,
    }
