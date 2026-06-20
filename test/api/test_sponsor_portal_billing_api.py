from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import AsyncClient

from apps.api.main import app


PARTNER_HEADERS = {"x-api-key": "test-fnb-key"}


pytestmark = pytest.mark.asyncio


async def test_sponsor_portal_dashboard_api(monkeypatch):
    from apps.api.routers import sponsor_portal_billing

    calls = {}

    async def fake_get_sponsor_billing_dashboard(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": kwargs["tenant_code"].strip().upper(),
            "sponsor_code": kwargs["sponsor_code"].strip().upper(),
            "invoice_count": 2,
            "totals": {"outstanding_amount": Decimal("115.00")},
        }

    monkeypatch.setattr(
        sponsor_portal_billing,
        "get_sponsor_billing_dashboard",
        fake_get_sponsor_billing_dashboard,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/tenants/FNB/sponsors/BOXER/billing/dashboard",
            params={"period_start": "2026-06-01", "period_end": "2026-06-30"},
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["dashboard"]["tenant_code"] == "FNB"
    assert body["dashboard"]["sponsor_code"] == "BOXER"
    assert calls["sponsor_code"] == "BOXER"


async def test_sponsor_portal_list_invoices_api(monkeypatch):
    from apps.api.routers import sponsor_portal_billing

    calls = {}

    async def fake_list_sponsor_invoices(**kwargs):
        calls.update(kwargs)
        return [{"invoice_id": "invoice-1", "status": "ISSUED"}]

    monkeypatch.setattr(
        sponsor_portal_billing,
        "list_sponsor_invoices",
        fake_list_sponsor_invoices,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/tenants/FNB/sponsors/BOXER/billing/invoices",
            params={"status": "issued"},
        )

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 1
    assert body["items"][0]["invoice_id"] == "invoice-1"
    assert calls["tenant_code"] == "FNB"
    assert calls["sponsor_code"] == "BOXER"
    assert calls["status"] == "issued"


async def test_sponsor_portal_invoice_detail_blocks_wrong_sponsor(monkeypatch):
    from apps.api.routers import sponsor_portal_billing

    async def fake_get_sponsor_invoice(**kwargs):
        return {
            "invoice_id": kwargs["invoice_id"],
            "tenant_code": "FNB",
            "sponsor_code": "OTHER",
        }

    monkeypatch.setattr(
        sponsor_portal_billing,
        "get_sponsor_invoice",
        fake_get_sponsor_invoice,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/tenants/FNB/sponsors/BOXER/billing/invoices/invoice-1",
        )

    assert response.status_code == 404


async def test_sponsor_portal_statement_api(monkeypatch):
    from apps.api.routers import sponsor_portal_billing

    calls = {}

    async def fake_get_sponsor_statement(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": "FNB",
            "sponsor_code": "BOXER",
            "invoice_count": 1,
            "totals": {"outstanding_amount": Decimal("65.00")},
        }

    monkeypatch.setattr(
        sponsor_portal_billing,
        "get_sponsor_statement",
        fake_get_sponsor_statement,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/tenants/FNB/sponsors/BOXER/billing/statements",
            params={"period_start": "2026-06-01", "period_end": "2026-06-30"},
        )

    assert response.status_code == 200
    body = response.json()

    assert body["statement"]["invoice_count"] == 1
    assert calls["period_start"].isoformat() == "2026-06-01"


async def test_sponsor_portal_payment_receipts_api(monkeypatch):
    from apps.api.routers import sponsor_portal_billing

    async def fake_list_sponsor_payment_receipts(**kwargs):
        return [{"receipt_id": "receipt-1", "status": "PARTIALLY_APPLIED"}]

    monkeypatch.setattr(
        sponsor_portal_billing,
        "list_sponsor_payment_receipts",
        fake_list_sponsor_payment_receipts,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/tenants/FNB/sponsors/BOXER/billing/payment-receipts",
        )

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 1
    assert body["items"][0]["receipt_id"] == "receipt-1"


async def test_sponsor_portal_payment_receipt_detail_blocks_wrong_sponsor(monkeypatch):
    from apps.api.routers import sponsor_portal_billing

    async def fake_get_sponsor_payment_receipt(**kwargs):
        return {
            "receipt_id": kwargs["receipt_id"],
            "tenant_code": "FNB",
            "sponsor_code": "OTHER",
        }

    monkeypatch.setattr(
        sponsor_portal_billing,
        "get_sponsor_payment_receipt",
        fake_get_sponsor_payment_receipt,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/tenants/FNB/sponsors/BOXER/billing/payment-receipts/receipt-1",
        )

    assert response.status_code == 404


async def test_sponsor_portal_wallet_api(monkeypatch):
    from apps.api.routers import sponsor_portal_billing

    calls = {}

    async def fake_get_sponsor_wallet_by_sponsor(**kwargs):
        calls.update(kwargs)
        return {
            "wallet_id": "wallet-1",
            "tenant_code": kwargs["tenant_code"],
            "sponsor_code": kwargs["sponsor_code"],
            "available_balance": Decimal("500.00"),
        }

    monkeypatch.setattr(
        sponsor_portal_billing,
        "get_sponsor_wallet_by_sponsor",
        fake_get_sponsor_wallet_by_sponsor,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/tenants/FNB/sponsors/BOXER/billing/wallet",
        )

    assert response.status_code == 200
    body = response.json()

    assert body["wallet"]["wallet_id"] == "wallet-1"
    assert body["wallet"]["available_balance"] == "500.00"
    assert calls["tenant_code"] == "FNB"
    assert calls["sponsor_code"] == "BOXER"


async def test_sponsor_portal_wallet_ledger_api(monkeypatch):
    from apps.api.routers import sponsor_portal_billing

    wallet_calls = {}
    ledger_calls = {}

    async def fake_get_sponsor_wallet_by_sponsor(**kwargs):
        wallet_calls.update(kwargs)
        return {
            "wallet_id": "wallet-1",
            "tenant_code": kwargs["tenant_code"],
            "sponsor_code": kwargs["sponsor_code"],
            "available_balance": Decimal("500.00"),
        }

    async def fake_list_sponsor_wallet_transactions(**kwargs):
        ledger_calls.update(kwargs)
        return [
            {
                "ledger_id": "ledger-1",
                "wallet_id": kwargs["wallet_id"],
                "tenant_code": "FNB",
                "transaction_type": "CREDIT",
                "amount": Decimal("250.00"),
                "balance_before": Decimal("0.00"),
                "balance_after": Decimal("250.00"),
            }
        ]

    monkeypatch.setattr(
        sponsor_portal_billing,
        "get_sponsor_wallet_by_sponsor",
        fake_get_sponsor_wallet_by_sponsor,
    )
    monkeypatch.setattr(
        sponsor_portal_billing,
        "list_sponsor_wallet_transactions",
        fake_list_sponsor_wallet_transactions,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/tenants/FNB/sponsors/BOXER/billing/wallet/ledger",
            params={"limit": 50},
        )

    assert response.status_code == 200
    body = response.json()

    assert body["wallet_id"] == "wallet-1"
    assert body["count"] == 1
    assert body["items"][0]["transaction_type"] == "CREDIT"
    assert body["items"][0]["amount"] == "250.00"
    assert wallet_calls == {"tenant_code": "FNB", "sponsor_code": "BOXER"}
    assert ledger_calls == {"wallet_id": "wallet-1", "limit": 50}


async def test_sponsor_portal_wallet_ledger_returns_404_when_wallet_missing(monkeypatch):
    from apps.api.routers import sponsor_portal_billing

    async def fake_get_sponsor_wallet_by_sponsor(**kwargs):
        return None

    monkeypatch.setattr(
        sponsor_portal_billing,
        "get_sponsor_wallet_by_sponsor",
        fake_get_sponsor_wallet_by_sponsor,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/tenants/FNB/sponsors/BOXER/billing/wallet/ledger",
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Sponsor wallet not found"}


async def test_sponsor_portal_contracts_api(monkeypatch):
    from apps.api.routers import sponsor_portal_billing

    calls = {}

    async def fake_list_funding_contracts(**kwargs):
        calls.update(kwargs)
        return [
            {
                "contract_id": "contract-1",
                "tenant_code": kwargs["tenant_code"],
                "sponsor_code": kwargs["sponsor_code"],
                "contract_value": Decimal("1000000.00"),
                "remaining_amount": Decimal("750000.00"),
                "status": "ACTIVE",
            }
        ]

    monkeypatch.setattr(
        sponsor_portal_billing,
        "list_funding_contracts",
        fake_list_funding_contracts,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/tenants/FNB/sponsors/BOXER/billing/contracts",
            params={"status": "ACTIVE", "limit": 25},
        )

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 1
    assert body["items"][0]["contract_id"] == "contract-1"
    assert body["items"][0]["remaining_amount"] == "750000.00"
    assert calls == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "status": "ACTIVE",
        "limit": 25,
    }


async def test_sponsor_portal_contract_detail_api(monkeypatch):
    from apps.api.routers import sponsor_portal_billing

    async def fake_get_funding_contract(**kwargs):
        return {
            "contract_id": kwargs["contract_id"],
            "tenant_code": "FNB",
            "sponsor_code": "BOXER",
            "contract_name": "Boxer Rewards 2026",
            "utilised_amount": Decimal("150000.00"),
        }

    monkeypatch.setattr(
        sponsor_portal_billing,
        "get_funding_contract",
        fake_get_funding_contract,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/tenants/FNB/sponsors/BOXER/billing/contracts/contract-1",
        )

    assert response.status_code == 200
    body = response.json()

    assert body["contract"]["contract_id"] == "contract-1"
    assert body["contract"]["utilised_amount"] == "150000.00"


async def test_sponsor_portal_contract_detail_blocks_wrong_sponsor(monkeypatch):
    from apps.api.routers import sponsor_portal_billing

    async def fake_get_funding_contract(**kwargs):
        return {
            "contract_id": kwargs["contract_id"],
            "tenant_code": "FNB",
            "sponsor_code": "OTHER",
        }

    monkeypatch.setattr(
        sponsor_portal_billing,
        "get_funding_contract",
        fake_get_funding_contract,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/tenants/FNB/sponsors/BOXER/billing/contracts/contract-1",
        )

    assert response.status_code == 404


async def test_sponsor_portal_contract_ledger_api(monkeypatch):
    from apps.api.routers import sponsor_portal_billing

    calls = {}

    async def fake_get_funding_contract(**kwargs):
        return {
            "contract_id": kwargs["contract_id"],
            "tenant_code": "FNB",
            "sponsor_code": "BOXER",
        }

    async def fake_get_funding_contract_ledger(**kwargs):
        calls.update(kwargs)
        return [
            {
                "ledger_id": "ledger-1",
                "contract_id": kwargs["contract_id"],
                "event_type": "BUDGET_UTILISED",
                "amount": Decimal("250.00"),
            }
        ]

    monkeypatch.setattr(
        sponsor_portal_billing,
        "get_funding_contract",
        fake_get_funding_contract,
    )
    monkeypatch.setattr(
        sponsor_portal_billing,
        "get_funding_contract_ledger",
        fake_get_funding_contract_ledger,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/tenants/FNB/sponsors/BOXER/billing/contracts/contract-1/ledger",
            params={"limit": 50},
        )

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 1
    assert body["items"][0]["event_type"] == "BUDGET_UTILISED"
    assert body["items"][0]["amount"] == "250.00"
    assert calls == {"contract_id": "contract-1", "limit": 50}


async def test_sponsor_portal_forecast_api(monkeypatch):
    from apps.api.routers import sponsor_portal_billing

    calls = {}

    async def fake_get_sponsor_funding_forecast(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": kwargs["tenant_code"].upper(),
            "sponsor_code": kwargs["sponsor_code"].upper(),
            "currency": kwargs["currency"].upper(),
            "wallet": {
                "available_balance": Decimal("900000.00"),
                "forecast_status": "HEALTHY",
            },
            "contracts": {
                "count": 1,
                "forecast_status": "HEALTHY",
                "items": [],
            },
        }

    monkeypatch.setattr(
        sponsor_portal_billing,
        "get_sponsor_funding_forecast",
        fake_get_sponsor_funding_forecast,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/tenants/FNB/sponsors/BOXER/billing/forecast",
            params={
                "currency": "zar",
                "burn_window_days": 60,
                "buffer_days": 45,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["forecast"]["tenant_code"] == "FNB"
    assert body["forecast"]["sponsor_code"] == "BOXER"
    assert body["forecast"]["wallet"]["available_balance"] == "900000.00"
    assert calls == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "currency": "zar",
        "burn_window_days": 60,
        "buffer_days": 45,
    }


async def test_sponsor_portal_forecast_not_found(monkeypatch):
    from apps.api.routers import sponsor_portal_billing

    async def fake_get_sponsor_funding_forecast(**kwargs):
        return None

    monkeypatch.setattr(
        sponsor_portal_billing,
        "get_sponsor_funding_forecast",
        fake_get_sponsor_funding_forecast,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/tenants/FNB/sponsors/BOXER/billing/forecast",
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Sponsor funding forecast not found"}


async def test_sponsor_portal_blocks_wrong_tenant():
    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/tenants/PNP/sponsors/BOXER/billing/invoices",
        )

    assert response.status_code == 403


async def test_sponsor_portal_requires_api_key():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/v1/tenants/FNB/sponsors/BOXER/billing/invoices",
        )

    assert response.status_code == 401
