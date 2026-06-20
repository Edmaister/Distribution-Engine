from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.schemas.distribution.distributors import (
    CreateDistributorRequest,
    UpdateDistributorProfileRequest,
)
from services.admin_audit_service import try_write_admin_audit
from services.distribution.distributor_service import (
    DistributorDuplicate,
    DistributorError,
    DistributorNotFound,
    activate_distributor,
    create_distributor,
    get_distributor,
    list_distributors,
    suspend_distributor,
    terminate_distributor,
    update_distributor_profile,
)
from utils.security import require_distribution_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/distribution/distributors",
    tags=["Admin Distribution Distributors"],
    dependencies=[Depends(require_admin_key)],
)


def _handle_distributor_error(exc: Exception) -> HTTPException:
    if isinstance(exc, DistributorNotFound):
        return HTTPException(status_code=404, detail=str(exc))

    if isinstance(exc, DistributorDuplicate):
        return HTTPException(status_code=409, detail=str(exc))

    if isinstance(exc, DistributorError):
        return HTTPException(status_code=400, detail=str(exc))

    return HTTPException(status_code=500, detail="Unexpected distributor error")


@router.post("")
async def create_distribution_distributor(
    request: CreateDistributorRequest,
    identity: dict = Depends(require_admin_key),
) -> dict[str, Any]:
    try:
        distributor = await create_distributor(
            tenant_code=request.tenant_code,
            distributor_code=request.distributor_code,
            distributor_name=request.distributor_name,
            distributor_type=request.distributor_type,
            contact_email=request.contact_email,
            contact_phone=request.contact_phone,
            channels=request.channels,
            segments=request.segments,
            regions=request.regions,
            capabilities=request.capabilities,
            eligibility=request.eligibility,
            operating_limits=request.operating_limits,
            metadata=request.metadata,
        )
        await try_write_admin_audit(
            action_type="DISTRIBUTOR_CREATE",
            action_domain="DISTRIBUTION",
            identity=identity,
            tenant_code=request.tenant_code,
            target_type="distributor",
            target_id=distributor.get("distributor_id"),
            request_payload=request.model_dump(mode="json"),
            result_payload={
                "distributor_id": distributor.get("distributor_id"),
                "distributor_code": distributor.get("distributor_code"),
                "status": distributor.get("status"),
            },
        )

        return {"status": "ok", "distributor": distributor}

    except Exception as exc:
        raise _handle_distributor_error(exc) from exc


@router.get("")
async def list_distribution_distributors(
    tenant_code: str = Query(...),
    status: str | None = Query(default=None),
    distributor_type: str | None = Query(default=None),
    segment: str | None = Query(default=None),
    region: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    distributors = await list_distributors(
        tenant_code=tenant_code,
        status=status,
        distributor_type=distributor_type,
        segment=segment,
        region=region,
        limit=limit,
    )

    return {
        "status": "ok",
        "tenant_code": tenant_code,
        "count": len(distributors),
        "items": distributors,
    }


@router.get("/{distributor_id}")
async def get_distribution_distributor(distributor_id: str) -> dict[str, Any]:
    try:
        distributor = await get_distributor(distributor_id=distributor_id)
        return {"status": "ok", "distributor": distributor}

    except Exception as exc:
        raise _handle_distributor_error(exc) from exc


@router.patch("/{distributor_id}/profile")
async def update_distribution_distributor_profile(
    distributor_id: str,
    request: UpdateDistributorProfileRequest,
) -> dict[str, Any]:
    try:
        distributor = await update_distributor_profile(
            distributor_id=distributor_id,
            distributor_name=request.distributor_name,
            contact_email=request.contact_email,
            contact_phone=request.contact_phone,
            channels=request.channels,
            segments=request.segments,
            regions=request.regions,
            capabilities=request.capabilities,
            eligibility=request.eligibility,
            operating_limits=request.operating_limits,
            metadata=request.metadata,
        )

        return {"status": "ok", "distributor": distributor}

    except Exception as exc:
        raise _handle_distributor_error(exc) from exc


@router.post("/{distributor_id}/activate")
async def activate_distribution_distributor(
    distributor_id: str,
    identity: dict = Depends(require_admin_key),
) -> dict[str, Any]:
    try:
        distributor = await activate_distributor(distributor_id=distributor_id)
        await try_write_admin_audit(
            action_type="DISTRIBUTOR_ACTIVATE",
            action_domain="DISTRIBUTION",
            identity=identity,
            tenant_code=distributor.get("tenant_code"),
            target_type="distributor",
            target_id=distributor_id,
            result_payload={"status": distributor.get("status")},
        )
        return {"status": "ok", "distributor": distributor}

    except Exception as exc:
        raise _handle_distributor_error(exc) from exc


@router.post("/{distributor_id}/suspend")
async def suspend_distribution_distributor(
    distributor_id: str,
    identity: dict = Depends(require_admin_key),
) -> dict[str, Any]:
    try:
        distributor = await suspend_distributor(distributor_id=distributor_id)
        await try_write_admin_audit(
            action_type="DISTRIBUTOR_SUSPEND",
            action_domain="DISTRIBUTION",
            identity=identity,
            tenant_code=distributor.get("tenant_code"),
            target_type="distributor",
            target_id=distributor_id,
            result_payload={"status": distributor.get("status")},
        )
        return {"status": "ok", "distributor": distributor}

    except Exception as exc:
        raise _handle_distributor_error(exc) from exc


@router.post("/{distributor_id}/terminate")
async def terminate_distribution_distributor(
    distributor_id: str,
    identity: dict = Depends(require_admin_key),
) -> dict[str, Any]:
    try:
        distributor = await terminate_distributor(distributor_id=distributor_id)
        await try_write_admin_audit(
            action_type="DISTRIBUTOR_TERMINATE",
            action_domain="DISTRIBUTION",
            identity=identity,
            tenant_code=distributor.get("tenant_code"),
            target_type="distributor",
            target_id=distributor_id,
            result_payload={"status": distributor.get("status")},
        )
        return {"status": "ok", "distributor": distributor}

    except Exception as exc:
        raise _handle_distributor_error(exc) from exc
