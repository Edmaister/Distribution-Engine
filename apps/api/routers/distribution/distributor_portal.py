from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.schemas.distribution.distributor_portal import (
    DistributorPortalOfferListResponse,
    DistributorPortalOfferResponse,
    DistributorPortalConversionListResponse,
    DistributorPortalPerformanceResponse,
    DistributorPortalProfileResponse,
    DistributorPortalRouteResponse,
    DistributorPortalRouteReferralLinkResponse,
    DistributorPortalWalletLedgerResponse,
    DistributorPortalWalletListResponse,
    LinkDistributorPortalReferralRequest,
)
from services.distribution.distributor_portal_service import (
    DistributorPortalError,
    DistributorPortalNotFound,
    accept_portal_offer,
    decline_portal_offer,
    get_portal_distributor,
    get_portal_performance,
    link_portal_referral_to_route,
    list_portal_conversions,
    list_portal_offers,
    list_portal_wallet_ledger,
    list_portal_wallets,
)
from services.distribution.routing_service import RouteNotFound, RoutingError
from services.insurance_journey_proof_service import (
    get_distributor_insurance_journey_proof,
)
from services.outcome_money_reconciliation_service import (
    get_distributor_outcome_money_review,
)
from services.channel_readiness_service import get_channel_readiness, recommend_channels
from utils.security import require_admin_partner_or_distributor_key
from utils.permissions import require_distributor_scope


router = APIRouter(
    prefix="/distribution/portal",
    tags=["Distribution Portal"],
    dependencies=[Depends(require_admin_partner_or_distributor_key)],
)


def _handle_portal_error(exc: Exception) -> HTTPException:
    if isinstance(exc, (DistributorPortalNotFound, RouteNotFound)):
        return HTTPException(status_code=404, detail=str(exc))

    if isinstance(exc, (DistributorPortalError, RoutingError)):
        return HTTPException(status_code=400, detail=str(exc))

    return HTTPException(status_code=500, detail="Unexpected distributor portal error")


def _enforce_distributor_access(
    identity: dict,
    tenant_code: str,
    distributor_code: str,
) -> None:
    require_distributor_scope(
        identity,
        tenant_code=tenant_code,
        distributor_code=distributor_code,
    )


@router.get("/profile", response_model=DistributorPortalProfileResponse)
async def get_profile(
    tenant_code: str = Query(...),
    distributor_code: str = Query(...),
    identity: dict = Depends(require_admin_partner_or_distributor_key),
) -> dict:
    _enforce_distributor_access(identity, tenant_code, distributor_code)
    try:
        return await get_portal_distributor(
            tenant_code=tenant_code,
            distributor_code=distributor_code,
        )

    except Exception as exc:
        raise _handle_portal_error(exc) from exc


@router.get("/offers", response_model=DistributorPortalOfferListResponse)
async def list_offers(
    tenant_code: str = Query(...),
    distributor_code: str = Query(...),
    route_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    identity: dict = Depends(require_admin_partner_or_distributor_key),
) -> dict:
    _enforce_distributor_access(identity, tenant_code, distributor_code)
    try:
        return await list_portal_offers(
            tenant_code=tenant_code,
            distributor_code=distributor_code,
            route_status=route_status,
            limit=limit,
        )

    except Exception as exc:
        raise _handle_portal_error(exc) from exc


@router.post("/offers/{route_id}/accept", response_model=DistributorPortalRouteResponse)
async def accept_offer(
    route_id: str,
    tenant_code: str = Query(...),
    distributor_code: str = Query(...),
    identity: dict = Depends(require_admin_partner_or_distributor_key),
) -> dict:
    _enforce_distributor_access(identity, tenant_code, distributor_code)
    try:
        return await accept_portal_offer(
            tenant_code=tenant_code,
            distributor_code=distributor_code,
            route_id=route_id,
        )

    except Exception as exc:
        raise _handle_portal_error(exc) from exc


@router.post(
    "/offers/{route_id}/decline", response_model=DistributorPortalRouteResponse
)
async def decline_offer(
    route_id: str,
    tenant_code: str = Query(...),
    distributor_code: str = Query(...),
    identity: dict = Depends(require_admin_partner_or_distributor_key),
) -> dict:
    _enforce_distributor_access(identity, tenant_code, distributor_code)
    try:
        return await decline_portal_offer(
            tenant_code=tenant_code,
            distributor_code=distributor_code,
            route_id=route_id,
        )

    except Exception as exc:
        raise _handle_portal_error(exc) from exc


@router.post(
    "/offers/{route_id}/referrals",
    response_model=DistributorPortalRouteReferralLinkResponse,
)
async def link_offer_referral(
    route_id: str,
    request: LinkDistributorPortalReferralRequest,
    tenant_code: str = Query(...),
    distributor_code: str = Query(...),
    identity: dict = Depends(require_admin_partner_or_distributor_key),
) -> dict:
    _enforce_distributor_access(identity, tenant_code, distributor_code)
    try:
        return await link_portal_referral_to_route(
            tenant_code=tenant_code,
            distributor_code=distributor_code,
            route_id=route_id,
            referral_track_id=request.referral_track_id,
            metadata=request.metadata,
        )

    except Exception as exc:
        raise _handle_portal_error(exc) from exc


