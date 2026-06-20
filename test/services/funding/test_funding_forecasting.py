from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from services.funding.forecasting import (
    _days_remaining,
    _forecast_status,
    _money,
    get_funding_forecast,
    get_sponsor_funding_forecast,
    list_settlement_exposure_forecasts,
    list_funding_forecasts,
    list_sponsor_funding_forecasts,
)


class FakeConnection:
    def __init__(
        self,
        *,
        account=None,
        burn=None,
        accounts=None,
        wallet=None,
        wallet_burn=None,
        wallets=None,
        contracts=None,
        contract_burn=None,
        settlement_exposure=None,
        settlement_burn=None,
    ):
        self.account = account
        self.burn = burn
        self.accounts = accounts or []
        self.wallet = wallet
        self.wallet_burn = wallet_burn
        self.wallets = wallets or []
        self.contracts = contracts or []
        self.contract_burn = contract_burn or []
        self.settlement_exposure = settlement_exposure or []
        self.settlement_burn = settlement_burn or []

    async def fetchrow(self, query, *args):
        if "FROM sponsor_wallets" in query:
            return self.wallet

        if "FROM sponsor_wallet_ledger" in query:
            return self.wallet_burn

        if "FROM funding_accounts" in query:
            return self.account

        if "FROM funding_transactions" in query:
            return self.burn

        return None

    async def fetch(self, query, *args):
        if "FROM fulfilment_settlement_ledger" in query and "status = 'SETTLED'" in query:
            return self.settlement_burn

        if "FROM fulfilment_settlement_ledger" in query:
            return self.settlement_exposure

        if "FROM sponsor_wallets" in query:
            return self.wallets

        if "FROM funding_contract_ledger" in query:
            return self.contract_burn

        if "FROM funding_contracts" in query:
            return self.contracts

        return self.accounts


class FakeDbConnection:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return None


def patch_db(monkeypatch, conn):
    monkeypatch.setattr(
        "services.funding.forecasting.db_connection",
        lambda: FakeDbConnection(conn),
    )


def test_money_handles_none():
    assert _money(None) == Decimal("0.00")


def test_money_rounds_to_two_decimals():
    assert _money("10.126") == Decimal("10.13")


def test_days_remaining_returns_none_when_no_burn():
    assert _days_remaining(
        available_balance=Decimal("1000.00"),
        burn_rate=Decimal("0.00"),
    ) is None


def test_days_remaining_calculates_value():
    assert _days_remaining(
        available_balance=Decimal("5000000.00"),
        burn_rate=Decimal("120000.00"),
    ) == Decimal("41.67")


@pytest.mark.parametrize(
    "available_balance,days_remaining,expected",
    [
        (Decimal("0.00"), None, "DEPLETED"),
        (Decimal("-1.00"), None, "DEPLETED"),
        (Decimal("100.00"), None, "NO_BURN"),
        (Decimal("100.00"), Decimal("6.99"), "CRITICAL"),
        (Decimal("100.00"), Decimal("14.99"), "LOW"),
        (Decimal("100.00"), Decimal("29.99"), "WATCH"),
        (Decimal("100.00"), Decimal("30.00"), "HEALTHY"),
    ],
)
def test_forecast_statuses(available_balance, days_remaining, expected):
    assert (
        _forecast_status(
            available_balance=available_balance,
            days_remaining=days_remaining,
        )
        == expected
    )


@pytest.mark.asyncio
async def test_get_funding_forecast_returns_none_when_account_not_found(monkeypatch):
    patch_db(
        monkeypatch,
        FakeConnection(account=None, burn={"total_burn": Decimal("0.00")}),
    )

    result = await get_funding_forecast(account_id=str(uuid4()))

    assert result is None


@pytest.mark.asyncio
async def test_get_funding_forecast_calculates_forecast(monkeypatch):
    account_id = uuid4()

    patch_db(
        monkeypatch,
        FakeConnection(
            account={
                "account_id": account_id,
                "tenant_code": "FNB",
                "account_name": "Main Rewards Funding",
                "account_type": "REWARD_POOL",
                "currency_code": "ZAR",
                "current_balance": Decimal("5000000.00"),
                "reserved_balance": Decimal("200000.00"),
                "available_balance": Decimal("4800000.00"),
                "status": "ACTIVE",
            },
            burn={"total_burn": Decimal("3600000.00")},
        ),
    )

    result = await get_funding_forecast(
        account_id=str(account_id),
        burn_window_days=30,
        buffer_days=30,
    )

    assert result == {
        "account_id": str(account_id),
        "tenant_code": "FNB",
        "account_name": "Main Rewards Funding",
        "account_type": "REWARD_POOL",
        "currency": "ZAR",
        "account_status": "ACTIVE",
        "current_balance": Decimal("5000000.00"),
        "reserved_amount": Decimal("200000.00"),
        "available_balance": Decimal("4800000.00"),
        "burn_window_days": 30,
        "buffer_days": 30,
        "total_burn": Decimal("3600000.00"),
        "average_burn_rate_per_day": Decimal("120000.00"),
        "days_remaining": Decimal("40.00"),
        "target_buffer": Decimal("3600000.00"),
        "funding_required": Decimal("0.00"),
        "recommended_top_up": Decimal("0.00"),
        "status": "HEALTHY",
    }


