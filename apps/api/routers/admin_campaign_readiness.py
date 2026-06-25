from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from services.campaign_readiness_service import get_campaign_readiness
from utils.security import require_distribution_admin_key

router = APIRouter(
    prefix="/admin/campaigns",
    tags=["Admin - Campaign Readiness"],
)

NOT_FOUND_BLOCKERS = {"CAMPAIGN_NOT_FOUND", "TENANT_MISMATCH"}


def _normalise_tenant_code(tenant_code: str) -> str:
    tenant = str(tenant_code or "").strip().upper()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "tenant_code is required",
            },
        )
    return tenant


def _has_blocker(readiness: dict[str, Any], codes: set[str]) -> bool:
    return any(
        str(blocker.get("code") or "").upper() in codes
        for blocker in readiness.get("blockers", [])
        if isinstance(blocker, dict)
    )


@router.get("/{campaign_code}/readiness")
async def get_admin_campaign_readiness(
    campaign_code: str,
    tenant_code: Annotated[str, Query(min_length=1)],
    operation: Annotated[str, Query(min_length=1)] = "CONTROL_PLANE_VIEW",
    opportunity_id: str | None = Query(default=None),
    include_evidence: bool = Query(default=True),
    identity: dict = Depends(require_distribution_admin_key),
) -> dict[str, Any]:
    resolved_tenant = _normalise_tenant_code(tenant_code)

    try:
        readiness = await get_campaign_readiness(
            tenant_code=resolved_tenant,
            campaign_code=campaign_code,
            operation=operation,
            opportunity_id=opportunity_id,
            include_evidence=include_evidence,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": str(exc),
            },
        ) from exc

    if _has_blocker(readiness, NOT_FOUND_BLOCKERS):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "campaign_readiness_not_found",
                "message": (
                    "Campaign readiness was not found for the requested tenant."
                ),
            },
        )

    return {
        "status": "ok",
        "readiness": readiness,
        "guardrail": (
            "Read-only admin campaign readiness. This endpoint does not mutate "
            "campaigns, policies, referrals, attribution, funding, fulfilment, "
            "settlement, audit, or rewards."
        ),
    }
