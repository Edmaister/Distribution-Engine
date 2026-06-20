from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from services.marketplace_funding import sponsor_billing_service as service
from services.marketplace_funding.sponsor_billing_service import (
    SponsorInvoiceAmountError,
    SponsorInvoiceInvalidState,
    allocate_sponsor_payment,
    create_sponsor_invoice,
    generate_sponsor_invoice_from_utilisation,
    get_sponsor_payment_receipt,
    get_sponsor_billing_dashboard,
    get_sponsor_statement,
    get_sponsor_vat_report,
    issue_sponsor_invoice,
    list_sponsor_invoices,
    list_sponsor_payment_receipts,
    record_sponsor_invoice_payment,
    reverse_sponsor_payment_allocation,
    reverse_sponsor_invoice_payment,
    run_sponsor_billing_generation,
)


pytestmark = pytest.mark.asyncio


async def test_create_sponsor_invoice_calculates_totals(monkeypatch):
    created_lines = []

    async def fake_create_invoice_record(**kwargs):
        return {
            "invoice_id": "invoice-1",
            "invoice_number": kwargs["invoice_number"],
            "tenant_code": kwargs["tenant_code"],
            "sponsor_code": kwargs["sponsor_code"],
            "currency": kwargs["currency"],
            "subtotal_amount": kwargs["subtotal_amount"],
            "vat_amount": kwargs["vat_amount"],
            "total_amount": kwargs["total_amount"],
            "outstanding_amount": kwargs["total_amount"],
            "status": "DRAFT",
        }

    async def fake_create_invoice_line_record(**kwargs):
        created_lines.append(kwargs)
        return {"line_id": f"line-{len(created_lines)}", **kwargs}

    monkeypatch.setattr(service, "create_invoice_record", fake_create_invoice_record)
    monkeypatch.setattr(service, "create_invoice_line_record", fake_create_invoice_line_record)

    invoice = await create_sponsor_invoice(
        tenant_code="fnb",
        sponsor_code="boxer",
        sponsor_name="Boxer",
        contract_id="contract-1",
        invoice_period_start=date(2026, 6, 1),
        invoice_period_end=date(2026, 6, 30),
        due_date=date(2026, 7, 15),
        vat_rate="0.15",
        lines=[
            {
                "description": "June utilised rewards",
                "quantity": "2",
                "unit_amount": "100.00",
            },
            {
                "line_type": "platform_fee",
                "description": "Platform fee",
                "quantity": "1",
                "unit_amount": "50.00",
            },
        ],
    )

    assert invoice["tenant_code"] == "FNB"
    assert invoice["sponsor_code"] == "BOXER"
    assert invoice["currency"] == "ZAR"
    assert invoice["subtotal_amount"] == Decimal("250.00")
    assert invoice["vat_amount"] == Decimal("37.50")
    assert invoice["total_amount"] == Decimal("287.50")
    assert invoice["outstanding_amount"] == Decimal("287.50")
    assert invoice["lines"][1]["line_type"] == "PLATFORM_FEE"


async def test_create_sponsor_invoice_rejects_empty_lines():
    with pytest.raises(SponsorInvoiceAmountError, match="at least one line"):
        await create_sponsor_invoice(
            tenant_code="FNB",
            sponsor_code="BOXER",
            sponsor_name="Boxer",
            lines=[],
        )


async def test_generate_sponsor_invoice_from_utilisation(monkeypatch):
    calls = {}

    async def fake_list_unbilled_contract_utilisation(**kwargs):
        calls["list"] = kwargs
        return [
            {
                "ledger_id": "ledger-1",
                "contract_id": kwargs["contract_id"],
                "amount": Decimal("125.00"),
                "reward_id": "reward-1",
                "allocation_id": "allocation-1",
                "correlation_id": "corr-1",
                "metadata": {"source": "test"},
                "created_at": datetime(2026, 6, 5, 10, 0, tzinfo=timezone.utc),
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "sponsor_name": "Boxer",
            },
            {
                "ledger_id": "ledger-2",
                "contract_id": kwargs["contract_id"],
                "amount": Decimal("75.00"),
                "reward_id": None,
                "allocation_id": None,
                "correlation_id": "corr-2",
                "metadata": {},
                "created_at": datetime(2026, 6, 6, 10, 0, tzinfo=timezone.utc),
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "sponsor_name": "Boxer",
            },
        ]

    async def fake_create_sponsor_invoice(**kwargs):
        calls["create"] = kwargs
        return {
            "invoice_id": "invoice-1",
            "status": "DRAFT",
            "total_amount": Decimal("230.00"),
            "lines": kwargs["lines"],
        }

    monkeypatch.setattr(
        service,
        "list_unbilled_contract_utilisation",
        fake_list_unbilled_contract_utilisation,
    )
    monkeypatch.setattr(service, "create_sponsor_invoice", fake_create_sponsor_invoice)

    invoice = await generate_sponsor_invoice_from_utilisation(
        contract_id="contract-1",
        invoice_period_start=date(2026, 6, 1),
        invoice_period_end=date(2026, 6, 30),
        due_date=date(2026, 7, 15),
        vat_rate="0.15",
    )

    assert invoice["invoice_id"] == "invoice-1"
    assert calls["list"]["period_start"] == date(2026, 6, 1)
    assert calls["create"]["tenant_code"] == "FNB"
    assert calls["create"]["sponsor_code"] == "BOXER"
    assert calls["create"]["vat_rate"] == "0.15"
    assert calls["create"]["metadata"]["generated_from"] == "BUDGET_UTILISED"
    assert calls["create"]["metadata"]["source_ledger_count"] == 2
    assert calls["create"]["lines"][0]["source_ledger_id"] == "ledger-1"
    assert calls["create"]["lines"][0]["unit_amount"] == Decimal("125.00")


