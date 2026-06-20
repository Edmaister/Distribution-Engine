from __future__ import annotations

from fastapi import APIRouter, Depends

from services.insurance_journey_proof_service import get_insurance_journey_proof
from services.vertical_readiness_service import get_vertical_readiness
from utils.security import require_finance_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/verticals",
    tags=["Admin - Verticals"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("/readiness")
async def get_admin_vertical_readiness():
    return {
        "status": "ok",
        "readiness": get_vertical_readiness(),
        "proof": {
            "insurance": await get_insurance_journey_proof(),
        },
    }


@router.get("/proof/insurance")
async def get_admin_insurance_journey_proof():
    return {
        "status": "ok",
        "proof": await get_insurance_journey_proof(),
    }
