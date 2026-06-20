from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from utils.db import get_async_connection
from utils.kafka import publish_event


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def add_points(
    referrer_hash: str,
    points: int,
    reason: str,
    meta: Optional[Dict[str, Any]] = None,
) -> int:
    async with get_async_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO user_points (referrer_hash, points, reason, meta, created_at)
            VALUES ($1, $2, $3, $4::jsonb, NOW())
            RETURNING id
            """,
            referrer_hash,
            points,
            reason,
            json.dumps(meta or {}),
        )

    pid = int(row["id"])

    publish_event(
        "referral-events",
        {
            "eventType": "POINTS_ADDED",
            "referrerHash": referrer_hash,
            "points": points,
            "reason": reason,
            "meta": meta or {},
        },
    )

    return pid


async def get_progress(referrer_hash: str) -> Dict[str, Any]:
    async with get_async_connection() as conn:
        total_points = await conn.fetchval(
            """
            SELECT COALESCE(SUM(points),0)
            FROM user_points
            WHERE referrer_hash = $1
            """,
            referrer_hash,
        )

        total_referrals = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM referrals
            WHERE referrer_ucn_encrypted = $1
            """,
            referrer_hash,
        )

        total_rewards = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM referral_rewards r
            JOIN referrals f
              ON f.referral_track_id = r.referral_track_id
            WHERE f.referrer_ucn_encrypted = $1
            """,
            referrer_hash,
        )

        mission_rows = await conn.fetch(
            """
            SELECT
                m.mission_code,
                m.title,
                ump.status,
                COALESCE(ump.progress,0) AS progress,
                m.goal
            FROM user_mission_progress ump
            JOIN missions m
              ON m.mission_code = ump.mission_code
            WHERE ump.referrer_hash = $1
            """,
            referrer_hash,
        )

        badge_rows = await conn.fetch(
            """
            SELECT
                b.badge_code,
                b.title,
                ub.earned_at
            FROM user_badges ub
            JOIN badges b
              ON b.badge_code = ub.badge_code
            WHERE ub.referrer_hash = $1
            ORDER BY ub.earned_at DESC
            """,
            referrer_hash,
        )

    missions = [
        {
            "missionCode": row["mission_code"],
            "title": row["title"],
            "status": row["status"],
            "progress": int(row["progress"]),
            "goal": int(row["goal"]),
        }
        for row in mission_rows
    ]

    badges = [
        {
            "badgeCode": row["badge_code"],
            "title": row["title"],
            "earnedAt": row["earned_at"].isoformat()
            if row["earned_at"]
            else None,
        }
        for row in badge_rows
    ]

    return {
        "points": int(total_points or 0),
        "referrals": int(total_referrals or 0),
        "rewards": int(total_rewards or 0),
        "missions": missions,
        "badges": badges,
    }


async def ensure_mission_progress(referrer_hash: str, mission_code: str) -> None:
    async with get_async_connection() as conn:
        await conn.execute(
            """
            INSERT INTO user_mission_progress (
                referrer_hash,
                mission_code,
                status,
                progress,
                created_at,
                updated_at
            )
            VALUES ($1, $2, 'ACTIVE', 0, NOW(), NOW())
            ON CONFLICT (referrer_hash, mission_code) DO NOTHING
            """,
            referrer_hash,
            mission_code,
        )


async def increment_mission(
    referrer_hash: str,
    mission_code: str,
    inc: int = 1,
) -> None:
    async with get_async_connection() as conn:
        await conn.execute(
            """
            UPDATE user_mission_progress
               SET progress = progress + $1,
                   updated_at = NOW()
             WHERE referrer_hash = $2
               AND mission_code = $3
               AND status IN ('ACTIVE', 'STARTED')
            """,
            inc,
            referrer_hash,
            mission_code,
        )


async def complete_mission_if_goal(
    referrer_hash: str,
    mission_code: str,
) -> Optional[Dict[str, Any]]:
    async with get_async_connection() as conn:
        mission = await conn.fetchrow(
            """
            SELECT goal, reward_points
            FROM missions
            WHERE mission_code = $1
            """,
            mission_code,
        )

        if not mission:
            return None

        goal = int(mission["goal"])
        reward_points = int(mission["reward_points"] or 0)

        progress_row = await conn.fetchrow(
            """
            SELECT progress, status
            FROM user_mission_progress
            WHERE referrer_hash = $1
              AND mission_code = $2
            """,
            referrer_hash,
            mission_code,
        )

        if not progress_row:
            return None

        progress = int(progress_row["progress"])
        status = progress_row["status"]

        if status in ("COMPLETED", "REWARDED"):
            return None

        if progress < goal:
            return None

        completed_row = await conn.fetchrow(
            """
            UPDATE user_mission_progress
               SET status = 'COMPLETED',
                   completed_at = NOW(),
                   updated_at = NOW()
             WHERE referrer_hash = $1
               AND mission_code = $2
             RETURNING 1
            """,
            referrer_hash,
            mission_code,
        )

    if not completed_row:
        return None

    if reward_points > 0:
        await add_points(
            referrer_hash,
            reward_points,
            f"MISSION:{mission_code}",
            {"mission": mission_code},
        )

    publish_event(
        "referral-events",
        {
            "eventType": "MISSION_COMPLETED",
            "referrerHash": referrer_hash,
            "missionCode": mission_code,
        },
    )

    return {
        "missionCode": mission_code,
        "rewardPoints": reward_points,
    }


async def award_badge(referrer_hash: str, badge_code: str) -> bool:
    async with get_async_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO user_badges (referrer_hash, badge_code, earned_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (referrer_hash, badge_code) DO NOTHING
            RETURNING 1
            """,
            referrer_hash,
            badge_code,
        )

    created = row is not None

    if created:
        publish_event(
            "referral-events",
            {
                "eventType": "BADGE_AWARDED",
                "referrerHash": referrer_hash,
                "badgeCode": badge_code,
            },
        )

    return created


async def on_referral_created(referrer_hash: str) -> None:
    await ensure_mission_progress(referrer_hash, "INVITE_5")
    await increment_mission(referrer_hash, "INVITE_5", 1)
    await complete_mission_if_goal(referrer_hash, "INVITE_5")


async def on_reward_applied(referrer_hash: str, reward_type: str) -> None:
    await add_points(referrer_hash, 5, f"REWARD:{reward_type}")
    await ensure_mission_progress(referrer_hash, "EARN_3_REWARDS")
    await increment_mission(referrer_hash, "EARN_3_REWARDS", 1)
    await complete_mission_if_goal(referrer_hash, "EARN_3_REWARDS")