"""Wire system events to gamification (skeleton).
If you centralize events in Kafka, subscribe and route to:
 - services.gamification_service.on_referral_created
 - services.gamification_service.on_reward_applied
"""
from ...services.gamification_service import on_referral_created, on_reward_applied

def handle_event(evt: dict):
    et = evt.get("eventType")
    rh = evt.get("referrerHash")
    if et == "REFERRAL_CODE_ISSUED" and rh:
        on_referral_created(rh)
    elif et in ("REWARD_APPLIED", "REFERRAL_REWARDED") and rh:
        on_reward_applied(rh, evt.get("rewardType", "UNKNOWN"))
