from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query

from utils.security import (
    require_admin_or_partner_key,
    require_admin_partner_or_consumer_key,
)
from apps.api.schemas.dashboard import (
    DashboardBadgeItem,
    DashboardLeaderboard,
    DashboardMissionGroups,
    DashboardProgress,
    DashboardReferralCard,
    ReferralDashboardResponse,
    ReferralRewardItem,
    ReferralRewardPartySummary,
    ReferralRewardSummary,
    ReferrerDashboardResponse,
    ReferrerDashboardSummary,
    ReferrerRewardSummary,
    ReferrerRewardTotals,
)
from services.badge_service import list_badges_for_referrer
from services.leaderboard_service import (
    get_next_rank_info,
    get_referrer_leaderboard_entry,
)
from services.mission_service import (
    get_missions_for_referral,
    get_missions_for_referrer,
)
from services.reward_summary_service import (
    get_reward_summary_for_referral,
    get_reward_summary_for_referrer,
)
from services.insurance_journey_proof_service import get_consumer_insurance_journey_proof
from utils.db import get_async_connection


router = APIRouter(
    tags=["Dashboard"],
    dependencies=[Depends(require_admin_partner_or_consumer_key)],
)

DEFAULT_LEADERBOARD_CODE = "GLOBAL_OVERALL"


def _enforce_tenant_access(identity: dict, tenant_code: str) -> None:
    if str(identity.get("role") or "").upper() == "ADMIN":
        return
    if str(identity.get("tenant_code") or "").upper() != tenant_code.upper():
        raise HTTPException(
            status_code=403,
            detail="API key is not authorised for this tenant",
        )


async def _get_referrals_for_referrer(
    referrer_ucn: str,
    tenant_code: str,
):
    async with get_async_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                referral_track_id,
                product,
                sub_product,
                progress_percent,
                progress_band,
                display_status,
                next_milestone,
                is_complete,
                created_at,
                updated_at
            FROM referral_instances
            WHERE referrer_ucn = $1
              AND tenant_code = $2
            ORDER BY updated_at DESC NULLS LAST,
                     created_at DESC NULLS LAST,
                     referral_track_id DESC
            """,
            referrer_ucn,
            tenant_code,
        )

    return [dict(row) for row in rows]


async def _get_referral_progress(
    referral_track_id: str,
    tenant_code: str,
):
    async with get_async_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                referral_track_id,
                referrer_ucn,
                status,
                is_complete,
                progress_percent,
                progress_band,
                display_status,
                next_milestone
            FROM referral_instances
            WHERE referral_track_id = $1
              AND tenant_code = $2
            """,
            referral_track_id,
            tenant_code,
        )

    return dict(row) if row else None


@router.get(
    "/v1/referrers/{referrer_ucn}/dashboard",
    response_model=ReferrerDashboardResponse,
)
async def get_referrer_dashboard(
    referrer_ucn: str,
    identity=Depends(require_admin_or_partner_key),
):

    tenant_code = identity.get("tenant_code")

    referrals = await _get_referrals_for_referrer(
        referrer_ucn,
        tenant_code,
    )

    if not referrals:
        raise HTTPException(
            status_code=404,
            detail="No referrals found for referrer",
        )

    (
        reward_summary,
        missions,
        badges,
        leaderboard_entry,
    ) = await asyncio.gather(
        get_reward_summary_for_referrer(
            referrer_ucn,
            tenant_code=tenant_code,
        ),
        get_missions_for_referrer(
            referrer_ucn=referrer_ucn,
            tenant_code=tenant_code,
            audit=False,
            grouped=True,
        ),
        list_badges_for_referrer(
            referrer_ucn,
            tenant_code=tenant_code,
        ),
        get_referrer_leaderboard_entry(
            DEFAULT_LEADERBOARD_CODE,
            referrer_ucn,
            tenant_code=tenant_code,
        ),
    )

    next_rank = (
        await get_next_rank_info(
            DEFAULT_LEADERBOARD_CODE,
            referrer_ucn,
            tenant_code=tenant_code,
        )
        if leaderboard_entry
        else None
    )

    totals = reward_summary["totals"]

    return ReferrerDashboardResponse(
        summary=ReferrerDashboardSummary(
            referrerUcn=referrer_ucn,
            currency=reward_summary["currency"],
            generatedAt=reward_summary["generatedAt"],
            totalEarned=int(totals["earned"]),
            totalPending=int(totals["pending"]),
            totalPotential=int(totals["totalPotential"]),
            nextEligibleReward=int(totals["nextEligibleReward"]),
            referralsCount=int(reward_summary["referralsCount"]),
            completedReferralsCount=int(
                reward_summary["completedReferralsCount"]
            ),
            pendingBonusesCount=int(
                reward_summary["pendingBonusesCount"]
            ),
            badgeCount=len(badges),
            leaderboardRank=(
                leaderboard_entry["rank_position"]
                if leaderboard_entry else None
            ),
            leaderboardTier=(
                leaderboard_entry["rank_tier"]
                if leaderboard_entry else None
            ),
            totalScore=(
                leaderboard_entry["total_score"]
                if leaderboard_entry else None
            ),
            pointsToNextRank=(
                next_rank["points_to_next_rank"]
                if next_rank else None
            ),
        ),
        rewards=ReferrerRewardSummary(
            currency=reward_summary["currency"],
            generatedAt=reward_summary["generatedAt"],
            totals=ReferrerRewardTotals(
                **reward_summary["totals"]
            ),
            referralsCount=reward_summary["referralsCount"],
            completedReferralsCount=reward_summary[
                "completedReferralsCount"
            ],
            pendingBonusesCount=reward_summary[
                "pendingBonusesCount"
            ],
            count=reward_summary["count"],
            disclosures=reward_summary.get(
                "disclosures"
            ) or [],
            compliance=reward_summary["compliance"],
        ),
        missions=DashboardMissionGroups(
            core=missions.get("core", []),
            boost=missions.get("boost", []),
            milestone=missions.get("milestone", []),
        ),
        badges=[
            DashboardBadgeItem(**badge)
            for badge in badges
        ],
        leaderboard=DashboardLeaderboard(
            leaderboardCode=(
                leaderboard_entry["leaderboard_code"]
                if leaderboard_entry else None
            ),
            rankPosition=(
                leaderboard_entry["rank_position"]
                if leaderboard_entry else None
            ),
            rankTier=(
                leaderboard_entry["rank_tier"]
                if leaderboard_entry else None
            ),
            pointsToNextRank=(
                next_rank["points_to_next_rank"]
                if next_rank else None
            ),
        ),
        referrals=[
            DashboardReferralCard(
                referralTrackId=str(
                    referral["referral_track_id"]
                ),
                product=referral.get("product"),
                subProduct=referral.get("sub_product"),
                progressPercent=int(
                    referral.get("progress_percent") or 0
                ),
                progressBand=referral.get("progress_band"),
                displayStatus=referral.get("display_status"),
                nextMilestone=referral.get("next_milestone"),
                isComplete=bool(
                    referral.get("is_complete")
                ),
                createdAt=referral.get("created_at"),
                updatedAt=referral.get("updated_at"),
            )
            for referral in referrals
        ],
    )


