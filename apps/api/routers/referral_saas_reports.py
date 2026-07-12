from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from services.referral_saas_account_scope_service import (
    resolve_referral_saas_account_scope,
)
from services.referral_saas_reporting_service import (
    build_referral_saas_report_export_preview,
    get_referral_saas_report,
    validate_referral_saas_report_export_request,
)
from utils.security import require_session_key

router = APIRouter(
    prefix="/v1/referral-saas",
    tags=["Referral SaaS"],
)

REFERRAL_SAAS_REPORT_ROLES = {
    "ADMIN",
    "SYSTEM_ADMIN",
    "DISTRIBUTION_ADMIN",
    "PLATFORM_ADMIN",
}


class ReferralSaasReportExportValidationRequest(BaseModel):
    format: str | None = Field(default=None, description="json or csv.")
    redaction_profile: str | None = Field(default=None)
    dimensions: list[str] | None = Field(default=None)
    filters: dict[str, Any] | None = Field(default=None)
    row_limit: int | None = Field(default=None)
    data_window_start: datetime | None = Field(default=None)
    data_window_end: datetime | None = Field(default=None)


def _require_referral_saas_report_reader(identity: dict[str, Any]) -> dict[str, Any]:
    role = str(identity.get("role") or "").upper()
    if role not in REFERRAL_SAAS_REPORT_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": "API key is not authorised for Referral SaaS reports.",
            },
        )
    return identity


def _filters(
    *,
    beneficiary_type: str | None,
    campaign_ref: str | None,
    campaign_code: str | None,
    link_code_status: str | None,
    product: str | None,
    reward_source: str | None,
    reward_status: str | None,
    reward_type: str | None,
    sponsor_code: str | None,
    source_type: str | None,
    sub_product: str | None,
) -> dict[str, str]:
    return {
        key: value.strip()
        for key, value in {
            "beneficiary_type": beneficiary_type,
            "campaign_ref": campaign_ref,
            "campaign_code": campaign_code,
            "link_code_status": link_code_status,
            "product": product,
            "reward_source": reward_source,
            "reward_status": reward_status,
            "reward_type": reward_type,
            "sponsor_code": sponsor_code,
            "source_type": source_type,
            "sub_product": sub_product,
        }.items()
        if value is not None and value.strip()
    }


@router.post("/reports/{report_type}/exports/validate")
async def validate_referral_saas_product_report_export(
    report_type: str,
    request: ReferralSaasReportExportValidationRequest,
    tenant_code: Annotated[
        str | None,
        Query(
            min_length=1,
            description=(
                "Optional internal tenant scope. Tenant-scoped identities may "
                "omit this; internal report readers must provide it until SaaS "
                "account resolution is implemented."
            ),
        ),
    ] = None,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_report_reader(identity)

    try:
        account_scope = resolve_referral_saas_account_scope(
            identity=identity,
            requested_tenant_code=tenant_code,
        )
        export_request = validate_referral_saas_report_export_request(
            tenant_code=account_scope.tenant_code,
            report_type=report_type,
            export_format=request.format,
            redaction_profile=request.redaction_profile,
            dimensions=request.dimensions,
            filters=request.filters,
            row_limit=request.row_limit,
            data_window_start=request.data_window_start,
            data_window_end=request.data_window_end,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": str(exc),
            },
        ) from exc
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
        "export_request": export_request,
        "account_scope": {
            "source": account_scope.source,
            "account_ref": account_scope.account_ref,
            "external_tenant_ref": account_scope.external_tenant_ref,
        },
        "guardrail": (
            "Validation-only Referral SaaS export wrapper. This endpoint does "
            "not create export files, storage records, delivery jobs, scheduled "
            "exports, audit rows, invoices, billing events, or mutate funding, "
            "settlement, fulfilment, reward, commission, tenant, or analytics "
            "records."
        ),
    }


