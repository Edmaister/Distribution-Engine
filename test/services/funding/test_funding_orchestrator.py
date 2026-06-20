from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from services.funding.orchestrator import (
    NoActiveFundingAccount,
    has_reward_reservation,
    release_reward_funding,
    reserve_reward_funding,
    settle_reward_funding,
)
from services.funding.reservations import get_funding_reservation_by_reward
from services.funding.limits import create_funding_limit
from services.funding_service import (
    FundingAccountNotFound,
    InsufficientAvailableBalance,
    create_funding_account,
    get_account_balance,
)
from services.funding.account_rules import create_funding_account_rule

pytestmark = pytest.mark.asyncio


def unique_reward_id(prefix: str = "REWARD") -> str:
    return f"{prefix}-{uuid4()}"


def unique_tenant_code(prefix: str = "TENANT") -> str:
    return f"{prefix}_{uuid4().hex[:8].upper()}"


async def create_wallet_with_limit(
    *,
    tenant_code: str,
    account_name: str,
    account_type: str = "TENANT_WALLET",
    opening_balance: str = "1000.00",
    daily_limit: Decimal = Decimal("10000.00"),
    monthly_limit: Decimal = Decimal("100000.00"),
    exposure_limit: Decimal = Decimal("1000000.00"),
    create_default_rule: bool = True,
):
    account = await create_funding_account(
        tenant_code=tenant_code,
        account_name=account_name,
        account_type=account_type,
        opening_balance=opening_balance,
    )

    await create_funding_limit(
        tenant_code=tenant_code,
        account_id=account["account_id"],
        daily_limit=daily_limit,
        monthly_limit=monthly_limit,
        exposure_limit=exposure_limit,
    )

    if create_default_rule:
        await create_funding_account_rule(
            tenant_code=tenant_code,
            account_id=account["account_id"],
            priority=100,
        )

    return account


async def test_reserve_reward_funding():
    tenant_code = unique_tenant_code("FNB")
    reward_id = unique_reward_id("REWARD")

    account = await create_wallet_with_limit(
        tenant_code=tenant_code,
        account_name="FNB Tenant Wallet",
    )

    result = await reserve_reward_funding(
        reward_id=reward_id,
        tenant_code=tenant_code,
        amount="100.00",
        correlation_id=f"CORR-{uuid4()}",
    )

    assert result["reserved"] is True
    assert result["reservation"]["reward_id"] == reward_id
    assert result["reservation"]["status"] == "RESERVED"
    assert result["funding_transaction"]["transaction_type"] == "RESERVE"
    assert result["already_reserved"] is False
    assert str(result["funding_account"]["account_id"]) == str(account["account_id"])

    balance = await get_account_balance(account_id=account["account_id"])

    assert balance["current_balance"] == Decimal("1000.00")
    assert balance["reserved_balance"] == Decimal("100.00")
    assert balance["available_balance"] == Decimal("900.00")


async def test_reserve_reward_funding_duplicate_reward_returns_existing():
    tenant_code = unique_tenant_code("FNB")
    reward_id = unique_reward_id("REWARD-DUP")

    await create_wallet_with_limit(
        tenant_code=tenant_code,
        account_name="FNB Duplicate Wallet",
    )

    first = await reserve_reward_funding(
        reward_id=reward_id,
        tenant_code=tenant_code,
        amount="100.00",
    )

    second = await reserve_reward_funding(
        reward_id=reward_id,
        tenant_code=tenant_code,
        amount="100.00",
    )

    assert first["reservation"]["reservation_id"] == second["reservation"]["reservation_id"]
    assert second["reserved"] is True
    assert second["already_reserved"] is True


async def test_reserve_reward_funding_no_active_wallet_raises():
    tenant_code = unique_tenant_code("NO_WALLET")

    with pytest.raises(NoActiveFundingAccount):
        await reserve_reward_funding(
            reward_id=unique_reward_id("REWARD-NO-WALLET"),
            tenant_code=tenant_code,
            amount="100.00",
        )


