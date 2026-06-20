from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from services.marketplace_funding.sponsor_wallet_ledger_service import (
    list_sponsor_wallet_transactions,
    record_wallet_transaction,
)
from services.marketplace_funding.sponsor_wallet_service import (
    create_sponsor_wallet,
)

pytestmark = pytest.mark.asyncio


def unique_code(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}".upper()


async def test_record_wallet_transaction_creates_ledger_entry():
    wallet = await create_sponsor_wallet(
        tenant_code="FNB",
        sponsor_code=unique_code("LEDGER"),
        sponsor_name="Ledger Sponsor",
        currency="ZAR",
    )

    entry = await record_wallet_transaction(
        wallet_id=str(wallet["wallet_id"]),
        tenant_code="FNB",
        transaction_type="TOPUP",
        amount=Decimal("500.00"),
        balance_before=Decimal("0.00"),
        balance_after=Decimal("500.00"),
        correlation_id="corr-ledger-001",
        metadata={"source": "test"},
    )

    assert str(entry["wallet_id"]) == str(wallet["wallet_id"])
    assert entry["tenant_code"] == "FNB"
    assert entry["transaction_type"] == "TOPUP"
    assert entry["amount"] == Decimal("500.00")
    assert entry["balance_before"] == Decimal("0.00")
    assert entry["balance_after"] == Decimal("500.00")
    assert entry["correlation_id"] == "corr-ledger-001"
    assert entry["metadata"] == {"source": "test"}


async def test_record_wallet_transaction_defaults_metadata_to_empty_dict():
    wallet = await create_sponsor_wallet(
        tenant_code="FNB",
        sponsor_code=unique_code("NOMETA"),
        sponsor_name="No Metadata Sponsor",
        currency="ZAR",
    )

    entry = await record_wallet_transaction(
        wallet_id=str(wallet["wallet_id"]),
        tenant_code="FNB",
        transaction_type="RESERVE",
        amount="100.00",
        balance_before="0.00",
        balance_after="100.00",
    )

    assert entry["transaction_type"] == "RESERVE"
    assert entry["amount"] == Decimal("100.00")
    assert entry["metadata"] == {}


async def test_list_sponsor_wallet_transactions_returns_wallet_entries():
    wallet = await create_sponsor_wallet(
        tenant_code="FNB",
        sponsor_code=unique_code("LISTLEDGER"),
        sponsor_name="List Ledger Sponsor",
        currency="ZAR",
    )

    await record_wallet_transaction(
        wallet_id=str(wallet["wallet_id"]),
        tenant_code="FNB",
        transaction_type="TOPUP",
        amount=Decimal("250.00"),
        balance_before=Decimal("0.00"),
        balance_after=Decimal("250.00"),
        correlation_id="corr-list-001",
        metadata={"step": 1},
    )

    transactions = await list_sponsor_wallet_transactions(
        wallet_id=str(wallet["wallet_id"]),
        limit=10,
    )

    assert len(transactions) >= 1
    assert str(transactions[0]["wallet_id"]) == str(wallet["wallet_id"])

    transaction_types = {item["transaction_type"] for item in transactions}
    assert "TOPUP" in transaction_types