from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services.admin_audit_service import try_write_admin_audit
from services.marketplace_funding.sponsor_billing_service import (
    SponsorBillingError,
    SponsorInvoiceAmountError,
    SponsorInvoiceInvalidState,
    SponsorInvoiceNotFound,
    allocate_sponsor_payment,
    create_sponsor_invoice,
    generate_sponsor_invoice_from_utilisation,
    get_sponsor_billing_dashboard,
    get_sponsor_statement,
    get_sponsor_invoice,
    get_sponsor_payment_receipt,
    get_sponsor_vat_report,
    issue_sponsor_invoice,
    list_sponsor_invoices,
    record_sponsor_invoice_payment,
    reverse_sponsor_payment_allocation,
    reverse_sponsor_invoice_payment,
    run_sponsor_billing_generation,
)
from utils.security import require_finance_admin_key as require_admin_key

router = APIRouter(
    prefix="/admin/funding/sponsor-billing",
    tags=["Sponsor Billing"],
    dependencies=[Depends(require_admin_key)],
)


class SponsorInvoiceLineRequest(BaseModel):
    line_type: str = "UTILISATION"
    description: str
    quantity: Decimal = Field(default=Decimal("1.00"), gt=0)
    unit_amount: Decimal = Field(gt=0)
    reward_id: str | None = None
    allocation_id: str | None = None
    settlement_id: str | None = None
    metadata: dict[str, Any] | None = None


class CreateSponsorInvoiceRequest(BaseModel):
    tenant_code: str
    sponsor_code: str
    sponsor_name: str
    contract_id: str | None = None
    invoice_period_start: date | None = None
    invoice_period_end: date | None = None
    due_date: date | None = None
    currency: str = "ZAR"
    vat_rate: Decimal = Field(default=Decimal("0"), ge=0)
    invoice_number: str | None = None
    metadata: dict[str, Any] | None = None
    lines: list[SponsorInvoiceLineRequest]


class GenerateSponsorInvoiceRequest(BaseModel):
    contract_id: str
    invoice_period_start: date
    invoice_period_end: date
    due_date: date | None = None
    currency: str = "ZAR"
    vat_rate: Decimal = Field(default=Decimal("0"), ge=0)
    invoice_number: str | None = None
    issue: bool = False
    metadata: dict[str, Any] | None = None


class RunSponsorBillingGenerationRequest(BaseModel):
    tenant_code: str
    invoice_period_start: date
    invoice_period_end: date
    due_date: date | None = None
    sponsor_code: str | None = None
    currency: str = "ZAR"
    vat_rate: Decimal = Field(default=Decimal("0"), ge=0)
    issue: bool = False
    dry_run: bool = True
    limit: int = Field(default=500, ge=1, le=2000)
    metadata: dict[str, Any] | None = None


class RecordSponsorPaymentRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    payment_reference: str | None = None
    paid_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class SponsorPaymentAllocationRequest(BaseModel):
    invoice_id: str
    amount: Decimal = Field(gt=0)
    metadata: dict[str, Any] | None = None


class AllocateSponsorPaymentRequest(BaseModel):
    tenant_code: str
    sponsor_code: str
    amount: Decimal = Field(gt=0)
    currency: str = "ZAR"
    payment_reference: str | None = None
    received_at: datetime | None = None
    allocated_by: str | None = None
    metadata: dict[str, Any] | None = None
    allocations: list[SponsorPaymentAllocationRequest]


class ReverseSponsorPaymentRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    reason: str = Field(min_length=1)
    reversed_by: str | None = None
    reversed_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class ReverseSponsorPaymentAllocationRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    reason: str = Field(min_length=1)
    reversed_by: str | None = None
    reversed_at: datetime | None = None
    metadata: dict[str, Any] | None = None


