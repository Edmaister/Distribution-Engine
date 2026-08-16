from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from utils.db import db_connection

PROGRAMME_ANALYTICS_GUARDRAILS = (
    "ACCOUNT_SCOPED_PROGRAMME_ANALYTICS",
    "PUBLISHED_PROGRAMME_VERSION_DIMENSION_ONLY",
    "TENANT_SAFE_AGGREGATES_ONLY",
    "NO_RAW_IDENTITY_OR_EVENT_PAYLOAD",
    "NO_INCENTIVE_REWARD_PAYOUT_DETAIL",
    "NO_BILLING_SETTLEMENT_OR_MONEY_ACTION",
    "NO_PROVIDER_OR_AUTH_MUTATION",
)

PROGRAMME_ANALYTICS_REDACTIONS = (
    "tenant_code",
    "account_id",
    "raw_event_payload",
    "provider_payload",
    "secret",
    "credential",
    "auth_claim",
    "billing",
    "wallet",
    "payout",
    "settlement",
    "invoice",
    "money",
    "reward_amount",
    "reward_policy_internal_config",
    "user_ucn_encrypted",
    "device_fingerprint",
    "ip_address",
    "qr_payload",
)

MAX_PROGRAMME_ANALYTICS_LIMIT = 100


@dataclass(frozen=True)
class ProgrammeVersionAnalytics:
    programme_version_id: str
    programme_code: str
    programme_name: str
    version_number: int
    version_status: str
    customer_journey_version_id: str
    sub_product_code: str
    published_at: datetime | str | None
    campaign_count: int
    active_campaign_count: int
    referral_count: int
    attributed_referral_count: int
    completed_referral_count: int
    progress_event_count: int
    high_value_event_count: int
    incentive_binding_count: int
    engagement_binding_count: int

    @property
    def attribution_gap_count(self) -> int:
        return max(0, self.referral_count - self.attributed_referral_count)

    @property
    def completion_gap_count(self) -> int:
        return max(0, self.referral_count - self.completed_referral_count)

    @property
    def attribution_rate(self) -> float:
        return _safe_rate(self.attributed_referral_count, self.referral_count)

    @property
    def completion_rate(self) -> float:
        return _safe_rate(self.completed_referral_count, self.referral_count)

    @property
    def high_value_event_rate(self) -> float:
        return _safe_rate(self.high_value_event_count, self.progress_event_count)

    @property
    def performance_signal(self) -> str:
        if self.referral_count <= 0:
            return "NO_TRAFFIC"
        if self.attribution_gap_count > self.completed_referral_count:
            return "OPTIMISE_ATTRIBUTION"
        if self.completion_gap_count > self.completed_referral_count:
            return "OPTIMISE_COMPLETION"
        if self.incentive_binding_count <= 0 and self.engagement_binding_count <= 0:
            return "CONFIGURATION_GAP"
        return "COMPARABLE"

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "programmeVersionId": self.programme_version_id,
            "programmeCode": self.programme_code,
            "programmeName": self.programme_name,
            "versionNumber": self.version_number,
            "versionStatus": self.version_status,
            "customerJourneyVersionId": self.customer_journey_version_id,
            "subProductCode": self.sub_product_code,
            "publishedAt": _isoformat(self.published_at),
            "campaignCount": self.campaign_count,
            "activeCampaignCount": self.active_campaign_count,
            "referralCount": self.referral_count,
            "attributedReferralCount": self.attributed_referral_count,
            "completedReferralCount": self.completed_referral_count,
            "progressEventCount": self.progress_event_count,
            "highValueEventCount": self.high_value_event_count,
            "incentiveBindingCount": self.incentive_binding_count,
            "engagementBindingCount": self.engagement_binding_count,
            "attributionGapCount": self.attribution_gap_count,
            "completionGapCount": self.completion_gap_count,
            "attributionRate": self.attribution_rate,
            "completionRate": self.completion_rate,
            "highValueEventRate": self.high_value_event_rate,
            "performanceSignal": self.performance_signal,
            "guardrails": list(PROGRAMME_ANALYTICS_GUARDRAILS),
            "redactions": list(PROGRAMME_ANALYTICS_REDACTIONS),
        }