async def test_generate_sponsor_invoice_from_utilisation_can_issue(monkeypatch):
    async def fake_list_unbilled_contract_utilisation(**kwargs):
        return [
            {
                "ledger_id": "ledger-1",
                "contract_id": kwargs["contract_id"],
                "amount": Decimal("125.00"),
                "reward_id": None,
                "allocation_id": None,
                "correlation_id": None,
                "metadata": {},
                "created_at": datetime(2026, 6, 5, 10, 0, tzinfo=timezone.utc),
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "sponsor_name": "Boxer",
            },
        ]

    async def fake_create_sponsor_invoice(**kwargs):
        return {
            "invoice_id": "invoice-1",
            "status": "DRAFT",
            "lines": kwargs["lines"],
        }

    async def fake_issue_sponsor_invoice(**kwargs):
        return {
            "invoice_id": kwargs["invoice_id"],
            "status": "ISSUED",
        }

    monkeypatch.setattr(
        service,
        "list_unbilled_contract_utilisation",
        fake_list_unbilled_contract_utilisation,
    )
    monkeypatch.setattr(service, "create_sponsor_invoice", fake_create_sponsor_invoice)
    monkeypatch.setattr(service, "issue_sponsor_invoice", fake_issue_sponsor_invoice)

    invoice = await generate_sponsor_invoice_from_utilisation(
        contract_id="contract-1",
        invoice_period_start=date(2026, 6, 1),
        invoice_period_end=date(2026, 6, 30),
        issue=True,
    )

    assert invoice["status"] == "ISSUED"
    assert invoice["lines"][0]["source_ledger_id"] == "ledger-1"


async def test_generate_sponsor_invoice_from_utilisation_rejects_empty_period(monkeypatch):
    async def fake_list_unbilled_contract_utilisation(**kwargs):
        return []

    monkeypatch.setattr(
        service,
        "list_unbilled_contract_utilisation",
        fake_list_unbilled_contract_utilisation,
    )

    with pytest.raises(SponsorInvoiceAmountError, match="No unbilled"):
        await generate_sponsor_invoice_from_utilisation(
            contract_id="contract-1",
            invoice_period_start=date(2026, 6, 1),
            invoice_period_end=date(2026, 6, 30),
        )


async def test_run_sponsor_billing_generation_dry_run(monkeypatch):
    calls = {}

    async def fake_list_funding_contracts(**kwargs):
        calls["contracts"] = kwargs
        return [
            {
                "contract_id": "contract-1",
                "sponsor_code": "BOXER",
                "sponsor_name": "Boxer",
            },
            {
                "contract_id": "contract-2",
                "sponsor_code": "SHOP",
                "sponsor_name": "Shop",
            },
        ]

    async def fake_list_unbilled_contract_utilisation(**kwargs):
        if kwargs["contract_id"] == "contract-1":
            return [
                {"amount": Decimal("125.00")},
                {"amount": Decimal("75.00")},
            ]
        return []

    monkeypatch.setattr(service, "list_funding_contracts", fake_list_funding_contracts)
    monkeypatch.setattr(
        service,
        "list_unbilled_contract_utilisation",
        fake_list_unbilled_contract_utilisation,
    )

    result = await run_sponsor_billing_generation(
        tenant_code=" fnb ",
        sponsor_code=" boxer ",
        invoice_period_start=date(2026, 6, 1),
        invoice_period_end=date(2026, 6, 30),
        dry_run=True,
    )

    assert result["tenant_code"] == "FNB"
    assert result["sponsor_code"] == "BOXER"
    assert result["dry_run"] is True
    assert result["contract_count"] == 2
    assert result["ready_count"] == 1
    assert result["generated_count"] == 0
    assert result["skipped_count"] == 1
    assert result["total_unbilled_amount"] == Decimal("200.00")
    assert result["items"][0]["status"] == "READY"
    assert result["items"][0]["unbilled_count"] == 2
    assert calls["contracts"]["status"] == "ACTIVE"


