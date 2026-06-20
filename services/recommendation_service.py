from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from utils.db import db_connection


ACTION_AUDIENCE = {
    "SEND_INVITE": "REFERRER",
    "SHARE_QR": "REFERRER",
    "COMPLETE_MISSION": "REFERRER",
    "CLAIM_BADGE": "REFERRER",
    "COMPLETE_YOUR_APPLICATION": "SELF",
    "FUND_YOUR_ACCOUNT": "SELF",
    "ACTIVATE_YOUR_CARD": "SELF",
    "SWITCH_YOUR_SALARY": "SELF",
    "SWITCH_YOUR_DEBIT_ORDERS": "SELF",
    "PERFORM_A_TRANSACTION": "SELF",
    "APPLY_REWARD": "OPS",
    "INVESTIGATE_STALLED_REFERRAL": "OPS",
    "SUPPRESS_NUDGE": "SYSTEM",
}

QUALIFYING_REWARD_EVENTS = (
    "ACCOUNT_OPENED",
    "ACCOUNT_ACTIVATED",
    "FUNDED",
    "DEBIT_ORDER_SWITCHED",
    "SALARY_SWITCHED",
    "FIRST_TRANSACTION_COMPLETED",
)


def _utcnow():
    return datetime.now(timezone.utc)


def _iso(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _score(confidence, value=0.5, effort=0.5):
    return round((confidence * 0.6) + (value * 0.3) - (effort * 0.1), 3)


def _is_allowed(action, subject_role):
    audience = ACTION_AUDIENCE.get(action)

    if audience == "REFERRER":
        return True

    if audience == "SELF":
        return subject_role == "SELF"

    return audience in {"OPS", "SYSTEM"}


def _reason_codes(*codes):
    return [c for c in codes if c]


async def _get_referrer_ucn(referrer_hash: str):
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT referrer_ucn
            FROM referrer_codes
            WHERE referrer_ucn_hash = $1
            LIMIT 1
            """,
            referrer_hash,
        )

    return row["referrer_ucn"] if row else None


async def _closest_mission_for(referrer_hash: str):
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                m.mission_code,
                m.title,
                ump.progress,
                m.goal,
                m.reward_points
            FROM user_mission_progress ump
            JOIN missions m
              ON m.mission_code = ump.mission_code
            WHERE ump.referrer_hash = $1
              AND ump.status IN ('ACTIVE', 'STARTED')
            ORDER BY
              (CAST(ump.progress AS FLOAT) / NULLIF(m.goal, 0)) DESC NULLS LAST,
              m.goal ASC
            LIMIT 1
            """,
            referrer_hash,
        )

    if not row:
        return None

    progress = int(row["progress"] or 0)
    goal = int(row["goal"] or 0)
    reward_points = int(row["reward_points"] or 0)
    remaining = max(0, goal - progress)
    pct = float(progress) / float(goal or 1)
    confidence = round(min(0.95, pct + 0.2), 2)

    return {
        "action": "COMPLETE_MISSION",
        "audience": "REFERRER",
        "confidence": confidence,
        "priorityScore": _score(confidence, value=0.8, effort=0.2),
        "reason": f"Only {remaining} more to complete {row['title']}",
        "reasonCodes": _reason_codes("MISSION_NEAR_COMPLETE"),
        "meta": {
            "missionCode": row["mission_code"],
            "mission_code": row["mission_code"],
            "title": row["title"],
            "progress": progress,
            "goal": goal,
            "rewardPoints": reward_points,
            "reward_points": reward_points,
        },
    }


