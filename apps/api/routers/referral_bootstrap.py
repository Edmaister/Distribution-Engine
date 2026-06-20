import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from utils.security import require_partner_key
from apps.api.schemas.referral_bootstrap import (
    ReferralBootstrapRequest,
    ReferralBootstrapResponse,
    AcceptTermsRequest,
    AcceptTermsResponse,
)
from services.referral_bootstrap_service import (
    ReferralBootstrapError,
    bootstrap_referrer_profile,
    accept_terms,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/referrals",
    tags=["Referrals"],
    dependencies=[Depends(require_partner_key)],
)


@router.post(
    "/bootstrap",
    response_model=ReferralBootstrapResponse,
)
async def bootstrap_referrer(
    payload: ReferralBootstrapRequest,
    request: Request,
    identity=Depends(require_partner_key),
):
    try:
        tenant_code = identity["tenant_code"]

        return await bootstrap_referrer_profile(
            referrer_ucn=payload.referrerUcn,
            tenant_code=tenant_code,
        )

    except ReferralBootstrapError as exc:
        logger.warning(
            "Bootstrap validation failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=400,
            detail="Invalid request",
        )

    except Exception:
        correlation_id = getattr(
            request.state,
            "correlation_id",
            "unknown",
        )

        logger.exception(
            (
                "Bootstrap failed | "
                "correlation_id=%s | "
                "referrer_ucn=%s | "
                "tenant_code=%s"
            ),
            correlation_id,
            payload.referrerUcn,
            tenant_code,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "correlation_id": correlation_id,
            },
        )


@router.post(
    "/accept-terms",
    response_model=AcceptTermsResponse,
)
async def accept_referral_terms(
    payload: AcceptTermsRequest,
    request: Request,
    identity=Depends(require_partner_key),
):
    try:
        tenant_code = identity["tenant_code"]

        return await accept_terms(
            referrer_ucn=payload.referrerUcn,
            tenant_code=tenant_code,
        )

    except ReferralBootstrapError as exc:
        logger.warning(
            "Accept terms validation failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=404,
            detail="Not found",
        )

    except Exception:
        correlation_id = getattr(
            request.state,
            "correlation_id",
            "unknown",
        )

        logger.exception(
            (
                "Accept terms failed | "
                "correlation_id=%s | "
                "referrer_ucn=%s | "
                "tenant_code=%s"
            ),
            correlation_id,
            payload.referrerUcn,
            tenant_code,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "correlation_id": correlation_id,
            },
        )