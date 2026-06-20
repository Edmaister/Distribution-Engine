from __future__ import annotations

import json
from typing import Any
from uuid import UUID, uuid4

from services.distribution.distributor_service import (
    DISTRIBUTOR_STATUS_ACTIVE,
    DISTRIBUTOR_STATUS_SUSPENDED,
    DISTRIBUTOR_STATUS_TERMINATED,
)
from utils.db import db_connection


COMPLIANCE_STATUS_OPEN = "OPEN"
COMPLIANCE_STATUS_COMPLETED = "COMPLETED"

DISPUTE_STATUS_OPEN = "OPEN"
DISPUTE_STATUS_RESOLVED = "RESOLVED"
DISPUTE_STATUS_REJECTED = "REJECTED"

GOVERNANCE_ACTION_SUSPEND = "SUSPEND"
GOVERNANCE_ACTION_REINSTATE = "REINSTATE"
GOVERNANCE_ACTION_TERMINATE = "TERMINATE"
GOVERNANCE_ACTION_UPDATE_LIMITS = "UPDATE_LIMITS"


class GovernanceError(Exception):
    pass


class GovernanceNotFound(GovernanceError):
    pass


class GovernanceInvalidAction(GovernanceError):
    pass


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, default=str)


def _serialize(row: Any) -> dict[str, Any]:
    result = {
        key: str(value) if isinstance(value, UUID) else value
        for key, value in dict(row).items()
    }

    for key in ("metadata", "before_state", "after_state"):
        if isinstance(result.get(key), str):
            result[key] = json.loads(result[key])

    return result


async def _get_distributor(distributor_id: str) -> dict[str, Any]:
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
        raise GovernanceNotFound("Distributor not found")

    return dict(row)


async def create_compliance_review(
    *,
    distributor_id: str,
    review_type: str,
    reviewer: str | None = None,
    notes: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    distributor = await _get_distributor(distributor_id)

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO distribution_compliance_reviews (
                review_id,
                tenant_code,
                distributor_id,
                distributor_code,
                review_type,
                review_status,
                reviewer,
                notes,
                metadata
            )
            VALUES ($1, $2, $3, $4, $5, 'OPEN', $6, $7, $8::jsonb)
            RETURNING *
            """,
            uuid4(),
            distributor["tenant_code"],
            distributor["distributor_id"],
            distributor["distributor_code"],
            review_type,
            reviewer,
            notes,
            _json(metadata),
        )

    return _serialize(row)


async def list_compliance_reviews(
    *,
    tenant_code: str,
    distributor_id: str | None = None,
    review_status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM distribution_compliance_reviews
            WHERE tenant_code = $1
              AND ($2::uuid IS NULL OR distributor_id = $2::uuid)
              AND ($3::text IS NULL OR review_status = $3)
            ORDER BY created_at DESC
            LIMIT $4
            """,
            tenant_code,
            distributor_id,
            review_status,
            limit,
        )

    return [_serialize(row) for row in rows]


