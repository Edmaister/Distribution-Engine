from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from utils.security import require_admin_or_partner_key

from apps.api.schemas.badge import BadgeItem, BadgeListResponse
from services.badge_service import (
    list_badges_for_referral,
    list_badges_for_referrer,
)
from services.mission_service import _get_referral_row  # consider moving later


router = APIRouter(
    prefix="/v1",
    tags=["Badges"],
    dependencies=[Depends(require_admin_or_partner_key)],
)


@router.get(
    "/referrals/{referral_track_id}/badges",
    response_model=BadgeListResponse,
    summary="Get badges for a referral track",
)
def get_badges_for_referral(
    referral_track_id: str,
    identity=Depends(require_admin_or_partner_key),
) -> BadgeListResponse:

    referral = _get_referral_row(referral_track_id)

    if not referral:
        raise HTTPException(status_code=404, detail="Referral track not found")

    tenant_code = identity.get("tenant_code")

    if not tenant_code and identity.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Tenant access required")

    items = list_badges_for_referral(
        referral_track_id=referral_track_id,
        tenant_code=tenant_code,
    )

    return BadgeListResponse(
        count=len(items),
        items=[BadgeItem(**item) for item in items],
    )


@router.get(
    "/users/{referrer_ucn}/badges",
    response_model=BadgeListResponse,
    summary="Get badges for a referrer (user-level badges)",
)
def get_badges_for_referrer(
    referrer_ucn: str,
    identity=Depends(require_admin_or_partner_key),
) -> BadgeListResponse:

    tenant_code = identity.get("tenant_code")

    if not tenant_code and identity.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Tenant access required")

    items = list_badges_for_referrer(
        referrer_ucn=referrer_ucn,
        tenant_code=tenant_code,
    )

    return BadgeListResponse(
        count=len(items),
        items=[BadgeItem(**item) for item in items],
    )