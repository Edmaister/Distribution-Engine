from __future__ import annotations

from decimal import Decimal

import pytest

from services.funding_service import (
    FundingAccountNotFound,
    InsufficientAvailableBalance,
    InvalidFundingAmount,
    create_funding_account,
    credit_account,
    debit_account,
    get_account_balance,
    get_funding_account,
    list_funding_accounts,
    list_funding_transactions,
    release_reserved_funds,
    reserve_funds,
    settle_reserved_funds,
)


pytestmark = pytest.mark.asyncio


async def test_create_funding_account():
    account = await create_funding_account(
        tenant_code="FNB",
        account_name="FNB Tenant Wallet",
        account_type="TENANT_WALLET",
        opening_balance=Decimal("1000.00"),
    )

    assert account["tenant_code"] == "FNB"
    assert account["account_name"] == "FNB Tenant Wallet"
    assert account["account_type"] == "TENANT_WALLET"
    assert account["currency_code"] == "ZAR"
    assert account["current_balance"] == Decimal("1000.00")
    assert account["reserved_balance"] == Decimal("0.00")
    assert account["available_balance"] == Decimal("1000.00")
    assert account["status"] == "ACTIVE"


async def test_get_funding_account():
    created = await create_funding_account(
        tenant_code="FNB",
        account_name="Lookup Wallet",
        account_type="TENANT_WALLET",
        opening_balance="500.00",
    )

    account = await get_funding_account(account_id=created["account_id"])

    assert account is not None
    assert account["account_id"] == created["account_id"]
    assert account["current_balance"] == Decimal("500.00")


async def test_list_funding_accounts():
    await create_funding_account(
        tenant_code="FNB",
        account_name="List Wallet",
        account_type="TENANT_WALLET",
        opening_balance="250.00",
    )

    accounts = await list_funding_accounts(tenant_code="FNB")

    assert len(accounts) >= 1
    assert any(account["account_name"] == "List Wallet" for account in accounts)


async def test_credit_account():
    account = await create_funding_account(
        tenant_code="FNB",
        account_name="Credit Wallet",
        account_type="TENANT_WALLET",
        opening_balance="100.00",
    )

    result = await credit_account(
        account_id=account["account_id"],
        amount="50.00",
        reference_id="TOPUP-001",
        correlation_id="CORR-001",
    )

    updated = result["account"]
    tx = result["transaction"]

    assert updated["current_balance"] == Decimal("150.00")
    assert updated["available_balance"] == Decimal("150.00")
    assert updated["reserved_balance"] == Decimal("0.00")

    assert tx["transaction_type"] == "CREDIT"
    assert tx["amount"] == Decimal("50.00")
    assert tx["reference_id"] == "TOPUP-001"
    assert tx["correlation_id"] == "CORR-001"


async def test_debit_account():
    account = await create_funding_account(
        tenant_code="FNB",
        account_name="Debit Wallet",
        account_type="TENANT_WALLET",
        opening_balance="300.00",
    )

    result = await debit_account(
        account_id=account["account_id"],
        amount="75.00",
        reference_id="DEBIT-001",
    )

    updated = result["account"]
    tx = result["transaction"]

    assert updated["current_balance"] == Decimal("225.00")
    assert updated["available_balance"] == Decimal("225.00")
    assert tx["transaction_type"] == "DEBIT"
    assert tx["amount"] == Decimal("75.00")


async def test_debit_account_insufficient_balance():
    account = await create_funding_account(
        tenant_code="FNB",
        account_name="Low Balance Wallet",
        account_type="TENANT_WALLET",
        opening_balance="20.00",
    )

    with pytest.raises(InsufficientAvailableBalance):
        await debit_account(
            account_id=account["account_id"],
            amount="25.00",
        )


async def test_reserve_funds():
    account = await create_funding_account(
        tenant_code="FNB",
        account_name="Reserve Wallet",
        account_type="TENANT_WALLET",
        opening_balance="1000.00",
    )

    result = await reserve_funds(
        account_id=account["account_id"],
        amount="200.00",
        reference_id="REWARD-001",
    )

    updated = result["account"]
    tx = result["transaction"]

    assert updated["current_balance"] == Decimal("1000.00")
    assert updated["reserved_balance"] == Decimal("200.00")
    assert updated["available_balance"] == Decimal("800.00")

    assert tx["transaction_type"] == "RESERVE"
    assert tx["amount"] == Decimal("200.00")


async def test_reserve_funds_insufficient_available_balance():
    account = await create_funding_account(
        tenant_code="FNB",
        account_name="Reserve Fail Wallet",
        account_type="TENANT_WALLET",
        opening_balance="100.00",
    )

    with pytest.raises(InsufficientAvailableBalance):
        await reserve_funds(
            account_id=account["account_id"],
            amount="150.00",
        )


async def test_release_reserved_funds():
    account = await create_funding_account(
        tenant_code="FNB",
        account_name="Release Wallet",
        account_type="TENANT_WALLET",
        opening_balance="500.00",
    )

    await reserve_funds(
        account_id=account["account_id"],
        amount="200.00",
    )

    result = await release_reserved_funds(
        account_id=account["account_id"],
        amount="80.00",
        reference_id="RELEASE-001",
    )

    updated = result["account"]
    tx = result["transaction"]

    assert updated["current_balance"] == Decimal("500.00")
    assert updated["reserved_balance"] == Decimal("120.00")
    assert updated["available_balance"] == Decimal("380.00")

    assert tx["transaction_type"] == "RELEASE"
    assert tx["amount"] == Decimal("80.00")


