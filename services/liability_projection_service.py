from __future__ import annotations

from decimal import Decimal
from typing import Any

from services.outcome_trace_service import get_outcome_trace

MONEY_SECTIONS = {
    "reward",
    "commission",
    "funding",
    "fulfilment",
    "settlement",
    "audit",
}

TOTAL_FIELDS = [
    "obligation_total",
    "reserved_total",
    "released_total",
    "fulfilled_total",
    "settled_total",
    "reversed_total",
    "failed_total",
    "disputed_total",
]


def _decimal(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0.00")
    return Decimal(str(value))


def _money(value: Any) -> Decimal:
    return _decimal(value).quantize(Decimal("0.01"))


def _section_items(trace: dict[str, Any], section: str) -> list[dict[str, Any]]:
    data = trace.get("sections", {}).get(section) or {}
    return list(data.get("items") or [])


def _source_status(item: dict[str, Any]) -> str:
    return str(
        item.get("status")
        or item.get("commission_status")
        or item.get("source_status")
        or "UNKNOWN"
    ).upper()


def _reward_category(item: dict[str, Any]) -> str:
    beneficiary_type = str(item.get("beneficiary_type") or "").upper()
    reward_type = str(item.get("reward_type") or "").upper()

    if beneficiary_type == "REFEREE" or reward_type in {"REFEREE", "CUSTOMER"}:
        return "CUSTOMER_REWARD"
    return "REFERRER_REWARD"


def _reward_state(item: dict[str, Any]) -> str:
    status = _source_status(item)
    if status == "FULFILLED":
        return "FULFILLED"
    if status == "REVERSED":
        return "REVERSED"
    if status == "FAILED":
        return "FAILED"
    if status in {"PENDING_FULFILMENT", "PENDING", "PROCESSING"}:
        return "PENDING"
    return "CALCULATED"


def _commission_state(item: dict[str, Any]) -> str:
    status = _source_status(item)
    if status == "CREDITED":
        return "FULFILLED"
    if status == "REVERSED":
        return "REVERSED"
    if status == "FAILED":
        return "FAILED"
    return "CALCULATED"


def _funding_state(item: dict[str, Any]) -> str:
    status = _source_status(item)
    if status in {"RESERVED", "RELEASED", "SETTLED", "REVERSED"}:
        return status
    if status in {"FAILED", "DISPUTED"}:
        return status
    return "PENDING"


def _fulfilment_state(item: dict[str, Any]) -> str:
    status = _source_status(item)
    if status == "SUCCESS":
        return "FULFILLED"
    if status in {"FAILED_RETRYABLE", "FAILED_FINAL", "DLQ", "FAILED"}:
        return "FAILED"
    if status == "SKIPPED_DUPLICATE":
        return "FULFILLED"
    return "PENDING"


def _settlement_state(item: dict[str, Any]) -> str:
    if int(item.get("exception_count") or 0) > 0:
        return "DISPUTED"
    status = _source_status(item)
    if status in {"SETTLED", "FAILED", "REVERSED", "DISPUTED"}:
        return status
    return "PENDING"


def _item(
    *,
    source_family: str,
    source: str | None,
    source_id: str | None,
    liability_category: str | None,
    derived_state: str,
    amount: Decimal,
    currency: str | None,
    source_status: str,
    source_item: dict[str, Any],
    join_confidence: str = "MEDIUM",
) -> dict[str, Any]:
    return {
        "source_family": source_family,
        "source": source,
        "source_id": source_id,
        "liability_category": liability_category,
        "derived_state": derived_state,
        "amount": amount,
        "currency": currency or "ZAR",
        "source_status": source_status,
        "join_confidence": join_confidence,
        "evidence": source_item,
    }


def _add_total(totals: dict[str, Decimal], field: str, amount: Decimal) -> None:
    totals[field] += amount


def _recalculate_by_category(
    items: list[dict[str, Any]]
) -> dict[str, dict[str, Decimal]]:
    by_category: dict[str, dict[str, Decimal]] = {}
    for category in ["CUSTOMER_REWARD", "REFERRER_REWARD", "DISTRIBUTOR_COMMISSION"]:
        by_category[category] = {field: Decimal("0.00") for field in TOTAL_FIELDS}

    for item in items:
        category = item.get("liability_category")
        if category not in by_category:
            continue
        amount = _money(item.get("amount"))
        state = item.get("derived_state")
        if item["source_family"] in {"reward", "commission"} and state != "REVERSED":
            by_category[category]["obligation_total"] += amount
        if state == "RESERVED":
            by_category[category]["reserved_total"] += amount
        elif state == "RELEASED":
            by_category[category]["released_total"] += amount
        elif state == "FULFILLED":
            by_category[category]["fulfilled_total"] += amount
        elif state == "SETTLED":
            by_category[category]["settled_total"] += amount
        elif state == "REVERSED":
            by_category[category]["reversed_total"] += amount
        elif state == "FAILED":
            by_category[category]["failed_total"] += amount
        elif state == "DISPUTED":
            by_category[category]["disputed_total"] += amount

    return by_category


def _liability_completeness(missing_evidence: list[dict[str, Any]]) -> str:
    if not missing_evidence:
        return "COMPLETE"
    if any(item.get("code") == "SOURCE_CONFLICT" for item in missing_evidence):
        return "INCONSISTENT"
    if any(item.get("code") == "SOURCE_UNAVAILABLE" for item in missing_evidence):
        return "UNAVAILABLE"
    return "PARTIAL"


def derive_liability_projection(trace: dict[str, Any]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    duplicate_keys: set[tuple[Any, ...]] = set()
    warnings: list[dict[str, Any]] = []

    for reward in _section_items(trace, "reward"):
        category = _reward_category(reward)
        amount = _money(reward.get("amount"))
        key = (
            "reward",
            category,
            reward.get("reward_id"),
            reward.get("beneficiary_type"),
            reward.get("beneficiary_ref"),
            reward.get("reward_type"),
            str(amount),
        )
        if key in duplicate_keys:
            warnings.append(
                {
                    "section": "reward",
                    "code": "DUPLICATE_SOURCE_EVIDENCE",
                    "severity": "WARNING",
                    "message": "Duplicate reward source evidence was not added to obligation totals.",
                    "source": reward.get("source") or "reward",
                }
            )
            continue
        duplicate_keys.add(key)
        items.append(
            _item(
                source_family="reward",
                source=reward.get("source"),
                source_id=reward.get("reward_id"),
                liability_category=category,
                derived_state=_reward_state(reward),
                amount=amount,
                currency=reward.get("currency"),
                source_status=_source_status(reward),
                source_item=reward,
                join_confidence="MEDIUM",
            )
        )

    for commission in _section_items(trace, "commission"):
        amount = _money(commission.get("commission_amount") or commission.get("amount"))
        items.append(
            _item(
                source_family="commission",
                source=commission.get("source") or "distribution_commission_events",
                source_id=commission.get("commission_event_id"),
                liability_category="DISTRIBUTOR_COMMISSION",
                derived_state=_commission_state(commission),
                amount=amount,
                currency=commission.get("currency"),
                source_status=_source_status(commission),
                source_item=commission,
                join_confidence="MEDIUM",
            )
        )

    for funding in _section_items(trace, "funding"):
        items.append(
            _item(
                source_family="funding",
                source=funding.get("source"),
                source_id=funding.get("funding_id"),
                liability_category=None,
                derived_state=_funding_state(funding),
                amount=_money(funding.get("amount")),
                currency=funding.get("currency"),
                source_status=_source_status(funding),
                source_item=funding,
                join_confidence="LOW",
            )
        )

    for fulfilment in _section_items(trace, "fulfilment"):
        items.append(
            _item(
                source_family="fulfilment",
                source=fulfilment.get("source") or "fulfilment_audit",
                source_id=fulfilment.get("audit_id"),
                liability_category=None,
                derived_state=_fulfilment_state(fulfilment),
                amount=_money(
                    fulfilment.get("amount") or fulfilment.get("reward_value")
                ),
                currency=fulfilment.get("currency"),
                source_status=_source_status(fulfilment),
                source_item=fulfilment,
                join_confidence="MEDIUM",
            )
        )

    for settlement in _section_items(trace, "settlement"):
        items.append(
            _item(
                source_family="settlement",
                source=settlement.get("source") or "fulfilment_settlement_ledger",
                source_id=settlement.get("settlement_id"),
                liability_category=None,
                derived_state=_settlement_state(settlement),
                amount=_money(settlement.get("amount")),
                currency=settlement.get("currency"),
                source_status=_source_status(settlement),
                source_item=settlement,
                join_confidence="MEDIUM",
            )
        )

    totals = {field: Decimal("0.00") for field in TOTAL_FIELDS}
    for item in items:
        amount = _money(item["amount"])
        state = item["derived_state"]
        if item["source_family"] in {"reward", "commission"} and state != "REVERSED":
            _add_total(totals, "obligation_total", amount)
        if state == "RESERVED":
            _add_total(totals, "reserved_total", amount)
        elif state == "RELEASED":
            _add_total(totals, "released_total", amount)
        elif state == "FULFILLED":
            _add_total(totals, "fulfilled_total", amount)
        elif state == "SETTLED":
            _add_total(totals, "settled_total", amount)
        elif state == "REVERSED":
            _add_total(totals, "reversed_total", amount)
        elif state == "FAILED":
            _add_total(totals, "failed_total", amount)
        elif state == "DISPUTED":
            _add_total(totals, "disputed_total", amount)

    relevant_missing = [
        item
        for item in trace.get("missing_evidence", [])
        if item.get("section") in MONEY_SECTIONS
        and item.get("code") != "SECTION_NOT_REQUESTED"
    ]
    source_warnings = [
        item
        for item in trace.get("source_warnings", [])
        if item.get("section") in MONEY_SECTIONS
    ]
    source_warnings.extend(warnings)

    return {
        "projection_type": "OUTCOME_LIABILITY",
        "tenant_code": trace.get("tenant_code"),
        "lookup": trace.get("lookup"),
        "trace_id": trace.get("trace_id"),
        "trace_completeness": trace.get("trace_completeness"),
        "liability_completeness": _liability_completeness(relevant_missing),
        "totals": totals,
        "totals_by_category": _recalculate_by_category(items),
        "items": items,
        "missing_evidence": relevant_missing,
        "source_warnings": source_warnings,
        "redactions": trace.get("redactions", []),
        "generated_at": trace.get("generated_at"),
    }


async def get_outcome_liability_projection(
    *,
    tenant_code: str,
    referral_track_id: str,
    identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    trace = await get_outcome_trace(
        tenant_code=tenant_code,
        referral_track_id=referral_track_id,
        identity=identity,
        include_sections=[
            "reward",
            "commission",
            "funding",
            "fulfilment",
            "settlement",
            "audit",
        ],
    )
    return derive_liability_projection(trace)
