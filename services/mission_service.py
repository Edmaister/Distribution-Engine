from __future__ import annotations

import datetime
import json
import logging
from typing import Any, Dict, List, Optional, Union

from utils.db import db_connection

logger = logging.getLogger(__name__)

MISSION_CATEGORY_CORE = "CORE"
MISSION_CATEGORY_BOOST = "BOOST"
MISSION_CATEGORY_MILESTONE = "MILESTONE"
MISSION_CATEGORY_DEFAULT = MISSION_CATEGORY_CORE
MISSION_CATEGORIES = {
    MISSION_CATEGORY_CORE,
    MISSION_CATEGORY_BOOST,
    MISSION_CATEGORY_MILESTONE,
}

MISSION_SCOPE_REFERRAL = "REFERRAL"
MISSION_SCOPE_PORTFOLIO = "PORTFOLIO"


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _normalize_mission_category(value: Optional[str]) -> str:
    category = (value or MISSION_CATEGORY_DEFAULT).upper()
    if category not in MISSION_CATEGORIES:
        return MISSION_CATEGORY_DEFAULT
    return category


def _derive_mission_status(progress_count: int, goal_count: int, is_complete: bool) -> str:
    if is_complete:
        return "COMPLETED"
    if progress_count <= 0:
        return "AVAILABLE"
    if progress_count < goal_count:
        return "IN_PROGRESS"
    return "COMPLETED"


def _group_sort_key(item: Dict[str, Any]) -> tuple[Any, ...]:
    return (
        bool(item.get("isComplete", False)),
        int(item.get("displayOrder", 9999)),
        item.get("missionCode", ""),
    )


def _group_mission_items(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {
        "core": [],
        "boost": [],
        "milestone": [],
    }

    for item in items:
        category = _normalize_mission_category(item.get("category"))
        grouped[category.lower()].append(item)

    for key in grouped:
        grouped[key].sort(key=_group_sort_key)

    return grouped


def _empty_grouped_response() -> Dict[str, List[Dict[str, Any]]]:
    return {"core": [], "boost": [], "milestone": []}


def _row_to_dict(row: Any) -> Dict[str, Any]:
    return dict(row)


async def _get_referral_row(referral_track_id: str) -> Optional[Dict[str, Any]]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                ri.referral_track_id,
                ri.product,
                ri.sub_product,
                ri.referrer_ucn,
                ri.referee_ucn
            FROM referral_instances ri
            WHERE ri.referral_track_id = $1
            """,
            referral_track_id,
        )

    return _row_to_dict(row) if row else None


async def _get_referrals_for_referrer(referrer_ucn: str) -> List[Dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                ri.referral_track_id,
                ri.product,
                ri.sub_product,
                ri.referrer_ucn,
                ri.referee_ucn,
                ri.progress_percent,
                ri.progress_band,
                ri.display_status,
                ri.created_at,
                ri.updated_at
            FROM referral_instances ri
            WHERE ri.referrer_ucn = $1
            ORDER BY ri.created_at ASC NULLS LAST, ri.referral_track_id ASC
            """,
            referrer_ucn,
        )

    return [_row_to_dict(row) for row in rows]


async def _get_mission_definitions(
    product: Optional[str],
    sub_product: Optional[str],
) -> List[Dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                mission_code,
                mission_name,
                mission_description,
                product,
                sub_product,
                event_type,
                goal_count,
                bonus_reward_amount,
                currency,
                is_optional,
                is_credit_related,
                requires_disclaimer,
                regulatory_tags,
                display_priority,
                COALESCE(mission_category, 'CORE') AS mission_category
            FROM mission_definitions
            WHERE is_active = TRUE
              AND (product IS NULL OR LOWER(product) = LOWER($1))
              AND (sub_product IS NULL OR LOWER(sub_product) = LOWER($2))
            ORDER BY
                CASE COALESCE(mission_category, 'CORE')
                    WHEN 'CORE' THEN 1
                    WHEN 'BOOST' THEN 2
                    WHEN 'MILESTONE' THEN 3
                    ELSE 4
                END,
                display_priority ASC,
                mission_code ASC
            """,
            product,
            sub_product,
        )

    return [_row_to_dict(row) for row in rows]


async def _get_reward_disclosures(codes: List[str]) -> List[str]:
    if not codes:
        return []

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT disclosure_code, disclosure_text
            FROM reward_disclosures
            WHERE disclosure_code = ANY($1::text[])
              AND is_active = TRUE
            ORDER BY disclosure_code
            """,
            codes,
        )

    by_code = {
        row["disclosure_code"]: row["disclosure_text"]
        for row in rows
    }

    return [by_code[code] for code in codes if code in by_code]


