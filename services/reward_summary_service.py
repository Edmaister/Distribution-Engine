from __future__ import annotations

import datetime
from typing import Any, Dict, List

from utils.db import get_async_connection


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


async def _get_reward_rows(
    referral_track_id: str,
    tenant_code: str,
) -> List[Dict[str, Any]]:
    async with get_async_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                beneficiary_type,
                reward_type,
                reward_source,
                status,
                amount,
                mission_code
            FROM rewards
            WHERE referral_track_id = $1
              AND tenant_code = $2
            ORDER BY created_at ASC
            """,
            referral_track_id,
            tenant_code,
        )

    return [dict(row) for row in rows]


async def _get_referral_row(
    referral_track_id: str,
    tenant_code: str,
) -> Dict[str, Any] | None:
    async with get_async_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                referral_track_id,
                referrer_ucn,
                referee_alias,
                product,
                sub_product,
                next_milestone
            FROM referral_instances
            WHERE referral_track_id = $1
              AND tenant_code = $2
            """,
            referral_track_id,
            tenant_code,
        )

    return dict(row) if row else None


async def _get_pending_mission_bonus_rows(
    referral_track_id: str,
    tenant_code: str,
) -> List[Dict[str, Any]]:
    async with get_async_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                ump.beneficiary_type,
                md.mission_code,
                md.bonus_reward_amount AS amount
            FROM user_mission_progress ump
            JOIN mission_definitions md
              ON md.mission_code = ump.mission_code
            WHERE ump.referral_track_id = $1
              AND ump.tenant_code = $2
              AND ump.is_complete = FALSE
              AND md.is_active = TRUE
              AND md.bonus_reward_amount > 0
            """,
            referral_track_id,
            tenant_code,
        )

    return [dict(row) for row in rows]


async def _get_reward_rows_for_referrer(
    referrer_ucn: str,
    tenant_code: str,
) -> List[Dict[str, Any]]:
    async with get_async_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                r.referral_track_id,
                r.beneficiary_type,
                r.reward_type,
                r.reward_source,
                r.status,
                r.amount,
                r.mission_code
            FROM rewards r
            JOIN referral_instances ri
              ON ri.referral_track_id = r.referral_track_id::uuid
            WHERE ri.referrer_ucn = $1
              AND ri.tenant_code = $2
              AND r.beneficiary_type = 'REFERRER'
            ORDER BY r.created_at ASC
            """,
            referrer_ucn,
            tenant_code,
        )

    return [dict(row) for row in rows]


async def _get_pending_mission_bonus_rows_for_referrer(
    referrer_ucn: str,
    tenant_code: str,
) -> List[Dict[str, Any]]:
    async with get_async_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                ump.referral_track_id,
                ump.beneficiary_type,
                md.mission_code,
                md.bonus_reward_amount AS amount
            FROM user_mission_progress ump
            JOIN mission_definitions md
              ON md.mission_code = ump.mission_code
            JOIN referral_instances ri
              ON ri.referral_track_id = ump.referral_track_id::uuid
            WHERE ri.referrer_ucn = $1
              AND ri.tenant_code = $2
              AND ump.beneficiary_type = 'REFERRER'
              AND ump.is_complete = FALSE
              AND md.is_active = TRUE
              AND md.bonus_reward_amount > 0
            """,
            referrer_ucn,
            tenant_code,
        )

    return [dict(row) for row in rows]


async def _get_referral_counts_for_referrer(
    referrer_ucn: str,
    tenant_code: str,
) -> Dict[str, int]:
    async with get_async_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS referrals_count,
                COUNT(*) FILTER (WHERE is_complete = TRUE) AS completed_referrals_count
            FROM referral_instances
            WHERE referrer_ucn = $1
              AND tenant_code = $2
            """,
            referrer_ucn,
            tenant_code,
        )

    row_dict = dict(row) if row else {}

    return {
        "referralsCount": int(row_dict.get("referrals_count") or 0),
        "completedReferralsCount": int(row_dict.get("completed_referrals_count") or 0),
    }


async def _get_reward_disclosures(codes: List[str]) -> List[str]:
    if not codes:
        return []

    async with get_async_connection() as conn:
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


def _blank_totals() -> Dict[str, int]:
    return {
        "earned": 0,
        "pending": 0,
        "nextEligibleReward": 0,
        "totalPotential": 0,
    }


def _build_description(row: Dict[str, Any]) -> str:
    if row["reward_source"] == "MISSION_BONUS":
        return "Optional mission bonus reward"
    if row["beneficiary_type"] == "REFEREE":
        return "Referee reward"
    return "Base referral reward"


