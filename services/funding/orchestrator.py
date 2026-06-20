from __future__ import annotations

from decimal import Decimal
from typing import Any

from services.funding.reservations import (
    create_funding_reservation,
    get_funding_reservation_by_reward,
    mark_reservation_released,
    mark_reservation_settled,
)
from services.funding_service import (
    FundingAccountNotFound,
    get_account_balance,
    list_funding_accounts,
    release_reserved_funds,
    reserve_funds,
    settle_reserved_funds,
)
from services.funding.exposure_limits import validate_exposure
from services.funding.account_resolution import resolve_funding_account
from services.funding.resolution_audit import (
    create_funding_resolution_audit,
)
from services.marketplace_funding.sponsor_funding_service import (
    reserve_reward_funding as reserve_sponsor_reward_funding,
    release_reward_funding as release_sponsor_reward_funding,
    debit_reward_funding as debit_sponsor_reward_funding,
)


class FundingOrchestrationError(Exception):
    """Base funding orchestration error."""


class NoActiveFundingAccount(FundingOrchestrationError):
    """Raised when no active tenant funding account exists."""


class RewardAlreadyReserved(FundingOrchestrationError):
    """Raised when reward already has a funding reservation."""




async def _get_active_tenant_wallet(
    *,
    tenant_code: str,
) -> dict[str, Any]:
    accounts = await list_funding_accounts(
        tenant_code=tenant_code,
        status="ACTIVE",
        limit=100,
    )

    for account in accounts:
        if account["account_type"] == "TENANT_WALLET":
            return account

    raise NoActiveFundingAccount("No active tenant wallet found")



async def has_reward_reservation(
    *,
    reward_id: str,
) -> bool:
    reservation = await get_funding_reservation_by_reward(
        reward_id=reward_id,
    )

    return reservation is not None


