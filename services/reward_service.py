from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
import uuid

from utils.db import db_connection
from utils.logging import get_logger
from services.fulfilment_events import publish_reward_fulfilment_requested

try:
    from utils.kafka import publish_event
except Exception:
    publish_event = None

try:
    from utils.metrics import rewards_applied_inc
except Exception:
    rewards_applied_inc = None


logger = get_logger(__name__)

REWARD_NS = uuid.UUID("12345678-1234-5678-1234-567812345678")

VALID_BENEFICIARY_TYPES = {"REFERRER", "REFEREE"}
VALID_REWARD_SOURCES = {"BASE", "MISSION_BONUS"}
VALID_REWARD_STATUSES = {
    "APPLIED",
    "EARNED",
    "PENDING_FULFILMENT",
    "FULFILLED",
    "FAILED",
    "REVERSED",
}


@dataclass
class RewardInstruction:
    tenant_code: str
    referral_track_id: str
    beneficiary_type: str
    beneficiary_ref: str
    product: str
    sub_product: Optional[str]
    reward_type: str
    amount: Decimal
    journey_code: Optional[str] = None
    milestone_code: Optional[str] = None
    reward_source: str = "BASE"
    mission_code: Optional[str] = None
    status: str = "APPLIED"


def _quantize_amount(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _validate_instruction(instruction: RewardInstruction) -> None:
    if not instruction.tenant_code:
        raise ValueError("tenant_code is required")
    if not instruction.referral_track_id:
        raise ValueError("referral_track_id is required")
    if instruction.beneficiary_type not in VALID_BENEFICIARY_TYPES:
        raise ValueError(f"Invalid beneficiary_type: {instruction.beneficiary_type}")
    if not instruction.beneficiary_ref:
        raise ValueError("beneficiary_ref is required")
    if not instruction.product:
        raise ValueError("product is required")
    if not instruction.reward_type:
        raise ValueError("reward_type is required")
    if instruction.reward_source not in VALID_REWARD_SOURCES:
        raise ValueError(f"Invalid reward_source: {instruction.reward_source}")
    if instruction.status not in VALID_REWARD_STATUSES:
        raise ValueError(f"Invalid status: {instruction.status}")
    if instruction.amount <= Decimal("0"):
        raise ValueError("amount must be > 0")


def _derive_business_key(
    referral_track_id: str,
    beneficiary_type: str,
    beneficiary_ref: str,
    product: str,
    reward_type: str,
    reward_source: str,
    mission_code: Optional[str],
) -> str:
    raw = (
        f"{referral_track_id}|{beneficiary_type}|{beneficiary_ref}|"
        f"{product}|{reward_type}|{reward_source}|{mission_code or ''}"
    )
    return str(uuid.uuid5(REWARD_NS, raw))


def _row_to_dict(row: Any) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "tenant_code": row["tenant_code"],
        "referral_track_id": row["referral_track_id"],
        "beneficiary_type": row["beneficiary_type"],
        "beneficiary_ref": row["beneficiary_ref"],
        "product": row["product"],
        "sub_product": row["sub_product"],
        "reward_type": row["reward_type"],
        "amount": float(row["amount"]),
        "status": row["status"],
        "created_at": (
            row["created_at"].isoformat()
            if hasattr(row["created_at"], "isoformat")
            else str(row["created_at"])
        ),
        "reward_source": row["reward_source"],
        "mission_code": row["mission_code"],
    }


REWARD_SELECT_FIELDS = """
    id,
    tenant_code,
    referral_track_id,
    beneficiary_type,
    beneficiary_ref,
    product,
    sub_product,
    reward_type,
    amount,
    status,
    created_at,
    reward_source,
    mission_code
"""


async def _publish_reward_applied_event(payload: Dict[str, Any]) -> None:
    if not publish_event:
        logger.debug("reward.applied event skipped because publisher is unavailable")
        return

    try:
        publish_event(
            "reward.applied",
            {
                **payload,
                "event_type": "REWARD_APPLIED",
                "version": 2,
            },
        )
    except Exception as e:
        logger.warning("Failed to publish reward.applied event: %s", e)


