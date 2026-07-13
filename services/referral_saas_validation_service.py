from __future__ import annotations

from typing import Any

ALIAS_ERROR_CODES = {
    "ALIAS_REQUIRED",
    "ALIAS_TOO_SHORT",
    "ALIAS_TOO_LONG",
    "ALIAS_INVALID_FORMAT",
    "ALIAS_NOT_ALLOWED",
}

VALIDATION_RECOVERY_MAP = {
    "REJECTED_TERMS_REQUIRED": (
        "ACCEPT_TERMS_AND_RETRY",
        "Accept the referral terms and try again.",
    ),
    "REJECTED_ALIAS": (
        "RETRY_WITH_VALID_ALIAS",
        "Use a valid display alias and try again.",
    ),
    "REJECTED_CODE_NOT_FOUND": (
        "CHECK_CODE_AND_RETRY",
        "Check the referral code and try again.",
    ),
    "RECOVERY_REQUIRED_LOGGING": (
        "RETRY_VALIDATION_OR_CONTACT_SUPPORT",
        "We could not finish setting up this referral. Try again or contact support.",
    ),
}

VALIDATION_IDEMPOTENCY_POSTURE = {
    "validationAttemptPolicy": "NEW_JOURNEY_PER_SUCCESSFUL_VALIDATION",
    "duplicateSubmitGuarantee": "NOT_IDEMPOTENT",
    "idempotencyKeySupported": False,
    "safeMessage": (
        "Successful public validation currently records a new referral "
        "journey for each submit. Do not treat repeated validation submits "
        "as idempotent until a schema-backed idempotency key or duplicate "
        "reuse contract is implemented."
    ),
}


def referral_saas_validation_status(body: dict[str, Any], status_code: int) -> str:
    error_code = str(body.get("error_code") or body.get("errorCode") or "")
    if error_code == "TENANT_CODE_REQUIRED":
        return "REJECTED_MISSING_TENANT"
    if error_code == "REFERRAL_CODE_REQUIRED":
        return "REJECTED_MISSING_CODE"
    if error_code == "ACCEPTED_TERMS_REQUIRED":
        return "REJECTED_TERMS_REQUIRED"
    if error_code in ALIAS_ERROR_CODES:
        return "REJECTED_ALIAS"
    if error_code == "REFERRAL_CODE_NOT_FOUND":
        return "REJECTED_CODE_NOT_FOUND"
    if error_code == "REFERRAL_LOG_FAILED":
        return "RECOVERY_REQUIRED_LOGGING"
    if status_code >= 400:
        return "FAILED"
    return "VALIDATED" if body.get("valid") else "FAILED"


def referral_saas_validation_recovery(validation_status: str) -> dict[str, str] | None:
    mapped = VALIDATION_RECOVERY_MAP.get(validation_status)
    if not mapped:
        return None
    action, safe_message = mapped
    return {"action": action, "safeMessage": safe_message}


def build_referral_saas_validation_result(
    body: dict[str, Any],
    status_code: int,
) -> dict[str, Any]:
    validation_status = referral_saas_validation_status(body, status_code)
    return {
        "validationStatus": validation_status,
        "valid": bool(body.get("valid")) and validation_status == "VALIDATED",
        "referralTrackId": body.get("referral_track_id") or body.get("referralTrackId"),
        "alias": body.get("alias") or body.get("alias_value"),
        "errorCode": body.get("error_code") or body.get("errorCode"),
        "message": body.get("message"),
        "recovery": referral_saas_validation_recovery(validation_status),
        "idempotency": dict(VALIDATION_IDEMPOTENCY_POSTURE),
    }