def _handle_billing_error(exc: Exception) -> HTTPException:
    if isinstance(exc, SponsorInvoiceNotFound):
        return HTTPException(status_code=404, detail=str(exc))

    if isinstance(exc, (SponsorInvoiceInvalidState, SponsorInvoiceAmountError)):
        return HTTPException(status_code=400, detail=str(exc))

    if isinstance(exc, SponsorBillingError):
        return HTTPException(status_code=400, detail=str(exc))

    return HTTPException(status_code=500, detail="Unexpected sponsor billing error")


@router.post("/invoices")
async def create_invoice(
    request: CreateSponsorInvoiceRequest,
    identity: dict = Depends(require_admin_key),
) -> dict[str, Any]:
    try:
        invoice = await create_sponsor_invoice(
            tenant_code=request.tenant_code,
            sponsor_code=request.sponsor_code,
            sponsor_name=request.sponsor_name,
            contract_id=request.contract_id,
            invoice_period_start=request.invoice_period_start,
            invoice_period_end=request.invoice_period_end,
            due_date=request.due_date,
            currency=request.currency,
            vat_rate=request.vat_rate,
            invoice_number=request.invoice_number,
            metadata=request.metadata,
            lines=[line.dict() for line in request.lines],
        )
        await try_write_admin_audit(
            action_type="SPONSOR_INVOICE_CREATE",
            action_domain="FINANCE",
            identity=identity,
            tenant_code=request.tenant_code,
            target_type="sponsor_invoice",
            target_id=invoice.get("invoice_id"),
            request_payload=request.model_dump(mode="json"),
            result_payload={
                "invoice_id": invoice.get("invoice_id"),
                "sponsor_code": invoice.get("sponsor_code"),
                "status": invoice.get("status"),
                "total_amount": invoice.get("total_amount"),
            },
        )

        return {"status": "ok", "invoice": invoice}

    except Exception as exc:
        raise _handle_billing_error(exc) from exc


@router.get("/invoices")
async def list_invoices(
    tenant_code: str = Query(...),
    sponsor_code: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    invoices = await list_sponsor_invoices(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        status=status,
        limit=limit,
    )

    return {
        "status": "ok",
        "tenant_code": tenant_code.strip().upper(),
        "count": len(invoices),
        "items": invoices,
    }


@router.get("/statements")
async def get_statement(
    tenant_code: str = Query(...),
    sponsor_code: str = Query(...),
    period_start: date = Query(...),
    period_end: date = Query(...),
    currency: str | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=1000),
) -> dict[str, Any]:
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
        raise _handle_billing_error(exc) from exc


@router.get("/dashboard")
async def get_billing_dashboard(
    tenant_code: str = Query(...),
    sponsor_code: str | None = Query(default=None),
    period_start: date | None = Query(default=None),
    period_end: date | None = Query(default=None),
    currency: str | None = Query(default=None),
    as_of_date: date | None = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=2000),
) -> dict[str, Any]:
    try:
        dashboard = await get_sponsor_billing_dashboard(
            tenant_code=tenant_code,
            sponsor_code=sponsor_code,
            period_start=period_start,
            period_end=period_end,
            currency=currency,
            as_of_date=as_of_date,
            limit=limit,
        )

        return {"status": "ok", "dashboard": dashboard}

    except Exception as exc:
        raise _handle_billing_error(exc) from exc


@router.get("/vat-report")
async def get_vat_report(
    tenant_code: str = Query(...),
    period_start: date = Query(...),
    period_end: date = Query(...),
    sponsor_code: str | None = Query(default=None),
    currency: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=2000, ge=1, le=5000),
) -> dict[str, Any]:
    try:
        report = await get_sponsor_vat_report(
            tenant_code=tenant_code,
            period_start=period_start,
            period_end=period_end,
            sponsor_code=sponsor_code,
            currency=currency,
            status=status,
            limit=limit,
        )

        return {"status": "ok", "report": report}

    except Exception as exc:
        raise _handle_billing_error(exc) from exc


