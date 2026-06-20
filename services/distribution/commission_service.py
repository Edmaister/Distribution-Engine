from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID, uuid4

from services.distribution.distributor_wallet_service import credit_distributor_wallet
from utils.db import db_connection


RULE_STATUS_ACTIVE = "ACTIVE"
COMMISSION_STATUS_CALCULATED = "CALCULATED"
COMMISSION_STATUS_CREDITED = "CREDITED"


class CommissionError(Exception):
    pass


class CommissionRuleNotFound(CommissionError):
    pass


class CommissionDistributorNotFound(CommissionError):
    pass


class CommissionWalletNotFound(CommissionError):
    pass


class CommissionDuplicateEvent(CommissionError):
    pass


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
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


async def create_commission_rule(
    *,
    tenant_code: str,
    commission_type: str,
    sponsor_code: str | None = None,
    campaign_code: str | None = None,
    distributor_type: str | None = None,
    rate: Decimal | int | float | str | None = None,
    fixed_amount: Decimal | int | float | str | None = None,
    min_commission: Decimal | int | float | str | None = None,
    max_commission: Decimal | int | float | str | None = None,
    currency: str = "ZAR",
    priority: int = 100,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO distribution_commission_rules (
                rule_id,
                tenant_code,
                sponsor_code,
                campaign_code,
                distributor_type,
                commission_type,
                rate,
                fixed_amount,
                min_commission,
                max_commission,
                currency,
                rule_status,
                priority,
                description,
                metadata
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, 'ACTIVE', $12, $13, $14::jsonb
            )
            RETURNING *
            """,
            uuid4(),
            tenant_code,
            sponsor_code,
            campaign_code,
            distributor_type,
            commission_type,
            _to_decimal(rate) if rate is not None else None,
            _to_decimal(fixed_amount) if fixed_amount is not None else None,
            _to_decimal(min_commission) if min_commission is not None else None,
            _to_decimal(max_commission) if max_commission is not None else None,
            currency,
            priority,
            description,
            _json(metadata),
        )

    return _serialize(row)


async def list_commission_rules(
    *,
    tenant_code: str,
    sponsor_code: str | None = None,
    campaign_code: str | None = None,
    distributor_type: str | None = None,
    rule_status: str | None = RULE_STATUS_ACTIVE,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM distribution_commission_rules
            WHERE tenant_code = $1
              AND ($2::text IS NULL OR sponsor_code = $2)
              AND ($3::text IS NULL OR campaign_code = $3)
              AND ($4::text IS NULL OR distributor_type = $4)
              AND ($5::text IS NULL OR rule_status = $5)
            ORDER BY priority ASC, created_at DESC
            LIMIT $6
            """,
            tenant_code,
            sponsor_code,
            campaign_code,
            distributor_type,
            rule_status,
            limit,
        )

    return [_serialize(row) for row in rows]