async def test_reserve_reward_funding_insufficient_balance_raises():
    tenant_code = unique_tenant_code("LOW_BALANCE")

    await create_wallet_with_limit(
        tenant_code=tenant_code,
        account_name="Low Balance Wallet",
        opening_balance="50.00",
    )

    with pytest.raises(InsufficientAvailableBalance):
        await reserve_reward_funding(
            reward_id=unique_reward_id("REWARD-LOW"),
            tenant_code=tenant_code,
            amount="100.00",
        )


async def test_reserve_reward_funding_rejects_without_active_limit():
    tenant_code = unique_tenant_code("NO_LIMIT")
    reward_id = unique_reward_id("REWARD-NO-LIMIT")

    account = await create_funding_account(
        tenant_code=tenant_code,
        account_name="Wallet Without Limit",
        account_type="TENANT_WALLET",
        opening_balance="1000.00",
    )

    await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=account["account_id"],
        priority=100,
    )

    result = await reserve_reward_funding(
        reward_id=reward_id,
        tenant_code=tenant_code,
        amount="100.00",
    )

    assert result["reserved"] is False
    assert result["reservation"] is None
    assert result["funding_transaction"] is None
    assert result["already_reserved"] is False
    assert result["rejected"] is True
    assert result["reason"] == "NO_ACTIVE_LIMIT"


async def test_reserve_reward_funding_routes_using_direct_sponsor_code():
    tenant_code = unique_tenant_code("SPONSOR")
    reward_id = unique_reward_id("REWARD-SPONSOR")

    default_account = await create_wallet_with_limit(
        tenant_code=tenant_code,
        account_name="Default Tenant Wallet",
        account_type="TENANT_WALLET",
    )

    sponsor_account = await create_wallet_with_limit(
        tenant_code=tenant_code,
        account_name="Pick n Pay Sponsor Wallet",
        account_type="SPONSOR_WALLET",
        create_default_rule=False,
    )

    await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=sponsor_account["account_id"],
        sponsor_code="PNP",
        priority=1,
    )

    result = await reserve_reward_funding(
        reward_id=reward_id,
        tenant_code=tenant_code,
        amount="100.00",
        sponsor_code="PNP",
    )

    assert result["reserved"] is True
    assert str(result["funding_account"]["account_id"]) == str(sponsor_account["account_id"])
    assert result["funding_account"]["account_type"] == "SPONSOR_WALLET"

    sponsor_balance = await get_account_balance(account_id=sponsor_account["account_id"])
    default_balance = await get_account_balance(account_id=default_account["account_id"])

    assert sponsor_balance["reserved_balance"] == Decimal("100.00")
    assert default_balance["reserved_balance"] == Decimal("0.00")


async def test_reserve_reward_funding_routes_using_metadata_sponsor_code():
    tenant_code = unique_tenant_code("META_SPONSOR")
    reward_id = unique_reward_id("REWARD-META-SPONSOR")

    sponsor_account = await create_wallet_with_limit(
        tenant_code=tenant_code,
        account_name="MTN Sponsor Wallet",
        account_type="SPONSOR_WALLET",
        create_default_rule=False,
    )

    await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=sponsor_account["account_id"],
        sponsor_code="MTN",
        priority=1,
    )

    result = await reserve_reward_funding(
        reward_id=reward_id,
        tenant_code=tenant_code,
        amount="100.00",
        metadata={
            "sponsor_code": "MTN",
            "source": "test",
        },
    )

    assert result["reserved"] is True
    assert str(result["funding_account"]["account_id"]) == str(sponsor_account["account_id"])
    metadata = str(result["funding_transaction"]["metadata"])
    
    assert "MTN" in metadata
    assert "test" in metadata


async def test_reserve_reward_funding_direct_argument_overrides_metadata():
    tenant_code = unique_tenant_code("OVERRIDE")
    reward_id = unique_reward_id("REWARD-OVERRIDE")

    metadata_sponsor_account = await create_wallet_with_limit(
        tenant_code=tenant_code,
        account_name="Metadata Sponsor Wallet",
        account_type="SPONSOR_WALLET",
        create_default_rule=False,
    )

    direct_sponsor_account = await create_wallet_with_limit(
        tenant_code=tenant_code,
        account_name="Direct Sponsor Wallet",
        account_type="SPONSOR_WALLET",
        create_default_rule=False,
    )

    await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=metadata_sponsor_account["account_id"],
        sponsor_code="META",
        priority=1,
    )

    await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=direct_sponsor_account["account_id"],
        sponsor_code="DIRECT",
        priority=1,
    )

    result = await reserve_reward_funding(
        reward_id=reward_id,
        tenant_code=tenant_code,
        amount="100.00",
        sponsor_code="DIRECT",
        metadata={
            "sponsor_code": "META",
        },
    )

    assert result["reserved"] is True
    assert str(result["funding_account"]["account_id"]) == str(direct_sponsor_account["account_id"])
    metadata = str(result["funding_transaction"]["metadata"])

    assert "DIRECT" in metadata


