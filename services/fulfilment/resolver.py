from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from utils.db import get_async_pool


@dataclass(frozen=True)
class FulfilmentPolicy:
    fulfilment_policy_id: str
    tenant_code: str
    reward_type: str
    journey_code: str | None
    journey_version: str | None
    product_code: str | None
    execution_model: str
    funding_model: str
    settlement_model: str
    provider_key: str
    sla_seconds: int
    max_retries: int
    retry_backoff_seconds: int
    metadata: dict[str, Any]


class FulfilmentPolicyNotFoundError(LookupError):
    pass


def _row_to_policy(row: Any) -> FulfilmentPolicy:
    return FulfilmentPolicy(
        fulfilment_policy_id=str(row["fulfilment_policy_id"]),
        tenant_code=row["tenant_code"],
        reward_type=row["reward_type"],
        journey_code=row.get("journey_code"),
        journey_version=row.get("journey_version"),
        product_code=row.get("product_code"),
        execution_model=row["execution_model"],
        funding_model=row["funding_model"],
        settlement_model=row["settlement_model"],
        provider_key=row["provider_key"],
        sla_seconds=row["sla_seconds"],
        max_retries=row["max_retries"],
        retry_backoff_seconds=row["retry_backoff_seconds"],
        metadata=row.get("metadata") or {},
    )


async def resolve_fulfilment_policy(
    *,
    tenant_code: str,
    reward_type: str,
    journey_code: str | None = None,
    journey_version: str | None = None,
    product_code: str | None = None,
) -> FulfilmentPolicy:
    pool = get_async_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                fulfilment_policy_id,
                tenant_code,
                reward_type,
                journey_code,
                journey_version,
                product_code,
                execution_model,
                funding_model,
                settlement_model,
                provider_key,
                sla_seconds,
                max_retries,
                retry_backoff_seconds,
                metadata
            FROM fulfilment_policies
            WHERE tenant_code = $1
              AND reward_type = $2
              AND (journey_code = $3 OR journey_code IS NULL)
              AND (journey_version = $4 OR journey_version IS NULL)
              AND (product_code = $5 OR product_code IS NULL)
              AND status = 'ACTIVE'
            ORDER BY
                CASE
                    WHEN journey_code = $3 THEN 0
                    WHEN journey_code IS NULL THEN 1
                    ELSE 2
                END,
                CASE
                    WHEN journey_version = $4 THEN 0
                    WHEN journey_version IS NULL THEN 1
                    ELSE 2
                END,
                CASE
                    WHEN product_code = $5 THEN 0
                    WHEN product_code IS NULL THEN 1
                    ELSE 2
                END,
                updated_at DESC
            LIMIT 1
            """,
            tenant_code,
            reward_type,
            journey_code,
            journey_version,
            product_code,
        )

    if not row:
        raise FulfilmentPolicyNotFoundError(
            f"No active fulfilment policy found for tenant={tenant_code}, "
            f"reward_type={reward_type}, journey={journey_code or '*'}"
        )

    return _row_to_policy(row)
