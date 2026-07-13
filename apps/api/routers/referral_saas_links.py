from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from services.referral_code import (
    capture_referee_ucn,
    get_or_create_referrer_code,
    validate_referral_code,
)
from utils.security import require_partner_key
from utils.tenant_guard import require_valid_tenant

router = APIRouter(
    prefix="/v1/referral-saas",
    tags=["Referral SaaS"],
)


class ReferralSaasCodeIssueRequest(BaseModel):
    referrer_ucn: str = Field(..., alias="referrerUcn")
    sticker: str
    segment: str
    preferred_handle: str | None = Field(default=None, alias="preferredHandle")
    accepted_terms: bool = Field(..., alias="acceptedTerms")


class ReferralSaasValidationRequest(BaseModel):
    tenant_code: str = Field(..., alias="tenantCode")
    referral_code: str = Field(..., alias="referralCode")
    accepted_terms: bool = Field(..., alias="acceptedTerms")
    alias_value: str | None = Field(default=None, alias="alias")
    device_fingerprint: str | None = Field(default=None, alias="deviceFingerprint")
    ip_address: str | None = Field(default=None, alias="ipAddress")
    qr_code: str | None = Field(default=None, alias="qrCode")


class ReferralSaasRefereeUcnCaptureRequest(BaseModel):
    referee_ucn: str = Field(..., alias="refereeUcn")


def _account_scope(identity: dict[str, Any]) -> dict[str, str | None]:
    return {
        "source": "identity_tenant",
        "account_ref": identity.get("account_ref"),
        "external_tenant_ref": identity.get("external_tenant_ref"),
    }


def _issue_status(body: dict[str, Any], status_code: int) -> str:
    error_code = str(body.get("error_code") or "")
    if error_code == "MISSING_FIELDS":
        return "REJECTED_MISSING_FIELDS"
    if error_code == "ACCEPTED_TERMS_REQUIRED":
        return "REJECTED_TERMS_REQUIRED"
    if status_code >= 400:
        return "FAILED"
    return "CREATED" if body.get("created") else "EXISTING"


def _validation_status(body: dict[str, Any], status_code: int) -> str:
    error_code = str(body.get("error_code") or body.get("errorCode") or "")
    if error_code == "TENANT_CODE_REQUIRED":
        return "REJECTED_MISSING_TENANT"
    if error_code == "REFERRAL_CODE_REQUIRED":
        return "REJECTED_MISSING_CODE"
    if error_code == "ACCEPTED_TERMS_REQUIRED":
        return "REJECTED_TERMS_REQUIRED"
    if error_code in {
        "ALIAS_REQUIRED",
        "ALIAS_TOO_SHORT",
        "ALIAS_TOO_LONG",
        "ALIAS_INVALID_FORMAT",
        "ALIAS_NOT_ALLOWED",
    }:
        return "REJECTED_ALIAS"
    if error_code == "REFERRAL_CODE_NOT_FOUND":
        return "REJECTED_CODE_NOT_FOUND"
    if error_code == "REFERRAL_LOG_FAILED":
        return "RECOVERY_REQUIRED_LOGGING"
    if status_code >= 400:
        return "FAILED"
    return "VALIDATED" if body.get("valid") else "FAILED"


