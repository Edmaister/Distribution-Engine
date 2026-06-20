from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from utils.security import require_admin_or_partner_key
from apps.api.schemas.reward_summary import (
    ReferrerRewardSummaryResponse,
    RewardSummaryComplianceMetadata,
    RewardSummaryItem,
    RewardSummaryResponse,
    RewardSummaryTotals,
)
from services.reward_summary_service import (
    get_reward_summary_for_referral,
    get_reward_summary_for_referrer,
)

router = APIRouter(
    prefix="/v1/rewards/summary",
    tags=["reward-summary"],
    dependencies=[Depends(require_admin_or_partner_key)],
)


@router.get(
    "/referrers/{referrer_ucn}",
    response_model=ReferrerRewardSummaryResponse,
)
async def get_referrer_reward_summary(
    referrer_ucn: str,
    identity=Depends(require_admin_or_partner_key),
) -> ReferrerRewardSummaryResponse:

    tenant_code = identity.get("tenant_code")

    result = await get_reward_summary_for_referrer(
        referrer_ucn,
        tenant_code=tenant_code,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Referrer not found or no reward summary available",
        )

    return ReferrerRewardSummaryResponse(
        referrerUcn=result["referrerUcn"],
        currency=result["currency"],
        generatedAt=result["generatedAt"],
        totals=RewardSummaryTotals(**result["totals"]),
        referralsCount=result["referralsCount"],
        completedReferralsCount=result["completedReferralsCount"],
        pendingBonusesCount=result["pendingBonusesCount"],
        count=result["count"],
        disclosures=result.get("disclosures", []),
        compliance=RewardSummaryComplianceMetadata(
            **result["compliance"]
        ),
    )


@router.get(
    "/{referral_track_id}",
    response_model=RewardSummaryResponse,
)
async def get_reward_summary(
    referral_track_id: str,
    identity=Depends(require_admin_or_partner_key),
) -> RewardSummaryResponse:

    tenant_code = identity.get("tenant_code")

    result = await get_reward_summary_for_referral(
        referral_track_id,
        tenant_code=tenant_code,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Referral not found or no reward summary available",
        )

    return RewardSummaryResponse(
        referralTrackId=result["referralTrackId"],
        currency=result["currency"],
        generatedAt=result["generatedAt"],
        referrer=RewardSummaryTotals(**result["referrer"]),
        referee=RewardSummaryTotals(**result["referee"]),
        count=result["count"],
        items=[
            RewardSummaryItem(**item)
            for item in result["items"]
        ],
        disclosures=result.get("disclosures", []),
        compliance=RewardSummaryComplianceMetadata(
            **result["compliance"]
        ),
    )