@pytest.mark.asyncio
async def test_get_funding_forecast_recommends_top_up(monkeypatch):
    account_id = uuid4()

    patch_db(
        monkeypatch,
        FakeConnection(
            account={
                "account_id": account_id,
                "tenant_code": "FNB",
                "account_name": "Low Funding Account",
                "account_type": "REWARD_POOL",
                "currency_code": "ZAR",
                "current_balance": Decimal("1000000.00"),
                "reserved_balance": Decimal("100000.00"),
                "available_balance": Decimal("900000.00"),
                "status": "ACTIVE",
            },
            burn={"total_burn": Decimal("3600000.00")},
        ),
    )

    result = await get_funding_forecast(
        account_id=str(account_id),
        burn_window_days=30,
        buffer_days=30,
    )

    assert result["average_burn_rate_per_day"] == Decimal("120000.00")
    assert result["days_remaining"] == Decimal("7.50")
    assert result["target_buffer"] == Decimal("3600000.00")
    assert result["funding_required"] == Decimal("2700000.00")
    assert result["recommended_top_up"] == Decimal("2700000.00")
    assert result["status"] == "LOW"


@pytest.mark.asyncio
async def test_get_funding_forecast_handles_no_burn(monkeypatch):
    account_id = uuid4()

    patch_db(
        monkeypatch,
        FakeConnection(
            account={
                "account_id": account_id,
                "tenant_code": "FNB",
                "account_name": "No Burn Account",
                "account_type": "REWARD_POOL",
                "currency_code": "ZAR",
                "current_balance": Decimal("1000000.00"),
                "reserved_balance": Decimal("0.00"),
                "available_balance": Decimal("1000000.00"),
                "status": "ACTIVE",
            },
            burn={"total_burn": Decimal("0.00")},
        ),
    )

    result = await get_funding_forecast(account_id=str(account_id))

    assert result["average_burn_rate_per_day"] == Decimal("0.00")
    assert result["days_remaining"] is None
    assert result["funding_required"] == Decimal("0.00")
    assert result["status"] == "NO_BURN"


@pytest.mark.asyncio
async def test_list_funding_forecasts(monkeypatch):
    account_id = uuid4()

    patch_db(
        monkeypatch,
        FakeConnection(
            account={
                "account_id": account_id,
                "tenant_code": "FNB",
                "account_name": "Main Rewards Funding",
                "account_type": "REWARD_POOL",
                "currency_code": "ZAR",
                "current_balance": Decimal("5000000.00"),
                "reserved_balance": Decimal("200000.00"),
                "available_balance": Decimal("4800000.00"),
                "status": "ACTIVE",
            },
            burn={"total_burn": Decimal("3600000.00")},
            accounts=[{"account_id": account_id}],
        ),
    )

    result = await list_funding_forecasts(tenant_code="FNB")

    assert len(result) == 1
    assert result[0]["account_id"] == str(account_id)
    assert result[0]["tenant_code"] == "FNB"