@router.get("/v1/tenants/{tenant_code}/consumer/proof/insurance")
async def get_consumer_insurance_proof(
    tenant_code: str,
    referral_track_id: str | None = Query(default=None),
    identity=Depends(require_admin_partner_or_consumer_key),
) -> dict:
    _enforce_tenant_access(identity, tenant_code)
    return await get_consumer_insurance_journey_proof(
        tenant_code=tenant_code.strip().upper(),
        referral_track_id=referral_track_id,
    )


@router.get(
    "/v1/referrals/{referral_track_id}/dashboard",
    response_model=ReferralDashboardResponse,
)
async def get_referral_dashboard(
    referral_track_id: str,
    identity=Depends(require_admin_or_partner_key),
):

    tenant_code = identity.get("tenant_code")

    progress = await _get_referral_progress(
        referral_track_id,
        tenant_code,
    )

    if not progress:
        raise HTTPException(
            status_code=404,
            detail="Referral track not found",
        )

    reward_summary, missions = await asyncio.gather(
        get_reward_summary_for_referral(
            referral_track_id,
            tenant_code=tenant_code,
        ),
        get_missions_for_referral(
            referral_track_id=referral_track_id,
            tenant_code=tenant_code,
            audit=False,
            grouped=True,
        ),
    )

    if not reward_summary:
        raise HTTPException(
            status_code=404,
            detail="Reward summary not found",
        )

    return ReferralDashboardResponse(
        referralTrackId=referral_track_id,
        referrerUcn=progress["referrer_ucn"],
        progress=DashboardProgress(
            status=progress["status"],
            isComplete=bool(progress["is_complete"]),
            progressPercent=int(
                progress.get("progress_percent") or 0
            ),
            progressBand=progress.get("progress_band"),
            displayStatus=progress.get("display_status"),
            nextMilestone=progress.get("next_milestone"),
        ),
        rewards=ReferralRewardSummary(
            referralTrackId=reward_summary[
                "referralTrackId"
            ],
            currency=reward_summary["currency"],
            generatedAt=reward_summary["generatedAt"],
            referrer=ReferralRewardPartySummary(
                **reward_summary["referrer"]
            ),
            referee=ReferralRewardPartySummary(
                **reward_summary["referee"]
            ),
            count=reward_summary["count"],
            items=[
                ReferralRewardItem(**item)
                for item in reward_summary.get(
                    "items"
                ) or []
            ],
            disclosures=reward_summary.get(
                "disclosures"
            ) or [],
            compliance=reward_summary["compliance"],
        ),
        missions=DashboardMissionGroups(
            core=missions.get("core", []),
            boost=missions.get("boost", []),
            milestone=missions.get("milestone", []),
        ),
    )
