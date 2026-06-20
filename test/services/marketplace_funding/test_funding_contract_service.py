from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from services.marketplace_funding.funding_contract_service import (
    FundingContractExceeded,
    FundingContractInactive,
    FundingContractNotFound,
    activate_funding_contract,
    cancel_funding_contract,
    commit_funding_contract_budget,
    create_funding_contract,
    get_funding_contract,
    get_funding_contract_ledger,
    list_funding_contracts,
    release_funding_contract_budget,
    resolve_active_funding_contract,
    suspend_funding_contract,
    utilise_funding_contract_budget,
)


pytestmark = pytest.mark.asyncio


def unique_code(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


async def test_create_and_get_funding_contract_service():
    sponsor_code = unique_code("BOXER")

    created = await create_funding_contract(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
        sponsor_name="Boxer",
        contract_name="FY27 Boxer Acquisition",
        contract_value="1000000.00",
        start_date=date(2026, 1, 1),
        end_date=date(2027, 12, 31),
        currency="ZAR",
        metadata={"source": "service-test"},
    )

    assert created["tenant_code"] == "FNB"
    assert created["sponsor_code"] == sponsor_code
    assert created["contract_value"] == 1000000.00 or str(created["contract_value"]) == "1000000.00"
    assert created["remaining_amount"] == 1000000.00 or str(created["remaining_amount"]) == "1000000.00"

    fetched = await get_funding_contract(contract_id=created["contract_id"])

    assert fetched["contract_id"] == created["contract_id"]
    assert fetched["sponsor_code"] == sponsor_code


async def test_list_and_resolve_active_funding_contract_service():
    sponsor_code = unique_code("MTN")

    created = await create_funding_contract(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
        sponsor_name="MTN",
        contract_name="MTN Airtime Rewards",
        contract_value="500000.00",
        start_date=date(2026, 1, 1),
        end_date=date(2027, 12, 31),
    )

    contracts = await list_funding_contracts(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
    )

    assert any(item["contract_id"] == created["contract_id"] for item in contracts)

    active = await resolve_active_funding_contract(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
        as_of_date=date(2026, 6, 1),
    )

    assert active["contract_id"] == created["contract_id"]
    assert active["status"] == "ACTIVE"


async def test_commit_release_and_utilise_contract_budget_service():
    sponsor_code = unique_code("SHOPRITE")

    created = await create_funding_contract(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
        sponsor_name="Shoprite",
        contract_name="Shoprite Grocery Rewards",
        contract_value="1000.00",
        start_date=date(2026, 1, 1),
        end_date=date(2027, 12, 31),
    )

    contract_id = created["contract_id"]

    committed = await commit_funding_contract_budget(
        contract_id=contract_id,
        amount="300.00",
        reward_id=str(uuid4()),
        allocation_id=str(uuid4()),
        correlation_id="corr-service-commit",
        metadata={"step": "commit"},
    )

    assert str(committed["committed_amount"]) == "300.00"
    assert str(committed["remaining_amount"]) == "700.00"

    released = await release_funding_contract_budget(
        contract_id=contract_id,
        amount="100.00",
        correlation_id="corr-service-release",
    )

    assert str(released["committed_amount"]) == "200.00"
    assert str(released["remaining_amount"]) == "800.00"

    utilised = await utilise_funding_contract_budget(
        contract_id=contract_id,
        amount="200.00",
        correlation_id="corr-service-utilise",
    )

    assert str(utilised["committed_amount"]) == "0.00"
    assert str(utilised["utilised_amount"]) == "200.00"
    assert str(utilised["remaining_amount"]) == "800.00"


async def test_commit_contract_budget_exceeded_service():
    sponsor_code = unique_code("DISCOVERY")

    created = await create_funding_contract(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
        sponsor_name="Discovery",
        contract_name="Discovery Health Rewards",
        contract_value="100.00",
        start_date=date(2026, 1, 1),
        end_date=date(2027, 12, 31),
    )

    with pytest.raises(FundingContractExceeded):
        await commit_funding_contract_budget(
            contract_id=created["contract_id"],
            amount="150.00",
        )


async def test_release_more_than_committed_raises_service():
    sponsor_code = unique_code("TOYOTA")

    created = await create_funding_contract(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
        sponsor_name="Toyota",
        contract_name="Toyota Vehicle Rewards",
        contract_value="1000.00",
        start_date=date(2026, 1, 1),
        end_date=date(2027, 12, 31),
    )

    with pytest.raises(FundingContractExceeded):
        await release_funding_contract_budget(
            contract_id=created["contract_id"],
            amount="100.00",
        )


async def test_utilise_more_than_committed_raises_service():
    sponsor_code = unique_code("VODACOM")

    created = await create_funding_contract(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
        sponsor_name="Vodacom",
        contract_name="Vodacom Data Rewards",
        contract_value="1000.00",
        start_date=date(2026, 1, 1),
        end_date=date(2027, 12, 31),
    )

    with pytest.raises(FundingContractExceeded):
        await utilise_funding_contract_budget(
            contract_id=created["contract_id"],
            amount="100.00",
        )


async def test_suspend_blocks_commit_then_activate_allows_commit_service():
    sponsor_code = unique_code("PEP")

    created = await create_funding_contract(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
        sponsor_name="PEP",
        contract_name="PEP Retail Rewards",
        contract_value="1000.00",
        start_date=date(2026, 1, 1),
        end_date=date(2027, 12, 31),
    )

    contract_id = created["contract_id"]

    suspended = await suspend_funding_contract(contract_id=contract_id)

    assert suspended["status"] == "SUSPENDED"

    with pytest.raises(FundingContractInactive):
        await commit_funding_contract_budget(
            contract_id=contract_id,
            amount="100.00",
        )

    activated = await activate_funding_contract(contract_id=contract_id)

    assert activated["status"] == "ACTIVE"

    committed = await commit_funding_contract_budget(
        contract_id=contract_id,
        amount="100.00",
    )

    assert str(committed["committed_amount"]) == "100.00"


async def test_cancel_contract_service():
    sponsor_code = unique_code("MAKRO")

    created = await create_funding_contract(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
        sponsor_name="Makro",
        contract_name="Makro Retail Rewards",
        contract_value="1000.00",
        start_date=date(2026, 1, 1),
        end_date=date(2027, 12, 31),
    )

    cancelled = await cancel_funding_contract(
        contract_id=created["contract_id"],
    )

    assert cancelled["status"] == "CANCELLED"


async def test_get_missing_contract_raises_service():
    with pytest.raises(FundingContractNotFound):
        await get_funding_contract(contract_id=str(uuid4()))


async def test_resolve_missing_active_contract_raises_service():
    with pytest.raises(FundingContractNotFound):
        await resolve_active_funding_contract(
            tenant_code="FNB",
            sponsor_code=unique_code("MISSING"),
            as_of_date=date(2026, 6, 1),
        )


async def test_contract_ledger_service():
    sponsor_code = unique_code("CHECKERS")

    created = await create_funding_contract(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
        sponsor_name="Checkers",
        contract_name="Checkers Grocery Rewards",
        contract_value="1000.00",
        start_date=date(2026, 1, 1),
        end_date=date(2027, 12, 31),
    )

    await commit_funding_contract_budget(
        contract_id=created["contract_id"],
        amount="100.00",
        correlation_id="corr-service-ledger",
    )

    ledger = await get_funding_contract_ledger(
        contract_id=created["contract_id"],
    )

    event_types = {item["event_type"] for item in ledger}

    assert "CONTRACT_CREATED" in event_types
    assert "BUDGET_COMMITTED" in event_types

async def test_commit_returns_none_raises_exceeded(monkeypatch):
    from services.marketplace_funding import funding_contract_service

    async def fake_commit_contract_amount(**kwargs):
        return None

    monkeypatch.setattr(
        funding_contract_service,
        "commit_contract_amount",
        fake_commit_contract_amount,
    )

    created = await create_funding_contract(
        tenant_code="FNB",
        sponsor_code=unique_code("COMMIT"),
        sponsor_name="Commit Test",
        contract_name="Commit Test",
        contract_value="1000.00",
        start_date=date(2026, 1, 1),
        end_date=date(2027, 12, 31),
    )

    with pytest.raises(FundingContractExceeded):
        await commit_funding_contract_budget(
            contract_id=created["contract_id"],
            amount="100.00",
        )


async def test_release_returns_none_raises_exceeded(monkeypatch):
    from services.marketplace_funding import funding_contract_service

    async def fake_release_contract_amount(**kwargs):
        return None

    monkeypatch.setattr(
        funding_contract_service,
        "release_contract_amount",
        fake_release_contract_amount,
    )

    created = await create_funding_contract(
        tenant_code="FNB",
        sponsor_code=unique_code("RELEASE"),
        sponsor_name="Release Test",
        contract_name="Release Test",
        contract_value="1000.00",
        start_date=date(2026, 1, 1),
        end_date=date(2027, 12, 31),
    )

    with pytest.raises(FundingContractExceeded):
        await release_funding_contract_budget(
            contract_id=created["contract_id"],
            amount="100.00",
        )


async def test_suspend_missing_contract_raises(monkeypatch):
    from services.marketplace_funding import funding_contract_service

    async def fake_update_contract_status(**kwargs):
        return None

    monkeypatch.setattr(
        funding_contract_service,
        "update_contract_status",
        fake_update_contract_status,
    )

    with pytest.raises(FundingContractNotFound):
        await suspend_funding_contract(
            contract_id=str(uuid4()),
        )


async def test_activate_missing_contract_raises(monkeypatch):
    from services.marketplace_funding import funding_contract_service

    async def fake_update_contract_status(**kwargs):
        return None

    monkeypatch.setattr(
        funding_contract_service,
        "update_contract_status",
        fake_update_contract_status,
    )

    with pytest.raises(FundingContractNotFound):
        await activate_funding_contract(
            contract_id=str(uuid4()),
        )


async def test_cancel_missing_contract_raises(monkeypatch):
    from services.marketplace_funding import funding_contract_service

    async def fake_update_contract_status(**kwargs):
        return None

    monkeypatch.setattr(
        funding_contract_service,
        "update_contract_status",
        fake_update_contract_status,
    )

    with pytest.raises(FundingContractNotFound):
        await cancel_funding_contract(
            contract_id=str(uuid4()),
        )

async def test_commit_repository_returns_none_raises_exceeded(monkeypatch):
    from services.marketplace_funding import funding_contract_service

    async def fake_commit_contract_amount(**kwargs):
        return None

    monkeypatch.setattr(
        funding_contract_service,
        "commit_contract_amount",
        fake_commit_contract_amount,
    )

    created = await create_funding_contract(
        tenant_code="FNB",
        sponsor_code=unique_code("COMMITNONE"),
        sponsor_name="Commit None",
        contract_name="Commit None",
        contract_value="1000.00",
        start_date=date(2026, 1, 1),
        end_date=date(2027, 12, 31),
    )

    # Make sure validation passes first
    contract = await get_funding_contract(
        contract_id=created["contract_id"]
    )

    assert str(contract["remaining_amount"]) == "1000.00"

    with pytest.raises(FundingContractExceeded):
        await commit_funding_contract_budget(
            contract_id=created["contract_id"],
            amount="100.00",
        )

async def test_commit_updated_none_branch(monkeypatch):
    from services.marketplace_funding import funding_contract_service

    created = await create_funding_contract(
        tenant_code="FNB",
        sponsor_code=unique_code("NONE"),
        sponsor_name="None Test",
        contract_name="None Test",
        contract_value="1000.00",
        start_date=date(2026, 1, 1),
        end_date=date(2027, 12, 31),
    )

    async def fake_commit_contract_amount(*args, **kwargs):
        return None

    monkeypatch.setattr(
        funding_contract_service,
        "commit_contract_amount",
        fake_commit_contract_amount,
    )

    with pytest.raises(FundingContractExceeded):
        await funding_contract_service.commit_funding_contract_budget(
            contract_id=created["contract_id"],
            amount="100.00",
        )