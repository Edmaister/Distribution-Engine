from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from utils.db import db_connection


async def create_invoice_record(
    *,
    tenant_code: str,
    sponsor_code: str,
    sponsor_name: str,
    invoice_number: str,
    contract_id: str | None,
    invoice_period_start: date | None,
    invoice_period_end: date | None,
    due_date: date | None,
    currency: str,
    subtotal_amount: Decimal,
    vat_amount: Decimal,
    total_amount: Decimal,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = """
        INSERT INTO sponsor_invoices (
            tenant_code,
            sponsor_code,
            sponsor_name,
            contract_id,
            invoice_number,
            invoice_period_start,
            invoice_period_end,
            due_date,
            currency,
            subtotal_amount,
            vat_amount,
            total_amount,
            outstanding_amount,
            metadata
        )
        VALUES (
            $1, $2, $3, $4, $5,
            $6, $7, $8, $9,
            $10, $11, $12, $12,
            $13::jsonb
        )
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(
            query,
            tenant_code,
            sponsor_code,
            sponsor_name,
            contract_id,
            invoice_number,
            invoice_period_start,
            invoice_period_end,
            due_date,
            currency,
            subtotal_amount,
            vat_amount,
            total_amount,
            json.dumps(metadata or {}),
        )

    return dict(row)


async def create_invoice_line_record(
    *,
    invoice_id: str,
    line_type: str,
    description: str,
    quantity: Decimal,
    unit_amount: Decimal,
    line_amount: Decimal,
    reward_id: str | None = None,
    allocation_id: str | None = None,
    settlement_id: str | None = None,
    source_ledger_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = """
        INSERT INTO sponsor_invoice_lines (
            invoice_id,
            line_type,
            description,
            quantity,
            unit_amount,
            line_amount,
            reward_id,
            allocation_id,
            settlement_id,
            source_ledger_id,
            metadata
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb)
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(
            query,
            invoice_id,
            line_type,
            description,
            quantity,
            unit_amount,
            line_amount,
            reward_id,
            allocation_id,
            settlement_id,
            source_ledger_id,
            json.dumps(metadata or {}),
        )

    return dict(row)


async def get_invoice_record(*, invoice_id: str) -> dict[str, Any] | None:
    query = """
        SELECT *
        FROM sponsor_invoices
        WHERE invoice_id = $1;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, invoice_id)

    return dict(row) if row else None


async def list_invoice_records(
    *,
    tenant_code: str,
    sponsor_code: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM sponsor_invoices
        WHERE tenant_code = $1
          AND ($2::text IS NULL OR sponsor_code = $2)
          AND ($3::text IS NULL OR status = $3)
        ORDER BY created_at DESC
        LIMIT $4;
    """

    async with db_connection() as conn:
        rows = await conn.fetch(query, tenant_code, sponsor_code, status, limit)

    return [dict(row) for row in rows]


async def list_statement_invoice_records(
    *,
    tenant_code: str,
    sponsor_code: str,
    period_start: date,
    period_end: date,
    currency: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM sponsor_invoices
        WHERE tenant_code = $1
          AND sponsor_code = $2
          AND COALESCE(invoice_period_start, created_at::date) <= $4
          AND COALESCE(invoice_period_end, created_at::date) >= $3
          AND ($5::text IS NULL OR currency = $5)
        ORDER BY invoice_period_start NULLS LAST, created_at ASC
        LIMIT $6;
    """

    async with db_connection() as conn:
        rows = await conn.fetch(
            query,
            tenant_code,
            sponsor_code,
            period_start,
            period_end,
            currency,
            limit,
        )

    return [dict(row) for row in rows]


async def list_billing_dashboard_invoice_records(
    *,
    tenant_code: str,
    sponsor_code: str | None = None,
    period_start: date | None = None,
    period_end: date | None = None,
    currency: str | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM sponsor_invoices
        WHERE tenant_code = $1
          AND ($2::text IS NULL OR sponsor_code = $2)
          AND ($3::date IS NULL OR COALESCE(invoice_period_end, created_at::date) >= $3)
          AND ($4::date IS NULL OR COALESCE(invoice_period_start, created_at::date) <= $4)
          AND ($5::text IS NULL OR currency = $5)
        ORDER BY created_at DESC
        LIMIT $6;
    """

    async with db_connection() as conn:
        rows = await conn.fetch(
            query,
            tenant_code,
            sponsor_code,
            period_start,
            period_end,
            currency,
            limit,
        )

    return [dict(row) for row in rows]


async def list_vat_report_invoice_records(
    *,
    tenant_code: str,
    period_start: date,
    period_end: date,
    sponsor_code: str | None = None,
    currency: str | None = None,
    status: str | None = None,
    limit: int = 2000,
) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM sponsor_invoices
        WHERE tenant_code = $1
          AND COALESCE(invoice_period_start, issued_at::date, created_at::date) <= $3
          AND COALESCE(invoice_period_end, issued_at::date, created_at::date) >= $2
          AND ($4::text IS NULL OR sponsor_code = $4)
          AND ($5::text IS NULL OR currency = $5)
          AND ($6::text IS NULL OR status = $6)
        ORDER BY COALESCE(invoice_period_start, issued_at::date, created_at::date) ASC,
                 invoice_number ASC
        LIMIT $7;
    """

    async with db_connection() as conn:
        rows = await conn.fetch(
            query,
            tenant_code,
            period_start,
            period_end,
            sponsor_code,
            currency,
            status,
            limit,
        )

    return [dict(row) for row in rows]


async def list_statement_payment_records(
    *,
    tenant_code: str,
    sponsor_code: str,
    period_start: date,
    period_end: date,
    currency: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    query = """
        SELECT
            p.*,
            i.invoice_number,
            i.currency
        FROM sponsor_invoice_payments p
        JOIN sponsor_invoices i
          ON i.invoice_id = p.invoice_id
        WHERE i.tenant_code = $1
          AND i.sponsor_code = $2
          AND p.paid_at::date >= $3
          AND p.paid_at::date <= $4
          AND ($5::text IS NULL OR i.currency = $5)
        ORDER BY p.paid_at ASC, p.created_at ASC
        LIMIT $6;
    """

    async with db_connection() as conn:
        rows = await conn.fetch(
            query,
            tenant_code,
            sponsor_code,
            period_start,
            period_end,
            currency,
            limit,
        )

    return [dict(row) for row in rows]


async def list_unbilled_contract_utilisation(
    *,
    contract_id: str,
    period_start: date,
    period_end: date,
) -> list[dict[str, Any]]:
    query = """
        SELECT
            l.ledger_id,
            l.contract_id,
            l.amount,
            l.reward_id,
            l.allocation_id,
            l.correlation_id,
            l.metadata,
            l.created_at,
            c.tenant_code,
            c.sponsor_code,
            c.sponsor_name
        FROM funding_contract_ledger l
        JOIN funding_contracts c
          ON c.contract_id = l.contract_id
        LEFT JOIN sponsor_invoice_lines il
          ON il.source_ledger_id = l.ledger_id
        WHERE l.contract_id = $1
          AND l.event_type = 'BUDGET_UTILISED'
          AND l.created_at::date >= $2
          AND l.created_at::date <= $3
          AND il.line_id IS NULL
        ORDER BY l.created_at ASC, l.ledger_id ASC;
    """

    async with db_connection() as conn:
        rows = await conn.fetch(query, contract_id, period_start, period_end)

    return [dict(row) for row in rows]


async def list_invoice_line_records(*, invoice_id: str) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM sponsor_invoice_lines
        WHERE invoice_id = $1
        ORDER BY created_at ASC;
    """

    async with db_connection() as conn:
        rows = await conn.fetch(query, invoice_id)

    return [dict(row) for row in rows]


async def issue_invoice_record(*, invoice_id: str) -> dict[str, Any] | None:
    query = """
        UPDATE sponsor_invoices
        SET status = 'ISSUED',
            issued_at = COALESCE(issued_at, NOW()),
            updated_at = NOW()
        WHERE invoice_id = $1
          AND status = 'DRAFT'
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, invoice_id)

    return dict(row) if row else None


async def create_invoice_payment_record(
    *,
    invoice_id: str,
    amount: Decimal,
    payment_reference: str | None = None,
    paid_at: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = """
        INSERT INTO sponsor_invoice_payments (
            invoice_id,
            amount,
            payment_reference,
            paid_at,
            metadata
        )
        VALUES ($1, $2, $3, COALESCE($4, NOW()), $5::jsonb)
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(
            query,
            invoice_id,
            amount,
            payment_reference,
            paid_at,
            json.dumps(metadata or {}),
        )

    return dict(row)


async def get_invoice_payment_record(*, payment_id: str) -> dict[str, Any] | None:
    query = """
        SELECT *
        FROM sponsor_invoice_payments
        WHERE payment_id = $1;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, payment_id)

    return dict(row) if row else None


async def apply_invoice_payment_amount(
    *,
    invoice_id: str,
    amount: Decimal,
) -> dict[str, Any] | None:
    query = """
        UPDATE sponsor_invoices
        SET paid_amount = paid_amount + $2,
            outstanding_amount = GREATEST(total_amount - (paid_amount + $2), 0),
            status = CASE
                WHEN total_amount - (paid_amount + $2) <= 0 THEN 'PAID'
                WHEN paid_amount + $2 > 0 THEN 'PARTIALLY_PAID'
                ELSE status
            END,
            paid_at = CASE
                WHEN total_amount - (paid_amount + $2) <= 0 THEN COALESCE(paid_at, NOW())
                ELSE paid_at
            END,
            updated_at = NOW()
        WHERE invoice_id = $1
          AND status IN ('ISSUED', 'PARTIALLY_PAID')
          AND outstanding_amount >= $2
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, invoice_id, amount)

    return dict(row) if row else None


async def create_invoice_payment_reversal_record(
    *,
    payment_id: str,
    invoice_id: str,
    amount: Decimal,
    reason: str,
    reversed_by: str | None = None,
    reversed_at: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = """
        INSERT INTO sponsor_invoice_payment_reversals (
            payment_id,
            invoice_id,
            amount,
            reason,
            reversed_by,
            reversed_at,
            metadata
        )
        VALUES ($1, $2, $3, $4, $5, COALESCE($6, NOW()), $7::jsonb)
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(
            query,
            payment_id,
            invoice_id,
            amount,
            reason,
            reversed_by,
            reversed_at,
            json.dumps(metadata or {}),
        )

    return dict(row)


async def get_reversed_payment_amount(*, payment_id: str) -> Decimal:
    query = """
        SELECT COALESCE(SUM(amount), 0)
        FROM sponsor_invoice_payment_reversals
        WHERE payment_id = $1;
    """

    async with db_connection() as conn:
        value = await conn.fetchval(query, payment_id)

    return Decimal(str(value or 0))


async def apply_invoice_payment_reversal_amount(
    *,
    invoice_id: str,
    amount: Decimal,
) -> dict[str, Any] | None:
    query = """
        UPDATE sponsor_invoices
        SET paid_amount = paid_amount - $2,
            outstanding_amount = LEAST(total_amount, outstanding_amount + $2),
            status = CASE
                WHEN paid_amount - $2 <= 0 THEN 'ISSUED'
                WHEN outstanding_amount + $2 >= total_amount THEN 'ISSUED'
                ELSE 'PARTIALLY_PAID'
            END,
            paid_at = CASE
                WHEN paid_amount - $2 <= 0 THEN NULL
                ELSE paid_at
            END,
            updated_at = NOW()
        WHERE invoice_id = $1
          AND paid_amount >= $2
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, invoice_id, amount)

    return dict(row) if row else None


async def list_invoice_payment_records(
    *,
    invoice_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM sponsor_invoice_payments
        WHERE invoice_id = $1
        ORDER BY paid_at DESC, created_at DESC
        LIMIT $2;
    """

    async with db_connection() as conn:
        rows = await conn.fetch(query, invoice_id, limit)

    return [dict(row) for row in rows]


async def list_invoice_payment_reversal_records(
    *,
    invoice_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM sponsor_invoice_payment_reversals
        WHERE invoice_id = $1
        ORDER BY reversed_at DESC, created_at DESC
        LIMIT $2;
    """

    async with db_connection() as conn:
        rows = await conn.fetch(query, invoice_id, limit)

    return [dict(row) for row in rows]


async def create_payment_receipt_record(
    *,
    tenant_code: str,
    sponsor_code: str,
    currency: str,
    amount: Decimal,
    payment_reference: str | None = None,
    received_at: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = """
        INSERT INTO sponsor_payment_receipts (
            tenant_code,
            sponsor_code,
            currency,
            amount,
            unapplied_amount,
            payment_reference,
            received_at,
            metadata
        )
        VALUES ($1, $2, $3, $4, $4, $5, COALESCE($6, NOW()), $7::jsonb)
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(
            query,
            tenant_code,
            sponsor_code,
            currency,
            amount,
            payment_reference,
            received_at,
            json.dumps(metadata or {}),
        )

    return dict(row)


async def get_payment_receipt_record(*, receipt_id: str) -> dict[str, Any] | None:
    query = """
        SELECT *
        FROM sponsor_payment_receipts
        WHERE receipt_id = $1;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, receipt_id)

    return dict(row) if row else None


async def list_payment_receipt_records(
    *,
    tenant_code: str,
    sponsor_code: str,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM sponsor_payment_receipts
        WHERE tenant_code = $1
          AND sponsor_code = $2
          AND ($3::text IS NULL OR status = $3)
        ORDER BY received_at DESC, created_at DESC
        LIMIT $4;
    """

    async with db_connection() as conn:
        rows = await conn.fetch(query, tenant_code, sponsor_code, status, limit)

    return [dict(row) for row in rows]


async def apply_payment_receipt_allocation_amount(
    *,
    receipt_id: str,
    amount: Decimal,
) -> dict[str, Any] | None:
    query = """
        UPDATE sponsor_payment_receipts
        SET applied_amount = applied_amount + $2,
            unapplied_amount = amount - (applied_amount + $2),
            status = CASE
                WHEN amount - (applied_amount + $2) <= 0 THEN 'FULLY_APPLIED'
                WHEN applied_amount + $2 > 0 THEN 'PARTIALLY_APPLIED'
                ELSE status
            END,
            updated_at = NOW()
        WHERE receipt_id = $1
          AND unapplied_amount >= $2
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, receipt_id, amount)

    return dict(row) if row else None


async def reverse_payment_receipt_allocation_amount(
    *,
    receipt_id: str,
    amount: Decimal,
) -> dict[str, Any] | None:
    query = """
        UPDATE sponsor_payment_receipts
        SET applied_amount = applied_amount - $2,
            unapplied_amount = unapplied_amount + $2,
            status = CASE
                WHEN applied_amount - $2 <= 0 THEN 'UNAPPLIED'
                WHEN unapplied_amount + $2 > 0 THEN 'PARTIALLY_APPLIED'
                ELSE 'FULLY_APPLIED'
            END,
            updated_at = NOW()
        WHERE receipt_id = $1
          AND applied_amount >= $2
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, receipt_id, amount)

    return dict(row) if row else None


async def create_payment_allocation_record(
    *,
    receipt_id: str,
    invoice_id: str,
    payment_id: str,
    amount: Decimal,
    allocated_by: str | None = None,
    allocated_at: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = """
        INSERT INTO sponsor_payment_allocations (
            receipt_id,
            invoice_id,
            payment_id,
            amount,
            allocated_by,
            allocated_at,
            metadata
        )
        VALUES ($1, $2, $3, $4, $5, COALESCE($6, NOW()), $7::jsonb)
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(
            query,
            receipt_id,
            invoice_id,
            payment_id,
            amount,
            allocated_by,
            allocated_at,
            json.dumps(metadata or {}),
        )

    return dict(row)


async def get_payment_allocation_record(
    *,
    allocation_id: str,
) -> dict[str, Any] | None:
    query = """
        SELECT *
        FROM sponsor_payment_allocations
        WHERE allocation_id = $1;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, allocation_id)

    return dict(row) if row else None


async def get_reversed_payment_allocation_amount(*, allocation_id: str) -> Decimal:
    query = """
        SELECT COALESCE(SUM(amount), 0)
        FROM sponsor_payment_allocation_reversals
        WHERE allocation_id = $1;
    """

    async with db_connection() as conn:
        value = await conn.fetchval(query, allocation_id)

    return Decimal(str(value or 0))


async def create_payment_allocation_reversal_record(
    *,
    allocation_id: str,
    receipt_id: str,
    invoice_id: str,
    payment_id: str,
    amount: Decimal,
    reason: str,
    reversed_by: str | None = None,
    reversed_at: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = """
        INSERT INTO sponsor_payment_allocation_reversals (
            allocation_id,
            receipt_id,
            invoice_id,
            payment_id,
            amount,
            reason,
            reversed_by,
            reversed_at,
            metadata
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, COALESCE($8, NOW()), $9::jsonb)
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(
            query,
            allocation_id,
            receipt_id,
            invoice_id,
            payment_id,
            amount,
            reason,
            reversed_by,
            reversed_at,
            json.dumps(metadata or {}),
        )

    return dict(row)


async def list_payment_allocation_records(
    *,
    receipt_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM sponsor_payment_allocations
        WHERE receipt_id = $1
        ORDER BY allocated_at ASC, created_at ASC
        LIMIT $2;
    """

    async with db_connection() as conn:
        rows = await conn.fetch(query, receipt_id, limit)

    return [dict(row) for row in rows]
