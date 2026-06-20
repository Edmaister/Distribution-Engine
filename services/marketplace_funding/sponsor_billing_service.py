from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import uuid4

from services.marketplace_funding.sponsor_billing_repository import (
    apply_invoice_payment_amount,
    apply_invoice_payment_reversal_amount,
    apply_payment_receipt_allocation_amount,
    create_invoice_line_record,
    create_invoice_payment_record,
    create_invoice_payment_reversal_record,
    create_invoice_record,
    create_payment_allocation_record,
    create_payment_allocation_reversal_record,
    create_payment_receipt_record,
    get_invoice_record,
    get_invoice_payment_record,
    get_payment_allocation_record,
    get_payment_receipt_record,
    get_reversed_payment_amount,
    get_reversed_payment_allocation_amount,
    issue_invoice_record,
    list_billing_dashboard_invoice_records,
    list_invoice_line_records,
    list_invoice_payment_records,
    list_invoice_payment_reversal_records,
    list_payment_allocation_records,
    list_payment_receipt_records,
    list_invoice_records,
    list_statement_invoice_records,
    list_statement_payment_records,
    list_unbilled_contract_utilisation,
    list_vat_report_invoice_records,
    reverse_payment_receipt_allocation_amount,
)
from services.marketplace_funding.funding_contract_service import list_funding_contracts


class SponsorBillingError(Exception):
    pass


class SponsorInvoiceNotFound(SponsorBillingError):
    pass


class SponsorInvoiceInvalidState(SponsorBillingError):
    pass


class SponsorInvoiceAmountError(SponsorBillingError):
    pass


MONEY_PLACES = Decimal("0.01")


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def _normalise_code(value: str) -> str:
    return value.strip().upper()


def _generate_invoice_number(*, tenant_code: str) -> str:
    today = date.today().strftime("%Y%m%d")
    return f"INV-{tenant_code}-{today}-{uuid4().hex[:8].upper()}"


def _calculate_line_amount(
    *,
    quantity: Decimal | int | float | str,
    unit_amount: Decimal | int | float | str,
) -> Decimal:
    qty = _to_decimal(quantity)
    unit = _to_decimal(unit_amount)

    if qty <= 0 or unit <= 0:
        raise SponsorInvoiceAmountError("Invoice line quantity and unit amount must be positive")

    return (qty * unit).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def _sum_money(items: list[dict[str, Any]], key: str) -> Decimal:
    total = Decimal("0.00")
    for item in items:
        total += _to_decimal(item.get(key) or 0)
    return total


async def create_sponsor_invoice(
    *,
    tenant_code: str,
    sponsor_code: str,
    sponsor_name: str,
    lines: list[dict[str, Any]],
    contract_id: str | None = None,
    invoice_period_start: date | None = None,
    invoice_period_end: date | None = None,
    due_date: date | None = None,
    currency: str = "ZAR",
    vat_rate: Decimal | int | float | str = 0,
    invoice_number: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not lines:
        raise SponsorInvoiceAmountError("Invoice must contain at least one line")

    tenant = _normalise_code(tenant_code)
    sponsor = _normalise_code(sponsor_code)
    resolved_currency = _normalise_code(currency)

    prepared_lines: list[dict[str, Any]] = []
    subtotal = Decimal("0.00")

    for line in lines:
        line_amount = _calculate_line_amount(
            quantity=line.get("quantity", 1),
            unit_amount=line["unit_amount"],
        )
        subtotal += line_amount
        prepared_lines.append(
            {
                "line_type": _normalise_code(line.get("line_type", "UTILISATION")),
                "description": str(line["description"]),
                "quantity": _to_decimal(line.get("quantity", 1)),
                "unit_amount": _to_decimal(line["unit_amount"]),
                "line_amount": line_amount,
                "reward_id": line.get("reward_id"),
                "allocation_id": line.get("allocation_id"),
                "settlement_id": line.get("settlement_id"),
                "source_ledger_id": line.get("source_ledger_id"),
                "metadata": line.get("metadata"),
            }
        )

    rate = Decimal(str(vat_rate))
    if rate < 0:
        raise SponsorInvoiceAmountError("VAT rate cannot be negative")

    vat_amount = (subtotal * rate).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)
    total = (subtotal + vat_amount).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)

    invoice = await create_invoice_record(
        tenant_code=tenant,
        sponsor_code=sponsor,
        sponsor_name=sponsor_name,
        invoice_number=invoice_number or _generate_invoice_number(tenant_code=tenant),
        contract_id=contract_id,
        invoice_period_start=invoice_period_start,
        invoice_period_end=invoice_period_end,
        due_date=due_date,
        currency=resolved_currency,
        subtotal_amount=subtotal,
        vat_amount=vat_amount,
        total_amount=total,
        metadata=metadata,
    )

    created_lines = []
    for line in prepared_lines:
        created_lines.append(
            await create_invoice_line_record(
                invoice_id=invoice["invoice_id"],
                **line,
            )
        )

    return {
        **invoice,
        "lines": created_lines,
    }


