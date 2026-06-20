from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from services.funding.funding_contract_repository import (
    commit_contract_amount,
    create_contract,
    create_contract_ledger_entry,
    get_active_contract_for_sponsor,
    get_contract,
    list_contract_ledger,
    list_contracts,
    release_contract_amount,
    update_contract_status,
    utilise_contract_amount,
)


class FundingContractError(Exception):
    pass


class FundingContractNotFound(FundingContractError):
    pass


class FundingContractInactive(FundingContractError):
    pass


class FundingContractExpired(FundingContractError):
    pass


class FundingContractExceeded(FundingContractError):
    pass


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value))


async def create_funding_contract(
    *,
    tenant_code: str,
    sponsor_code: str,
    sponsor_name: str,
    contract_name: str,
    contract_value: Decimal | int | float | str,
    start_date: date,
    end_date: date,
    currency: str = "ZAR",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    amount = _to_decimal(contract_value)

    contract = await create_contract(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        sponsor_name=sponsor_name,
        contract_name=contract_name,
        contract_value=amount,
        start_date=start_date,
        end_date=end_date,
        currency=currency,
        metadata=metadata,
    )

    await create_contract_ledger_entry(
        contract_id=contract["contract_id"],
        event_type="CONTRACT_CREATED",
        amount=amount,
        metadata=metadata,
    )

    return contract


async def get_funding_contract(
    *,
    contract_id: str,
) -> dict[str, Any]:
    contract = await get_contract(contract_id=contract_id)

    if not contract:
        raise FundingContractNotFound("Funding contract not found")

    return contract


async def list_funding_contracts(
    *,
    tenant_code: str,
    sponsor_code: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    return await list_contracts(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        status=status,
        limit=limit,
    )


async def resolve_active_funding_contract(
    *,
    tenant_code: str,
    sponsor_code: str,
    as_of_date: date | None = None,
) -> dict[str, Any]:
    resolved_date = as_of_date or date.today()

    contract = await get_active_contract_for_sponsor(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        as_of_date=resolved_date,
    )

    if not contract:
        raise FundingContractNotFound("No active funding contract found")

    return contract


def validate_contract_for_amount(
    *,
    contract: dict[str, Any],
    amount: Decimal,
    as_of_date: date | None = None,
) -> None:
    resolved_date = as_of_date or date.today()

    if contract["status"] != "ACTIVE":
        raise FundingContractInactive("Funding contract is not active")

    if contract["start_date"] > resolved_date or contract["end_date"] < resolved_date:
        raise FundingContractExpired("Funding contract is outside valid date range")

    if _to_decimal(contract["remaining_amount"]) < amount:
        raise FundingContractExceeded("Funding contract has insufficient remaining budget")


async def commit_funding_contract_budget(
    *,
    contract_id: str,
    amount: Decimal | int | float | str,
    reward_id: str | None = None,
    allocation_id: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = _to_decimal(amount)

    contract = await get_funding_contract(contract_id=contract_id)

    validate_contract_for_amount(
        contract=contract,
        amount=value,
    )

    updated = await commit_contract_amount(
        contract_id=contract_id,
        amount=value,
    )

    if not updated:
        raise FundingContractExceeded("Funding contract has insufficient remaining budget")

    await create_contract_ledger_entry(
        contract_id=contract_id,
        event_type="BUDGET_COMMITTED",
        amount=value,
        reward_id=reward_id,
        allocation_id=allocation_id,
        correlation_id=correlation_id,
        metadata=metadata,
    )

    return updated


async def release_funding_contract_budget(
    *,
    contract_id: str,
    amount: Decimal | int | float | str,
    reward_id: str | None = None,
    allocation_id: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = _to_decimal(amount)

    updated = await release_contract_amount(
        contract_id=contract_id,
        amount=value,
    )

    if not updated:
        raise FundingContractExceeded("Funding contract has insufficient committed budget")

    await create_contract_ledger_entry(
        contract_id=contract_id,
        event_type="BUDGET_RELEASED",
        amount=value,
        reward_id=reward_id,
        allocation_id=allocation_id,
        correlation_id=correlation_id,
        metadata=metadata,
    )

    return updated


async def utilise_funding_contract_budget(
    *,
    contract_id: str,
    amount: Decimal | int | float | str,
    reward_id: str | None = None,
    allocation_id: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = _to_decimal(amount)

    updated = await utilise_contract_amount(
        contract_id=contract_id,
        amount=value,
    )

    if not updated:
        raise FundingContractExceeded("Funding contract has insufficient committed budget")

    await create_contract_ledger_entry(
        contract_id=contract_id,
        event_type="BUDGET_UTILISED",
        amount=value,
        reward_id=reward_id,
        allocation_id=allocation_id,
        correlation_id=correlation_id,
        metadata=metadata,
    )

    return updated


async def suspend_funding_contract(
    *,
    contract_id: str,
) -> dict[str, Any]:
    updated = await update_contract_status(
        contract_id=contract_id,
        status="SUSPENDED",
    )

    if not updated:
        raise FundingContractNotFound("Funding contract not found")

    return updated


async def activate_funding_contract(
    *,
    contract_id: str,
) -> dict[str, Any]:
    updated = await update_contract_status(
        contract_id=contract_id,
        status="ACTIVE",
    )

    if not updated:
        raise FundingContractNotFound("Funding contract not found")

    return updated


async def cancel_funding_contract(
    *,
    contract_id: str,
) -> dict[str, Any]:
    updated = await update_contract_status(
        contract_id=contract_id,
        status="CANCELLED",
    )

    if not updated:
        raise FundingContractNotFound("Funding contract not found")

    return updated


async def get_funding_contract_ledger(
    *,
    contract_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    await get_funding_contract(contract_id=contract_id)

    return await list_contract_ledger(
        contract_id=contract_id,
        limit=limit,
    )