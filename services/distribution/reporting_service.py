from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from utils.db import db_connection


def _serialize(row: Any) -> dict[str, Any]:
    return {
        key: str(value) if isinstance(value, UUID) else value
        for key, value in dict(row).items()
    }


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value or 0))


async def get_marketplace_overview(
    *,
    tenant_code: str,
    sponsor_code: str | None = None,
    campaign_code: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        distributors = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS total_count,
                COUNT(*) FILTER (WHERE status = 'ACTIVE') AS active_count,
                COUNT(*) FILTER (WHERE status = 'SUSPENDED') AS suspended_count,
                COUNT(*) FILTER (WHERE status = 'TERMINATED') AS terminated_count
            FROM distribution_distributors
            WHERE tenant_code = $1
            """,
            tenant_code,
        )

        opportunities = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS total_count,
                COUNT(*) FILTER (WHERE opportunity_status = 'DRAFT') AS draft_count,
                COUNT(*) FILTER (WHERE opportunity_status = 'PUBLISHED') AS published_count,
                COUNT(*) FILTER (WHERE opportunity_status = 'CLOSED') AS closed_count,
                COALESCE(SUM(total_budget), 0) AS total_budget,
                COALESCE(SUM(remaining_budget), 0) AS remaining_budget
            FROM distribution_opportunities
            WHERE tenant_code = $1
              AND ($2::text IS NULL OR sponsor_code = $2)
              AND ($3::text IS NULL OR campaign_code = $3)
            """,
            tenant_code,
            sponsor_code,
            campaign_code,
        )

        routes = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS total_count,
                COUNT(*) FILTER (WHERE r.route_status = 'ROUTED') AS routed_count,
                COUNT(*) FILTER (WHERE r.route_status = 'ACCEPTED') AS accepted_count,
                COUNT(*) FILTER (WHERE r.route_status = 'DECLINED') AS declined_count,
                COALESCE(AVG(r.route_score), 0) AS average_route_score
            FROM distribution_offer_routes r
            JOIN distribution_opportunities o
              ON o.opportunity_id = r.opportunity_id
            WHERE r.tenant_code = $1
              AND ($2::text IS NULL OR o.sponsor_code = $2)
              AND ($3::text IS NULL OR o.campaign_code = $3)
            """,
            tenant_code,
            sponsor_code,
            campaign_code,
        )

        commissions = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS event_count,
                COALESCE(SUM(commission_amount), 0) AS total_commission_amount,
                COUNT(*) FILTER (WHERE commission_status = 'CREDITED') AS credited_count
            FROM distribution_commission_events
            WHERE tenant_code = $1
              AND ($2::text IS NULL OR sponsor_code = $2)
              AND ($3::text IS NULL OR campaign_code = $3)
            """,
            tenant_code,
            sponsor_code,
            campaign_code,
        )

        conversions = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS linked_count,
                COUNT(*) FILTER (WHERE ri.is_complete) AS completed_count,
                COUNT(DISTINCT l.route_id) AS linked_route_count,
                COUNT(DISTINCT l.opportunity_id) AS linked_opportunity_count,
                CASE
                    WHEN COUNT(*) > 0
                    THEN ROUND((COUNT(*) FILTER (WHERE ri.is_complete))::numeric / COUNT(*)::numeric, 4)
                    ELSE 0
                END AS completion_rate
            FROM distribution_route_referral_links l
            JOIN referral_instances ri
              ON ri.referral_track_id = l.referral_track_id
            JOIN distribution_opportunities o
              ON o.opportunity_id = l.opportunity_id
            WHERE l.tenant_code = $1
              AND l.link_status = 'ACTIVE'
              AND ($2::text IS NULL OR o.sponsor_code = $2)
              AND ($3::text IS NULL OR o.campaign_code = $3)
            """,
            tenant_code,
            sponsor_code,
            campaign_code,
        )

        attribution = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS total_referral_count,
                COUNT(*) FILTER (WHERE l.referral_track_id IS NOT NULL) AS attributed_count,
                COUNT(*) FILTER (WHERE l.referral_track_id IS NULL) AS unlinked_count,
                CASE
                    WHEN COUNT(*) > 0
                    THEN ROUND(
                        (COUNT(*) FILTER (WHERE l.referral_track_id IS NOT NULL))::numeric
                        / COUNT(*)::numeric,
                        4
                    )
                    ELSE 0
                END AS attribution_rate
            FROM referral_instances ri
            LEFT JOIN distribution_route_referral_links l
              ON l.referral_track_id = ri.referral_track_id
             AND l.link_status = 'ACTIVE'
            LEFT JOIN distribution_opportunities o
              ON o.opportunity_id = l.opportunity_id
            WHERE ri.tenant_code = $1
              AND ($2::text IS NULL OR o.sponsor_code = $2)
              AND ($3::text IS NULL OR o.campaign_code = $3)
            """,
            tenant_code,
            sponsor_code,
            campaign_code,
        )

        wallets = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS wallet_count,
                COALESCE(SUM(current_balance), 0) AS current_balance,
                COALESCE(SUM(available_balance), 0) AS available_balance,
                COALESCE(SUM(held_balance), 0) AS held_balance,
                COALESCE(SUM(paid_out_balance), 0) AS paid_out_balance,
                COALESCE(SUM(reversed_balance), 0) AS reversed_balance
            FROM distribution_distributor_wallets
            WHERE tenant_code = $1
            """,
            tenant_code,
        )

        governance = await conn.fetchrow(
            """
            SELECT
                (SELECT COUNT(*) FROM distribution_compliance_reviews WHERE tenant_code = $1)
                    AS compliance_review_count,
                (SELECT COUNT(*) FROM distribution_compliance_reviews WHERE tenant_code = $1 AND review_status = 'OPEN')
                    AS open_compliance_review_count,
                (SELECT COUNT(*) FROM distribution_disputes WHERE tenant_code = $1)
                    AS dispute_count,
                (SELECT COUNT(*) FROM distribution_disputes WHERE tenant_code = $1 AND dispute_status = 'OPEN')
                    AS open_dispute_count,
                (SELECT COUNT(*) FROM distribution_governance_audit WHERE tenant_code = $1)
                    AS governance_action_count
            """,
            tenant_code,
        )

    accepted_count = _decimal(routes["accepted_count"])
    route_count = _decimal(routes["total_count"])

    return {
        "tenant_code": tenant_code,
        "sponsor_code": sponsor_code,
        "campaign_code": campaign_code,
        "distributors": _serialize(distributors),
        "opportunities": _serialize(opportunities),
        "routes": {
            **_serialize(routes),
            "acceptance_rate": (
                accepted_count / route_count if route_count else Decimal("0")
            ).quantize(Decimal("0.0001")),
        },
        "commissions": _serialize(commissions),
        "conversions": {
            **_serialize(conversions),
            **_serialize(attribution),
        },
        "wallets": _serialize(wallets),
        "governance": _serialize(governance),
    }


async def list_opportunity_performance(
    *,
    tenant_code: str,
    sponsor_code: str | None = None,
    campaign_code: str | None = None,
    opportunity_status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                o.opportunity_id,
                o.tenant_code,
                o.sponsor_code,
                o.campaign_code,
                o.opportunity_code,
                o.title,
                o.opportunity_status,
                o.total_budget,
                o.remaining_budget,
                COALESCE(r.routed_count, 0) AS routed_count,
                COALESCE(r.accepted_count, 0) AS accepted_count,
                COALESCE(r.declined_count, 0) AS declined_count,
                COALESCE(r.average_route_score, 0) AS average_route_score,
                COALESCE(cv.conversion_count, 0) AS conversion_count,
                COALESCE(cv.completed_conversion_count, 0) AS completed_conversion_count,
                COALESCE(cv.conversion_completion_rate, 0) AS conversion_completion_rate,
                COALESCE(d.dispute_count, 0) AS dispute_count
            FROM distribution_opportunities o
            LEFT JOIN (
                SELECT
                    opportunity_id,
                    COUNT(*) AS routed_count,
                    COUNT(*) FILTER (WHERE route_status = 'ACCEPTED') AS accepted_count,
                    COUNT(*) FILTER (WHERE route_status = 'DECLINED') AS declined_count,
                    AVG(route_score) AS average_route_score
                FROM distribution_offer_routes
                GROUP BY opportunity_id
            ) r ON r.opportunity_id = o.opportunity_id
            LEFT JOIN (
                SELECT
                    l.opportunity_id,
                    COUNT(*) AS conversion_count,
                    COUNT(*) FILTER (WHERE ri.is_complete) AS completed_conversion_count,
                    CASE
                        WHEN COUNT(*) > 0
                        THEN ROUND((COUNT(*) FILTER (WHERE ri.is_complete))::numeric / COUNT(*)::numeric, 4)
                        ELSE 0
                    END AS conversion_completion_rate
                FROM distribution_route_referral_links l
                JOIN referral_instances ri
                  ON ri.referral_track_id = l.referral_track_id
                WHERE l.link_status = 'ACTIVE'
                GROUP BY l.opportunity_id
            ) cv ON cv.opportunity_id = o.opportunity_id
            LEFT JOIN (
                SELECT opportunity_id, COUNT(*) AS dispute_count
                FROM distribution_disputes
                GROUP BY opportunity_id
            ) d ON d.opportunity_id = o.opportunity_id
            WHERE o.tenant_code = $1
              AND ($2::text IS NULL OR o.sponsor_code = $2)
              AND ($3::text IS NULL OR o.campaign_code = $3)
              AND ($4::text IS NULL OR o.opportunity_status = $4)
            ORDER BY o.created_at DESC
            LIMIT $5
            """,
            tenant_code,
            sponsor_code,
            campaign_code,
            opportunity_status,
            limit,
        )

    return [_serialize(row) for row in rows]


