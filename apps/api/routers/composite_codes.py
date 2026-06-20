from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from apps.api.schemas.composite_codes import (
    CompositeCodeValidateRequest,
    CompositeCodeValidateResponse,
)
from services.composite_code_service import validate_composite_code
from utils.security import require_partner_key

router = APIRouter(
    prefix="/composite-codes",
    tags=["Composite Codes"],
    dependencies=[Depends(require_partner_key)],
)


@router.post("/validate", response_model=CompositeCodeValidateResponse)
def validate_composite_code_api(
    req: CompositeCodeValidateRequest,
    identity=Depends(require_partner_key),  # ✅ added
):
    attrs = dict(req.attributes or {})
    if getattr(req, "channel", None):
        attrs["channel"] = req.channel

    body, status = validate_composite_code(
        composite_code=req.composite_code,
        tenant_code=identity["tenant_code"],  # ✅ FIXED
        attributes=attrs,
    )

    if status >= 400:
        return JSONResponse(status_code=status, content=body)

    return body