@router.post("/invoices/generate-from-utilisation")
async def generate_invoice_from_utilisation(
    request: GenerateSponsorInvoiceRequest,
    identity: dict = Depends(require_admin_key),
) -> dict[str, Any]:
    try:
        invoice = await generate_sponsor_invoice_from_utilisation(
            contract_id=request.contract_id,
            invoice_period_start=request.invoice_period_start,
            invoice_period_end=request.invoice_period_end,
            due_date=request.due_date,
            currency=request.currency,
            vat_rate=request.vat_rate,
            invoice_number=request.invoice_number,
            issue=request.issue,
            metadata=request.metadata,
        )
        await try_write_admin_audit(
            action_type="SPONSOR_INVOICE_GENERATE_FROM_UTILISATION",
            action_domain="FINANCE",
            identity=identity,
            target_type="funding_contract",
            target_id=request.contract_id,
            request_payload=request.model_dump(mode="json"),
            result_payload={
                "invoice_id": invoice.get("invoice_id"),
                "status": invoice.get("status"),
            },
        )

        return {"status": "ok", "invoice": invoice}

    except Exception as exc:
        raise _handle_billing_error(exc) from exc


@router.post("/scheduled-generation")
async def scheduled_generation(
    request: RunSponsorBillingGenerationRequest,
    identity: dict = Depends(require_admin_key),
) -> dict[str, Any]:
    try:
        result = await run_sponsor_billing_generation(
            tenant_code=request.tenant_code,
            sponsor_code=request.sponsor_code,
            invoice_period_start=request.invoice_period_start,
            invoice_period_end=request.invoice_period_end,
            due_date=request.due_date,
            currency=request.currency,
            vat_rate=request.vat_rate,
            issue=request.issue,
            dry_run=request.dry_run,
            limit=request.limit,
            metadata=request.metadata,
        )
        await try_write_admin_audit(
            action_type="SPONSOR_BILLING_SCHEDULED_GENERATION",
            action_domain="FINANCE",
            identity=identity,
            tenant_code=request.tenant_code,
            target_type="sponsor_billing_generation",
            target_id=request.sponsor_code,
            request_payload=request.model_dump(mode="json"),
            result_payload={
                "dry_run": result.get("dry_run"),
                "contract_count": result.get("contract_count"),
                "generated_count": result.get("generated_count"),
            },
        )

        return {"status": "ok", "generation": result}

    except Exception as exc:
        raise _handle_billing_error(exc) from exc


@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str) -> dict[str, Any]:
    try:
        invoice = await get_sponsor_invoice(invoice_id=invoice_id)
        return {"status": "ok", "invoice": invoice}

    except Exception as exc:
        raise _handle_billing_error(exc) from exc


@router.post("/invoices/{invoice_id}/issue")
async def issue_invoice(
    invoice_id: str,
    identity: dict = Depends(require_admin_key),
) -> dict[str, Any]:
    try:
        invoice = await issue_sponsor_invoice(invoice_id=invoice_id)
        await try_write_admin_audit(
            action_type="SPONSOR_INVOICE_ISSUE",
            action_domain="FINANCE",
            identity=identity,
            tenant_code=invoice.get("tenant_code"),
            target_type="sponsor_invoice",
            target_id=invoice_id,
            result_payload={
                "invoice_id": invoice.get("invoice_id"),
                "status": invoice.get("status"),
            },
        )
        return {"status": "ok", "invoice": invoice}

    except Exception as exc:
        raise _handle_billing_error(exc) from exc


@router.post("/invoices/{invoice_id}/payments")
async def record_payment(
    invoice_id: str,
    request: RecordSponsorPaymentRequest,
    identity: dict = Depends(require_admin_key),
) -> dict[str, Any]:
    try:
        result = await record_sponsor_invoice_payment(
            invoice_id=invoice_id,
            amount=request.amount,
            payment_reference=request.payment_reference,
            paid_at=request.paid_at,
            metadata=request.metadata,
        )
        await try_write_admin_audit(
            action_type="SPONSOR_INVOICE_PAYMENT_RECORD",
            action_domain="FINANCE",
            identity=identity,
            tenant_code=result.get("invoice", {}).get("tenant_code"),
            target_type="sponsor_invoice",
            target_id=invoice_id,
            request_payload=request.model_dump(mode="json"),
            result_payload={
                "payment_id": result.get("payment", {}).get("payment_id"),
                "invoice_status": result.get("invoice", {}).get("status"),
            },
        )

        return {"status": "ok", **result}

    except Exception as exc:
        raise _handle_billing_error(exc) from exc