async def list_producer_conversion_journeys(
    *,
    tenant_code: str,
    sponsor_code: str,
    campaign_code: str | None = None,
    opportunity_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                ri.referral_track_id,
                ri.tenant_code,
                o.sponsor_code AS producer_code,
                o.campaign_code,
                o.opportunity_id,
                o.opportunity_code,
                o.title AS opportunity_title,
                l.route_id,
                d.distributor_id,
                d.distributor_code,
                d.distributor_name,
                d.distributor_type,
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
            FROM distribution_route_referral_links l
            JOIN distribution_opportunities o
              ON o.opportunity_id = l.opportunity_id
            JOIN distribution_distributors d
              ON d.distributor_id = l.distributor_id
            JOIN referral_instances ri
              ON ri.referral_track_id = l.referral_track_id
            WHERE l.tenant_code = $1
              AND o.sponsor_code = $2
              AND l.link_status = 'ACTIVE'
              AND ($3::text IS NULL OR o.campaign_code = $3)
              AND ($4::uuid IS NULL OR o.opportunity_id = $4::uuid)
            ORDER BY ri.updated_at DESC NULLS LAST,
                     ri.created_at DESC NULLS LAST,
                     ri.referral_track_id DESC
            LIMIT $5
            """,
            tenant_code,
            sponsor_code,
            campaign_code,
            opportunity_id,
            limit,
        )

    items = [_serialize(row) for row in rows]
    completed_count = sum(1 for item in items if item.get("is_complete"))
    completion_rate = (
        Decimal(completed_count) / Decimal(len(items)) if items else Decimal("0")
    ).quantize(Decimal("0.0001"))
    return {
        "tenant_code": tenant_code,
        "producer_code": sponsor_code,
        "campaign_code": campaign_code,
        "opportunity_id": opportunity_id,
        "count": len(items),
        "completed_count": completed_count,
        "completion_rate": completion_rate,
        "items": items,
    }


async def list_attribution_exceptions(
    *,
    tenant_code: str,
    limit: int = 100,
) -> dict[str, Any]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                ri.referral_track_id,
                ri.tenant_code,
                ri.referrer_ucn AS distributor_code,
                ri.product,
                ri.sub_product,
                ri.status,
                ri.display_status,
                ri.progress_percent,
                ri.progress_band,
                ri.next_milestone,
                ri.is_complete,
                ri.validated_at,
                ri.ucn_captured_at,
                ri.account_opened_at,
                ri.account_activated_at,
                ri.funded_at,
                ri.debit_order_switched_at,
                ri.salary_switched_at,
                ri.first_transaction_completed_at,
                ri.completed_at,
                ri.created_at,
                ri.updated_at
            FROM referral_instances ri
            LEFT JOIN distribution_route_referral_links l
              ON l.referral_track_id = ri.referral_track_id
             AND l.link_status = 'ACTIVE'
            WHERE ri.tenant_code = $1
              AND l.referral_track_id IS NULL
            ORDER BY ri.updated_at DESC NULLS LAST,
                     ri.created_at DESC NULLS LAST,
                     ri.referral_track_id DESC
            LIMIT $2
            """,
            tenant_code,
            limit,
        )

    items = [_serialize(row) for row in rows]
    completed_count = sum(1 for item in items if item.get("is_complete"))
    return {
        "tenant_code": tenant_code,
        "count": len(items),
        "completed_count": completed_count,
        "items": items,
    }


