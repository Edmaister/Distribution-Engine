from __future__ import annotations

from typing import Any
from uuid import UUID

from utils.db import db_connection


def _row_to_dict(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


async def create_funding_account_rule(
    *,
    tenant_code: str,
    account_id: UUID | str,
    reward_type: str | None = None,
    segment_code: str | None = None,
    campaign_code: str | None = None,
    sponsor_code: str | None = None,
    priority: int = 100,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO funding_account_rules (
                tenant_code,
                account_id,
                reward_type,
                segment_code,
                campaign_code,
                sponsor_code,
                priority,
                is_active
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, TRUE)
            RETURNING *
            """,
            tenant_code,
            account_id,
            reward_type,
            segment_code,
            campaign_code,
            sponsor_code,
            priority,
        )

    return dict(row)


async def update_funding_account_rule(
    *,
    rule_id: UUID | str,
    reward_type: str | None = None,
    segment_code: str | None = None,
    campaign_code: str | None = None,
    sponsor_code: str | None = None,
    priority: int | None = None,
    is_active: bool | None = None,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE funding_account_rules
            SET
                reward_type = COALESCE($2, reward_type),
                segment_code = COALESCE($3, segment_code),
                campaign_code = COALESCE($4, campaign_code),
                sponsor_code = COALESCE($5, sponsor_code),
                priority = COALESCE($6, priority),
                is_active = COALESCE($7, is_active),
                updated_at = NOW()
            WHERE rule_id = $1
            RETURNING *
            """,
            rule_id,
            reward_type,
            segment_code,
            campaign_code,
            sponsor_code,
            priority,
            is_active,
        )

    return _row_to_dict(row)


async def get_funding_account_rule(
    *,
    rule_id: UUID | str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM funding_account_rules
            WHERE rule_id = $1
            """,
            rule_id,
        )

    return _row_to_dict(row)


async def list_funding_account_rules(
    *,
    tenant_code: str | None = None,
    account_id: UUID | str | None = None,
    active_only: bool = True,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM funding_account_rules
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::uuid IS NULL OR account_id = $2)
              AND ($3::boolean IS FALSE OR is_active = TRUE)
            ORDER BY priority ASC, created_at DESC
            LIMIT $4
            """,
            tenant_code,
            account_id,
            active_only,
            limit,
        )

    return [dict(row) for row in rows]