from __future__ import annotations

from uuid import uuid4

import pytest

from services.funding.account_rules import (
    _row_to_dict,
    create_funding_account_rule,
    get_funding_account_rule,
    list_funding_account_rules,
    update_funding_account_rule,
)
from services.funding_service import create_funding_account

pytestmark = pytest.mark.asyncio


def unique_tenant_code(prefix: str = "TENANT") -> str:
    return f"{prefix}_{uuid4().hex[:8].upper()}"


async def create_test_account(*, tenant_code: str):
    return await create_funding_account(
        tenant_code=tenant_code,
        account_name=f"{tenant_code} Wallet",
        account_type="TENANT_WALLET",
        opening_balance="1000.00",
    )


def test_row_to_dict_none():
    assert _row_to_dict(None) is None


async def test_create_and_get_funding_account_rule():
    tenant_code = unique_tenant_code("FNB")
    account = await create_test_account(tenant_code=tenant_code)

    created = await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=account["account_id"],
        reward_type="REFERRAL",
        segment_code="PERSONAL",
        campaign_code="BURGER_FRIDAY",
        sponsor_code="FNB",
        priority=10,
    )

    assert created["tenant_code"] == tenant_code
    assert created["account_id"] == account["account_id"]
    assert created["reward_type"] == "REFERRAL"
    assert created["segment_code"] == "PERSONAL"
    assert created["campaign_code"] == "BURGER_FRIDAY"
    assert created["sponsor_code"] == "FNB"
    assert created["priority"] == 10
    assert created["is_active"] is True

    fetched = await get_funding_account_rule(rule_id=created["rule_id"])

    assert fetched is not None
    assert fetched["rule_id"] == created["rule_id"]


async def test_get_missing_funding_account_rule_returns_none():
    fetched = await get_funding_account_rule(rule_id=uuid4())

    assert fetched is None


async def test_update_funding_account_rule():
    tenant_code = unique_tenant_code("FNB")
    account = await create_test_account(tenant_code=tenant_code)

    created = await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=account["account_id"],
        reward_type="REFERRAL",
        priority=100,
    )

    updated = await update_funding_account_rule(
        rule_id=created["rule_id"],
        reward_type="CAMPAIGN",
        segment_code="PRIVATE",
        campaign_code="BLACK_FRIDAY",
        sponsor_code="PNP",
        priority=5,
        is_active=False,
    )

    assert updated is not None
    assert updated["reward_type"] == "CAMPAIGN"
    assert updated["segment_code"] == "PRIVATE"
    assert updated["campaign_code"] == "BLACK_FRIDAY"
    assert updated["sponsor_code"] == "PNP"
    assert updated["priority"] == 5
    assert updated["is_active"] is False


async def test_update_missing_funding_account_rule_returns_none():
    updated = await update_funding_account_rule(
        rule_id=uuid4(),
        reward_type="MISSING",
    )

    assert updated is None


async def test_list_funding_account_rules_active_only():
    tenant_code = unique_tenant_code("FNB")
    account = await create_test_account(tenant_code=tenant_code)

    active = await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=account["account_id"],
        reward_type="ACTIVE",
        priority=10,
    )

    inactive = await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=account["account_id"],
        reward_type="INACTIVE",
        priority=5,
    )

    await update_funding_account_rule(
        rule_id=inactive["rule_id"],
        is_active=False,
    )

    rows = await list_funding_account_rules(
        tenant_code=tenant_code,
        active_only=True,
    )

    rule_ids = {row["rule_id"] for row in rows}

    assert active["rule_id"] in rule_ids
    assert inactive["rule_id"] not in rule_ids


async def test_list_funding_account_rules_including_inactive():
    tenant_code = unique_tenant_code("FNB")
    account = await create_test_account(tenant_code=tenant_code)

    active = await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=account["account_id"],
        reward_type="ACTIVE",
        priority=10,
    )

    inactive = await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=account["account_id"],
        reward_type="INACTIVE",
        priority=5,
    )

    await update_funding_account_rule(
        rule_id=inactive["rule_id"],
        is_active=False,
    )

    rows = await list_funding_account_rules(
        tenant_code=tenant_code,
        active_only=False,
    )

    rule_ids = {row["rule_id"] for row in rows}

    assert active["rule_id"] in rule_ids
    assert inactive["rule_id"] in rule_ids


async def test_list_funding_account_rules_by_account_id():
    tenant_code = unique_tenant_code("FNB")
    account = await create_test_account(tenant_code=tenant_code)

    created = await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=account["account_id"],
        reward_type="REFERRAL",
    )

    rows = await list_funding_account_rules(
        tenant_code=tenant_code,
        account_id=account["account_id"],
    )

    assert any(row["rule_id"] == created["rule_id"] for row in rows)