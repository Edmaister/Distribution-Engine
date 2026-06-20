from __future__ import annotations

import json
from decimal import Decimal
from typing import Any
from uuid import UUID

from services.distribution.routing_service import (
    ROUTE_STATUS_ACCEPTED,
    ROUTE_STATUS_DECLINED,
    ROUTE_STATUS_ROUTED,
    RouteNotFound,
)
from utils.db import db_connection


class DistributorPortalError(Exception):
    pass


class DistributorPortalNotFound(DistributorPortalError):
    pass


class DistributorPortalInvalidState(DistributorPortalError):
    pass


def _serialize(row: Any) -> dict[str, Any]:
    result = {
        key: str(value) if isinstance(value, UUID) else value
        for key, value in dict(row).items()
    }

    for key in (
        "route_reasons",
        "capabilities",
        "eligibility",
        "operating_limits",
        "metadata",
    ):
        if isinstance(result.get(key), str):
            result[key] = json.loads(result[key])

    return result


async def get_portal_distributor(
    *,
    tenant_code: str,
    distributor_code: str,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM distribution_distributors
            WHERE tenant_code = $1
              AND distributor_code = $2
            """,
            tenant_code,
            distributor_code,
        )

    if not row:
        raise DistributorPortalNotFound("Distributor not found")

    return _serialize(row)


async def list_portal_offers(
    *,
    tenant_code: str,
    distributor_code: str,
    route_status: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    distributor = await get_portal_distributor(
        tenant_code=tenant_code,
        distributor_code=distributor_code,
    )

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                r.*,
                o.sponsor_code,
                o.campaign_code,
                o.opportunity_code,
                o.title,
                o.description,
                o.product_code,
                o.product_name,
                o.estimated_reward_amount,
                o.estimated_commission_amount,
                o.starts_at,
                o.ends_at,
                COALESCE(l.referral_link_count, 0) AS referral_link_count,
                l.latest_referral_track_id,
                COALESCE(l.referral_link_count, 0) > 0 AS has_referral_link
            FROM distribution_offer_routes r
            JOIN distribution_opportunities o
              ON o.opportunity_id = r.opportunity_id
            LEFT JOIN (
                SELECT
                    route_id,
                    COUNT(*) AS referral_link_count,
                    (ARRAY_AGG(referral_track_id ORDER BY updated_at DESC, created_at DESC))[1]
                        AS latest_referral_track_id
                FROM distribution_route_referral_links
                WHERE link_status = 'ACTIVE'
                GROUP BY route_id
            ) l ON l.route_id = r.route_id
            WHERE r.tenant_code = $1
              AND r.distributor_id = $2
              AND ($3::text IS NULL OR r.route_status = $3)
            ORDER BY r.routed_at DESC
            LIMIT $4
            """,
            tenant_code,
            distributor["distributor_id"],
            route_status,
            limit,
        )

    items = [_serialize(row) for row in rows]
    return {
        "tenant_code": tenant_code,
        "distributor_id": distributor["distributor_id"],
        "distributor_code": distributor_code,
        "count": len(items),
        "items": items,
    }


async def accept_portal_offer(
    *,
    tenant_code: str,
    distributor_code: str,
    route_id: str,
) -> dict[str, Any]:
    return await _set_portal_route_status(
        tenant_code=tenant_code,
        distributor_code=distributor_code,
        route_id=route_id,
        route_status=ROUTE_STATUS_ACCEPTED,
    )


async def decline_portal_offer(
    *,
    tenant_code: str,
    distributor_code: str,
    route_id: str,
) -> dict[str, Any]:
    return await _set_portal_route_status(
        tenant_code=tenant_code,
        distributor_code=distributor_code,
        route_id=route_id,
        route_status=ROUTE_STATUS_DECLINED,
    )


async def _set_portal_route_status(
    *,
    tenant_code: str,
    distributor_code: str,
    route_id: str,
    route_status: str,
) -> dict[str, Any]:
    distributor = await get_portal_distributor(
        tenant_code=tenant_code,
        distributor_code=distributor_code,
    )

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE distribution_offer_routes
            SET
                route_status = $4,
                accepted_at = CASE WHEN $4 = 'ACCEPTED' THEN NOW() ELSE accepted_at END,
                declined_at = CASE WHEN $4 = 'DECLINED' THEN NOW() ELSE declined_at END,
                updated_at = NOW()
            WHERE route_id = $1
              AND tenant_code = $2
              AND distributor_id = $3
              AND route_status = 'ROUTED'
            RETURNING *
            """,
            route_id,
            tenant_code,
            distributor["distributor_id"],
            route_status,
        )

    if not row:
        async with db_connection() as conn:
            existing = await conn.fetchrow(
                """
                SELECT route_status
                FROM distribution_offer_routes
                WHERE route_id = $1
                  AND tenant_code = $2
                  AND distributor_id = $3
                """,
                route_id,
                tenant_code,
                distributor["distributor_id"],
            )

        if existing:
            raise DistributorPortalError(
                f"Only {ROUTE_STATUS_ROUTED} offers can be accepted or declined"
            )
        raise RouteNotFound("Route not found")

    return _serialize(row)


async def list_portal_wallets(
    *,
    tenant_code: str,
    distributor_code: str,
    limit: int = 100,
) -> dict[str, Any]:
    distributor = await get_portal_distributor(
        tenant_code=tenant_code,
        distributor_code=distributor_code,
    )

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM distribution_distributor_wallets
            WHERE tenant_code = $1
              AND distributor_id = $2
            ORDER BY created_at DESC
            LIMIT $3
            """,
            tenant_code,
            distributor["distributor_id"],
            limit,
        )

    items = [_serialize(row) for row in rows]
    return {
        "tenant_code": tenant_code,
        "distributor_id": distributor["distributor_id"],
        "distributor_code": distributor_code,
        "count": len(items),
        "items": items,
    }