async def test_run_sponsor_billing_generation_creates_invoices(monkeypatch):
    calls = {}

    async def fake_list_funding_contracts(**kwargs):
        return [
            {
                "contract_id": "contract-1",
                "sponsor_code": "BOXER",
                "sponsor_name": "Boxer",
            }
        ]

    async def fake_list_unbilled_contract_utilisation(**kwargs):
        return [{"amount": Decimal("125.00")}]

    async def fake_generate_sponsor_invoice_from_utilisation(**kwargs):
        calls["generate"] = kwargs
        return {
            "invoice_id": "invoice-1",
            "status": "ISSUED" if kwargs["issue"] else "DRAFT",
        }

    monkeypatch.setattr(service, "list_funding_contracts", fake_list_funding_contracts)
    monkeypatch.setattr(
        service,
        "list_unbilled_contract_utilisation",
        fake_list_unbilled_contract_utilisation,
    )
    monkeypatch.setattr(
        service,
        "generate_sponsor_invoice_from_utilisation",
        fake_generate_sponsor_invoice_from_utilisation,
    )

    result = await run_sponsor_billing_generation(
        tenant_code="FNB",
        invoice_period_start=date(2026, 6, 1),
        invoice_period_end=date(2026, 6, 30),
        due_date=date(2026, 7, 15),
        vat_rate="0.15",
        issue=True,
        dry_run=False,
    )

    assert result["dry_run"] is False
    assert result["generated_count"] == 1
    assert result["items"][0]["status"] == "GENERATED"
    assert result["items"][0]["invoice"]["status"] == "ISSUED"
    assert calls["generate"]["contract_id"] == "contract-1"
    assert calls["generate"]["vat_rate"] == "0.15"
    assert calls["generate"]["issue"] is True
    assert calls["generate"]["metadata"]["generation_source"] == "scheduled_sponsor_billing"


async def test_run_sponsor_billing_generation_rejects_invalid_period():
    with pytest.raises(SponsorInvoiceInvalidState, match="period end"):
        await run_sponsor_billing_generation(
            tenant_code="FNB",
            invoice_period_start=date(2026, 7, 1),
            invoice_period_end=date(2026, 6, 30),
        )


async def test_list_sponsor_invoices_normalises_filters(monkeypatch):
    calls = {}

    async def fake_list_invoice_records(**kwargs):
        calls.update(kwargs)
        return [{"invoice_id": "invoice-1"}]

    monkeypatch.setattr(service, "list_invoice_records", fake_list_invoice_records)

    invoices = await list_sponsor_invoices(
        tenant_code=" fnb ",
        sponsor_code=" boxer ",
        status=" issued ",
    )

    assert invoices == [{"invoice_id": "invoice-1"}]
    assert calls["tenant_code"] == "FNB"
    assert calls["sponsor_code"] == "BOXER"
    assert calls["status"] == "ISSUED"


async def test_get_sponsor_statement_totals_period_activity(monkeypatch):
    calls = {}

    async def fake_list_statement_invoice_records(**kwargs):
        calls["invoices"] = kwargs
        return [
            {
                "invoice_id": "invoice-1",
                "invoice_number": "INV-1",
                "currency": "ZAR",
                "subtotal_amount": Decimal("100.00"),
                "vat_amount": Decimal("15.00"),
                "total_amount": Decimal("115.00"),
                "paid_amount": Decimal("50.00"),
                "outstanding_amount": Decimal("65.00"),
            },
            {
                "invoice_id": "invoice-2",
                "invoice_number": "INV-2",
                "currency": "ZAR",
                "subtotal_amount": Decimal("200.00"),
                "vat_amount": Decimal("30.00"),
                "total_amount": Decimal("230.00"),
                "paid_amount": Decimal("0.00"),
                "outstanding_amount": Decimal("230.00"),
            },
        ]

    async def fake_list_statement_payment_records(**kwargs):
        calls["payments"] = kwargs
        return [
            {
                "payment_id": "payment-1",
                "invoice_id": "invoice-1",
                "invoice_number": "INV-1",
                "currency": "ZAR",
                "amount": Decimal("50.00"),
            }
        ]

    monkeypatch.setattr(
        service,
        "list_statement_invoice_records",
        fake_list_statement_invoice_records,
    )
    monkeypatch.setattr(
        service,
        "list_statement_payment_records",
        fake_list_statement_payment_records,
    )

    statement = await get_sponsor_statement(
        tenant_code=" fnb ",
        sponsor_code=" boxer ",
        period_start=date(2026, 6, 1),
        period_end=date(2026, 6, 30),
        currency=" zar ",
    )

    assert statement["tenant_code"] == "FNB"
    assert statement["sponsor_code"] == "BOXER"
    assert statement["currency"] == "ZAR"
    assert statement["invoice_count"] == 2
    assert statement["payment_count"] == 1
    assert statement["totals"]["subtotal_amount"] == Decimal("300.00")
    assert statement["totals"]["vat_amount"] == Decimal("45.00")
    assert statement["totals"]["total_amount"] == Decimal("345.00")
    assert statement["totals"]["paid_amount"] == Decimal("50.00")
    assert statement["totals"]["outstanding_amount"] == Decimal("295.00")
    assert statement["totals"]["payments_received_amount"] == Decimal("50.00")
    assert calls["invoices"]["tenant_code"] == "FNB"
    assert calls["payments"]["sponsor_code"] == "BOXER"


