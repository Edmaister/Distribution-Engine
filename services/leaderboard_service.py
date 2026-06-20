from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from apps.core.cache import cache_delete_pattern, cache_get, cache_set
from services.journey_definitions import DEFAULT_JOURNEY_CODE, DEFAULT_JOURNEY_VERSION, get_journey_definition

try:
    from utils.db import async_db_connection
except ImportError:  # fallback if your helper has a different export name
    from utils.db import get_async_connection as async_db_connection


MISSION_CATEGORY_CORE = "CORE"
MISSION_CATEGORY_BOOST = "BOOST"
MISSION_CATEGORY_MILESTONE = "MILESTONE"

MISSION_POINTS = {
    "ACCOUNT_OPENED_CORE": 20,
    "ACCOUNT_ACTIVATED_CORE": 30,
    "ACCOUNT_FUNDED_CORE": 50,
    "FIRST_DEBIT_ORDER_SWITCH": 20,
    "FIRST_SALARY_SWITCH": 25,
    "FIRST_TRANSACTION_COMPLETED": 15,
    "COMPLETE_1_REFERRAL": 25,
    "COMPLETE_3_REFERRALS": 75,
    "COMPLETE_5_REFERRALS": 150,
}

LEADERBOARD_CACHE_TTL_SECONDS = 30


def _normalize_cache_part(value: str | None, default: str = "DEFAULT") -> str:
    if not value:
        return default
    cleaned = str(value).strip().upper()
    return cleaned or default


def _leaderboard_cache_key(
    leaderboard_code: str,
    tenant_code: str | None,
    limit: int,
    offset: int,
) -> str:
    tenant = _normalize_cache_part(tenant_code)
    code = _normalize_cache_part(leaderboard_code)
    return f"leaderboard:{tenant}:{code}:limit:{limit}:offset:{offset}"


def _leaderboard_cache_pattern(tenant_code: str | None = None) -> str:
    tenant = _normalize_cache_part(tenant_code)
    return f"leaderboard:{tenant}:*"


def invalidate_leaderboard_cache(tenant_code: str | None = None) -> None:
    cache_delete_pattern(_leaderboard_cache_pattern(tenant_code))


def _hash_referrer_ucn(referrer_ucn: str) -> str:
    return hashlib.sha256(referrer_ucn.encode("utf-8")).hexdigest()


def _row_to_dict(row: Any) -> Dict[str, Any]:
    return dict(row)


def get_rank_tier(total_score: int) -> str:
    if total_score >= 200:
        return "Platinum"
    if total_score >= 100:
        return "Gold"
    if total_score >= 50:
        return "Silver"
    if total_score > 0:
        return "Bronze"
    return "Newbie"


@dataclass
class ScoreBreakdown:
    total_score: int
    referral_score: int
    milestone_score: int
    bonus_score: int
    referrals_count: int
    completed_referrals_count: int
    last_event_at: Optional[Any]


async def get_referrer_display_name(referrer_ucn: str) -> str:
    async with async_db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT gaming_handle, sticker, referral_code
            FROM referrer_codes
            WHERE referrer_ucn = $1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            referrer_ucn,
        )

    if row:
        gaming_handle = row["gaming_handle"]
        sticker = row["sticker"]
        referral_code = row["referral_code"]

        if gaming_handle and str(gaming_handle).strip():
            return str(gaming_handle).strip()

        if sticker and str(sticker).strip():
            return str(sticker).strip()

        if referral_code and str(referral_code).strip():
            return str(referral_code).strip()

    suffix = referrer_ucn[-4:] if referrer_ucn else "0000"
    return f"Player-{suffix}"