@router.post("/payment-receipts")
async def allocate_payment_receipt(
    request: AllocateSponsorPaymentRequest,
    identity: dict = Depends(require_admin_key),
) -> dict[str, Any]:
    try:
        result = await allocate_sponsor_payment(
            tenant_code=request.tenant_code,
            sponsor_code=request.sponsor_code,
            amount=request.amount,
            currency=request.currency,
            payment_reference=request.payment_reference,
            received_at=request.received_at,
            allocated_by=request.allocated_by,
            metadata=request.metadata,
            allocations=[allocation.dict() for allocation in request.allocations],
        )
        await try_write_admin_audit(
            action_type="SPONSOR_PAYMENT_RECEIPT_ALLOCATE",
            action_domain="FINANCE",
            identity=identity,
            tenant_code=request.tenant_code,
            target_type="sponsor_payment_receipt",
            target_id=result.get("receipt", {}).get("receipt_id"),
            request_payload=request.model_dump(mode="json"),
            result_payload={
                "receipt_id": result.get("receipt", {}).get("receipt_id"),
                "allocation_count": len(result.get("allocations", [])),
            },
        )

        return {"status": "ok", **result}

    except Exception as exc:
        raise _handle_billing_error(exc) from exc


@router.get("/payment-receipts/{receipt_id}")
async def get_payment_receipt(receipt_id: str) -> dict[str, Any]:
    try:
        receipt = await get_sponsor_payment_receipt(receipt_id=receipt_id)
        return {"status": "ok", "receipt": receipt}

    except Exception as exc:
        raise _handle_billing_error(exc) from exc


@router.post("/payments/{payment_id}/reversals")
async def reverse_payment(
    payment_id: str,
    request: ReverseSponsorPaymentRequest,
    identity: dict = Depends(require_admin_key),
) -> dict[str, Any]:
    try:
        result = await reverse_sponsor_invoice_payment(
            payment_id=payment_id,
            amount=request.amount,
            reason=request.reason,
            reversed_by=request.reversed_by,
            reversed_at=request.reversed_at,
            metadata=request.metadata,
        )
        await try_write_admin_audit(
            action_type="SPONSOR_PAYMENT_REVERSE",
            action_domain="FINANCE",
            identity=identity,
            target_type="sponsor_payment",
            target_id=payment_id,
            reason=request.reason,
            request_payload=request.model_dump(mode="json"),
            result_payload={
                "reversal_id": result.get("reversal", {}).get("reversal_id"),
                "payment_id": payment_id,
            },
        )

        return {"status": "ok", **result}

    except Exception as exc:
        raise _handle_billing_error(exc) from exc


@router.post("/payment-allocations/{allocation_id}/reversals")
async def reverse_payment_allocation(
    allocation_id: str,
    request: ReverseSponsorPaymentAllocationRequest,
    identity: dict = Depends(require_admin_key),
) -> dict[str, Any]:
    try:
        result = await reverse_sponsor_payment_allocation(
            allocation_id=allocation_id,
            amount=request.amount,
            reason=request.reason,
            reversed_by=request.reversed_by,
            reversed_at=request.reversed_at,
            metadata=request.metadata,
        )
        await try_write_admin_audit(
            action_type="SPONSOR_PAYMENT_ALLOCATION_REVERSE",
            action_domain="FINANCE",
            identity=identity,
            target_type="sponsor_payment_allocation",
            target_id=allocation_id,
            reason=request.reason,
            request_payload=request.model_dump(mode="json"),
            result_payload={
                "reversal_id": result.get("reversal", {}).get("reversal_id"),
                "allocation_id": allocation_id,
            },
        )

        return {"status": "ok", **result}

    except Exception as exc:
        raise _handle_billing_error(exc) from exc
