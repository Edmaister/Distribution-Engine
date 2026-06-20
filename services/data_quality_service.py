from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class DataQualityIssue:
    section: str
    severity: str
    code: str
    message: str
    action: str

    def as_dict(self) -> dict[str, str]:
        return {
            "section": self.section,
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "action": self.action,
        }


def _norm(value: Any) -> str:
    return str(value or "").strip()


def _upper(value: Any) -> str:
    return _norm(value).upper()


def _items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _mission_items(missions: dict[str, Any] | None) -> Iterable[dict[str, Any]]:
    if not isinstance(missions, dict):
        return []

    flattened: list[dict[str, Any]] = []
    for group in ("core", "boost", "milestone"):
        flattened.extend(_items(missions.get(group)))
    return flattened


def _add_issue(
    issues: list[DataQualityIssue],
    *,
    section: str,
    severity: str,
    code: str,
    message: str,
    action: str,
) -> None:
    issues.append(
        DataQualityIssue(
            section=section,
            severity=severity,
            code=code,
            message=message,
            action=action,
        )
    )


def _report(issues: list[DataQualityIssue]) -> dict[str, Any]:
    if any(issue.severity == "critical" for issue in issues):
        status = "failed"
    elif issues:
        status = "warning"
    else:
        status = "ok"

    return {
        "status": status,
        "issueCount": len(issues),
        "criticalCount": sum(1 for issue in issues if issue.severity == "critical"),
        "warningCount": sum(1 for issue in issues if issue.severity == "warning"),
        "issues": [issue.as_dict() for issue in issues],
    }


def validate_consumer_experience_integrity(
    *,
    tenant_code: str,
    referrer_ucn: str,
    referral_track_id: str | None = None,
    leaderboard_code: str = "GLOBAL_OVERALL",
    profile: list[dict[str, Any]] | None = None,
    rewards: dict[str, Any] | None = None,
    missions: dict[str, Any] | None = None,
    leaderboard: dict[str, Any] | None = None,
    insurance_proof: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate cross-surface joins for the consumer value journey."""

    expected_tenant = _upper(tenant_code)
    expected_referrer = _norm(referrer_ucn)
    expected_track_id = _norm(referral_track_id)
    expected_leaderboard = _upper(leaderboard_code)
    issues: list[DataQualityIssue] = []

    referral_rows = profile or []
    referral_ids = {
        _norm(row.get("referral_track_id") or row.get("referralTrackId"))
        for row in referral_rows
        if _norm(row.get("referral_track_id") or row.get("referralTrackId"))
    }

    if expected_track_id and expected_track_id not in referral_ids:
        _add_issue(
            issues,
            section="profile",
            severity="critical",
            code="profile.referral_missing",
            message="Requested referral track id is not present in the profile referral set.",
            action="Confirm the referral belongs to this referrer and tenant before showing linked journey proof.",
        )

    for row in referral_rows:
        row_tenant = row.get("tenant_code") or row.get("tenantCode")
        if row_tenant and _upper(row_tenant) != expected_tenant:
            _add_issue(
                issues,
                section="profile",
                severity="critical",
                code="profile.tenant_mismatch",
                message="A profile referral belongs to a different tenant.",
                action="Repair tenant attribution on the referral row or block the aggregate response.",
            )
        row_referrer = row.get("referrer_ucn") or row.get("referrerUcn")
        if row_referrer and _norm(row_referrer) != expected_referrer:
            _add_issue(
                issues,
                section="profile",
                severity="critical",
                code="profile.referrer_mismatch",
                message="A profile referral belongs to a different referrer.",
                action="Repair referrer attribution before using this row in consumer journey totals.",
            )

    if rewards:
        reward_referrer = rewards.get("referrerUcn") or rewards.get("referrer_ucn")
        if reward_referrer and _norm(reward_referrer) != expected_referrer:
            _add_issue(
                issues,
                section="rewards",
                severity="critical",
                code="rewards.referrer_mismatch",
                message="Reward summary was calculated for a different referrer.",
                action="Rebuild the reward summary using the aggregate referrer id.",
            )
        reward_count = rewards.get("referralsCount") or rewards.get("referrals_count")
        if reward_count is not None and referral_rows and int(reward_count) != len(referral_rows):
            _add_issue(
                issues,
                section="rewards",
                severity="warning",
                code="rewards.referral_count_mismatch",
                message="Reward summary referral count does not match the profile referral set.",
                action="Reconcile reward summary joins against referral_instances for this referrer.",
            )

    for mission in _mission_items(missions):
        mission_track_id = _norm(
            mission.get("referralTrackId") or mission.get("referral_track_id")
        )
        if mission_track_id and referral_ids and mission_track_id not in referral_ids:
            _add_issue(
                issues,
                section="missions",
                severity="critical",
                code="missions.referral_missing",
                message="A mission progress item points at a referral outside the profile set.",
                action="Repair user_mission_progress referral attribution before showing mission progress.",
            )

    leaderboard_entry = leaderboard.get("entry") if isinstance(leaderboard, dict) else None
    if isinstance(leaderboard_entry, dict):
        entry_referrer = leaderboard_entry.get("referrer_ucn") or leaderboard_entry.get("referrerUcn")
        if entry_referrer and _norm(entry_referrer) != expected_referrer:
            _add_issue(
                issues,
                section="leaderboard",
                severity="critical",
                code="leaderboard.referrer_mismatch",
                message="Leaderboard entry belongs to a different referrer.",
                action="Rebuild the leaderboard entry for the aggregate referrer id.",
            )
        entry_tenant = leaderboard_entry.get("tenant_code") or leaderboard_entry.get("tenantCode")
        if entry_tenant and _upper(entry_tenant) != expected_tenant:
            _add_issue(
                issues,
                section="leaderboard",
                severity="critical",
                code="leaderboard.tenant_mismatch",
                message="Leaderboard entry belongs to a different tenant.",
                action="Rebuild or filter leaderboard data by tenant before returning the aggregate.",
            )
        entry_code = leaderboard_entry.get("leaderboard_code") or leaderboard_entry.get("leaderboardCode")
        if entry_code and _upper(entry_code) != expected_leaderboard:
            _add_issue(
                issues,
                section="leaderboard",
                severity="warning",
                code="leaderboard.code_mismatch",
                message="Leaderboard entry was produced for a different leaderboard code.",
                action="Reload leaderboard data for the requested leaderboard code.",
            )

    if insurance_proof:
        proof_tenant = insurance_proof.get("tenant_code") or insurance_proof.get("tenantCode")
        if proof_tenant and _upper(proof_tenant) != expected_tenant:
            _add_issue(
                issues,
                section="insuranceProof",
                severity="critical",
                code="proof.tenant_mismatch",
                message="Insurance proof belongs to a different tenant.",
                action="Block the proof from this consumer response and repair proof scoping.",
            )
        proof_track_id = _norm(
            insurance_proof.get("referral_track_id") or insurance_proof.get("referralTrackId")
        )
        if expected_track_id and proof_track_id and proof_track_id != expected_track_id:
            _add_issue(
                issues,
                section="insuranceProof",
                severity="critical",
                code="proof.referral_mismatch",
                message="Insurance proof belongs to a different referral track id.",
                action="Reload proof for the requested referral or show proof unavailable.",
            )

    return _report(issues)
