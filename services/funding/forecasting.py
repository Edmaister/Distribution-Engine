from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from utils.db import db_connection


DEFAULT_BURN_WINDOW_DAYS = 30
DEFAULT_BUFFER_DAYS = 30


def _money(value: Any) -> Decimal:
    if value is None:
        return Decimal("0.00")

    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def _days_remaining(
    *,
    available_balance: Decimal,
    burn_rate: Decimal,
) -> Decimal | None:
    if burn_rate <= 0:
        return None

    return (available_balance / burn_rate).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def _forecast_status(
    *,
    available_balance: Decimal,
    days_remaining: Decimal | None,
) -> str:
    if available_balance <= 0:
        return "DEPLETED"

    if days_remaining is None:
        return "NO_BURN"

    if days_remaining < Decimal("7"):
        return "CRITICAL"

    if days_remaining < Decimal("15"):
        return "LOW"

    if days_remaining < Decimal("30"):
        return "WATCH"

    return "HEALTHY"


async def get_funding_forecast(
    *,
    account_id: str,
    burn_window_days: int = DEFAULT_BURN_WINDOW_DAYS,
    buffer_days: int = DEFAULT_BUFFER_DAYS,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        account = await conn.fetchrow(
            """
            SELECT
                account_id,
                tenant_code,
                account_name,
                account_type,
                currency_code,
                current_balance,
                reserved_balance,
                available_balance,
                status
            FROM funding_accounts
            WHERE account_id = $1
            """,
            account_id,
        )

        if not account:
            return None

        burn_row = await conn.fetchrow(
            """
            SELECT
                COALESCE(SUM(amount), 0) AS total_burn
            FROM funding_transactions
            WHERE account_id = $1
              AND transaction_type IN (
                    'DEBIT',
                    'RESERVATION',
                    'SETTLEMENT',
                    'FULFILMENT'
              )
              AND created_at >= NOW() - ($2::int * INTERVAL '1 day')
            """,
            account_id,
            burn_window_days,
        )

    current_balance = _money(account["current_balance"])
    reserved_amount = _money(account["reserved_balance"])
    available_balance = _money(account["available_balance"])

    total_burn = _money(burn_row["total_burn"] if burn_row else 0)

    average_burn_rate_per_day = _money(
        total_burn / Decimal(str(burn_window_days))
        if burn_window_days > 0
        else Decimal("0.00")
    )

    days_remaining = _days_remaining(
        available_balance=available_balance,
        burn_rate=average_burn_rate_per_day,
    )

    target_buffer = _money(
        average_burn_rate_per_day * Decimal(str(buffer_days))
    )

    funding_required = _money(
        max(Decimal("0.00"), target_buffer - available_balance)
    )

    return {
        "account_id": str(account["account_id"]),
        "tenant_code": account["tenant_code"],
        "account_name": account["account_name"],
        "account_type": account["account_type"],
        "currency": account["currency_code"],
        "account_status": account["status"],
        "current_balance": current_balance,
        "reserved_amount": reserved_amount,
        "available_balance": available_balance,
        "burn_window_days": burn_window_days,
        "buffer_days": buffer_days,
        "total_burn": total_burn,
        "average_burn_rate_per_day": average_burn_rate_per_day,
        "days_remaining": days_remaining,
        "target_buffer": target_buffer,
        "funding_required": funding_required,
        "recommended_top_up": funding_required,
        "status": _forecast_status(
            available_balance=available_balance,
            days_remaining=days_remaining,
        ),
    }


async def list_funding_forecasts(
    *,
    tenant_code: str | None = None,
    burn_window_days: int = DEFAULT_BURN_WINDOW_DAYS,
    buffer_days: int = DEFAULT_BUFFER_DAYS,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT account_id
            FROM funding_accounts
            WHERE ($1::text IS NULL OR tenant_code = $1)
            ORDER BY tenant_code, account_name, account_id
            LIMIT $2
            """,
            tenant_code,
            limit,
        )

    forecasts: list[dict[str, Any]] = []

    for row in rows:
        forecast = await get_funding_forecast(
            account_id=str(row["account_id"]),
            burn_window_days=burn_window_days,
            buffer_days=buffer_days,
        )

        if forecast:
            forecasts.append(forecast)

    return forecasts


async def get_sponsor_funding_forecast(
    *,
    tenant_code: str,
    sponsor_code: str,
    currency: str = "ZAR",
    burn_window_days: int = DEFAULT_BURN_WINDOW_DAYS,
    buffer_days: int = DEFAULT_BUFFER_DAYS,
) -> dict[str, Any] | None:
    tenant = tenant_code.strip().upper()
    sponsor = sponsor_code.strip().upper()
    resolved_currency = currency.strip().upper()

    async with db_connection() as conn:
        wallet = await conn.fetchrow(
            """
            SELECT
                wallet_id,
                tenant_code,
                sponsor_code,
                sponsor_name,
                currency,
                current_balance,
                reserved_balance,
                status
            FROM sponsor_wallets
            WHERE tenant_code = $1
              AND sponsor_code = $2
              AND currency = $3
            """,
            tenant,
            sponsor,
            resolved_currency,
        )

        if not wallet:
            return None

        wallet_burn = await conn.fetchrow(
            """
            SELECT COALESCE(SUM(amount), 0) AS total_burn
            FROM sponsor_wallet_ledger
            WHERE wallet_id = $1
              AND transaction_type IN ('RESERVE', 'DEBIT')
              AND created_at >= NOW() - ($2::int * INTERVAL '1 day')
            """,
            wallet["wallet_id"],
            burn_window_days,
        )

        contracts = await conn.fetch(
            """
            SELECT
                contract_id,
                contract_name,
                contract_value,
                committed_amount,
                utilised_amount,
                remaining_amount,
                start_date,
                end_date,
                status
            FROM funding_contracts
            WHERE tenant_code = $1
              AND sponsor_code = $2
              AND status = 'ACTIVE'
            ORDER BY end_date ASC, created_at DESC
            """,
            tenant,
            sponsor,
        )

        contract_burn_rows = await conn.fetch(
            """
            SELECT
                l.contract_id,
                COALESCE(SUM(l.amount), 0) AS total_burn
            FROM funding_contract_ledger l
            JOIN funding_contracts c
              ON c.contract_id = l.contract_id
            WHERE c.tenant_code = $1
              AND c.sponsor_code = $2
              AND c.status = 'ACTIVE'
              AND l.event_type IN ('BUDGET_COMMITTED', 'BUDGET_UTILISED')
              AND l.created_at >= NOW() - ($3::int * INTERVAL '1 day')
            GROUP BY l.contract_id
            """,
            tenant,
            sponsor,
            burn_window_days,
        )

    current_balance = _money(wallet["current_balance"])
    reserved_amount = _money(wallet["reserved_balance"])
    available_balance = _money(current_balance - reserved_amount)
    total_wallet_burn = _money(wallet_burn["total_burn"] if wallet_burn else 0)
    wallet_burn_rate = _money(total_wallet_burn / Decimal(str(burn_window_days)))
    wallet_days_remaining = _days_remaining(
        available_balance=available_balance,
        burn_rate=wallet_burn_rate,
    )
    target_buffer = _money(wallet_burn_rate * Decimal(str(buffer_days)))
    recommended_top_up = _money(max(Decimal("0.00"), target_buffer - available_balance))

    contract_burn_by_id = {
        str(row["contract_id"]): _money(row["total_burn"])
        for row in contract_burn_rows
    }
    contract_items = []

    for contract in contracts:
        contract_id = str(contract["contract_id"])
        remaining_amount = _money(contract["remaining_amount"])
        contract_burn = contract_burn_by_id.get(contract_id, Decimal("0.00"))
        contract_burn_rate = _money(contract_burn / Decimal(str(burn_window_days)))
        contract_days_remaining = _days_remaining(
            available_balance=remaining_amount,
            burn_rate=contract_burn_rate,
        )

        contract_items.append(
            {
                "contract_id": contract_id,
                "contract_name": contract["contract_name"],
                "contract_value": _money(contract["contract_value"]),
                "committed_amount": _money(contract["committed_amount"]),
                "utilised_amount": _money(contract["utilised_amount"]),
                "remaining_amount": remaining_amount,
                "start_date": contract["start_date"],
                "end_date": contract["end_date"],
                "status": contract["status"],
                "burn_window_days": burn_window_days,
                "total_burn": contract_burn,
                "average_burn_rate_per_day": contract_burn_rate,
                "days_remaining": contract_days_remaining,
                "forecast_status": _forecast_status(
                    available_balance=remaining_amount,
                    days_remaining=contract_days_remaining,
                ),
            }
        )

    aggregate_contract_remaining = _money(
        sum((item["remaining_amount"] for item in contract_items), Decimal("0.00"))
    )
    aggregate_contract_burn = _money(
        sum((item["total_burn"] for item in contract_items), Decimal("0.00"))
    )
    aggregate_contract_burn_rate = _money(
        aggregate_contract_burn / Decimal(str(burn_window_days))
    )
    aggregate_contract_days_remaining = _days_remaining(
        available_balance=aggregate_contract_remaining,
        burn_rate=aggregate_contract_burn_rate,
    )

    return {
        "tenant_code": tenant,
        "sponsor_code": sponsor,
        "sponsor_name": wallet["sponsor_name"],
        "currency": resolved_currency,
        "burn_window_days": burn_window_days,
        "buffer_days": buffer_days,
        "wallet": {
            "wallet_id": str(wallet["wallet_id"]),
            "status": wallet["status"],
            "current_balance": current_balance,
            "reserved_amount": reserved_amount,
            "available_balance": available_balance,
            "total_burn": total_wallet_burn,
            "average_burn_rate_per_day": wallet_burn_rate,
            "days_remaining": wallet_days_remaining,
            "target_buffer": target_buffer,
            "recommended_top_up": recommended_top_up,
            "forecast_status": _forecast_status(
                available_balance=available_balance,
                days_remaining=wallet_days_remaining,
            ),
        },
        "contracts": {
            "count": len(contract_items),
            "remaining_amount": aggregate_contract_remaining,
            "total_burn": aggregate_contract_burn,
            "average_burn_rate_per_day": aggregate_contract_burn_rate,
            "days_remaining": aggregate_contract_days_remaining,
            "forecast_status": _forecast_status(
                available_balance=aggregate_contract_remaining,
                days_remaining=aggregate_contract_days_remaining,
            ),
            "items": contract_items,
        },
    }


async def list_sponsor_funding_forecasts(
    *,
    tenant_code: str | None = None,
    sponsor_code: str | None = None,
    currency: str = "ZAR",
    burn_window_days: int = DEFAULT_BURN_WINDOW_DAYS,
    buffer_days: int = DEFAULT_BUFFER_DAYS,
    limit: int = 100,
) -> list[dict[str, Any]]:
    tenant = tenant_code.strip().upper() if tenant_code else None
    sponsor = sponsor_code.strip().upper() if sponsor_code else None
    resolved_currency = currency.strip().upper()

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT tenant_code, sponsor_code
            FROM sponsor_wallets
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::text IS NULL OR sponsor_code = $2)
              AND currency = $3
            ORDER BY tenant_code, sponsor_code
            LIMIT $4
            """,
            tenant,
            sponsor,
            resolved_currency,
            limit,
        )

    forecasts: list[dict[str, Any]] = []

    for row in rows:
        forecast = await get_sponsor_funding_forecast(
            tenant_code=row["tenant_code"],
            sponsor_code=row["sponsor_code"],
            currency=resolved_currency,
            burn_window_days=burn_window_days,
            buffer_days=buffer_days,
        )

        if forecast:
            forecasts.append(forecast)

    return forecasts


async def list_settlement_exposure_forecasts(
    *,
    tenant_code: str | None = None,
    provider_key: str | None = None,
    currency: str | None = None,
    burn_window_days: int = DEFAULT_BURN_WINDOW_DAYS,
    buffer_days: int = DEFAULT_BUFFER_DAYS,
    limit: int = 100,
) -> list[dict[str, Any]]:
    tenant = tenant_code.strip().upper() if tenant_code else None
    provider = provider_key.strip().upper() if provider_key else None
    resolved_currency = currency.strip().upper() if currency else None

    async with db_connection() as conn:
        exposure_rows = await conn.fetch(
            """
            SELECT
                tenant_code,
                provider_key,
                currency,
                COUNT(*) AS open_settlement_count,
                COALESCE(SUM(amount), 0) AS current_exposure_amount
            FROM fulfilment_settlement_ledger
            WHERE status IN ('PENDING', 'PROCESSING', 'FAILED', 'DISPUTED')
              AND ($1::text IS NULL OR tenant_code = $1)
              AND ($2::text IS NULL OR provider_key = $2)
              AND ($3::text IS NULL OR currency = $3)
            GROUP BY tenant_code, provider_key, currency
            ORDER BY current_exposure_amount DESC
            LIMIT $4
            """,
            tenant,
            provider,
            resolved_currency,
            limit,
        )

        burn_rows = await conn.fetch(
            """
            SELECT
                tenant_code,
                provider_key,
                currency,
                COUNT(*) AS settled_count,
                COALESCE(SUM(amount), 0) AS settled_amount
            FROM fulfilment_settlement_ledger
            WHERE status = 'SETTLED'
              AND COALESCE(settled_at, updated_at, created_at) >= NOW() - ($4::int * INTERVAL '1 day')
              AND ($1::text IS NULL OR tenant_code = $1)
              AND ($2::text IS NULL OR provider_key = $2)
              AND ($3::text IS NULL OR currency = $3)
            GROUP BY tenant_code, provider_key, currency
            """,
            tenant,
            provider,
            resolved_currency,
            burn_window_days,
        )

    burn_by_key = {
        (
            row["tenant_code"],
            row["provider_key"],
            row["currency"],
        ): row
        for row in burn_rows
    }

    forecasts = []

    for exposure in exposure_rows:
        key = (
            exposure["tenant_code"],
            exposure["provider_key"],
            exposure["currency"],
        )
        burn = burn_by_key.get(key, {})

        current_exposure_amount = _money(exposure["current_exposure_amount"])
        settled_amount = _money(burn.get("settled_amount") or 0)
        average_settlement_rate_per_day = _money(
            settled_amount / Decimal(str(burn_window_days))
        )
        projected_settlement_amount = _money(
            average_settlement_rate_per_day * Decimal(str(buffer_days))
        )
        projected_total_exposure = _money(
            current_exposure_amount + projected_settlement_amount
        )

        forecasts.append(
            {
                "tenant_code": exposure["tenant_code"],
                "provider_key": exposure["provider_key"],
                "currency": exposure["currency"],
                "burn_window_days": burn_window_days,
                "buffer_days": buffer_days,
                "open_settlement_count": int(exposure["open_settlement_count"] or 0),
                "current_exposure_amount": current_exposure_amount,
                "settled_count": int(burn.get("settled_count") or 0),
                "settled_amount": settled_amount,
                "average_settlement_rate_per_day": average_settlement_rate_per_day,
                "projected_settlement_amount": projected_settlement_amount,
                "projected_total_exposure": projected_total_exposure,
                "forecast_status": _forecast_status(
                    available_balance=current_exposure_amount,
                    days_remaining=(
                        Decimal("0.00")
                        if current_exposure_amount > 0
                        else None
                    ),
                ),
            }
        )

    return forecasts
