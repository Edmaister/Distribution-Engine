from __future__ import annotations

from services.data_quality_service import validate_consumer_experience_integrity


def test_validate_consumer_experience_integrity_passes_clean_journey():
    report = validate_consumer_experience_integrity(
        tenant_code="FNB",
        referrer_ucn="900010",
        referral_track_id="track-1",
        leaderboard_code="GLOBAL_OVERALL",
        profile=[
            {
                "referral_track_id": "track-1",
                "tenant_code": "FNB",
                "referrer_ucn": "900010",
            }
        ],
        rewards={
            "referrerUcn": "900010",
            "referralsCount": 1,
        },
        missions={
            "core": [{"referralTrackId": "track-1", "missionCode": "ACCOUNT_OPENED"}],
            "boost": [],
            "milestone": [],
        },
        leaderboard={
            "entry": {
                "referrer_ucn": "900010",
                "tenant_code": "FNB",
                "leaderboard_code": "GLOBAL_OVERALL",
            }
        },
        insurance_proof={
            "tenant_code": "FNB",
            "referral_track_id": "track-1",
        },
    )

    assert report == {
        "status": "ok",
        "issueCount": 0,
        "criticalCount": 0,
        "warningCount": 0,
        "issues": [],
    }


def test_validate_consumer_experience_integrity_flags_cross_join_mismatches():
    report = validate_consumer_experience_integrity(
        tenant_code="FNB",
        referrer_ucn="900010",
        referral_track_id="track-1",
        leaderboard_code="GLOBAL_OVERALL",
        profile=[
            {
                "referral_track_id": "track-1",
                "tenant_code": "PNP",
                "referrer_ucn": "900010",
            }
        ],
        rewards={
            "referrerUcn": "900011",
            "referralsCount": 2,
        },
        missions={
            "core": [{"referralTrackId": "track-2", "missionCode": "ACCOUNT_OPENED"}],
            "boost": [],
            "milestone": [],
        },
        leaderboard={
            "entry": {
                "referrer_ucn": "900010",
                "tenant_code": "FNB",
                "leaderboard_code": "WEEKLY",
            }
        },
        insurance_proof={
            "tenant_code": "FNB",
            "referral_track_id": "track-3",
        },
    )

    assert report["status"] == "failed"
    assert report["criticalCount"] == 4
    assert report["warningCount"] == 2

    codes = {issue["code"] for issue in report["issues"]}
    assert codes == {
        "profile.tenant_mismatch",
        "rewards.referrer_mismatch",
        "rewards.referral_count_mismatch",
        "missions.referral_missing",
        "leaderboard.code_mismatch",
        "proof.referral_mismatch",
    }