async def list_portal_wallet_ledger(
    *,
    tenant_code: str,
    distributor_code: str,
    wallet_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    distributor = await get_portal_distributor(
        tenant_code=tenant_code,
        distributor_code=distributor_code,
    )

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT l.*
            FROM distribution_distributor_wallet_ledger l
            JOIN distribution_distributor_wallets w
              ON w.wallet_id = l.wallet_id
            WHERE l.wallet_id = $1
              AND w.tenant_code = $2
              AND w.distributor_id = $3
            ORDER BY l.created_at DESC
            LIMIT $4
            """,
            wallet_id,
            tenant_code,
            distributor["distributor_id"],
            limit,
        )

    items = [_serialize(row) for row in rows]
    return {
        "tenant_code": tenant_code,
        "distributor_id": distributor["distributor_id"],
        "distributor_code": distributor_code,
        "wallet_id": wallet_id,
        "count": len(items),
        "items": items,
    }


async def list_portal_conversions(
    *,
    tenant_code: str,
    distributor_code: str,
    limit: int = 100,
) -> dict[str, Any]:
    distributor = await get_portal_distributor(
        tenant_code=tenant_code,
        distributor_code=distributor_code,
    )

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                ri.referral_track_id,
                ri.tenant_code,
                ri.referrer_ucn AS distributor_code,
                l.route_id,
                l.opportunity_id,
                o.opportunity_code,
                o.title AS opportunity_title,
                o.sponsor_code,
                o.campaign_code,
                ri.product,
                ri.sub_product,
                ri.status,
                ri.display_status,
                ri.progress_percent,
                ri.progress_band,
                ri.next_milestone,
                ri.is_complete,
                ri.completed_at,
                ri.validated_at,
                ri.ucn_captured_at,
                ri.account_opened_at,
                ri.account_activated_at,
                ri.funded_at,
                ri.debit_order_switched_at,
                ri.salary_switched_at,
                ri.first_transaction_completed_at,
                ri.created_at,
                ri.updated_at
            FROM referral_instances ri
            LEFT JOIN distribution_route_referral_links l
              ON l.referral_track_id = ri.referral_track_id
             AND l.link_status = 'ACTIVE'
            LEFT JOIN distribution_opportunities o
              ON o.opportunity_id = l.opportunity_id
            WHERE ri.tenant_code = $1
              AND ri.referrer_ucn = $2
            ORDER BY ri.updated_at DESC NULLS LAST,
                     ri.created_at DESC NULLS LAST,
                     ri.referral_track_id DESC
            LIMIT $3
            """,
            tenant_code,
            distributor_code,
            limit,
        )

    items = [_serialize(row) for row in rows]
    completed_count = sum(1 for item in items if item.get("is_complete"))
    attributed_count = sum(1 for item in items if item.get("route_id"))
    unlinked_count = len(items) - attributed_count
    completion_rate = (
        Decimal(completed_count) / Decimal(len(items)) if items else Decimal("0")
    ).quantize(Decimal("0.0001"))
    attribution_rate = (
        Decimal(attributed_count) / Decimal(len(items)) if items else Decimal("0")
    ).quantize(Decimal("0.0001"))
    return {
        "tenant_code": tenant_code,
        "distributor_id": distributor["distributor_id"],
        "distributor_code": distributor_code,
        "count": len(items),
        "completed_count": completed_count,
        "completion_rate": completion_rate,
        "attributed_count": attributed_count,
        "unlinked_count": unlinked_count,
        "attribution_rate": attribution_rate,
        "items": items,
    }


