from fastapi import APIRouter, Depends, HTTPException

from services.reward_service import RewardInstruction, apply_reward
from utils.security import require_partner_key

from ..schemas.rewards import RewardApply

router = APIRouter(
    prefix="/rewards",
    tags=["rewards"],
    dependencies=[Depends(require_partner_key)],
)


@router.post("/apply")
async def apply_reward_api(
    payload: RewardApply,
    identity=Depends(require_partner_key),
):
    tenant_code = identity["tenant_code"]

    instruction = RewardInstruction(
        tenant_code=tenant_code,
        referral_track_id=payload.referral_track_id,
        beneficiary_type=payload.beneficiary_type,
        beneficiary_ref=payload.beneficiary_ref,
        product=payload.product,
        sub_product=payload.sub_product,
        reward_type=payload.reward_type,
        amount=payload.amount,
        reward_source=payload.reward_source,
        mission_code=payload.mission_code,
        status=payload.status,
    )

    try:
        return await apply_reward(instruction)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