async def list_distributor_performance(
    *,
    tenant_code: str,
    distributor_type: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                d.distributor_id,
                d.tenant_code,
                d.distributor_code,
                d.distributor_name,
                d.distributor_type,
                d.status,
                COALESCE(r.routed_count, 0) AS routed_count,
                COALESCE(r.accepted_count, 0) AS accepted_count,
                COALESCE(r.declined_count, 0) AS declined_count,
                COALESCE(cv.conversion_count, 0) AS conversion_count,
                COALESCE(cv.completed_conversion_count, 0) AS completed_conversion_count,
                COALESCE(cv.conversion_completion_rate, 0) AS conversion_completion_rate,
                COALESCE(c.commission_event_count, 0) AS commission_event_count,
                COALESCE(c.total_commission_amount, 0) AS total_commission_amount,
                COALESCE(w.current_balance, 0) AS wallet_current_balance,
                COALESCE(w.available_balance, 0) AS wallet_available_balance,
                COALESCE(dp.dispute_count, 0) AS dispute_count,
                COALESCE(cr.open_review_count, 0) AS open_compliance_review_count
            FROM distribution_distributors d
            LEFT JOIN (
                SELECT
                    distributor_id,
                    COUNT(*) AS routed_count,
                    COUNT(*) FILTER (WHERE route_status = 'ACCEPTED') AS accepted_count,
                    COUNT(*) FILTER (WHERE route_status = 'DECLINED') AS declined_count
                FROM distribution_offer_routes
                GROUP BY distributor_id
            ) r ON r.distributor_id = d.distributor_id
            LEFT JOIN (
                SELECT
                    l.distributor_id,
                    COUNT(*) AS conversion_count,
                    COUNT(*) FILTER (WHERE ri.is_complete) AS completed_conversion_count,
                    CASE
                        WHEN COUNT(*) > 0
                        THEN ROUND((COUNT(*) FILTER (WHERE ri.is_complete))::numeric / COUNT(*)::numeric, 4)
                        ELSE 0
                    END AS conversion_completion_rate
                FROM distribution_route_referral_links l
                JOIN referral_instances ri
                  ON ri.referral_track_id = l.referral_track_id
                WHERE l.link_status = 'ACTIVE'
                GROUP BY l.distributor_id
            ) cv ON cv.distributor_id = d.distributor_id
            LEFT JOIN (
                SELECT
                    distributor_id,
                    COUNT(*) AS commission_event_count,
                    SUM(commission_amount) AS total_commission_amount
                FROM distribution_commission_events
                GROUP BY distributor_id
            ) c ON c.distributor_id = d.distributor_id
            LEFT JOIN (
                SELECT
                    distributor_id,
                    SUM(current_balance) AS current_balance,
                    SUM(available_balance) AS available_balance
                FROM distribution_distributor_wallets
                GROUP BY distributor_id
            ) w ON w.distributor_id = d.distributor_id
            LEFT JOIN (
                SELECT distributor_id, COUNT(*) AS dispute_count
                FROM distribution_disputes
                GROUP BY distributor_id
            ) dp ON dp.distributor_id = d.distributor_id
            LEFT JOIN (
                SELECT distributor_id, COUNT(*) AS open_review_count
                FROM distribution_compliance_reviews
                WHERE review_status = 'OPEN'
                GROUP BY distributor_id
            ) cr ON cr.distributor_id = d.distributor_id
            WHERE d.tenant_code = $1
              AND ($2::text IS NULL OR d.distributor_type = $2)
              AND ($3::text IS NULL OR d.status = $3)
            ORDER BY d.created_at DESC
            LIMIT $4
            """,
            tenant_code,
            distributor_type,
            status,
            limit,
        )

    return [_serialize(row) for row in rows]


async def get_governance_report(*, tenant_code: str) -> dict[str, Any]:
    async with db_connection() as conn:
        compliance = await conn.fetch(
            """
            SELECT review_status AS status, COUNT(*) AS count
            FROM distribution_compliance_reviews
            WHERE tenant_code = $1
            GROUP BY review_status
            ORDER BY review_status
            """,
            tenant_code,
        )

        disputes = await conn.fetch(
            """
            SELECT dispute_status AS status, COUNT(*) AS count
            FROM distribution_disputes
            WHERE tenant_code = $1
            GROUP BY dispute_status
            ORDER BY dispute_status
            """,
            tenant_code,
        )

        actions = await conn.fetch(
            """
            SELECT action_type, COUNT(*) AS count
            FROM distribution_governance_audit
            WHERE tenant_code = $1
            GROUP BY action_type
            ORDER BY action_type
            """,
            tenant_code,
        )

    return {
        "tenant_code": tenant_code,
        "compliance_reviews": [_serialize(row) for row in compliance],
        "disputes": [_serialize(row) for row in disputes],
        "governance_actions": [_serialize(row) for row in actions],
    }