async def link_portal_referral_to_route(
    *,
    tenant_code: str,
    distributor_code: str,
    route_id: str,
    referral_track_id: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    distributor = await get_portal_distributor(
        tenant_code=tenant_code,
        distributor_code=distributor_code,
    )

    async with db_connection() as conn:
        route = await conn.fetchrow(
            """
            SELECT route_id, tenant_code, distributor_id, opportunity_id, route_status
            FROM distribution_offer_routes
            WHERE route_id = $1
              AND tenant_code = $2
              AND distributor_id = $3
            """,
            route_id,
            tenant_code,
            distributor["distributor_id"],
        )

        if not route:
            raise RouteNotFound("Route not found")

        if route["route_status"] != ROUTE_STATUS_ACCEPTED:
            raise DistributorPortalInvalidState(
                "Only accepted routes can be linked to customer conversions"
            )

        referral = await conn.fetchrow(
            """
            SELECT referral_track_id
            FROM referral_instances
            WHERE referral_track_id = $1
              AND tenant_code = $2
              AND referrer_ucn = $3
            """,
            referral_track_id,
            tenant_code,
            distributor_code,
        )

        if not referral:
            raise DistributorPortalNotFound("Referral track not found for distributor")

        existing_link = await conn.fetchrow(
            """
            SELECT route_id
            FROM distribution_route_referral_links
            WHERE referral_track_id = $1
              AND link_status = 'ACTIVE'
            """,
            referral_track_id,
        )

        if existing_link and str(existing_link["route_id"]) != str(route["route_id"]):
            raise DistributorPortalInvalidState(
                "Referral track is already linked to another accepted route"
            )

        row = await conn.fetchrow(
            """
            INSERT INTO distribution_route_referral_links (
                route_id,
                referral_track_id,
                tenant_code,
                distributor_id,
                opportunity_id,
                link_status,
                metadata
            )
            VALUES ($1, $2, $3, $4, $5, 'ACTIVE', $6::jsonb)
            ON CONFLICT (route_id, referral_track_id)
            DO UPDATE SET
                link_status = 'ACTIVE',
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            RETURNING *
            """,
            route_id,
            referral_track_id,
            tenant_code,
            distributor["distributor_id"],
            route["opportunity_id"],
            _json(metadata),
        )

    result = _serialize(row)
    result["distributor_code"] = distributor_code
    return result


async def get_portal_performance(
    *,
    tenant_code: str,
    distributor_code: str,
) -> dict[str, Any]:
    distributor = await get_portal_distributor(
        tenant_code=tenant_code,
        distributor_code=distributor_code,
    )

    async with db_connection() as conn:
        route_summary = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS routed_count,
                COUNT(*) FILTER (WHERE route_status = 'ACCEPTED') AS accepted_count,
                COUNT(*) FILTER (WHERE route_status = 'DECLINED') AS declined_count
            FROM distribution_offer_routes
            WHERE tenant_code = $1
              AND distributor_id = $2
            """,
            tenant_code,
            distributor["distributor_id"],
        )

        commission_summary = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS commission_event_count,
                COALESCE(SUM(commission_amount), 0) AS total_commission_amount
            FROM distribution_commission_events
            WHERE tenant_code = $1
              AND distributor_id = $2
            """,
            tenant_code,
            distributor["distributor_id"],
        )

        wallet_summary = await conn.fetchrow(
            """
            SELECT
                COALESCE(SUM(current_balance), 0) AS current_balance,
                COALESCE(SUM(available_balance), 0) AS available_balance,
                COALESCE(SUM(held_balance), 0) AS held_balance,
                COALESCE(SUM(paid_out_balance), 0) AS paid_out_balance,
                COALESCE(SUM(reversed_balance), 0) AS reversed_balance
            FROM distribution_distributor_wallets
            WHERE tenant_code = $1
              AND distributor_id = $2
            """,
            tenant_code,
            distributor["distributor_id"],
        )

        conversion_summary = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS conversion_count,
                COUNT(*) FILTER (WHERE ri.is_complete) AS completed_conversion_count,
                CASE
                    WHEN COUNT(*) > 0
                    THEN ROUND((COUNT(*) FILTER (WHERE ri.is_complete))::numeric / COUNT(*)::numeric, 4)
                    ELSE 0
                END AS conversion_completion_rate
            FROM referral_instances ri
            WHERE ri.tenant_code = $1
              AND ri.referrer_ucn = $2
            """,
            tenant_code,
            distributor_code,
        )

    routed_count = int(route_summary["routed_count"] or 0)
    accepted_count = int(route_summary["accepted_count"] or 0)
    acceptance_rate = (
        Decimal(accepted_count) / Decimal(routed_count)
        if routed_count
        else Decimal("0")
    )

    return {
        "tenant_code": tenant_code,
        "distributor_id": distributor["distributor_id"],
        "distributor_code": distributor_code,
        "routed_count": routed_count,
        "accepted_count": accepted_count,
        "declined_count": int(route_summary["declined_count"] or 0),
        "acceptance_rate": acceptance_rate.quantize(Decimal("0.0001")),
        "conversion_count": int(conversion_summary["conversion_count"] or 0),
        "completed_conversion_count": int(conversion_summary["completed_conversion_count"] or 0),
        "conversion_completion_rate": conversion_summary["conversion_completion_rate"],
        "commission_event_count": int(commission_summary["commission_event_count"] or 0),
        "total_commission_amount": commission_summary["total_commission_amount"],
        "wallet_current_balance": wallet_summary["current_balance"],
        "wallet_available_balance": wallet_summary["available_balance"],
        "wallet_held_balance": wallet_summary["held_balance"],
        "wallet_paid_out_balance": wallet_summary["paid_out_balance"],
        "wallet_reversed_balance": wallet_summary["reversed_balance"],
    }
