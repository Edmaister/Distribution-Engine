from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from utils.db import db_connection

DEFAULT_RETENTION_DAYS = 1825


def _parse_rowcount(result: str | None) -> int:
    if not result:
        return 0

    try:
        return int(str(result).split()[-1])
    except Exception:
        return 0


def _ensure_naive_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None

    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    return dt


async def _get_retention_days(
    tenant_code: str,
    jurisdiction_code: Optional[str] = None,
) -> int:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT retention_days
            FROM privacy_retention_policies
            WHERE tenant_code = $1
              AND (
                    jurisdiction_code = $2
                    OR jurisdiction_code IS NULL
                  )
              AND is_active = TRUE
            ORDER BY
              CASE WHEN jurisdiction_code = $2 THEN 0 ELSE 1 END,
              created_at DESC
            LIMIT 1
            """,
            tenant_code,
            jurisdiction_code,
        )

    if not row:
        return DEFAULT_RETENTION_DAYS

    return int(row["retention_days"])


async def erase_referrer_by_ucn(
    *,
    referrer_ucn: str,
    tenant_code: str,
    requested_by: str = "admin",
    correlation_id: Optional[str] = None,
    jurisdiction_code: Optional[str] = None,
) -> dict:
    correlation_id = correlation_id or str(uuid4())

    if requested_by == "referee":
        return {
            "status": "blocked",
            "tenant_code": tenant_code,
            "requested_by": requested_by,
            "correlation_id": correlation_id,
            "message": "Referee-initiated erasure is not allowed for referrer records",
        }

    retention_days = await _get_retention_days(
        tenant_code,
        jurisdiction_code,
    )

    async with db_connection() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT referrer_code_id, created_at
                FROM referrer_codes
                WHERE referrer_ucn = $1
                  AND tenant_code = $2
                LIMIT 1
                """,
                referrer_ucn,
                tenant_code,
            )

            if not row:
                await conn.execute(
                    """
                    INSERT INTO privacy_erasure_audit (
                        correlation_id,
                        tenant_code,
                        referrer_code_id,
                        requested_by,
                        status,
                        referral_instances_anonymised,
                        referrer_codes_anonymised,
                        created_at
                    )
                    VALUES ($1, $2, NULL, $3, $4, 0, 0, NOW())
                    """,
                    correlation_id,
                    tenant_code,
                    requested_by,
                    "not_found",
                )

                return {
                    "status": "not_found",
                    "tenant_code": tenant_code,
                    "requested_by": requested_by,
                    "correlation_id": correlation_id,
                }

            referrer_code_id = row["referrer_code_id"]
            created_at = _ensure_naive_utc(row["created_at"])

            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            if created_at and created_at > cutoff_date:
                return {
                    "status": "blocked",
                    "tenant_code": tenant_code,
                    "requested_by": requested_by,
                    "correlation_id": correlation_id,
                    "retention_days": retention_days,
                    "message": "Referrer record is still inside the retention period",
                }

            referral_result = await conn.execute(
                """
                UPDATE referral_instances
                SET
                    referrer_ucn = NULL,
                    referee_ucn = NULL,
                    referee_alias = NULL,
                    referee_alias_normalized = NULL,
                    referee_account_number = NULL,
                    referee_account_masked = NULL,
                    updated_at = NOW()
                WHERE referrer_ucn = $1
                  AND tenant_code = $2
                """,
                referrer_ucn,
                tenant_code,
            )

            referrer_result = await conn.execute(
                """
                UPDATE referrer_codes
                SET
                    referrer_ucn = NULL,
                    referrer_ucn_hash = NULL,
                    gaming_handle = NULL,
                    updated_at = NOW()
                WHERE referrer_ucn = $1
                  AND tenant_code = $2
                """,
                referrer_ucn,
                tenant_code,
            )

            referral_count = _parse_rowcount(referral_result)
            referrer_count = _parse_rowcount(referrer_result)

            await conn.execute(
                """
                INSERT INTO privacy_erasure_audit (
                    correlation_id,
                    tenant_code,
                    referrer_code_id,
                    requested_by,
                    status,
                    referral_instances_anonymised,
                    referrer_codes_anonymised,
                    created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                """,
                correlation_id,
                tenant_code,
                referrer_code_id,
                requested_by,
                "erased",
                referral_count,
                referrer_count,
            )

    return {
        "status": "erased",
        "tenant_code": tenant_code,
        "requested_by": requested_by,
        "correlation_id": correlation_id,
        "referrer_code_id": referrer_code_id,
        "referral_instances_anonymised": referral_count,
        "referrer_codes_anonymised": referrer_count,
    }


async def purge_expired_data(
    tenant_code: str,
    jurisdiction_code: Optional[str] = None,
) -> dict:
    retention_days = await _get_retention_days(
        tenant_code,
        jurisdiction_code,
    )

    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

    async with db_connection() as conn:
        async with conn.transaction():
            referral_result = await conn.execute(
                """
                DELETE FROM referral_instances
                WHERE tenant_code = $1
                  AND created_at < $2
                """,
                tenant_code,
                cutoff_date,
            )

            referrer_result = await conn.execute(
                """
                DELETE FROM referrer_codes
                WHERE tenant_code = $1
                  AND created_at < $2
                """,
                tenant_code,
                cutoff_date,
            )

    return {
        "status": "purged",
        "tenant_code": tenant_code,
        "retention_days": retention_days,
        "cutoff_date": cutoff_date.isoformat(),
        "deleted_referral_instances": _parse_rowcount(referral_result),
        "deleted_referrer_codes": _parse_rowcount(referrer_result),
    }