@dataclass(frozen=True)
class ProgrammeAnalyticsReadModel:
    account_id: str
    version_count: int
    versions: tuple[ProgrammeVersionAnalytics, ...]
    summary: dict[str, Any]
    data_window_start: datetime | str | None
    data_window_end: datetime | str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "versionCount": self.version_count,
            "versions": [version.to_safe_dict() for version in self.versions],
            "summary": dict(self.summary),
            "dataWindowStart": _isoformat(self.data_window_start),
            "dataWindowEnd": _isoformat(self.data_window_end),
            "guardrails": list(PROGRAMME_ANALYTICS_GUARDRAILS),
            "redactions": list(PROGRAMME_ANALYTICS_REDACTIONS),
            "noRawIdentityOrEventPayloadConfirmed": True,
            "noIncentiveRewardPayoutDetailConfirmed": True,
            "noProviderDispatchConfirmed": True,
            "noAuthBillingSettlementOrMoneyActionConfirmed": True,
        }


async def build_referral_saas_programme_analytics_read_model(
    *,
    account_id: str,
    tenant_code: str,
    limit: int = 50,
    data_window_start: datetime | None = None,
    data_window_end: datetime | None = None,
) -> ProgrammeAnalyticsReadModel:
    safe_account_id = _required_text(account_id, "account_id")
    safe_tenant_code = _required_text(tenant_code, "tenant_code")
    safe_limit = _safe_limit(limit)

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            WITH versions AS (
                SELECT
                    programme_version_id,
                    account_id,
                    programme_code,
                    programme_name,
                    version_number,
                    version_status,
                    customer_journey_version_id,
                    sub_product_code,
                    published_at,
                    jsonb_array_length(
                        COALESCE(incentive_refs_snapshot, '[]'::jsonb)
                    ) AS incentive_binding_count,
                    jsonb_array_length(
                        COALESCE(engagement_refs_snapshot, '[]'::jsonb)
                    ) AS engagement_binding_count
                FROM referral_saas_programme_versions
                WHERE account_id = $1
                  AND version_status IN ('PUBLISHED', 'ACTIVE', 'RETIRED', 'ROLLBACK_READY')
                ORDER BY published_at DESC, version_number DESC
                LIMIT $4
            ),
            campaign_bindings AS (
                SELECT DISTINCT
                    mc.attributes->'referral_saas_programme_binding'->>'programmeVersionId'
                        AS programme_version_id,
                    UPPER(mc.campaign_code) AS campaign_code,
                    COALESCE(mc.is_active, false) AS campaign_is_active
                FROM marketing_campaigns mc
                WHERE UPPER(COALESCE(mc.tenant_code, '')) = UPPER($2)
                  AND mc.attributes ? 'referral_saas_programme_binding'
                  AND COALESCE(
                      mc.attributes->'referral_saas_programme_binding'->>'programmeVersionId',
                      ''
                  ) <> ''
            ),
            campaign_counts AS (
                SELECT
                    programme_version_id,
                    COUNT(DISTINCT campaign_code) AS campaign_count,
                    COUNT(DISTINCT campaign_code) FILTER (WHERE campaign_is_active)
                        AS active_campaign_count
                FROM campaign_bindings
                GROUP BY programme_version_id
            ),
            referral_evidence AS (
                SELECT DISTINCT
                    v.programme_version_id,
                    ri.referral_track_id,
                    COALESCE(ri.is_complete, false) AS is_complete,
                    CASE
                        WHEN ca.campaign_track_id IS NOT NULL THEN true
                        WHEN ri.programme_version_id = v.programme_version_id THEN true
                        ELSE false
                    END AS has_attribution_evidence
                FROM versions v
                LEFT JOIN campaign_bindings cb
                    ON cb.programme_version_id = v.programme_version_id::text
                JOIN referral_instances ri
                    ON UPPER(ri.tenant_code) = UPPER($2)
                LEFT JOIN campaign_referral_links crl
                    ON crl.referral_track_id = ri.referral_track_id
                LEFT JOIN campaign_attributions ca
                    ON ca.campaign_track_id = crl.campaign_track_id
                   AND UPPER(COALESCE(ca.tenant_code, '')) = UPPER(ri.tenant_code)
                WHERE (
                        ri.programme_version_id = v.programme_version_id
                        OR UPPER(COALESCE(ca.campaign_code, '')) = cb.campaign_code
                    )
                  AND ($3::timestamptz IS NULL OR ri.created_at >= $3)
                  AND ($5::timestamptz IS NULL OR ri.created_at <= $5)
            ),
            referral_counts AS (
                SELECT
                    programme_version_id,
                    COUNT(DISTINCT referral_track_id) AS referral_count,
                    COUNT(DISTINCT referral_track_id) FILTER (
                        WHERE has_attribution_evidence
                    ) AS attributed_referral_count,
                    COUNT(DISTINCT referral_track_id) FILTER (
                        WHERE is_complete
                    ) AS completed_referral_count
                FROM referral_evidence
                GROUP BY programme_version_id
            ),
            progress_counts AS (
                SELECT
                    re.programme_version_id,
                    COUNT(*) AS progress_event_count,
                    COUNT(*) FILTER (
                        WHERE UPPER(COALESCE(rpe.event_type, '')) IN (
                            'FUNDED',
                            'DEBIT_ORDER_SWITCHED',
                            'SALARY_SWITCHED',
                            'FIRST_TRANSACTION_COMPLETED'
                        )
                    ) AS high_value_event_count
                FROM referral_evidence re
                JOIN referral_progress_events rpe
                    ON rpe.referral_track_id = re.referral_track_id
                WHERE ($3::timestamptz IS NULL OR rpe.occurred_at >= $3)
                  AND ($5::timestamptz IS NULL OR rpe.occurred_at <= $5)
                GROUP BY re.programme_version_id
            )
            SELECT
                v.programme_version_id,
                v.programme_code,
                v.programme_name,
                v.version_number,
                v.version_status,
                v.customer_journey_version_id,
                v.sub_product_code,
                v.published_at,
                COALESCE(cc.campaign_count, 0) AS campaign_count,
                COALESCE(cc.active_campaign_count, 0) AS active_campaign_count,
                COALESCE(rc.referral_count, 0) AS referral_count,
                COALESCE(rc.attributed_referral_count, 0) AS attributed_referral_count,
                COALESCE(rc.completed_referral_count, 0) AS completed_referral_count,
                COALESCE(pc.progress_event_count, 0) AS progress_event_count,
                COALESCE(pc.high_value_event_count, 0) AS high_value_event_count,
                COALESCE(v.incentive_binding_count, 0) AS incentive_binding_count,
                COALESCE(v.engagement_binding_count, 0) AS engagement_binding_count
            FROM versions v
            LEFT JOIN campaign_counts cc
                ON cc.programme_version_id = v.programme_version_id::text
            LEFT JOIN referral_counts rc
                ON rc.programme_version_id = v.programme_version_id
            LEFT JOIN progress_counts pc
                ON pc.programme_version_id = v.programme_version_id
            ORDER BY v.published_at DESC, v.version_number DESC
            """,
            safe_account_id,
            safe_tenant_code,
            data_window_start,
            safe_limit,
            data_window_end,
        )

    versions = tuple(_analytics_from_row(row) for row in rows)
    return ProgrammeAnalyticsReadModel(
        account_id=safe_account_id,
        version_count=len(versions),
        versions=versions,
        summary=_build_summary(versions),
        data_window_start=data_window_start,
        data_window_end=data_window_end,
    )


def _analytics_from_row(row: Mapping[str, Any]) -> ProgrammeVersionAnalytics:
    return ProgrammeVersionAnalytics(
        programme_version_id=str(row["programme_version_id"]),
        programme_code=str(row["programme_code"]),
        programme_name=str(row["programme_name"]),
        version_number=int(row["version_number"] or 0),
        version_status=str(row["version_status"]),
        customer_journey_version_id=str(row["customer_journey_version_id"]),
        sub_product_code=str(row["sub_product_code"]),
        published_at=row["published_at"],
        campaign_count=int(row["campaign_count"] or 0),
        active_campaign_count=int(row["active_campaign_count"] or 0),
        referral_count=int(row["referral_count"] or 0),
        attributed_referral_count=int(row["attributed_referral_count"] or 0),
        completed_referral_count=int(row["completed_referral_count"] or 0),
        progress_event_count=int(row["progress_event_count"] or 0),
        high_value_event_count=int(row["high_value_event_count"] or 0),
        incentive_binding_count=int(row["incentive_binding_count"] or 0),
        engagement_binding_count=int(row["engagement_binding_count"] or 0),
    )


def _build_summary(versions: tuple[ProgrammeVersionAnalytics, ...]) -> dict[str, Any]:
    referral_count = sum(version.referral_count for version in versions)
    attributed_count = sum(version.attributed_referral_count for version in versions)
    completed_count = sum(version.completed_referral_count for version in versions)
    progress_event_count = sum(version.progress_event_count for version in versions)
    high_value_event_count = sum(version.high_value_event_count for version in versions)
    campaign_count = sum(version.campaign_count for version in versions)
    active_campaign_count = sum(version.active_campaign_count for version in versions)
    latest_version = versions[0] if versions else None
    previous_version = versions[1] if len(versions) > 1 else None

    return {
        "programmeVersionsCompared": len(versions),
        "campaignCount": campaign_count,
        "activeCampaignCount": active_campaign_count,
        "referralCount": referral_count,
        "attributedReferralCount": attributed_count,
        "completedReferralCount": completed_count,
        "progressEventCount": progress_event_count,
        "highValueEventCount": high_value_event_count,
        "attributionGapCount": max(0, referral_count - attributed_count),
        "completionGapCount": max(0, referral_count - completed_count),
        "attributionRate": _safe_rate(attributed_count, referral_count),
        "completionRate": _safe_rate(completed_count, referral_count),
        "highValueEventRate": _safe_rate(high_value_event_count, progress_event_count),
        "analyticsSignal": _summary_signal(versions),
        "latestProgrammeVersionId": (
            latest_version.programme_version_id if latest_version else None
        ),
        "previousProgrammeVersionId": (
            previous_version.programme_version_id if previous_version else None
        ),
        "latestVsPrevious": _compare_latest_to_previous(
            latest_version,
            previous_version,
        ),
    }


def _compare_latest_to_previous(
    latest: ProgrammeVersionAnalytics | None,
    previous: ProgrammeVersionAnalytics | None,
) -> dict[str, Any]:
    if latest is None:
        return {"comparisonSignal": "NO_PUBLISHED_VERSIONS"}
    if previous is None:
        return {"comparisonSignal": "BASELINE_ONLY"}

    completion_rate_change = round(latest.completion_rate - previous.completion_rate, 4)
    attribution_rate_change = round(latest.attribution_rate - previous.attribution_rate, 4)
    referral_count_change = latest.referral_count - previous.referral_count

    if completion_rate_change > 0 or attribution_rate_change > 0:
        signal = "IMPROVED"
    elif completion_rate_change < 0 or attribution_rate_change < 0:
        signal = "REGRESSED"
    else:
        signal = "UNCHANGED"

    return {
        "comparisonSignal": signal,
        "completionRateChange": completion_rate_change,
        "attributionRateChange": attribution_rate_change,
        "referralCountChange": referral_count_change,
    }


def _summary_signal(versions: tuple[ProgrammeVersionAnalytics, ...]) -> str:
    if not versions:
        return "NO_PUBLISHED_PROGRAMME_VERSIONS"
    if all(version.referral_count <= 0 for version in versions):
        return "NO_TRAFFIC"
    latest_signal = versions[0].performance_signal
    if latest_signal != "NO_TRAFFIC":
        return latest_signal
    if any(version.performance_signal == "CONFIGURATION_GAP" for version in versions):
        return "CONFIGURATION_GAP"
    if any(version.performance_signal == "OPTIMISE_ATTRIBUTION" for version in versions):
        return "OPTIMISE_ATTRIBUTION"
    if any(version.performance_signal == "OPTIMISE_COMPLETION" for version in versions):
        return "OPTIMISE_COMPLETION"
    return "COMPARABLE"


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _safe_limit(limit: int) -> int:
    return max(1, min(int(limit), MAX_PROGRAMME_ANALYTICS_LIMIT))


def _required_text(value: Any, field_name: str) -> str:
    safe = str(value or "").strip()
    if not safe:
        raise ValueError(f"{field_name} is required.")
    return safe


def _isoformat(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)
