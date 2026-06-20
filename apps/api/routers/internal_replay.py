from fastapi import APIRouter, Depends
from utils.security import require_system_admin_key as require_admin_key

from services.replay_service import rebuild_referral_instance

router = APIRouter(
    prefix="/internal/replay",
    tags=["Replay"],
    dependencies=[Depends(require_admin_key)]
)


@router.post("/referrals/{referral_track_id}")
def replay_referral(referral_track_id: str, dry_run: bool = True):
    return rebuild_referral_instance(
        referral_track_id=referral_track_id,
        dry_run=dry_run,
    )
