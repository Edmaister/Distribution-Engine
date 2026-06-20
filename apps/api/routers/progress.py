from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Response

from apps.api.schemas.progress import (
    ProgressPostRequest,
    ProgressPostResponse,
    ReferrerReferralProgressResponse,
)
from services.progress_service import (
    get_referrals_progress_by_referrer_ucn,
    handle_progress_event,
)
from utils.security import require_admin_or_partner_key, require_partner_key

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1",
    tags=["Progress"],
)


@router.post("/progress", response_model=ProgressPostResponse)
async def post_progress(
    req: ProgressPostRequest,
    response: Response,
    identity=Depends(require_partner_key),
):
    # 🔒 derive tenant from key
    tenant_code = identity["tenant_code"]

    # pass tenant into service (must be supported there)
    body, code = await handle_progress_event(req, tenant_code=tenant_code)

    response.status_code = code
    return body


@router.get(
    "/referrers/{referrerUcn}",
    response_model=ReferrerReferralProgressResponse,
    summary="Get all referral progress records for a referrer",
    description="Returns a UI-safe progress summary for all referrals linked to the supplied referrer UCN.",
)
async def get_referrer_referrals_progress(
    referrerUcn: str = Path(..., description="Referrer UCN used to look up linked referrals"),
    identity=Depends(require_admin_or_partner_key),
):
    try:
        tenant_code = identity.get("tenant_code")

        return await get_referrals_progress_by_referrer_ucn(
            referrer_ucn=referrerUcn,
            tenant_code=tenant_code,
        )

    except Exception:
        logger.exception(
            "Failed to fetch referral progress | referrer_ucn=%s",
            referrerUcn,
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        )
