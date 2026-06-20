from __future__ import annotations

import json
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from utils.db import db_connection


OPPORTUNITY_STATUS_DRAFT = "DRAFT"
OPPORTUNITY_STATUS_PUBLISHED = "PUBLISHED"
OPPORTUNITY_STATUS_CLOSED = "CLOSED"


class OpportunityError(Exception):
    pass


class OpportunityNotFound(OpportunityError):
    pass


class OpportunityDuplicate(OpportunityError):
    pass


class OpportunityInvalidState(OpportunityError):
    pass


def _to_decimal(value: Decimal | int | float | str | None) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


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


async def create_opportunity(
    *,
    tenant_code: str,
    sponsor_code: str,
    opportunity_code: str,
    title: str,
    description: str | None = None,
    campaign_code: str | None = None,
    funding_contract_id: str | None = None,
    product_code: str | None = None,
    product_name: str | None = None,
    target_segments: list[str] | None = None,
    target_regions: list[str] | None = None,
    target_channels: list[str] | None = None,
    distributor_types: list[str] | None = None,
    commission_rule_id: str | None = None,
    estimated_reward_amount: Decimal | int | float | str | None = None,
    estimated_commission_amount: Decimal | int | float | str | None = None,
    total_budget: Decimal | int | float | str | None = None,
    max_allocations: int | None = None,
    starts_at: str | None = None,
    ends_at: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_total_budget = _to_decimal(total_budget)

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO distribution_opportunities (
                opportunity_id,
                tenant_code,
                sponsor_code,
                campaign_code,
                funding_contract_id,
                opportunity_code,
                title,
                description,
                product_code,
                product_name,
                opportunity_status,
                target_segments,
                target_regions,
                target_channels,
                distributor_types,
                commission_rule_id,
                estimated_reward_amount,
                estimated_commission_amount,
                total_budget,
                remaining_budget,
                max_allocations,
                remaining_allocations,
                starts_at,
                ends_at,
                metadata
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                'DRAFT', $11::text[], $12::text[], $13::text[], $14::text[],
                $15, $16, $17, $18, $18, $19, $19, $20, $21, $22::jsonb
            )
            ON CONFLICT (tenant_code, opportunity_code) DO NOTHING
            RETURNING *
            """,
            uuid4(),
            tenant_code,
            sponsor_code,
            campaign_code,
            funding_contract_id,
            opportunity_code,
            title,
            description,
            product_code,
            product_name,
            target_segments or [],
            target_regions or [],
            target_channels or [],
            distributor_types or [],
            commission_rule_id,
            _to_decimal(estimated_reward_amount),
            _to_decimal(estimated_commission_amount),
            resolved_total_budget,
            max_allocations,
            starts_at,
            ends_at,
            _json(metadata),
        )

    if not row:
        raise OpportunityDuplicate("Opportunity already exists for tenant")

    return _serialize(row)


async def list_opportunities(
    *,
    tenant_code: str,
    sponsor_code: str | None = None,
    campaign_code: str | None = None,
    opportunity_status: str | None = None,
    segment: str | None = None,
    region: str | None = None,
    channel: str | None = None,
    distributor_type: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM distribution_opportunities
            WHERE tenant_code = $1
              AND ($2::text IS NULL OR sponsor_code = $2)
              AND ($3::text IS NULL OR campaign_code = $3)
              AND ($4::text IS NULL OR opportunity_status = $4)
              AND ($5::text IS NULL OR $5 = ANY(target_segments))
              AND ($6::text IS NULL OR $6 = ANY(target_regions))
              AND ($7::text IS NULL OR $7 = ANY(target_channels))
              AND ($8::text IS NULL OR $8 = ANY(distributor_types))
            ORDER BY created_at DESC
            LIMIT $9
            """,
            tenant_code,
            sponsor_code,
            campaign_code,
            opportunity_status,
            segment,
            region,
            channel,
            distributor_type,
            limit,
        )

    return [_serialize(row) for row in rows]