async def calculate_commission(
    *,
    tenant_code: str,
    distributor_id: str,
    activity_type: str,
    sale_amount: Decimal | int | float | str = 0,
    sponsor_code: str | None = None,
    campaign_code: str | None = None,
    source_event_id: str | None = None,
    wallet_id: str | None = None,
    credit_wallet: bool = False,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_sale_amount = _to_decimal(sale_amount)

    async with db_connection() as conn:
        distributor = await conn.fetchrow(
            """
            SELECT distributor_id, tenant_code, distributor_code, distributor_type
            FROM distribution_distributors
            WHERE distributor_id = $1
              AND tenant_code = $2
            """,
            distributor_id,
            tenant_code,
        )

        if not distributor:
            raise CommissionDistributorNotFound("Distributor not found")

        rule = await conn.fetchrow(
            """
            SELECT *
            FROM distribution_commission_rules
            WHERE tenant_code = $1
              AND rule_status = 'ACTIVE'
              AND (sponsor_code IS NULL OR sponsor_code = $2)
              AND (campaign_code IS NULL OR campaign_code = $3)
              AND (distributor_type IS NULL OR distributor_type = $4)
            ORDER BY
              CASE WHEN sponsor_code IS NULL THEN 1 ELSE 0 END,
              CASE WHEN campaign_code IS NULL THEN 1 ELSE 0 END,
              CASE WHEN distributor_type IS NULL THEN 1 ELSE 0 END,
              priority ASC,
              created_at DESC
            LIMIT 1
            """,
            tenant_code,
            sponsor_code,
            campaign_code,
            distributor["distributor_type"],
        )

        if not rule:
            raise CommissionRuleNotFound("No active commission rule matched")

        resolved_wallet_id = wallet_id
        if credit_wallet and not resolved_wallet_id:
            wallet = await conn.fetchrow(
                """
                SELECT wallet_id
                FROM distribution_distributor_wallets
                WHERE distributor_id = $1
                  AND currency = $2
                  AND status = 'ACTIVE'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                distributor_id,
                rule["currency"],
            )

            if not wallet:
                raise CommissionWalletNotFound("Distributor wallet not found")

            resolved_wallet_id = str(wallet["wallet_id"])

        commission_amount = _calculate_amount(
            rule=rule,
            sale_amount=resolved_sale_amount,
        )

        event = await conn.fetchrow(
            """
            INSERT INTO distribution_commission_events (
                commission_event_id,
                tenant_code,
                distributor_id,
                distributor_code,
                wallet_id,
                rule_id,
                sponsor_code,
                campaign_code,
                source_event_id,
                activity_type,
                sale_amount,
                commission_amount,
                currency,
                commission_status,
                correlation_id,
                metadata
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, 'CALCULATED', $14, $15::jsonb
            )
            ON CONFLICT (tenant_code, source_event_id) DO NOTHING
            RETURNING *
            """,
            uuid4(),
            tenant_code,
            distributor["distributor_id"],
            distributor["distributor_code"],
            resolved_wallet_id,
            rule["rule_id"],
            sponsor_code,
            campaign_code,
            source_event_id,
            activity_type,
            resolved_sale_amount,
            commission_amount,
            rule["currency"],
            correlation_id,
            _json(metadata),
        )

    if not event:
        raise CommissionDuplicateEvent("Commission event already exists")

    event_dict = _serialize(event)
    credited_wallet = None

    if credit_wallet:
        credited_wallet = await credit_distributor_wallet(
            wallet_id=event_dict["wallet_id"],
            amount=commission_amount,
            correlation_id=correlation_id,
            metadata={
                "commission_event_id": event_dict["commission_event_id"],
                "source_event_id": source_event_id,
            },
        )

        async with db_connection() as conn:
            updated = await conn.fetchrow(
                """
                UPDATE distribution_commission_events
                SET
                    commission_status = 'CREDITED',
                    credited_at = NOW(),
                    updated_at = NOW()
                WHERE commission_event_id = $1
                RETURNING *
                """,
                event_dict["commission_event_id"],
            )

        event_dict = _serialize(updated)

    return {
        "commission_event": event_dict,
        "rule": _serialize(rule),
        "wallet": credited_wallet,
    }


async def list_commission_events(
    *,
    tenant_code: str,
    distributor_id: str | None = None,
    commission_status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM distribution_commission_events
            WHERE tenant_code = $1
              AND ($2::uuid IS NULL OR distributor_id = $2)
              AND ($3::text IS NULL OR commission_status = $3)
            ORDER BY created_at DESC
            LIMIT $4
            """,
            tenant_code,
            distributor_id,
            commission_status,
            limit,
        )

    return [_serialize(row) for row in rows]


def _calculate_amount(*, rule: Any, sale_amount: Decimal) -> Decimal:
    commission_type = rule["commission_type"]

    if commission_type == "PERCENTAGE":
        amount = sale_amount * _to_decimal(rule["rate"] or 0)
    elif commission_type == "FIXED":
        amount = _to_decimal(rule["fixed_amount"] or 0)
    elif commission_type == "HYBRID":
        amount = _to_decimal(rule["fixed_amount"] or 0)
        amount += sale_amount * _to_decimal(rule["rate"] or 0)
    else:
        raise CommissionError("Unsupported commission type")

    min_commission = rule["min_commission"]
    max_commission = rule["max_commission"]

    if min_commission is not None:
        amount = max(amount, _to_decimal(min_commission))

    if max_commission is not None:
        amount = min(amount, _to_decimal(max_commission))

    return _money(amount)