async def test_get_sponsor_statement_rejects_invalid_period():
    with pytest.raises(SponsorInvoiceInvalidState, match="period end"):
        await get_sponsor_statement(
            tenant_code="FNB",
            sponsor_code="BOXER",
            period_start=date(2026, 7, 1),
            period_end=date(2026, 6, 30),
        )


async def test_get_sponsor_billing_dashboard_totals_and_overdue(monkeypatch):
    calls = {}

    async def fake_list_billing_dashboard_invoice_records(**kwargs):
        calls.update(kwargs)
        return [
            {
                "invoice_id": "invoice-1",
                "sponsor_code": "BOXER",
                "status": "ISSUED",
                "due_date": date(2026, 6, 15),
                "subtotal_amount": Decimal("100.00"),
                "vat_amount": Decimal("15.00"),
                "total_amount": Decimal("115.00"),
                "paid_amount": Decimal("0.00"),
                "outstanding_amount": Decimal("115.00"),
            },
            {
                "invoice_id": "invoice-2",
                "sponsor_code": "BOXER",
                "status": "PAID",
                "due_date": date(2026, 6, 20),
                "subtotal_amount": Decimal("200.00"),
                "vat_amount": Decimal("30.00"),
                "total_amount": Decimal("230.00"),
                "paid_amount": Decimal("230.00"),
                "outstanding_amount": Decimal("0.00"),
            },
            {
                "invoice_id": "invoice-3",
                "sponsor_code": "MTN",
                "status": "PARTIALLY_PAID",
                "due_date": date(2026, 7, 10),
                "subtotal_amount": Decimal("300.00"),
                "vat_amount": Decimal("45.00"),
                "total_amount": Decimal("345.00"),
                "paid_amount": Decimal("100.00"),
                "outstanding_amount": Decimal("245.00"),
            },
        ]

    monkeypatch.setattr(
        service,
        "list_billing_dashboard_invoice_records",
        fake_list_billing_dashboard_invoice_records,
    )

    dashboard = await get_sponsor_billing_dashboard(
        tenant_code=" fnb ",
        period_start=date(2026, 6, 1),
        period_end=date(2026, 7, 31),
        currency=" zar ",
        as_of_date=date(2026, 7, 1),
    )

    assert dashboard["tenant_code"] == "FNB"
    assert dashboard["currency"] == "ZAR"
    assert dashboard["invoice_count"] == 3
    assert dashboard["overdue_count"] == 1
    assert dashboard["status_counts"] == {
        "ISSUED": 1,
        "PAID": 1,
        "PARTIALLY_PAID": 1,
    }
    assert dashboard["sponsor_counts"] == {"BOXER": 2, "MTN": 1}
    assert dashboard["totals"]["total_amount"] == Decimal("690.00")
    assert dashboard["totals"]["paid_amount"] == Decimal("330.00")
    assert dashboard["totals"]["outstanding_amount"] == Decimal("360.00")
    assert dashboard["totals"]["overdue_outstanding_amount"] == Decimal("115.00")
    assert dashboard["overdue_invoices"][0]["invoice_id"] == "invoice-1"
    assert calls["tenant_code"] == "FNB"
    assert calls["currency"] == "ZAR"


async def test_get_sponsor_billing_dashboard_rejects_invalid_period():
    with pytest.raises(SponsorInvoiceInvalidState, match="period end"):
        await get_sponsor_billing_dashboard(
            tenant_code="FNB",
            period_start=date(2026, 8, 1),
            period_end=date(2026, 7, 31),
        )


