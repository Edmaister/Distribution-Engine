from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from services.liability_projection_service import get_outcome_liability_projection
from services.outcome_trace_service import OutcomeTraceNotFound, get_outcome_trace
from utils.security import require_session_key

router = APIRouter(prefix="/admin/outcomes", tags=["Admin - Outcomes"])

ALLOWED_OUTCOME_TRACE_ROLES = {
    "ADMIN",
    "SYSTEM_ADMIN",
    "FINANCE_ADMIN",
    "DISTRIBUTION_ADMIN",
    "PLATFORM_ADMIN",
}


def _normalise_tenant_code(tenant_code: str) -> str:
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


def _require_operator_identity(identity: dict, tenant_code: str) -> dict:
    role = str(identity.get("role") or "").upper()
    if role not in ALLOWED_OUTCOME_TRACE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": "API key is not authorised for outcome trace access",
            },
        )

    identity_tenant = (
        str(identity.get("tenant_code") or identity.get("tenant") or "").strip().upper()
    )
    if (
        identity_tenant
        and identity_tenant != "INTERNAL"
        and identity_tenant != tenant_code
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": "API key is not authorised for this tenant",
            },
        )

    return identity


@router.get("/{referral_track_id}/trace")
async def get_admin_outcome_trace(
    referral_track_id: UUID,
    tenant_code: Annotated[str, Query(min_length=1)],
    include_sections: Annotated[list[str] | None, Query()] = None,
    identity: dict = Depends(require_session_key),
):
    resolved_tenant = _normalise_tenant_code(tenant_code)
    operator_identity = _require_operator_identity(identity, resolved_tenant)

    try:
        trace = await get_outcome_trace(
            tenant_code=resolved_tenant,
            referral_track_id=str(referral_track_id),
            identity=operator_identity,
            include_sections=include_sections,
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
                "message": "Outcome trace was not found for the requested tenant.",
            },
        ) from exc

    return {
        "status": "ok",
        "trace": trace,
        "guardrail": (
            "Read-only operator outcome trace. This endpoint does not mutate "
            "reward, funding, fulfilment, settlement, audit, or webhook state."
        ),
    }


@router.get("/{referral_track_id}/liability")
async def get_admin_outcome_liability_projection(
    referral_track_id: UUID,
    tenant_code: Annotated[str, Query(min_length=1)],
    identity: dict = Depends(require_session_key),
):
    resolved_tenant = _normalise_tenant_code(tenant_code)
    operator_identity = _require_operator_identity(identity, resolved_tenant)

    try:
        projection = await get_outcome_liability_projection(
            tenant_code=resolved_tenant,
            referral_track_id=str(referral_track_id),
            identity=operator_identity,
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
                    "Outcome liability projection was not found for the "
                    "requested tenant."
                ),
            },
        ) from exc

    return {
        "status": "ok",
        "projection": projection,
        "guardrail": (
            "Read-only operator liability projection. This endpoint does not "
            "mutate reward, commission, funding, fulfilment, settlement, "
            "audit, or liability state."
        ),
    }
