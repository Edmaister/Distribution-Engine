from __future__ import annotations

import datetime
from typing import Any, Dict, List, Union

from fastapi import APIRouter, Depends, HTTPException, Query

from utils.security import require_admin_or_partner_key

from apps.api.schemas.missions import (
    GroupedMissionListResponse,
    MissionComplianceMetadata,
    MissionItemResponse,
    MissionListResponse,
    ReferrerMissionListResponse,
)

from services.mission_service import (
    get_missions_for_referral,
    get_missions_for_referrer,
)

router = APIRouter(
    prefix="/v1/missions",
    tags=["missions"],
    dependencies=[Depends(require_admin_or_partner_key)],
)


def _to_item_response(item: Dict[str, Any]) -> MissionItemResponse:
    progress_count = int(item["progressCount"])
    goal_count = int(item["goalCount"])
    bonus_reward_amount = int(item["bonusRewardAmount"])

    return MissionItemResponse(
        missionCode=item["missionCode"],
        category=item.get("category", "CORE"),
        scope=item.get("scope", "REFERRAL"),
        displayOrder=int(item.get("displayOrder", 999)),
        beneficiaryType=item["beneficiaryType"],
        beneficiaryRef=item["beneficiaryRef"],
        title=item["title"],
        body=item["body"],
        progressCount=progress_count,
        goalCount=goal_count,
        progressLabel=item.get(
            "progressLabel",
            f"{progress_count} / {goal_count}",
        ),
        status=item.get("status", "IN_PROGRESS"),
        isComplete=bool(item["isComplete"]),
        completedAt=item.get("completedAt"),
        bonusRewardAmount=bonus_reward_amount,
        rewardLabel=item.get(
            "rewardLabel",
            f"+R{bonus_reward_amount}",
        ),
        currency=item.get("currency", "ZAR"),
        associatedReferralTrackIds=item.get(
            "associatedReferralTrackIds",
            [],
        ),
        disclosures=item.get("disclosures", []),
        compliance=MissionComplianceMetadata(
            **item["compliance"]
        ),
    )


def _build_grouped(
    items: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, List[MissionItemResponse]]:

    return {
        "core": [
            _to_item_response(i)
            for i in items.get("core", [])
        ],
        "boost": [
            _to_item_response(i)
            for i in items.get("boost", [])
        ],
        "milestone": [
            _to_item_response(i)
            for i in items.get("milestone", [])
        ],
    }


# ------------------------------------------------
# REFERRAL MISSIONS
# ------------------------------------------------

@router.get(
    "/{referral_track_id}",
    response_model=Union[
        MissionListResponse,
        GroupedMissionListResponse,
    ],
)
async def get_missions_by_referral(
    referral_track_id: str,
    audit: bool = Query(True),
    grouped: bool = Query(False),
    identity=Depends(require_admin_or_partner_key),
):
    tenant_code = identity.get("tenant_code")

    items = await get_missions_for_referral(
        referral_track_id=referral_track_id,
        tenant_code=tenant_code,
        channel="API",
        audit=audit,
        grouped=grouped,
    )

    if not items:
        raise HTTPException(
            status_code=404,
            detail="Referral not found",
        )

    if grouped:
        grouped_items = _build_grouped(items)

        return GroupedMissionListResponse(
            generatedAt=datetime.datetime.now(
                datetime.timezone.utc
            ),
            totalCount=sum(
                len(v)
                for v in grouped_items.values()
            ),
            **grouped_items,
        )

    flat_items = [
        _to_item_response(item)
        for item in items
    ]

    return MissionListResponse(
        referralTrackId=referral_track_id,
        generatedAt=datetime.datetime.now(
            datetime.timezone.utc
        ),
        count=len(flat_items),
        items=flat_items,
    )


# ------------------------------------------------
# REFERRER MISSIONS
# ------------------------------------------------

@router.get(
    "/referrer/{referrer_ucn}",
    response_model=ReferrerMissionListResponse,
)
async def get_missions_by_referrer(
    referrer_ucn: str,
    audit: bool = Query(True),
    identity=Depends(require_admin_or_partner_key),
):
    tenant_code = identity.get("tenant_code")

    items = await get_missions_for_referrer(
        referrer_ucn=referrer_ucn,
        tenant_code=tenant_code,
        channel="API",
        audit=audit,
        grouped=True,
    )

    grouped_items = _build_grouped(items)

    return ReferrerMissionListResponse(
        referrerUCN=referrer_ucn,
        generatedAt=datetime.datetime.now(
            datetime.timezone.utc
        ),
        totalCount=sum(
            len(v)
            for v in grouped_items.values()
        ),
        **grouped_items,
    )