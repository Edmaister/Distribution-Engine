from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from utils.security import require_partner_key

from apps.api.schemas.referrals import (
    ReferralCodeIssue,
    ReferralCodeIssueResponse,
    ReferralValidate,
    ReferralValidateResponse,
    RefereeUCNCapture,
    RefereeUCNCaptureResponse,
)

from services.referral_code import (
    get_or_create_referrer_code,
    validate_referral_code,
    capture_referee_ucn,
)
from utils.tenant_guard import require_valid_tenant


public_router = APIRouter(
    prefix="/public/referrals",
    tags=["Public Referrals"],
)


@public_router.post("/validate", response_model=ReferralValidateResponse)
async def validate(req: ReferralValidate, response: Response):
    tenant_code = await require_valid_tenant(req.tenant_code)

    body, code = await validate_referral_code(
        referral_code=req.referral_code,
        tenant_code=tenant_code,
        accepted_terms=req.accepted_terms,
        alias=req.alias_value,
        device_fingerprint=req.device_fingerprint,
        ip_address=req.ip_address,
        qr_code=req.qr_code,
    )

    if "valid" not in body:
        body["valid"] = False

    if "referralTrackId" not in body:
        body["referralTrackId"] = body.get("referral_track_id")

    if "errorCode" not in body:
        body["errorCode"] = body.get("error_code")

    if "attributes" not in body or body["attributes"] is None:
        body["attributes"] = {}

    if "message" not in body or not body["message"]:
        body["message"] = "OK" if not body.get("errorCode") else "Validation failed"

    if "validationOutcome" not in body or not body["validationOutcome"]:
        body["validationOutcome"] = "VALIDATED" if body.get("valid") else "FAILED"

    if "alias" not in body:
        body["alias"] = body.get("alias_value")

    response.status_code = code
    return body


router = APIRouter(
    prefix="/referrals",
    tags=["Referrals"],
    dependencies=[Depends(require_partner_key)],
)


@router.post(
    "/codes",
    response_model=ReferralCodeIssueResponse,
    status_code=status.HTTP_201_CREATED,
)
async def issue_code(
    req: ReferralCodeIssue,
    response: Response,
    identity=Depends(require_partner_key),
):
    tenant_code = identity["tenant_code"]

    body, code = await get_or_create_referrer_code(
        referrer_ucn=req.referrer_ucn,
        tenant=tenant_code,
        sticker=req.sticker,
        segment=req.segment,
        preferred_handle=req.preferred_handle,
        accepted_terms=req.accepted_terms,
    )

    response.status_code = code
    return body


@router.post("/referees/ucn", response_model=RefereeUCNCaptureResponse)
async def capture_ucn(
    req: RefereeUCNCapture,
    response: Response,
    identity=Depends(require_partner_key),
):
    tenant_code = identity["tenant_code"]

    body, code = await capture_referee_ucn(
        referral_track_id=req.referral_track_id,
        referee_ucn=req.referee_ucn,
        tenant_code=tenant_code,
    )

    if "error_code" not in body:
        body["error_code"] = None

    if "message" not in body or not body["message"]:
        body["message"] = "OK" if not body.get("error_code") else "Update failed"

    response.status_code = code
    return body