from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from services.link_code_service import inspect_link_code
from services.referral_code import (
    capture_referee_ucn,
    get_or_create_referrer_code,
    validate_referral_code,
)
from services.referral_saas_validation_service import (
    build_referral_saas_validation_result,
)
from utils.security import require_distribution_admin_key, require_partner_key
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


def _normalise_operator_tenant_code(tenant_code: str) -> str:
    tenant = str(tenant_code or "").strip().upper()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "tenant_code is required",
            },
        )
    return tenant


def _operator_next_diagnostics(link_code: dict[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    campaign = link_code.get("campaign") if isinstance(link_code.get("campaign"), dict) else {}
    attribution = (
        link_code.get("attribution")
        if isinstance(link_code.get("attribution"), dict)
        else {}
    )

    campaign_code = campaign.get("campaign_code")
    if campaign_code:
        diagnostics.append(
            {
                "type": "CAMPAIGN_READINESS",
                "label": "Inspect campaign readiness",
                "targetRef": str(campaign_code),
            }
        )

    referral_track_id = attribution.get("referral_track_id")
    if referral_track_id:
        diagnostics.append(
            {
                "type": "ATTRIBUTION_TRACE",
                "label": "Inspect attribution trace",
                "targetRef": str(referral_track_id),
            }
        )

    if link_code.get("missing_evidence"):
        diagnostics.append(
            {
                "type": "SUPPORT_TRIAGE",
                "label": "Review missing evidence",
                "targetRef": str(link_code.get("link_code_id") or ""),
            }
        )

    if link_code.get("source_warnings"):
        diagnostics.append(
            {
                "type": "SOURCE_WARNING",
                "label": "Review source warnings",
                "targetRef": str(link_code.get("link_code_id") or ""),
            }
        )

    return diagnostics


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


@router.get("/operator/links/inspect")
async def inspect_referral_saas_operator_link_code(
    tenant_code: Annotated[str, Query(min_length=1)],
    source_type: Annotated[str, Query(min_length=1)],
    link_code_id: str | None = Query(default=None),
    code_or_ref: str | None = Query(default=None),
    include_evidence: bool = Query(default=True),
    identity: dict = Depends(require_distribution_admin_key),
) -> dict[str, Any]:
    resolved_tenant = _normalise_operator_tenant_code(tenant_code)

    try:
        link_code = await inspect_link_code(
            tenant_code=resolved_tenant,
            source_type=source_type,
            link_code_id=link_code_id,
            code_or_ref=code_or_ref,
            include_evidence=include_evidence,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": str(exc),
            },
        ) from exc

    return {
        "status": "ok",
        "inspection": {
            "inspectionStatus": link_code.get("status"),
            "linkCode": link_code,
            "nextDiagnostics": _operator_next_diagnostics(link_code),
        },
        "operator_scope": {
            "source": "operator_query_tenant",
            "tenant_code": resolved_tenant,
            "account_ref": identity.get("account_ref"),
            "external_tenant_ref": identity.get("external_tenant_ref"),
        },
        "guardrail": (
            "Referral SaaS operator link/code inspection wrapper over the "
            "existing read-only inspection primitive. This endpoint does not "
            "issue, resolve, void, rotate, mutate, retry, replay, repair, "
            "reward, fund, fulfil, settle, or generate codes."
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
    response.status_code = code
    return {
        "status": "ok" if code < 400 else "rejected",
        "validation": build_referral_saas_validation_result(body, code),
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