async def test_get_sponsor_vat_report_groups_totals(monkeypatch):
    calls = {}

    async def fake_list_vat_report_invoice_records(**kwargs):
        calls.update(kwargs)
        return [
            {
                "invoice_id": "invoice-1",
                "invoice_number": "INV-1",
                "status": "ISSUED",
                "currency": "ZAR",
                "subtotal_amount": Decimal("100.00"),
                "vat_amount": Decimal("15.00"),
                "total_amount": Decimal("115.00"),
            },
            {
                "invoice_id": "invoice-2",
                "invoice_number": "INV-2",
                "status": "PAID",
                "currency": "ZAR",
                "subtotal_amount": Decimal("200.00"),
                "vat_amount": Decimal("30.00"),
                "total_amount": Decimal("230.00"),
            },
            {
                "invoice_id": "invoice-3",
                "invoice_number": "INV-3",
                "status": "ISSUED",
                "currency": "USD",
                "subtotal_amount": Decimal("300.00"),
                "vat_amount": Decimal("45.00"),
                "total_amount": Decimal("345.00"),
            },
        ]

    monkeypatch.setattr(
        service,
        "list_vat_report_invoice_records",
        fake_list_vat_report_invoice_records,
    )

    report = await get_sponsor_vat_report(
        tenant_code=" fnb ",
        sponsor_code=" boxer ",
        period_start=date(2026, 6, 1),
        period_end=date(2026, 6, 30),
        currency=" zar ",
        status=" issued ",
    )

    assert report["tenant_code"] == "FNB"
    assert report["sponsor_code"] == "BOXER"
    assert report["currency"] == "ZAR"
    assert report["status"] == "ISSUED"
    assert report["invoice_count"] == 3
    assert report["totals"]["subtotal_amount"] == Decimal("600.00")
    assert report["totals"]["vat_amount"] == Decimal("90.00")
    assert report["totals"]["total_amount"] == Decimal("690.00")
    assert report["by_status"][0]["status"] == "ISSUED"
    assert report["by_status"][0]["invoice_count"] == 2
    assert report["by_status"][0]["vat_amount"] == Decimal("60.00")
    assert report["by_currency"][1]["currency"] == "ZAR"
    assert report["by_currency"][1]["vat_amount"] == Decimal("45.00")
    assert calls["tenant_code"] == "FNB"
    assert calls["status"] == "ISSUED"


async def test_get_sponsor_vat_report_rejects_invalid_period():
    with pytest.raises(SponsorInvoiceInvalidState, match="period end"):
        await get_sponsor_vat_report(
            tenant_code="FNB",
            period_start=date(2026, 7, 1),
            period_end=date(2026, 6, 30),
        )


async def test_issue_sponsor_invoice(monkeypatch):
    async def fake_get_invoice_record(**kwargs):
        return {"invoice_id": kwargs["invoice_id"], "status": "DRAFT"}

    async def fake_issue_invoice_record(**kwargs):
        return {"invoice_id": kwargs["invoice_id"], "status": "ISSUED"}

    monkeypatch.setattr(service, "get_invoice_record", fake_get_invoice_record)
    monkeypatch.setattr(service, "issue_invoice_record", fake_issue_invoice_record)

    invoice = await issue_sponsor_invoice(invoice_id="invoice-1")

    assert invoice["status"] == "ISSUED"


async def test_issue_sponsor_invoice_rejects_non_draft(monkeypatch):
    async def fake_get_invoice_record(**kwargs):
        return {"invoice_id": kwargs["invoice_id"], "status": "ISSUED"}

    monkeypatch.setattr(service, "get_invoice_record", fake_get_invoice_record)

    with pytest.raises(SponsorInvoiceInvalidState, match="Only draft"):
        await issue_sponsor_invoice(invoice_id="invoice-1")


