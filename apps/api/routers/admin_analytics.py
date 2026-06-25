from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from services.tenant_safe_analytics_service import get_tenant_safe_analytics_report
from utils.security import require_session_key

router = APIRouter(
    prefix="/admin/analytics",
    tags=["Admin Analytics"],
)

ANALYTICS_ADMIN_ROLES = {
    "ADMIN",
    "SYSTEM_ADMIN",
    "FINANCE_ADMIN",
    "DISTRIBUTION_ADMIN",
    "PLATFORM_ADMIN",
}


def _require_analytics_admin(identity: dict[str, Any]) -> dict[str, Any]:
    role = str(identity.get("role") or "").upper()
    if role not in ANALYTICS_ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": "API key is not authorised for analytics reports.",
            },
        )
    return identity


def _filters(
    *,
    sponsor_code: str | None,
    campaign_code: str | None,
    provider_key: str | None,
) -> dict[str, str]:
    return {
        key: value.strip()
        for key, value in {
            "sponsor_code": sponsor_code,
            "campaign_code": campaign_code,
            "provider_key": provider_key,
        }.items()
        if value is not None and value.strip()
    }


@router.get("/reports/{report_type}")
async def get_admin_tenant_safe_analytics_report(
    report_type: str,
    tenant_code: Annotated[str, Query(min_length=1)],
    dimensions: Annotated[
        list[str] | None,
        Query(description="Repeatable approved analytics dimensions."),
    ] = None,
    sponsor_code: str | None = Query(default=None),
    campaign_code: str | None = Query(default=None),
    provider_key: str | None = Query(default=None),
    data_window_start: datetime | None = Query(default=None),
    data_window_end: datetime | None = Query(default=None),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_analytics_admin(identity)

    try:
        report = await get_tenant_safe_analytics_report(
            tenant_code=tenant_code,
            report_type=report_type,
            dimensions=dimensions,
            filters=_filters(
                sponsor_code=sponsor_code,
                campaign_code=campaign_code,
                provider_key=provider_key,
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
            "Read-only admin tenant-safe analytics. This endpoint does not "
            "create exports, generate invoices, create billing events, or "
            "mutate funding, settlement, fulfilment, reward, commission, "
            "audit, tenant, or analytics records."
        ),
    }
