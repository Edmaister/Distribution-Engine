from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from services.onboarding.onboarding_readiness_aggregation_service import (
    aggregate_onboarding_readiness,
)
from services.onboarding.onboarding_state_projection_service import (
    project_onboarding_state,
)
from utils.security import require_session_key

router = APIRouter(
    prefix="/admin/onboarding",
    tags=["Admin - Onboarding"],
)

ONBOARDING_ADMIN_ROLES = {
    "ADMIN",
    "SYSTEM_ADMIN",
    "DISTRIBUTION_ADMIN",
    "PLATFORM_ADMIN",
}


def _require_onboarding_admin(identity: dict[str, Any]) -> dict[str, Any]:
    role = str(identity.get("role") or "").upper()
    if role not in ONBOARDING_ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": "API key is not authorised for onboarding state.",
            },
        )
    return identity


def _scope(
    *,
    external_tenant_ref: str | None,
    organisation_ref: str | None,
    producer_ref: str | None,
    sponsor_ref: str | None,
    distributor_ref: str | None,
    campaign_code: str | None,
    opportunity_ref: str | None,
) -> dict[str, str]:
    return {
        key: value.strip()
        for key, value in {
            "external_tenant_ref": external_tenant_ref,
            "organisation_ref": organisation_ref,
            "producer_ref": producer_ref,
            "sponsor_ref": sponsor_ref,
            "distributor_ref": distributor_ref,
            "campaign_code": campaign_code,
            "opportunity_ref": opportunity_ref,
        }.items()
        if value is not None and value.strip()
    }


@router.get("/state")
async def get_admin_onboarding_state(
    external_tenant_ref: str | None = Query(default=None),
    organisation_ref: str | None = Query(default=None),
    producer_ref: str | None = Query(default=None),
    sponsor_ref: str | None = Query(default=None),
    distributor_ref: str | None = Query(default=None),
    campaign_code: str | None = Query(default=None),
    opportunity_ref: str | None = Query(default=None),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_onboarding_admin(identity)
    supplied_scope = _scope(
        external_tenant_ref=external_tenant_ref,
        organisation_ref=organisation_ref,
        producer_ref=producer_ref,
        sponsor_ref=sponsor_ref,
        distributor_ref=distributor_ref,
        campaign_code=campaign_code,
        opportunity_ref=opportunity_ref,
    )
    projection = project_onboarding_state({"scope": supplied_scope})
    readiness = aggregate_onboarding_readiness(projection)

    return {
        "status": "ok",
        "onboarding_state": projection,
        "readiness": readiness,
        "guardrail": (
            "Read-only admin onboarding state. This endpoint uses supplied "
            "external references and explicit shell-only or missing-evidence "
            "markers. It does not create or update onboarding records, create "
            "accounts, send invitations, publish campaigns, create credentials, "
            "deliver webhooks, fund, fulfil, settle, retry, mutate audit, "
            "activate go-live, or move money."
        ),
    }
