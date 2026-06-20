import datetime
from typing import Optional, Dict, Any, Tuple

from utils.db import get_connection
from utils.kafka import publish_event

try:
    from utils.crypto import hash_ucn
except Exception:
    import hashlib

    def hash_ucn(raw: str) -> str:
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _isoz(dt: datetime.datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def validate_referral_code_and_create_instance(
    *,
    referral_code: str,
    device_fingerprint: str,
    ip_address: Optional[str] = None,
    qr_payload: Optional[str] = None,
) -> Tuple[Dict[str, Any], int]:
    """
    Referral Domain Only:
    - Validates referral_code by resolving referrer_codes.
    - If valid: creates referral_instances row and returns referral_track_id (golden thread).
    - If invalid: returns valid=False and no referral_track_id (aligned to updated schema).

    Notes:
    - No campaign logic here (strict separation).
    - No raw UCN emitted; only hashes.
    """

    if not referral_code or not referral_code.strip():
        return {"error": "referral_code is required"}, 400
    if not device_fingerprint or not device_fingerprint.strip():
        return {"error": "device_fingerprint is required"}, 400

    referral_code_norm = referral_code.strip().upper()
    device_fingerprint = device_fingerprint.strip()

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Resolve referrer registry record
        cur.execute(
            """
            SELECT referrer_code_id, referrer_ucn, gaming_handle
            FROM referrer_codes
            WHERE UPPER(referral_code) = UPPER(%s)
            LIMIT 1
            """,
            (referral_code_norm,),
        )
        row = cur.fetchone()

        # ✅ NEW: invalid code returns {valid:false} (no 404)
        if not row:
            # Optional: emit a PII-safe event for fraud/telemetry
            publish_event(
                "referral-events",
                {
                    "eventType": "REFERRAL_VALIDATE_FAILED",
                    "referralCode": referral_code_norm,
                    "deviceFingerprint": device_fingerprint,
                    "ipAddress": ip_address,
                    "qrPayload": qr_payload,
                    "timestamp": _isoz(datetime.datetime.now(datetime.timezone.utc)),
                    "reason": "INVALID_CODE",
                },
            )
            return {
                "valid": False,
                "referral_track_id": None,
                "gaming_handle": None,
            }, 200

        referrer_code_id, referrer_ucn, gaming_handle = row

        # Create referral instance (golden thread starts here)
        cur.execute(
            """
            INSERT INTO referral_instances
              (referrer_code_id, referral_code, referrer_ucn, status)
            VALUES
              (%s, %s, %s, 'VALIDATED')
            RETURNING referral_track_id
            """,
            (referrer_code_id, referral_code_norm, referrer_ucn),
        )
        referral_track_id = str(cur.fetchone()[0])

        conn.commit()

    finally:
        cur.close()
        conn.close()

    # Emit a PII-safe event (no raw UCN)
    publish_event(
        "referral-events",
        {
            "eventType": "REFERRAL_VALIDATED",
            "referralTrackId": referral_track_id,
            "referralCode": referral_code_norm,
            "referrerUCNHash": hash_ucn(str(referrer_ucn)),
            "gamingHandle": gaming_handle,
            "deviceFingerprint": device_fingerprint,
            "ipAddress": ip_address,
            "qrPayload": qr_payload,
            "timestamp": _isoz(datetime.datetime.now(datetime.timezone.utc)),
        },
    )

    return {
        "valid": True,
        "referral_track_id": referral_track_id,
        "gaming_handle": gaming_handle,
    }, 200