def _validation_recovery(validation_status: str) -> dict[str, str] | None:
    recovery_map = {
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
    mapped = recovery_map.get(validation_status)
    if not mapped:
        return None
    action, safe_message = mapped
    return {"action": action, "safeMessage": safe_message}


def _capture_status(body: dict[str, Any], status_code: int) -> str:
    error_code = str(body.get("error_code") or "")
    if error_code == "REFEREE_UCN_REQUIRED":
        return "REJECTED_MISSING_REFEREE"
    if error_code == "REFERRAL_TRACK_NOT_FOUND":
        return "REJECTED_TRACK_NOT_FOUND"
    if error_code == "TENANT_INACTIVE":
        return "REJECTED_TENANT_INACTIVE"
    if error_code == "REFEREE_UCN_PROGRESS_EVENT_FAILED":
        return "RECOVERY_REQUIRED_PROGRESS_EVENT"
    if status_code >= 400:
        return "FAILED"
    return "CAPTURED"


@router.post("/referral-codes")
async def issue_referral_saas_code(
    request: ReferralSaasCodeIssueRequest,
    response: Response,
    identity: dict = Depends(require_partner_key),
) -> dict[str, Any]:
    body, code = await get_or_create_referrer_code(
        referrer_ucn=request.referrer_ucn,
        tenant=identity["tenant_code"],
        sticker=request.sticker,
        segment=request.segment,
        preferred_handle=request.preferred_handle,
        accepted_terms=request.accepted_terms,
    )

    response.status_code = code
    return {
        "status": "ok" if code < 400 else "rejected",
        "issue": {
            "issueStatus": _issue_status(body, code),
            "referralCode": body.get("referral_code"),
            "publicHandle": body.get("gaming_handle"),
            "created": bool(body.get("created")),
            "sourceType": "REFERRAL_CODE",
            "errorCode": body.get("error_code"),
            "message": body.get("message"),
        },
        "account_scope": _account_scope(identity),
        "guardrail": (
            "Referral SaaS issue wrapper over the existing referral code "
            "primitive. This endpoint derives tenant scope from the partner "
            "identity and does not expose raw UCNs, hashes, revoke, expire, "
            "reissue, rewards, funding, fulfilment, settlement, or wallet "
            "behavior."
        ),
    }


@router.post("/public/referrals/validate")
async def validate_referral_saas_code(
    request: ReferralSaasValidationRequest,
    response: Response,
) -> dict[str, Any]:
    tenant_code = await require_valid_tenant(request.tenant_code)
    body, code = await validate_referral_code(
        referral_code=request.referral_code,
        tenant_code=tenant_code,
        accepted_terms=request.accepted_terms,
        alias=request.alias_value,
        device_fingerprint=request.device_fingerprint,
        ip_address=request.ip_address,
        qr_code=request.qr_code,
    )
    validation_status = _validation_status(body, code)

    response.status_code = code
    return {
        "status": "ok" if code < 400 else "rejected",
        "validation": {
            "validationStatus": validation_status,
            "valid": bool(body.get("valid")) and validation_status == "VALIDATED",
            "referralTrackId": body.get("referral_track_id") or body.get("referralTrackId"),
            "alias": body.get("alias") or body.get("alias_value"),
            "errorCode": body.get("error_code") or body.get("errorCode"),
            "message": body.get("message"),
            "recovery": _validation_recovery(validation_status),
        },
        "guardrail": (
            "Referral SaaS validation wrapper over the existing public "
            "validation primitive. This endpoint returns a product status and "
            "does not expose raw UCNs, hashes, internal attributes, reward, "
            "funding, fulfilment, settlement, or wallet evidence."
        ),
    }


@router.post("/referrals/{referral_track_id}/referee-ucn")
async def capture_referral_saas_referee_ucn(
    referral_track_id: str,
    request: ReferralSaasRefereeUcnCaptureRequest,
    response: Response,
    identity: dict = Depends(require_partner_key),
) -> dict[str, Any]:
    body, code = await capture_referee_ucn(
        referral_track_id=referral_track_id,
        referee_ucn=request.referee_ucn,
        tenant_code=identity["tenant_code"],
    )

    response.status_code = code
    return {
        "status": "ok" if code < 400 else "rejected",
        "identityCapture": {
            "captureStatus": _capture_status(body, code),
            "referralTrackId": body.get("referral_track_id") or referral_track_id,
            "errorCode": body.get("error_code"),
            "message": body.get("message"),
        },
        "account_scope": _account_scope(identity),
        "guardrail": (
            "Referral SaaS identity-capture wrapper over the existing referee "
            "UCN capture primitive. This endpoint derives tenant scope from "
            "the partner identity and does not expose raw UCNs, hashes, "
            "reward, funding, fulfilment, settlement, or wallet behavior."
        ),
    }
