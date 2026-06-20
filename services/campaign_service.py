from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from utils.db import db_connection


def _normalize(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _generate_campaign_code(
    tenant_code: Optional[str],
    segment: str,
    name: str,
) -> str:
    tenant = (_normalize(tenant_code) or "GEN").upper()
    seg = (_normalize(segment) or "GENERAL").upper().replace(" ", "-")
    nm = (_normalize(name) or "CAMPAIGN").upper().replace(" ", "-")
    token = str(uuid4())[:8].upper()
    return f"{tenant}-{seg}-{nm[:30]}-{token}"


async def create_campaign(
    *,
    tenant_code: Optional[str],
    segment: str,
    name: str,
    campaign_code: Optional[str] = None,
    starts_at: Optional[datetime] = None,
    ends_at: Optional[datetime] = None,
    max_uses: Optional[int] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], int]:
    tenant_code = _normalize(tenant_code)
    segment = _normalize(segment)
    name = _normalize(name)
    campaign_code = _normalize(campaign_code)

    if not segment:
        return {
            "ok": False,
            "error_code": "VALIDATION_ERROR",
            "message": "segment is required",
        }, 422

    if not name:
        return {
            "ok": False,
            "error_code": "VALIDATION_ERROR",
            "message": "name is required",
        }, 422

    if starts_at and ends_at and ends_at < starts_at:
        return {
            "ok": False,
            "error_code": "VALIDATION_ERROR",
            "message": "ends_at must be >= starts_at",
        }, 422

    final_code = campaign_code or _generate_campaign_code(
        tenant_code,
        segment,
        name,
    )
    mode = "MIGRATED" if campaign_code else "GENERATED"

    async with db_connection() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO marketing_campaigns
                (
                    campaign_code,
                    tenant_code,
                    segment,
                    name,
                    starts_at,
                    ends_at,
                    max_uses,
                    attributes
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
                RETURNING campaign_code
                """,
                final_code,
                tenant_code,
                segment,
                name,
                starts_at,
                ends_at,
                max_uses,
                json.dumps(attributes or {}),
            )

    return {
        "ok": True,
        "campaign_code": row["campaign_code"],
        "mode": mode,
    }, 201


async def validate_campaign_and_create_track(
    *,
    tenant_code: Optional[str],
    campaign_code: str,
    user_ucn_encrypted: Optional[str] = None,
    device_fingerprint: Optional[str] = None,
    ip_address: Optional[str] = None,
    qr_payload: Optional[str] = None,
    source_channel: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], int]:
    tenant_code = _normalize(tenant_code)
    campaign_code = _normalize(campaign_code)

    if not campaign_code:
        return {
            "ok": False,
            "error_code": "VALIDATION_ERROR",
            "message": "campaign_code is required",
        }, 422

    async with db_connection() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT campaign_code, tenant_code, is_active, starts_at, ends_at
                FROM marketing_campaigns
                WHERE campaign_code = $1
                """,
                campaign_code,
            )

            if not row:
                return {
                    "valid": False,
                    "reason": "Campaign code not found",
                    "campaignCode": campaign_code,
                    "campaignTrackId": None,
                }, 200

            db_campaign_code = row["campaign_code"]
            db_tenant_code = row["tenant_code"]
            is_active = row["is_active"]
            starts_at = row["starts_at"]
            ends_at = row["ends_at"]

            if tenant_code and db_tenant_code and tenant_code != db_tenant_code:
                return {
                    "valid": False,
                    "reason": "Tenant mismatch",
                    "campaignCode": db_campaign_code,
                    "campaignTrackId": None,
                }, 200

            now = datetime.now(timezone.utc)

            if not is_active:
                return {
                    "valid": False,
                    "reason": "Campaign inactive",
                    "campaignCode": db_campaign_code,
                    "campaignTrackId": None,
                }, 200

            if starts_at and starts_at > now:
                return {
                    "valid": False,
                    "reason": "Campaign not started",
                    "campaignCode": db_campaign_code,
                    "campaignTrackId": None,
                }, 200

            if ends_at and ends_at < now:
                return {
                    "valid": False,
                    "reason": "Campaign expired",
                    "campaignCode": db_campaign_code,
                    "campaignTrackId": None,
                }, 200

            campaign_track_id = str(uuid4())

            await conn.execute(
                """
                INSERT INTO campaign_attributions
                (
                    campaign_track_id,
                    campaign_code,
                    tenant_code,
                    user_ucn_encrypted,
                    device_fingerprint,
                    ip_address,
                    qr_payload,
                    source_channel,
                    metadata_json,
                    status,
                    validated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10, NOW())
                """,
                campaign_track_id,
                db_campaign_code,
                db_tenant_code,
                user_ucn_encrypted,
                device_fingerprint,
                ip_address,
                qr_payload,
                source_channel,
                json.dumps(metadata or {}),
                "VALIDATED",
            )

    return {
        "valid": True,
        "campaignCode": campaign_code,
        "campaignTrackId": campaign_track_id,
    }, 200


async def update_campaign_track_status(
    *,
    campaign_track_id: str,
    status: str,
) -> Tuple[Dict[str, Any], int]:
    campaign_track_id = _normalize(campaign_track_id)
    status = _normalize(status)

    if not campaign_track_id:
        return {
            "ok": False,
            "error_code": "VALIDATION_ERROR",
            "message": "campaign_track_id is required",
        }, 422

    if not status:
        return {
            "ok": False,
            "error_code": "VALIDATION_ERROR",
            "message": "status is required",
        }, 422

    allowed_statuses = {
        "SCANNED",
        "VALIDATED",
        "ATTRIBUTED",
        "COMPLETED",
        "BLOCKED",
        "EXPIRED",
        "INVALID",
    }

    if status not in allowed_statuses:
        return {
            "ok": False,
            "error_code": "VALIDATION_ERROR",
            "message": "invalid status",
        }, 422

    async with db_connection() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE campaign_attributions
                SET
                    status = $1,
                    validated_at  = CASE WHEN $2 = 'VALIDATED'  THEN NOW() ELSE validated_at  END,
                    attributed_at = CASE WHEN $3 = 'ATTRIBUTED' THEN NOW() ELSE attributed_at END,
                    completed_at  = CASE WHEN $4 = 'COMPLETED'  THEN NOW() ELSE completed_at  END
                WHERE campaign_track_id = $5
                RETURNING campaign_track_id, status
                """,
                status,
                status,
                status,
                status,
                campaign_track_id,
            )

    if not row:
        return {
            "ok": False,
            "error_code": "NOT_FOUND",
            "message": "campaign_track_id not found",
        }, 404

    return {
        "ok": True,
        "campaignTrackId": row["campaign_track_id"],
        "newStatus": row["status"],
    }, 200