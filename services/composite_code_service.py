from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from services.campaign_service import validate_campaign_and_create_track
from services.referral_code import validate_referral_code


def _normalize_code(value: Optional[str]) -> str:
    """Normalize any code value for consistent comparison."""
    return (value or "").strip().upper()


def _derive_tenant_code(composite_code: str) -> Optional[str]:
    """
    Attempts to derive tenant_code from a composite code.

    Expected interim format:
        TENANT-<rest_of_code>

    Example:
        FNB-ABC123
        FNB-SOMEGENERATEDCODE
    """
    composite_code = _normalize_code(composite_code)

    if not composite_code or "-" not in composite_code:
        return None

    tenant, _ = composite_code.split("-", 1)
    tenant = tenant.strip().upper()

    return tenant or None


async def validate_composite_code(
    *,
    composite_code: str,
    tenant_code: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], int]:
    """
    Interim composite validation design.

    Current architecture note:
    - The same generated code is currently passed to both campaign and referral validators.
    - Campaign/referral code generation is not yet aligned to a target-state format where
      components can be parsed independently from the composite code.
    - Once upstream code generation is aligned, this service can be refactored to split the
      composite code into explicit campaign and referral components.
    """
    composite_code = _normalize_code(composite_code)
    tenant = _normalize_code(tenant_code) or _derive_tenant_code(composite_code)

    if not composite_code:
        return (
            {
                "error_code": "VALIDATION_ERROR",
                "message": "composite_code is required",
                "detail": {"field": "composite_code"},
            },
            422,
        )

    if not tenant:
        return (
            {
                "error_code": "VALIDATION_ERROR",
                "message": "tenant_code is required (or must be derivable from composite_code)",
                "detail": {"field": "tenant_code"},
            },
            422,
        )

    campaign_result, campaign_status = await validate_campaign_and_create_track(
        tenant_code=tenant,
        campaign_code=composite_code,
        metadata=attributes or {},
    )

    referral_result, referral_status = await validate_referral_code(
        tenant_code=tenant,
        referral_code=composite_code,
        accepted_terms=True,
        alias=(attributes or {}).get("alias"),
        device_fingerprint=(attributes or {}).get("deviceFingerprint"),
        ip_address=(attributes or {}).get("ipAddress"),
        qr_code=(attributes or {}).get("qrCode"),
    )

    campaign_valid = campaign_status < 400 and campaign_result.get("valid", False)
    referral_valid = referral_status < 400 and referral_result.get("valid", False)
    overall_ok = campaign_valid and referral_valid

    return (
        {
            "ok": overall_ok,
            "tenant_code": tenant,
            "composite_code": composite_code,
            "campaign": {
                "valid": campaign_valid,
                "campaignCode": composite_code,
                "campaignTrackId": campaign_result.get("campaignTrackId")
                or campaign_result.get("campaign_track_id"),
                "message": campaign_result.get("message")
                or campaign_result.get("reason"),
                "errorCode": campaign_result.get("error_code"),
                "attributes": campaign_result.get("attributes", {}),
            },
            "referral": {
                "valid": referral_valid,
                "referralCode": composite_code,
                "referralTrackId": referral_result.get("referral_track_id")
                or referral_result.get("referralTrackId"),
                "message": referral_result.get("message"),
                "errorCode": referral_result.get("error_code"),
                "attributes": referral_result.get("attributes", {}),
            },
        },
        200,
    )