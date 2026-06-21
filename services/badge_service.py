from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from utils.db import db_connection


HVE_EVENT_TYPES = {
    "SALARY_SWITCHED",
    "DEBIT_ORDER_SWITCHED",
    "FIRST_TRANSACTION_COMPLETED",
}


def _row_to_dict(row: Any) -> Dict[str, Any]:
    return dict(row)


def _resolve_referrer_hash(
    beneficiary_ref: str,
    referrer_hash: str | None = None,
) -> str:
    cleaned_hash = str(referrer_hash or "").strip()
    if cleaned_hash:
        return cleaned_hash

    from utils.crypto import ucn_lookup_key

    return ucn_lookup_key(beneficiary_ref)


async def _get_referral_row(referral_track_id: str) -> Optional[Dict[str, Any]]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                ri.referral_track_id,
                ri.referrer_ucn,
                rc.referrer_ucn_hash AS referrer_hash
            FROM referral_instances ri
            LEFT JOIN referrer_codes rc
              ON rc.referrer_code_id = ri.referrer_code_id
            WHERE ri.referral_track_id = $1
            """,
            referral_track_id,
        )

    return _row_to_dict(row) if row else None


async def _get_badge_definitions() -> List[Dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                badge_code,
                badge_name,
                badge_description,
                badge_category,
                trigger_type,
                trigger_value,
                icon_name,
                display_priority,
                regulatory_tags
            FROM badge_definitions
            WHERE is_active = TRUE
              AND beneficiary_type = 'REFERRER'
            ORDER BY display_priority ASC, badge_code ASC
            """
        )

    return [_row_to_dict(row) for row in rows]


async def _badge_exists(
    beneficiary_ref: str,
    badge_code: str,
) -> bool:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT 1
            FROM user_badges
            WHERE beneficiary_type = 'REFERRER'
              AND beneficiary_ref = $1
              AND badge_code = $2
            LIMIT 1
            """,
            beneficiary_ref,
            badge_code,
        )

    return row is not None


async def _award_badge(
    beneficiary_ref: str,
    badge_code: str,
    award_reason: str,
    metadata: Optional[Dict[str, Any]] = None,
    referral_track_id: Optional[str] = None,
    referrer_hash: Optional[str] = None,
) -> bool:
    resolved_referrer_hash = _resolve_referrer_hash(beneficiary_ref, referrer_hash)

    async with db_connection() as conn:
        async with conn.transaction():
            has_referrer_hash = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'user_badges'
                      AND column_name = 'referrer_hash'
                )
                """
            )

            if has_referrer_hash:
                result = await conn.execute(
                    """
                    INSERT INTO user_badges (
                        referrer_hash,
                        referral_track_id,
                        beneficiary_type,
                        beneficiary_ref,
                        badge_code,
                        award_reason,
                        metadata_json,
                        awarded_at
                    )
                    VALUES ($1, $2, 'REFERRER', $3, $4, $5, $6::jsonb, NOW())
                    ON CONFLICT (beneficiary_type, beneficiary_ref, badge_code)
                    DO NOTHING
                    """,
                    resolved_referrer_hash,
                    referral_track_id,
                    beneficiary_ref,
                    badge_code,
                    award_reason,
                    json.dumps(metadata or {}),
                )
            else:
                result = await conn.execute(
                    """
                    INSERT INTO user_badges (
                        referral_track_id,
                        beneficiary_type,
                        beneficiary_ref,
                        badge_code,
                        award_reason,
                        metadata_json,
                        awarded_at
                    )
                    VALUES ($1, 'REFERRER', $2, $3, $4, $5::jsonb, NOW())
                    ON CONFLICT (beneficiary_type, beneficiary_ref, badge_code)
                    DO NOTHING
                    """,
                    referral_track_id,
                    beneficiary_ref,
                    badge_code,
                    award_reason,
                    json.dumps(metadata or {}),
                )

    return str(result).upper().endswith(" 1")


async def _count_referrals_created(
    beneficiary_ref: str,
) -> int:
    async with db_connection() as conn:
        value = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM referral_instances
            WHERE referrer_ucn = $1
            """,
            beneficiary_ref,
        )

    return int(value or 0)


async def _count_completed_referrals(
    beneficiary_ref: str,
) -> int:
    async with db_connection() as conn:
        value = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM referral_instances
            WHERE referrer_ucn = $1
              AND is_complete = TRUE
            """,
            beneficiary_ref,
        )

    return int(value or 0)


