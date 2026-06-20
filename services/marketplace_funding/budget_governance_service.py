from __future__ import annotations

import json
from decimal import Decimal
from typing import Any
from uuid import uuid4

from utils.db import db_connection


REQUEST_STATUS_PENDING = "PENDING"
REQUEST_STATUS_APPROVED = "APPROVED"
REQUEST_STATUS_REJECTED = "REJECTED"
EXCEPTION_STATUS_OPEN = "OPEN"
EXCEPTION_STATUS_RESOLVED = "RESOLVED"
EXCEPTION_STATUS_WAIVED = "WAIVED"
POLICY_STATUS_ACTIVE = "ACTIVE"
DEFAULT_APPROVAL_LEVEL = "STANDARD"


class BudgetGovernanceError(Exception):
    pass


class BudgetAdjustmentRequestNotFound(BudgetGovernanceError):
    pass


class BudgetAdjustmentRequestInvalidState(BudgetGovernanceError):
    pass


class BudgetAdjustmentContractNotFound(BudgetGovernanceError):
    pass


class BudgetTransferRequestInvalidState(BudgetGovernanceError):
    pass


class BudgetTransferContractNotFound(BudgetGovernanceError):
    pass


class BudgetTransferInvalid(BudgetGovernanceError):
    pass


class BudgetTransferInsufficientBudget(BudgetGovernanceError):
    pass


class BudgetExceptionInvalidState(BudgetGovernanceError):
    pass


class BudgetExceptionContractNotFound(BudgetGovernanceError):
    pass


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value))


async def create_budget_approval_policy(
    *,
    tenant_code: str,
    request_type: str,
    approval_level: str,
    sponsor_code: str | None = None,
    min_amount: Decimal | int | float | str = 0,
    max_amount: Decimal | int | float | str | None = None,
    required_role: str | None = None,
    priority: int = 100,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_min_amount = _to_decimal(min_amount)
    resolved_max_amount = _to_decimal(max_amount) if max_amount is not None else None

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO funding_budget_approval_policies (
                policy_id,
                tenant_code,
                sponsor_code,
                request_type,
                min_amount,
                max_amount,
                approval_level,
                required_role,
                policy_status,
                priority,
                description,
                metadata
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8,
                'ACTIVE', $9, $10, $11::jsonb
            )
            RETURNING *
            """,
            uuid4(),
            tenant_code,
            sponsor_code,
            request_type,
            resolved_min_amount,
            resolved_max_amount,
            approval_level,
            required_role,
            priority,
            description,
            json.dumps(metadata or {}),
        )

    return dict(row)


async def list_budget_approval_policies(
    *,
    tenant_code: str | None = None,
    sponsor_code: str | None = None,
    request_type: str | None = None,
    policy_status: str | None = POLICY_STATUS_ACTIVE,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM funding_budget_approval_policies
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::text IS NULL OR sponsor_code = $2)
              AND ($3::text IS NULL OR request_type = $3)
              AND ($4::text IS NULL OR policy_status = $4)
            ORDER BY priority ASC, min_amount DESC, created_at DESC
            LIMIT $5
            """,
            tenant_code,
            sponsor_code,
            request_type,
            policy_status,
            limit,
        )

    return [dict(row) for row in rows]


async def evaluate_budget_approval_policy(
    *,
    tenant_code: str,
    request_type: str,
    amount: Decimal | int | float | str,
    sponsor_code: str | None = None,
) -> dict[str, Any]:
    resolved_amount = _to_decimal(amount)

    async with db_connection() as conn:
        policy = await conn.fetchrow(
            """
            SELECT *
            FROM funding_budget_approval_policies
            WHERE tenant_code = $1
              AND request_type = $2
              AND policy_status = 'ACTIVE'
              AND (sponsor_code IS NULL OR sponsor_code = $3)
              AND min_amount <= $4
              AND (max_amount IS NULL OR max_amount >= $4)
            ORDER BY
              CASE WHEN sponsor_code IS NULL THEN 1 ELSE 0 END,
              priority ASC,
              min_amount DESC,
              created_at DESC
            LIMIT 1
            """,
            tenant_code,
            request_type,
            sponsor_code,
            resolved_amount,
        )

    matched_policy = dict(policy) if policy else None

    return {
        "tenant_code": tenant_code,
        "sponsor_code": sponsor_code,
        "request_type": request_type,
        "amount": resolved_amount,
        "approval_level": (
            matched_policy["approval_level"]
            if matched_policy
            else DEFAULT_APPROVAL_LEVEL
        ),
        "required_role": matched_policy["required_role"] if matched_policy else None,
        "policy_required": bool(matched_policy),
        "matched_policy": matched_policy,
    }


