from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.schemas.distribution.routing import (
    MatchOpportunityRequest,
    OfferRouteListResponse,
    OfferRouteResponse,
    OpportunityMatchListResponse,
    RouteOpportunityRequest,
    OpportunityRouteListResponse,
)
from services.admin_audit_service import try_write_admin_audit
from services.distribution.routing_service import (
    RouteNotFound,
    RoutingError,
    RoutingOpportunityNotFound,
    RoutingOpportunityNotRoutable,
    accept_route,
    decline_route,
    list_routes,
    match_distributors_for_opportunity,
    route_opportunity,
)
from utils.security import require_distribution_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/distribution/routing",
    tags=["Admin Distribution Routing"],
    dependencies=[Depends(require_admin_key)],
)


def _handle_routing_error(exc: Exception) -> HTTPException:
    if isinstance(exc, (RouteNotFound, RoutingOpportunityNotFound)):
        return HTTPException(status_code=404, detail=str(exc))

    if isinstance(exc, RoutingOpportunityNotRoutable):
        return HTTPException(status_code=409, detail=str(exc))

    if isinstance(exc, RoutingError):
        return HTTPException(status_code=400, detail=str(exc))

    return HTTPException(status_code=500, detail="Unexpected routing error")


@router.post(
    "/opportunities/{opportunity_id}/matches",
    response_model=OpportunityMatchListResponse,
)
async def match_opportunity(
    opportunity_id: str,
    request: MatchOpportunityRequest,
) -> dict:
    try:
        return await match_distributors_for_opportunity(
            opportunity_id=opportunity_id,
            minimum_score=request.minimum_score,
            limit=request.limit,
        )

    except Exception as exc:
        raise _handle_routing_error(exc) from exc


@router.post(
    "/opportunities/{opportunity_id}/routes",
    response_model=OpportunityRouteListResponse,
)
async def route_to_distributors(
    opportunity_id: str,
    request: RouteOpportunityRequest,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        result = await route_opportunity(
            opportunity_id=opportunity_id,
            minimum_score=request.minimum_score,
            limit=request.limit,
            expires_at=request.expires_at,
            metadata=request.metadata,
        )
        await try_write_admin_audit(
            action_type="DISTRIBUTION_OPPORTUNITY_ROUTE",
            action_domain="DISTRIBUTION",
            identity=identity,
            target_type="distribution_opportunity",
            target_id=opportunity_id,
            request_payload=request.model_dump(mode="json"),
            result_payload={
                "opportunity_id": opportunity_id,
                "route_count": len(result.get("routes", [])) if isinstance(result, dict) else None,
            },
        )
        return result

    except Exception as exc:
        raise _handle_routing_error(exc) from exc


@router.get("/routes", response_model=OfferRouteListResponse)
async def list_offer_routes(
    tenant_code: str = Query(...),
    opportunity_id: str | None = Query(default=None),
    distributor_id: str | None = Query(default=None),
    route_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    return await list_routes(
        tenant_code=tenant_code,
        opportunity_id=opportunity_id,
        distributor_id=distributor_id,
        route_status=route_status,
        limit=limit,
    )


@router.post("/routes/{route_id}/accept", response_model=OfferRouteResponse)
async def accept_offer_route(
    route_id: str,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        route = await accept_route(route_id=route_id)
        await _audit_route_decision(
            action_type="DISTRIBUTION_ROUTE_ACCEPT",
            identity=identity,
            route_id=route_id,
            route=route,
        )
        return route

    except Exception as exc:
        raise _handle_routing_error(exc) from exc


@router.post("/routes/{route_id}/decline", response_model=OfferRouteResponse)
async def decline_offer_route(
    route_id: str,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        route = await decline_route(route_id=route_id)
        await _audit_route_decision(
            action_type="DISTRIBUTION_ROUTE_DECLINE",
            identity=identity,
            route_id=route_id,
            route=route,
        )
        return route

    except Exception as exc:
        raise _handle_routing_error(exc) from exc


async def _audit_route_decision(
    *,
    action_type: str,
    identity: dict,
    route_id: str,
    route: dict,
) -> None:
    await try_write_admin_audit(
        action_type=action_type,
        action_domain="DISTRIBUTION",
        identity=identity,
        tenant_code=route.get("tenant_code"),
        target_type="distribution_offer_route",
        target_id=route_id,
        result_payload={
            "route_id": route.get("route_id"),
            "opportunity_id": route.get("opportunity_id"),
            "distributor_id": route.get("distributor_id"),
            "route_status": route.get("route_status"),
        },
    )