async def _get_existing_progress(
    referral_track_id: str,
    mission_code: str,
    beneficiary_type: str,
    beneficiary_ref: str,
) -> Optional[Dict[str, Any]]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                id,
                referral_track_id,
                mission_code,
                beneficiary_type,
                beneficiary_ref,
                progress_count,
                goal_count,
                is_complete,
                completed_at,
                bonus_reward_applied
            FROM user_mission_progress
            WHERE referral_track_id = $1
              AND mission_code = $2
              AND beneficiary_type = $3
              AND beneficiary_ref = $4
            """,
            referral_track_id,
            mission_code,
            beneficiary_type,
            beneficiary_ref,
        )

    return _row_to_dict(row) if row else None


async def _upsert_progress_row(
    referral_track_id: str,
    mission_code: str,
    beneficiary_type: str,
    beneficiary_ref: str,
    goal_count: int,
) -> None:
    async with db_connection() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO user_mission_progress (
                    referral_track_id,
                    mission_code,
                    beneficiary_type,
                    beneficiary_ref,
                    progress_count,
                    goal_count,
                    is_complete,
                    bonus_reward_applied,
                    created_at,
                    updated_at
                )
                VALUES ($1, $2, $3, $4, 0, $5, FALSE, FALSE, NOW(), NOW())
                ON CONFLICT (referral_track_id, mission_code, beneficiary_type, beneficiary_ref)
                DO NOTHING
                """,
                referral_track_id,
                mission_code,
                beneficiary_type,
                beneficiary_ref,
                goal_count,
            )


