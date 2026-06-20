from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from utils.db import db_connection
from utils.metrics import admin_audit_write_inc

logger = logging.getLogger(__name__)


def _json(value: dict[str, Any] | None) -> str:
    return json.dumps(value or {}, default=str)


def _serialize(row: Any) -> dict[str, Any]:
    result = {
        key: str(value) if isinstance(value, UUID) else value
        for key, value in dict(row).items()
    }

    for key in ("request_payload", "result_payload"):
        if isinstance(result.get(key), str):
            result[key] = json.loads(result[key])

    return result


def actor_from_identity(identity: dict[str, Any] | None) -> dict[str, str | None]:
    identity = identity or {}
    return {
        "actor_role": identity.get("role"),
        "actor_tenant_code": identity.get("tenant_code") or identity.get("tenant"),
        "actor_subject": identity.get("subject") or identity.get("client_id"),
    }


async def write_admin_audit(
    *,
    action_type: str,
    action_domain: str,
    action_status: str = "SUCCESS",
    identity: dict[str, Any] | None = None,
    tenant_code: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    correlation_id: str | None = None,
    reason: str | None = None,
    request_payload: dict[str, Any] | None = None,
    result_payload: dict[str, Any] | None = None,
    error_message: str | None = None,
) -> dict[str, Any]:
    actor = actor_from_identity(identity)

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO admin_audit_log (
                action_type,
                action_domain,
                action_status,
                actor_role,
                actor_tenant_code,
                actor_subject,
                tenant_code,
                target_type,
                target_id,
                correlation_id,
                reason,
                request_payload,
                result_payload,
                error_message
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12::jsonb, $13::jsonb, $14
            )
            RETURNING *
            """,
            action_type,
            action_domain,
            action_status,
            actor["actor_role"],
            actor["actor_tenant_code"],
            actor["actor_subject"],
            tenant_code,
            target_type,
            target_id,
            correlation_id,
            reason,
            _json(request_payload),
            _json(result_payload),
            error_message,
        )

    admin_audit_write_inc(
        action_domain=action_domain,
        action_type=action_type,
        action_status=action_status,
        result="success",
    )
    return _serialize(row)


async def try_write_admin_audit(**kwargs: Any) -> dict[str, Any] | None:
    try:
        return await write_admin_audit(**kwargs)
    except Exception:
        logger.exception("Admin audit write failed")
        admin_audit_write_inc(
            action_domain=kwargs.get("action_domain"),
            action_type=kwargs.get("action_type"),
            action_status=kwargs.get("action_status", "SUCCESS"),
            result="failure",
        )
        return None


async def list_admin_audit(
    *,
    action_domain: str | None = None,
    action_type: str | None = None,
    tenant_code: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM admin_audit_log
            WHERE ($1::text IS NULL OR action_domain = $1)
              AND ($2::text IS NULL OR action_type = $2)
              AND ($3::text IS NULL OR tenant_code = $3)
              AND ($4::text IS NULL OR target_type = $4)
              AND ($5::text IS NULL OR target_id = $5)
            ORDER BY created_at DESC
            LIMIT $6
            """,
            action_domain,
            action_type,
            tenant_code,
            target_type,
            target_id,
            limit,
        )

    return [_serialize(row) for row in rows]


async def get_admin_audit_summary(
    *,
    action_domain: str | None = None,
    tenant_code: str | None = None,
    hours: int = 24,
) -> dict[str, Any]:
    async with db_connection() as conn:
        domain_rows = await conn.fetch(
            """
            SELECT action_domain, COUNT(*)::int AS count
            FROM admin_audit_log
            WHERE created_at >= NOW() - ($1::int * INTERVAL '1 hour')
              AND ($2::text IS NULL OR action_domain = $2)
              AND ($3::text IS NULL OR tenant_code = $3)
            GROUP BY action_domain
            ORDER BY action_domain
            """,
            hours,
            action_domain,
            tenant_code,
        )
        status_rows = await conn.fetch(
            """
            SELECT action_status, COUNT(*)::int AS count
            FROM admin_audit_log
            WHERE created_at >= NOW() - ($1::int * INTERVAL '1 hour')
              AND ($2::text IS NULL OR action_domain = $2)
              AND ($3::text IS NULL OR tenant_code = $3)
            GROUP BY action_status
            ORDER BY action_status
            """,
            hours,
            action_domain,
            tenant_code,
        )
        action_rows = await conn.fetch(
            """
            SELECT action_type, COUNT(*)::int AS count
            FROM admin_audit_log
            WHERE created_at >= NOW() - ($1::int * INTERVAL '1 hour')
              AND ($2::text IS NULL OR action_domain = $2)
              AND ($3::text IS NULL OR tenant_code = $3)
            GROUP BY action_type
            ORDER BY count DESC, action_type
            LIMIT 20
            """,
            hours,
            action_domain,
            tenant_code,
        )

    total = sum(int(row["count"]) for row in domain_rows)
    return {
        "window_hours": hours,
        "action_domain": action_domain,
        "tenant_code": tenant_code,
        "total": total,
        "by_domain": [dict(row) for row in domain_rows],
        "by_status": [dict(row) for row in status_rows],
        "top_actions": [dict(row) for row in action_rows],
    }
