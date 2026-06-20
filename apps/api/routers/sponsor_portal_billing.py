from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from services.funding.forecasting import (
    DEFAULT_BUFFER_DAYS,
    DEFAULT_BURN_WINDOW_DAYS,
    get_sponsor_funding_forecast,
)
from services.marketplace_funding.funding_contract_service import (
    FundingContractError,
    FundingContractNotFound,
    get_funding_contract,
    get_funding_contract_ledger,
    list_funding_contracts,
)
from services.marketplace_funding.sponsor_billing_service import (
    SponsorBillingError,
    SponsorInvoiceAmountError,
    SponsorInvoiceInvalidState,
    SponsorInvoiceNotFound,
    get_sponsor_billing_dashboard,
    get_sponsor_invoice,
    get_sponsor_payment_receipt,
    get_sponsor_statement,
    list_sponsor_invoices,
    list_sponsor_payment_receipts,
)
from services.marketplace_funding.sponsor_wallet_service import (
    get_sponsor_wallet_by_sponsor,
)
from services.marketplace_funding.sponsor_wallet_ledger_service import (
    list_sponsor_wallet_transactions,
)
from utils.security import require_admin_or_partner_key


router = APIRouter(
    prefix="/v1/tenants/{tenant_code}/sponsors/{sponsor_code}/billing",
    tags=["Sponsor Portal - Billing"],
)


def _normalise_code(value: str) -> str:
    return value.strip().upper()


def _enforce_tenant_access(identity: dict[str, Any], tenant_code: str) -> None:
    role = str(identity.get("role", "")).upper()
    key_tenant = str(identity.get("tenant_code", "")).upper()
    request_tenant = _normalise_code(tenant_code)

    if role == "ADMIN":
        return

    if role not in {"PARTNER", "TENANT_ADMIN"}:
        raise HTTPException(
            status_code=403,
            detail="API key is not authorised for this tenant",
        )

    if not key_tenant or key_tenant != request_tenant:
        raise HTTPException(
            status_code=403,
            detail="API key is not authorised for this tenant",
        )


def _handle_portal_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FundingContractNotFound):
        return HTTPException(status_code=404, detail=str(exc))

    if isinstance(exc, FundingContractError):
        return HTTPException(status_code=400, detail=str(exc))

    if isinstance(exc, SponsorInvoiceNotFound):
        return HTTPException(status_code=404, detail=str(exc))

    if isinstance(exc, (SponsorInvoiceInvalidState, SponsorInvoiceAmountError)):
        return HTTPException(status_code=400, detail=str(exc))

    if isinstance(exc, SponsorBillingError):
        return HTTPException(status_code=400, detail=str(exc))

    return HTTPException(status_code=500, detail="Unexpected sponsor portal billing error")


def _enforce_sponsor_invoice(
    *,
    invoice: dict[str, Any],
    tenant_code: str,
    sponsor_code: str,
) -> None:
    if (
        invoice.get("tenant_code") != _normalise_code(tenant_code)
        or invoice.get("sponsor_code") != _normalise_code(sponsor_code)
    ):
        raise HTTPException(status_code=404, detail="Sponsor invoice not found")


def _enforce_sponsor_receipt(
    *,
    receipt: dict[str, Any],
    tenant_code: str,
    sponsor_code: str,
) -> None:
    if (
        receipt.get("tenant_code") != _normalise_code(tenant_code)
        or receipt.get("sponsor_code") != _normalise_code(sponsor_code)
    ):
        raise HTTPException(status_code=404, detail="Sponsor payment receipt not found")


def _enforce_sponsor_contract(
    *,
    contract: dict[str, Any],
    tenant_code: str,
    sponsor_code: str,
) -> None:
    if (
        contract.get("tenant_code") != _normalise_code(tenant_code)
        or contract.get("sponsor_code") != _normalise_code(sponsor_code)
    ):
        raise HTTPException(status_code=404, detail="Funding contract not found")


@router.get("/dashboard")
async def get_portal_dashboard(
    tenant_code: str,
    sponsor_code: str,
    period_start: date | None = Query(default=None),
    period_end: date | None = Query(default=None),
    currency: str | None = Query(default=None),
    as_of_date: date | None = Query(default=None),
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)

    try:
        dashboard = await get_sponsor_billing_dashboard(
            tenant_code=tenant_code,
            sponsor_code=sponsor_code,
            period_start=period_start,
            period_end=period_end,
            currency=currency,
            as_of_date=as_of_date,
        )
        return {"status": "ok", "dashboard": dashboard}

    except Exception as exc:
        raise _handle_portal_error(exc) from exc


@router.get("/invoices")
async def list_portal_invoices(
    tenant_code: str,
    sponsor_code: str,
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)

    invoices = await list_sponsor_invoices(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        status=status,
        limit=limit,
    )

    return {
        "status": "ok",
        "tenant_code": _normalise_code(tenant_code),
        "sponsor_code": _normalise_code(sponsor_code),
        "count": len(invoices),
        "items": invoices,
    }


@router.get("/invoices/{invoice_id}")
async def get_portal_invoice(
    tenant_code: str,
    sponsor_code: str,
    invoice_id: str,
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)

    try:
        invoice = await get_sponsor_invoice(invoice_id=invoice_id)
        _enforce_sponsor_invoice(
            invoice=invoice,
            tenant_code=tenant_code,
            sponsor_code=sponsor_code,
        )
        return {"status": "ok", "invoice": invoice}

    except HTTPException:
        raise
    except Exception as exc:
        raise _handle_portal_error(exc) from exc