async def get_active_leaderboard_definitions(
    tenant_code: str | None = None,
) -> List[Dict[str, Any]]:
    async with async_db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT leaderboard_code, leaderboard_name, description, scope_type,
                   subject_type, tenant_code, product, sub_product, journey_code,
                   journey_version, aggregation_method, normalization_enabled,
                   weighting_config_json, active, effective_from, effective_to
            FROM leaderboard_definitions
            WHERE active = TRUE
              AND ($1::text IS NULL OR tenant_code = $1)
              AND (effective_to IS NULL OR effective_to > NOW())
            ORDER BY leaderboard_code
            """,
            tenant_code,
        )

    return [_row_to_dict(row) for row in rows]


async def get_leaderboard_definition(
    leaderboard_code: str,
    tenant_code: str | None = None,
) -> Optional[Dict[str, Any]]:
    async with async_db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT leaderboard_code, leaderboard_name, description, scope_type,
                   subject_type, tenant_code, product, sub_product, journey_code,
                   journey_version, aggregation_method, normalization_enabled,
                   weighting_config_json, active, effective_from, effective_to
            FROM leaderboard_definitions
            WHERE leaderboard_code = $1
              AND ($2::text IS NULL OR tenant_code = $2)
              AND active = TRUE
              AND (effective_to IS NULL OR effective_to > NOW())
            """,
            leaderboard_code,
            tenant_code,
        )

    return _row_to_dict(row) if row else None