async def test_release_reward_funding():
    tenant_code = unique_tenant_code("FNB")
    reward_id = unique_reward_id("REWARD-REL")

    account = await create_wallet_with_limit(
        tenant_code=tenant_code,
        account_name="Release Tenant Wallet",
    )

    await reserve_reward_funding(
        reward_id=reward_id,
        tenant_code=tenant_code,
        amount="250.00",
    )

    result = await release_reward_funding(
        reward_id=reward_id,
        correlation_id=f"CORR-REL-{uuid4()}",
    )

    assert result["released"] is True
    assert result["reservation"]["status"] == "RELEASED"
    assert result["funding_transaction"]["transaction_type"] == "RELEASE"

    balance = await get_account_balance(account_id=account["account_id"])

    assert balance["current_balance"] == Decimal("1000.00")
    assert balance["reserved_balance"] == Decimal("0.00")
    assert balance["available_balance"] == Decimal("1000.00")


async def test_settle_reward_funding():
    tenant_code = unique_tenant_code("FNB")
    reward_id = unique_reward_id("REWARD-SET")

    account = await create_wallet_with_limit(
        tenant_code=tenant_code,
        account_name="Settlement Tenant Wallet",
    )

    await reserve_reward_funding(
        reward_id=reward_id,
        tenant_code=tenant_code,
        amount="300.00",
    )

    result = await settle_reward_funding(
        reward_id=reward_id,
        correlation_id=f"CORR-SET-{uuid4()}",
    )

    assert result["settled"] is True
    assert result["reservation"]["status"] == "SETTLED"
    assert result["funding_transaction"]["transaction_type"] == "SETTLEMENT"

    balance = await get_account_balance(account_id=account["account_id"])

    assert balance["current_balance"] == Decimal("700.00")
    assert balance["reserved_balance"] == Decimal("0.00")
    assert balance["available_balance"] == Decimal("700.00")


async def test_release_missing_reward_reservation_raises():
    with pytest.raises(FundingAccountNotFound):
        await release_reward_funding(
            reward_id=unique_reward_id("REWARD-MISSING-REL"),
        )


async def test_settle_missing_reward_reservation_raises():
    with pytest.raises(FundingAccountNotFound):
        await settle_reward_funding(
            reward_id=unique_reward_id("REWARD-MISSING-SET"),
        )


async def test_get_reservation_by_reward_after_reserve():
    tenant_code = unique_tenant_code("FNB")
    reward_id = unique_reward_id("REWARD-LOOKUP")

    await create_wallet_with_limit(
        tenant_code=tenant_code,
        account_name="Lookup Reservation Wallet",
    )

    await reserve_reward_funding(
        reward_id=reward_id,
        tenant_code=tenant_code,
        amount="75.00",
    )

    reservation = await get_funding_reservation_by_reward(
        reward_id=reward_id,
    )

    assert reservation is not None
    assert reservation["reward_id"] == reward_id
    assert reservation["status"] == "RESERVED"


async def test_has_reward_reservation_returns_false_when_missing():
    exists = await has_reward_reservation(
        reward_id=unique_reward_id("REWARD-MISSING-HAS"),
    )

    assert exists is False


async def test_reserve_reward_funding_without_funding_rule_raises():
    tenant_code = unique_tenant_code("NO_RULE")

    await create_funding_account(
        tenant_code=tenant_code,
        account_name="Wallet Without Rule",
        account_type="TENANT_WALLET",
        opening_balance="1000.00",
    )

    with pytest.raises(NoActiveFundingAccount):
        await reserve_reward_funding(
            reward_id=unique_reward_id("REWARD-NO-RULE"),
            tenant_code=tenant_code,
            amount="100.00",
        )