@router.get("/statements")
async def get_portal_statement(
    tenant_code: str,
    sponsor_code: str,
    period_start: date = Query(...),
    period_end: date = Query(...),
    currency: str | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=1000),
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)

    try:
        statement = await get_sponsor_statement(
            tenant_code=tenant_code,
            sponsor_code=sponsor_code,
            period_start=period_start,
            period_end=period_end,
            currency=currency,
            limit=limit,
        )
        return {"status": "ok", "statement": statement}

    except Exception as exc:
        raise _handle_portal_error(exc) from exc


@router.get("/payment-receipts")
async def list_portal_payment_receipts(
    tenant_code: str,
    sponsor_code: str,
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)

    receipts = await list_sponsor_payment_receipts(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        status=status,
        limit=limit,
    )

    return {
        "status": "ok",
        "tenant_code": _normalise_code(tenant_code),
        "sponsor_code": _normalise_code(sponsor_code),
        "count": len(receipts),
        "items": receipts,
    }


@router.get("/payment-receipts/{receipt_id}")
async def get_portal_payment_receipt(
    tenant_code: str,
    sponsor_code: str,
    receipt_id: str,
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)

    try:
        receipt = await get_sponsor_payment_receipt(receipt_id=receipt_id)
        _enforce_sponsor_receipt(
            receipt=receipt,
            tenant_code=tenant_code,
            sponsor_code=sponsor_code,
        )
        return {"status": "ok", "receipt": receipt}

    except HTTPException:
        raise
    except Exception as exc:
        raise _handle_portal_error(exc) from exc


@router.get("/wallet")
async def get_portal_wallet(
    tenant_code: str,
    sponsor_code: str,
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)

    wallet = await get_sponsor_wallet_by_sponsor(
        tenant_code=_normalise_code(tenant_code),
        sponsor_code=_normalise_code(sponsor_code),
    )

    if not wallet:
        raise HTTPException(status_code=404, detail="Sponsor wallet not found")

    return {"status": "ok", "wallet": wallet}


@router.get("/wallet/ledger")
async def get_portal_wallet_ledger(
    tenant_code: str,
    sponsor_code: str,
    limit: int = Query(default=100, ge=1, le=500),
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)

    wallet = await get_sponsor_wallet_by_sponsor(
        tenant_code=_normalise_code(tenant_code),
        sponsor_code=_normalise_code(sponsor_code),
    )

    if not wallet:
        raise HTTPException(status_code=404, detail="Sponsor wallet not found")

    ledger = await list_sponsor_wallet_transactions(
        wallet_id=str(wallet["wallet_id"]),
        limit=limit,
    )

    return {
        "status": "ok",
        "tenant_code": _normalise_code(tenant_code),
        "sponsor_code": _normalise_code(sponsor_code),
        "wallet_id": str(wallet["wallet_id"]),
        "count": len(ledger),
        "items": ledger,
    }


@router.get("/contracts")
async def list_portal_contracts(
    tenant_code: str,
    sponsor_code: str,
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)

    contracts = await list_funding_contracts(
        tenant_code=_normalise_code(tenant_code),
        sponsor_code=_normalise_code(sponsor_code),
        status=status,
        limit=limit,
    )

    return {
        "status": "ok",
        "tenant_code": _normalise_code(tenant_code),
        "sponsor_code": _normalise_code(sponsor_code),
        "count": len(contracts),
        "items": contracts,
    }


@router.get("/contracts/{contract_id}")
async def get_portal_contract(
    tenant_code: str,
    sponsor_code: str,
    contract_id: str,
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)

    try:
        contract = await get_funding_contract(contract_id=contract_id)
        _enforce_sponsor_contract(
            contract=contract,
            tenant_code=tenant_code,
            sponsor_code=sponsor_code,
        )
        return {"status": "ok", "contract": contract}

    except HTTPException:
        raise
    except Exception as exc:
        raise _handle_portal_error(exc) from exc


@router.get("/contracts/{contract_id}/ledger")
async def get_portal_contract_ledger(
    tenant_code: str,
    sponsor_code: str,
    contract_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)

    try:
        contract = await get_funding_contract(contract_id=contract_id)
        _enforce_sponsor_contract(
            contract=contract,
            tenant_code=tenant_code,
            sponsor_code=sponsor_code,
        )
        ledger = await get_funding_contract_ledger(
            contract_id=contract_id,
            limit=limit,
        )
        return {
            "status": "ok",
            "contract_id": contract_id,
            "count": len(ledger),
            "items": ledger,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise _handle_portal_error(exc) from exc


@router.get("/forecast")
async def get_portal_forecast(
    tenant_code: str,
    sponsor_code: str,
    currency: str = Query(default="ZAR"),
    burn_window_days: int = Query(default=DEFAULT_BURN_WINDOW_DAYS, ge=1, le=365),
    buffer_days: int = Query(default=DEFAULT_BUFFER_DAYS, ge=1, le=365),
    identity: dict[str, Any] = Depends(require_admin_or_partner_key),
) -> dict[str, Any]:
    _enforce_tenant_access(identity, tenant_code)

    forecast = await get_sponsor_funding_forecast(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        currency=currency,
        burn_window_days=burn_window_days,
        buffer_days=buffer_days,
    )

    if not forecast:
        raise HTTPException(status_code=404, detail="Sponsor funding forecast not found")

    return {"status": "ok", "forecast": forecast}
