from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from apps.api.routers.dashboard import (
    _get_referral_progress as get_dashboard_referral_progress,
)
from services.link_code_service import inspect_link_code
from services.outcome_trace_service import OutcomeTraceNotFound, get_outcome_trace
from services.referral_code import (
    capture_referee_ucn,
    get_or_create_referrer_code,
    validate_referral_code,
)
from services.referral_saas_safe_status_service import project_referral_saas_safe_status
from services.referral_saas_validation_service import (
    build_referral_saas_validation_result,
)
from utils.security import require_distribution_admin_key, require_partner_key
from utils.tenant_guard import require_valid_tenant

router = APIRouter(
    prefix="/v1/referral-saas",
    tags=["Referral SaaS"],
)

REFERRAL_SAAS_OPERATOR_TRACE_SECTIONS = [
    "outcome",
    "attribution",
    "participants",
    "events",
    "audit",
]
REFERRAL_SAAS_OPERATOR_TRACE_SECTION_SET = set(REFERRAL_SAAS_OPERATOR_TRACE_SECTIONS)


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


def _normalise_operator_trace_sections(
    include_sections: list[str] | None,
) -> list[str]:
    if include_sections is None:
        return list(REFERRAL_SAAS_OPERATOR_TRACE_SECTIONS)

    sections = ["outcome"]
    for section in include_sections:
        normalised = str(section or "").strip().lower()
        if not normalised:
            continue
        if normalised not in REFERRAL_SAAS_OPERATOR_TRACE_SECTION_SET:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "validation_error",
                    "message": (
                        "Unsupported Referral SaaS attribution trace section: "
                        f"{section}"
                    ),
                },
            )
        if normalised not in sections:
            sections.append(normalised)
    return sections


def _operator_trace_sections(trace: dict[str, Any]) -> dict[str, Any]:
    sections = trace.get("sections") if isinstance(trace.get("sections"), dict) else {}
    return {
        section: sections[section]
        for section in REFERRAL_SAAS_OPERATOR_TRACE_SECTIONS
        if section in sections
    }


def _operator_trace_next_diagnostics(trace: dict[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    sections = trace.get("sections") if isinstance(trace.get("sections"), dict) else {}
    attribution = (
        sections.get("attribution")
        if isinstance(sections.get("attribution"), dict)
        else {}
    )

    campaign_links = attribution.get("campaign_links")
    if isinstance(campaign_links, list):
        for link in campaign_links:
            if not isinstance(link, dict):
                continue
            campaign_code = link.get("campaign_code")
            if campaign_code:
                diagnostics.append(
                    {
                        "type": "CAMPAIGN_READINESS",
                        "label": "Inspect campaign readiness",
                        "targetRef": str(campaign_code),
                    }
                )
                break

    trace_ref = str(trace.get("trace_id") or "")
    if trace.get("missing_evidence"):
        diagnostics.append(
            {
                "type": "SUPPORT_TRIAGE",
                "label": "Review missing evidence",
                "targetRef": trace_ref,
            }
        )

    if trace.get("source_warnings"):
        diagnostics.append(
            {
                "type": "SOURCE_WARNING",
                "label": "Review source warnings",
                "targetRef": trace_ref,
            }
        )

    support_trace = (
        trace.get("support_trace")
        if isinstance(trace.get("support_trace"), dict)
        else {}
    )
    if int(support_trace.get("correlation_reference_count") or 0) > 0:
        lookup = trace.get("lookup") if isinstance(trace.get("lookup"), dict) else {}
        diagnostics.append(
            {
                "type": "SUPPORT_CORRELATION",
                "label": "Review support correlations",
                "targetRef": str(lookup.get("value") or trace_ref),
            }
        )

    return diagnostics


def _operator_progress_next_diagnostics(
    progress: dict[str, Any],
    safe_status: dict[str, Any],
) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    referral_track_id = str(progress.get("referral_track_id") or "")
    next_milestone = progress.get("next_milestone")
    if next_milestone:
        diagnostics.append(
            {
                "type": "NEXT_MILESTONE",
                "label": "Review next progress milestone",
                "targetRef": str(next_milestone),
            }
        )

    product_status = str(
        safe_status.get("product_status") or safe_status.get("status") or ""
    ).upper()
    action_category = str(safe_status.get("action_category") or "").upper()
    if product_status in {"ACTION_NEEDED", "UNAVAILABLE"} or action_category not in {
        "",
        "NONE",
    }:
        diagnostics.append(
            {
                "type": "SUPPORT_TRIAGE",
                "label": "Review progress status with support",
                "targetRef": referral_track_id,
            }
        )

    if bool(progress.get("is_complete")):
        diagnostics.append(
            {
                "type": "ATTRIBUTION_TRACE",
                "label": "Inspect attribution trace",
                "targetRef": referral_track_id,
            }
        )

    return diagnostics


def _safe_progress_payload(progress: dict[str, Any]) -> dict[str, Any]:
    return {
        "referralTrackId": progress.get("referral_track_id"),
        "status": progress.get("status"),
        "isComplete": bool(progress.get("is_complete")),
        "progressPercent": int(progress.get("progress_percent") or 0),
        "progressBand": progress.get("progress_band"),
        "displayStatus": progress.get("display_status"),
        "nextMilestone": progress.get("next_milestone"),
    }


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


@router.get("/operator/referrals/{referral_track_id}/progress-status")
async def get_referral_saas_operator_progress_status(
    referral_track_id: UUID,
    tenant_code: Annotated[str, Query(min_length=1)],
    viewer_role: str = Query(default="referrer"),
    identity: dict = Depends(require_distribution_admin_key),
) -> dict[str, Any]:
    resolved_tenant = _normalise_operator_tenant_code(tenant_code)

    try:
        progress = await get_dashboard_referral_progress(
            str(referral_track_id),
            resolved_tenant,
        )
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "progress_status_not_found",
                    "message": (
                        "Progress status was not found for the requested tenant."
                    ),
                },
            )

        safe_projection = project_referral_saas_safe_status(
            viewer_role=viewer_role,
            subject={
                "type": "referral",
                "safe_ref": f"referral:track:{referral_track_id}",
            },
            evidence={
                "source_family": "outcome",
                "status": progress.get("status"),
                "source_confidence": "HIGH",
            },
            redactions=["referrer_ucn", "referee_ucn", "tenant_code"],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": str(exc),
            },
        ) from exc

    safe_status = safe_projection["safe_status"]
    return {
        "status": "ok",
        "progressStatus": {
            "lookup": {
                "type": "REFERRAL_TRACK_ID",
                "value": str(referral_track_id),
            },
            "tenantCode": resolved_tenant,
            "viewerRole": viewer_role,
            "progress": _safe_progress_payload(progress),
            "safeStatus": safe_status,
            "missingEvidence": safe_status.get("missing_evidence", []),
            "redactions": safe_status.get("redactions", []),
            "nextDiagnostics": _operator_progress_next_diagnostics(
                progress,
                safe_status,
            ),
        },
        "operator_scope": {
            "source": "operator_query_tenant",
            "tenant_code": resolved_tenant,
            "account_ref": identity.get("account_ref"),
            "external_tenant_ref": identity.get("external_tenant_ref"),
        },
        "guardrail": (
            "Referral SaaS operator progress/status wrapper over existing "
            "read-only referral progress and safe-status primitives. This "
            "endpoint does not mutate progress, attribution, campaign, reward, "
            "funding, fulfilment, settlement, audit, webhook, support-case, "
            "repair, replay, retry, or money state and does not expose raw UCNs."
        ),
    }


