from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.schemas.multi_currency import (
    ConversionQuoteResponse,
    CreateCrossBorderSettlementRequest,
    CreateFxRateRequest,
    CrossBorderSettlementResponse,
    FxRateResponse,
    QuoteConversionRequest,
)
from services.admin_audit_service import try_write_admin_audit
from services.funding.multi_currency import (
    CurrencyPairError,
    FxRateNotFound,
    MultiCurrencyError,
    create_cross_border_settlement,
    create_fx_rate,
    list_cross_border_settlements,
    list_fx_rates,
    quote_currency_conversion,
)
from utils.security import require_finance_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/multi-currency",
    tags=["Admin Multi-Currency"],
    dependencies=[Depends(require_admin_key)],
)


def _handle_multi_currency_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FxRateNotFound):
        return HTTPException(status_code=404, detail=str(exc))

    if isinstance(exc, (CurrencyPairError, MultiCurrencyError)):
        return HTTPException(status_code=400, detail=str(exc))

    return HTTPException(status_code=500, detail="Unexpected multi-currency error")


@router.post("/fx-rates", response_model=FxRateResponse)
async def create_rate(
    request: CreateFxRateRequest,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        fx_rate = await create_fx_rate(
            tenant_code=request.tenant_code,
            base_currency=request.base_currency,
            quote_currency=request.quote_currency,
            rate=request.rate,
            rate_date=request.rate_date,
            source_system=request.source_system,
            source_reference=request.source_reference,
            metadata=request.metadata,
        )
        await try_write_admin_audit(
            action_type="FX_RATE_UPSERT",
            action_domain="FINANCE",
            identity=identity,
            tenant_code=request.tenant_code,
            target_type="fx_rate",
            target_id=fx_rate.get("fx_rate_id"),
            request_payload=request.model_dump(mode="json"),
            result_payload={
                "fx_rate_id": fx_rate.get("fx_rate_id"),
                "base_currency": fx_rate.get("base_currency"),
                "quote_currency": fx_rate.get("quote_currency"),
                "rate_date": fx_rate.get("rate_date"),
            },
        )
        return fx_rate

    except Exception as exc:
        raise _handle_multi_currency_error(exc) from exc


@router.get("/fx-rates", response_model=list[FxRateResponse])
async def list_rates(
    tenant_code: str = Query(...),
    base_currency: str | None = Query(default=None, min_length=3, max_length=3),
    quote_currency: str | None = Query(default=None, min_length=3, max_length=3),
    rate_status: str | None = Query(default="ACTIVE"),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    try:
        return await list_fx_rates(
            tenant_code=tenant_code,
            base_currency=base_currency,
            quote_currency=quote_currency,
            rate_status=rate_status,
            limit=limit,
        )

    except Exception as exc:
        raise _handle_multi_currency_error(exc) from exc


@router.post("/quotes", response_model=ConversionQuoteResponse)
async def quote_conversion(request: QuoteConversionRequest) -> dict:
    try:
        return await quote_currency_conversion(
            tenant_code=request.tenant_code,
            source_currency=request.source_currency,
            target_currency=request.target_currency,
            source_amount=request.source_amount,
            as_of_date=request.as_of_date,
            persist_quote=request.persist_quote,
            metadata=request.metadata,
        )

    except Exception as exc:
        raise _handle_multi_currency_error(exc) from exc


@router.post("/cross-border-settlements", response_model=CrossBorderSettlementResponse)
async def create_settlement(
    request: CreateCrossBorderSettlementRequest,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        settlement = await create_cross_border_settlement(
            tenant_code=request.tenant_code,
            source_currency=request.source_currency,
            target_currency=request.target_currency,
            source_amount=request.source_amount,
            settlement_id=request.settlement_id,
            sponsor_code=request.sponsor_code,
            distributor_id=request.distributor_id,
            as_of_date=request.as_of_date,
            corridor=request.corridor,
            provider_key=request.provider_key,
            provider_reference=request.provider_reference,
            compliance_status=request.compliance_status,
            metadata=request.metadata,
        )
        await try_write_admin_audit(
            action_type="CROSS_BORDER_SETTLEMENT_CREATE",
            action_domain="FINANCE",
            identity=identity,
            tenant_code=request.tenant_code,
            target_type="cross_border_settlement",
            target_id=settlement.get("cross_border_settlement_id"),
            request_payload=request.model_dump(mode="json"),
            result_payload={
                "cross_border_settlement_id": settlement.get("cross_border_settlement_id"),
                "settlement_status": settlement.get("settlement_status"),
                "source_currency": settlement.get("source_currency"),
                "target_currency": settlement.get("target_currency"),
            },
        )
        return settlement

    except Exception as exc:
        raise _handle_multi_currency_error(exc) from exc


@router.get("/cross-border-settlements", response_model=list[CrossBorderSettlementResponse])
async def list_settlements(
    tenant_code: str = Query(...),
    settlement_status: str | None = Query(default=None),
    sponsor_code: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    return await list_cross_border_settlements(
        tenant_code=tenant_code,
        settlement_status=settlement_status,
        sponsor_code=sponsor_code,
        limit=limit,
    )