async def _record_reward_metric(payload: Dict[str, Any]) -> None:
    if not rewards_applied_inc:
        return

    try:
        rewards_applied_inc(
            product=payload["product"],
            reward_type=payload["reward_type"],
        )
    except Exception:
        logger.debug("Failed to increment reward metric", exc_info=True)


async def apply_reward(instruction: RewardInstruction) -> Dict[str, Any]:
    _validate_instruction(instruction)

    amount = _quantize_amount(instruction.amount)

    business_key = _derive_business_key(
        referral_track_id=instruction.referral_track_id,
        beneficiary_type=instruction.beneficiary_type,
        beneficiary_ref=instruction.beneficiary_ref,
        product=instruction.product,
        reward_type=instruction.reward_type,
        reward_source=instruction.reward_source,
        mission_code=instruction.mission_code,
    )

    logger.info(
        "Applying reward: tenant_code=%s business_key=%s track_id=%s beneficiary_type=%s "
        "beneficiary_ref=%s product=%s sub_product=%s reward_type=%s reward_source=%s "
        "mission_code=%s amount=%s",
        instruction.tenant_code,
        business_key,
        instruction.referral_track_id,
        instruction.beneficiary_type,
        instruction.beneficiary_ref,
        instruction.product,
        instruction.sub_product,
        instruction.reward_type,
        instruction.reward_source,
        instruction.mission_code,
        str(amount),
    )

    try:
        async with db_connection() as conn:
            async with conn.transaction():
                result = await conn.execute(
                    """
                    INSERT INTO rewards (
                        tenant_code,
                        referral_track_id,
                        beneficiary_type,
                        beneficiary_ref,
                        product,
                        sub_product,
                        reward_type,
                        amount,
                        status,
                        reward_source,
                        mission_code
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT DO NOTHING
                    """,
                    instruction.tenant_code,
                    instruction.referral_track_id,
                    instruction.beneficiary_type,
                    instruction.beneficiary_ref,
                    instruction.product,
                    instruction.sub_product,
                    instruction.reward_type,
                    amount,
                    instruction.status,
                    instruction.reward_source,
                    instruction.mission_code,
                )

                inserted = str(result).upper().endswith(" 1")

                if instruction.reward_source == "BASE":
                    row = await conn.fetchrow(
                        f"""
                        SELECT {REWARD_SELECT_FIELDS}
                        FROM rewards
                        WHERE referral_track_id = $1
                          AND tenant_code = $2
                          AND beneficiary_type = $3
                          AND product = $4
                          AND reward_type = $5
                          AND reward_source = 'BASE'
                        ORDER BY id DESC
                        LIMIT 1
                        """,
                        instruction.referral_track_id,
                        instruction.tenant_code,
                        instruction.beneficiary_type,
                        instruction.product,
                        instruction.reward_type,
                    )
                else:
                    row = await conn.fetchrow(
                        f"""
                        SELECT {REWARD_SELECT_FIELDS}
                        FROM rewards
                        WHERE referral_track_id = $1
                          AND tenant_code = $2
                          AND beneficiary_type = $3
                          AND mission_code = $4
                          AND reward_source = 'MISSION_BONUS'
                        ORDER BY id DESC
                        LIMIT 1
                        """,
                        instruction.referral_track_id,
                        instruction.tenant_code,
                        instruction.beneficiary_type,
                        instruction.mission_code,
                    )

        if row is None:
            raise RuntimeError("Reward write/read failed: no row returned")

        payload = _row_to_dict(row)
        payload["business_key"] = business_key
        payload["inserted"] = inserted

        await _publish_reward_applied_event(payload)
        await _record_reward_metric(payload)
        
        if inserted:
            await publish_reward_fulfilment_requested(
                tenant_code=payload["tenant_code"],
                reward_id=str(payload["id"]),
                reward_type=payload["reward_type"],
                reward_value=float(payload["amount"]),
                recipient_ucn=payload["beneficiary_ref"],
                currency="ZAR",
                journey_code=instruction.journey_code,
                milestone_code=instruction.milestone_code,
                product_code=payload["product"],
                correlation_id=payload["referral_track_id"],
                metadata={
                    "referral_track_id": payload["referral_track_id"],
                    "beneficiary_type": payload["beneficiary_type"],
                    "reward_source": payload["reward_source"],
                    "mission_code": payload["mission_code"],
                    "business_key": payload["business_key"],
                    "inserted": payload["inserted"],
                },
            )

        return payload

    except Exception as e:
        logger.exception("Failed to apply reward: %s", e)
        raise


