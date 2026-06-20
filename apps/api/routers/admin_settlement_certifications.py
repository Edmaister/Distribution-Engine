from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from services.fulfilment.settlement.certifications import (
    certify_settlement_period,
    create_settlement_certification,
    get_settlement_certification,
    list_settlement_certifications,
)
from utils.security import require_finance_admin_key as require_admin_key

router = APIRouter(
    prefix="/admin/settlement/certifications",
    tags=["Admin Settlement Certifications"],
    dependencies=[Depends(require_admin_key)],
)


@router.post("")
async def create_certification(payload: dict):
    return await create_settlement_certification(
        tenant_code=payload["tenant_code"],
        period_id=payload["period_id"],
        expected_amount=payload["expected_amount"],
        actual_amount=payload["actual_amount"],
    )


@router.get("")
async def list_certifications(
    tenant_code: str | None = None,
    limit: int = 100,
):
    return await list_settlement_certifications(
        tenant_code=tenant_code,
        limit=limit,
    )


@router.get("/{certification_id}")
async def get_certification(
    certification_id: str,
):
    certification = await get_settlement_certification(
        certification_id,
    )

    if not certification:
        raise HTTPException(
            status_code=404,
            detail="Certification not found",
        )

    return certification


@router.post("/{certification_id}/certify")
async def certify(
    certification_id: str,
    payload: dict,
):
    certification = await certify_settlement_period(
        certification_id=certification_id,
        certified_by=payload["certified_by"],
        certification_notes=payload.get(
            "certification_notes"
        ),
    )

    if not certification:
        raise HTTPException(
            status_code=404,
            detail="Certification not found",
        )

    return certification