async def test_allocate_sponsor_payment_splits_receipt_across_invoices(monkeypatch):
    calls = {"payments": [], "invoice_apply": [], "receipt_apply": []}

    invoices = {
        "invoice-1": {
            "invoice_id": "invoice-1",
            "tenant_code": "FNB",
            "sponsor_code": "BOXER",
            "currency": "ZAR",
            "status": "ISSUED",
            "outstanding_amount": Decimal("100.00"),
        },
        "invoice-2": {
            "invoice_id": "invoice-2",
            "tenant_code": "FNB",
            "sponsor_code": "BOXER",
            "currency": "ZAR",
            "status": "ISSUED",
            "outstanding_amount": Decimal("50.00"),
        },
    }

    async def fake_get_invoice_record(**kwargs):
        return invoices[kwargs["invoice_id"]]

    async def fake_create_payment_receipt_record(**kwargs):
        return {
            "receipt_id": "receipt-1",
            "amount": kwargs["amount"],
            "applied_amount": Decimal("0.00"),
            "unapplied_amount": kwargs["amount"],
            "status": "UNAPPLIED",
        }

    async def fake_create_invoice_payment_record(**kwargs):
        calls["payments"].append(kwargs)
        return {
            "payment_id": f"payment-{len(calls['payments'])}",
            **kwargs,
        }

    async def fake_apply_invoice_payment_amount(**kwargs):
        calls["invoice_apply"].append(kwargs)
        return {
            "invoice_id": kwargs["invoice_id"],
            "status": "PAID",
            "outstanding_amount": Decimal("0.00"),
        }

    async def fake_create_payment_allocation_record(**kwargs):
        return {
            "allocation_id": f"allocation-{len(calls['payments'])}",
            **kwargs,
        }

    async def fake_apply_payment_receipt_allocation_amount(**kwargs):
        calls["receipt_apply"].append(kwargs)
        applied = sum(item["amount"] for item in calls["receipt_apply"])
        return {
            "receipt_id": kwargs["receipt_id"],
            "amount": Decimal("175.00"),
            "applied_amount": applied,
            "unapplied_amount": Decimal("175.00") - applied,
            "status": "PARTIALLY_APPLIED",
        }

    monkeypatch.setattr(service, "get_invoice_record", fake_get_invoice_record)
    monkeypatch.setattr(service, "create_payment_receipt_record", fake_create_payment_receipt_record)
    monkeypatch.setattr(service, "create_invoice_payment_record", fake_create_invoice_payment_record)
    monkeypatch.setattr(service, "apply_invoice_payment_amount", fake_apply_invoice_payment_amount)
    monkeypatch.setattr(
        service,
        "create_payment_allocation_record",
        fake_create_payment_allocation_record,
    )
    monkeypatch.setattr(
        service,
        "apply_payment_receipt_allocation_amount",
        fake_apply_payment_receipt_allocation_amount,
    )

    result = await allocate_sponsor_payment(
        tenant_code=" fnb ",
        sponsor_code=" boxer ",
        amount="175.00",
        payment_reference="PAY-1",
        allocated_by="finance-user",
        allocations=[
            {"invoice_id": "invoice-1", "amount": "100.00"},
            {"invoice_id": "invoice-2", "amount": "50.00"},
        ],
    )

    assert result["receipt"]["status"] == "PARTIALLY_APPLIED"
    assert result["unapplied_amount"] == Decimal("25.00")
    assert len(result["allocations"]) == 2
    assert calls["payments"][0]["metadata"]["receipt_id"] == "receipt-1"
    assert calls["invoice_apply"][1]["invoice_id"] == "invoice-2"


async def test_allocate_sponsor_payment_rejects_over_allocation(monkeypatch):
    async def fake_get_invoice_record(**kwargs):
        return {
            "invoice_id": kwargs["invoice_id"],
            "tenant_code": "FNB",
            "sponsor_code": "BOXER",
            "currency": "ZAR",
            "status": "ISSUED",
            "outstanding_amount": Decimal("150.00"),
        }

    monkeypatch.setattr(service, "get_invoice_record", fake_get_invoice_record)

    with pytest.raises(SponsorInvoiceAmountError, match="Total allocations exceed"):
        await allocate_sponsor_payment(
            tenant_code="FNB",
            sponsor_code="BOXER",
            amount="100.00",
            allocations=[{"invoice_id": "invoice-1", "amount": "125.00"}],
        )


async def test_allocate_sponsor_payment_rejects_wrong_sponsor(monkeypatch):
    async def fake_get_invoice_record(**kwargs):
        return {
            "invoice_id": kwargs["invoice_id"],
            "tenant_code": "FNB",
            "sponsor_code": "OTHER",
            "currency": "ZAR",
            "status": "ISSUED",
            "outstanding_amount": Decimal("50.00"),
        }

    monkeypatch.setattr(service, "get_invoice_record", fake_get_invoice_record)

    with pytest.raises(SponsorInvoiceInvalidState, match="does not belong"):
        await allocate_sponsor_payment(
            tenant_code="FNB",
            sponsor_code="BOXER",
            amount="50.00",
            allocations=[{"invoice_id": "invoice-1", "amount": "50.00"}],
        )


async def test_get_sponsor_payment_receipt_includes_allocations(monkeypatch):
    async def fake_get_payment_receipt_record(**kwargs):
        return {"receipt_id": kwargs["receipt_id"], "status": "PARTIALLY_APPLIED"}

    async def fake_list_payment_allocation_records(**kwargs):
        return [{"allocation_id": "allocation-1", "receipt_id": kwargs["receipt_id"]}]

    monkeypatch.setattr(service, "get_payment_receipt_record", fake_get_payment_receipt_record)
    monkeypatch.setattr(
        service,
        "list_payment_allocation_records",
        fake_list_payment_allocation_records,
    )

    receipt = await get_sponsor_payment_receipt(receipt_id="receipt-1")

    assert receipt["receipt_id"] == "receipt-1"
    assert receipt["allocations"][0]["allocation_id"] == "allocation-1"


