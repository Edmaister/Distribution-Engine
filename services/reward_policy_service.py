from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from utils.db import get_async_connection
from utils.logging import get_logger

logger = get_logger(__name__)


def _normalize(value: Optional[str]) -> Optional[str]:
    if not isinstance(value, str):
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    return cleaned.upper()


def _row_to_policy(row: Any) -> Dict[str, Any]:
    return {
        "id": row[0],
        "product": row[1],
        "sub_product": row[2],
        "reward_type": row[3],
        "referrer_reward_amount": Decimal(str(row[4])),
        "referee_reward_amount": Decimal(str(row[5])),
        "allow_referee_reward": bool(row[6]),
        "is_active": bool(row[7]),
        "created_at": row[8],
        "updated_at": row[9],
    }


async def get_reward_policy(
    product: str,
    sub_product: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    normalized_product = _normalize(product)
    normalized_sub_product = _normalize(sub_product)

    if not normalized_product:
        raise ValueError("product is required")

    sql = """
    SELECT
        id,
        product,
        sub_product,
        reward_type,
        referrer_reward_amount,
        referee_reward_amount,
        allow_referee_reward,
        is_active,
        created_at,
        updated_at
    FROM reward_policies
    WHERE is_active = TRUE
      AND UPPER(product) = $1
      AND (
            UPPER(sub_product) = $2
            OR sub_product IS NULL
          )
    ORDER BY
        CASE
            WHEN UPPER(sub_product) = $3 THEN 0
            WHEN sub_product IS NULL THEN 1
            ELSE 2
        END,
        id DESC
    LIMIT 1
    """

    async with get_async_connection() as conn:
        row = await conn.fetchrow(
            sql,
            normalized_product,
            normalized_sub_product,
            normalized_sub_product,
        )

    if not row:
        logger.info(
            "No active reward policy found: product=%s sub_product=%s",
            normalized_product,
            normalized_sub_product,
        )
        return None

    policy = _row_to_policy(row)

    logger.info(
        "Resolved reward policy: id=%s product=%s sub_product=%s reward_type=%s",
        policy["id"],
        policy["product"],
        policy["sub_product"],
        policy["reward_type"],
    )

    return policy


async def list_reward_policies(
    product: Optional[str] = None,
    include_inactive: bool = False,
) -> List[Dict[str, Any]]:
    where_clauses: List[str] = []
    params: List[Any] = []

    normalized_product = _normalize(product)

    if normalized_product:
        params.append(normalized_product)
        where_clauses.append(f"UPPER(product) = ${len(params)}")

    if not include_inactive:
        where_clauses.append("is_active = TRUE")

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    sql = f"""
    SELECT
        id,
        product,
        sub_product,
        reward_type,
        referrer_reward_amount,
        referee_reward_amount,
        allow_referee_reward,
        is_active,
        created_at,
        updated_at
    FROM reward_policies
    {where_sql}
    ORDER BY product, sub_product NULLS LAST, id DESC
    """

    async with get_async_connection() as conn:
        rows = await conn.fetch(sql, *params)

    return [_row_to_policy(row) for row in rows]


async def get_reward_policy_by_id(policy_id: int) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT
        id,
        product,
        sub_product,
        reward_type,
        referrer_reward_amount,
        referee_reward_amount,
        allow_referee_reward,
        is_active,
        created_at,
        updated_at
    FROM reward_policies
    WHERE id = $1
    """

    async with get_async_connection() as conn:
        row = await conn.fetchrow(sql, policy_id)

    return _row_to_policy(row) if row else None


async def has_active_reward_policy(
    product: str,
    sub_product: Optional[str] = None,
) -> bool:
    return (
        await get_reward_policy(
            product=product,
            sub_product=sub_product,
        )
        is not None
    )