@router.get("/operator/outcomes/{referral_track_id}/trace")
async def get_referral_saas_operator_attribution_trace(
    referral_track_id: UUID,
    tenant_code: Annotated[str, Query(min_length=1)],
    include_sections: Annotated[list[str] | None, Query()] = None,
    identity: dict = Depends(require_distribution_admin_key),
) -> dict[str, Any]:
    resolved_tenant = _normalise_operator_tenant_code(tenant_code)
    sections = _normalise_operator_trace_sections(include_sections)

    try:
        trace = await get_outcome_trace(
            tenant_code=resolved_tenant,
            referral_track_id=str(referral_track_id),
            identity=identity,
            include_sections=sections,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": str(exc),
            },
        ) from exc
    except OutcomeTraceNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "outcome_not_found",
                "message": (
                    "Attribution trace was not found for the requested tenant."
                ),
            },
        ) from exc

    return {
        "status": "ok",
        "attributionTrace": {
            "traceStatus": trace.get("trace_completeness"),
            "traceId": trace.get("trace_id"),
            "lookup": trace.get("lookup"),
            "tenantCode": trace.get("tenant_code"),
            "sections": _operator_trace_sections(trace),
            "supportTrace": trace.get("support_trace"),
            "missingEvidence": trace.get("missing_evidence", []),
            "sourceWarnings": trace.get("source_warnings", []),
            "redactions": trace.get("redactions", []),
            "generatedAt": trace.get("generated_at"),
            "nextDiagnostics": _operator_trace_next_diagnostics(trace),
        },
        "operator_scope": {
            "source": "operator_query_tenant",
            "tenant_code": resolved_tenant,
            "account_ref": identity.get("account_ref"),
            "external_tenant_ref": identity.get("external_tenant_ref"),
        },
        "guardrail": (
            "Referral SaaS operator attribution trace wrapper over the "
            "existing read-only outcome trace primitive. This endpoint does "
            "not mutate attribution, progress, campaign, reward, funding, "
            "fulfilment, settlement, audit, webhook, or money state and does "
            "not expose money sections."
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
