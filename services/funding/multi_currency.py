from __future__ import annotations

import json
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID, uuid4

from utils.db import db_connection


class MultiCurrencyError(Exception):
    pass


class FxRateNotFound(MultiCurrencyError):
    pass


class CurrencyPairError(MultiCurrencyError):
    pass


def _currency(value: str) -> str:
    code = value.strip().upper()
    if len(code) != 3:
        raise CurrencyPairError("Currency codes must be 3-letter ISO-style codes")
    return code


def _decimal(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value))


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _json(value: dict[str, Any] | None) -> str:
    return json.dumps(value or {})


def _serialize(row: Any) -> dict[str, Any]:
    result = {
        key: str(value) if isinstance(value, UUID) else value
        for key, value in dict(row).items()
    }

    if isinstance(result.get("metadata"), str):
        result["metadata"] = json.loads(result["metadata"])

    return result


def _validate_pair(base_currency: str, quote_currency: str) -> tuple[str, str]:
    base = _currency(base_currency)
    quote = _currency(quote_currency)
    if base == quote:
        raise CurrencyPairError("Source and target currencies must differ")
    return base, quote


async def create_fx_rate(
    *,
    tenant_code: str,
    base_currency: str,
    quote_currency: str,
    rate: Decimal | int | float | str,
    rate_date: date,
    source_system: str,
    source_reference: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base, quote = _validate_pair(base_currency, quote_currency)
    resolved_rate = _decimal(rate)
    if resolved_rate <= 0:
        raise CurrencyPairError("FX rate must be greater than zero")

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO fx_rates (
                fx_rate_id,
                tenant_code,
                base_currency,
                quote_currency,
                rate,
                rate_date,
                source_system,
                source_reference,
                metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb)
            ON CONFLICT (
                tenant_code,
                base_currency,
                quote_currency,
                rate_date,
                source_system,
                source_reference
            )
            DO UPDATE SET
                rate = EXCLUDED.rate,
                metadata = EXCLUDED.metadata,
                rate_status = 'ACTIVE',
                updated_at = NOW()
            RETURNING *
            """,
            uuid4(),
            tenant_code,
            base,
            quote,
            resolved_rate,
            rate_date,
            source_system,
            source_reference,
            _json(metadata),
        )

    return _serialize(row)


async def list_fx_rates(
    *,
    tenant_code: str,
    base_currency: str | None = None,
    quote_currency: str | None = None,
    rate_status: str | None = "ACTIVE",
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM fx_rates
            WHERE tenant_code = $1
              AND ($2::text IS NULL OR base_currency = $2)
              AND ($3::text IS NULL OR quote_currency = $3)
              AND ($4::text IS NULL OR rate_status = $4)
            ORDER BY rate_date DESC, created_at DESC
            LIMIT $5
            """,
            tenant_code,
            _currency(base_currency) if base_currency else None,
            _currency(quote_currency) if quote_currency else None,
            rate_status,
            limit,
        )

    return [_serialize(row) for row in rows]


async def get_latest_fx_rate(
    *,
    tenant_code: str,
    source_currency: str,
    target_currency: str,
    as_of_date: date | None = None,
) -> tuple[dict[str, Any], str, Decimal]:
    source, target = _validate_pair(source_currency, target_currency)
    resolved_date = as_of_date or date.today()

    async with db_connection() as conn:
        direct = await conn.fetchrow(
            """
            SELECT *
            FROM fx_rates
            WHERE tenant_code = $1
              AND base_currency = $2
              AND quote_currency = $3
              AND rate_status = 'ACTIVE'
              AND rate_date <= $4
            ORDER BY rate_date DESC, created_at DESC
            LIMIT 1
            """,
            tenant_code,
            source,
            target,
            resolved_date,
        )

        if direct:
            return _serialize(direct), "DIRECT", _decimal(direct["rate"])

        inverse = await conn.fetchrow(
            """
            SELECT *
            FROM fx_rates
            WHERE tenant_code = $1
              AND base_currency = $2
              AND quote_currency = $3
              AND rate_status = 'ACTIVE'
              AND rate_date <= $4
            ORDER BY rate_date DESC, created_at DESC
            LIMIT 1
            """,
            tenant_code,
            target,
            source,
            resolved_date,
        )

    if inverse:
        inverse_rate = Decimal("1") / _decimal(inverse["rate"])
        return _serialize(inverse), "INVERSE", inverse_rate

    raise FxRateNotFound("No active FX rate found for currency pair")