async def test_list_sponsor_payment_receipts_normalises_filters(monkeypatch):
    calls = {}

    async def fake_list_payment_receipt_records(**kwargs):
        calls.update(kwargs)
        return [{"receipt_id": "receipt-1"}]

    monkeypatch.setattr(
        service,
        "list_payment_receipt_records",
        fake_list_payment_receipt_records,
    )

    receipts = await list_sponsor_payment_receipts(
        tenant_code=" fnb ",
        sponsor_code=" boxer ",
        status=" partially_applied ",
    )

    assert receipts == [{"receipt_id": "receipt-1"}]
    assert calls["tenant_code"] == "FNB"
    assert calls["sponsor_code"] == "BOXER"
    assert calls["status"] == "PARTIALLY_APPLIED"


async def test_record_sponsor_invoice_payment_marks_invoice_paid(monkeypatch):
    async def fake_get_invoice_record(**kwargs):
        return {
            "invoice_id": kwargs["invoice_id"],
            "status": "ISSUED",
            "outstanding_amount": Decimal("100.00"),
        }

    async def fake_create_invoice_payment_record(**kwargs):
        return {
            "payment_id": "payment-1",
            "invoice_id": kwargs["invoice_id"],
            "amount": kwargs["amount"],
        }

    async def fake_apply_invoice_payment_amount(**kwargs):
        return {
            "invoice_id": kwargs["invoice_id"],
            "status": "PAID",
            "paid_amount": kwargs["amount"],
            "outstanding_amount": Decimal("0.00"),
        }

    monkeypatch.setattr(service, "get_invoice_record", fake_get_invoice_record)
    monkeypatch.setattr(service, "create_invoice_payment_record", fake_create_invoice_payment_record)
    monkeypatch.setattr(service, "apply_invoice_payment_amount", fake_apply_invoice_payment_amount)

    result = await record_sponsor_invoice_payment(
        invoice_id="invoice-1",
        amount="100.00",
        payment_reference="PAY-1",
    )

    assert result["payment"]["amount"] == Decimal("100.00")
    assert result["invoice"]["status"] == "PAID"


async def test_record_sponsor_invoice_payment_rejects_overpayment(monkeypatch):
    async def fake_get_invoice_record(**kwargs):
        return {
            "invoice_id": kwargs["invoice_id"],
            "status": "ISSUED",
            "outstanding_amount": Decimal("50.00"),
        }

    monkeypatch.setattr(service, "get_invoice_record", fake_get_invoice_record)

    with pytest.raises(SponsorInvoiceAmountError, match="exceeds outstanding"):
        await record_sponsor_invoice_payment(
            invoice_id="invoice-1",
            amount="100.00",
        )


async def test_reverse_sponsor_invoice_payment(monkeypatch):
    calls = {}

    async def fake_get_invoice_payment_record(**kwargs):
        return {
            "payment_id": kwargs["payment_id"],
            "invoice_id": "invoice-1",
            "amount": Decimal("100.00"),
        }

    async def fake_get_invoice_record(**kwargs):
        return {
            "invoice_id": kwargs["invoice_id"],
            "status": "PAID",
        }

    async def fake_get_reversed_payment_amount(**kwargs):
        calls["reversed_payment_id"] = kwargs["payment_id"]
        return Decimal("25.00")

    async def fake_create_invoice_payment_reversal_record(**kwargs):
        calls["reversal"] = kwargs
        return {
            "reversal_id": "reversal-1",
            **kwargs,
        }

    async def fake_apply_invoice_payment_reversal_amount(**kwargs):
        calls["apply"] = kwargs
        return {
            "invoice_id": kwargs["invoice_id"],
            "status": "PARTIALLY_PAID",
            "paid_amount": Decimal("50.00"),
            "outstanding_amount": Decimal("50.00"),
        }

    monkeypatch.setattr(service, "get_invoice_payment_record", fake_get_invoice_payment_record)
    monkeypatch.setattr(service, "get_invoice_record", fake_get_invoice_record)
    monkeypatch.setattr(service, "get_reversed_payment_amount", fake_get_reversed_payment_amount)
    monkeypatch.setattr(
        service,
        "create_invoice_payment_reversal_record",
        fake_create_invoice_payment_reversal_record,
    )
    monkeypatch.setattr(
        service,
        "apply_invoice_payment_reversal_amount",
        fake_apply_invoice_payment_reversal_amount,
    )

    result = await reverse_sponsor_invoice_payment(
        payment_id="payment-1",
        amount="50.00",
        reason="Duplicate payment",
        reversed_by="finance-user",
    )

    assert result["invoice"]["status"] == "PARTIALLY_PAID"
    assert result["reversal"]["amount"] == Decimal("50.00")
    assert result["reversal"]["reason"] == "Duplicate payment"
    assert calls["reversed_payment_id"] == "payment-1"
    assert calls["apply"]["invoice_id"] == "invoice-1"


