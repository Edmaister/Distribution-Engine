def build_fulfilment_idempotency_key(
    *,
    tenant_code: str,
    referral_track_id: str | None,
    reward_type: str,
    beneficiary_ucn: str | None,
    journey_stage: str | None = None,
) -> str:
    safe_tenant = tenant_code.strip().upper()
    safe_track_id = (referral_track_id or "NO_TRACK_ID").strip().upper()
    safe_reward_type = reward_type.strip().upper()
    safe_beneficiary = (beneficiary_ucn or "NO_BENEFICIARY").strip().upper()
    safe_stage = (journey_stage or "DEFAULT").strip().upper()

    return (
        f"{safe_tenant}:"
        f"{safe_track_id}:"
        f"{safe_reward_type}:"
        f"{safe_beneficiary}:"
        f"{safe_stage}"
    )