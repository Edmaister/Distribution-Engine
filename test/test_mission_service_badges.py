from __future__ import annotations

import uuid

import pytest

from services.badge_service import evaluate_badges_for_hve_event
from utils.db import async_db_cursor


async def _reset(track_id: str, referrer_ucn: str) -> None:
    async with async_db_cursor() as cur:
        await cur.execute(
            "DELETE FROM user_badges WHERE beneficiary_ref = $1",
            referrer_ucn,
        )
        await cur.execute(
            "DELETE FROM referral_instances WHERE referral_track_id = $1",
            track_id,
        )
        await cur.execute(
            "DELETE FROM referrer_codes WHERE referrer_ucn_hash = $1",
            f"hash-{referrer_ucn}",
        )
        await cur.execute("DELETE FROM badge_definitions")


async def _insert_referral_with_hve(track_id: str, referrer_ucn: str) -> None:
    referral_code = f"CODE-{uuid.uuid4().hex[:8]}"
    gaming_handle = f"user-{uuid.uuid4().hex[:8]}"

    async with async_db_cursor() as cur:
        row = await cur.fetchrow(
            """
            INSERT INTO referrer_codes (
                referrer_ucn,
                referrer_ucn_hash,
                referral_code,
                gaming_handle,
                sticker,
                tenant_code,
                segment,
                created_at,
                updated_at
            )
            VALUES (
                $1, $2, $3, $4,
                'TEST', 'TEST', 'TEST',
                NOW(), NOW()
            )
            ON CONFLICT (referrer_ucn_hash) DO UPDATE SET
                referral_code = EXCLUDED.referral_code,
                gaming_handle = EXCLUDED.gaming_handle,
                updated_at = NOW()
            RETURNING referrer_code_id
            """,
            referrer_ucn,
            f"hash-{referrer_ucn}",
            referral_code,
            gaming_handle,
        )

        referrer_code_id = row["referrer_code_id"]

        await cur.execute(
            """
            INSERT INTO referral_instances (
                referral_track_id,
                referrer_code_id,
                referral_code,
                referrer_ucn,
                tenant_code,
                product,
                sub_product,
                status,
                is_complete,
                salary_switched_at,
                created_at,
                updated_at
            )
            VALUES (
                $1, $2, $3, $4,
                $5,
                'TRANSACTIONAL', NULL, 'FUNDED',
                FALSE, NOW(), NOW(), NOW()
            )
            ON CONFLICT (referral_track_id) DO UPDATE SET
                referrer_code_id = EXCLUDED.referrer_code_id,
                referral_code = EXCLUDED.referral_code,
                referrer_ucn = EXCLUDED.referrer_ucn,
                tenant_code = EXCLUDED.tenant_code,
                salary_switched_at = EXCLUDED.salary_switched_at,
                updated_at = NOW()
            """,
            track_id,
            referrer_code_id,
            referral_code,
            referrer_ucn,
            "FNB",
        )


async def _insert_hve_badge() -> None:
    async with async_db_cursor() as cur:
        await cur.execute(
            """
            INSERT INTO badges (
                badge_code,
                title,
                description,
                reward_points
            )
            VALUES (
                'VALUE_DRIVER',
                'Value Driver',
                'Awarded when value is established on your first referral.',
                NULL
            )
            ON CONFLICT (badge_code) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                reward_points = EXCLUDED.reward_points
            """
        )
        await cur.execute(
            """
            INSERT INTO badge_definitions (
                badge_code,
                badge_name,
                badge_description,
                badge_category,
                beneficiary_type,
                trigger_type,
                trigger_value,
                icon_name,
                display_priority,
                regulatory_tags,
                is_active,
                created_at
            )
            VALUES (
                'VALUE_DRIVER',
                'Value Driver',
                'Awarded when value is established on your first referral.',
                'REFERRAL_OUTCOME',
                'REFERRER',
                'HVE_COUNT',
                '1',
                'trending-up',
                1,
                '["TCF","FAIS","MARKET_CONDUCT"]'::jsonb,
                TRUE,
                NOW()
            )
            ON CONFLICT (badge_code) DO UPDATE SET
                badge_name = EXCLUDED.badge_name,
                badge_description = EXCLUDED.badge_description,
                badge_category = EXCLUDED.badge_category,
                beneficiary_type = EXCLUDED.beneficiary_type,
                trigger_type = EXCLUDED.trigger_type,
                trigger_value = EXCLUDED.trigger_value,
                icon_name = EXCLUDED.icon_name,
                display_priority = EXCLUDED.display_priority,
                regulatory_tags = EXCLUDED.regulatory_tags,
                is_active = EXCLUDED.is_active
            """
        )


@pytest.mark.asyncio
async def test_hve_event_awards_badge_once():
    track_id = "77777777-7777-7777-7777-777777777777"
    referrer_ucn = "900007"

    await _reset(track_id, referrer_ucn)
    await _insert_referral_with_hve(track_id, referrer_ucn)
    await _insert_hve_badge()

    first = await evaluate_badges_for_hve_event(
        track_id,
        "SALARY_SWITCHED",
    )

    second = await evaluate_badges_for_hve_event(
        track_id,
        "SALARY_SWITCHED",
    )

    assert len(first) == 1
    assert first[0]["badgeCode"] == "VALUE_DRIVER"

    assert second == []