async def create_budget_adjustment_request(
    *,
    contract_id: str,
    requested_amount: Decimal | int | float | str,
    reason: str | None = None,
    requested_by: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    amount = _to_decimal(requested_amount)

    async with db_connection() as conn:
        contract = await conn.fetchrow(
            """
            SELECT contract_id, tenant_code, sponsor_code
            FROM funding_contracts
            WHERE contract_id = $1
            """,
            contract_id,
        )

        if not contract:
            raise BudgetAdjustmentContractNotFound("Funding contract not found")

        row = await conn.fetchrow(
            """
            INSERT INTO funding_budget_adjustment_requests (
                request_id,
                contract_id,
                tenant_code,
                sponsor_code,
                adjustment_type,
                requested_amount,
                reason,
                request_status,
                requested_by,
                correlation_id,
                metadata
            )
            VALUES ($1, $2, $3, $4, 'INCREASE', $5, $6, 'PENDING', $7, $8, $9::jsonb)
            RETURNING *
            """,
            uuid4(),
            contract["contract_id"],
            contract["tenant_code"],
            contract["sponsor_code"],
            amount,
            reason,
            requested_by,
            correlation_id,
            json.dumps(metadata or {}),
        )

    return dict(row)


async def list_budget_adjustment_requests(
    *,
    tenant_code: str | None = None,
    sponsor_code: str | None = None,
    contract_id: str | None = None,
    request_status: str | None = REQUEST_STATUS_PENDING,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM funding_budget_adjustment_requests
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::text IS NULL OR sponsor_code = $2)
              AND ($3::uuid IS NULL OR contract_id = $3)
              AND ($4::text IS NULL OR request_status = $4)
            ORDER BY created_at DESC
            LIMIT $5
            """,
            tenant_code,
            sponsor_code,
            contract_id,
            request_status,
            limit,
        )

    return [dict(row) for row in rows]


async def approve_budget_adjustment_request(
    *,
    request_id: str,
    decided_by: str | None = None,
    decision_reason: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        async with conn.transaction():
            request = await conn.fetchrow(
                """
                SELECT *
                FROM funding_budget_adjustment_requests
                WHERE request_id = $1
                  AND request_status = 'PENDING'
                FOR UPDATE
                """,
                request_id,
            )

            if not request:
                raise BudgetAdjustmentRequestInvalidState(
                    "Budget adjustment request is not pending"
                )

            amount = _to_decimal(request["requested_amount"])

            contract = await conn.fetchrow(
                """
                UPDATE funding_contracts
                SET
                    contract_value = contract_value + $2,
                    remaining_amount = remaining_amount + $2,
                    updated_at = NOW()
                WHERE contract_id = $1
                RETURNING *
                """,
                request["contract_id"],
                amount,
            )

            if not contract:
                raise BudgetAdjustmentContractNotFound("Funding contract not found")

            updated_request = await conn.fetchrow(
                """
                UPDATE funding_budget_adjustment_requests
                SET
                    request_status = 'APPROVED',
                    decided_by = $2,
                    decision_reason = $3,
                    decided_at = NOW(),
                    updated_at = NOW()
                WHERE request_id = $1
                RETURNING *
                """,
                request_id,
                decided_by,
                decision_reason,
            )

            await conn.fetchrow(
                """
                INSERT INTO funding_contract_ledger (
                    contract_id,
                    event_type,
                    amount,
                    correlation_id,
                    metadata
                )
                VALUES ($1, 'BUDGET_INCREASE_APPROVED', $2, $3, $4::jsonb)
                RETURNING *
                """,
                request["contract_id"],
                amount,
                request["correlation_id"],
                json.dumps(
                    {
                        "request_id": str(request["request_id"]),
                        "approved_by": decided_by,
                        "decision_reason": decision_reason,
                    }
                ),
            )

    return {
        "request": dict(updated_request),
        "contract": dict(contract),
    }


async def reject_budget_adjustment_request(
    *,
    request_id: str,
    decided_by: str | None = None,
    decision_reason: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE funding_budget_adjustment_requests
            SET
                request_status = 'REJECTED',
                decided_by = $2,
                decision_reason = $3,
                decided_at = NOW(),
                updated_at = NOW()
            WHERE request_id = $1
              AND request_status = 'PENDING'
            RETURNING *
            """,
            request_id,
            decided_by,
            decision_reason,
        )

    if not row:
        raise BudgetAdjustmentRequestInvalidState(
            "Budget adjustment request is not pending"
        )

    return dict(row)