def _build_compliance_payload() -> Dict[str, Any]:
    return {
        "isAdvice": False,
        "requiresDisclaimer": True,
        "disclaimerCodes": ["GENERAL_INFO_ONLY", "REWARD_CONDITIONAL"],
        "regulatoryTags": ["TCF", "FAIS", "MARKET_CONDUCT", "BANKING_CODE"],
    }


async def get_reward_summary_for_referral(
    referral_track_id: str,
    tenant_code: str,
) -> Dict[str, Any] | None:
    referral = await _get_referral_row(referral_track_id, tenant_code)
    if not referral:
        return None

    reward_rows = await _get_reward_rows(referral_track_id, tenant_code)
    pending_bonus_rows = await _get_pending_mission_bonus_rows(
        referral_track_id,
        tenant_code,
    )

    referrer = _blank_totals()
    referee = _blank_totals()
    items: List[Dict[str, Any]] = []

    for row in reward_rows:
        beneficiary_bucket = (
            referrer if row["beneficiary_type"] == "REFERRER" else referee
        )
        amount = int(row["amount"])

        if row["status"] == "APPLIED":
            beneficiary_bucket["earned"] += amount

        items.append(
            {
                "beneficiaryType": row["beneficiary_type"],
                "rewardType": row["reward_type"],
                "rewardSource": row["reward_source"],
                "status": row["status"],
                "amount": amount,
                "description": _build_description(row),
                "missionCode": row.get("mission_code"),
            }
        )

    for row in pending_bonus_rows:
        beneficiary_bucket = (
            referrer if row["beneficiary_type"] == "REFERRER" else referee
        )
        amount = int(row["amount"])
        beneficiary_bucket["pending"] += amount

        if beneficiary_bucket["nextEligibleReward"] == 0:
            beneficiary_bucket["nextEligibleReward"] = amount

        items.append(
            {
                "beneficiaryType": row["beneficiary_type"],
                "rewardType": "BONUS",
                "rewardSource": "MISSION_BONUS",
                "status": "PENDING",
                "amount": amount,
                "description": (
                    "Optional mission bonus pending successful completion "
                    "of qualifying requirements"
                ),
                "missionCode": row["mission_code"],
            }
        )

    referrer["totalPotential"] = referrer["earned"] + referrer["pending"]
    referee["totalPotential"] = referee["earned"] + referee["pending"]

    disclosures = await _get_reward_disclosures(
        ["GENERAL_INFO_ONLY", "REWARD_CONDITIONAL"]
    )
    compliance = _build_compliance_payload()

    return {
        "referralTrackId": referral_track_id,
        "currency": "ZAR",
        "generatedAt": _utcnow(),
        "referrer": referrer,
        "referee": referee,
        "count": len(items),
        "items": items,
        "disclosures": disclosures,
        "compliance": compliance,
    }


async def get_reward_summary_for_referrer(
    referrer_ucn: str,
    tenant_code: str,
) -> Dict[str, Any]:
    reward_rows = await _get_reward_rows_for_referrer(referrer_ucn, tenant_code)
    pending_bonus_rows = await _get_pending_mission_bonus_rows_for_referrer(
        referrer_ucn,
        tenant_code,
    )
    counts = await _get_referral_counts_for_referrer(referrer_ucn, tenant_code)

    totals = _blank_totals()

    for row in reward_rows:
        amount = int(row["amount"])
        if row["status"] == "APPLIED":
            totals["earned"] += amount

    pending_bonuses_count = 0

    for row in pending_bonus_rows:
        amount = int(row["amount"])
        totals["pending"] += amount
        pending_bonuses_count += 1

        if totals["nextEligibleReward"] == 0:
            totals["nextEligibleReward"] = amount

    totals["totalPotential"] = totals["earned"] + totals["pending"]

    disclosures = await _get_reward_disclosures(
        ["GENERAL_INFO_ONLY", "REWARD_CONDITIONAL"]
    )
    compliance = _build_compliance_payload()

    return {
        "referrerUcn": referrer_ucn,
        "currency": "ZAR",
        "generatedAt": _utcnow(),
        "totals": totals,
        "referralsCount": counts["referralsCount"],
        "completedReferralsCount": counts["completedReferralsCount"],
        "pendingBonusesCount": pending_bonuses_count,
        "count": len(reward_rows) + len(pending_bonus_rows),
        "disclosures": disclosures,
        "compliance": compliance,
    }