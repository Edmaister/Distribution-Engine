from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from utils.db import db_cursor
from utils.kafka import publish_event
from services import quality_service


# ---------- helpers ----------

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat().replace("+00:00", "Z") if dt else None


# ---------- state I/O ----------

def _get_state(referrer_hash: str) -> Optional[Dict[str, Any]]:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT state, decision, reason, starts_at, ends_at, updated_at
            FROM referrer_cooldown_state
            WHERE referrer_hash = %s
            """,
            (referrer_hash,),
        )
        row = cur.fetchone()

        if not row:
            return None

        state, decision, reason, s_at, e_at, u_at = row

        return {
            "state": state,
            "decision": decision,
            "reason": reason,
            "startsAt": s_at,
            "endsAt": e_at,
            "updatedAt": u_at,
        }


def _set_state(
    referrer_hash: str,
    state: str,
    decision: str,
    reason: str,
    starts_at: Optional[datetime],
    ends_at: Optional[datetime],
) -> None:
    now = _utcnow()

    with db_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO referrer_cooldown_state
                (referrer_hash, state, decision, reason, starts_at, ends_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (referrer_hash) DO UPDATE SET
                state = EXCLUDED.state,
                decision = EXCLUDED.decision,
                reason = EXCLUDED.reason,
                starts_at = EXCLUDED.starts_at,
                ends_at = EXCLUDED.ends_at,
                updated_at = EXCLUDED.updated_at
            """,
            (
                referrer_hash,
                state,
                decision,
                reason,
                starts_at,
                ends_at,
                now,
            ),
        )


# ---------- evaluator ----------

def evaluate(*, referrer_hash: str, policy: Dict[str, Any]) -> Dict[str, Any]:
    """Return decision/caps based on rolling quality metrics and policy rules.
    decision: ELIGIBLE | WARN | SOFT | HARD
    """

    rolling_days: int = int(policy.get("rolling_window_days", 60))
    rules = policy.get("rules", []) or []

    metrics = quality_service.get_metrics(
        referrer_hash=referrer_hash,
        window_days=rolling_days,
    )

    activations = int(metrics.get("activations", 0))
    qr = float(metrics.get("qr", 0.0))

    outcome = {
        "decision": "ELIGIBLE",
        "reason": "meets quality",
        "caps": {},
        "metrics": metrics,
    }

    decided = "ELIGIBLE"
    chosen_rule: Optional[Dict[str, Any]] = None

    for rule in rules:
        action = rule.get("action")
        min_acts = int(rule.get("minActivations", 0))
        qr_below = float(rule.get("qrBelow", 0))

        if activations >= min_acts and qr < qr_below:
            order = {"HARD": 3, "SOFT": 2, "WARN": 1}

            if order.get(action, 0) > order.get(decided, 0):
                decided = action
                chosen_rule = rule

    now = _utcnow()
    starts_at = None
    ends_at = None
    caps: Dict[str, Any] = {}

    if decided == "WARN":
        _set_state(referrer_hash, "ACTIVE", "WARN", "low quality", None, None)

        publish_event("referral-events", {
            "eventType": "COOLDOWN_REEVALUATED",
            "referrerHash": referrer_hash,
            "decision": "WARN",
            "reason": "low quality",
            "metrics": metrics,
            "at": _iso(now),
        })

        outcome.update({"decision": "WARN", "reason": "low quality"})
        return outcome

    if decided == "SOFT" and chosen_rule:
        duration = int(chosen_rule.get("durationDays", 14))
        caps = chosen_rule.get("caps", {}) or {}

        starts_at = now
        ends_at = now + timedelta(days=duration)

        _set_state(referrer_hash, "ACTIVE", "SOFT", "low quality", starts_at, ends_at)

        publish_event("referral-events", {
            "eventType": "COOLDOWN_REEVALUATED",
            "referrerHash": referrer_hash,
            "decision": "SOFT",
            "reason": "low quality",
            "caps": caps,
            "startsAt": _iso(starts_at),
            "endsAt": _iso(ends_at),
            "metrics": metrics,
            "at": _iso(now),
        })

        outcome.update({
            "decision": "SOFT",
            "reason": "low quality",
            "caps": caps,
            "startsAt": _iso(starts_at),
            "endsAt": _iso(ends_at),
        })

        return outcome

    if decided == "HARD" and chosen_rule:
        duration = int(chosen_rule.get("durationDays", 30))

        starts_at = now
        ends_at = now + timedelta(days=duration)

        _set_state(referrer_hash, "ACTIVE", "HARD", "low quality", starts_at, ends_at)

        publish_event("referral-events", {
            "eventType": "COOLDOWN_REEVALUATED",
            "referrerHash": referrer_hash,
            "decision": "HARD",
            "reason": "low quality",
            "startsAt": _iso(starts_at),
            "endsAt": _iso(ends_at),
            "metrics": metrics,
            "at": _iso(now),
        })

        outcome.update({
            "decision": "HARD",
            "reason": "low quality",
            "startsAt": _iso(starts_at),
            "endsAt": _iso(ends_at),
        })

        return outcome

    # ELIGIBLE
    _set_state(referrer_hash, "ACTIVE", "ELIGIBLE", "meets quality", None, None)

    publish_event("referral-events", {
        "eventType": "COOLDOWN_REEVALUATED",
        "referrerHash": referrer_hash,
        "decision": "ELIGIBLE",
        "reason": "meets quality",
        "metrics": metrics,
        "at": _iso(now),
    })

    return outcome