async def test_release_reserved_funds_insufficient_reserved_balance():
    account = await create_funding_account(
        tenant_code="FNB",
        account_name="Release Fail Wallet",
        account_type="TENANT_WALLET",
        opening_balance="500.00",
    )

    await reserve_funds(
        account_id=account["account_id"],
        amount="50.00",
    )

    with pytest.raises(InsufficientAvailableBalance):
        await release_reserved_funds(
            account_id=account["account_id"],
            amount="75.00",
        )


async def test_settle_reserved_funds():
    account = await create_funding_account(
        tenant_code="FNB",
        account_name="Settlement Wallet",
        account_type="TENANT_WALLET",
        opening_balance="1000.00",
    )

    await reserve_funds(
        account_id=account["account_id"],
        amount="300.00",
        reference_id="REWARD-SETTLE-001",
    )

    result = await settle_reserved_funds(
        account_id=account["account_id"],
        amount="300.00",
        reference_id="REWARD-SETTLE-001",
    )

    updated = result["account"]
    tx = result["transaction"]

    assert updated["current_balance"] == Decimal("700.00")
    assert updated["reserved_balance"] == Decimal("0.00")
    assert updated["available_balance"] == Decimal("700.00")

    assert tx["transaction_type"] == "SETTLEMENT"
    assert tx["amount"] == Decimal("300.00")


async def test_settle_reserved_funds_insufficient_reserved_balance():
    account = await create_funding_account(
        tenant_code="FNB",
        account_name="Settlement Fail Wallet",
        account_type="TENANT_WALLET",
        opening_balance="1000.00",
    )

    await reserve_funds(
        account_id=account["account_id"],
        amount="100.00",
    )

    with pytest.raises(InsufficientAvailableBalance):
        await settle_reserved_funds(
            account_id=account["account_id"],
            amount="150.00",
        )


async def test_get_account_balance():
    account = await create_funding_account(
        tenant_code="FNB",
        account_name="Balance Wallet",
        account_type="TENANT_WALLET",
        opening_balance="900.00",
    )

    await reserve_funds(
        account_id=account["account_id"],
        amount="250.00",
    )

    balance = await get_account_balance(account_id=account["account_id"])

    assert balance["current_balance"] == Decimal("900.00")
    assert balance["reserved_balance"] == Decimal("250.00")
    assert balance["available_balance"] == Decimal("650.00")


async def test_list_funding_transactions():
    account = await create_funding_account(
        tenant_code="FNB",
        account_name="Transaction Wallet",
        account_type="TENANT_WALLET",
        opening_balance="100.00",
    )

    await credit_account(
        account_id=account["account_id"],
        amount="50.00",
        correlation_id="CORR-LIST-001",
    )

    transactions = await list_funding_transactions(
        account_id=account["account_id"],
        transaction_type="CREDIT",
    )

    assert len(transactions) >= 1
    assert transactions[0]["transaction_type"] == "CREDIT"


async def test_invalid_zero_amount():
    account = await create_funding_account(
        tenant_code="FNB",
        account_name="Invalid Amount Wallet",
        account_type="TENANT_WALLET",
        opening_balance="100.00",
    )

    with pytest.raises(InvalidFundingAmount):
        await credit_account(
            account_id=account["account_id"],
            amount="0.00",
        )


async def test_invalid_negative_amount():
    account = await create_funding_account(
        tenant_code="FNB",
        account_name="Negative Amount Wallet",
        account_type="TENANT_WALLET",
        opening_balance="100.00",
    )

    with pytest.raises(InvalidFundingAmount):
        await debit_account(
            account_id=account["account_id"],
            amount="-10.00",
        )


async def test_create_account_negative_opening_balance():
    with pytest.raises(InvalidFundingAmount):
        await create_funding_account(
            tenant_code="FNB",
            account_name="Bad Opening Wallet",
            account_type="TENANT_WALLET",
            opening_balance="-1.00",
        )


async def test_get_missing_account_returns_none():
    account = await get_funding_account(
        account_id="00000000-0000-0000-0000-000000000000",
    )

    assert account is None


async def test_get_balance_missing_account_raises():
    with pytest.raises(FundingAccountNotFound):
        await get_account_balance(
            account_id="00000000-0000-0000-0000-000000000000",
        )

async def test_credit_missing_account_raises():
    with pytest.raises(FundingAccountNotFound):
        await credit_account(
            account_id="00000000-0000-0000-0000-000000000000",
            amount="10.00",
        )


async def test_debit_missing_account_raises():
    with pytest.raises(FundingAccountNotFound):
        await debit_account(
            account_id="00000000-0000-0000-0000-000000000000",
            amount="10.00",
        )


async def test_reserve_missing_account_raises():
    with pytest.raises(FundingAccountNotFound):
        await reserve_funds(
            account_id="00000000-0000-0000-0000-000000000000",
            amount="10.00",
        )


async def test_release_missing_account_raises():
    with pytest.raises(FundingAccountNotFound):
        await release_reserved_funds(
            account_id="00000000-0000-0000-0000-000000000000",
            amount="10.00",
        )


async def test_settle_missing_account_raises():
    with pytest.raises(FundingAccountNotFound):
        await settle_reserved_funds(
            account_id="00000000-0000-0000-0000-000000000000",
            amount="10.00",
        )