async def get_opportunity(*, opportunity_id: str) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM distribution_opportunities
            WHERE opportunity_id = $1
            """,
            opportunity_id,
        )

    if not row:
        raise OpportunityNotFound("Opportunity not found")

    return _serialize(row)


async def update_opportunity(
    *,
    opportunity_id: str,
    title: str | None = None,
    description: str | None = None,
    product_code: str | None = None,
    product_name: str | None = None,
    target_segments: list[str] | None = None,
    target_regions: list[str] | None = None,
    target_channels: list[str] | None = None,
    distributor_types: list[str] | None = None,
    commission_rule_id: str | None = None,
    estimated_reward_amount: Decimal | int | float | str | None = None,
    estimated_commission_amount: Decimal | int | float | str | None = None,
    total_budget: Decimal | int | float | str | None = None,
    max_allocations: int | None = None,
    starts_at: str | None = None,
    ends_at: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE distribution_opportunities
            SET
                title = COALESCE($2, title),
                description = COALESCE($3, description),
                product_code = COALESCE($4, product_code),
                product_name = COALESCE($5, product_name),
                target_segments = COALESCE($6::text[], target_segments),
                target_regions = COALESCE($7::text[], target_regions),
                target_channels = COALESCE($8::text[], target_channels),
                distributor_types = COALESCE($9::text[], distributor_types),
                commission_rule_id = COALESCE($10::uuid, commission_rule_id),
                estimated_reward_amount = COALESCE($11, estimated_reward_amount),
                estimated_commission_amount = COALESCE($12, estimated_commission_amount),
                total_budget = COALESCE($13, total_budget),
                remaining_budget = CASE
                    WHEN $13::numeric IS NULL THEN remaining_budget
                    ELSE $13
                END,
                max_allocations = COALESCE($14, max_allocations),
                remaining_allocations = CASE
                    WHEN $14::integer IS NULL THEN remaining_allocations
                    ELSE $14
                END,
                starts_at = COALESCE($15::timestamp, starts_at),
                ends_at = COALESCE($16::timestamp, ends_at),
                metadata = COALESCE($17::jsonb, metadata),
                updated_at = NOW()
            WHERE opportunity_id = $1
            RETURNING *
            """,
            opportunity_id,
            title,
            description,
            product_code,
            product_name,
            target_segments,
            target_regions,
            target_channels,
            distributor_types,
            commission_rule_id,
            _to_decimal(estimated_reward_amount),
            _to_decimal(estimated_commission_amount),
            _to_decimal(total_budget),
            max_allocations,
            starts_at,
            ends_at,
            _json(metadata) if metadata is not None else None,
        )

    if not row:
        raise OpportunityNotFound("Opportunity not found")

    return _serialize(row)


async def publish_opportunity(*, opportunity_id: str) -> dict[str, Any]:
    return await _set_opportunity_status(
        opportunity_id=opportunity_id,
        status=OPPORTUNITY_STATUS_PUBLISHED,
    )


async def close_opportunity(*, opportunity_id: str) -> dict[str, Any]:
    return await _set_opportunity_status(
        opportunity_id=opportunity_id,
        status=OPPORTUNITY_STATUS_CLOSED,
    )


async def reopen_opportunity(*, opportunity_id: str) -> dict[str, Any]:
    return await _set_opportunity_status(
        opportunity_id=opportunity_id,
        status=OPPORTUNITY_STATUS_PUBLISHED,
    )


async def _set_opportunity_status(
    *,
    opportunity_id: str,
    status: str,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE distribution_opportunities
            SET
                opportunity_status = $2,
                published_at = CASE
                    WHEN $2 = 'PUBLISHED' AND published_at IS NULL THEN NOW()
                    ELSE published_at
                END,
                closed_at = CASE
                    WHEN $2 = 'CLOSED' THEN NOW()
                    WHEN $2 = 'PUBLISHED' THEN NULL
                    ELSE closed_at
                END,
                updated_at = NOW()
            WHERE opportunity_id = $1
            RETURNING *
            """,
            opportunity_id,
            status,
        )

    if not row:
        raise OpportunityNotFound("Opportunity not found")

    return _serialize(row)
