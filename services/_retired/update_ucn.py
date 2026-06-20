# services/update_ucn.py
# Purpose:
#   Capture the referee's UCN for a validated referral instance (golden thread),
#   store it in the referral domain, and emit a PII-safe event.
#
# This version aligns with the STRICT domain model:
#   - Referral share code (hashed/encrypted derivative of referrer UCN) is created and stored in referrer_codes
#   - referral_track_id is created ONLY when the share code is validated/used (referral_instances row)
#   - referee UCN is captured AGAINST referral_track_id (not referral_code)
#
# Key changes vs legacy:
#   - Uses referral_instances (NOT referrals)
#   - No campaign_code handling (strict separation)
#   - Accepts referral_track_id input (golden thread)
#   - Stores raw referee UCN in DB (allowed per your rule), but NEVER surfaces or logs it
#   - Emits only a one-way hash in events (no raw UCN)
#   - Idempotent update: will not overwrite if already captured
#
# Tables used (Referral Domain):
#   referral_instances(referral_track_id, referee_ucn, status, updated_at, ...)
#
# Security:
#   - Do NOT emit raw UCN. Emit only one-way hash for dedupe/fraud/analytics.
#   - Do NOT log raw UCN.

import datetime
from typing import Tuple, Dict, Any

from utils.db import get_connection
from utils.kafka import publish_event

# Optional crypto (hash only needed for event emission)
try:
    from utils.crypto import hash_ucn  # if you have it
except Exception:
    import hashlib

    def hash_ucn(raw: str) -> str:
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _isoz(dt: datetime.datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def capture_referee_ucn(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Capture referee UCN for an existing referral instance.

    Args:
        data: { "referralTrackId": str, "refereeUCN": str }

    Returns:
        (payload, http_status)
    """
    referral_track_id = (data or {}).get("referralTrackId") or (data or {}).get("referral_track_id")
    referee_ucn_raw = (data or {}).get("refereeUCN") or (data or {}).get("referee_ucn")

    if not referral_track_id or not referee_ucn_raw:
        return ({"status": "error", "message": "referralTrackId and refereeUCN required"}, 400)

    referral_track_id = str(referral_track_id).strip()
    referee_ucn_raw = str(referee_ucn_raw).strip()

    # Hash for event emission (never raw)
    referee_ucn_hash = hash_ucn(referee_ucn_raw)

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Idempotent update: do not overwrite if already captured
        cur.execute(
            """
            UPDATE referral_instances
               SET referee_ucn = %s,
                   status = 'UCN_CAPTURED',
                   updated_at = NOW()
             WHERE referral_track_id = %s
               AND referee_ucn IS NULL
            RETURNING referral_track_id
            """,
            (referee_ucn_raw, referral_track_id),
        )
        row = cur.fetchone()

        if not row:
            # Either: instance not found OR already captured.
            cur.execute(
                """
                SELECT referee_ucn IS NOT NULL AS already_captured
                FROM referral_instances
                WHERE referral_track_id = %s
                """,
                (referral_track_id,),
            )
            chk = cur.fetchone()
            if not chk:
                return ({"status": "error", "message": "Referral instance not found"}, 404)

            already_captured = bool(chk[0])

            # Emit "skipped" event for auditing (still no raw UCN)
            publish_event(
                "referral-events",
                {
                    "eventType": "REFEREE_UCN_CAPTURED_SKIPPED",
                    "reason": "ALREADY_CAPTURED" if already_captured else "UNKNOWN",
                    "referralTrackId": referral_track_id,
                    "refereeUCNHash": referee_ucn_hash,
                    "timestamp": _isoz(datetime.datetime.now(datetime.timezone.utc)),
                },
            )
            return ({"status": "ok", "message": "UCN already captured"}, 200)

        conn.commit()
    finally:
        cur.close()
        conn.close()

    # Emit PII-safe event
    publish_event(
        "referral-events",
        {
            "eventType": "REFEREE_UCN_CAPTURED",
            "referralTrackId": referral_track_id,
            "refereeUCNHash": referee_ucn_hash,
            "timestamp": _isoz(datetime.datetime.now(datetime.timezone.utc)),
        },
    )

    # Do NOT return/surface raw UCN
    return ({"status": "success", "message": "UCN captured", "referralTrackId": referral_track_id}, 201)