@router.get("/wallets", response_model=DistributorPortalWalletListResponse)
async def list_wallets(
    tenant_code: str = Query(...),
    distributor_code: str = Query(...),
    limit: int = Query(default=100, ge=1, le=500),
    identity: dict = Depends(require_admin_partner_or_distributor_key),
) -> dict:
    _enforce_distributor_access(identity, tenant_code, distributor_code)
    try:
        return await list_portal_wallets(
            tenant_code=tenant_code,
            distributor_code=distributor_code,
            limit=limit,
        )

    except Exception as exc:
        raise _handle_portal_error(exc) from exc


@router.get(
    "/wallets/{wallet_id}/ledger",
    response_model=DistributorPortalWalletLedgerResponse,
)
async def list_wallet_ledger(
    wallet_id: str,
    tenant_code: str = Query(...),
    distributor_code: str = Query(...),
    limit: int = Query(default=100, ge=1, le=500),
    identity: dict = Depends(require_admin_partner_or_distributor_key),
) -> dict:
    _enforce_distributor_access(identity, tenant_code, distributor_code)
    try:
        return await list_portal_wallet_ledger(
            tenant_code=tenant_code,
            distributor_code=distributor_code,
            wallet_id=wallet_id,
            limit=limit,
        )

    except Exception as exc:
        raise _handle_portal_error(exc) from exc


@router.get("/conversions", response_model=DistributorPortalConversionListResponse)
async def list_conversions(
    tenant_code: str = Query(...),
    distributor_code: str = Query(...),
    limit: int = Query(default=100, ge=1, le=500),
    identity: dict = Depends(require_admin_partner_or_distributor_key),
) -> dict:
    _enforce_distributor_access(identity, tenant_code, distributor_code)
    try:
        return await list_portal_conversions(
            tenant_code=tenant_code,
            distributor_code=distributor_code,
            limit=limit,
        )

    except Exception as exc:
        raise _handle_portal_error(exc) from exc


@router.get("/outcome-money-review")
async def get_outcome_money_review(
    tenant_code: str = Query(...),
    distributor_code: str = Query(...),
    limit: int = Query(default=100, ge=1, le=250),
    identity: dict = Depends(require_admin_partner_or_distributor_key),
) -> dict:
    _enforce_distributor_access(identity, tenant_code, distributor_code)
    review = await get_distributor_outcome_money_review(
        tenant_code=tenant_code,
        distributor_code=distributor_code,
        limit=limit,
    )
    return {
        "status": "ok",
        "review": review,
    }


@router.get("/channel-recommendations")
async def get_channel_recommendations(
    tenant_code: str = Query(...),
    distributor_code: str = Query(...),
    event_type: str = Query(default="ROUTE_ASSIGNED"),
    audience: str = Query(default="DISTRIBUTOR"),
    distributor_channels: list[str] | None = Query(default=None),
    identity: dict = Depends(require_admin_partner_or_distributor_key),
) -> dict:
    _enforce_distributor_access(identity, tenant_code, distributor_code)
    return {
        "status": "ok",
        "recommendations": recommend_channels(
            event_type=event_type,
            audience=audience,
            distributor_channels=distributor_channels,
        ),
    }


@router.get("/channel-readiness")
async def get_channel_readiness_view(
    tenant_code: str = Query(...),
    distributor_code: str = Query(...),
    identity: dict = Depends(require_admin_partner_or_distributor_key),
) -> dict:
    _enforce_distributor_access(identity, tenant_code, distributor_code)
    return {
        "status": "ok",
        "surface": "Distributor - Demand",
        "tenant_code": tenant_code.strip().upper(),
        "distributor_code": distributor_code.strip().upper(),
        "readiness": get_channel_readiness(),
    }


@router.get("/proof/insurance")
async def get_insurance_proof(
    tenant_code: str = Query(...),
    distributor_code: str = Query(...),
    identity: dict = Depends(require_admin_partner_or_distributor_key),
) -> dict:
    _enforce_distributor_access(identity, tenant_code, distributor_code)
    return await get_distributor_insurance_journey_proof(
        tenant_code=tenant_code.strip().upper(),
        distributor_code=distributor_code.strip().upper(),
    )


@router.get("/performance", response_model=DistributorPortalPerformanceResponse)
async def get_performance(
    tenant_code: str = Query(...),
    distributor_code: str = Query(...),
    identity: dict = Depends(require_admin_partner_or_distributor_key),
) -> dict:
    _enforce_distributor_access(identity, tenant_code, distributor_code)
    try:
        return await get_portal_performance(
            tenant_code=tenant_code,
            distributor_code=distributor_code,
        )

    except Exception as exc:
        raise _handle_portal_error(exc) from exc
