from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from utils.db import db_connection


async def create_funding_resolution_audit(
    *,
    reward_id: str,
    tenant_code: str,
    account_id: UUID,
    rule_id: UUID | None,
    reward_type: str | None,
    segment_code: str | None,
    campaign_code: str | None,
    sponsor_code: str | None,
    amount: Decimal,
    correlation_id: str | None,
) -> None:
    async with db_connection() as conn:
        await conn.execute(
            """
            INSERT INTO funding_resolution_audit (
                reward_id,
                tenant_code,
                account_id,
                rule_id,
                reward_type,
                segment_code,
                campaign_code,
                sponsor_code,
                amount,
                correlation_id
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            reward_id,
            tenant_code,
            account_id,
            rule_id,
            reward_type,
            segment_code,
            campaign_code,
            sponsor_code,
            amount,
            correlation_id,
        )


async def list_funding_resolution_audit(
    *,
    tenant_code: str | None = None,
    limit: int = 100,
) -> list[dict]:
    async with db_connection() as conn:
        if tenant_code:
            rows = await conn.fetch(
                """
                SELECT *
                FROM funding_resolution_audit
                WHERE tenant_code = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                tenant_code,
                limit,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT *
                FROM funding_resolution_audit
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit,
            )

    return [dict(row) for row in rows]