async def _hour_with_best_response(referrer_hash):
    try:
        async with db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT hour_of_day
                FROM mv_referrer_best_hour
                WHERE referrer_hash = $1
                ORDER BY hour_of_day ASC
                LIMIT 1
                """,
                referrer_hash,
            )

        return int(row["hour_of_day"]) if row else None

    except Exception:
        return None


async def _invite_nudge_for(referrer_hash):
    best_hour = await _hour_with_best_response(referrer_hash)

    return {
        "action": "SEND_INVITE",
        "audience": "REFERRER",
        "confidence": 0.58 if best_hour is not None else 0.50,
        "priorityScore": _score(
            0.58 if best_hour is not None else 0.50,
            value=0.60,
            effort=0.20,
        ),
        "reason": (
            "You have referral activity momentum"
            + (
                f" and {best_hour:02d}:00 is a strong response hour"
                if best_hour is not None
                else ""
            )
        ),
        "reasonCodes": _reason_codes(
            "REFERRAL_NUDGE",
            "BEST_HOUR_AVAILABLE" if best_hour is not None else "",
        ),
        "meta": {"bestHour": best_hour},
    }


async def _dangling_rewards(referrer_hash):
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                ri.referral_track_id,
                MAX(rpe.occurred_at) AS last_event_at,
                COUNT(*) AS qualifying_event_count
            FROM referrer_codes rc
            JOIN referral_instances ri
              ON ri.referrer_ucn = rc.referrer_ucn
            JOIN referral_progress_events rpe
              ON rpe.referral_track_id = ri.referral_track_id
            LEFT JOIN referral_rewards rr
              ON rr.referral_track_id = ri.referral_track_id
            WHERE rc.referrer_ucn_hash = $1
              AND rpe.event_type = ANY($2::text[])
              AND rr.referral_track_id IS NULL
            GROUP BY ri.referral_track_id
            ORDER BY last_event_at DESC
            LIMIT 1
            """,
            referrer_hash,
            list(QUALIFYING_REWARD_EVENTS),
        )

    if not row:
        return None

    return {
        "action": "APPLY_REWARD",
        "audience": "OPS",
        "confidence": 0.7,
        "priorityScore": _score(0.7, value=0.9, effort=0.1),
        "reason": "Qualifying progress exists but no reward has been applied yet",
        "reasonCodes": _reason_codes("QUALIFYING_EVENT_NO_REWARD"),
        "meta": {
            "referralTrackId": str(row["referral_track_id"]),
            "lastQualifyingEventAt": (
                _iso(row["last_event_at"]) if row["last_event_at"] else None
            ),
            "qualifyingEventCount": int(row["qualifying_event_count"] or 0),
        },
    }


async def _latest_self_referral(referrer_hash):
    referrer_ucn = await _get_referrer_ucn(referrer_hash)

    if not referrer_ucn:
        return None

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                ri.referral_track_id,
                ri.status,
                ri.created_at,
                ri.account_opened_at,
                ri.account_activated_at,
                ri.funded_at,
                ri.debit_order_switched_at,
                ri.salary_switched_at,
                ri.first_transaction_completed_at
            FROM referral_instances ri
            WHERE ri.referee_ucn = $1
            ORDER BY ri.created_at DESC
            LIMIT 1
            """,
            referrer_ucn,
        )

    if not row:
        return None

    return {
        "referralTrackId": str(row["referral_track_id"]),
        "status": row["status"],
        "createdAt": row["created_at"],
        "accountOpenedAt": row["account_opened_at"],
        "accountActivatedAt": row["account_activated_at"],
        "fundedAt": row["funded_at"],
        "debitOrderSwitchedAt": row["debit_order_switched_at"],
        "salarySwitchedAt": row["salary_switched_at"],
        "firstTransactionCompletedAt": row["first_transaction_completed_at"],
        "referral_track_id": str(row["referral_track_id"]),
        "account_opened_at": row["account_opened_at"],
        "account_activated_at": row["account_activated_at"],
        "funded_at": row["funded_at"],
        "debit_order_switched_at": row["debit_order_switched_at"],
        "salary_switched_at": row["salary_switched_at"],
        "first_transaction_completed_at": row["first_transaction_completed_at"],
    }


async def _self_actions_for(referrer_hash):
    journey = await _latest_self_referral(referrer_hash)

    if not journey:
        return []

    referral_track_id = journey.get("referralTrackId") or journey.get("referral_track_id")

    account_opened = journey.get("accountOpenedAt") or journey.get("account_opened_at")
    funded = journey.get("fundedAt") or journey.get("funded_at")
    activated = journey.get("accountActivatedAt") or journey.get("account_activated_at")
    debit_order = journey.get("debitOrderSwitchedAt") or journey.get("debit_order_switched_at")
    salary = journey.get("salarySwitchedAt") or journey.get("salary_switched_at")
    first_txn = (
        journey.get("firstTransactionCompletedAt")
        or journey.get("first_transaction_completed_at")
    )

    actions = []

    if not account_opened:
        actions.append(
            {
                "action": "COMPLETE_YOUR_APPLICATION",
                "audience": "SELF",
                "confidence": 0.75,
                "priorityScore": _score(0.75, value=0.8, effort=0.3),
                "reason": "Your own referral journey has started but the account is not opened yet",
                "reasonCodes": _reason_codes("SELF_ACCOUNT_NOT_OPENED"),
                "meta": {"referralTrackId": referral_track_id},
            }
        )
        return actions

    if not funded:
        actions.append(
            {
                "action": "FUND_YOUR_ACCOUNT",
                "audience": "SELF",
                "confidence": 0.78,
                "priorityScore": _score(0.78, value=0.85, effort=0.3),
                "reason": "Your account is open but not yet funded",
                "reasonCodes": _reason_codes("SELF_ACCOUNT_NOT_FUNDED"),
                "meta": {"referralTrackId": referral_track_id},
            }
        )
        return actions

    if not activated:
        actions.append(
            {
                "action": "ACTIVATE_YOUR_CARD",
                "audience": "SELF",
                "confidence": 0.72,
                "priorityScore": _score(0.72, value=0.75, effort=0.25),
                "reason": "Your account is funded but not yet activated",
                "reasonCodes": _reason_codes("SELF_ACCOUNT_NOT_ACTIVATED"),
                "meta": {"referralTrackId": referral_track_id},
            }
        )
        return actions

    if not debit_order:
        actions.append(
            {
                "action": "SWITCH_YOUR_DEBIT_ORDERS",
                "audience": "SELF",
                "confidence": 0.68,
                "priorityScore": _score(0.68, value=0.8, effort=0.5),
                "reason": "Your account is active; switching debit orders will deepen your banking relationship",
                "reasonCodes": _reason_codes("SELF_DEBIT_ORDER_NOT_SWITCHED"),
                "meta": {"referralTrackId": referral_track_id},
            }
        )

    if not salary:
        actions.append(
            {
                "action": "SWITCH_YOUR_SALARY",
                "audience": "SELF",
                "confidence": 0.66,
                "priorityScore": _score(0.66, value=0.82, effort=0.55),
                "reason": "Switching your salary can improve account stickiness and value",
                "reasonCodes": _reason_codes("SELF_SALARY_NOT_SWITCHED"),
                "meta": {"referralTrackId": referral_track_id},
            }
        )

    if not first_txn:
        actions.append(
            {
                "action": "PERFORM_A_TRANSACTION",
                "audience": "SELF",
                "confidence": 0.64,
                "priorityScore": _score(0.64, value=0.7, effort=0.2),
                "reason": "A first transaction confirms real account usage and deepens engagement",
                "reasonCodes": _reason_codes("SELF_FIRST_TRANSACTION_NOT_COMPLETED"),
                "meta": {"referralTrackId": referral_track_id},
            }
        )

    return actions


async def get_cached_recommendations(referrer_hash):
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT items, generated_at, ttl_seconds
            FROM recommendations_cache
            WHERE referrer_hash = $1
            """,
            referrer_hash,
        )

    if not row:
        return None

    items = row["items"]
    generated_at = row["generated_at"] or _utcnow()
    ttl_seconds = int(row["ttl_seconds"] or 0)

    if generated_at + timedelta(seconds=ttl_seconds) < _utcnow():
        return None

    return items


