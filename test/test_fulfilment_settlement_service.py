from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from services.fulfilment.settlement.service import (
    get_provider_exposure,
    get_settlement_by_id,
    get_settlement_by_reward,
    list_settlements,
    mark_disputed,
    mark_failed,
    mark_processing,
    mark_reversed,
    mark_settled,
    record_pending_settlement,
    update_settlement_status,
    _row_to_dict,
    _to_decimal,
)
from services.fulfilment.settlement.status import SettlementStatus



def test_to_decimal_returns_existing_decimal():
    value = Decimal("123.45")

    result = _to_decimal(value)

    assert result is value


def test_row_to_dict_returns_none():
    assert _row_to_dict(None) is None


pytestmark = pytest.mark.asyncio


def unique_uuid() -> str:
    return str(uuid4())


async def create_pending_settlement(
    *,
    tenant_code: str = "FNB",
    provider_key: str = "CASH_PROVIDER",
    amount: str = "100.00",
) -> dict:
    return await record_pending_settlement(
        tenant_code=tenant_code,
        reward_id=unique_uuid(),
        audit_id=unique_uuid(),
        provider_key=provider_key,
        provider_reference="PROV-123",
        amount=amount,
        currency="ZAR",
    )


async def test_record_pending_settlement():
    reward_id = unique_uuid()
    audit_id = unique_uuid()

    settlement = await record_pending_settlement(
        tenant_code="FNB",
        reward_id=reward_id,
        audit_id=audit_id,
        provider_key="CASH_PROVIDER",
        provider_reference="PROV-123",
        amount="100.00",
        currency="ZAR",
    )

    assert settlement["tenant_code"] == "FNB"
    assert str(settlement["reward_id"]) == reward_id
    assert str(settlement["audit_id"]) == audit_id
    assert settlement["provider_key"] == "CASH_PROVIDER"
    assert settlement["provider_reference"] == "PROV-123"
    assert settlement["amount"] == Decimal("100.00")
    assert settlement["currency"] == "ZAR"
    assert settlement["status"] == SettlementStatus.PENDING.value


async def test_mark_processing():
    settlement = await create_pending_settlement()

    updated = await mark_processing(
        settlement_id=settlement["settlement_id"],
    )

    assert updated["status"] == SettlementStatus.PROCESSING.value


async def test_mark_settled():
    settlement = await create_pending_settlement()

    updated = await mark_settled(
        settlement_id=settlement["settlement_id"],
    )

    assert updated["status"] == SettlementStatus.SETTLED.value
    assert updated["settled_at"] is not None


async def test_mark_failed():
    settlement = await create_pending_settlement()

    updated = await mark_failed(
        settlement_id=settlement["settlement_id"],
        failure_reason="provider failed",
    )

    assert updated["status"] == SettlementStatus.FAILED.value
    assert updated["failed_at"] is not None
    assert updated["failure_reason"] == "provider failed"


async def test_mark_reversed():
    settlement = await create_pending_settlement()

    updated = await mark_reversed(
        settlement_id=settlement["settlement_id"],
        reversal_reason="manual reversal",
    )

    assert updated["status"] == SettlementStatus.REVERSED.value
    assert updated["reversed_at"] is not None
    assert updated["reversal_reason"] == "manual reversal"


async def test_mark_disputed():
    settlement = await create_pending_settlement()

    updated = await mark_disputed(
        settlement_id=settlement["settlement_id"],
    )

    assert updated["status"] == SettlementStatus.DISPUTED.value


async def test_get_settlement_by_id():
    settlement = await create_pending_settlement()

    found = await get_settlement_by_id(
        settlement_id=settlement["settlement_id"],
    )

    assert found is not None
    assert found["settlement_id"] == settlement["settlement_id"]


async def test_get_settlement_by_reward():
    reward_id = unique_uuid()

    settlement = await record_pending_settlement(
        tenant_code="FNB",
        reward_id=reward_id,
        audit_id=unique_uuid(),
        provider_key="CASH_PROVIDER",
        provider_reference="PROV-123",
        amount="100.00",
    )

    found = await get_settlement_by_reward(
        reward_id=reward_id,
    )

    assert found is not None
    assert found["settlement_id"] == settlement["settlement_id"]
    assert str(found["reward_id"]) == reward_id


async def test_get_missing_settlement_by_id_returns_none():
    found = await get_settlement_by_id(
        settlement_id=unique_uuid(),
    )

    assert found is None


async def test_get_missing_settlement_by_reward_returns_none():
    found = await get_settlement_by_reward(
        reward_id=unique_uuid(),
    )

    assert found is None


async def test_list_settlements_with_filters():
    reward_id = unique_uuid()

    await record_pending_settlement(
        tenant_code="LIST_TENANT",
        reward_id=reward_id,
        audit_id=unique_uuid(),
        provider_key="LIST_PROVIDER",
        provider_reference="PROV-LIST",
        amount="50.00",
    )

    rows = await list_settlements(
        tenant_code="LIST_TENANT",
        provider_key="LIST_PROVIDER",
        status=SettlementStatus.PENDING,
        limit=50,
    )

    assert len(rows) >= 1
    assert any(str(row["reward_id"]) == reward_id for row in rows)


async def test_list_settlements_without_filters():
    reward_id = unique_uuid()

    await record_pending_settlement(
        tenant_code="LIST_ALL_TENANT",
        reward_id=reward_id,
        audit_id=unique_uuid(),
        provider_key="LIST_ALL_PROVIDER",
        provider_reference="PROV-LIST-ALL",
        amount="75.00",
    )

    rows = await list_settlements(limit=100)

    assert len(rows) >= 1
    assert any(str(row["reward_id"]) == reward_id for row in rows)


async def test_get_provider_exposure():
    await record_pending_settlement(
        tenant_code="EXPOSURE_TENANT",
        reward_id=unique_uuid(),
        audit_id=unique_uuid(),
        provider_key="EXPOSURE_PROVIDER",
        provider_reference="PROV-EXP",
        amount="150.00",
    )

    exposure = await get_provider_exposure(
        tenant_code="EXPOSURE_TENANT",
        provider_key="EXPOSURE_PROVIDER",
    )

    assert len(exposure) >= 1
    row = exposure[0]

    assert row["tenant_code"] == "EXPOSURE_TENANT"
    assert row["provider_key"] == "EXPOSURE_PROVIDER"
    assert row["currency"] == "ZAR"
    assert row["settlement_count"] >= 1
    assert row["exposure_amount"] >= Decimal("150.00")


async def test_update_settlement_status_invalid_status_raises():
    settlement = await create_pending_settlement()

    with pytest.raises(ValueError, match="Invalid settlement status"):
        await update_settlement_status(
            settlement_id=settlement["settlement_id"],
            status="BAD_STATUS",
        )


async def test_update_missing_settlement_raises():
    with pytest.raises(ValueError, match="Settlement not found"):
        await update_settlement_status(
            settlement_id=unique_uuid(),
            status=SettlementStatus.SETTLED,
        )