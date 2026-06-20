from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.api.main import app


ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


pytestmark = pytest.mark.asyncio


def rule_payload(rule_id: str, **overrides):
    payload = {
        "rule_id": rule_id,
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "campaign_code": "BOXER_ACQ",
        "distributor_type": "AGENCY",
        "commission_type": "PERCENTAGE",
        "rate": Decimal("0.050000"),
        "fixed_amount": None,
        "min_commission": Decimal("10.00"),
        "max_commission": Decimal("500.00"),
        "currency": "ZAR",
        "rule_status": "ACTIVE",
        "priority": 10,
        "description": "Agency commission",
        "metadata": {"source": "test"},
        "created_at": "2026-06-12T10:00:00",
        "updated_at": "2026-06-12T10:00:00",
    }
    payload.update(overrides)
    return payload


def event_payload(event_id: str, distributor_id: str, rule_id: str, **overrides):
    payload = {
        "commission_event_id": event_id,
        "tenant_code": "FNB",
        "distributor_id": distributor_id,
        "distributor_code": "AGENCY_001",
        "wallet_id": None,
        "rule_id": rule_id,
        "sponsor_code": "BOXER",
        "campaign_code": "BOXER_ACQ",
        "source_event_id": "sale-1",
        "activity_type": "SALE_CONFIRMED",
        "sale_amount": Decimal("1000.00"),
        "commission_amount": Decimal("50.00"),
        "currency": "ZAR",
        "commission_status": "CALCULATED",
        "credited_at": None,
        "correlation_id": "commission-corr-1",
        "metadata": {"source": "test"},
        "created_at": "2026-06-12T10:00:00",
        "updated_at": "2026-06-12T10:00:00",
    }
    payload.update(overrides)
    return payload


