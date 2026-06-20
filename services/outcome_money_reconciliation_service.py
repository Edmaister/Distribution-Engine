from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from utils.db import db_connection


MONEY_STEPS = [
    ("reward_count", "Reward recorded"),
    ("commission_count", "Commission calculated"),
    ("wallet_movement_count", "Distributor wallet movement"),
    ("invoice_count", "Producer invoice line"),
    ("settled_count", "Settlement settled"),
]

ATTENTION_ACTIONS = {
    "Reward recorded": {
        "owner": "Producer - Supply",
        "action": "Check reward policy and completed outcome eligibility.",
    },
    "Commission calculated": {
        "owner": "Distributor - Demand",
        "action": "Check commission rule matching and attribution evidence.",
    },
    "Distributor wallet movement": {
        "owner": "Distributor - Demand",
        "action": "Check wallet crediting and ledger correlation.",
    },
    "Producer invoice line": {
        "owner": "Producer - Supply",
        "action": "Check sponsor billing utilisation and invoice generation.",
    },
    "Settlement settled": {
        "owner": "Amplifi Admin",
        "action": "Check settlement batch, provider response, and approval state.",
    },
    "Open exception": {
        "owner": "Amplifi Admin",
        "action": "Review and resolve the settlement exception.",
    },
}

ROLE_REVIEW_STEPS = {
    "PRODUCER_SUPPLY": {
        "surface": "Producer - Supply",
        "owned_steps": {"Reward recorded", "Producer invoice line"},
        "filter_owner": "Producer - Supply",
        "summary": "Producer-owned outcome money evidence for rewards and invoice readiness.",
        "next_action": "Review missing reward or producer invoice evidence before settlement follow-up.",
    },
    "DISTRIBUTOR_DEMAND": {
        "surface": "Distributor - Demand",
        "owned_steps": {"Commission calculated", "Distributor wallet movement"},
        "filter_owner": "Distributor - Demand",
        "summary": "Distributor-owned outcome money evidence for commission and wallet movement readiness.",
        "next_action": "Review missing commission or wallet evidence before payout and settlement follow-up.",
    },
}


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value or 0))


def _integer(value: Any) -> int:
    return int(value or 0)


def _serialize(row: Any) -> dict[str, Any]:
    data = dict(row) if row else {}
    return {key: _serialise_value(value) for key, value in data.items()}


def _serialise_value(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, list):
        return [_serialise_value(item) for item in value]
    return value


def _money_status(item: dict[str, Any]) -> str:
    if item["exception_count"] > 0:
        return "ATTENTION"

    missing_steps = item.get("missing_steps") or []
    return "READY" if not missing_steps else "ATTENTION"


def _normalise_item(row: Any) -> dict[str, Any]:
    item = _serialize(row)

    for key in [
        "reward_count",
        "commission_count",
        "wallet_movement_count",
        "invoice_count",
        "settlement_count",
        "settled_count",
        "exception_count",
    ]:
        item[key] = _integer(item.get(key))

    for key in [
        "reward_amount",
        "commission_amount",
        "wallet_movement_amount",
        "invoiced_amount",
        "settled_amount",
    ]:
        item[key] = _decimal(item.get(key))

    missing_steps = [label for key, label in MONEY_STEPS if item.get(key, 0) <= 0]
    item["missing_steps"] = missing_steps
    item["repair_actions"] = _repair_actions(item, missing_steps)
    item["money_status"] = _money_status(item)
    return item


def _repair_actions(
    item: dict[str, Any], missing_steps: list[str]
) -> list[dict[str, Any]]:
    actions = []

    for step in missing_steps:
        action = ATTENTION_ACTIONS[step]
        if step == "Reward recorded" and item.get("product"):
            actions.append(
                {
                    "type": "CREATE_REWARD_EVIDENCE",
                    "label": "Create reward evidence",
                    "owner": action["owner"],
                    "action": action["action"],
                    "available": True,
                }
            )
            continue

        if (
            step == "Commission calculated"
            and item.get("reward_count", 0) > 0
            and item.get("distributor_code")
            and item.get("sponsor_code")
        ):
            actions.append(
                {
                    "type": "CREATE_COMMISSION_EVIDENCE",
                    "label": "Create commission evidence",
                    "owner": action["owner"],
                    "action": action["action"],
                    "available": True,
                }
            )
            continue

        if (
            step == "Distributor wallet movement"
            and item.get("commission_count", 0) > 0
        ):
            actions.append(
                {
                    "type": "CREATE_WALLET_EVIDENCE",
                    "label": "Create distributor wallet evidence",
                    "owner": action["owner"],
                    "action": action["action"],
                    "available": True,
                }
            )
            continue

        if (
            step == "Producer invoice line"
            and item.get("reward_count", 0) > 0
            and item.get("sponsor_code")
        ):
            actions.append(
                {
                    "type": "CREATE_INVOICE_EVIDENCE",
                    "label": "Create producer invoice evidence",
                    "owner": action["owner"],
                    "action": action["action"],
                    "available": True,
                }
            )
            continue

        if (
            step == "Settlement settled"
            and item.get("reward_count", 0) > 0
            and item.get("invoice_count", 0) > 0
            and item.get("exception_count", 0) <= 0
        ):
            actions.append(
                {
                    "type": "CREATE_SETTLEMENT_EVIDENCE",
                    "label": "Create settlement evidence",
                    "owner": action["owner"],
                    "action": action["action"],
                    "available": True,
                }
            )
            continue

        actions.append(
            {
                "type": "GUIDED_REPAIR",
                "label": step,
                "owner": action["owner"],
                "action": action["action"],
                "available": False,
            }
        )

    if item.get("exception_count", 0) > 0:
        action = ATTENTION_ACTIONS["Open exception"]
        actions.append(
            {
                "type": "RESOLVE_SETTLEMENT_EXCEPTIONS",
                "label": "Resolve settlement exception",
                "owner": action["owner"],
                "action": action["action"],
                "available": True,
                "exception_ids": item.get("open_exception_ids") or [],
            }
        )

    return actions


