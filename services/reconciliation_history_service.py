from __future__ import annotations

from typing import Any

from utils.db import db_connection


async def create_reconciliation_run(
    *,
    tenant_code: str | None,
    provider_key: str,
    total_records: int,
    matched_count: int,
    missing_count: int,
    duplicate_count: int,
    overpaid_count: int,
    underpaid_count: int,
) -> dict[str, Any]:

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO reconciliation_runs (
                tenant_code,
                provider_key,
                total_records,
                matched_count,
                missing_count,
                duplicate_count,
                overpaid_count,
                underpaid_count
            )
            VALUES (
                $1,$2,$3,$4,$5,$6,$7,$8
            )
            RETURNING *
            """,
            tenant_code,
            provider_key,
            total_records,
            matched_count,
            missing_count,
            duplicate_count,
            overpaid_count,
            underpaid_count,
        )

    return dict(row)


async def create_reconciliation_results(
    *,
    run_id: str,
    results: list[dict[str, Any]],
) -> int:

    if not results:
        return 0

    async with db_connection() as conn:
        for result in results:
            await conn.execute(
                """
                INSERT INTO reconciliation_results (
                    run_id,
                    provider_reference,
                    status,
                    platform_amount,
                    provider_amount
                )
                VALUES (
                    $1,$2,$3,$4,$5
                )
                """,
                run_id,
                result.get("provider_reference"),
                result.get("status"),
                result.get("platform_amount"),
                result.get("provider_amount"),
            )

    return len(results)


async def get_reconciliation_run(
    *,
    run_id: str,
) -> dict[str, Any] | None:

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM reconciliation_runs
            WHERE run_id = $1
            """,
            run_id,
        )

    return dict(row) if row else None


async def list_reconciliation_runs(
    *,
    tenant_code: str | None = None,
    provider_key: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:

    filters = []
    params = []

    if tenant_code:
        params.append(tenant_code)
        filters.append(f"tenant_code = ${len(params)}")

    if provider_key:
        params.append(provider_key)
        filters.append(f"provider_key = ${len(params)}")

    params.append(limit)

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    async with db_connection() as conn:
        rows = await conn.fetch(
            f"""
            SELECT *
            FROM reconciliation_runs
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${len(params)}
            """,
            *params,
        )

    return [dict(row) for row in rows]


async def get_reconciliation_results(
    *,
    run_id: str,
) -> list[dict[str, Any]]:

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM reconciliation_results
            WHERE run_id = $1
            ORDER BY created_at
            """,
            run_id,
        )

    return [dict(row) for row in rows]