async def get_scoring_rules(
    leaderboard_code: str,
    tenant_code: str | None = None,
) -> List[Dict[str, Any]]:
    async with async_db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT id, leaderboard_code, journey_code, journey_version, product,
                   sub_product, milestone_code, score_type, score_value,
                   max_awards_per_referral, active, effective_from, effective_to
            FROM leaderboard_scoring_rules
            WHERE leaderboard_code = $1
              AND active = TRUE
              AND (effective_to IS NULL OR effective_to > NOW())
            ORDER BY score_type, milestone_code
            """,
            leaderboard_code,
        )

    return [_row_to_dict(row) for row in rows]


async def get_referrals_for_board(
    leaderboard: Dict[str, Any],
    referrer_ucn: Optional[str] = None,
) -> List[Dict[str, Any]]:
    sql = """
        SELECT referral_track_id, referrer_ucn, product, sub_product, status,
               validated_at, account_opened_at, account_activated_at, funded_at,
               debit_order_switched_at, salary_switched_at,
               first_transaction_completed_at, is_complete, completed_at,
               journey_code, journey_version, created_at, updated_at
        FROM referral_instances
        WHERE 1=1
    """
    params: List[Any] = []

    def add_param(value: Any) -> str:
        params.append(value)
        return f"${len(params)}"

    if referrer_ucn:
        sql += f" AND referrer_ucn = {add_param(referrer_ucn)}"

    if leaderboard.get("tenant_code"):
        sql += f" AND tenant_code = {add_param(leaderboard['tenant_code'])}"

    if leaderboard.get("product"):
        sql += f" AND UPPER(TRIM(product)) = UPPER(TRIM({add_param(leaderboard['product'])}))"

    if leaderboard.get("sub_product"):
        sql += f" AND UPPER(TRIM(sub_product)) = UPPER(TRIM({add_param(leaderboard['sub_product'])}))"

    if leaderboard.get("journey_code"):
        sql += f" AND UPPER(TRIM(journey_code)) = UPPER(TRIM({add_param(leaderboard['journey_code'])}))"

    if leaderboard.get("journey_version"):
        sql += f" AND UPPER(TRIM(journey_version)) = UPPER(TRIM({add_param(leaderboard['journey_version'])}))"

    sql += " ORDER BY referrer_ucn, updated_at NULLS LAST, created_at NULLS LAST"

    async with async_db_connection() as conn:
        rows = await conn.fetch(sql, *params)

    return [_row_to_dict(row) for row in rows]


async def get_completed_missions_for_referrer(
    referrer_ucn: str,
    leaderboard: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    sql = """
        SELECT ump.mission_code, ump.referral_track_id, ump.progress_count,
               ump.goal_count, ump.is_complete, ump.completed_at,
               COALESCE(md.mission_category, 'CORE') AS mission_category,
               md.product, md.sub_product
        FROM user_mission_progress ump
        JOIN mission_definitions md ON md.mission_code = ump.mission_code
        LEFT JOIN referral_instances ri ON ri.referral_track_id = ump.referral_track_id
        WHERE ump.beneficiary_type = 'REFERRER'
          AND ump.beneficiary_ref = $1
          AND ump.is_complete = TRUE
          AND md.is_active = TRUE
    """
    params: List[Any] = [referrer_ucn]

    def add_param(value: Any) -> str:
        params.append(value)
        return f"${len(params)}"

    if leaderboard and leaderboard.get("product"):
        sql += f"""
          AND (md.product IS NULL OR UPPER(TRIM(md.product)) = UPPER(TRIM({add_param(leaderboard['product'])})))
        """

    if leaderboard and leaderboard.get("sub_product"):
        sql += f"""
          AND (md.sub_product IS NULL OR UPPER(TRIM(md.sub_product)) = UPPER(TRIM({add_param(leaderboard['sub_product'])})))
        """

    sql += " ORDER BY ump.completed_at NULLS LAST, ump.mission_code"

    async with async_db_connection() as conn:
        rows = await conn.fetch(sql, *params)

    return [_row_to_dict(row) for row in rows]


async def calculate_mission_score_for_referrer(
    referrer_ucn: str,
    leaderboard: Optional[Dict[str, Any]] = None,
) -> Dict[str, int]:
    missions = await get_completed_missions_for_referrer(
        referrer_ucn,
        leaderboard=leaderboard,
    )

    total_score = referral_score = milestone_score = bonus_score = 0

    for mission in missions:
        mission_code = str(mission["mission_code"])
        category = str(mission.get("mission_category") or MISSION_CATEGORY_CORE).upper()
        points = int(MISSION_POINTS.get(mission_code, 0))

        total_score += points

        if category == MISSION_CATEGORY_CORE:
            referral_score += points
        elif category == MISSION_CATEGORY_BOOST:
            bonus_score += points
        elif category == MISSION_CATEGORY_MILESTONE:
            milestone_score += points
            bonus_score += points

    return {
        "total_score": total_score,
        "referral_score": referral_score,
        "milestone_score": milestone_score,
        "bonus_score": bonus_score,
    }


def _normalized(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip().upper()
    return cleaned or None


def _rule_matches_referral(rule: Dict[str, Any], referral: Dict[str, Any]) -> bool:
    for field in ("journey_code", "journey_version", "product", "sub_product"):
        rule_value = _normalized(rule.get(field))
        referral_value = _normalized(referral.get(field))
        if rule_value and rule_value != referral_value:
            return False
    return True


def _referral_has_milestone(referral: Dict[str, Any], milestone_code: str | None) -> bool:
    milestone = _normalized(milestone_code)
    if not milestone:
        return False

    if milestone == "COMPLETION_BONUS":
        return bool(referral.get("is_complete"))

    if _normalized(referral.get("status")) == milestone:
        return True

    journey_code = str(referral.get("journey_code") or DEFAULT_JOURNEY_CODE)
    journey_version = str(referral.get("journey_version") or DEFAULT_JOURNEY_VERSION)
    try:
        journey_definition = get_journey_definition(journey_code, journey_version)
    except ValueError:
        return False

    timestamp_field = journey_definition.event_to_timestamp_field.get(milestone)
    if timestamp_field and referral.get(timestamp_field) is not None:
        return True

    if milestone in journey_definition.core_sequence:
        current = _normalized(referral.get("status"))
        try:
            return journey_definition.core_sequence.index(current) >= journey_definition.core_sequence.index(milestone)
        except ValueError:
            return False

    return False


async def calculate_configured_score_for_referrals(
    leaderboard: Dict[str, Any],
    referrals: List[Dict[str, Any]],
) -> Dict[str, int]:
    leaderboard_code = leaderboard.get("leaderboard_code")
    if not leaderboard_code:
        return {"total_score": 0, "milestone_score": 0, "bonus_score": 0}

    rules = await get_scoring_rules(
        str(leaderboard_code),
        tenant_code=leaderboard.get("tenant_code"),
    )

    milestone_score = bonus_score = 0
    for referral in referrals:
        for rule in rules:
            if not _rule_matches_referral(rule, referral):
                continue
            if not _referral_has_milestone(referral, rule.get("milestone_code")):
                continue

            score_value = int(rule.get("score_value") or 0)
            score_type = _normalized(rule.get("score_type"))
            if score_type == "BONUS":
                bonus_score += score_value
            else:
                milestone_score += score_value

    return {
        "total_score": milestone_score + bonus_score,
        "milestone_score": milestone_score,
        "bonus_score": bonus_score,
    }


async def calculate_referrer_score_for_board(
    leaderboard: Dict[str, Any],
    referrer_ucn: str,
) -> ScoreBreakdown:
    referrals = await get_referrals_for_board(leaderboard, referrer_ucn=referrer_ucn)
    mission_score = await calculate_mission_score_for_referrer(
        referrer_ucn,
        leaderboard=leaderboard,
    )
    configured_score = await calculate_configured_score_for_referrals(
        leaderboard,
        referrals,
    )

    completed_referrals_count = 0
    last_event_at = None

    for referral in referrals:
        if referral.get("is_complete"):
            completed_referrals_count += 1

        updated_at = referral.get("updated_at")
        if updated_at is not None and (last_event_at is None or updated_at > last_event_at):
            last_event_at = updated_at

    return ScoreBreakdown(
        total_score=mission_score["total_score"] + configured_score["total_score"],
        referral_score=mission_score["referral_score"],
        milestone_score=mission_score["milestone_score"] + configured_score["milestone_score"],
        bonus_score=mission_score["bonus_score"] + configured_score["bonus_score"],
        referrals_count=len(referrals),
        completed_referrals_count=completed_referrals_count,
        last_event_at=last_event_at,
    )


async def upsert_leaderboard_entry(
    leaderboard: Dict[str, Any],
    referrer_ucn: str,
    score: ScoreBreakdown,
) -> None:
    referrer_ucn_hash = _hash_referrer_ucn(referrer_ucn)
    display_name = await get_referrer_display_name(referrer_ucn)
    rank_tier = get_rank_tier(score.total_score)

    async with async_db_connection() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO leaderboard_entries (
                    leaderboard_code, referrer_ucn, referrer_ucn_hash, display_name,
                    total_score, referral_score, milestone_score, bonus_score,
                    referrals_count, completed_referrals_count, last_event_at,
                    rank_position, rank_tier, tenant_code, product, sub_product,
                    created_at, updated_at
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, NULL, $12, $13, $14, $15, NOW(), NOW()
                )
                ON CONFLICT (leaderboard_code, referrer_ucn)
                DO UPDATE SET
                    referrer_ucn_hash = EXCLUDED.referrer_ucn_hash,
                    display_name = EXCLUDED.display_name,
                    total_score = EXCLUDED.total_score,
                    referral_score = EXCLUDED.referral_score,
                    milestone_score = EXCLUDED.milestone_score,
                    bonus_score = EXCLUDED.bonus_score,
                    referrals_count = EXCLUDED.referrals_count,
                    completed_referrals_count = EXCLUDED.completed_referrals_count,
                    last_event_at = EXCLUDED.last_event_at,
                    rank_tier = EXCLUDED.rank_tier,
                    tenant_code = EXCLUDED.tenant_code,
                    product = EXCLUDED.product,
                    sub_product = EXCLUDED.sub_product,
                    updated_at = NOW()
                """,
                leaderboard["leaderboard_code"],
                referrer_ucn,
                referrer_ucn_hash,
                display_name,
                score.total_score,
                score.referral_score,
                score.milestone_score,
                score.bonus_score,
                score.referrals_count,
                score.completed_referrals_count,
                score.last_event_at,
                rank_tier,
                leaderboard.get("tenant_code"),
                leaderboard.get("product"),
                leaderboard.get("sub_product"),
            )


