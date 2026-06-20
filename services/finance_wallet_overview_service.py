from __future__ import annotations

from decimal import Decimal
from typing import Any

from utils.db import db_connection


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value or 0))


def _serialize(row: Any) -> dict[str, Any]:
    return dict(row) if row else {}


async def get_network_wallet_overview(
    *,
    tenant_code: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        producer = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS wallet_count,
                COUNT(*) FILTER (WHERE status = 'ACTIVE') AS active_count,
                COUNT(*) FILTER (WHERE status <> 'ACTIVE') AS attention_count,
                COALESCE(SUM(current_balance), 0) AS current_balance,
                COALESCE(SUM(reserved_balance), 0) AS reserved_balance,
                COALESCE(SUM(current_balance - reserved_balance), 0) AS available_balance
            FROM sponsor_wallets
            WHERE ($1::text IS NULL OR tenant_code = $1)
            """,
            tenant_code,
        )

        distributor = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS wallet_count,
                COUNT(*) FILTER (WHERE status = 'ACTIVE') AS active_count,
                COUNT(*) FILTER (WHERE status <> 'ACTIVE') AS attention_count,
                COALESCE(SUM(current_balance), 0) AS current_balance,
                COALESCE(SUM(available_balance), 0) AS available_balance,
                COALESCE(SUM(held_balance), 0) AS held_balance,
                COALESCE(SUM(paid_out_balance), 0) AS paid_out_balance,
                COALESCE(SUM(reversed_balance), 0) AS reversed_balance
            FROM distribution_distributor_wallets
            WHERE ($1::text IS NULL OR tenant_code = $1)
            """,
            tenant_code,
        )

    producer_summary = _serialize(producer)
    distributor_summary = _serialize(distributor)
    producer_available = _decimal(producer_summary.get("available_balance"))
    distributor_available = _decimal(distributor_summary.get("available_balance"))
    distributor_held = _decimal(distributor_summary.get("held_balance"))

    return {
        "tenant_code": tenant_code,
        "producer_wallets": producer_summary,
        "distributor_wallets": distributor_summary,
        "network": {
            "wallet_count": int(producer_summary.get("wallet_count") or 0)
            + int(distributor_summary.get("wallet_count") or 0),
            "attention_count": int(producer_summary.get("attention_count") or 0)
            + int(distributor_summary.get("attention_count") or 0),
            "available_balance": producer_available,
            "demand_liability": distributor_available + distributor_held,
            "net_available_position": producer_available
            - distributor_available
            - distributor_held,
        },
    }