def _rate(numerator: int, denominator: int) -> Decimal:
    if denominator <= 0:
        return Decimal("0")
    return (Decimal(numerator) / Decimal(denominator)).quantize(Decimal("0.0001"))


def _step_summary(
    *,
    key: str,
    label: str,
    completed_outcome_count: int,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    ready_count = sum(1 for item in items if _integer(item.get(key)) > 0)
    return {
        "step": label,
        "ready_count": ready_count,
        "missing_count": max(completed_outcome_count - ready_count, 0),
        "completion_rate": _rate(ready_count, completed_outcome_count),
    }


def _summarise(items: list[dict[str, Any]]) -> dict[str, Any]:
    completed_outcome_count = len(items)
    ready_count = sum(1 for item in items if item["money_status"] == "READY")
    exception_count = sum(1 for item in items if item["exception_count"] > 0)
    attention_breakdown = _attention_breakdown(items)

    return {
        "completed_outcome_count": completed_outcome_count,
        "rewarded_count": sum(1 for item in items if item["reward_count"] > 0),
        "commissioned_count": sum(1 for item in items if item["commission_count"] > 0),
        "wallet_movement_count": sum(
            1 for item in items if item["wallet_movement_count"] > 0
        ),
        "invoiced_count": sum(1 for item in items if item["invoice_count"] > 0),
        "settled_count": sum(1 for item in items if item["settled_count"] > 0),
        "exception_count": exception_count,
        "ready_count": ready_count,
        "attention_count": completed_outcome_count - ready_count,
        "money_completion_rate": _rate(ready_count, completed_outcome_count),
        "attention_breakdown": attention_breakdown,
    }


def _attention_breakdown(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    breakdown: list[dict[str, Any]] = []

    for key, label in MONEY_STEPS:
        count = sum(1 for item in items if _integer(item.get(key)) <= 0)
        if count <= 0:
            continue

        action = ATTENTION_ACTIONS[label]
        breakdown.append(
            {
                "key": key,
                "label": label,
                "count": count,
                "owner": action["owner"],
                "action": action["action"],
            }
        )

    exception_count = sum(1 for item in items if item["exception_count"] > 0)
    if exception_count > 0:
        action = ATTENTION_ACTIONS["Open exception"]
        breakdown.append(
            {
                "key": "exception_count",
                "label": "Open exception",
                "count": exception_count,
                "owner": action["owner"],
                "action": action["action"],
            }
        )

    return breakdown


def _journey(
    summary: dict[str, Any], items: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    completed_outcome_count = int(summary["completed_outcome_count"])
    journey = [
        {
            "step": "Completed outcome",
            "ready_count": completed_outcome_count,
            "missing_count": 0,
            "completion_rate": (
                Decimal("1") if completed_outcome_count else Decimal("0")
            ),
        }
    ]
    journey.extend(
        _step_summary(
            key=key,
            label=label,
            completed_outcome_count=completed_outcome_count,
            items=items,
        )
        for key, label in MONEY_STEPS
    )
    journey.append(
        {
            "step": "Open exception",
            "ready_count": int(summary["exception_count"]),
            "missing_count": max(
                completed_outcome_count - int(summary["exception_count"]), 0
            ),
            "completion_rate": _rate(
                int(summary["exception_count"]), completed_outcome_count
            ),
        }
    )
    return journey


async def get_outcome_money_map(
    *,
    tenant_code: str | None = None,
    sponsor_code: str | None = None,
    distributor_code: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    clamped_limit = max(1, min(limit, 250))

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            WITH completed AS (
                SELECT
                    ri.referral_track_id,
                    ri.tenant_code,
                    ri.referrer_ucn,
                    ri.status,
                    ri.product,
                    ri.sub_product,
                    ri.journey_code,
                    ri.completed_at,
                    ri.updated_at
                FROM referral_instances ri
                WHERE ri.is_complete = TRUE
                  AND ($1::text IS NULL OR ri.tenant_code = $1)
            ),
            linked_context AS (
                SELECT
                    l.referral_track_id,
                    MAX(o.sponsor_code) AS sponsor_code,
                    MAX(o.campaign_code) AS campaign_code,
                    MAX(o.opportunity_code) AS opportunity_code,
                    MAX(o.title) AS opportunity_title,
                    MAX(d.distributor_code) AS distributor_code,
                    MAX(d.distributor_name) AS distributor_name
                FROM distribution_route_referral_links l
                JOIN distribution_opportunities o
                  ON o.opportunity_id = l.opportunity_id
                JOIN distribution_distributors d
                  ON d.distributor_id = l.distributor_id
                WHERE l.link_status = 'ACTIVE'
                GROUP BY l.referral_track_id
            ),
            rewards AS (
                SELECT
                    rr.referral_track_id,
                    COUNT(*) AS reward_count,
                    COALESCE(SUM(rr.amount), 0) AS reward_amount
                FROM referral_rewards rr
                JOIN completed c
                  ON c.referral_track_id = rr.referral_track_id
                GROUP BY rr.referral_track_id
            ),
            commissions AS (
                SELECT
                    c.referral_track_id,
                    COUNT(DISTINCT ce.commission_event_id) AS commission_count,
                    COALESCE(SUM(ce.commission_amount), 0) AS commission_amount
                FROM completed c
                JOIN distribution_commission_events ce
                  ON ce.tenant_code = c.tenant_code
                 AND (
                    ce.source_event_id = c.referral_track_id::text
                    OR ce.correlation_id = c.referral_track_id::text
                 )
                GROUP BY c.referral_track_id
            ),
            wallet_movements AS (
                SELECT
                    c.referral_track_id,
                    COUNT(DISTINCT wl.ledger_id) AS wallet_movement_count,
                    COALESCE(SUM(wl.amount), 0) AS wallet_movement_amount
                FROM completed c
                JOIN distribution_distributor_wallet_ledger wl
                  ON wl.tenant_code = c.tenant_code
                 AND (
                    wl.correlation_id = c.referral_track_id::text
                    OR wl.metadata->>'source_event_id' = c.referral_track_id::text
                 )
                GROUP BY c.referral_track_id
            ),
            invoices AS (
                SELECT
                    rr.referral_track_id,
                    COUNT(DISTINCT sil.invoice_id) AS invoice_count,
                    COALESCE(SUM(sil.line_amount), 0) AS invoiced_amount
                FROM referral_rewards rr
                JOIN sponsor_invoice_lines sil
                  ON sil.reward_id = rr.reward_id
                JOIN completed c
                  ON c.referral_track_id = rr.referral_track_id
                GROUP BY rr.referral_track_id
            ),
            settlements AS (
                SELECT
                    rr.referral_track_id,
                    COUNT(DISTINCT fsl.settlement_id) AS settlement_count,
                    COUNT(DISTINCT fsl.settlement_id) FILTER (WHERE fsl.status = 'SETTLED') AS settled_count,
                    COALESCE(SUM(fsl.amount) FILTER (WHERE fsl.status = 'SETTLED'), 0) AS settled_amount
                FROM referral_rewards rr
                JOIN fulfilment_settlement_ledger fsl
                  ON fsl.reward_id = rr.reward_id
                JOIN completed c
                  ON c.referral_track_id = rr.referral_track_id
                GROUP BY rr.referral_track_id
            ),
            exceptions AS (
                SELECT
                    rr.referral_track_id,
                    COUNT(DISTINCT se.exception_id) AS exception_count,
                    ARRAY_AGG(DISTINCT se.exception_id) AS open_exception_ids
                FROM referral_rewards rr
                JOIN fulfilment_settlement_ledger fsl
                  ON fsl.reward_id = rr.reward_id
                JOIN settlement_exceptions se
                  ON se.settlement_id = fsl.settlement_id
                 AND se.status = 'OPEN'
                JOIN completed c
                  ON c.referral_track_id = rr.referral_track_id
                GROUP BY rr.referral_track_id
            )
            SELECT
                c.referral_track_id,
                c.tenant_code,
                COALESCE(lc.distributor_code, c.referrer_ucn) AS distributor_code,
                lc.distributor_name,
                lc.sponsor_code,
                lc.campaign_code,
                lc.opportunity_code,
                lc.opportunity_title,
                c.product,
                c.sub_product,
                c.journey_code,
                c.status,
                c.completed_at,
                COALESCE(r.reward_count, 0) AS reward_count,
                COALESCE(r.reward_amount, 0) AS reward_amount,
                COALESCE(cm.commission_count, 0) AS commission_count,
                COALESCE(cm.commission_amount, 0) AS commission_amount,
                COALESCE(wm.wallet_movement_count, 0) AS wallet_movement_count,
                COALESCE(wm.wallet_movement_amount, 0) AS wallet_movement_amount,
                COALESCE(inv.invoice_count, 0) AS invoice_count,
                COALESCE(inv.invoiced_amount, 0) AS invoiced_amount,
                COALESCE(st.settlement_count, 0) AS settlement_count,
                COALESCE(st.settled_count, 0) AS settled_count,
                COALESCE(st.settled_amount, 0) AS settled_amount,
                COALESCE(ex.exception_count, 0) AS exception_count,
                COALESCE(ex.open_exception_ids, ARRAY[]::uuid[]) AS open_exception_ids
            FROM completed c
            LEFT JOIN linked_context lc
              ON lc.referral_track_id = c.referral_track_id
            LEFT JOIN rewards r
              ON r.referral_track_id = c.referral_track_id
            LEFT JOIN commissions cm
              ON cm.referral_track_id = c.referral_track_id
            LEFT JOIN wallet_movements wm
              ON wm.referral_track_id = c.referral_track_id
            LEFT JOIN invoices inv
              ON inv.referral_track_id = c.referral_track_id
            LEFT JOIN settlements st
              ON st.referral_track_id = c.referral_track_id
            LEFT JOIN exceptions ex
              ON ex.referral_track_id = c.referral_track_id
            WHERE ($2::text IS NULL OR lc.sponsor_code = $2)
              AND (
                $3::text IS NULL
                OR lc.distributor_code = $3
                OR c.referrer_ucn = $3
              )
            ORDER BY c.completed_at DESC NULLS LAST, c.updated_at DESC NULLS LAST
            LIMIT $4
            """,
            tenant_code,
            sponsor_code,
            distributor_code,
            clamped_limit,
        )

    items = [_normalise_item(row) for row in rows]
    summary = _summarise(items)

    return {
        "tenant_code": tenant_code,
        "sponsor_code": sponsor_code,
        "distributor_code": distributor_code,
        "limit": clamped_limit,
        "summary": summary,
        "journey": _journey(summary, items),
        "items": items,
    }


def _role_item_review(
    item: dict[str, Any],
    *,
    owned_steps: set[str],
    owner: str,
) -> dict[str, Any]:
    missing_steps = [
        step for step in item.get("missing_steps", []) if step in owned_steps
    ]
    owned_actions = [
        action
        for action in item.get("repair_actions", [])
        if action.get("owner") == owner
    ]
    admin_actions = [
        action
        for action in item.get("repair_actions", [])
        if action.get("owner") == "Amplifi Admin"
    ]
    status_value = "ATTENTION" if missing_steps else "READY"
    if item.get("exception_count", 0) > 0 and not missing_steps:
        status_value = "ADMIN_REVIEW"

    return {
        "referral_track_id": item.get("referral_track_id"),
        "tenant_code": item.get("tenant_code"),
        "sponsor_code": item.get("sponsor_code"),
        "distributor_code": item.get("distributor_code"),
        "distributor_name": item.get("distributor_name"),
        "campaign_code": item.get("campaign_code"),
        "opportunity_code": item.get("opportunity_code"),
        "opportunity_title": item.get("opportunity_title"),
        "product": item.get("product"),
        "journey_code": item.get("journey_code"),
        "completed_at": item.get("completed_at"),
        "money_status": item.get("money_status"),
        "review_status": status_value,
        "missing_owned_steps": missing_steps,
        "owned_actions": owned_actions,
        "admin_follow_up": admin_actions,
        "reward_amount": item.get("reward_amount"),
        "commission_amount": item.get("commission_amount"),
        "wallet_movement_amount": item.get("wallet_movement_amount"),
        "invoiced_amount": item.get("invoiced_amount"),
        "settled_amount": item.get("settled_amount"),
        "counts": {
            "rewards": item.get("reward_count", 0),
            "commissions": item.get("commission_count", 0),
            "wallet_movements": item.get("wallet_movement_count", 0),
            "invoices": item.get("invoice_count", 0),
            "settled": item.get("settled_count", 0),
            "exceptions": item.get("exception_count", 0),
        },
    }


def _role_review_from_money_map(
    money_map: dict[str, Any],
    *,
    role_key: str,
) -> dict[str, Any]:
    config = ROLE_REVIEW_STEPS[role_key]
    owner = str(config["filter_owner"])
    owned_steps = set(config["owned_steps"])
    items = [
        _role_item_review(item, owned_steps=owned_steps, owner=owner)
        for item in money_map.get("items", [])
    ]
    attention_items = [item for item in items if item["review_status"] == "ATTENTION"]
    admin_review_items = [
        item for item in items if item["review_status"] == "ADMIN_REVIEW"
    ]
    ready_count = sum(1 for item in items if item["review_status"] == "READY")

    return {
        "surface": config["surface"],
        "tenant_code": money_map.get("tenant_code"),
        "sponsor_code": money_map.get("sponsor_code"),
        "distributor_code": money_map.get("distributor_code"),
        "limit": money_map.get("limit"),
        "summary": {
            "completed_outcome_count": len(items),
            "ready_count": ready_count,
            "attention_count": len(attention_items),
            "admin_review_count": len(admin_review_items),
            "money_completion_rate": _rate(ready_count, len(items)),
        },
        "owned_steps": list(owned_steps),
        "items": items,
        "attention_items": attention_items[:10],
        "guardrails": [
            config["summary"],
            "This view is read-only for role users; Admin owns repair execution and settlement exception resolution.",
            config["next_action"],
        ],
    }


async def get_producer_outcome_money_review(
    *,
    tenant_code: str,
    producer_code: str,
    limit: int = 100,
) -> dict[str, Any]:
    money_map = await get_outcome_money_map(
        tenant_code=tenant_code.strip().upper(),
        sponsor_code=producer_code.strip().upper(),
        limit=limit,
    )
    return _role_review_from_money_map(money_map, role_key="PRODUCER_SUPPLY")


async def get_distributor_outcome_money_review(
    *,
    tenant_code: str,
    distributor_code: str,
    limit: int = 100,
) -> dict[str, Any]:
    money_map = await get_outcome_money_map(
        tenant_code=tenant_code.strip().upper(),
        distributor_code=distributor_code.strip().upper(),
        limit=limit,
    )
    return _role_review_from_money_map(money_map, role_key="DISTRIBUTOR_DEMAND")


async def resolve_outcome_settlement_exceptions(
    *,
    referral_track_id: str,
    resolved_by: str,
    tenant_code: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            UPDATE settlement_exceptions se
            SET
                status = 'RESOLVED',
                resolved_at = NOW(),
                resolved_by = $2
            FROM fulfilment_settlement_ledger fsl
            JOIN referral_rewards rr
              ON rr.reward_id = fsl.reward_id
            WHERE se.settlement_id = fsl.settlement_id
              AND rr.referral_track_id = $1::uuid
              AND se.status = 'OPEN'
              AND ($3::text IS NULL OR rr.tenant_code = $3)
            RETURNING
                se.exception_id,
                se.batch_id,
                se.settlement_id,
                se.exception_type,
                se.severity,
                se.status,
                se.exception_message,
                se.correlation_id,
                se.created_at,
                se.resolved_at,
                se.resolved_by
            """,
            referral_track_id,
            resolved_by,
            tenant_code,
        )

    items = [_serialize(row) for row in rows]
    return {
        "referral_track_id": referral_track_id,
        "tenant_code": tenant_code,
        "resolved_count": len(items),
        "items": items,
    }


async def create_outcome_reward_evidence(
    *,
    referral_track_id: str,
    created_by: str,
    tenant_code: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            WITH completed AS (
                SELECT
                    ri.referral_track_id,
                    ri.tenant_code,
                    ri.product,
                    ri.sub_product
                FROM referral_instances ri
                WHERE ri.referral_track_id = $1::uuid
                  AND ri.is_complete = TRUE
                  AND ($2::text IS NULL OR ri.tenant_code = $2)
            ),
            policy AS (
                SELECT
                    c.referral_track_id,
                    c.tenant_code,
                    c.product,
                    rp.reward_type,
                    CASE
                        WHEN rp.referrer_reward_amount > 0 THEN rp.referrer_reward_amount
                        WHEN rp.allow_referee_reward THEN rp.referee_reward_amount
                        ELSE 0
                    END AS reward_amount
                FROM completed c
                JOIN LATERAL (
                    SELECT *
                    FROM reward_policies rp
                    WHERE rp.product = c.product
                      AND rp.is_active = TRUE
                      AND (
                        rp.sub_product IS NULL
                        OR rp.sub_product = c.sub_product
                      )
                    ORDER BY
                        CASE WHEN rp.sub_product = c.sub_product THEN 0 ELSE 1 END,
                        rp.updated_at DESC,
                        rp.created_at DESC
                    LIMIT 1
                ) rp ON TRUE
            ),
            repair_insert AS (
                INSERT INTO referral_rewards (
                    referral_track_id,
                    reward_type,
                    product,
                    amount,
                    tenant_code
                )
                SELECT
                    p.referral_track_id,
                    p.reward_type,
                    p.product,
                    p.reward_amount,
                    p.tenant_code
                FROM policy p
                WHERE p.reward_amount > 0
                ON CONFLICT (referral_track_id, reward_type) DO NOTHING
                RETURNING
                    reward_id,
                    referral_track_id,
                    reward_type,
                    product,
                    amount,
                    tenant_code,
                    created_at
            )
            SELECT *
            FROM repair_insert
            """,
            referral_track_id,
            tenant_code,
        )

    items = [_serialize(row) for row in rows]
    return {
        "referral_track_id": referral_track_id,
        "tenant_code": tenant_code,
        "reward_count": len(items),
        "reward_amount": sum(
            (_decimal(item.get("amount")) for item in items), Decimal("0")
        ),
        "items": items,
    }


async def create_outcome_commission_evidence(
    *,
    referral_track_id: str,
    created_by: str,
    tenant_code: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            WITH context AS (
                SELECT
                    ri.referral_track_id,
                    ri.tenant_code,
                    ri.product,
                    ri.sub_product,
                    rr.reward_id,
                    rr.amount AS reward_amount,
                    d.distributor_id,
                    d.distributor_code,
                    d.distributor_type,
                    o.sponsor_code,
                    o.campaign_code,
                    o.commission_rule_id,
                    o.estimated_commission_amount,
                    w.wallet_id
                FROM referral_instances ri
                JOIN referral_rewards rr
                  ON rr.referral_track_id = ri.referral_track_id
                JOIN distribution_route_referral_links l
                  ON l.referral_track_id = ri.referral_track_id
                 AND l.link_status = 'ACTIVE'
                JOIN distribution_distributors d
                  ON d.distributor_id = l.distributor_id
                JOIN distribution_opportunities o
                  ON o.opportunity_id = l.opportunity_id
                LEFT JOIN distribution_distributor_wallets w
                  ON w.distributor_id = d.distributor_id
                 AND w.status = 'ACTIVE'
                 AND w.currency = 'ZAR'
                LEFT JOIN distribution_commission_events existing
                  ON existing.tenant_code = ri.tenant_code
                 AND (
                    existing.source_event_id = ri.referral_track_id::text
                    OR existing.correlation_id = ri.referral_track_id::text
                 )
                WHERE ri.referral_track_id = $1::uuid
                  AND ri.is_complete = TRUE
                  AND existing.commission_event_id IS NULL
                  AND ($2::text IS NULL OR ri.tenant_code = $2)
            ),
            rule AS (
                SELECT
                    c.*,
                    r.rule_id,
                    r.commission_type,
                    r.rate,
                    r.fixed_amount,
                    r.min_commission,
                    r.max_commission,
                    r.currency
                FROM context c
                JOIN LATERAL (
                    SELECT *
                    FROM distribution_commission_rules r
                    WHERE r.tenant_code = c.tenant_code
                      AND r.rule_status = 'ACTIVE'
                      AND (
                        c.commission_rule_id IS NULL
                        OR r.rule_id = c.commission_rule_id
                      )
                      AND (r.sponsor_code IS NULL OR r.sponsor_code = c.sponsor_code)
                      AND (r.campaign_code IS NULL OR r.campaign_code = c.campaign_code)
                      AND (r.distributor_type IS NULL OR r.distributor_type = c.distributor_type)
                    ORDER BY
                        CASE WHEN r.rule_id = c.commission_rule_id THEN 0 ELSE 1 END,
                        CASE WHEN r.sponsor_code IS NULL THEN 1 ELSE 0 END,
                        CASE WHEN r.campaign_code IS NULL THEN 1 ELSE 0 END,
                        CASE WHEN r.distributor_type IS NULL THEN 1 ELSE 0 END,
                        r.priority ASC,
                        r.created_at DESC
                    LIMIT 1
                ) r ON TRUE
            ),
            calculated AS (
                SELECT
                    *,
                    ROUND(
                        CASE
                            WHEN commission_type = 'PERCENTAGE' THEN COALESCE(reward_amount, 0) * COALESCE(rate, 0)
                            WHEN commission_type = 'FIXED' THEN COALESCE(fixed_amount, 0)
                            WHEN commission_type = 'HYBRID' THEN COALESCE(fixed_amount, 0) + COALESCE(reward_amount, 0) * COALESCE(rate, 0)
                            ELSE COALESCE(estimated_commission_amount, 0)
                        END,
                        2
                    ) AS raw_commission_amount
                FROM rule
            ),
            bounded AS (
                SELECT
                    *,
                    LEAST(
                        COALESCE(max_commission, raw_commission_amount),
                        GREATEST(COALESCE(min_commission, raw_commission_amount), raw_commission_amount)
                    ) AS commission_amount
                FROM calculated
            ),
            commission_insert AS (
                INSERT INTO distribution_commission_events (
                    commission_event_id,
                    tenant_code,
                    distributor_id,
                    distributor_code,
                    wallet_id,
                    rule_id,
                    sponsor_code,
                    campaign_code,
                    source_event_id,
                    activity_type,
                    sale_amount,
                    commission_amount,
                    currency,
                    commission_status,
                    correlation_id,
                    metadata
                )
                SELECT
                    gen_random_uuid(),
                    b.tenant_code,
                    b.distributor_id,
                    b.distributor_code,
                    b.wallet_id,
                    b.rule_id,
                    b.sponsor_code,
                    b.campaign_code,
                    b.referral_track_id::text,
                    'COMPLETED_OUTCOME_REPAIR',
                    COALESCE(b.reward_amount, 0),
                    b.commission_amount,
                    COALESCE(b.currency, 'ZAR'),
                    'CALCULATED',
                    b.referral_track_id::text,
                    jsonb_build_object(
                        'source', 'OUTCOME_MONEY_REPAIR',
                        'created_by', $3::text,
                        'reward_id', b.reward_id::text
                    )
                FROM bounded b
                WHERE b.commission_amount > 0
                ON CONFLICT (tenant_code, source_event_id) DO NOTHING
                RETURNING
                    commission_event_id,
                    tenant_code,
                    distributor_id,
                    distributor_code,
                    wallet_id,
                    rule_id,
                    sponsor_code,
                    campaign_code,
                    source_event_id,
                    activity_type,
                    sale_amount,
                    commission_amount,
                    currency,
                    commission_status,
                    correlation_id,
                    metadata,
                    created_at
            )
            SELECT *
            FROM commission_insert
            """,
            referral_track_id,
            tenant_code,
            created_by,
        )

    items = [_serialize(row) for row in rows]
    return {
        "referral_track_id": referral_track_id,
        "tenant_code": tenant_code,
        "commission_count": len(items),
        "commission_amount": sum(
            (_decimal(item.get("commission_amount")) for item in items), Decimal("0")
        ),
        "items": items,
    }


async def create_outcome_wallet_evidence(
    *,
    referral_track_id: str,
    created_by: str,
    tenant_code: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        async with conn.transaction():
            rows = await conn.fetch(
                """
                WITH context AS (
                    SELECT
                        ce.commission_event_id,
                        ce.tenant_code,
                        ce.distributor_id,
                        ce.distributor_code,
                        ce.commission_amount,
                        ce.source_event_id,
                        w.wallet_id,
                        w.available_balance
                    FROM distribution_commission_events ce
                    JOIN distribution_distributor_wallets w
                      ON w.distributor_id = ce.distributor_id
                     AND w.status = 'ACTIVE'
                     AND w.currency = ce.currency
                    LEFT JOIN distribution_distributor_wallet_ledger existing
                      ON existing.tenant_code = ce.tenant_code
                     AND (
                        existing.correlation_id = ce.source_event_id
                        OR existing.metadata->>'source_event_id' = ce.source_event_id
                     )
                    WHERE ce.source_event_id = $1
                      AND existing.ledger_id IS NULL
                      AND ($2::text IS NULL OR ce.tenant_code = $2)
                    FOR UPDATE OF w
                ),
                wallet_update AS (
                    UPDATE distribution_distributor_wallets w
                    SET
                        current_balance = w.current_balance + c.commission_amount,
                        available_balance = w.available_balance + c.commission_amount,
                        updated_at = NOW()
                    FROM context c
                    WHERE w.wallet_id = c.wallet_id
                    RETURNING
                        c.commission_event_id,
                        c.tenant_code,
                        c.distributor_id,
                        c.distributor_code,
                        c.commission_amount,
                        c.source_event_id,
                        c.wallet_id,
                        c.available_balance AS balance_before,
                        w.available_balance AS balance_after
                ),
                ledger_insert AS (
                    INSERT INTO distribution_distributor_wallet_ledger (
                        ledger_id,
                        wallet_id,
                        distributor_id,
                        tenant_code,
                        transaction_type,
                        amount,
                        balance_before,
                        balance_after,
                        correlation_id,
                        metadata
                    )
                    SELECT
                        gen_random_uuid(),
                        wu.wallet_id,
                        wu.distributor_id,
                        wu.tenant_code,
                        'CREDIT',
                        wu.commission_amount,
                        wu.balance_before,
                        wu.balance_after,
                        wu.source_event_id,
                        jsonb_build_object(
                            'source', 'OUTCOME_MONEY_REPAIR',
                            'created_by', $3::text,
                            'commission_event_id', wu.commission_event_id::text,
                            'source_event_id', wu.source_event_id
                        )
                    FROM wallet_update wu
                    RETURNING
                        ledger_id,
                        wallet_id,
                        distributor_id,
                        tenant_code,
                        transaction_type,
                        amount,
                        balance_before,
                        balance_after,
                        correlation_id,
                        metadata,
                        created_at
                )
                UPDATE distribution_commission_events ce
                SET
                    wallet_id = li.wallet_id,
                    commission_status = 'CREDITED',
                    credited_at = NOW(),
                    updated_at = NOW()
                FROM ledger_insert li
                WHERE ce.commission_event_id = (li.metadata->>'commission_event_id')::uuid
                RETURNING
                    li.ledger_id,
                    li.wallet_id,
                    li.distributor_id,
                    li.tenant_code,
                    li.transaction_type,
                    li.amount,
                    li.balance_before,
                    li.balance_after,
                    li.correlation_id,
                    li.metadata,
                    li.created_at
                """,
                referral_track_id,
                tenant_code,
                created_by,
            )

    items = [_serialize(row) for row in rows]
    return {
        "referral_track_id": referral_track_id,
        "tenant_code": tenant_code,
        "wallet_movement_count": len(items),
        "wallet_movement_amount": sum(
            (_decimal(item.get("amount")) for item in items), Decimal("0")
        ),
        "items": items,
    }


async def create_outcome_invoice_evidence(
    *,
    referral_track_id: str,
    created_by: str,
    tenant_code: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            WITH context AS (
                SELECT
                    ri.referral_track_id,
                    ri.tenant_code,
                    MAX(o.sponsor_code) AS sponsor_code,
                    (ARRAY_AGG(o.funding_contract_id) FILTER (WHERE o.funding_contract_id IS NOT NULL))[1]
                        AS funding_contract_id,
                    MAX(o.opportunity_code) AS opportunity_code,
                    MAX(o.title) AS opportunity_title
                FROM referral_instances ri
                JOIN distribution_route_referral_links l
                  ON l.referral_track_id = ri.referral_track_id
                 AND l.link_status = 'ACTIVE'
                JOIN distribution_opportunities o
                  ON o.opportunity_id = l.opportunity_id
                WHERE ri.referral_track_id = $1::uuid
                  AND ri.is_complete = TRUE
                  AND ($2::text IS NULL OR ri.tenant_code = $2)
                GROUP BY ri.referral_track_id, ri.tenant_code
            ),
            rewards_without_invoice AS (
                SELECT
                    rr.reward_id,
                    rr.amount
                FROM referral_rewards rr
                JOIN context c
                  ON c.referral_track_id = rr.referral_track_id
                LEFT JOIN sponsor_invoice_lines sil
                  ON sil.reward_id = rr.reward_id
                WHERE sil.line_id IS NULL
            ),
            invoice_insert AS (
                INSERT INTO sponsor_invoices (
                    tenant_code,
                    sponsor_code,
                    sponsor_name,
                    contract_id,
                    invoice_number,
                    invoice_period_start,
                    invoice_period_end,
                    due_date,
                    currency,
                    subtotal_amount,
                    vat_amount,
                    total_amount,
                    outstanding_amount,
                    status,
                    metadata
                )
                SELECT
                    c.tenant_code,
                    c.sponsor_code,
                    c.sponsor_code,
                    c.funding_contract_id,
                    'REPAIR-' || SUBSTRING(c.referral_track_id::text, 1, 8)
                        || '-' || TO_CHAR(clock_timestamp(), 'YYYYMMDDHH24MISSMS'),
                    CURRENT_DATE,
                    CURRENT_DATE,
                    CURRENT_DATE + INTERVAL '7 days',
                    'ZAR',
                    COALESCE(SUM(r.amount), 0),
                    0,
                    COALESCE(SUM(r.amount), 0),
                    COALESCE(SUM(r.amount), 0),
                    'DRAFT',
                    jsonb_build_object(
                        'source', 'OUTCOME_MONEY_REPAIR',
                        'created_by', $3::text,
                        'referral_track_id', c.referral_track_id::text,
                        'opportunity_code', c.opportunity_code
                    )
                FROM context c
                JOIN rewards_without_invoice r
                  ON TRUE
                WHERE c.sponsor_code IS NOT NULL
                GROUP BY
                    c.tenant_code,
                    c.sponsor_code,
                    c.funding_contract_id,
                    c.referral_track_id,
                    c.opportunity_code
                HAVING COUNT(r.reward_id) > 0
                RETURNING invoice_id
            ),
            line_insert AS (
                INSERT INTO sponsor_invoice_lines (
                    invoice_id,
                    line_type,
                    description,
                    quantity,
                    unit_amount,
                    line_amount,
                    reward_id,
                    metadata
                )
                SELECT
                    ii.invoice_id,
                    'UTILISATION',
                    'Completed customer outcome repair: ' || c.referral_track_id::text,
                    1,
                    COALESCE(r.amount, 0),
                    COALESCE(r.amount, 0),
                    r.reward_id,
                    jsonb_build_object(
                        'source', 'OUTCOME_MONEY_REPAIR',
                        'created_by', $3::text,
                        'referral_track_id', c.referral_track_id::text
                    )
                FROM invoice_insert ii
                JOIN context c
                  ON TRUE
                JOIN rewards_without_invoice r
                  ON TRUE
                RETURNING line_id, invoice_id, reward_id, line_amount
            )
            SELECT
                (SELECT invoice_id FROM invoice_insert LIMIT 1) AS invoice_id,
                COUNT(line_id) AS line_count,
                COALESCE(SUM(line_amount), 0) AS invoice_amount
            FROM line_insert
            """,
            referral_track_id,
            tenant_code,
            created_by,
        )

    result = _serialize(row)
    return {
        "referral_track_id": referral_track_id,
        "tenant_code": tenant_code,
        "invoice_id": result.get("invoice_id"),
        "line_count": _integer(result.get("line_count")),
        "invoice_amount": _decimal(result.get("invoice_amount")),
    }


async def create_outcome_settlement_evidence(
    *,
    referral_track_id: str,
    created_by: str,
    tenant_code: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            WITH eligible_rewards AS (
                SELECT
                    rr.reward_id,
                    rr.referral_track_id,
                    rr.tenant_code,
                    rr.reward_type,
                    rr.product,
                    rr.amount,
                    ri.referrer_ucn
                FROM referral_rewards rr
                JOIN referral_instances ri
                  ON ri.referral_track_id = rr.referral_track_id
                JOIN sponsor_invoice_lines sil
                  ON sil.reward_id = rr.reward_id
                LEFT JOIN fulfilment_settlement_ledger settled
                  ON settled.reward_id = rr.reward_id
                 AND settled.status = 'SETTLED'
                WHERE rr.referral_track_id = $1::uuid
                  AND ri.is_complete = TRUE
                  AND settled.settlement_id IS NULL
                  AND ($2::text IS NULL OR rr.tenant_code = $2)
                GROUP BY
                    rr.reward_id,
                    rr.referral_track_id,
                    rr.tenant_code,
                    rr.reward_type,
                    rr.product,
                    rr.amount,
                    ri.referrer_ucn
            ),
            audit_upsert AS (
                INSERT INTO fulfilment_audit (
                    tenant_code,
                    referral_track_id,
                    referrer_ucn,
                    referee_ucn,
                    reward_type,
                    fulfilment_provider,
                    idempotency_key,
                    status,
                    provider_reference,
                    provider_status,
                    provider_response,
                    correlation_id,
                    event_type,
                    completed_at
                )
                SELECT
                    er.tenant_code,
                    er.referral_track_id::text,
                    er.referrer_ucn,
                    er.referrer_ucn,
                    er.reward_type,
                    'OUTCOME_MONEY_REPAIR',
                    'outcome-money-settlement-repair:' || er.reward_id::text,
                    'SUCCESS',
                    'REPAIR-' || SUBSTRING(er.reward_id::text, 1, 8),
                    'REPAIRED',
                    jsonb_build_object(
                        'source', 'OUTCOME_MONEY_REPAIR',
                        'created_by', $3::text,
                        'referral_track_id', er.referral_track_id::text
                    ),
                    er.reward_id::text,
                    'OUTCOME_MONEY_SETTLEMENT_REPAIR',
                    NOW()
                FROM eligible_rewards er
                ON CONFLICT (idempotency_key) DO UPDATE
                SET updated_at = fulfilment_audit.updated_at
                RETURNING
                    audit_id,
                    correlation_id,
                    provider_reference
            ),
            settlement_insert AS (
                INSERT INTO fulfilment_settlement_ledger (
                    tenant_code,
                    reward_id,
                    audit_id,
                    provider_key,
                    provider_reference,
                    amount,
                    currency,
                    status,
                    settlement_date,
                    settled_at
                )
                SELECT
                    er.tenant_code,
                    er.reward_id,
                    au.audit_id,
                    'OUTCOME_MONEY_REPAIR',
                    au.provider_reference,
                    COALESCE(er.amount, 0),
                    'ZAR',
                    'SETTLED',
                    NOW(),
                    NOW()
                FROM eligible_rewards er
                JOIN audit_upsert au
                  ON au.correlation_id = er.reward_id::text
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM fulfilment_settlement_ledger existing
                    WHERE existing.reward_id = er.reward_id
                      AND existing.status = 'SETTLED'
                )
                RETURNING
                    settlement_id,
                    reward_id,
                    audit_id,
                    amount,
                    currency,
                    status,
                    settled_at
            )
            SELECT
                settlement_id,
                reward_id,
                audit_id,
                amount,
                currency,
                status,
                settled_at
            FROM settlement_insert
            """,
            referral_track_id,
            tenant_code,
            created_by,
        )

    items = [_serialize(row) for row in rows]
    return {
        "referral_track_id": referral_track_id,
        "tenant_code": tenant_code,
        "settlement_count": len(items),
        "settled_amount": sum(
            (_decimal(item.get("amount")) for item in items), Decimal("0")
        ),
        "items": items,
    }
