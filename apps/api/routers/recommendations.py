from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from utils.security import require_admin_or_partner_key

from apps.api.schemas.recommendations import (
    ComplianceMetadata,
    RecommendationItemResponse,
    RecommendationListResponse,
    RewardPreview,
)
from services.recommendation_compliance_service import (
    generate_recommendations_for_referral,
)

router = APIRouter(
    prefix="/v1/recommendations",
    tags=["recommendations"],
    dependencies=[Depends(require_admin_or_partner_key)]
)


def _to_item_response(item: dict) -> RecommendationItemResponse:
    reward_preview = item.get("rewardPreview")
    compliance = item.get("compliance") or {}

    return RecommendationItemResponse(
        recommendationId=item["recommendationId"],
        category=item["category"],
        title=item["title"],
        body=item["body"],
        ctaLabel=item["ctaLabel"],
        ctaAction=item["ctaAction"],
        priority=item["priority"],
        rewardPreview=RewardPreview(**reward_preview) if reward_preview else None,
        disclosures=item.get("disclosures", []),
        compliance=ComplianceMetadata(**compliance),
        templateCode=item["templateCode"],
        templateVersion=item["templateVersion"],
        policyVersion=item["policyVersion"],
    )


@router.get("/{referral_track_id}", response_model=RecommendationListResponse)
def get_recommendations(
    referral_track_id: str,
    audit: bool = Query(True, description="Whether recommendation display should be audited"),
    identity=Depends(require_admin_or_partner_key),
) -> RecommendationListResponse:
    tenant_code = identity.get("tenant_code")

    items = generate_recommendations_for_referral(
        referral_track_id=referral_track_id,
        tenant_code=tenant_code,
        channel="API",
        audit=audit,
    )

    if not items:
        raise HTTPException(status_code=404, detail="Referral not found or no recommendations available")

    return RecommendationListResponse(
        referralTrackId=referral_track_id,
        generatedAt=datetime.datetime.now(datetime.timezone.utc),
        count=len(items),
        items=[_to_item_response(item) for item in items],
    )