from decimal import Decimal
from typing import Optional


from pydantic import BaseModel


class RewardApply(BaseModel):
    referral_track_id: str
    beneficiary_type: str
    beneficiary_ref: str
    reward_type: str
    product: str
    amount: Decimal
    sub_product: Optional[str] = None
    reward_source: str = "BASE"
    mission_code: Optional[str] = None
    status: str = "APPLIED"
