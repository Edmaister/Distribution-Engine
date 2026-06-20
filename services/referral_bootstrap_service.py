from __future__ import annotations

from typing import Any, Dict, Optional

from utils.db import db_connection


class ReferralBootstrapError(Exception):
    pass


def _row_get(row: Any, key: str, default=None):
    try:
        return row[key]
    except Exception:
        return default


async def get_referrer_by_ucn_and_tenant(
    referrer_ucn: str,
    tenant_code: str,
) -> Optional[Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                referrer_code_id,
                referrer_ucn,
                referral_code,
                gaming_handle,
                tenant_code,
                accepted_terms,
                accepted_terms_at,
                created_at,
                updated_at
            FROM referrer_codes
            WHERE referrer_ucn = $1
              AND tenant_code = $2
            LIMIT 1
            """,
            referrer_ucn,
            tenant_code,
        )

    return row


async def bootstrap_referrer_profile(
    referrer_ucn: str,
    tenant_code: str,
) -> Dict[str, Any]:
    existing = await get_referrer_by_ucn_and_tenant(
        referrer_ucn,
        tenant_code,
    )

    if not existing:
        return {
            "referrerUcn": referrer_ucn,
            "tenantCode": tenant_code,
            "exists": False,
            "referralCode": None,
            "alias": None,
            "acceptedTerms": False,
            "requiresTermsAcceptance": False,
            "qrEligible": False,
            "message": "Referrer profile does not exist",
        }

    accepted_terms = bool(_row_get(existing, "accepted_terms", False))
    referral_code = _row_get(existing, "referral_code")
    alias_value = _row_get(existing, "gaming_handle")

    return {
        "referrerUcn": _row_get(existing, "referrer_ucn"),
        "tenantCode": _row_get(existing, "tenant_code"),
        "exists": True,
        "referralCode": referral_code,
        "alias": alias_value,
        "acceptedTerms": accepted_terms,
        "requiresTermsAcceptance": not accepted_terms,
        "qrEligible": bool(referral_code) and accepted_terms,
        "message": "Existing referrer profile found",
    }


async def accept_terms(
    referrer_ucn: str,
    tenant_code: str,
) -> Dict[str, Any]:
    async with db_connection() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE referrer_codes
                SET
                    accepted_terms = TRUE,
                    accepted_terms_at = NOW(),
                    updated_at = NOW()
                WHERE referrer_ucn = $1
                  AND tenant_code = $2
                RETURNING
                    referrer_ucn,
                    tenant_code,
                    accepted_terms,
                    accepted_terms_at
                """,
                referrer_ucn,
                tenant_code,
            )

    if not row:
        raise ReferralBootstrapError("Referrer profile not found")

    accepted_terms_at = _row_get(row, "accepted_terms_at")

    return {
        "referrerUcn": _row_get(row, "referrer_ucn"),
        "tenantCode": _row_get(row, "tenant_code"),
        "acceptedTerms": bool(_row_get(row, "accepted_terms", False)),
        "acceptedTermsAt": accepted_terms_at.isoformat() if accepted_terms_at else None,
        "message": "Terms accepted successfully",
    }