async def reserve_reward_funding(
    *,
    reward_id: str,
    tenant_code: str,
    amount: Decimal | int | float | str,
    reward_type: str | None = None,
    segment_code: str | None = None,
    campaign_code: str | None = None,
    sponsor_code: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    existing = await get_funding_reservation_by_reward(
        reward_id=reward_id,
    )

    if existing:
        return {
            "reserved": True,
            "reservation": existing,
            "already_reserved": True,
        }

    routing_metadata = metadata or {}

    resolved_reward_type = reward_type or routing_metadata.get("reward_type")
    resolved_segment_code = segment_code or routing_metadata.get("segment_code")
    resolved_campaign_code = campaign_code or routing_metadata.get("campaign_code")
    resolved_sponsor_code = sponsor_code or routing_metadata.get("sponsor_code")

    account = await resolve_funding_account(
        tenant_code=tenant_code,
        reward_type=resolved_reward_type,
        segment_code=resolved_segment_code,
        campaign_code=resolved_campaign_code,
        sponsor_code=resolved_sponsor_code,
    )

    if account is None:
        raise NoActiveFundingAccount(
            f"No active funding account rule found for tenant {tenant_code}"
        )

    normalised_amount = Decimal(str(amount)).quantize(
        Decimal("0.01")
    )

    funding_model = account.get("funding_model")

    if funding_model == "SPONSOR_FUNDED":
        if not resolved_sponsor_code:
            raise FundingOrchestrationError(
                "Sponsor funded reward missing sponsor_code"
            )

        wallet_id = account.get("wallet_id")

        if not wallet_id:
            raise FundingOrchestrationError(
                "Sponsor funded account missing wallet_id"
            )

        sponsor_reservation = await reserve_sponsor_reward_funding(
            reward_id=reward_id,
            wallet_id=str(wallet_id),
            tenant_code=tenant_code,
            sponsor_code=resolved_sponsor_code,
            amount=normalised_amount,
            correlation_id=correlation_id,
            metadata={
                **routing_metadata,
                "reward_id": reward_id,
                "tenant_code": tenant_code,
                "reward_type": resolved_reward_type,
                "segment_code": resolved_segment_code,
                "campaign_code": resolved_campaign_code,
                "sponsor_code": resolved_sponsor_code,
                "funding_model": funding_model,
                "funding_rule_id": str(account.get("rule_id")),
                "wallet_id": str(wallet_id),
            },
        )

        return {
            **sponsor_reservation,
            "funding_source": "SPONSOR_WALLET",
            "funding_rule_id": account.get("rule_id"),
            "funding_account": account,
        }

    await create_funding_resolution_audit(
        reward_id=reward_id,
        tenant_code=tenant_code,
        account_id=account["account_id"],
        rule_id=account.get("rule_id"),
        reward_type=resolved_reward_type,
        segment_code=resolved_segment_code,
        campaign_code=resolved_campaign_code,
        sponsor_code=resolved_sponsor_code,
        amount=normalised_amount,
        correlation_id=correlation_id,
    )

    valid, reason = await validate_exposure(
        tenant_code=tenant_code,
        account_id=account["account_id"],
        amount=normalised_amount,
    )

    if not valid:
        return {
            "reserved": False,
            "reservation": None,
            "funding_transaction": None,
            "balance": await get_account_balance(
                account_id=account["account_id"]
            ),
            "already_reserved": False,
            "rejected": True,
            "reason": reason,
            "funding_rule_id": account.get("rule_id"),
            "funding_account": account,
        }

    funding_result = await reserve_funds(
        account_id=account["account_id"],
        amount=normalised_amount,
        reference_id=reward_id,
        correlation_id=correlation_id,
        metadata={
            **routing_metadata,
            "reward_id": reward_id,
            "tenant_code": tenant_code,
            "reward_type": resolved_reward_type,
            "segment_code": resolved_segment_code,
            "campaign_code": resolved_campaign_code,
            "sponsor_code": resolved_sponsor_code,
            "funding_rule_id": str(account.get("rule_id")),
            "funding_account_id": str(account["account_id"]),
        },
    )

    transaction = funding_result["transaction"]

    reservation = await create_funding_reservation(
        reward_id=reward_id,
        tenant_code=tenant_code,
        account_id=account["account_id"],
        amount=normalised_amount,
        funding_transaction_id=transaction["transaction_id"],
        correlation_id=correlation_id,
    )

    balance = await get_account_balance(
        account_id=account["account_id"]
    )

    return {
        "reserved": True,
        "reservation": reservation,
        "funding_transaction": transaction,
        "balance": balance,
        "already_reserved": False,
        "funding_rule_id": account.get("rule_id"),
        "funding_account": account,
        "funding_source": "TENANT_WALLET",
    }


async def release_reward_funding(
    *,
    reward_id: str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sponsor_release = await release_sponsor_reward_funding(
        reward_id=reward_id,
        correlation_id=correlation_id,
        metadata=metadata,
    )

    if sponsor_release.get("released") is True:
        return {
            **sponsor_release,
            "funding_source": "SPONSOR_WALLET",
        }

    reservation = await get_funding_reservation_by_reward(
        reward_id=reward_id,
    )

    if not reservation:
        raise FundingAccountNotFound("Funding reservation not found")

    funding_result = await release_reserved_funds(
        account_id=reservation["account_id"],
        amount=reservation["amount"],
        reference_id=reward_id,
        correlation_id=correlation_id or reservation["correlation_id"],
        metadata={
            "reward_id": reward_id,
            "reservation_id": str(reservation["reservation_id"]),
            **(metadata or {}),
        },
    )

    updated_reservation = await mark_reservation_released(
        reward_id=reward_id,
    )

    balance = await get_account_balance(
        account_id=reservation["account_id"],
    )

    return {
        "released": True,
        "reservation": updated_reservation,
        "funding_transaction": funding_result["transaction"],
        "balance": balance,
        "funding_source": "TENANT_WALLET",
    }


async def settle_reward_funding(
    *,
    reward_id: str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sponsor_settlement = await debit_sponsor_reward_funding(
        reward_id=reward_id,
        correlation_id=correlation_id,
        metadata=metadata,
    )

    if sponsor_settlement.get("debited") is True:
        return {
            **sponsor_settlement,
            "settled": True,
            "funding_source": "SPONSOR_WALLET",
        }

    reservation = await get_funding_reservation_by_reward(
        reward_id=reward_id,
    )

    if not reservation:
        raise FundingAccountNotFound("Funding reservation not found")

    funding_result = await settle_reserved_funds(
        account_id=reservation["account_id"],
        amount=reservation["amount"],
        reference_id=reward_id,
        correlation_id=correlation_id or reservation["correlation_id"],
        metadata={
            "reward_id": reward_id,
            "reservation_id": str(reservation["reservation_id"]),
            **(metadata or {}),
        },
    )

    updated_reservation = await mark_reservation_settled(
        reward_id=reward_id,
    )

    balance = await get_account_balance(
        account_id=reservation["account_id"],
    )

    return {
        "settled": True,
        "reservation": updated_reservation,
        "funding_transaction": funding_result["transaction"],
        "balance": balance,
        "funding_source": "TENANT_WALLET",
    }