async def create_budget_transfer_request(
    *,
    source_contract_id: str,
    target_contract_id: str,
    requested_amount: Decimal | int | float | str,
    reason: str | None = None,
    requested_by: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if source_contract_id == target_contract_id:
        raise BudgetTransferInvalid("Source and target contracts must differ")

    amount = _to_decimal(requested_amount)

    async with db_connection() as conn:
        contracts = await conn.fetch(
            """
            SELECT contract_id, tenant_code, sponsor_code
            FROM funding_contracts
            WHERE contract_id IN ($1, $2)
            """,
            source_contract_id,
            target_contract_id,
        )

        contracts_by_id = {
            str(contract["contract_id"]): contract
            for contract in contracts
        }
        source_contract = contracts_by_id.get(source_contract_id)
        target_contract = contracts_by_id.get(target_contract_id)

        if not source_contract or not target_contract:
            raise BudgetTransferContractNotFound("Funding contract not found")

        if source_contract["tenant_code"] != target_contract["tenant_code"]:
            raise BudgetTransferInvalid("Budget transfers must stay within one tenant")

        row = await conn.fetchrow(
            """
            INSERT INTO funding_budget_transfer_requests (
                request_id,
                source_contract_id,
                target_contract_id,
                tenant_code,
                source_sponsor_code,
                target_sponsor_code,
                requested_amount,
                reason,
                request_status,
                requested_by,
                correlation_id,
                metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'PENDING', $9, $10, $11::jsonb)
            RETURNING *
            """,
            uuid4(),
            source_contract["contract_id"],
            target_contract["contract_id"],
            source_contract["tenant_code"],
            source_contract["sponsor_code"],
            target_contract["sponsor_code"],
            amount,
            reason,
            requested_by,
            correlation_id,
            json.dumps(metadata or {}),
        )

    return dict(row)


async def list_budget_transfer_requests(
    *,
    tenant_code: str | None = None,
    source_contract_id: str | None = None,
    target_contract_id: str | None = None,
    request_status: str | None = REQUEST_STATUS_PENDING,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM funding_budget_transfer_requests
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::uuid IS NULL OR source_contract_id = $2)
              AND ($3::uuid IS NULL OR target_contract_id = $3)
              AND ($4::text IS NULL OR request_status = $4)
            ORDER BY created_at DESC
            LIMIT $5
            """,
            tenant_code,
            source_contract_id,
            target_contract_id,
            request_status,
            limit,
        )

    return [dict(row) for row in rows]


async def approve_budget_transfer_request(
    *,
    request_id: str,
    decided_by: str | None = None,
    decision_reason: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        async with conn.transaction():
            request = await conn.fetchrow(
                """
                SELECT *
                FROM funding_budget_transfer_requests
                WHERE request_id = $1
                  AND request_status = 'PENDING'
                FOR UPDATE
                """,
                request_id,
            )

            if not request:
                raise BudgetTransferRequestInvalidState(
                    "Budget transfer request is not pending"
                )

            amount = _to_decimal(request["requested_amount"])

            source_contract = await conn.fetchrow(
                """
                UPDATE funding_contracts
                SET
                    contract_value = contract_value - $2,
                    remaining_amount = remaining_amount - $2,
                    updated_at = NOW()
                WHERE contract_id = $1
                  AND remaining_amount >= $2
                RETURNING *
                """,
                request["source_contract_id"],
                amount,
            )

            if not source_contract:
                raise BudgetTransferInsufficientBudget(
                    "Source contract has insufficient remaining budget"
                )

            target_contract = await conn.fetchrow(
                """
                UPDATE funding_contracts
                SET
                    contract_value = contract_value + $2,
                    remaining_amount = remaining_amount + $2,
                    updated_at = NOW()
                WHERE contract_id = $1
                RETURNING *
                """,
                request["target_contract_id"],
                amount,
            )

            if not target_contract:
                raise BudgetTransferContractNotFound("Funding contract not found")

            updated_request = await conn.fetchrow(
                """
                UPDATE funding_budget_transfer_requests
                SET
                    request_status = 'APPROVED',
                    decided_by = $2,
                    decision_reason = $3,
                    decided_at = NOW(),
                    updated_at = NOW()
                WHERE request_id = $1
                RETURNING *
                """,
                request_id,
                decided_by,
                decision_reason,
            )

            metadata = {
                "request_id": str(request["request_id"]),
                "approved_by": decided_by,
                "decision_reason": decision_reason,
                "source_contract_id": str(request["source_contract_id"]),
                "target_contract_id": str(request["target_contract_id"]),
            }

            await conn.fetchrow(
                """
                INSERT INTO funding_contract_ledger (
                    contract_id,
                    event_type,
                    amount,
                    correlation_id,
                    metadata
                )
                VALUES ($1, 'BUDGET_TRANSFER_OUT_APPROVED', $2, $3, $4::jsonb)
                RETURNING *
                """,
                request["source_contract_id"],
                amount,
                request["correlation_id"],
                json.dumps(metadata),
            )
            await conn.fetchrow(
                """
                INSERT INTO funding_contract_ledger (
                    contract_id,
                    event_type,
                    amount,
                    correlation_id,
                    metadata
                )
                VALUES ($1, 'BUDGET_TRANSFER_IN_APPROVED', $2, $3, $4::jsonb)
                RETURNING *
                """,
                request["target_contract_id"],
                amount,
                request["correlation_id"],
                json.dumps(metadata),
            )

    return {
        "request": dict(updated_request),
        "source_contract": dict(source_contract),
        "target_contract": dict(target_contract),
    }


async def reject_budget_transfer_request(
    *,
    request_id: str,
    decided_by: str | None = None,
    decision_reason: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE funding_budget_transfer_requests
            SET
                request_status = 'REJECTED',
                decided_by = $2,
                decision_reason = $3,
                decided_at = NOW(),
                updated_at = NOW()
            WHERE request_id = $1
              AND request_status = 'PENDING'
            RETURNING *
            """,
            request_id,
            decided_by,
            decision_reason,
        )

    if not row:
        raise BudgetTransferRequestInvalidState(
            "Budget transfer request is not pending"
        )

    return dict(row)