async def _record_mission_display_audit(
    referral_track_id: str,
    mission_code: str,
    title: str,
    body: str,
    compliance: Dict[str, Any],
    disclosures: List[str],
    channel: str,
) -> None:
    async with db_connection() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO mission_display_audit (
                    referral_track_id,
                    mission_code,
                    title,
                    body,
                    compliance_json,
                    disclosures_json,
                    channel,
                    shown_at
                )
                VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, NOW())
                """,
                referral_track_id,
                mission_code,
                title,
                body,
                json.dumps(compliance),
                json.dumps(disclosures),
                channel,
            )


async def _build_mission_response_item(
    definition: Dict[str, Any],
    progress_row: Dict[str, Any],
    scope: str = MISSION_SCOPE_REFERRAL,
    associated_referral_track_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    disclaimer_codes = ["GENERAL_INFO_ONLY", "REWARD_CONDITIONAL"]
    if definition.get("is_credit_related"):
        disclaimer_codes.append("CREDIT_DISCLOSURE")

    disclosures = await _get_reward_disclosures(disclaimer_codes)
    category = _normalize_mission_category(definition.get("mission_category"))
    progress_count = int(progress_row["progress_count"])
    goal_count = int(progress_row["goal_count"])
    is_complete = bool(progress_row["is_complete"])
    status = _derive_mission_status(progress_count, goal_count, is_complete)
    reward_amount = int(definition["bonus_reward_amount"])
    currency = definition.get("currency") or "ZAR"

    compliance = {
        "isAdvice": False,
        "isCreditRelated": bool(definition.get("is_credit_related", False)),
        "requiresDisclaimer": True,
        "disclaimerCodes": disclaimer_codes,
        "regulatoryTags": list(
            definition.get("regulatory_tags")
            or ["TCF", "FAIS", "MARKET_CONDUCT", "BANKING_CODE"]
        ),
        "blocked": False,
        "blockedReason": None,
    }

    return {
        "missionCode": definition["mission_code"],
        "category": category,
        "scope": scope,
        "displayOrder": int(definition.get("display_priority") or 9999),
        "beneficiaryType": progress_row["beneficiary_type"],
        "beneficiaryRef": progress_row["beneficiary_ref"],
        "title": definition["mission_name"],
        "body": definition["mission_description"],
        "progressCount": progress_count,
        "goalCount": goal_count,
        "progressLabel": f"{progress_count} / {goal_count}",
        "status": status,
        "isComplete": is_complete,
        "completedAt": progress_row["completed_at"],
        "bonusRewardAmount": reward_amount,
        "rewardLabel": f"+{currency} {reward_amount}",
        "currency": currency,
        "associatedReferralTrackIds": associated_referral_track_ids or [],
        "disclosures": disclosures,
        "compliance": compliance,
    }


async def _count_completed_referrals_for_referrer(
    referrer_ucn: str,
    product: Optional[str] = None,
    sub_product: Optional[str] = None,
) -> Dict[str, Any]:
    sql = """
        SELECT
            COUNT(*) AS completed_count,
            ARRAY_AGG(referral_track_id::text ORDER BY created_at NULLS LAST, referral_track_id) AS referral_track_ids
        FROM referral_instances
        WHERE referrer_ucn = $1
          AND progress_band = 'COMPLETE'
    """
    params: List[Any] = [referrer_ucn]

    def add_param(value: Any) -> str:
        params.append(value)
        return f"${len(params)}"

    if product:
        sql += f" AND UPPER(TRIM(product)) = UPPER(TRIM({add_param(product)}))"

    if sub_product:
        sql += f" AND UPPER(TRIM(sub_product)) = UPPER(TRIM({add_param(sub_product)}))"

    async with db_connection() as conn:
        row = await conn.fetchrow(sql, *params)

    row_dict = _row_to_dict(row) if row else {}

    raw_ids = row_dict.get("referral_track_ids")

    if isinstance(raw_ids, list):
        referral_ids = raw_ids
    elif isinstance(raw_ids, str):
        referral_ids = [
            x.strip()
            for x in raw_ids.strip("{}").split(",")
            if x.strip()
        ]
    else:
        referral_ids = []

    return {
        "completed_count": int(row_dict.get("completed_count") or 0),
        "referral_track_ids": referral_ids,
    }


async def _build_portfolio_milestone_item(
    definition: Dict[str, Any],
    beneficiary_ref: str,
    completed_count: int,
    associated_referral_track_ids: List[str],
) -> Dict[str, Any]:
    disclaimer_codes = ["GENERAL_INFO_ONLY", "REWARD_CONDITIONAL"]
    disclosures = await _get_reward_disclosures(disclaimer_codes)

    goal_count = int(definition["goal_count"])
    progress_count = min(completed_count, goal_count)
    is_complete = progress_count >= goal_count

    compliance = {
        "isAdvice": False,
        "isCreditRelated": bool(definition.get("is_credit_related", False)),
        "requiresDisclaimer": True,
        "disclaimerCodes": disclaimer_codes,
        "regulatoryTags": list(
            definition.get("regulatory_tags")
            or ["TCF", "FAIS", "MARKET_CONDUCT", "BANKING_CODE"]
        ),
        "blocked": False,
        "blockedReason": None,
    }

    reward_amount = int(definition["bonus_reward_amount"])
    currency = definition.get("currency") or "ZAR"

    return {
        "missionCode": definition["mission_code"],
        "category": _normalize_mission_category(definition.get("mission_category")),
        "scope": MISSION_SCOPE_PORTFOLIO,
        "displayOrder": int(definition.get("display_priority") or 9999),
        "beneficiaryType": "REFERRER",
        "beneficiaryRef": beneficiary_ref,
        "title": definition["mission_name"],
        "body": definition["mission_description"],
        "progressCount": progress_count,
        "goalCount": goal_count,
        "progressLabel": f"{progress_count} / {goal_count}",
        "status": _derive_mission_status(progress_count, goal_count, is_complete),
        "isComplete": is_complete,
        "completedAt": None,
        "bonusRewardAmount": reward_amount,
        "rewardLabel": f"+{currency} {reward_amount}",
        "currency": currency,
        "associatedReferralTrackIds": associated_referral_track_ids,
        "disclosures": disclosures,
        "compliance": compliance,
    }


async def get_missions_for_referral(
    referral_track_id: str,
    tenant_code: str | None = None,
    channel: str = "API",
    audit: bool = True,
    grouped: bool = False,
) -> Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    referral = await _get_referral_row(referral_track_id)
    if not referral:
        return _empty_grouped_response() if grouped else []

    beneficiary_type = "REFERRER"
    beneficiary_ref = referral.get("referrer_ucn")
    if not beneficiary_ref:
        return _empty_grouped_response() if grouped else []

    definitions = await _get_mission_definitions(
        referral.get("product"),
        referral.get("sub_product"),
    )

    items: List[Dict[str, Any]] = []

    for definition in definitions:
        category = _normalize_mission_category(definition.get("mission_category"))

        if category == MISSION_CATEGORY_MILESTONE:
            continue

        await _upsert_progress_row(
            referral_track_id=referral_track_id,
            mission_code=definition["mission_code"],
            beneficiary_type=beneficiary_type,
            beneficiary_ref=beneficiary_ref,
            goal_count=int(definition["goal_count"]),
        )

        progress_row = await _get_existing_progress(
            referral_track_id=referral_track_id,
            mission_code=definition["mission_code"],
            beneficiary_type=beneficiary_type,
            beneficiary_ref=beneficiary_ref,
        )
        if not progress_row:
            continue

        item = await _build_mission_response_item(
            definition=definition,
            progress_row=progress_row,
            scope=MISSION_SCOPE_REFERRAL,
            associated_referral_track_ids=[referral_track_id],
        )

        if audit:
            await _record_mission_display_audit(
                referral_track_id=referral_track_id,
                mission_code=item["missionCode"],
                title=item["title"],
                body=item["body"],
                compliance=item["compliance"],
                disclosures=item["disclosures"],
                channel=channel,
            )

        items.append(item)

    items.sort(key=_group_sort_key)
    if grouped:
        return _group_mission_items(items)
    return items


async def get_missions_for_referrer(
    referrer_ucn: str,
    channel: str = "API",
    audit: bool = True,
    grouped: bool = True,
) -> Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    referrals = await _get_referrals_for_referrer(referrer_ucn)
    if not referrals:
        return _empty_grouped_response() if grouped else []

    referral_items: List[Dict[str, Any]] = []
    milestone_items: List[Dict[str, Any]] = []

    for referral in referrals:
        referral_track_id = referral["referral_track_id"]
        items = await get_missions_for_referral(
            referral_track_id=referral_track_id,
            channel=channel,
            audit=audit,
            grouped=False,
        )
        referral_items.extend(items)

    product = referrals[0].get("product")
    sub_product = referrals[0].get("sub_product")

    definitions = await _get_mission_definitions(product, sub_product)
    milestone_definitions = [
        d
        for d in definitions
        if _normalize_mission_category(d.get("mission_category"))
        == MISSION_CATEGORY_MILESTONE
    ]

    completed = await _count_completed_referrals_for_referrer(
        referrer_ucn=referrer_ucn,
        product=product,
        sub_product=sub_product,
    )

    for definition in milestone_definitions:
        milestone_items.append(
            await _build_portfolio_milestone_item(
                definition=definition,
                beneficiary_ref=referrer_ucn,
                completed_count=completed["completed_count"],
                associated_referral_track_ids=completed["referral_track_ids"],
            )
        )

    items = referral_items + milestone_items
    items.sort(key=_group_sort_key)

    if grouped:
        return _group_mission_items(items)
    return items


async def apply_event_to_missions(
    referral_track_id: str,
    event_type: str,
    tenant_code: str | None = None,
) -> List[Dict[str, Any]]:
    referral = await _get_referral_row(referral_track_id)
    if not referral:
        return []

    beneficiary_type = "REFERRER"
    beneficiary_ref = referral.get("referrer_ucn")
    if not beneficiary_ref:
        return []

    definitions = await _get_mission_definitions(
        referral.get("product"),
        referral.get("sub_product"),
    )

    matching = [
        d
        for d in definitions
        if d["event_type"] == event_type
        and _normalize_mission_category(d.get("mission_category"))
        != MISSION_CATEGORY_MILESTONE
    ]

    updated: List[Dict[str, Any]] = []

    for definition in matching:
        category = _normalize_mission_category(definition.get("mission_category"))

        await _upsert_progress_row(
            referral_track_id=referral_track_id,
            mission_code=definition["mission_code"],
            beneficiary_type=beneficiary_type,
            beneficiary_ref=beneficiary_ref,
            goal_count=int(definition["goal_count"]),
        )

        row = await _get_existing_progress(
            referral_track_id=referral_track_id,
            mission_code=definition["mission_code"],
            beneficiary_type=beneficiary_type,
            beneficiary_ref=beneficiary_ref,
        )
        if not row:
            continue

        if row["is_complete"]:
            updated.append(
                {
                    "missionCode": definition["mission_code"],
                    "category": category,
                    "scope": MISSION_SCOPE_REFERRAL,
                    "displayOrder": int(definition.get("display_priority") or 9999),
                    "progressCount": int(row["progress_count"]),
                    "goalCount": int(row["goal_count"]),
                    "progressLabel": f'{int(row["progress_count"])} / {int(row["goal_count"])}',
                    "status": _derive_mission_status(
                        int(row["progress_count"]),
                        int(row["goal_count"]),
                        bool(row["is_complete"]),
                    ),
                    "isComplete": bool(row["is_complete"]),
                    "bonusRewardApplied": bool(row.get("bonus_reward_applied", False)),
                    "beneficiaryType": row["beneficiary_type"],
                    "beneficiaryRef": row["beneficiary_ref"],
                    "associatedReferralTrackIds": [referral_track_id],
                }
            )
            continue

        new_progress = min(int(row["progress_count"]) + 1, int(row["goal_count"]))
        is_complete = new_progress >= int(row["goal_count"])
        completed_at = _utcnow() if is_complete else None

        async with db_connection() as conn:
            async with conn.transaction():
                await conn.execute(
                    """
                    UPDATE user_mission_progress
                    SET progress_count = $1,
                        is_complete = $2,
                        completed_at = COALESCE(completed_at, $3),
                        updated_at = NOW()
                    WHERE referral_track_id = $4
                      AND mission_code = $5
                      AND beneficiary_type = $6
                      AND beneficiary_ref = $7
                    """,
                    new_progress,
                    is_complete,
                    completed_at,
                    referral_track_id,
                    definition["mission_code"],
                    beneficiary_type,
                    beneficiary_ref,
                )

        if (
            is_complete
            and not row["bonus_reward_applied"]
            and int(definition["bonus_reward_amount"]) > 0
        ):
            async with db_connection() as conn:
                async with conn.transaction():
                    inserted = await conn.fetchrow(
                        """
                        INSERT INTO rewards (
                            referral_track_id,
                            beneficiary_type,
                            beneficiary_ref,
                            product,
                            sub_product,
                            reward_type,
                            amount,
                            reward_source,
                            mission_code,
                            status,
                            created_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'APPLIED', NOW())
                        ON CONFLICT DO NOTHING
                        RETURNING id
                        """,
                        referral_track_id,
                        beneficiary_type,
                        beneficiary_ref,
                        referral.get("product"),
                        referral.get("sub_product"),
                        "BONUS",
                        int(definition["bonus_reward_amount"]),
                        "MISSION_BONUS",
                        definition["mission_code"],
                    )

                    if inserted:
                        await conn.execute(
                            """
                            UPDATE user_mission_progress
                            SET bonus_reward_applied = TRUE,
                                updated_at = NOW()
                            WHERE referral_track_id = $1
                              AND mission_code = $2
                              AND beneficiary_type = $3
                              AND beneficiary_ref = $4
                            """,
                            referral_track_id,
                            definition["mission_code"],
                            beneficiary_type,
                            beneficiary_ref,
                        )

                        logger.info(
                            "mission_bonus_applied referral_track_id=%s mission_code=%s amount=%s category=%s",
                            referral_track_id,
                            definition["mission_code"],
                            int(definition["bonus_reward_amount"]),
                            category,
                        )
                    else:
                        logger.info(
                            "mission_bonus_not_inserted referral_track_id=%s mission_code=%s",
                            referral_track_id,
                            definition["mission_code"],
                        )

        final_row = await _get_existing_progress(
            referral_track_id=referral_track_id,
            mission_code=definition["mission_code"],
            beneficiary_type=beneficiary_type,
            beneficiary_ref=beneficiary_ref,
        )

        if final_row:
            updated.append(
                {
                    "missionCode": definition["mission_code"],
                    "category": category,
                    "scope": MISSION_SCOPE_REFERRAL,
                    "displayOrder": int(definition.get("display_priority") or 9999),
                    "progressCount": int(final_row["progress_count"]),
                    "goalCount": int(final_row["goal_count"]),
                    "progressLabel": f'{int(final_row["progress_count"])} / {int(final_row["goal_count"])}',
                    "status": _derive_mission_status(
                        int(final_row["progress_count"]),
                        int(final_row["goal_count"]),
                        bool(final_row["is_complete"]),
                    ),
                    "isComplete": bool(final_row["is_complete"]),
                    "bonusRewardApplied": bool(
                        final_row.get("bonus_reward_applied", False)
                    ),
                    "beneficiaryType": final_row["beneficiary_type"],
                    "beneficiaryRef": final_row["beneficiary_ref"],
                    "associatedReferralTrackIds": [referral_track_id],
                }
            )

    return updated