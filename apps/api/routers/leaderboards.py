from __future__ import annotations

import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.schemas.leaderboard import (
    LeaderboardEntryResponse,
    LeaderboardListResponse,
    MyLeaderboardEntryResponse,
)
from services.leaderboard_service import (
    get_leaderboard,
    get_leaderboard_count,
    get_leaderboard_definition,
    get_next_rank_info,
    get_referrer_leaderboard_entry,
)
from utils.security import require_admin_or_partner_key


router = APIRouter(
    prefix="/v1/tenants/{tenant_code}/leaderboards",
    tags=["leaderboards"],
)


def _enforce_tenant_access(identity: dict[str, Any], tenant_code: str) -> None:
    role = str(identity.get("role", "")).upper()
    key_tenant = str(identity.get("tenant_code", "")).upper()
    request_tenant = tenant_code.upper()

    if role == "ADMIN":
        return

    if role not in {"PARTNER", "TENANT_ADMIN"}:
        raise HTTPException(
            status_code=403,
            detail="API key is not authorised for this tenant",
        )

    if not key_tenant or key_tenant != request_tenant:
        raise HTTPException(
            status_code=403,
            detail="API key is not authorised for this tenant",
        )


def _to_leaderboard_entry_response(item: dict) -> LeaderboardEntryResponse:
    return LeaderboardEntryResponse(
        leaderboardCode=item["leaderboard_code"],
        displayName=item["display_name"],
        totalScore=item["total_score"],
        referralScore=item["referral_score"],
        milestoneScore=item["milestone_score"],
        bonusScore=item["bonus_score"],
        referralsCount=item["referrals_count"],
        completedReferralsCount=item["completed_referrals_count"],
        lastEventAt=item.get("last_event_at"),
        rankPosition=item.get("rank_position"),
        rankedTier=item["rank_tier"],
    )


def _to_my_leaderboard_entry_response(
    item: dict,
    next_info: dict | None = None,
) -> MyLeaderboardEntryResponse:
    payload = {
        "leaderboardCode": item["leaderboard_code"],
        "displayName": item["display_name"],
        "totalScore": item["total_score"],
        "referralScore": item["referral_score"],
        "milestoneScore": item["milestone_score"],
        "bonusScore": item["bonus_score"],
        "referralsCount": item["referrals_count"],
        "completedReferralsCount": item["completed_referrals_count"],
        "lastEventAt": item.get("last_event_at"),
        "rankPosition": item.get("rank_position"),
        "rankedTier": item["rank_tier"],
    }

    if next_info:
        payload["nextRankPosition"] = next_info.get("next_rank_position")
        payload["nextRankScore"] = next_info.get("next_rank_score")
        payload["pointsToNextRank"] = next_info.get("points_to_next_rank")

    return MyLeaderboardEntryResponse(**payload)


@router.get("/{leaderboard_code}", response_model=LeaderboardListResponse)
async def read_leaderboard(
    tenant_code: str,
    leaderboard_code: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> LeaderboardListResponse:
    _enforce_tenant_access(identity, tenant_code)

    leaderboard = await get_leaderboard_definition(
        leaderboard_code=leaderboard_code,
        tenant_code=tenant_code,
    )

    if not leaderboard:
        raise HTTPException(
            status_code=404,
            detail="Leaderboard not found",
        )

    items = await get_leaderboard(
        leaderboard_code=leaderboard_code,
        tenant_code=tenant_code,
        limit=limit,
        offset=offset,
    )

    total_count = await get_leaderboard_count(
        leaderboard_code=leaderboard_code,
        tenant_code=tenant_code,
    )

    return LeaderboardListResponse(
        leaderboardCode=leaderboard_code,
        count=len(items),
        totalCount=total_count,
        offset=offset,
        limit=limit,
        generatedAt=datetime.datetime.now(datetime.timezone.utc),
        items=[_to_leaderboard_entry_response(item) for item in items],
    )


@router.get("/{leaderboard_code}/me", response_model=MyLeaderboardEntryResponse)
async def read_my_leaderboard_position(
    tenant_code: str,
    leaderboard_code: str,
    referrer_ucn: str = Query(..., min_length=1),
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> MyLeaderboardEntryResponse:
    _enforce_tenant_access(identity, tenant_code)

    leaderboard = await get_leaderboard_definition(
        leaderboard_code=leaderboard_code,
        tenant_code=tenant_code,
    )

    if not leaderboard:
        raise HTTPException(
            status_code=404,
            detail="Leaderboard not found",
        )

    item = await get_referrer_leaderboard_entry(
        leaderboard_code=leaderboard_code,
        referrer_ucn=referrer_ucn,
        tenant_code=tenant_code,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Leaderboard entry not found",
        )

    next_info = await get_next_rank_info(
        leaderboard_code=leaderboard_code,
        referrer_ucn=referrer_ucn,
        tenant_code=tenant_code,
    )

    return _to_my_leaderboard_entry_response(item, next_info)