async def generate_sponsor_invoice_from_utilisation(
    *,
    contract_id: str,
    invoice_period_start: date,
    invoice_period_end: date,
    due_date: date | None = None,
    currency: str = "ZAR",
    vat_rate: Decimal | int | float | str = 0,
    invoice_number: str | None = None,
    issue: bool = False,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if invoice_period_end < invoice_period_start:
        raise SponsorInvoiceInvalidState("Invoice period end cannot be before period start")

    entries = await list_unbilled_contract_utilisation(
        contract_id=contract_id,
        period_start=invoice_period_start,
        period_end=invoice_period_end,
    )

    if not entries:
        raise SponsorInvoiceAmountError("No unbilled contract utilisation found")

    first_entry = entries[0]
    lines = []

    for entry in entries:
        occurred_on = entry["created_at"].date() if entry.get("created_at") else invoice_period_end
        metadata_payload = {
            "source": "funding_contract_ledger",
            "ledger_id": str(entry["ledger_id"]),
            "correlation_id": entry.get("correlation_id"),
            "ledger_metadata": entry.get("metadata") or {},
        }
        lines.append(
            {
                "line_type": "UTILISATION",
                "description": f"Contract utilisation on {occurred_on.isoformat()}",
                "quantity": Decimal("1.00"),
                "unit_amount": _to_decimal(entry["amount"]),
                "reward_id": str(entry["reward_id"]) if entry.get("reward_id") else None,
                "allocation_id": str(entry["allocation_id"]) if entry.get("allocation_id") else None,
                "source_ledger_id": str(entry["ledger_id"]),
                "metadata": metadata_payload,
            }
        )

    invoice = await create_sponsor_invoice(
        tenant_code=first_entry["tenant_code"],
        sponsor_code=first_entry["sponsor_code"],
        sponsor_name=first_entry["sponsor_name"],
        contract_id=contract_id,
        invoice_period_start=invoice_period_start,
        invoice_period_end=invoice_period_end,
        due_date=due_date,
        currency=currency,
        vat_rate=vat_rate,
        invoice_number=invoice_number,
        metadata={
            **(metadata or {}),
            "generated_from": "BUDGET_UTILISED",
            "source_ledger_count": len(entries),
        },
        lines=lines,
    )

    if issue:
        issued = await issue_sponsor_invoice(invoice_id=invoice["invoice_id"])
        return {
            **issued,
            "lines": invoice["lines"],
        }

    return invoice


async def run_sponsor_billing_generation(
    *,
    tenant_code: str,
    invoice_period_start: date,
    invoice_period_end: date,
    due_date: date | None = None,
    sponsor_code: str | None = None,
    currency: str = "ZAR",
    vat_rate: Decimal | int | float | str = 0,
    issue: bool = False,
    dry_run: bool = True,
    limit: int = 500,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if invoice_period_end < invoice_period_start:
        raise SponsorInvoiceInvalidState("Billing period end cannot be before period start")

    tenant = _normalise_code(tenant_code)
    sponsor = _normalise_code(sponsor_code) if sponsor_code else None
    resolved_currency = _normalise_code(currency)

    contracts = await list_funding_contracts(
        tenant_code=tenant,
        sponsor_code=sponsor,
        status="ACTIVE",
        limit=limit,
    )

    items: list[dict[str, Any]] = []
    ready_count = 0
    generated_count = 0
    skipped_count = 0
    failed_count = 0
    total_unbilled_amount = Decimal("0.00")

    for contract in contracts:
        contract_id = str(contract["contract_id"])
        item = {
            "contract_id": contract_id,
            "sponsor_code": contract.get("sponsor_code"),
            "sponsor_name": contract.get("sponsor_name"),
        }

        try:
            entries = await list_unbilled_contract_utilisation(
                contract_id=contract_id,
                period_start=invoice_period_start,
                period_end=invoice_period_end,
            )

            unbilled_amount = _sum_money(entries, "amount")
            total_unbilled_amount += unbilled_amount

            if not entries:
                skipped_count += 1
                items.append(
                    {
                        **item,
                        "status": "SKIPPED",
                        "reason": "No unbilled contract utilisation found",
                        "unbilled_count": 0,
                        "unbilled_amount": Decimal("0.00"),
                    }
                )
                continue

            if dry_run:
                ready_count += 1
                items.append(
                    {
                        **item,
                        "status": "READY",
                        "unbilled_count": len(entries),
                        "unbilled_amount": unbilled_amount,
                    }
                )
                continue

            invoice = await generate_sponsor_invoice_from_utilisation(
                contract_id=contract_id,
                invoice_period_start=invoice_period_start,
                invoice_period_end=invoice_period_end,
                due_date=due_date,
                currency=resolved_currency,
                vat_rate=vat_rate,
                issue=issue,
                metadata={
                    **(metadata or {}),
                    "generation_source": "scheduled_sponsor_billing",
                    "scheduled_generation_dry_run": False,
                },
            )
            generated_count += 1
            items.append(
                {
                    **item,
                    "status": "GENERATED",
                    "unbilled_count": len(entries),
                    "unbilled_amount": unbilled_amount,
                    "invoice": invoice,
                }
            )

        except Exception as exc:
            failed_count += 1
            items.append(
                {
                    **item,
                    "status": "FAILED",
                    "error": str(exc),
                }
            )

    return {
        "tenant_code": tenant,
        "sponsor_code": sponsor,
        "invoice_period_start": invoice_period_start,
        "invoice_period_end": invoice_period_end,
        "due_date": due_date,
        "currency": resolved_currency,
        "vat_rate": Decimal(str(vat_rate)),
        "issue": issue,
        "dry_run": dry_run,
        "contract_count": len(contracts),
        "ready_count": ready_count,
        "generated_count": generated_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count,
        "total_unbilled_amount": total_unbilled_amount,
        "items": items,
    }


async def get_sponsor_invoice(*, invoice_id: str) -> dict[str, Any]:
    invoice = await get_invoice_record(invoice_id=invoice_id)

    if not invoice:
        raise SponsorInvoiceNotFound("Sponsor invoice not found")

    lines = await list_invoice_line_records(invoice_id=invoice_id)
    payments = await list_invoice_payment_records(invoice_id=invoice_id)
    reversals = await list_invoice_payment_reversal_records(invoice_id=invoice_id)

    return {
        **invoice,
        "lines": lines,
        "payments": payments,
        "payment_reversals": reversals,
    }


async def list_sponsor_invoices(
    *,
    tenant_code: str,
    sponsor_code: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    return await list_invoice_records(
        tenant_code=_normalise_code(tenant_code),
        sponsor_code=_normalise_code(sponsor_code) if sponsor_code else None,
        status=_normalise_code(status) if status else None,
        limit=limit,
    )


async def get_sponsor_statement(
    *,
    tenant_code: str,
    sponsor_code: str,
    period_start: date,
    period_end: date,
    currency: str | None = None,
    limit: int = 500,
) -> dict[str, Any]:
    if period_end < period_start:
        raise SponsorInvoiceInvalidState("Statement period end cannot be before period start")

    tenant = _normalise_code(tenant_code)
    sponsor = _normalise_code(sponsor_code)
    resolved_currency = _normalise_code(currency) if currency else None

    invoices = await list_statement_invoice_records(
        tenant_code=tenant,
        sponsor_code=sponsor,
        period_start=period_start,
        period_end=period_end,
        currency=resolved_currency,
        limit=limit,
    )
    payments = await list_statement_payment_records(
        tenant_code=tenant,
        sponsor_code=sponsor,
        period_start=period_start,
        period_end=period_end,
        currency=resolved_currency,
        limit=limit,
    )

    currencies = sorted(
        {
            item["currency"]
            for item in [*invoices, *payments]
            if item.get("currency")
        }
    )

    return {
        "tenant_code": tenant,
        "sponsor_code": sponsor,
        "period_start": period_start,
        "period_end": period_end,
        "currency": resolved_currency,
        "currencies": currencies,
        "invoice_count": len(invoices),
        "payment_count": len(payments),
        "totals": {
            "subtotal_amount": _sum_money(invoices, "subtotal_amount"),
            "vat_amount": _sum_money(invoices, "vat_amount"),
            "total_amount": _sum_money(invoices, "total_amount"),
            "paid_amount": _sum_money(invoices, "paid_amount"),
            "outstanding_amount": _sum_money(invoices, "outstanding_amount"),
            "payments_received_amount": _sum_money(payments, "amount"),
        },
        "invoices": invoices,
        "payments": payments,
    }


async def get_sponsor_billing_dashboard(
    *,
    tenant_code: str,
    sponsor_code: str | None = None,
    period_start: date | None = None,
    period_end: date | None = None,
    currency: str | None = None,
    as_of_date: date | None = None,
    limit: int = 1000,
) -> dict[str, Any]:
    if period_start and period_end and period_end < period_start:
        raise SponsorInvoiceInvalidState("Dashboard period end cannot be before period start")

    tenant = _normalise_code(tenant_code)
    sponsor = _normalise_code(sponsor_code) if sponsor_code else None
    resolved_currency = _normalise_code(currency) if currency else None
    resolved_as_of = as_of_date or date.today()

    invoices = await list_billing_dashboard_invoice_records(
        tenant_code=tenant,
        sponsor_code=sponsor,
        period_start=period_start,
        period_end=period_end,
        currency=resolved_currency,
        limit=limit,
    )

    status_counts: dict[str, int] = {}
    sponsor_counts: dict[str, int] = {}
    overdue_invoices = []

    for invoice in invoices:
        status = str(invoice.get("status") or "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1

        invoice_sponsor = str(invoice.get("sponsor_code") or "UNKNOWN")
        sponsor_counts[invoice_sponsor] = sponsor_counts.get(invoice_sponsor, 0) + 1

        due_date = invoice.get("due_date")
        if (
            due_date is not None
            and due_date < resolved_as_of
            and status in {"ISSUED", "PARTIALLY_PAID"}
            and _to_decimal(invoice.get("outstanding_amount") or 0) > 0
        ):
            overdue_invoices.append(invoice)

    return {
        "tenant_code": tenant,
        "sponsor_code": sponsor,
        "period_start": period_start,
        "period_end": period_end,
        "currency": resolved_currency,
        "as_of_date": resolved_as_of,
        "invoice_count": len(invoices),
        "overdue_count": len(overdue_invoices),
        "status_counts": status_counts,
        "sponsor_counts": sponsor_counts,
        "totals": {
            "subtotal_amount": _sum_money(invoices, "subtotal_amount"),
            "vat_amount": _sum_money(invoices, "vat_amount"),
            "total_amount": _sum_money(invoices, "total_amount"),
            "paid_amount": _sum_money(invoices, "paid_amount"),
            "outstanding_amount": _sum_money(invoices, "outstanding_amount"),
            "overdue_outstanding_amount": _sum_money(
                overdue_invoices,
                "outstanding_amount",
            ),
        },
        "recent_invoices": invoices[:25],
        "overdue_invoices": overdue_invoices[:25],
    }


def _add_money_to_bucket(
    bucket: dict[str, Any],
    invoice: dict[str, Any],
) -> None:
    bucket["invoice_count"] += 1
    bucket["subtotal_amount"] += _to_decimal(invoice.get("subtotal_amount") or 0)
    bucket["vat_amount"] += _to_decimal(invoice.get("vat_amount") or 0)
    bucket["total_amount"] += _to_decimal(invoice.get("total_amount") or 0)


async def get_sponsor_vat_report(
    *,
    tenant_code: str,
    period_start: date,
    period_end: date,
    sponsor_code: str | None = None,
    currency: str | None = None,
    status: str | None = None,
    limit: int = 2000,
) -> dict[str, Any]:
    if period_end < period_start:
        raise SponsorInvoiceInvalidState("VAT report period end cannot be before period start")

    tenant = _normalise_code(tenant_code)
    sponsor = _normalise_code(sponsor_code) if sponsor_code else None
    resolved_currency = _normalise_code(currency) if currency else None
    resolved_status = _normalise_code(status) if status else None

    invoices = await list_vat_report_invoice_records(
        tenant_code=tenant,
        period_start=period_start,
        period_end=period_end,
        sponsor_code=sponsor,
        currency=resolved_currency,
        status=resolved_status,
        limit=limit,
    )

    by_status: dict[str, dict[str, Any]] = {}
    by_currency: dict[str, dict[str, Any]] = {}

    for invoice in invoices:
        invoice_status = str(invoice.get("status") or "UNKNOWN")
        invoice_currency = str(invoice.get("currency") or "UNKNOWN")

        by_status.setdefault(
            invoice_status,
            {
                "status": invoice_status,
                "invoice_count": 0,
                "subtotal_amount": Decimal("0.00"),
                "vat_amount": Decimal("0.00"),
                "total_amount": Decimal("0.00"),
            },
        )
        by_currency.setdefault(
            invoice_currency,
            {
                "currency": invoice_currency,
                "invoice_count": 0,
                "subtotal_amount": Decimal("0.00"),
                "vat_amount": Decimal("0.00"),
                "total_amount": Decimal("0.00"),
            },
        )

        _add_money_to_bucket(by_status[invoice_status], invoice)
        _add_money_to_bucket(by_currency[invoice_currency], invoice)

    return {
        "tenant_code": tenant,
        "sponsor_code": sponsor,
        "period_start": period_start,
        "period_end": period_end,
        "currency": resolved_currency,
        "status": resolved_status,
        "invoice_count": len(invoices),
        "totals": {
            "subtotal_amount": _sum_money(invoices, "subtotal_amount"),
            "vat_amount": _sum_money(invoices, "vat_amount"),
            "total_amount": _sum_money(invoices, "total_amount"),
        },
        "by_status": sorted(by_status.values(), key=lambda item: item["status"]),
        "by_currency": sorted(by_currency.values(), key=lambda item: item["currency"]),
        "invoices": invoices,
    }


async def issue_sponsor_invoice(*, invoice_id: str) -> dict[str, Any]:
    existing = await get_invoice_record(invoice_id=invoice_id)

    if not existing:
        raise SponsorInvoiceNotFound("Sponsor invoice not found")

    if existing["status"] != "DRAFT":
        raise SponsorInvoiceInvalidState("Only draft invoices can be issued")

    issued = await issue_invoice_record(invoice_id=invoice_id)

    if not issued:
        raise SponsorInvoiceInvalidState("Invoice could not be issued")

    return issued


async def allocate_sponsor_payment(
    *,
    tenant_code: str,
    sponsor_code: str,
    amount: Decimal | int | float | str,
    allocations: list[dict[str, Any]],
    currency: str = "ZAR",
    payment_reference: str | None = None,
    received_at: datetime | None = None,
    allocated_by: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payment_amount = _to_decimal(amount)

    if payment_amount <= 0:
        raise SponsorInvoiceAmountError("Payment receipt amount must be positive")

    if not allocations:
        raise SponsorInvoiceAmountError("Payment allocation must contain at least one invoice")

    tenant = _normalise_code(tenant_code)
    sponsor = _normalise_code(sponsor_code)
    resolved_currency = _normalise_code(currency)

    prepared_allocations = []
    total_allocation = Decimal("0.00")

    for allocation in allocations:
        allocation_amount = _to_decimal(allocation["amount"])

        if allocation_amount <= 0:
            raise SponsorInvoiceAmountError("Allocation amount must be positive")

        invoice = await get_invoice_record(invoice_id=allocation["invoice_id"])

        if not invoice:
            raise SponsorInvoiceNotFound("Sponsor invoice not found")

        if invoice["tenant_code"] != tenant or invoice["sponsor_code"] != sponsor:
            raise SponsorInvoiceInvalidState("Invoice does not belong to sponsor payment")

        if invoice["currency"] != resolved_currency:
            raise SponsorInvoiceInvalidState("Invoice currency does not match payment currency")

        if invoice["status"] not in {"ISSUED", "PARTIALLY_PAID"}:
            raise SponsorInvoiceInvalidState("Only issued invoices can receive allocations")

        if allocation_amount > _to_decimal(invoice["outstanding_amount"]):
            raise SponsorInvoiceAmountError("Allocation exceeds outstanding invoice amount")

        total_allocation += allocation_amount
        prepared_allocations.append(
            {
                "invoice": invoice,
                "amount": allocation_amount,
                "metadata": allocation.get("metadata"),
            }
        )

    if total_allocation > payment_amount:
        raise SponsorInvoiceAmountError("Total allocations exceed payment receipt amount")

    receipt = await create_payment_receipt_record(
        tenant_code=tenant,
        sponsor_code=sponsor,
        currency=resolved_currency,
        amount=payment_amount,
        payment_reference=payment_reference,
        received_at=received_at,
        metadata=metadata,
    )

    applied_allocations = []
    updated_invoices = []

    for allocation in prepared_allocations:
        invoice = allocation["invoice"]
        allocation_amount = allocation["amount"]

        payment = await create_invoice_payment_record(
            invoice_id=invoice["invoice_id"],
            amount=allocation_amount,
            payment_reference=payment_reference,
            paid_at=received_at,
            metadata={
                **(allocation.get("metadata") or {}),
                "receipt_id": str(receipt["receipt_id"]),
                "source": "sponsor_payment_allocation",
            },
        )

        updated_invoice = await apply_invoice_payment_amount(
            invoice_id=invoice["invoice_id"],
            amount=allocation_amount,
        )

        if not updated_invoice:
            raise SponsorInvoiceInvalidState("Invoice payment allocation could not be applied")

        payment_allocation = await create_payment_allocation_record(
            receipt_id=receipt["receipt_id"],
            invoice_id=invoice["invoice_id"],
            payment_id=payment["payment_id"],
            amount=allocation_amount,
            allocated_by=allocated_by,
            allocated_at=received_at,
            metadata=allocation.get("metadata"),
        )

        receipt = await apply_payment_receipt_allocation_amount(
            receipt_id=receipt["receipt_id"],
            amount=allocation_amount,
        )

        if not receipt:
            raise SponsorInvoiceInvalidState("Payment receipt allocation could not be applied")

        applied_allocations.append(
            {
                **payment_allocation,
                "payment": payment,
            }
        )
        updated_invoices.append(updated_invoice)

    return {
        "receipt": receipt,
        "allocations": applied_allocations,
        "invoices": updated_invoices,
        "unapplied_amount": _to_decimal(receipt["unapplied_amount"]),
    }


async def get_sponsor_payment_receipt(*, receipt_id: str) -> dict[str, Any]:
    receipt = await get_payment_receipt_record(receipt_id=receipt_id)

    if not receipt:
        raise SponsorInvoiceNotFound("Sponsor payment receipt not found")

    allocations = await list_payment_allocation_records(receipt_id=receipt_id)

    return {
        **receipt,
        "allocations": allocations,
    }


async def list_sponsor_payment_receipts(
    *,
    tenant_code: str,
    sponsor_code: str,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    return await list_payment_receipt_records(
        tenant_code=_normalise_code(tenant_code),
        sponsor_code=_normalise_code(sponsor_code),
        status=_normalise_code(status) if status else None,
        limit=limit,
    )


async def record_sponsor_invoice_payment(
    *,
    invoice_id: str,
    amount: Decimal | int | float | str,
    payment_reference: str | None = None,
    paid_at: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payment_amount = _to_decimal(amount)

    if payment_amount <= 0:
        raise SponsorInvoiceAmountError("Payment amount must be positive")

    invoice = await get_invoice_record(invoice_id=invoice_id)

    if not invoice:
        raise SponsorInvoiceNotFound("Sponsor invoice not found")

    if invoice["status"] not in {"ISSUED", "PARTIALLY_PAID"}:
        raise SponsorInvoiceInvalidState("Only issued invoices can receive payments")

    if _to_decimal(invoice["outstanding_amount"]) < payment_amount:
        raise SponsorInvoiceAmountError("Payment exceeds outstanding invoice amount")

    payment = await create_invoice_payment_record(
        invoice_id=invoice_id,
        amount=payment_amount,
        payment_reference=payment_reference,
        paid_at=paid_at,
        metadata=metadata,
    )

    updated_invoice = await apply_invoice_payment_amount(
        invoice_id=invoice_id,
        amount=payment_amount,
    )

    if not updated_invoice:
        raise SponsorInvoiceInvalidState("Invoice payment could not be applied")

    return {
        "invoice": updated_invoice,
        "payment": payment,
    }


async def reverse_sponsor_invoice_payment(
    *,
    payment_id: str,
    amount: Decimal | int | float | str,
    reason: str,
    reversed_by: str | None = None,
    reversed_at: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    reversal_amount = _to_decimal(amount)

    if reversal_amount <= 0:
        raise SponsorInvoiceAmountError("Reversal amount must be positive")

    if not reason.strip():
        raise SponsorInvoiceInvalidState("Payment reversal reason is required")

    payment = await get_invoice_payment_record(payment_id=payment_id)

    if not payment:
        raise SponsorInvoiceNotFound("Sponsor invoice payment not found")

    invoice = await get_invoice_record(invoice_id=payment["invoice_id"])

    if not invoice:
        raise SponsorInvoiceNotFound("Sponsor invoice not found")

    reversed_amount = _to_decimal(
        await get_reversed_payment_amount(payment_id=payment_id)
    )
    reversible_amount = _to_decimal(payment["amount"]) - reversed_amount

    if reversal_amount > reversible_amount:
        raise SponsorInvoiceAmountError("Reversal exceeds unreversed payment amount")

    reversal = await create_invoice_payment_reversal_record(
        payment_id=payment_id,
        invoice_id=payment["invoice_id"],
        amount=reversal_amount,
        reason=reason.strip(),
        reversed_by=reversed_by,
        reversed_at=reversed_at,
        metadata=metadata,
    )

    updated_invoice = await apply_invoice_payment_reversal_amount(
        invoice_id=payment["invoice_id"],
        amount=reversal_amount,
    )

    if not updated_invoice:
        raise SponsorInvoiceInvalidState("Invoice payment reversal could not be applied")

    return {
        "invoice": updated_invoice,
        "payment": payment,
        "reversal": reversal,
    }


async def reverse_sponsor_payment_allocation(
    *,
    allocation_id: str,
    amount: Decimal | int | float | str,
    reason: str,
    reversed_by: str | None = None,
    reversed_at: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    reversal_amount = _to_decimal(amount)

    if reversal_amount <= 0:
        raise SponsorInvoiceAmountError("Allocation reversal amount must be positive")

    if not reason.strip():
        raise SponsorInvoiceInvalidState("Payment allocation reversal reason is required")

    allocation = await get_payment_allocation_record(allocation_id=allocation_id)

    if not allocation:
        raise SponsorInvoiceNotFound("Sponsor payment allocation not found")

    reversed_amount = _to_decimal(
        await get_reversed_payment_allocation_amount(allocation_id=allocation_id)
    )
    reversible_amount = _to_decimal(allocation["amount"]) - reversed_amount

    if reversal_amount > reversible_amount:
        raise SponsorInvoiceAmountError("Reversal exceeds unreversed allocation amount")

    payment_reversal_result = await reverse_sponsor_invoice_payment(
        payment_id=allocation["payment_id"],
        amount=reversal_amount,
        reason=reason,
        reversed_by=reversed_by,
        reversed_at=reversed_at,
        metadata={
            **(metadata or {}),
            "allocation_id": allocation_id,
            "source": "sponsor_payment_allocation_reversal",
        },
    )

    allocation_reversal = await create_payment_allocation_reversal_record(
        allocation_id=allocation_id,
        receipt_id=allocation["receipt_id"],
        invoice_id=allocation["invoice_id"],
        payment_id=allocation["payment_id"],
        amount=reversal_amount,
        reason=reason.strip(),
        reversed_by=reversed_by,
        reversed_at=reversed_at,
        metadata=metadata,
    )

    receipt = await reverse_payment_receipt_allocation_amount(
        receipt_id=allocation["receipt_id"],
        amount=reversal_amount,
    )

    if not receipt:
        raise SponsorInvoiceInvalidState("Payment receipt allocation reversal could not be applied")

    return {
        "receipt": receipt,
        "allocation": allocation,
        "allocation_reversal": allocation_reversal,
        **payment_reversal_result,
    }
