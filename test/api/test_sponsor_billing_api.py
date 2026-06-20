from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import AsyncClient

from apps.api.main import app


ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


pytestmark = pytest.mark.asyncio


async def test_create_sponsor_invoice_api(monkeypatch):
    from apps.api.routers import sponsor_billing

    calls = {}
    audit_calls = []

    async def fake_create_sponsor_invoice(**kwargs):
        calls.update(kwargs)
        return {
            "invoice_id": "invoice-1",
            "tenant_code": kwargs["tenant_code"].upper(),
            "sponsor_code": kwargs["sponsor_code"].upper(),
            "status": "DRAFT",
            "total_amount": Decimal("115.00"),
            "lines": [{"line_id": "line-1"}],
        }

    async def fake_audit(**kwargs):
        audit_calls.append(kwargs)

    monkeypatch.setattr(
        sponsor_billing,
        "create_sponsor_invoice",
        fake_create_sponsor_invoice,
    )
    monkeypatch.setattr(
        sponsor_billing,
        "try_write_admin_audit",
        fake_audit,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/sponsor-billing/invoices",
            json={
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "sponsor_name": "Boxer",
                "currency": "ZAR",
                "vat_rate": "0.15",
                "lines": [
                    {
                        "description": "June utilised rewards",
                        "quantity": "1",
                        "unit_amount": "100.00",
                    }
                ],
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["invoice"]["invoice_id"] == "invoice-1"
    assert calls["vat_rate"] == Decimal("0.15")
    assert calls["lines"][0]["description"] == "June utilised rewards"
    assert audit_calls[0]["action_type"] == "SPONSOR_INVOICE_CREATE"
    assert audit_calls[0]["target_id"] == "invoice-1"


async def test_list_sponsor_invoices_api(monkeypatch):
    from apps.api.routers import sponsor_billing

    calls = {}

    async def fake_list_sponsor_invoices(**kwargs):
        calls.update(kwargs)
        return [{"invoice_id": "invoice-1", "status": "ISSUED"}]

    monkeypatch.setattr(
        sponsor_billing,
        "list_sponsor_invoices",
        fake_list_sponsor_invoices,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/funding/sponsor-billing/invoices",
            params={
                "tenant_code": " fnb ",
                "sponsor_code": " boxer ",
                "status": "issued",
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["tenant_code"] == "FNB"
    assert body["count"] == 1
    assert calls["tenant_code"] == " fnb "
    assert calls["sponsor_code"] == " boxer "


async def test_generate_sponsor_invoice_from_utilisation_api(monkeypatch):
    from apps.api.routers import sponsor_billing

    calls = {}

    async def fake_generate_sponsor_invoice_from_utilisation(**kwargs):
        calls.update(kwargs)
        return {
            "invoice_id": "invoice-1",
            "status": "ISSUED" if kwargs["issue"] else "DRAFT",
            "lines": [{"source_ledger_id": "ledger-1"}],
        }

    monkeypatch.setattr(
        sponsor_billing,
        "generate_sponsor_invoice_from_utilisation",
        fake_generate_sponsor_invoice_from_utilisation,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/sponsor-billing/invoices/generate-from-utilisation",
            json={
                "contract_id": "contract-1",
                "invoice_period_start": "2026-06-01",
                "invoice_period_end": "2026-06-30",
                "due_date": "2026-07-15",
                "vat_rate": "0.15",
                "issue": True,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["invoice"]["status"] == "ISSUED"
    assert calls["contract_id"] == "contract-1"
    assert calls["vat_rate"] == Decimal("0.15")
    assert calls["issue"] is True


async def test_scheduled_sponsor_billing_generation_api(monkeypatch):
    from apps.api.routers import sponsor_billing

    calls = {}

    async def fake_run_sponsor_billing_generation(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": kwargs["tenant_code"].strip().upper(),
            "dry_run": kwargs["dry_run"],
            "contract_count": 1,
            "ready_count": 1,
            "generated_count": 0,
            "items": [{"contract_id": "contract-1", "status": "READY"}],
        }

    monkeypatch.setattr(
        sponsor_billing,
        "run_sponsor_billing_generation",
        fake_run_sponsor_billing_generation,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/sponsor-billing/scheduled-generation",
            json={
                "tenant_code": " fnb ",
                "sponsor_code": "boxer",
                "invoice_period_start": "2026-06-01",
                "invoice_period_end": "2026-06-30",
                "due_date": "2026-07-15",
                "vat_rate": "0.15",
                "dry_run": True,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["generation"]["tenant_code"] == "FNB"
    assert body["generation"]["ready_count"] == 1
    assert calls["sponsor_code"] == "boxer"
    assert calls["vat_rate"] == Decimal("0.15")
    assert calls["dry_run"] is True


async def test_get_sponsor_statement_api(monkeypatch):
    from apps.api.routers import sponsor_billing

    calls = {}

    async def fake_get_sponsor_statement(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": kwargs["tenant_code"].strip().upper(),
            "sponsor_code": kwargs["sponsor_code"].strip().upper(),
            "period_start": kwargs["period_start"],
            "period_end": kwargs["period_end"],
            "invoice_count": 1,
            "payment_count": 1,
            "totals": {
                "total_amount": Decimal("115.00"),
                "payments_received_amount": Decimal("50.00"),
                "outstanding_amount": Decimal("65.00"),
            },
            "invoices": [{"invoice_id": "invoice-1"}],
            "payments": [{"payment_id": "payment-1"}],
        }

    monkeypatch.setattr(
        sponsor_billing,
        "get_sponsor_statement",
        fake_get_sponsor_statement,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/funding/sponsor-billing/statements",
            params={
                "tenant_code": " fnb ",
                "sponsor_code": " boxer ",
                "period_start": "2026-06-01",
                "period_end": "2026-06-30",
                "currency": "zar",
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["statement"]["tenant_code"] == "FNB"
    assert body["statement"]["invoice_count"] == 1
    assert body["statement"]["totals"]["outstanding_amount"] == "65.00"
    assert calls["currency"] == "zar"


async def test_get_sponsor_billing_dashboard_api(monkeypatch):
    from apps.api.routers import sponsor_billing

    calls = {}

    async def fake_get_sponsor_billing_dashboard(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": kwargs["tenant_code"].strip().upper(),
            "sponsor_code": kwargs["sponsor_code"].strip().upper(),
            "invoice_count": 3,
            "overdue_count": 1,
            "status_counts": {"ISSUED": 2, "PAID": 1},
            "totals": {
                "total_amount": Decimal("345.00"),
                "paid_amount": Decimal("115.00"),
                "outstanding_amount": Decimal("230.00"),
                "overdue_outstanding_amount": Decimal("115.00"),
            },
            "recent_invoices": [{"invoice_id": "invoice-1"}],
            "overdue_invoices": [{"invoice_id": "invoice-2"}],
        }

    monkeypatch.setattr(
        sponsor_billing,
        "get_sponsor_billing_dashboard",
        fake_get_sponsor_billing_dashboard,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/funding/sponsor-billing/dashboard",
            params={
                "tenant_code": " fnb ",
                "sponsor_code": " boxer ",
                "period_start": "2026-06-01",
                "period_end": "2026-06-30",
                "currency": "zar",
                "as_of_date": "2026-07-01",
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["dashboard"]["tenant_code"] == "FNB"
    assert body["dashboard"]["overdue_count"] == 1
    assert body["dashboard"]["totals"]["outstanding_amount"] == "230.00"
    assert calls["currency"] == "zar"


async def test_get_sponsor_vat_report_api(monkeypatch):
    from apps.api.routers import sponsor_billing

    calls = {}

    async def fake_get_sponsor_vat_report(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": kwargs["tenant_code"].strip().upper(),
            "period_start": kwargs["period_start"],
            "period_end": kwargs["period_end"],
            "invoice_count": 2,
            "totals": {
                "subtotal_amount": Decimal("300.00"),
                "vat_amount": Decimal("45.00"),
                "total_amount": Decimal("345.00"),
            },
            "by_status": [{"status": "ISSUED", "vat_amount": Decimal("45.00")}],
            "by_currency": [{"currency": "ZAR", "vat_amount": Decimal("45.00")}],
            "invoices": [{"invoice_id": "invoice-1"}],
        }

    monkeypatch.setattr(
        sponsor_billing,
        "get_sponsor_vat_report",
        fake_get_sponsor_vat_report,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/funding/sponsor-billing/vat-report",
            params={
                "tenant_code": " fnb ",
                "period_start": "2026-06-01",
                "period_end": "2026-06-30",
                "sponsor_code": "boxer",
                "currency": "zar",
                "status": "issued",
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["report"]["tenant_code"] == "FNB"
    assert body["report"]["invoice_count"] == 2
    assert body["report"]["totals"]["vat_amount"] == "45.00"
    assert calls["currency"] == "zar"
    assert calls["status"] == "issued"


async def test_issue_sponsor_invoice_api(monkeypatch):
    from apps.api.routers import sponsor_billing

    async def fake_issue_sponsor_invoice(**kwargs):
        return {"invoice_id": kwargs["invoice_id"], "status": "ISSUED"}

    monkeypatch.setattr(
        sponsor_billing,
        "issue_sponsor_invoice",
        fake_issue_sponsor_invoice,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/sponsor-billing/invoices/invoice-1/issue",
        )

    assert response.status_code == 200
    assert response.json()["invoice"]["status"] == "ISSUED"


async def test_record_sponsor_invoice_payment_api(monkeypatch):
    from apps.api.routers import sponsor_billing

    calls = {}

    async def fake_record_sponsor_invoice_payment(**kwargs):
        calls.update(kwargs)
        return {
            "invoice": {"invoice_id": kwargs["invoice_id"], "status": "PAID"},
            "payment": {
                "payment_id": "payment-1",
                "amount": kwargs["amount"],
            },
        }

    monkeypatch.setattr(
        sponsor_billing,
        "record_sponsor_invoice_payment",
        fake_record_sponsor_invoice_payment,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/sponsor-billing/invoices/invoice-1/payments",
            json={
                "amount": "115.00",
                "payment_reference": "PAY-1",
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["invoice"]["status"] == "PAID"
    assert body["payment"]["payment_id"] == "payment-1"
    assert calls["amount"] == Decimal("115.00")


async def test_allocate_sponsor_payment_api(monkeypatch):
    from apps.api.routers import sponsor_billing

    calls = {}

    async def fake_allocate_sponsor_payment(**kwargs):
        calls.update(kwargs)
        return {
            "receipt": {
                "receipt_id": "receipt-1",
                "status": "PARTIALLY_APPLIED",
                "unapplied_amount": Decimal("25.00"),
            },
            "allocations": [{"allocation_id": "allocation-1"}],
            "invoices": [{"invoice_id": "invoice-1", "status": "PAID"}],
            "unapplied_amount": Decimal("25.00"),
        }

    monkeypatch.setattr(
        sponsor_billing,
        "allocate_sponsor_payment",
        fake_allocate_sponsor_payment,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/sponsor-billing/payment-receipts",
            json={
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "amount": "175.00",
                "payment_reference": "PAY-1",
                "allocated_by": "finance-user",
                "allocations": [
                    {"invoice_id": "invoice-1", "amount": "150.00"},
                ],
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["receipt"]["receipt_id"] == "receipt-1"
    assert body["unapplied_amount"] == "25.00"
    assert calls["amount"] == Decimal("175.00")
    assert calls["allocations"][0]["invoice_id"] == "invoice-1"


async def test_get_sponsor_payment_receipt_api(monkeypatch):
    from apps.api.routers import sponsor_billing

    async def fake_get_sponsor_payment_receipt(**kwargs):
        return {
            "receipt_id": kwargs["receipt_id"],
            "status": "PARTIALLY_APPLIED",
            "allocations": [{"allocation_id": "allocation-1"}],
        }

    monkeypatch.setattr(
        sponsor_billing,
        "get_sponsor_payment_receipt",
        fake_get_sponsor_payment_receipt,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/funding/sponsor-billing/payment-receipts/receipt-1",
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["receipt"]["receipt_id"] == "receipt-1"
    assert body["receipt"]["allocations"][0]["allocation_id"] == "allocation-1"


async def test_reverse_sponsor_invoice_payment_api(monkeypatch):
    from apps.api.routers import sponsor_billing

    calls = {}

    async def fake_reverse_sponsor_invoice_payment(**kwargs):
        calls.update(kwargs)
        return {
            "invoice": {"invoice_id": "invoice-1", "status": "PARTIALLY_PAID"},
            "payment": {"payment_id": kwargs["payment_id"], "amount": Decimal("115.00")},
            "reversal": {
                "reversal_id": "reversal-1",
                "amount": kwargs["amount"],
                "reason": kwargs["reason"],
            },
        }

    monkeypatch.setattr(
        sponsor_billing,
        "reverse_sponsor_invoice_payment",
        fake_reverse_sponsor_invoice_payment,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/sponsor-billing/payments/payment-1/reversals",
            json={
                "amount": "25.00",
                "reason": "Duplicate payment",
                "reversed_by": "finance-user",
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["invoice"]["status"] == "PARTIALLY_PAID"
    assert body["reversal"]["amount"] == "25.00"
    assert calls["payment_id"] == "payment-1"
    assert calls["amount"] == Decimal("25.00")
    assert calls["reason"] == "Duplicate payment"


async def test_reverse_sponsor_payment_allocation_api(monkeypatch):
    from apps.api.routers import sponsor_billing

    calls = {}

    async def fake_reverse_sponsor_payment_allocation(**kwargs):
        calls.update(kwargs)
        return {
            "receipt": {"receipt_id": "receipt-1", "status": "PARTIALLY_APPLIED"},
            "allocation": {"allocation_id": kwargs["allocation_id"]},
            "allocation_reversal": {
                "reversal_id": "allocation-reversal-1",
                "amount": kwargs["amount"],
            },
            "invoice": {"invoice_id": "invoice-1", "status": "PARTIALLY_PAID"},
            "payment": {"payment_id": "payment-1"},
            "reversal": {"reversal_id": "payment-reversal-1"},
        }

    monkeypatch.setattr(
        sponsor_billing,
        "reverse_sponsor_payment_allocation",
        fake_reverse_sponsor_payment_allocation,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/sponsor-billing/payment-allocations/allocation-1/reversals",
            json={
                "amount": "25.00",
                "reason": "Misallocated",
                "reversed_by": "finance-user",
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["allocation_reversal"]["amount"] == "25.00"
    assert calls["allocation_id"] == "allocation-1"
    assert calls["amount"] == Decimal("25.00")


async def test_sponsor_billing_requires_admin_key():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/admin/funding/sponsor-billing/invoices",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 401
