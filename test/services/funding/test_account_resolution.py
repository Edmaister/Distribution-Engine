from __future__ import annotations

from uuid import uuid4

import pytest

from services.funding.account_resolution import (
    _serialize_row,
    list_matching_funding_rules,
    resolve_funding_account,
)
from services.funding.account_rules import (
    create_funding_account_rule,
    update_funding_account_rule,
)
from services.funding_service import create_funding_account

pytestmark = pytest.mark.asyncio


def unique_tenant_code(prefix: str = "TENANT") -> str:
    return f"{prefix}_{uuid4().hex[:8].upper()}"


async def create_test_account(
    *,
    tenant_code: str,
    account_name: str,
    account_type: str = "TENANT_WALLET",
    opening_balance: str = "1000.00",
):
    return await create_funding_account(
        tenant_code=tenant_code,
        account_name=account_name,
        account_type=account_type,
        opening_balance=opening_balance,
    )


def test_row_to_dict_none():
    assert _serialize_row(None) is None


async def test_resolve_returns_none_when_no_rule_exists():
    result = await resolve_funding_account(
        tenant_code=unique_tenant_code("NO_RULE"),
        reward_type="REFERRAL",
    )

    assert result is None


async def test_resolve_default_rule():
    tenant_code = unique_tenant_code("DEFAULT")
    account = await create_test_account(
        tenant_code=tenant_code,
        account_name="Default Wallet",
    )

    await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=account["account_id"],
        priority=100,
    )

    result = await resolve_funding_account(
        tenant_code=tenant_code,
        reward_type="REFERRAL",
    )

    assert result is not None
    assert str(result["account_id"]) == str(account["account_id"])
    assert result["account_name"] == "Default Wallet"
    assert result["match_strength"] == 0


async def test_segment_rule_beats_default_when_priority_is_better():
    tenant_code = unique_tenant_code("SEGMENT")

    default_account = await create_test_account(
        tenant_code=tenant_code,
        account_name="Default Wallet",
    )
    segment_account = await create_test_account(
        tenant_code=tenant_code,
        account_name="Personal Segment Wallet",
        account_type="SEGMENT_WALLET",
    )

    await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=default_account["account_id"],
        priority=100,
    )

    await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=segment_account["account_id"],
        segment_code="PERSONAL",
        priority=10,
    )

    result = await resolve_funding_account(
        tenant_code=tenant_code,
        segment_code="PERSONAL",
    )

    assert result is not None
    assert str(result["account_id"]) == str(segment_account["account_id"])
    assert result["account_type"] == "SEGMENT_WALLET"
    assert result["match_strength"] == 1


async def test_campaign_rule_beats_segment_when_priority_is_better():
    tenant_code = unique_tenant_code("CAMPAIGN")

    segment_account = await create_test_account(
        tenant_code=tenant_code,
        account_name="Personal Segment Wallet",
        account_type="SEGMENT_WALLET",
    )
    campaign_account = await create_test_account(
        tenant_code=tenant_code,
        account_name="Burger Friday Wallet",
        account_type="CAMPAIGN_WALLET",
    )

    await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=segment_account["account_id"],
        segment_code="PERSONAL",
        priority=50,
    )

    await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=campaign_account["account_id"],
        segment_code="PERSONAL",
        campaign_code="BURGER_FRIDAY",
        priority=5,
    )

    result = await resolve_funding_account(
        tenant_code=tenant_code,
        segment_code="PERSONAL",
        campaign_code="BURGER_FRIDAY",
    )

    assert result is not None
    assert str(result["account_id"]) == str(campaign_account["account_id"])
    assert result["account_type"] == "CAMPAIGN_WALLET"
    assert result["match_strength"] == 2


async def test_sponsor_rule_beats_campaign_when_priority_is_better():
    tenant_code = unique_tenant_code("SPONSOR")

    campaign_account = await create_test_account(
        tenant_code=tenant_code,
        account_name="Burger Friday Wallet",
        account_type="CAMPAIGN_WALLET",
    )
    sponsor_account = await create_test_account(
        tenant_code=tenant_code,
        account_name="Pick n Pay Sponsor Wallet",
        account_type="SPONSOR_WALLET",
    )

    await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=campaign_account["account_id"],
        campaign_code="BURGER_FRIDAY",
        priority=50,
    )

    await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=sponsor_account["account_id"],
        campaign_code="BURGER_FRIDAY",
        sponsor_code="PNP",
        priority=1,
    )

    result = await resolve_funding_account(
        tenant_code=tenant_code,
        campaign_code="BURGER_FRIDAY",
        sponsor_code="PNP",
    )

    assert result is not None
    assert str(result["account_id"]) == str(sponsor_account["account_id"])
    assert result["account_type"] == "SPONSOR_WALLET"
    assert result["match_strength"] == 2


async def test_inactive_rule_is_ignored():
    tenant_code = unique_tenant_code("INACTIVE")

    account = await create_test_account(
        tenant_code=tenant_code,
        account_name="Inactive Rule Wallet",
    )

    rule = await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=account["account_id"],
        reward_type="REFERRAL",
        priority=1,
    )

    await update_funding_account_rule(
        rule_id=rule["rule_id"],
        is_active=False,
    )

    result = await resolve_funding_account(
        tenant_code=tenant_code,
        reward_type="REFERRAL",
    )

    assert result is None


async def test_priority_ordering_is_honoured_before_match_strength():
    tenant_code = unique_tenant_code("PRIORITY")

    high_priority_account = await create_test_account(
        tenant_code=tenant_code,
        account_name="High Priority Default Wallet",
    )
    lower_priority_specific_account = await create_test_account(
        tenant_code=tenant_code,
        account_name="Lower Priority Specific Wallet",
    )

    await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=high_priority_account["account_id"],
        priority=1,
    )

    await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=lower_priority_specific_account["account_id"],
        reward_type="REFERRAL",
        segment_code="PERSONAL",
        campaign_code="BURGER_FRIDAY",
        priority=10,
    )

    result = await resolve_funding_account(
        tenant_code=tenant_code,
        reward_type="REFERRAL",
        segment_code="PERSONAL",
        campaign_code="BURGER_FRIDAY",
    )

    assert result is not None
    assert str(result["account_id"]) == str(high_priority_account["account_id"])
    assert result["match_strength"] == 0


async def test_list_matching_funding_rules_respects_limit():
    tenant_code = unique_tenant_code("LIMIT")
    account_one = await create_test_account(
        tenant_code=tenant_code,
        account_name="Wallet One",
    )
    account_two = await create_test_account(
        tenant_code=tenant_code,
        account_name="Wallet Two",
    )

    await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=account_one["account_id"],
        priority=1,
    )

    await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=account_two["account_id"],
        priority=2,
    )

    rows = await list_matching_funding_rules(
        tenant_code=tenant_code,
        limit=1,
    )

    assert len(rows) == 1
    assert str(rows[0]["account_id"]) == str(account_one["account_id"])