async def upsert_recommendations_cache(
    referrer_hash,
    items,
    ttl_seconds=86400,
):
    async with db_connection() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO recommendations_cache (
                    referrer_hash,
                    items,
                    generated_at,
                    ttl_seconds
                )
                VALUES ($1, $2::jsonb, NOW(), $3)
                ON CONFLICT (referrer_hash)
                DO UPDATE SET
                    items = EXCLUDED.items,
                    generated_at = NOW(),
                    ttl_seconds = EXCLUDED.ttl_seconds
                """,
                referrer_hash,
                json.dumps(items),
                ttl_seconds,
            )


async def recommend_for_referrer(
    referrer_hash,
    segment,
    tenant=None,
    subject_role="REFERRER",
    top_k=3,
    use_cache=True,
    cache_ttl_seconds=86400,
):
    if use_cache:
        cached = await get_cached_recommendations(referrer_hash)
        if cached:
            return cached

    candidates = []

    mission = await _closest_mission_for(referrer_hash)
    if mission:
        candidates.append(mission)

    invite = await _invite_nudge_for(referrer_hash)
    if invite:
        candidates.append(invite)

    candidates.extend(await _self_actions_for(referrer_hash))

    dangling_reward = await _dangling_rewards(referrer_hash)
    if dangling_reward:
        candidates.append(dangling_reward)

    ranked = sorted(
        [
            x
            for x in candidates
            if x
            and x.get("action")
            and _is_allowed(x["action"], subject_role)
        ],
        key=lambda x: x.get("priorityScore", 0),
        reverse=True,
    )

    primary = ranked[0] if ranked else None

    secondary = [
        x
        for x in ranked[1:]
        if x.get("audience") in {"REFERRER", "SELF"}
    ][: max(0, int(top_k or 3) - 1)]

    ops_actions = [x for x in ranked if x.get("audience") == "OPS"]

    result = {
        "referrerHash": referrer_hash,
        "generatedAt": _iso(_utcnow()),
        "subjectRole": subject_role,
        "primaryAction": primary,
        "secondaryActions": secondary,
        "opsActions": ops_actions,
    }

    if use_cache:
        await upsert_recommendations_cache(
            referrer_hash,
            result,
            ttl_seconds=cache_ttl_seconds,
        )

    return result


async def compute_campaign_insights(
    campaign_code,
    segment=None,
    tenant=None,
):
    return {
        "campaignCode": campaign_code,
        "segment": segment,
        "tenant": tenant,
        "metrics": {
            "scanned30d": 0,
            "validated30d": 0,
            "attributed30d": 0,
            "completed30d": 0,
        },
    }