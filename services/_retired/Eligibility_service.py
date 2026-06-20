from __future__ import annotations
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone

from utils.db import db_cursor
from services import policy_service, cooldown_service


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _exists(query: str, params: tuple) -> bool:
    with db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchone() is not None


def _scalar(query: str, params: tuple) -> int:
    with db_cursor() as cur:
        cur.execute(query, params)
        row = cur.fetchone()
        return int(row[0]) if row and row[0] is not None else 0


# Built-in defaults for legacy rewards
def _is_activated(referral_track_id: str) -> Tuple[bool, str]:
    if _exists(
        "SELECT 1 FROM referrals WHERE referral_track_id=%s AND status IN ('ACTIVATED','COMPLETED')",
        (referral_track_id,),
    ):
        return True, "Referral status is ACTIVATED/COMPLETED"

    if _exists(
        "SELECT 1 FROM enterprise_events WHERE referral_track_id=%s AND event_type = ANY(%s)",
        (referral_track_id, ["ACCOUNT_ACTIVATED", "REFERRAL_ACTIVATED"]),
    ):
        return True, "Activation event seen"

    return False, "No activation found"


def _event_count(referral_track_id: str, types: list[str], since: datetime) -> int:
    return _scalar(
        "SELECT COUNT(*) FROM enterprise_events WHERE referral_track_id=%s AND event_type = ANY(%s) AND occurred_at >= %s",
        (referral_track_id, types, since),
    )


def _months_with(referral_track_id: str, types: list[str], since: datetime) -> int:
    return _scalar(
        "SELECT COUNT(DISTINCT date_trunc('month', occurred_at)) FROM enterprise_events WHERE referral_track_id=%s AND event_type = ANY(%s) AND occurred_at >= %s",
        (referral_track_id, types, since),
    )


def _already_rewarded(referral_track_id: str, reward_type: str) -> bool:
    return _exists(
        "SELECT 1 FROM referral_rewards WHERE referral_track_id=%s AND reward_type=%s",
        (referral_track_id, reward_type),
    )


def _eval_product_rule(referral_track_id: str, rule: Dict[str, Any]) -> Tuple[bool, str]:
    kind = (rule.get("kind") or "").lower()

    if kind == "event_count":
        types = list(rule.get("eventTypes") or [])
        at_least = int(rule.get("atLeast", 1))
        since = _utcnow() - timedelta(days=int(rule.get("windowDays", 60)))
        cnt = _event_count(referral_track_id, types, since)
        return (cnt >= at_least, f"{cnt} {types} in {rule.get('windowDays', 60)}d >= {at_least}")

    if kind == "distinct_months":
        types = list(rule.get("eventTypes") or [])
        at_least = int(rule.get("atLeast", 1))
        since = _utcnow() - timedelta(days=int(rule.get("windowDays", 90)))
        months = _months_with(referral_track_id, types, since)
        return (months >= at_least, f"{months} months with {types} in {rule.get('windowDays', 90)}d >= {at_least}")

    if kind == "status_in":
        table = rule.get("table", "referrals")
        column = rule.get("column", "status")
        values = tuple(rule.get("values") or [])
        if not values:
            return False, "No values specified"

        ok = _exists(
            f"SELECT 1 FROM {table} WHERE referral_track_id=%s AND {column} = ANY(%s)",
            (referral_track_id, list(values)),
        )
        return ok, f"{table}.{column} in {values}"

    return False, f"Unknown rule kind '{kind}'"


def _check_product_rules(
    referral_track_id: str,
    prules_for_reward: list[Dict[str, Any]],
) -> Tuple[bool, str]:
    for r in prules_for_reward or []:
        ok, why = _eval_product_rule(referral_track_id, r)
        if not ok:
            return False, f"Failed: {why}"
    return True, "All rules satisfied"


def check(
    *,
    referral_track_id: str,
    referrer_hash: str,
    reward_type: Optional[str] = None,
    sticker: Optional[str] = None,
    product: Optional[str] = None,
    segment: Optional[str] = None,
    campaign_id: Optional[str] = None,
) -> Dict[str, Any]:
    policy = policy_service.get_effective_policy(
        sticker=sticker,
        segment=segment,
        campaign_id=campaign_id,
    )

    cd = cooldown_service.evaluate(
        referrer_hash=referrer_hash,
        policy=policy,
    )

    rt = (reward_type or "").upper()
    eligible, reason = True, "n/a"

    prules = policy.get("productRules") or {}
    rules_for_product = prules.get((product or "").upper(), {}) if product else {}
    rules_for_reward = rules_for_product.get(rt) or []

    if rules_for_reward:
        eligible, reason = _check_product_rules(
            referral_track_id,
            rules_for_reward,
        )
    else:
        if rt == "ACTIVATION":
            eligible, reason = _is_activated(referral_track_id)

        elif rt == "DEBIT_ORDER":
            since = _utcnow() - timedelta(
                days=int((policy.get("productWindows") or {}).get("debitOrderDays", 60))
            )
            cnt = _event_count(
                referral_track_id,
                ["DEBIT_ORDER_SWITCHED", "DEBIT_ORDER_MOVED"],
                since,
            )
            eligible, reason = (cnt >= 2, f"{cnt} debit-order events in window")

        elif rt == "SALARY":
            since = _utcnow() - timedelta(
                days=int((policy.get("productWindows") or {}).get("salaryDays", 90))
            )
            months = _months_with(
                referral_track_id,
                ["SALARY_DEPOSIT"],
                since,
            )
            eligible, reason = (months >= 2, f"{months} months with salary events in window")

        elif rt:
            eligible, reason = False, f"Unknown reward_type '{rt}'"

    if rt and _already_rewarded(referral_track_id, rt):
        eligible, reason = False, f"{rt} already rewarded"

    return {
        **cd,
        "productEligibility": {
            "rewardType": rt or None,
            "eligible": eligible,
            "reason": reason,
        },
    }