@pytest.mark.asyncio
async def test_get_sponsor_funding_forecast_returns_none_when_wallet_not_found(monkeypatch):
    patch_db(monkeypatch, FakeConnection(wallet=None))

    result = await get_sponsor_funding_forecast(
        tenant_code="FNB",
        sponsor_code="BOXER",
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_sponsor_funding_forecast_calculates_wallet_and_contract_runway(
    monkeypatch,
):
    wallet_id = uuid4()
    contract_id = uuid4()

    patch_db(
        monkeypatch,
        FakeConnection(
            wallet={
                "wallet_id": wallet_id,
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "sponsor_name": "Boxer",
                "currency": "ZAR",
                "current_balance": Decimal("1000000.00"),
                "reserved_balance": Decimal("100000.00"),
                "status": "ACTIVE",
            },
            wallet_burn={"total_burn": Decimal("300000.00")},
            contracts=[
                {
                    "contract_id": contract_id,
                    "contract_name": "Boxer June Contract",
                    "contract_value": Decimal("2000000.00"),
                    "committed_amount": Decimal("250000.00"),
                    "utilised_amount": Decimal("500000.00"),
                    "remaining_amount": Decimal("1250000.00"),
                    "start_date": None,
                    "end_date": None,
                    "status": "ACTIVE",
                }
            ],
            contract_burn=[
                {
                    "contract_id": contract_id,
                    "total_burn": Decimal("600000.00"),
                }
            ],
        ),
    )

    result = await get_sponsor_funding_forecast(
        tenant_code=" fnb ",
        sponsor_code=" boxer ",
        burn_window_days=30,
        buffer_days=45,
    )

    assert result["tenant_code"] == "FNB"
    assert result["sponsor_code"] == "BOXER"
    assert result["wallet"]["available_balance"] == Decimal("900000.00")
    assert result["wallet"]["average_burn_rate_per_day"] == Decimal("10000.00")
    assert result["wallet"]["days_remaining"] == Decimal("90.00")
    assert result["wallet"]["recommended_top_up"] == Decimal("0.00")
    assert result["contracts"]["count"] == 1
    assert result["contracts"]["average_burn_rate_per_day"] == Decimal("20000.00")
    assert result["contracts"]["days_remaining"] == Decimal("62.50")
    assert result["contracts"]["items"][0]["contract_id"] == str(contract_id)


@pytest.mark.asyncio
async def test_get_sponsor_funding_forecast_recommends_wallet_top_up(monkeypatch):
    wallet_id = uuid4()

    patch_db(
        monkeypatch,
        FakeConnection(
            wallet={
                "wallet_id": wallet_id,
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "sponsor_name": "Boxer",
                "currency": "ZAR",
                "current_balance": Decimal("100000.00"),
                "reserved_balance": Decimal("0.00"),
                "status": "ACTIVE",
            },
            wallet_burn={"total_burn": Decimal("300000.00")},
            contracts=[],
            contract_burn=[],
        ),
    )

    result = await get_sponsor_funding_forecast(
        tenant_code="FNB",
        sponsor_code="BOXER",
        burn_window_days=30,
        buffer_days=30,
    )

    assert result["wallet"]["average_burn_rate_per_day"] == Decimal("10000.00")
    assert result["wallet"]["target_buffer"] == Decimal("300000.00")
    assert result["wallet"]["recommended_top_up"] == Decimal("200000.00")
    assert result["wallet"]["forecast_status"] == "LOW"


@pytest.mark.asyncio
async def test_list_sponsor_funding_forecasts(monkeypatch):
    wallet_id = uuid4()

    patch_db(
        monkeypatch,
        FakeConnection(
            wallets=[{"tenant_code": "FNB", "sponsor_code": "BOXER"}],
            wallet={
                "wallet_id": wallet_id,
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "sponsor_name": "Boxer",
                "currency": "ZAR",
                "current_balance": Decimal("1000000.00"),
                "reserved_balance": Decimal("0.00"),
                "status": "ACTIVE",
            },
            wallet_burn={"total_burn": Decimal("0.00")},
            contracts=[],
            contract_burn=[],
        ),
    )

    result = await list_sponsor_funding_forecasts(tenant_code=" fnb ")

    assert len(result) == 1
    assert result[0]["tenant_code"] == "FNB"
    assert result[0]["sponsor_code"] == "BOXER"


@pytest.mark.asyncio
async def test_list_settlement_exposure_forecasts_projects_buffer_pressure(monkeypatch):
    patch_db(
        monkeypatch,
        FakeConnection(
            settlement_exposure=[
                {
                    "tenant_code": "FNB",
                    "provider_key": "CASH_PROVIDER",
                    "currency": "ZAR",
                    "open_settlement_count": 4,
                    "current_exposure_amount": Decimal("4000.00"),
                }
            ],
            settlement_burn=[
                {
                    "tenant_code": "FNB",
                    "provider_key": "CASH_PROVIDER",
                    "currency": "ZAR",
                    "settled_count": 10,
                    "settled_amount": Decimal("3000.00"),
                }
            ],
        ),
    )

    result = await list_settlement_exposure_forecasts(
        tenant_code=" fnb ",
        provider_key=" cash_provider ",
        currency=" zar ",
        burn_window_days=30,
        buffer_days=15,
    )

    assert len(result) == 1
    forecast = result[0]
    assert forecast["tenant_code"] == "FNB"
    assert forecast["provider_key"] == "CASH_PROVIDER"
    assert forecast["currency"] == "ZAR"
    assert forecast["open_settlement_count"] == 4
    assert forecast["current_exposure_amount"] == Decimal("4000.00")
    assert forecast["settled_amount"] == Decimal("3000.00")
    assert forecast["average_settlement_rate_per_day"] == Decimal("100.00")
    assert forecast["projected_settlement_amount"] == Decimal("1500.00")
    assert forecast["projected_total_exposure"] == Decimal("5500.00")
    assert forecast["forecast_status"] == "CRITICAL"


@pytest.mark.asyncio
async def test_list_settlement_exposure_forecasts_handles_no_burn(monkeypatch):
    patch_db(
        monkeypatch,
        FakeConnection(
            settlement_exposure=[
                {
                    "tenant_code": "FNB",
                    "provider_key": "VOUCHER_PROVIDER",
                    "currency": "ZAR",
                    "open_settlement_count": 1,
                    "current_exposure_amount": Decimal("250.00"),
                }
            ],
            settlement_burn=[],
        ),
    )

    result = await list_settlement_exposure_forecasts()

    assert result[0]["settled_count"] == 0
    assert result[0]["average_settlement_rate_per_day"] == Decimal("0.00")
    assert result[0]["projected_total_exposure"] == Decimal("250.00")
