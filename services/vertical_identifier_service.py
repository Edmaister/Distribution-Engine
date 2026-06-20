from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IdentifierRequirement:
    event_type: str
    required_any: tuple[str, ...] = ()
    required_all: tuple[str, ...] = ()
    label: str = "identifier"


IDENTIFIER_REQUIREMENTS: dict[str, tuple[IdentifierRequirement, ...]] = {
    "BANKING_TRANSACTIONAL:v1": (
        IdentifierRequirement(
            "UCN_CAPTURED", required_all=("refereeUCN",), label="customer UCN"
        ),
        IdentifierRequirement(
            "ACCOUNT_OPENED",
            required_all=("refereeUCN", "accountNumber"),
            label="customer UCN and account number",
        ),
        IdentifierRequirement(
            "ACCOUNT_ACTIVATED",
            required_all=("refereeUCN",),
            label="customer UCN",
        ),
        IdentifierRequirement(
            "FUNDED", required_all=("refereeUCN",), label="customer UCN"
        ),
        IdentifierRequirement(
            "DEBIT_ORDER_SWITCHED",
            required_all=("refereeUCN",),
            label="customer UCN",
        ),
        IdentifierRequirement(
            "SALARY_SWITCHED",
            required_all=("refereeUCN",),
            label="customer UCN",
        ),
        IdentifierRequirement(
            "FIRST_TRANSACTION_COMPLETED",
            required_all=("refereeUCN",),
            label="customer UCN",
        ),
    ),
    "INSURANCE_POLICY:v1": (
        IdentifierRequirement(
            "QUOTE_REQUESTED",
            required_any=("customerReference", "refereeUCN"),
            label="customer reference",
        ),
        IdentifierRequirement(
            "QUOTE_ACCEPTED",
            required_any=("customerReference", "refereeUCN"),
            label="customer reference",
        ),
        IdentifierRequirement(
            "POLICY_ISSUED", required_all=("policyNumber",), label="policy number"
        ),
        IdentifierRequirement(
            "FIRST_PREMIUM_PAID", required_all=("policyNumber",), label="policy number"
        ),
    ),
    "RETAIL_LOYALTY:v1": (
        IdentifierRequirement(
            "BASKET_CREATED",
            required_any=("customerReference", "loyaltyId"),
            label="customer reference or loyalty id",
        ),
        IdentifierRequirement(
            "ORDER_PLACED",
            required_all=("orderId",),
            label="order id",
        ),
        IdentifierRequirement(
            "FIRST_PURCHASE_COMPLETED",
            required_all=("orderId", "basketId"),
            label="order and basket evidence",
        ),
    ),
}


def _lookup(payload: dict[str, Any], field: str) -> Any:
    aliases = {
        field,
        field[:1].lower() + field[1:],
        field[:1].upper() + field[1:],
        _to_snake(field),
    }

    for key in aliases:
        value = payload.get(key)
        if _has_value(value):
            return value

    meta = payload.get("meta")
    if isinstance(meta, dict):
        for key in aliases:
            value = meta.get(key)
            if _has_value(value):
                return value

    return None


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    return bool(str(value).strip())


def _to_snake(value: str) -> str:
    chars: list[str] = []
    for index, char in enumerate(value):
        if char.isupper() and index > 0:
            chars.append("_")
        chars.append(char.lower())
    return "".join(chars)


def get_identifier_requirements(
    journey_code: str, journey_version: str
) -> tuple[IdentifierRequirement, ...]:
    return IDENTIFIER_REQUIREMENTS.get(f"{journey_code}:{journey_version}", ())


def validate_event_identifiers(
    *,
    journey_code: str,
    journey_version: str,
    event_type: str,
    payload: dict[str, Any],
) -> tuple[bool, list[str]]:
    event = str(event_type or "").strip().upper()
    for requirement in get_identifier_requirements(journey_code, journey_version):
        if requirement.event_type != event:
            continue

        missing_all = [
            field for field in requirement.required_all if not _lookup(payload, field)
        ]
        has_any = not requirement.required_any or any(
            _lookup(payload, field) for field in requirement.required_any
        )

        errors: list[str] = []
        if missing_all:
            errors.append(f"{', '.join(missing_all)} is required for {event}")
        if not has_any:
            errors.append(
                f"one of {', '.join(requirement.required_any)} is required for {event}"
            )

        return not errors, errors

    return True, []