async def delete_leaderboard_entry_if_no_referrals(
    leaderboard_code: str,
    referrer_ucn: str,
    tenant_code: str | None = None,
) -> None:
    async with async_db_connection() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                DELETE FROM leaderboard_entries
                WHERE leaderboard_code = $1
                  AND referrer_ucn = $2
                  AND ($3::text IS NULL OR tenant_code = $3)
                """,
                leaderboard_code,
                referrer_ucn,
                tenant_code,
            )


async def recalculate_rankings(
    leaderboard_code: str,
    tenant_code: str | None = None,
) -> None:
    async with async_db_connection() as conn:
        async with conn.transaction():
            rows = await conn.fetch(
                """
                SELECT referrer_ucn
                FROM leaderboard_entries
                WHERE leaderboard_code = $1
                  AND ($2::text IS NULL OR tenant_code = $2)
                ORDER BY total_score DESC,
                         completed_referrals_count DESC,
                         last_event_at ASC NULLS LAST,
                         referrer_ucn_hash ASC
                """,
                leaderboard_code,
                tenant_code,
            )

            for rank, row in enumerate(rows, start=1):
                await conn.execute(
                    """
                    UPDATE leaderboard_entries
                    SET rank_position = $1,
                        updated_at = NOW()
                    WHERE leaderboard_code = $2
                      AND referrer_ucn = $3
                      AND ($4::text IS NULL OR tenant_code = $4)
                    """,
                    rank,
                    leaderboard_code,
                    row["referrer_ucn"],
                    tenant_code,
                )


async def rebuild_leaderboard_for_referrer(
    referrer_ucn: str,
    tenant_code: str | None = None,
) -> None:
    leaderboards = await get_active_leaderboard_definitions(tenant_code=tenant_code)

    affected_tenants: set[str | None] = set()

    for leaderboard in leaderboards:
        referrals = await get_referrals_for_board(leaderboard, referrer_ucn=referrer_ucn)
        board_tenant_code = leaderboard.get("tenant_code")
        affected_tenants.add(board_tenant_code)

        if not referrals:
            await delete_leaderboard_entry_if_no_referrals(
                leaderboard_code=leaderboard["leaderboard_code"],
                referrer_ucn=referrer_ucn,
                tenant_code=board_tenant_code,
            )
            await recalculate_rankings(
                leaderboard_code=leaderboard["leaderboard_code"],
                tenant_code=board_tenant_code,
            )
            continue

        score = await calculate_referrer_score_for_board(leaderboard, referrer_ucn)
        await upsert_leaderboard_entry(leaderboard, referrer_ucn, score)
        await recalculate_rankings(
            leaderboard_code=leaderboard["leaderboard_code"],
            tenant_code=board_tenant_code,
        )

    for affected_tenant in affected_tenants:
        invalidate_leaderboard_cache(affected_tenant)


async def rebuild_leaderboard_for_board(
    leaderboard_code: str,
    tenant_code: str | None = None,
) -> None:
    leaderboard = await get_leaderboard_definition(
        leaderboard_code=leaderboard_code,
        tenant_code=tenant_code,
    )
    if not leaderboard:
        raise ValueError(f"Active leaderboard not found: {leaderboard_code}")

    board_tenant_code = leaderboard.get("tenant_code")
    referrals = await get_referrals_for_board(leaderboard)
    referrers = sorted({r["referrer_ucn"] for r in referrals if r.get("referrer_ucn")})

    async with async_db_connection() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                DELETE FROM leaderboard_entries
                WHERE leaderboard_code = $1
                  AND ($2::text IS NULL OR tenant_code = $2)
                """,
                leaderboard_code,
                board_tenant_code,
            )

    for referrer_ucn in referrers:
        score = await calculate_referrer_score_for_board(leaderboard, referrer_ucn)
        await upsert_leaderboard_entry(leaderboard, referrer_ucn, score)

    await recalculate_rankings(
        leaderboard_code=leaderboard_code,
        tenant_code=board_tenant_code,
    )
    invalidate_leaderboard_cache(board_tenant_code)