async def complete_compliance_review(
    *,
    review_id: str,
    review_result: str,
    reviewer: str | None = None,
    notes: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        async with conn.transaction():
            before = await conn.fetchrow(
                """
                SELECT *
                FROM distribution_compliance_reviews
                WHERE review_id = $1
                FOR UPDATE
                """,
                review_id,
            )

            if not before:
                raise GovernanceNotFound("Compliance review not found")

            row = await conn.fetchrow(
                """
                UPDATE distribution_compliance_reviews
                SET
                    review_status = 'COMPLETED',
                    review_result = $2,
                    reviewer = COALESCE($3, reviewer),
                    notes = COALESCE($4, notes),
                    metadata = metadata || $5::jsonb,
                    reviewed_at = NOW(),
                    updated_at = NOW()
                WHERE review_id = $1
                RETURNING *
                """,
                review_id,
                review_result,
                reviewer,
                notes,
                _json(metadata),
            )

            await _record_audit_with_connection(
                conn=conn,
                tenant_code=row["tenant_code"],
                action_type="COMPLETE_COMPLIANCE_REVIEW",
                compliance_review_id=row["review_id"],
                distributor_id=row["distributor_id"],
                actor=reviewer,
                notes=notes,
                before_state=dict(before),
                after_state=dict(row),
                metadata=metadata,
            )

    return _serialize(row)


async def create_dispute(
    *,
    route_id: str,
    raised_by: str,
    reason_code: str,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        route = await conn.fetchrow(
            """
            SELECT *
            FROM distribution_offer_routes
            WHERE route_id = $1
            """,
            route_id,
        )

        if not route:
            raise GovernanceNotFound("Route not found")

        row = await conn.fetchrow(
            """
            INSERT INTO distribution_disputes (
                dispute_id,
                tenant_code,
                route_id,
                opportunity_id,
                distributor_id,
                raised_by,
                reason_code,
                description,
                metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb)
            RETURNING *
            """,
            uuid4(),
            route["tenant_code"],
            route["route_id"],
            route["opportunity_id"],
            route["distributor_id"],
            raised_by,
            reason_code,
            description,
            _json(metadata),
        )

    return _serialize(row)


async def list_disputes(
    *,
    tenant_code: str,
    distributor_id: str | None = None,
    opportunity_id: str | None = None,
    dispute_status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM distribution_disputes
            WHERE tenant_code = $1
              AND ($2::uuid IS NULL OR distributor_id = $2::uuid)
              AND ($3::uuid IS NULL OR opportunity_id = $3::uuid)
              AND ($4::text IS NULL OR dispute_status = $4)
            ORDER BY created_at DESC
            LIMIT $5
            """,
            tenant_code,
            distributor_id,
            opportunity_id,
            dispute_status,
            limit,
        )

    return [_serialize(row) for row in rows]


async def resolve_dispute(
    *,
    dispute_id: str,
    dispute_status: str = DISPUTE_STATUS_RESOLVED,
    resolved_by: str | None = None,
    resolution_notes: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if dispute_status not in {DISPUTE_STATUS_RESOLVED, DISPUTE_STATUS_REJECTED}:
        raise GovernanceInvalidAction("Dispute can only be resolved or rejected")

    async with db_connection() as conn:
        async with conn.transaction():
            before = await conn.fetchrow(
                """
                SELECT *
                FROM distribution_disputes
                WHERE dispute_id = $1
                FOR UPDATE
                """,
                dispute_id,
            )

            if not before:
                raise GovernanceNotFound("Dispute not found")

            row = await conn.fetchrow(
                """
                UPDATE distribution_disputes
                SET
                    dispute_status = $2,
                    resolved_by = $3,
                    resolution_notes = $4,
                    metadata = metadata || $5::jsonb,
                    resolved_at = NOW(),
                    updated_at = NOW()
                WHERE dispute_id = $1
                RETURNING *
                """,
                dispute_id,
                dispute_status,
                resolved_by,
                resolution_notes,
                _json(metadata),
            )

            await _record_audit_with_connection(
                conn=conn,
                tenant_code=row["tenant_code"],
                action_type="RESOLVE_DISPUTE",
                dispute_id=row["dispute_id"],
                distributor_id=row["distributor_id"],
                route_id=row["route_id"],
                actor=resolved_by,
                notes=resolution_notes,
                before_state=dict(before),
                after_state=dict(row),
                metadata=metadata,
            )

    return _serialize(row)


async def apply_distributor_governance_action(
    *,
    distributor_id: str,
    action_type: str,
    reason_code: str | None = None,
    actor: str | None = None,
    notes: str | None = None,
    operating_limits: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if action_type not in {
        GOVERNANCE_ACTION_SUSPEND,
        GOVERNANCE_ACTION_REINSTATE,
        GOVERNANCE_ACTION_TERMINATE,
        GOVERNANCE_ACTION_UPDATE_LIMITS,
    }:
        raise GovernanceInvalidAction("Unsupported governance action")

    async with db_connection() as conn:
        async with conn.transaction():
            before = await conn.fetchrow(
                """
                SELECT *
                FROM distribution_distributors
                WHERE distributor_id = $1
                FOR UPDATE
                """,
                distributor_id,
            )

            if not before:
                raise GovernanceNotFound("Distributor not found")

            status = before["status"]
            if action_type == GOVERNANCE_ACTION_SUSPEND:
                status = DISTRIBUTOR_STATUS_SUSPENDED
            elif action_type == GOVERNANCE_ACTION_REINSTATE:
                status = DISTRIBUTOR_STATUS_ACTIVE
            elif action_type == GOVERNANCE_ACTION_TERMINATE:
                status = DISTRIBUTOR_STATUS_TERMINATED

            row = await conn.fetchrow(
                """
                UPDATE distribution_distributors
                SET
                    status = $2,
                    operating_limits = CASE
                        WHEN $3::jsonb IS NULL THEN operating_limits
                        ELSE $3::jsonb
                    END,
                    metadata = metadata || $4::jsonb,
                    status_changed_at = CASE
                        WHEN $2 <> status THEN NOW()
                        ELSE status_changed_at
                    END,
                    updated_at = NOW()
                WHERE distributor_id = $1
                RETURNING *
                """,
                distributor_id,
                status,
                _json(operating_limits) if operating_limits is not None else None,
                _json(
                    {
                        "last_governance_action": action_type,
                        "last_governance_reason": reason_code,
                        **(metadata or {}),
                    }
                ),
            )

            audit = await _record_audit_with_connection(
                conn=conn,
                tenant_code=row["tenant_code"],
                action_type=action_type,
                distributor_id=row["distributor_id"],
                reason_code=reason_code,
                actor=actor,
                notes=notes,
                before_state=dict(before),
                after_state=dict(row),
                metadata=metadata,
            )

    return {
        "distributor": _serialize(row),
        "audit": _serialize(audit),
    }


async def list_governance_audit(
    *,
    tenant_code: str,
    distributor_id: str | None = None,
    action_type: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM distribution_governance_audit
            WHERE tenant_code = $1
              AND ($2::uuid IS NULL OR distributor_id = $2::uuid)
              AND ($3::text IS NULL OR action_type = $3)
            ORDER BY created_at DESC
            LIMIT $4
            """,
            tenant_code,
            distributor_id,
            action_type,
            limit,
        )

    return [_serialize(row) for row in rows]


async def _record_audit_with_connection(
    *,
    conn,
    tenant_code: str,
    action_type: str,
    distributor_id: str | None = None,
    route_id: str | None = None,
    dispute_id: str | None = None,
    compliance_review_id: str | None = None,
    reason_code: str | None = None,
    actor: str | None = None,
    notes: str | None = None,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
):
    return await conn.fetchrow(
        """
        INSERT INTO distribution_governance_audit (
            audit_id,
            tenant_code,
            distributor_id,
            route_id,
            dispute_id,
            compliance_review_id,
            action_type,
            reason_code,
            actor,
            notes,
            before_state,
            after_state,
            metadata
        )
        VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            $11::jsonb, $12::jsonb, $13::jsonb
        )
        RETURNING *
        """,
        uuid4(),
        tenant_code,
        distributor_id,
        route_id,
        dispute_id,
        compliance_review_id,
        action_type,
        reason_code,
        actor,
        notes,
        _json(before_state),
        _json(after_state),
        _json(metadata),
    )
