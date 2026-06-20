from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from services.funding.alerts import (
    acknowledge_funding_alert,
    create_funding_alert,
    determine_forecast_alert,
    determine_status_alert,
    evaluate_funding_alerts,
    list_funding_alerts,
    resolve_funding_alert,
)


class FakeConnection:
    def __init__(self, *, existing=None, row=None, rows=None):
        self.existing = existing
        self.row = row
        self.rows = rows or []

    async def fetchrow(self, query, *args):
        if "SELECT" in query and "FROM funding_alerts" in query:
            return self.existing

        return self.row

    async def fetch(self, query, *args):
        return self.rows


class FakeDbConnection:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return None


def patch_db(monkeypatch, conn):
    monkeypatch.setattr(
        "services.funding.alerts.db_connection",
        lambda: FakeDbConnection(conn),
    )


@pytest.mark.parametrize(
    "days_remaining,available_balance,reserved_amount,expected_type",
    [
        (Decimal("40.00"), Decimal("1000.00"), Decimal("100.00"), None),
        (None, Decimal("1000.00"), Decimal("100.00"), None),
        (Decimal("20.00"), Decimal("1000.00"), Decimal("100.00"), "FUNDING_WATCH"),
        (Decimal("10.00"), Decimal("1000.00"), Decimal("100.00"), "FUNDING_LOW"),
        (Decimal("5.00"), Decimal("1000.00"), Decimal("100.00"), "FUNDING_CRITICAL"),
        (Decimal("40.00"), Decimal("0.00"), Decimal("100.00"), "FUNDING_DEPLETED"),
        (Decimal("40.00"), Decimal("100.00"), Decimal("200.00"), "EXPOSURE_BREACH"),
    ],
)
def test_determine_forecast_alert(
    days_remaining,
    available_balance,
    reserved_amount,
    expected_type,
):
    result = determine_forecast_alert(
        days_remaining=days_remaining,
        available_balance=available_balance,
        reserved_amount=reserved_amount,
    )

    if expected_type is None:
        assert result is None
    else:
        assert result[0] == expected_type


@pytest.mark.parametrize(
    "forecast_status,expected",
    [
        ("DEPLETED", ("SPONSOR_WALLET_CRITICAL", "CRITICAL")),
        ("CRITICAL", ("SPONSOR_WALLET_CRITICAL", "CRITICAL")),
        ("LOW", ("SPONSOR_WALLET_LOW", "WARNING")),
        ("WATCH", ("SPONSOR_WALLET_WATCH", "INFO")),
        ("HEALTHY", None),
        ("NO_BURN", None),
    ],
)
def test_determine_status_alert(forecast_status, expected):
    result = determine_status_alert(
        forecast_status=forecast_status,
        critical_type="SPONSOR_WALLET_CRITICAL",
        low_type="SPONSOR_WALLET_LOW",
        watch_type="SPONSOR_WALLET_WATCH",
        critical_message="Critical",
        low_message="Low",
        watch_message="Watch",
    )

    if expected is None:
        assert result is None
    else:
        assert result[:2] == expected


@pytest.mark.asyncio
async def test_create_funding_alert_returns_existing(monkeypatch):
    alert_id = uuid4()
    account_id = uuid4()

    existing = {
        "alert_id": alert_id,
        "tenant_code": "FNB",
        "account_id": account_id,
        "alert_type": "FUNDING_LOW",
        "severity": "WARNING",
        "alert_message": "Existing alert",
        "status": "OPEN",
        "correlation_id": "corr-1",
        "created_at": None,
        "acknowledged_at": None,
        "resolved_at": None,
    }

    patch_db(monkeypatch, FakeConnection(existing=existing))

    result = await create_funding_alert(
        tenant_code="FNB",
        account_id=str(account_id),
        alert_type="FUNDING_LOW",
        severity="WARNING",
        alert_message="New alert",
        correlation_id="corr-2",
    )

    assert result == existing


@pytest.mark.asyncio
async def test_create_funding_alert_inserts_new(monkeypatch):
    alert_id = uuid4()
    account_id = uuid4()

    row = {
        "alert_id": alert_id,
        "tenant_code": "FNB",
        "account_id": account_id,
        "alert_type": "FUNDING_CRITICAL",
        "severity": "CRITICAL",
        "alert_message": "Critical alert",
        "status": "OPEN",
        "correlation_id": "corr-1",
        "created_at": None,
        "acknowledged_at": None,
        "resolved_at": None,
    }

    patch_db(monkeypatch, FakeConnection(existing=None, row=row))

    result = await create_funding_alert(
        tenant_code="FNB",
        account_id=str(account_id),
        alert_type="FUNDING_CRITICAL",
        severity="CRITICAL",
        alert_message="Critical alert",
        correlation_id="corr-1",
    )

    assert result == row


@pytest.mark.asyncio
async def test_list_funding_alerts(monkeypatch):
    alert_id = uuid4()
    account_id = uuid4()

    rows = [
        {
            "alert_id": alert_id,
            "tenant_code": "FNB",
            "account_id": account_id,
            "alert_type": "FUNDING_WATCH",
            "severity": "INFO",
            "alert_message": "Watch alert",
            "status": "OPEN",
            "correlation_id": None,
            "created_at": None,
            "acknowledged_at": None,
            "resolved_at": None,
        }
    ]

    patch_db(monkeypatch, FakeConnection(rows=rows))

    result = await list_funding_alerts(
        tenant_code="FNB",
        account_id=str(account_id),
        status="OPEN",
        limit=10,
    )

    assert result == rows