async def rebuild_all_leaderboards(tenant_code: str | None = None) -> None:
    affected_tenants: set[str | None] = set()

    for leaderboard in await get_active_leaderboard_definitions(tenant_code=tenant_code):
        board_tenant_code = leaderboard.get("tenant_code")
        affected_tenants.add(board_tenant_code)

        await rebuild_leaderboard_for_board(
            leaderboard_code=leaderboard["leaderboard_code"],
            tenant_code=board_tenant_code,
        )

    for affected_tenant in affected_tenants:
        invalidate_leaderboard_cache(affected_tenant)


async def get_leaderboard(
    leaderboard_code: str,
    tenant_code: str,
    limit: int = 10,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    cache_key = _leaderboard_cache_key(
        leaderboard_code=leaderboard_code,
        tenant_code=tenant_code,
        limit=limit,
        offset=offset,
    )

    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    async with async_db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT leaderboard_code, display_name, total_score, referral_score,
                   milestone_score, bonus_score, referrals_count,
                   completed_referrals_count, last_event_at, rank_position, rank_tier
            FROM leaderboard_entries
            WHERE leaderboard_code = $1
              AND tenant_code = $2
            ORDER BY rank_position ASC NULLS LAST, total_score DESC
            LIMIT $3 OFFSET $4
            """,
            leaderboard_code,
            tenant_code,
            limit,
            offset,
        )

    result = [_row_to_dict(row) for row in rows]
    cache_set(cache_key, result, ttl_seconds=LEADERBOARD_CACHE_TTL_SECONDS)
    return result


async def get_referrer_leaderboard_entry(
    leaderboard_code: str,
    referrer_ucn: str,
    tenant_code: str,
) -> Optional[Dict[str, Any]]:
    async with async_db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT leaderboard_code, display_name, total_score, referral_score,
                   milestone_score, bonus_score, referrals_count,
                   completed_referrals_count, last_event_at, rank_position, rank_tier
            FROM leaderboard_entries
            WHERE leaderboard_code = $1
              AND referrer_ucn = $2
              AND tenant_code = $3
            """,
            leaderboard_code,
            referrer_ucn,
            tenant_code,
        )

    return _row_to_dict(row) if row else None