async def quote_currency_conversion(
    *,
    tenant_code: str,
    source_currency: str,
    target_currency: str,
    source_amount: Decimal | int | float | str,
    as_of_date: date | None = None,
    persist_quote: bool = True,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    amount = _decimal(source_amount)
    if amount <= 0:
        raise CurrencyPairError("Source amount must be greater than zero")

    rate_row, direction, effective_rate = await get_latest_fx_rate(
        tenant_code=tenant_code,
        source_currency=source_currency,
        target_currency=target_currency,
        as_of_date=as_of_date,
    )
    target_amount = _money(amount * effective_rate)

    quote = {
        "tenant_code": tenant_code,
        "source_currency": _currency(source_currency),
        "target_currency": _currency(target_currency),
        "source_amount": _money(amount),
        "target_amount": target_amount,
        "fx_rate_id": rate_row["fx_rate_id"],
        "rate": effective_rate,
        "rate_date": rate_row["rate_date"],
        "conversion_direction": direction,
        "metadata": metadata or {},
    }

    if not persist_quote:
        return quote

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO currency_conversion_quotes (
                quote_id,
                tenant_code,
                source_currency,
                target_currency,
                source_amount,
                target_amount,
                fx_rate_id,
                rate,
                rate_date,
                conversion_direction,
                metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb)
            RETURNING *
            """,
            uuid4(),
            quote["tenant_code"],
            quote["source_currency"],
            quote["target_currency"],
            quote["source_amount"],
            quote["target_amount"],
            quote["fx_rate_id"],
            quote["rate"],
            quote["rate_date"],
            quote["conversion_direction"],
            _json(quote["metadata"]),
        )

    return _serialize(row)


async def create_cross_border_settlement(
    *,
    tenant_code: str,
    source_currency: str,
    target_currency: str,
    source_amount: Decimal | int | float | str,
    settlement_id: str | None = None,
    sponsor_code: str | None = None,
    distributor_id: str | None = None,
    as_of_date: date | None = None,
    corridor: str | None = None,
    provider_key: str | None = None,
    provider_reference: str | None = None,
    compliance_status: str = "PENDING",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    quote = await quote_currency_conversion(
        tenant_code=tenant_code,
        source_currency=source_currency,
        target_currency=target_currency,
        source_amount=source_amount,
        as_of_date=as_of_date,
        persist_quote=True,
        metadata=metadata,
    )

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO cross_border_settlements (
                cross_border_settlement_id,
                tenant_code,
                settlement_id,
                sponsor_code,
                distributor_id,
                source_currency,
                target_currency,
                source_amount,
                target_amount,
                fx_rate_id,
                rate,
                rate_date,
                settlement_status,
                corridor,
                provider_key,
                provider_reference,
                compliance_status,
                metadata
            )
            VALUES (
                $1, $2, $3::uuid, $4, $5::uuid, $6, $7, $8, $9, $10,
                $11, $12, 'PENDING', $13, $14, $15, $16, $17::jsonb
            )
            RETURNING *
            """,
            uuid4(),
            tenant_code,
            settlement_id,
            sponsor_code,
            distributor_id,
            quote["source_currency"],
            quote["target_currency"],
            quote["source_amount"],
            quote["target_amount"],
            quote["fx_rate_id"],
            quote["rate"],
            quote["rate_date"],
            corridor,
            provider_key,
            provider_reference,
            compliance_status,
            _json(metadata),
        )

    return _serialize(row)


async def list_cross_border_settlements(
    *,
    tenant_code: str,
    settlement_status: str | None = None,
    sponsor_code: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM cross_border_settlements
            WHERE tenant_code = $1
              AND ($2::text IS NULL OR settlement_status = $2)
              AND ($3::text IS NULL OR sponsor_code = $3)
            ORDER BY created_at DESC
            LIMIT $4
            """,
            tenant_code,
            settlement_status,
            sponsor_code,
            limit,
        )

    return [_serialize(row) for row in rows]