@pytest.mark.asyncio
async def test_acknowledge_funding_alert(monkeypatch):
    alert_id = uuid4()

    row = {
        "alert_id": alert_id,
        "tenant_code": "FNB",
        "account_id": uuid4(),
        "alert_type": "FUNDING_LOW",
        "severity": "WARNING",
        "alert_message": "Low alert",
        "status": "ACKNOWLEDGED",
        "correlation_id": None,
        "created_at": None,
        "acknowledged_at": None,
        "resolved_at": None,
    }

    patch_db(monkeypatch, FakeConnection(row=row))

    result = await acknowledge_funding_alert(alert_id=str(alert_id))

    assert result == row


@pytest.mark.asyncio
async def test_acknowledge_funding_alert_returns_none(monkeypatch):
    patch_db(monkeypatch, FakeConnection(row=None))

    result = await acknowledge_funding_alert(alert_id=str(uuid4()))

    assert result is None


@pytest.mark.asyncio
async def test_resolve_funding_alert(monkeypatch):
    alert_id = uuid4()

    row = {
        "alert_id": alert_id,
        "tenant_code": "FNB",
        "account_id": uuid4(),
        "alert_type": "FUNDING_LOW",
        "severity": "WARNING",
        "alert_message": "Low alert",
        "status": "RESOLVED",
        "correlation_id": None,
        "created_at": None,
        "acknowledged_at": None,
        "resolved_at": None,
    }

    patch_db(monkeypatch, FakeConnection(row=row))

    result = await resolve_funding_alert(alert_id=str(alert_id))

    assert result == row


@pytest.mark.asyncio
async def test_resolve_funding_alert_returns_none(monkeypatch):
    patch_db(monkeypatch, FakeConnection(row=None))

    result = await resolve_funding_alert(alert_id=str(uuid4()))

    assert result is None


@pytest.mark.asyncio
async def test_evaluate_funding_alerts(monkeypatch):
    account_id = str(uuid4())

    async def fake_list_funding_forecasts(**kwargs):
        return [
            {
                "tenant_code": "FNB",
                "account_id": account_id,
                "days_remaining": Decimal("5.00"),
                "available_balance": Decimal("500000.00"),
                "reserved_amount": Decimal("100000.00"),
            }
        ]

    async def fake_create_funding_alert(**kwargs):
        return {
            "alert_id": str(uuid4()),
            **kwargs,
            "status": "OPEN",
        }

    async def fake_list_sponsor_funding_forecasts(**kwargs):
        return [
            {
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "currency": "ZAR",
                "wallet": {
                    "forecast_status": "LOW",
                    "days_remaining": Decimal("10.00"),
                },
                "contracts": {
                    "forecast_status": "HEALTHY",
                    "days_remaining": Decimal("45.00"),
                },
            }
        ]

    async def fake_list_settlement_exposure_forecasts(**kwargs):
        return [
            {
                "tenant_code": "FNB",
                "provider_key": "CASH_PROVIDER",
                "currency": "ZAR",
                "forecast_status": "CRITICAL",
            }
        ]

    monkeypatch.setattr(
        "services.funding.alerts.list_funding_forecasts",
        fake_list_funding_forecasts,
    )

    monkeypatch.setattr(
        "services.funding.alerts.create_funding_alert",
        fake_create_funding_alert,
    )
    monkeypatch.setattr(
        "services.funding.alerts.list_sponsor_funding_forecasts",
        fake_list_sponsor_funding_forecasts,
    )
    monkeypatch.setattr(
        "services.funding.alerts.list_settlement_exposure_forecasts",
        fake_list_settlement_exposure_forecasts,
    )

    result = await evaluate_funding_alerts(
        tenant_code="FNB",
        correlation_id="corr-1",
    )

    assert result["status"] == "ok"
    assert result["evaluated_count"] == 1
    assert result["alert_count"] == 1
    assert result["items"][0]["alert_type"] == "FUNDING_CRITICAL"
    assert result["forecast_risk_count"] == 2
    assert result["forecast_risks"][0]["risk_scope"] == "SPONSOR_WALLET"
    assert result["forecast_risks"][0]["alert_type"] == "SPONSOR_WALLET_LOW"
    assert result["forecast_risks"][1]["risk_scope"] == "SETTLEMENT_EXPOSURE"
    assert result["forecast_risks"][1]["alert_type"] == "SETTLEMENT_EXPOSURE_CRITICAL"


@pytest.mark.asyncio
async def test_evaluate_funding_alerts_no_alerts(monkeypatch):
    async def fake_list_funding_forecasts(**kwargs):
        return [
            {
                "tenant_code": "FNB",
                "account_id": str(uuid4()),
                "days_remaining": Decimal("40.00"),
                "available_balance": Decimal("5000000.00"),
                "reserved_amount": Decimal("100000.00"),
            }
        ]

    async def fake_list_sponsor_funding_forecasts(**kwargs):
        return []

    async def fake_list_settlement_exposure_forecasts(**kwargs):
        return []

    monkeypatch.setattr(
        "services.funding.alerts.list_funding_forecasts",
        fake_list_funding_forecasts,
    )
    monkeypatch.setattr(
        "services.funding.alerts.list_sponsor_funding_forecasts",
        fake_list_sponsor_funding_forecasts,
    )
    monkeypatch.setattr(
        "services.funding.alerts.list_settlement_exposure_forecasts",
        fake_list_settlement_exposure_forecasts,
    )

    result = await evaluate_funding_alerts(tenant_code="FNB")

    assert result == {
        "status": "ok",
        "evaluated_count": 1,
        "alert_count": 0,
        "items": [],
        "forecast_risk_count": 0,
        "forecast_risks": [],
    }
