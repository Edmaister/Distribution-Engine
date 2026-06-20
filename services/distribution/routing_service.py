from __future__ import annotations

import json
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from services.distribution.opportunity_service import OPPORTUNITY_STATUS_PUBLISHED
from utils.db import db_connection


ROUTE_STATUS_ROUTED = "ROUTED"
ROUTE_STATUS_ACCEPTED = "ACCEPTED"
ROUTE_STATUS_DECLINED = "DECLINED"


class RoutingError(Exception):
    pass


class RoutingOpportunityNotFound(RoutingError):
    pass


class RoutingOpportunityNotRoutable(RoutingError):
    pass


class RouteNotFound(RoutingError):
    pass


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {})


def _serialize(row: Any) -> dict[str, Any]:
    result = {
        key: str(value) if isinstance(value, UUID) else value
        for key, value in dict(row).items()
    }

    for key in ("route_reasons", "metadata"):
        if isinstance(result.get(key), str):
            result[key] = json.loads(result[key])

    return result


def _as_set(value: list[str] | tuple[str, ...] | None) -> set[str]:
    return {item for item in value or [] if item}


def _score_dimension(
    *,
    required: set[str],
    available: set[str],
    weight: int,
    label: str,
) -> tuple[int, bool, str]:
    if not required:
        return weight, True, f"{label}: wildcard"

    matched = sorted(required.intersection(available))
    if matched:
        return weight, True, f"{label}: matched {', '.join(matched)}"

    return 0, False, f"{label}: no match"


def score_distributor_for_opportunity(
    *,
    opportunity: dict[str, Any],
    distributor: dict[str, Any],
) -> dict[str, Any]:
    score = 0
    eligible = True
    reasons = []

    type_required = _as_set(opportunity.get("distributor_types"))
    type_available = {distributor.get("distributor_type")}
    type_score, type_ok, type_reason = _score_dimension(
        required=type_required,
        available=type_available,
        weight=30,
        label="distributor_type",
    )
    score += type_score
    eligible = eligible and type_ok
    reasons.append(type_reason)

    segment_score, segment_ok, segment_reason = _score_dimension(
        required=_as_set(opportunity.get("target_segments")),
        available=_as_set(distributor.get("segments")),
        weight=25,
        label="segment",
    )
    score += segment_score
    eligible = eligible and segment_ok
    reasons.append(segment_reason)

    region_score, region_ok, region_reason = _score_dimension(
        required=_as_set(opportunity.get("target_regions")),
        available=_as_set(distributor.get("regions")),
        weight=25,
        label="region",
    )
    score += region_score
    eligible = eligible and region_ok
    reasons.append(region_reason)

    channel_score, channel_ok, channel_reason = _score_dimension(
        required=_as_set(opportunity.get("target_channels")),
        available=_as_set(distributor.get("channels")),
        weight=20,
        label="channel",
    )
    score += channel_score
    eligible = eligible and channel_ok
    reasons.append(channel_reason)

    return {
        "eligible": eligible,
        "route_score": Decimal(score),
        "route_reasons": reasons,
    }


