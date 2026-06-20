from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from utils.db import db_connection


DISTRIBUTOR_STATUS_ONBOARDING = "ONBOARDING"
DISTRIBUTOR_STATUS_ACTIVE = "ACTIVE"
DISTRIBUTOR_STATUS_SUSPENDED = "SUSPENDED"
DISTRIBUTOR_STATUS_TERMINATED = "TERMINATED"


class DistributorError(Exception):
    pass


class DistributorNotFound(DistributorError):
    pass


class DistributorDuplicate(DistributorError):
    pass


def _json(value: dict[str, Any] | None) -> str:
    return json.dumps(value or {})


async def create_distributor(
    *,
    tenant_code: str,
    distributor_code: str,
    distributor_name: str,
    distributor_type: str,
    contact_email: str | None = None,
    contact_phone: str | None = None,
    channels: list[str] | None = None,
    segments: list[str] | None = None,
    regions: list[str] | None = None,
    capabilities: dict[str, Any] | None = None,
    eligibility: dict[str, Any] | None = None,
    operating_limits: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO distribution_distributors (
                distributor_id,
                tenant_code,
                distributor_code,
                distributor_name,
                distributor_type,
                status,
                contact_email,
                contact_phone,
                channels,
                segments,
                regions,
                capabilities,
                eligibility,
                operating_limits,
                metadata
            )
            VALUES (
                $1, $2, $3, $4, $5, 'ONBOARDING', $6, $7,
                $8::text[], $9::text[], $10::text[],
                $11::jsonb, $12::jsonb, $13::jsonb, $14::jsonb
            )
            ON CONFLICT (tenant_code, distributor_code) DO NOTHING
            RETURNING *
            """,
            uuid4(),
            tenant_code,
            distributor_code,
            distributor_name,
            distributor_type,
            contact_email,
            contact_phone,
            channels or [],
            segments or [],
            regions or [],
            _json(capabilities),
            _json(eligibility),
            _json(operating_limits),
            _json(metadata),
        )

    if not row:
        raise DistributorDuplicate("Distributor already exists for tenant")

    return dict(row)


async def list_distributors(
    *,
    tenant_code: str,
    status: str | None = None,
    distributor_type: str | None = None,
    segment: str | None = None,
    region: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM distribution_distributors
            WHERE tenant_code = $1
              AND ($2::text IS NULL OR status = $2)
              AND ($3::text IS NULL OR distributor_type = $3)
              AND ($4::text IS NULL OR $4 = ANY(segments))
              AND ($5::text IS NULL OR $5 = ANY(regions))
            ORDER BY created_at DESC
            LIMIT $6
            """,
            tenant_code,
            status,
            distributor_type,
            segment,
            region,
            limit,
        )

    return [dict(row) for row in rows]


async def get_distributor(
    *,
    distributor_id: str,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM distribution_distributors
            WHERE distributor_id = $1
            """,
            distributor_id,
        )

    if not row:
        raise DistributorNotFound("Distributor not found")

    return dict(row)


async def update_distributor_profile(
    *,
    distributor_id: str,
    distributor_name: str | None = None,
    contact_email: str | None = None,
    contact_phone: str | None = None,
    channels: list[str] | None = None,
    segments: list[str] | None = None,
    regions: list[str] | None = None,
    capabilities: dict[str, Any] | None = None,
    eligibility: dict[str, Any] | None = None,
    operating_limits: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE distribution_distributors
            SET
                distributor_name = COALESCE($2, distributor_name),
                contact_email = COALESCE($3, contact_email),
                contact_phone = COALESCE($4, contact_phone),
                channels = COALESCE($5::text[], channels),
                segments = COALESCE($6::text[], segments),
                regions = COALESCE($7::text[], regions),
                capabilities = COALESCE($8::jsonb, capabilities),
                eligibility = COALESCE($9::jsonb, eligibility),
                operating_limits = COALESCE($10::jsonb, operating_limits),
                metadata = COALESCE($11::jsonb, metadata),
                updated_at = NOW()
            WHERE distributor_id = $1
            RETURNING *
            """,
            distributor_id,
            distributor_name,
            contact_email,
            contact_phone,
            channels,
            segments,
            regions,
            _json(capabilities) if capabilities is not None else None,
            _json(eligibility) if eligibility is not None else None,
            _json(operating_limits) if operating_limits is not None else None,
            _json(metadata) if metadata is not None else None,
        )

    if not row:
        raise DistributorNotFound("Distributor not found")

    return dict(row)


async def set_distributor_status(
    *,
    distributor_id: str,
    status: str,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE distribution_distributors
            SET
                status = $2,
                status_changed_at = NOW(),
                updated_at = NOW()
            WHERE distributor_id = $1
            RETURNING *
            """,
            distributor_id,
            status,
        )

    if not row:
        raise DistributorNotFound("Distributor not found")

    return dict(row)


async def activate_distributor(*, distributor_id: str) -> dict[str, Any]:
    return await set_distributor_status(
        distributor_id=distributor_id,
        status=DISTRIBUTOR_STATUS_ACTIVE,
    )


async def suspend_distributor(*, distributor_id: str) -> dict[str, Any]:
    return await set_distributor_status(
        distributor_id=distributor_id,
        status=DISTRIBUTOR_STATUS_SUSPENDED,
    )


async def terminate_distributor(*, distributor_id: str) -> dict[str, Any]:
    return await set_distributor_status(
        distributor_id=distributor_id,
        status=DISTRIBUTOR_STATUS_TERMINATED,
    )
