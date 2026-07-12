from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from services.referral_saas_reporting_service import get_referral_saas_report
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
    campaign_ref: str | None,
    campaign_code: str | None,
    sponsor_code: str | None,
) -> dict[str, str]:
    return {
        key: value.strip()
        for key, value in {
            "campaign_ref": campaign_ref,
            "campaign_code": campaign_code,
            "sponsor_code": sponsor_code,
        }.items()
        if value is not None and value.strip()
    }


@router.get("/reports/{report_type}")
async def get_referral_saas_product_report(
    report_type: str,
    tenant_code: Annotated[
        str,
        Query(
            min_length=1,
            description=(
                "Temporary internal tenant scope until SaaS account resolution "
                "is implemented."
            ),
        ),
    ],
    dimensions: Annotated[
        list[str] | None,
        Query(description="Repeatable approved Referral SaaS report dimensions."),
    ] = None,
    campaign_ref: str | None = Query(default=None),
    campaign_code: str | None = Query(default=None),
    sponsor_code: str | None = Query(default=None),
    data_window_start: datetime | None = Query(default=None),
    data_window_end: datetime | None = Query(default=None),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_report_reader(identity)

    try:
        report = await get_referral_saas_report(
            tenant_code=tenant_code,
            report_type=report_type,
            dimensions=dimensions,
            filters=_filters(
                campaign_ref=campaign_ref,
                campaign_code=campaign_code,
                sponsor_code=sponsor_code,
            ),
            data_window_start=data_window_start,
            data_window_end=data_window_end,
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
        "report": report,
        "guardrail": (
            "Read-only Referral SaaS report wrapper. This endpoint does not "
            "create exports, resolve SaaS account membership, generate "
            "invoices, create billing events, or mutate funding, settlement, "
            "fulfilment, reward, commission, audit, tenant, or analytics "
            "records."
        ),
    }
