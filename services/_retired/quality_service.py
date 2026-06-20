# services/quality_service.py

from typing import Dict
from utils.db import db_cursor


def get_metrics(referrer_hash: str, window_days: int) -> Dict[str, float]:
    """
    Rolling metrics within window_days.

    Returns:
        {activations: int, hve: int, qr: float}

    HVE = completed referral OR reward of type SALARY/DEBIT_ORDER.
    """

    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM referrals
            WHERE referrer_ucn_encrypted = %s
              AND status = 'ACTIVATED'
              AND created_at >= NOW() - (%s || ' days')::INTERVAL
            """,
            (referrer_hash, window_days),
        )
        activations = int(cursor.fetchone()[0])

        cursor.execute(
            """
            SELECT
              COALESCE((
                SELECT COUNT(*)
                FROM referrals r
                WHERE r.referrer_ucn_encrypted = %s
                  AND r.status = 'COMPLETED'
                  AND r.created_at >= NOW() - (%s || ' days')::INTERVAL
              ), 0)
              +
              COALESCE((
                SELECT COUNT(*)
                FROM referral_rewards rr
                JOIN referrals r2
                  ON r2.referral_track_id = rr.referral_track_id
                WHERE r2.referrer_ucn_encrypted = %s
                  AND rr.reward_type IN ('SALARY', 'DEBIT_ORDER')
                  AND rr.created_at >= NOW() - (%s || ' days')::INTERVAL
              ), 0) AS hve
            """,
            (referrer_hash, window_days, referrer_hash, window_days),
        )
        hve = int(cursor.fetchone()[0])

    qr = hve / activations if activations > 0 else 0.0

    return {
        "activations": activations,
        "hve": hve,
        "qr": float(qr),
    }