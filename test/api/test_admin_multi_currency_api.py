from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.api.main import app
from services.funding.multi_currency import CurrencyPairError, FxRateNotFound


pytestmark = pytest.mark.asyncio

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


def _fx_rate(**overrides):
    now = datetime.now(timezone.utc)
    data = {
        "fx_rate_id": uuid4(),
        "tenant_code": "FNB",
        "base_currency": "ZAR",
        "quote_currency": "USD",
        "rate": Decimal("0.05400000"),
        "rate_date": date(2026, 6, 12),
        "source_system": "MANUAL",
        "source_reference": "FX-001",
        "rate_status": "ACTIVE",
        "metadata": {"desk": "treasury"},
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    return data


def _quote(**overrides):
    data = {
        "quote_id": uuid4(),
        "tenant_code": "FNB",
        "source_currency": "ZAR",
        "target_currency": "USD",
        "source_amount": Decimal("1000.00"),
        "target_amount": Decimal("54.00"),
        "fx_rate_id": uuid4(),
        "rate": Decimal("0.05400000"),
        "rate_date": date(2026, 6, 12),
        "conversion_direction": "DIRECT",
        "metadata": {"source": "pytest"},
        "created_at": datetime.now(timezone.utc),
    }
    data.update(overrides)
    return data


def _cross_border_settlement(**overrides):
    now = datetime.now(timezone.utc)
    data = {
        "cross_border_settlement_id": uuid4(),
        "tenant_code": "FNB",
        "settlement_id": None,
        "sponsor_code": "SPONSOR-1",
        "distributor_id": None,
        "source_currency": "ZAR",
        "target_currency": "USD",
        "source_amount": Decimal("1000.00"),
        "target_amount": Decimal("54.00"),
        "fx_rate_id": uuid4(),
        "rate": Decimal("0.05400000"),
        "rate_date": date(2026, 6, 12),
        "settlement_status": "PENDING",
        "corridor": "ZA-US",
        "provider_key": "BANK",
        "provider_reference": "CB-001",
        "compliance_status": "PENDING",
        "failure_reason": None,
        "metadata": {"source": "pytest"},
        "created_at": now,
        "updated_at": now,
        "settled_at": None,
        "failed_at": None,
    }
    data.update(overrides)
    return data


async def test_create_fx_rate(monkeypatch):
    from apps.api.routers import admin_multi_currency

    audit_calls = []

    async def fake_create_fx_rate(**kwargs):
        assert kwargs["base_currency"] == "zar"
        assert kwargs["quote_currency"] == "usd"
        return _fx_rate(
            base_currency="ZAR",
            quote_currency="USD",
            rate=kwargs["rate"],
        )

    async def fake_audit(**kwargs):
        audit_calls.append(kwargs)

    monkeypatch.setattr(admin_multi_currency, "create_fx_rate", fake_create_fx_rate)
    monkeypatch.setattr(admin_multi_currency, "try_write_admin_audit", fake_audit)

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/multi-currency/fx-rates",
            json={
                "tenant_code": "FNB",
                "base_currency": "zar",
                "quote_currency": "usd",
                "rate": "0.054",
                "rate_date": "2026-06-12",
                "source_system": "MANUAL",
                "source_reference": "FX-001",
                "metadata": {"desk": "treasury"},
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["base_currency"] == "ZAR"
    assert body["quote_currency"] == "USD"
    assert body["rate"] == "0.054"
    assert audit_calls[0]["action_type"] == "FX_RATE_UPSERT"
    assert audit_calls[0]["action_domain"] == "FINANCE"
    assert audit_calls[0]["tenant_code"] == "FNB"


async def test_list_fx_rates(monkeypatch):
    from apps.api.routers import admin_multi_currency

    async def fake_list_fx_rates(**kwargs):
        assert kwargs["tenant_code"] == "FNB"
        assert kwargs["base_currency"] == "ZAR"
        return [_fx_rate()]

    monkeypatch.setattr(admin_multi_currency, "list_fx_rates", fake_list_fx_rates)

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/multi-currency/fx-rates",
            params={"tenant_code": "FNB", "base_currency": "ZAR"},
        )

    assert response.status_code == 200
    assert response.json()[0]["source_system"] == "MANUAL"


async def test_quote_conversion(monkeypatch):
    from apps.api.routers import admin_multi_currency

    async def fake_quote_currency_conversion(**kwargs):
        assert kwargs["source_amount"] == Decimal("1000.00")
        return _quote(source_amount=kwargs["source_amount"])

    monkeypatch.setattr(
        admin_multi_currency,
        "quote_currency_conversion",
        fake_quote_currency_conversion,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/multi-currency/quotes",
            json={
                "tenant_code": "FNB",
                "source_currency": "ZAR",
                "target_currency": "USD",
                "source_amount": "1000.00",
                "as_of_date": "2026-06-12",
                "persist_quote": True,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["target_amount"] == "54.00"
    assert body["conversion_direction"] == "DIRECT"


async def test_quote_conversion_missing_rate_returns_404(monkeypatch):
    from apps.api.routers import admin_multi_currency

    async def fake_quote_currency_conversion(**kwargs):
        raise FxRateNotFound("No active FX rate found for currency pair")

    monkeypatch.setattr(
        admin_multi_currency,
        "quote_currency_conversion",
        fake_quote_currency_conversion,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/multi-currency/quotes",
            json={
                "tenant_code": "FNB",
                "source_currency": "ZAR",
                "target_currency": "USD",
                "source_amount": "1000.00",
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "No active FX rate found for currency pair"


async def test_same_currency_pair_returns_400(monkeypatch):
    from apps.api.routers import admin_multi_currency

    async def fake_create_fx_rate(**kwargs):
        raise CurrencyPairError("Source and target currencies must differ")

    monkeypatch.setattr(admin_multi_currency, "create_fx_rate", fake_create_fx_rate)

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/multi-currency/fx-rates",
            json={
                "tenant_code": "FNB",
                "base_currency": "ZAR",
                "quote_currency": "ZAR",
                "rate": "1.00",
                "rate_date": "2026-06-12",
                "source_system": "MANUAL",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Source and target currencies must differ"


async def test_create_cross_border_settlement(monkeypatch):
    from apps.api.routers import admin_multi_currency

    async def fake_create_cross_border_settlement(**kwargs):
        assert kwargs["corridor"] == "ZA-US"
        return _cross_border_settlement()

    monkeypatch.setattr(
        admin_multi_currency,
        "create_cross_border_settlement",
        fake_create_cross_border_settlement,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/multi-currency/cross-border-settlements",
            json={
                "tenant_code": "FNB",
                "source_currency": "ZAR",
                "target_currency": "USD",
                "source_amount": "1000.00",
                "sponsor_code": "SPONSOR-1",
                "corridor": "ZA-US",
                "provider_key": "BANK",
                "provider_reference": "CB-001",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["settlement_status"] == "PENDING"
    assert body["target_amount"] == "54.00"


async def test_list_cross_border_settlements(monkeypatch):
    from apps.api.routers import admin_multi_currency

    async def fake_list_cross_border_settlements(**kwargs):
        assert kwargs["settlement_status"] == "PENDING"
        return [_cross_border_settlement()]

    monkeypatch.setattr(
        admin_multi_currency,
        "list_cross_border_settlements",
        fake_list_cross_border_settlements,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/multi-currency/cross-border-settlements",
            params={"tenant_code": "FNB", "settlement_status": "PENDING"},
        )

    assert response.status_code == 200
    assert response.json()[0]["corridor"] == "ZA-US"