async def _get_routable_opportunity(opportunity_id: str) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM distribution_opportunities
            WHERE opportunity_id = $1
            """,
            opportunity_id,
        )

    if not row:
        raise RoutingOpportunityNotFound("Opportunity not found")

    opportunity = dict(row)
    if opportunity["opportunity_status"] != OPPORTUNITY_STATUS_PUBLISHED:
        raise RoutingOpportunityNotRoutable("Opportunity must be published before routing")

    return opportunity


async def match_distributors_for_opportunity(
    *,
    opportunity_id: str,
    minimum_score: Decimal | int | float | str = 1,
    limit: int = 25,
) -> dict[str, Any]:
    opportunity = await _get_routable_opportunity(opportunity_id)
    resolved_minimum_score = Decimal(str(minimum_score))

    async with db_connection() as conn:
        distributors = await conn.fetch(
            """
            SELECT *
            FROM distribution_distributors
            WHERE tenant_code = $1
              AND status = 'ACTIVE'
            ORDER BY created_at DESC
            """,
            opportunity["tenant_code"],
        )

    matches = []
    for row in distributors:
        distributor = dict(row)
        score = score_distributor_for_opportunity(
            opportunity=opportunity,
            distributor=distributor,
        )

        if score["eligible"] and score["route_score"] >= resolved_minimum_score:
            matches.append(
                {
                    "opportunity_id": str(opportunity["opportunity_id"]),
                    "distributor_id": str(distributor["distributor_id"]),
                    "distributor_code": distributor["distributor_code"],
                    "distributor_name": distributor["distributor_name"],
                    "distributor_type": distributor["distributor_type"],
                    "route_score": score["route_score"],
                    "route_reasons": score["route_reasons"],
                }
            )

    matches.sort(
        key=lambda item: (
            item["route_score"],
            item["distributor_code"],
        ),
        reverse=True,
    )

    return {
        "opportunity_id": str(opportunity["opportunity_id"]),
        "tenant_code": opportunity["tenant_code"],
        "count": len(matches[:limit]),
        "items": matches[:limit],
    }


async def route_opportunity(
    *,
    opportunity_id: str,
    minimum_score: Decimal | int | float | str = 1,
    limit: int = 25,
    expires_at: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    matched = await match_distributors_for_opportunity(
        opportunity_id=opportunity_id,
        minimum_score=minimum_score,
        limit=limit,
    )

    routes = []
    async with db_connection() as conn:
        for item in matched["items"]:
            row = await conn.fetchrow(
                """
                INSERT INTO distribution_offer_routes (
                    route_id,
                    tenant_code,
                    opportunity_id,
                    distributor_id,
                    route_status,
                    route_score,
                    route_reasons,
                    expires_at,
                    metadata
                )
                VALUES (
                    $1, $2, $3, $4, 'ROUTED', $5, $6::jsonb, $7::timestamp, $8::jsonb
                )
                ON CONFLICT (opportunity_id, distributor_id)
                DO UPDATE SET
                    route_status = 'ROUTED',
                    route_score = EXCLUDED.route_score,
                    route_reasons = EXCLUDED.route_reasons,
                    expires_at = EXCLUDED.expires_at,
                    metadata = EXCLUDED.metadata,
                    routed_at = NOW(),
                    accepted_at = NULL,
                    declined_at = NULL,
                    updated_at = NOW()
                RETURNING *
                """,
                uuid4(),
                matched["tenant_code"],
                opportunity_id,
                item["distributor_id"],
                item["route_score"],
                _json(item["route_reasons"]),
                expires_at,
                _json(metadata),
            )
            routes.append(_serialize(row))

    return {
        "opportunity_id": opportunity_id,
        "tenant_code": matched["tenant_code"],
        "count": len(routes),
        "items": routes,
    }


async def list_routes(
    *,
    tenant_code: str,
    opportunity_id: str | None = None,
    distributor_id: str | None = None,
    route_status: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM distribution_offer_routes
            WHERE tenant_code = $1
              AND ($2::uuid IS NULL OR opportunity_id = $2::uuid)
              AND ($3::uuid IS NULL OR distributor_id = $3::uuid)
              AND ($4::text IS NULL OR route_status = $4)
            ORDER BY routed_at DESC
            LIMIT $5
            """,
            tenant_code,
            opportunity_id,
            distributor_id,
            route_status,
            limit,
        )

    items = [_serialize(row) for row in rows]
    return {
        "tenant_code": tenant_code,
        "count": len(items),
        "items": items,
    }


async def accept_route(*, route_id: str) -> dict[str, Any]:
    return await _set_route_status(route_id=route_id, route_status=ROUTE_STATUS_ACCEPTED)


async def decline_route(*, route_id: str) -> dict[str, Any]:
    return await _set_route_status(route_id=route_id, route_status=ROUTE_STATUS_DECLINED)


async def _set_route_status(*, route_id: str, route_status: str) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE distribution_offer_routes
            SET
                route_status = $2,
                accepted_at = CASE WHEN $2 = 'ACCEPTED' THEN NOW() ELSE accepted_at END,
                declined_at = CASE WHEN $2 = 'DECLINED' THEN NOW() ELSE declined_at END,
                updated_at = NOW()
            WHERE route_id = $1
            RETURNING *
            """,
            route_id,
            route_status,
        )

    if not row:
        raise RouteNotFound("Route not found")

    return _serialize(row)
