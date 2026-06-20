# Data Quality Checks

This note defines the first enterprise-readiness data-quality gate for the consumer value journey. The check is intentionally read-only: it validates whether the objects we are about to join for a consumer view actually belong together.

## Consumer Journey Integrity

The validator in `services/data_quality_service.py` checks these joins:

| Section | Check | Severity |
| --- | --- | --- |
| Profile referrals | Requested referral track id is present in the referrer's referral set | Critical |
| Profile referrals | Referral tenant and referrer match the aggregate request | Critical |
| Rewards | Reward summary referrer matches the aggregate request | Critical |
| Rewards | Reward referral count matches the profile referral set when both are present | Warning |
| Missions | Mission progress referral ids belong to the profile referral set | Critical |
| Leaderboard | Leaderboard entry tenant and referrer match the aggregate request | Critical |
| Leaderboard | Leaderboard code matches the requested leaderboard | Warning |
| Insurance proof | Proof tenant and referral track id match the aggregate request | Critical |

## Operating Rule

Treat `failed` reports as release-blocking for any journey that surfaces proof, rewards, or leaderboard position to a customer. Treat `warning` reports as a reconciliation item: the page may still be safe to show, but the counts or leaderboard context need review before release sign-off.

## Repair Guidance

Start with the section and code in the report:

| Code family | First repair action |
| --- | --- |
| `profile.*` | Check `referral_instances` tenant, referrer, and referral track attribution. |
| `rewards.*` | Rebuild or inspect reward summary joins against `referral_instances` for the referrer. |
| `missions.*` | Repair `user_mission_progress` referral attribution before showing progress. |
| `leaderboard.*` | Rebuild or filter the leaderboard entry by tenant, referrer, and requested leaderboard code. |
| `proof.*` | Reload proof for the requested tenant/referral or show proof unavailable. |

## Verification

Run:

```bash
python -m pytest test/test_data_quality_service.py -q
```