async def test_create_commission_rule(monkeypatch):
    from apps.api.routers.distribution import admin_commissions

    rule_id = str(uuid4())
    calls = {}

    async def fake_create_commission_rule(**kwargs):
        calls.update(kwargs)
        return rule_payload(rule_id)

    monkeypatch.setattr(
        admin_commissions,
        "create_commission_rule",
        fake_create_commission_rule,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/distribution/commissions/rules",
            json={
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "campaign_code": "BOXER_ACQ",
                "distributor_type": "AGENCY",
                "commission_type": "PERCENTAGE",
                "rate": "0.05",
                "min_commission": "10.00",
                "max_commission": "500.00",
                "currency": "ZAR",
                "priority": 10,
                "description": "Agency commission",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["rule_id"] == rule_id
    assert body["rate"] == "0.050000"
    assert calls == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "campaign_code": "BOXER_ACQ",
        "distributor_type": "AGENCY",
        "commission_type": "PERCENTAGE",
        "rate": Decimal("0.05"),
        "fixed_amount": None,
        "min_commission": Decimal("10.00"),
        "max_commission": Decimal("500.00"),
        "currency": "ZAR",
        "priority": 10,
        "description": "Agency commission",
        "metadata": {"source": "test"},
    }


async def test_list_commission_rules(monkeypatch):
    from apps.api.routers.distribution import admin_commissions

    rule_id = str(uuid4())
    calls = {}

    async def fake_list_commission_rules(**kwargs):
        calls.update(kwargs)
        return [rule_payload(rule_id)]

    monkeypatch.setattr(
        admin_commissions,
        "list_commission_rules",
        fake_list_commission_rules,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/distribution/commissions/rules",
            params={
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "campaign_code": "BOXER_ACQ",
                "distributor_type": "AGENCY",
                "rule_status": "ACTIVE",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    assert response.json()[0]["rule_id"] == rule_id
    assert calls == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "campaign_code": "BOXER_ACQ",
        "distributor_type": "AGENCY",
        "rule_status": "ACTIVE",
        "limit": 25,
    }


async def test_calculate_commission(monkeypatch):
    from apps.api.routers.distribution import admin_commissions

    event_id = str(uuid4())
    distributor_id = str(uuid4())
    rule_id = str(uuid4())
    wallet_id = str(uuid4())
    calls = {}

    async def fake_calculate_commission(**kwargs):
        calls.update(kwargs)
        return {
            "commission_event": event_payload(
                event_id,
                distributor_id,
                rule_id,
                wallet_id=wallet_id,
                commission_status="CREDITED",
                credited_at="2026-06-12T10:00:01",
            ),
            "rule": rule_payload(rule_id),
            "wallet": {
                "wallet_id": wallet_id,
                "distributor_id": distributor_id,
                "tenant_code": "FNB",
                "distributor_code": "AGENCY_001",
                "currency": "ZAR",
                "current_balance": Decimal("50.00"),
                "available_balance": Decimal("50.00"),
                "held_balance": Decimal("0.00"),
                "paid_out_balance": Decimal("0.00"),
                "reversed_balance": Decimal("0.00"),
                "status": "ACTIVE",
                "metadata": {},
                "created_at": "2026-06-12T10:00:00",
                "updated_at": "2026-06-12T10:00:01",
            },
        }

    monkeypatch.setattr(
        admin_commissions,
        "calculate_commission",
        fake_calculate_commission,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/distribution/commissions/calculate",
            json={
                "tenant_code": "FNB",
                "distributor_id": distributor_id,
                "sponsor_code": "BOXER",
                "campaign_code": "BOXER_ACQ",
                "activity_type": "SALE_CONFIRMED",
                "sale_amount": "1000.00",
                "source_event_id": "sale-1",
                "wallet_id": wallet_id,
                "credit_wallet": True,
                "correlation_id": "commission-corr-1",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["commission_event"]["commission_amount"] == "50.00"
    assert body["commission_event"]["commission_status"] == "CREDITED"
    assert body["wallet"]["current_balance"] == "50.00"
    assert calls == {
        "tenant_code": "FNB",
        "distributor_id": distributor_id,
        "sponsor_code": "BOXER",
        "campaign_code": "BOXER_ACQ",
        "activity_type": "SALE_CONFIRMED",
        "sale_amount": Decimal("1000.00"),
        "source_event_id": "sale-1",
        "wallet_id": wallet_id,
        "credit_wallet": True,
        "correlation_id": "commission-corr-1",
        "metadata": {"source": "test"},
    }


async def test_list_commission_events(monkeypatch):
    from apps.api.routers.distribution import admin_commissions

    event_id = str(uuid4())
    distributor_id = str(uuid4())
    rule_id = str(uuid4())
    calls = {}

    async def fake_list_commission_events(**kwargs):
        calls.update(kwargs)
        return [event_payload(event_id, distributor_id, rule_id)]

    monkeypatch.setattr(
        admin_commissions,
        "list_commission_events",
        fake_list_commission_events,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/distribution/commissions/events",
            params={
                "tenant_code": "FNB",
                "distributor_id": distributor_id,
                "commission_status": "CALCULATED",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    assert response.json()[0]["commission_event_id"] == event_id
    assert calls == {
        "tenant_code": "FNB",
        "distributor_id": distributor_id,
        "commission_status": "CALCULATED",
        "limit": 25,
    }


async def test_missing_commission_rule_returns_404(monkeypatch):
    from apps.api.routers.distribution import admin_commissions

    async def fake_calculate_commission(**kwargs):
        raise admin_commissions.CommissionRuleNotFound(
            "No active commission rule matched"
        )

    monkeypatch.setattr(
        admin_commissions,
        "calculate_commission",
        fake_calculate_commission,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/distribution/commissions/calculate",
            json={
                "tenant_code": "FNB",
                "distributor_id": str(uuid4()),
                "activity_type": "SALE_CONFIRMED",
            },
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "No active commission rule matched"}


async def test_duplicate_commission_event_returns_409(monkeypatch):
    from apps.api.routers.distribution import admin_commissions

    async def fake_calculate_commission(**kwargs):
        raise admin_commissions.CommissionDuplicateEvent(
            "Commission event already exists"
        )

    monkeypatch.setattr(
        admin_commissions,
        "calculate_commission",
        fake_calculate_commission,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/distribution/commissions/calculate",
            json={
                "tenant_code": "FNB",
                "distributor_id": str(uuid4()),
                "activity_type": "SALE_CONFIRMED",
                "source_event_id": "sale-1",
            },
        )

    assert response.status_code == 409
    assert response.json() == {"detail": "Commission event already exists"}
