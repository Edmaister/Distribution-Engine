from __future__ import annotations

from typing import Any
from uuid import UUID

from utils.db import db_connection


def _serialize_row(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None

    data = dict(row)

    return {
        key: str(value) if isinstance(value, UUID) else value
        for key, value in data.items()
    }


async def list_matching_funding_rules(
    *,
    tenant_code: str,
    reward_type: str | None = None,
    segment_code: str | None = None,
    campaign_code: str | None = None,
    sponsor_code: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                r.rule_id,
                r.tenant_code,
                r.account_id,
                r.reward_type,
                r.segment_code,
                r.campaign_code,
                r.sponsor_code,
                r.priority,
                r.is_active,
                r.funding_model,
                r.sponsor_wallet_id AS wallet_id,
                r.created_at,
                r.updated_at,

                a.account_name,
                a.account_type,
                a.currency_code,
                a.current_balance,
                a.reserved_balance,
                a.available_balance,
                a.status,

                (
                    CASE WHEN r.reward_type IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN r.segment_code IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN r.campaign_code IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN r.sponsor_code IS NOT NULL THEN 1 ELSE 0 END
                ) AS match_strength
            FROM funding_account_rules r
            JOIN funding_accounts a
              ON a.account_id = r.account_id
            WHERE r.tenant_code = $1
              AND r.is_active = TRUE
              AND a.status = 'ACTIVE'
              AND (r.reward_type IS NULL OR r.reward_type = $2)
              AND (r.segment_code IS NULL OR r.segment_code = $3)
              AND (r.campaign_code IS NULL OR r.campaign_code = $4)
              AND (r.sponsor_code IS NULL OR r.sponsor_code = $5)
            ORDER BY
                r.priority ASC,
                match_strength DESC,
                r.created_at DESC
            LIMIT $6
            """,
            tenant_code,
            reward_type,
            segment_code,
            campaign_code,
            sponsor_code,
            limit,
        )

    return [
        serialized
        for row in rows
        if (serialized := _serialize_row(row)) is not None
    ]


async def resolve_funding_account(
    *,
    tenant_code: str,
    reward_type: str | None = None,
    segment_code: str | None = None,
    campaign_code: str | None = None,
    sponsor_code: str | None = None,
) -> dict[str, Any] | None:
    rows = await list_matching_funding_rules(
        tenant_code=tenant_code,
        reward_type=reward_type,
        segment_code=segment_code,
        campaign_code=campaign_code,
        sponsor_code=sponsor_code,
        limit=1,
    )

    if not rows:
        return None

    return rows[0]