async def _count_hve_referrals(
    beneficiary_ref: str,
) -> int:
    async with db_connection() as conn:
        value = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM referral_instances
            WHERE referrer_ucn = $1
              AND (
                    salary_switched_at IS NOT NULL
                 OR debit_order_switched_at IS NOT NULL
                 OR first_transaction_completed_at IS NOT NULL
              )
            """,
            beneficiary_ref,
        )

    return int(value or 0)


async def _evaluate_and_award_badges(
    beneficiary_ref: str,
    referral_track_id: Optional[str] = None,
    referrer_hash: Optional[str] = None,
) -> List[Dict[str, Any]]:
    referrals_created = await _count_referrals_created(beneficiary_ref)
    completed_referrals = await _count_completed_referrals(beneficiary_ref)
    hve_referrals = await _count_hve_referrals(beneficiary_ref)

    awarded: List[Dict[str, Any]] = []

    for badge in await _get_badge_definitions():
        trigger_type = str(badge.get("trigger_type") or "").upper()
        trigger_value_raw = badge.get("trigger_value")
        threshold = int(str(trigger_value_raw)) if trigger_value_raw is not None else 0

        should_award = False
        reason = ""
        metadata: Dict[str, Any] = {
            "badgeCategory": badge.get("badge_category"),
            "referralsCreated": referrals_created,
            "completedReferrals": completed_referrals,
            "hveReferrals": hve_referrals,
        }

        if trigger_type == "REFERRAL_CREATED_COUNT":
            if referrals_created >= threshold:
                should_award = True
                reason = (
                    "First referral created"
                    if threshold <= 1
                    else f"Created {referrals_created} referral(s)"
                )

        elif trigger_type == "COMPLETED_REFERRALS_COUNT":
            if completed_referrals >= threshold:
                should_award = True
                reason = (
                    "First successful referral"
                    if threshold <= 1
                    else f"Completed {completed_referrals} referral(s)"
                )

        elif trigger_type == "HVE_COUNT":
            if hve_referrals >= threshold:
                should_award = True
                reason = (
                    "Value established"
                    if threshold <= 1
                    else f"Achieved value on {hve_referrals} referral(s)"
                )

        if not should_award:
            continue

        if await _badge_exists(beneficiary_ref, badge["badge_code"]):
            continue

        inserted = await _award_badge(
            beneficiary_ref=beneficiary_ref,
            badge_code=badge["badge_code"],
            award_reason=reason,
            metadata=metadata,
            referral_track_id=referral_track_id,
            referrer_hash=referrer_hash,
        )

        if inserted:
            awarded.append(_format_badge(badge, reason))

    return awarded


async def evaluate_badges_for_referral_created(
    referral_track_id: str,
) -> List[Dict[str, Any]]:
    referral = await _get_referral_row(referral_track_id)
    if not referral or not referral.get("referrer_ucn"):
        return []

    return await _evaluate_and_award_badges(
        beneficiary_ref=referral["referrer_ucn"],
        referral_track_id=referral_track_id,
        referrer_hash=referral.get("referrer_hash"),
    )


async def evaluate_badges_for_referral_completion(
    referral_track_id: str,
) -> List[Dict[str, Any]]:
    referral = await _get_referral_row(referral_track_id)
    if not referral or not referral.get("referrer_ucn"):
        return []

    return await _evaluate_and_award_badges(
        beneficiary_ref=referral["referrer_ucn"],
        referral_track_id=referral_track_id,
        referrer_hash=referral.get("referrer_hash"),
    )


async def evaluate_badges_for_hve_event(
    referral_track_id: str,
    event_type: str,
) -> List[Dict[str, Any]]:
    if str(event_type or "").upper() not in HVE_EVENT_TYPES:
        return []

    referral = await _get_referral_row(referral_track_id)
    if not referral or not referral.get("referrer_ucn"):
        return []

    return await _evaluate_and_award_badges(
        beneficiary_ref=referral["referrer_ucn"],
        referral_track_id=referral_track_id,
        referrer_hash=referral.get("referrer_hash"),
    )


async def list_badges_for_referral(
    referral_track_id: str,
    tenant_code: str | None = None,
) -> List[Dict[str, Any]]:
    referral = await _get_referral_row(referral_track_id)

    if not referral or not referral.get("referrer_ucn"):
        return []

    return await list_badges_for_referrer(
        referrer_ucn=referral["referrer_ucn"],
        tenant_code=tenant_code,
    )


async def list_badges_for_referrer(
    referrer_ucn: str,
    tenant_code: str | None = None,
) -> List[Dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                ub.badge_code,
                ub.awarded_at,
                ub.award_reason,
                ub.metadata_json,
                bd.badge_name,
                bd.badge_description,
                bd.badge_category,
                bd.icon_name,
                bd.regulatory_tags
            FROM user_badges ub
            JOIN badge_definitions bd
              ON bd.badge_code = ub.badge_code
            WHERE ub.beneficiary_type = 'REFERRER'
              AND ub.beneficiary_ref = $1
            ORDER BY ub.awarded_at DESC, ub.badge_code ASC
            """,
            referrer_ucn,
        )

    return [
        {
            "badgeCode": row["badge_code"],
            "badgeName": row["badge_name"],
            "badgeDescription": row["badge_description"],
            "badgeCategory": row["badge_category"],
            "iconName": row["icon_name"],
            "awardedAt": row["awarded_at"],
            "awardReason": row["award_reason"],
            "metadata": row["metadata_json"] or {},
            "compliance": {
                "isAdvice": False,
                "requiresDisclaimer": False,
                "regulatoryTags": row.get("regulatory_tags")
                or ["TCF", "FAIS", "MARKET_CONDUCT"],
                "blocked": False,
                "blockedReason": None,
            },
        }
        for row in rows
    ]


def _format_badge(badge: Dict[str, Any], reason: str) -> Dict[str, Any]:
    return {
        "badgeCode": badge["badge_code"],
        "badgeName": badge["badge_name"],
        "badgeDescription": badge["badge_description"],
        "badgeCategory": badge["badge_category"],
        "iconName": badge.get("icon_name"),
        "awardReason": reason,
    }
