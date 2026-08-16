from __future__ import annotations

import pytest

from services.referral_saas_programme_configuration_service import (
    ProgrammeConfigurationValidationError,
    _get_active_customer_product_offering_binding,
)


class FakeBindingConnection:
    def __init__(self, row):
        self.row = row
        self.calls = []

    async def fetchrow(self, query, *args):
        self.calls.append({"query": query, "args": args})
        return self.row


@pytest.mark.asyncio
async def test_programme_product_binding_accepts_active_same_account_offering() -> None:
    conn = FakeBindingConnection(
        {
            "customer_product_line_id": "line-1",
            "external_product_line_ref": "TRANSACTIONAL_BANKING",
            "product_line_name": "Transactional Banking",
            "product_line_category": "BANKING",
            "product_line_status": "ACTIVE",
            "customer_product_offering_id": "offering-1",
            "external_offering_ref": "EASY_ACCOUNT",
            "offering_name": "Easy Account",
            "offering_family": "Retail accounts",
            "product_offering_status": "ACTIVE",
            "product_offering_operating_jurisdiction_code": "ZA",
        }
    )

    binding = await _get_active_customer_product_offering_binding(
        conn,
        account_id="acct-1",
        operating_jurisdiction_code="ZA",
        customer_product_line_id="line-1",
        customer_product_offering_id="offering-1",
        required=True,
    )

    assert binding["productLineName"] == "Transactional Banking"
    assert binding["offeringName"] == "Easy Account"
    assert conn.calls[0]["args"] == ("acct-1", "line-1", "offering-1", "ZA")


@pytest.mark.asyncio
async def test_programme_product_binding_rejects_missing_or_wrong_account_offering() -> None:
    conn = FakeBindingConnection(None)

    with pytest.raises(ProgrammeConfigurationValidationError) as exc:
        await _get_active_customer_product_offering_binding(
            conn,
            account_id="acct-1",
            operating_jurisdiction_code="ZA",
            customer_product_line_id="line-other",
            customer_product_offering_id="offering-other",
            required=True,
        )

    assert "same account and jurisdiction" in str(exc.value)


@pytest.mark.asyncio
async def test_programme_product_binding_rejects_retired_offering() -> None:
    conn = FakeBindingConnection(
        {
            "customer_product_line_id": "line-1",
            "product_line_status": "ACTIVE",
            "customer_product_offering_id": "offering-1",
            "product_offering_status": "RETIRED",
        }
    )

    with pytest.raises(ProgrammeConfigurationValidationError) as exc:
        await _get_active_customer_product_offering_binding(
            conn,
            account_id="acct-1",
            operating_jurisdiction_code="ZA",
            customer_product_line_id="line-1",
            customer_product_offering_id="offering-1",
            required=True,
        )

    assert "active product line and active offering" in str(exc.value)


@pytest.mark.asyncio
async def test_programme_product_binding_requires_line_and_offering_together() -> None:
    conn = FakeBindingConnection(None)

    with pytest.raises(ProgrammeConfigurationValidationError) as exc:
        await _get_active_customer_product_offering_binding(
            conn,
            account_id="acct-1",
            operating_jurisdiction_code="ZA",
            customer_product_line_id="line-1",
            customer_product_offering_id=None,
            required=True,
        )

    assert "needs both" in str(exc.value)