@router.post("/reports/{report_type}/exports/preview")
async def preview_referral_saas_product_report_export(
    report_type: str,
    request: ReferralSaasReportExportValidationRequest,
    tenant_code: Annotated[
        str | None,
        Query(
            min_length=1,
            description=(
                "Optional internal tenant scope. Tenant-scoped identities may "
                "omit this; internal report readers must provide it until SaaS "
                "account resolution is implemented."
            ),
        ),
    ] = None,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_report_reader(identity)

    try:
        account_scope = resolve_referral_saas_account_scope(
            identity=identity,
            requested_tenant_code=tenant_code,
        )
        export_preview = await build_referral_saas_report_export_preview(
            tenant_code=account_scope.tenant_code,
            report_type=report_type,
            export_format=request.format,
            redaction_profile=request.redaction_profile,
            dimensions=request.dimensions,
            filters=request.filters,
            row_limit=request.row_limit,
            data_window_start=request.data_window_start,
            data_window_end=request.data_window_end,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": str(exc),
            },
        ) from exc
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
        "export_preview": export_preview,
        "account_scope": {
            "source": account_scope.source,
            "account_ref": account_scope.account_ref,
            "external_tenant_ref": account_scope.external_tenant_ref,
        },
        "guardrail": (
            "Inline Referral SaaS export preview wrapper. This endpoint does "
            "not create export files, storage records, delivery jobs, scheduled "
            "exports, audit rows, retention records, download URLs, invoices, "
            "billing events, or mutate funding, settlement, fulfilment, reward, "
            "commission, tenant, or analytics records."
        ),
    }


@router.get("/reports/{report_type}")
async def get_referral_saas_product_report(
    report_type: str,
    tenant_code: Annotated[
        str | None,
        Query(
            min_length=1,
            description=(
                "Optional internal tenant scope. Tenant-scoped identities may "
                "omit this; internal report readers must provide it until SaaS "
                "account resolution is implemented."
            ),
        ),
    ] = None,
    beneficiary_type: str | None = Query(default=None),
    dimensions: Annotated[
        list[str] | None,
        Query(description="Repeatable approved Referral SaaS report dimensions."),
    ] = None,
    campaign_ref: str | None = Query(default=None),
    campaign_code: str | None = Query(default=None),
    link_code_status: str | None = Query(default=None),
    product: str | None = Query(default=None),
    reward_source: str | None = Query(default=None),
    reward_status: str | None = Query(default=None),
    reward_type: str | None = Query(default=None),
    sponsor_code: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    sub_product: str | None = Query(default=None),
    data_window_start: datetime | None = Query(default=None),
    data_window_end: datetime | None = Query(default=None),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_report_reader(identity)

    try:
        account_scope = resolve_referral_saas_account_scope(
            identity=identity,
            requested_tenant_code=tenant_code,
        )
        report = await get_referral_saas_report(
            tenant_code=account_scope.tenant_code,
            report_type=report_type,
            dimensions=dimensions,
            filters=_filters(
                beneficiary_type=beneficiary_type,
                campaign_ref=campaign_ref,
                campaign_code=campaign_code,
                link_code_status=link_code_status,
                product=product,
                reward_source=reward_source,
                reward_status=reward_status,
                reward_type=reward_type,
                sponsor_code=sponsor_code,
                source_type=source_type,
                sub_product=sub_product,
            ),
            data_window_start=data_window_start,
            data_window_end=data_window_end,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": str(exc),
            },
        ) from exc
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
        "report": report,
        "account_scope": {
            "source": account_scope.source,
            "account_ref": account_scope.account_ref,
            "external_tenant_ref": account_scope.external_tenant_ref,
        },
        "guardrail": (
            "Read-only Referral SaaS report wrapper. This endpoint does not "
            "create exports, resolve SaaS account membership, generate "
            "invoices, create billing events, or mutate funding, settlement, "
            "fulfilment, reward, commission, audit, tenant, or analytics "
            "records."
        ),
    }