async def get_next_rank_info(
    leaderboard_code: str,
    referrer_ucn: str,
    tenant_code: str,
):
    async with async_db_connection() as conn:
        current = await conn.fetchrow(
            """
            SELECT rank_position, total_score
            FROM leaderboard_entries
            WHERE leaderboard_code = $1
              AND referrer_ucn = $2
              AND tenant_code = $3
            """,
            leaderboard_code,
            referrer_ucn,
            tenant_code,
        )

        if not current:
            return None

        next_row = await conn.fetchrow(
            """
            SELECT rank_position, total_score
            FROM leaderboard_entries
            WHERE leaderboard_code = $1
              AND tenant_code = $2
              AND rank_position < $3
            ORDER BY rank_position DESC
            LIMIT 1
            """,
            leaderboard_code,
            tenant_code,
            current["rank_position"],
        )

    if not next_row:
        return None

    return {
        "next_rank_position": next_row["rank_position"],
        "next_rank_score": next_row["total_score"],
        "points_to_next_rank": max(0, next_row["total_score"] - current["total_score"]),
    }


async def get_leaderboard_count(
    leaderboard_code: str,
    tenant_code: str,
) -> int:
    async with async_db_connection() as conn:
        value = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM leaderboard_entries
            WHERE leaderboard_code = $1
              AND tenant_code = $2
            """,
            leaderboard_code,
            tenant_code,
        )

    return int(value or 0)
