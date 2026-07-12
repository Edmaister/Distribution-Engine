from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import uuid4

from utils.db import db_connection


def _money(value: Any) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(Decimal("0.01"))


async def run_funding_reconciliation(
    *,
    tenant_code: str,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        expected_row = await conn.fetchrow(
            """
            SELECT COALESCE(SUM(amount), 0) AS expected_amount
            FROM funding_reservations
            WHERE tenant_code = $1
              AND status IN ('RESERVED', 'SETTLED')
            """,
            tenant_code,
        )

        actual_row = await conn.fetchrow(
            """
            SELECT COALESCE(SUM(amount), 0) AS actual_amount
            FROM fulfilment_settlement_ledger
            WHERE tenant_code = $1
              AND status IN ('SETTLED', 'COMPLETED', 'SUCCESS')
            """,
            tenant_code,
        )

        expected_amount = _money(expected_row["expected_amount"])
        actual_amount = _money(actual_row["actual_amount"])
        variance_amount = _money(actual_amount - expected_amount)

        status = "MATCHED" if variance_amount == Decimal("0.00") else "EXCEPTION"

        run_id = uuid4()

        run = await conn.fetchrow(
            """
            INSERT INTO funding_reconciliation_runs (
                run_id,
                tenant_code,
                run_date,
                expected_amount,
                actual_amount,
                variance_amount,
                status,
                correlation_id
            )
            VALUES ($1, $2, NOW(), $3, $4, $5, $6, $7)
            RETURNING
                run_id,
                tenant_code,
                expected_amount,
                actual_amount,
                variance_amount,
                status,
                correlation_id,
                created_at
            """,
            run_id,
            tenant_code,
            expected_amount,
            actual_amount,
            variance_amount,
            status,
            correlation_id,
        )

        exceptions: list[dict[str, Any]] = []

        if status == "EXCEPTION":
            exception = await conn.fetchrow(
                """
                INSERT INTO funding_reconciliation_exceptions (
                    exception_id,
                    run_id,
                    tenant_code,
                    exception_type,
                    expected_amount,
                    actual_amount,
                    variance_amount,
                    status,
                    correlation_id
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, 'OPEN', $8)
                RETURNING
                    exception_id,
                    run_id,
                    tenant_code,
                    exception_type,
                    reference_id,
                    expected_amount,
                    actual_amount,
                    variance_amount,
                    status,
                    correlation_id,
                    created_at,
                    resolved_at
                """,
                uuid4(),
                run_id,
                tenant_code,
                "FUNDING_VARIANCE",
                expected_amount,
                actual_amount,
                variance_amount,
                correlation_id,
            )

            exceptions.append(dict(exception))

    return {
        "status": "ok",
        "run": dict(run),
        "exception_count": len(exceptions),
        "exceptions": exceptions,
    }


async def list_funding_reconciliation_runs(
    *,
    tenant_code: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                run_id,
                tenant_code,
                expected_amount,
                actual_amount,
                variance_amount,
                status,
                correlation_id,
                created_at
            FROM funding_reconciliation_runs
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::text IS NULL OR status = $2)
            ORDER BY created_at DESC
            LIMIT $3
            """,
            tenant_code,
            status,
            limit,
        )

    return [dict(row) for row in rows]


async def get_funding_reconciliation_run(
    *,
    run_id: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        run = await conn.fetchrow(
            """
            SELECT
                run_id,
                tenant_code,
                expected_amount,
                actual_amount,
                variance_amount,
                status,
                correlation_id,
                created_at
            FROM funding_reconciliation_runs
            WHERE run_id = $1
            """,
            run_id,
        )

        if not run:
            return None

        exceptions = await conn.fetch(
            """
            SELECT
                exception_id,
                run_id,
                tenant_code,
                exception_type,
                reference_id,
                expected_amount,
                actual_amount,
                variance_amount,
                status,
                correlation_id,
                created_at,
                resolved_at
            FROM funding_reconciliation_exceptions
            WHERE run_id = $1
            ORDER BY created_at DESC
            """,
            run_id,
        )

    return {
        "run": dict(run),
        "exception_count": len(exceptions),
        "exceptions": [dict(row) for row in exceptions],
    }


async def list_funding_reconciliation_exceptions(
    *,
    tenant_code: str | None = None,
    status: str | None = "OPEN",
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                exception_id,
                run_id,
                tenant_code,
                exception_type,
                reference_id,
                expected_amount,
                actual_amount,
                variance_amount,
                status,
                correlation_id,
                created_at,
                resolved_at
            FROM funding_reconciliation_exceptions
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::text IS NULL OR status = $2)
            ORDER BY created_at DESC
            LIMIT $3
            """,
            tenant_code,
            status,
            limit,
        )

    return [dict(row) for row in rows]


async def resolve_funding_reconciliation_exception(
    *,
    exception_id: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE funding_reconciliation_exceptions
            SET
                status = 'RESOLVED',
                resolved_at = NOW()
            WHERE exception_id = $1
              AND status = 'OPEN'
            RETURNING
                exception_id,
                run_id,
                tenant_code,
                exception_type,
                reference_id,
                expected_amount,
                actual_amount,
                variance_amount,
                status,
                correlation_id,
                created_at,
                resolved_at
            """,
            exception_id,
        )

    return dict(row) if row else None