async def create_budget_exception(
    *,
    tenant_code: str,
    exception_type: str,
    exception_message: str,
    severity: str = "WARNING",
    sponsor_code: str | None = None,
    contract_id: str | None = None,
    amount: Decimal | int | float | str | None = None,
    detected_by: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_amount = _to_decimal(amount) if amount is not None else None

    async with db_connection() as conn:
        resolved_tenant = tenant_code
        resolved_sponsor = sponsor_code

        if contract_id:
            contract = await conn.fetchrow(
                """
                SELECT contract_id, tenant_code, sponsor_code
                FROM funding_contracts
                WHERE contract_id = $1
                """,
                contract_id,
            )

            if not contract:
                raise BudgetExceptionContractNotFound("Funding contract not found")

            resolved_tenant = contract["tenant_code"]
            resolved_sponsor = contract["sponsor_code"]

        row = await conn.fetchrow(
            """
            INSERT INTO funding_budget_exceptions (
                exception_id,
                contract_id,
                tenant_code,
                sponsor_code,
                exception_type,
                severity,
                exception_message,
                amount,
                exception_status,
                detected_by,
                correlation_id,
                metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'OPEN', $9, $10, $11::jsonb)
            RETURNING *
            """,
            uuid4(),
            contract_id,
            resolved_tenant,
            resolved_sponsor,
            exception_type,
            severity,
            exception_message,
            resolved_amount,
            detected_by,
            correlation_id,
            json.dumps(metadata or {}),
        )

    return dict(row)


async def list_budget_exceptions(
    *,
    tenant_code: str | None = None,
    sponsor_code: str | None = None,
    contract_id: str | None = None,
    exception_status: str | None = EXCEPTION_STATUS_OPEN,
    exception_type: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM funding_budget_exceptions
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::text IS NULL OR sponsor_code = $2)
              AND ($3::uuid IS NULL OR contract_id = $3)
              AND ($4::text IS NULL OR exception_status = $4)
              AND ($5::text IS NULL OR exception_type = $5)
            ORDER BY created_at DESC
            LIMIT $6
            """,
            tenant_code,
            sponsor_code,
            contract_id,
            exception_status,
            exception_type,
            limit,
        )

    return [dict(row) for row in rows]


async def resolve_budget_exception(
    *,
    exception_id: str,
    resolved_by: str | None = None,
    resolution_reason: str | None = None,
) -> dict[str, Any]:
    return await _close_budget_exception(
        exception_id=exception_id,
        exception_status=EXCEPTION_STATUS_RESOLVED,
        resolved_by=resolved_by,
        resolution_reason=resolution_reason,
    )


async def waive_budget_exception(
    *,
    exception_id: str,
    resolved_by: str | None = None,
    resolution_reason: str | None = None,
) -> dict[str, Any]:
    return await _close_budget_exception(
        exception_id=exception_id,
        exception_status=EXCEPTION_STATUS_WAIVED,
        resolved_by=resolved_by,
        resolution_reason=resolution_reason,
    )


async def _close_budget_exception(
    *,
    exception_id: str,
    exception_status: str,
    resolved_by: str | None = None,
    resolution_reason: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE funding_budget_exceptions
            SET
                exception_status = $2,
                resolved_by = $3,
                resolution_reason = $4,
                resolved_at = NOW(),
                updated_at = NOW()
            WHERE exception_id = $1
              AND exception_status = 'OPEN'
            RETURNING *
            """,
            exception_id,
            exception_status,
            resolved_by,
            resolution_reason,
        )

    if not row:
        raise BudgetExceptionInvalidState("Budget exception is not open")

    return dict(row)