def build_base_reward_instructions(
    referral_row: Dict[str, Any],
    reward_policy: Dict[str, Any],
) -> List[RewardInstruction]:
    instructions: List[RewardInstruction] = []

    tenant_code = referral_row["tenant_code"]
    referral_track_id = referral_row["referral_track_id"]
    product = referral_row["product"]
    sub_product = referral_row.get("sub_product")

    referrer_ref = referral_row.get("referrer_ucn_hash") or referral_row.get("referrer_ucn")
    referee_ref = referral_row.get("referee_ucn_hash") or referral_row.get("referee_ucn")

    reward_type = reward_policy["reward_type"]
    journey_code = referral_row.get("journey_code")
    milestone_code = referral_row.get("status")

    referrer_amount = Decimal(str(reward_policy.get("referrer_reward_amount") or 0))
    if referrer_amount > 0 and referrer_ref:
        instructions.append(
            RewardInstruction(
                tenant_code=tenant_code,
                referral_track_id=referral_track_id,
                beneficiary_type="REFERRER",
                beneficiary_ref=str(referrer_ref),
                product=product,
                sub_product=sub_product,
                reward_type=reward_type,
                amount=referrer_amount,
                journey_code=journey_code,
                milestone_code=milestone_code,
            )
        )

    allow_referee_reward = bool(reward_policy.get("allow_referee_reward"))
    referee_amount = Decimal(str(reward_policy.get("referee_reward_amount") or 0))

    if (
        allow_referee_reward
        and referee_amount > 0
        and referee_ref
        and str(referee_ref) != str(referrer_ref)
    ):
        instructions.append(
            RewardInstruction(
                tenant_code=tenant_code,
                referral_track_id=referral_track_id,
                beneficiary_type="REFEREE",
                beneficiary_ref=str(referee_ref),
                product=product,
                sub_product=sub_product,
                reward_type=reward_type,
                amount=referee_amount,
                journey_code=journey_code,
                milestone_code=milestone_code,
            )
        )

    return instructions


def build_mission_reward_instruction(
    tenant_code: str,
    referral_track_id: str,
    beneficiary_type: str,
    beneficiary_ref: str,
    product: str,
    sub_product: Optional[str],
    reward_type: str,
    amount: Decimal,
    mission_code: str,
    status: str = "APPLIED",
) -> RewardInstruction:
    return RewardInstruction(
        tenant_code=tenant_code,
        referral_track_id=referral_track_id,
        beneficiary_type=beneficiary_type,
        beneficiary_ref=beneficiary_ref,
        product=product,
        sub_product=sub_product,
        reward_type=reward_type,
        amount=amount,
        reward_source="MISSION_BONUS",
        mission_code=mission_code,
        status=status,
    )


async def get_reward_by_id(
    reward_id: int,
    tenant_code: str,
) -> Optional[Dict[str, Any]]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            f"""
            SELECT {REWARD_SELECT_FIELDS}
            FROM rewards
            WHERE id = $1
              AND tenant_code = $2
            """,
            reward_id,
            tenant_code,
        )

    return _row_to_dict(row) if row else None


async def list_rewards_for_referral(
    referral_track_id: str,
    tenant_code: str,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            f"""
            SELECT {REWARD_SELECT_FIELDS}
            FROM rewards
            WHERE referral_track_id = $1
              AND tenant_code = $2
            ORDER BY created_at DESC, id DESC
            LIMIT $3
            """,
            referral_track_id,
            tenant_code,
            limit,
        )

    return [_row_to_dict(row) for row in rows]


async def list_rewards_for_beneficiary(
    beneficiary_type: str,
    beneficiary_ref: str,
    tenant_code: str,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            f"""
            SELECT {REWARD_SELECT_FIELDS}
            FROM rewards
            WHERE beneficiary_type = $1
              AND beneficiary_ref = $2
              AND tenant_code = $3
            ORDER BY created_at DESC, id DESC
            LIMIT $4
            """,
            beneficiary_type,
            beneficiary_ref,
            tenant_code,
            limit,
        )

    return [_row_to_dict(row) for row in rows]