async def test_reverse_sponsor_invoice_payment_rejects_over_reversal(monkeypatch):
    async def fake_get_invoice_payment_record(**kwargs):
        return {
            "payment_id": kwargs["payment_id"],
            "invoice_id": "invoice-1",
            "amount": Decimal("100.00"),
        }

    async def fake_get_invoice_record(**kwargs):
        return {
            "invoice_id": kwargs["invoice_id"],
            "status": "PAID",
        }

    async def fake_get_reversed_payment_amount(**kwargs):
        return Decimal("80.00")

    monkeypatch.setattr(service, "get_invoice_payment_record", fake_get_invoice_payment_record)
    monkeypatch.setattr(service, "get_invoice_record", fake_get_invoice_record)
    monkeypatch.setattr(service, "get_reversed_payment_amount", fake_get_reversed_payment_amount)

    with pytest.raises(SponsorInvoiceAmountError, match="exceeds unreversed"):
        await reverse_sponsor_invoice_payment(
            payment_id="payment-1",
            amount="25.00",
            reason="Too much",
        )


async def test_reverse_sponsor_invoice_payment_requires_reason():
    with pytest.raises(SponsorInvoiceInvalidState, match="reason is required"):
        await reverse_sponsor_invoice_payment(
            payment_id="payment-1",
            amount="25.00",
            reason=" ",
        )


async def test_reverse_sponsor_payment_allocation_restores_unapplied_credit(monkeypatch):
    calls = {}

    async def fake_get_payment_allocation_record(**kwargs):
        return {
            "allocation_id": kwargs["allocation_id"],
            "receipt_id": "receipt-1",
            "invoice_id": "invoice-1",
            "payment_id": "payment-1",
            "amount": Decimal("100.00"),
        }

    async def fake_get_reversed_payment_allocation_amount(**kwargs):
        return Decimal("25.00")

    async def fake_reverse_sponsor_invoice_payment(**kwargs):
        calls["payment_reversal"] = kwargs
        return {
            "invoice": {"invoice_id": "invoice-1", "status": "PARTIALLY_PAID"},
            "payment": {"payment_id": kwargs["payment_id"]},
            "reversal": {"reversal_id": "payment-reversal-1"},
        }

    async def fake_create_payment_allocation_reversal_record(**kwargs):
        calls["allocation_reversal"] = kwargs
        return {"reversal_id": "allocation-reversal-1", **kwargs}

    async def fake_reverse_payment_receipt_allocation_amount(**kwargs):
        calls["receipt"] = kwargs
        return {
            "receipt_id": kwargs["receipt_id"],
            "applied_amount": Decimal("50.00"),
            "unapplied_amount": Decimal("50.00"),
            "status": "PARTIALLY_APPLIED",
        }

    monkeypatch.setattr(service, "get_payment_allocation_record", fake_get_payment_allocation_record)
    monkeypatch.setattr(
        service,
        "get_reversed_payment_allocation_amount",
        fake_get_reversed_payment_allocation_amount,
    )
    monkeypatch.setattr(
        service,
        "reverse_sponsor_invoice_payment",
        fake_reverse_sponsor_invoice_payment,
    )
    monkeypatch.setattr(
        service,
        "create_payment_allocation_reversal_record",
        fake_create_payment_allocation_reversal_record,
    )
    monkeypatch.setattr(
        service,
        "reverse_payment_receipt_allocation_amount",
        fake_reverse_payment_receipt_allocation_amount,
    )

    result = await reverse_sponsor_payment_allocation(
        allocation_id="allocation-1",
        amount="50.00",
        reason="Misallocated",
        reversed_by="finance-user",
    )

    assert result["receipt"]["unapplied_amount"] == Decimal("50.00")
    assert result["allocation_reversal"]["amount"] == Decimal("50.00")
    assert calls["payment_reversal"]["payment_id"] == "payment-1"
    assert calls["receipt"]["receipt_id"] == "receipt-1"


async def test_reverse_sponsor_payment_allocation_rejects_over_reversal(monkeypatch):
    async def fake_get_payment_allocation_record(**kwargs):
        return {
            "allocation_id": kwargs["allocation_id"],
            "receipt_id": "receipt-1",
            "invoice_id": "invoice-1",
            "payment_id": "payment-1",
            "amount": Decimal("100.00"),
        }

    async def fake_get_reversed_payment_allocation_amount(**kwargs):
        return Decimal("90.00")

    monkeypatch.setattr(service, "get_payment_allocation_record", fake_get_payment_allocation_record)
    monkeypatch.setattr(
        service,
        "get_reversed_payment_allocation_amount",
        fake_get_reversed_payment_allocation_amount,
    )

    with pytest.raises(SponsorInvoiceAmountError, match="exceeds unreversed"):
        await reverse_sponsor_payment_allocation(
            allocation_id="allocation-1",
            amount="25.00",
            reason="Too much",
        )
