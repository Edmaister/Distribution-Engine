from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from utils.db import db_connection

JOURNEY_ANALYTICS_GUARDRAILS = (
    "ACCOUNT_SCOPED_JOURNEY_ANALYTICS",
    "PUBLISHED_VERSION_DIMENSION_ONLY",
    "TENANT_SAFE_AGGREGATES_ONLY",
    "NO_RAW_IDENTITY_OR_EVENT_PAYLOAD",
    "NO_REWARD_PAYOUT_DETAIL",
    "NO_PROVIDER_AUTH_BILLING_OR_MONEY_ACTION",
)

JOURNEY_ANALYTICS_REDACTIONS = (
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
    "user_ucn_encrypted",
    "device_fingerprint",
    "ip_address",
    "qr_payload",
)

MAX_JOURNEY_ANALYTICS_LIMIT = 100


@dataclass(frozen=True)
class JourneyVersionAnalytics:
    customer_journey_version_id: str
    customer_journey_code: str
    version_number: int
    version_status: str
    template_code: str
    template_version: str
    published_at: datetime | str | None
    campaign_count: int
    active_campaign_count: int
    referral_count: int
    attributed_referral_count: int
    completed_referral_count: int
    progress_event_count: int
    high_value_event_count: int

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
    def performance_signal(self) -> str:
        if self.referral_count <= 0:
            return "NO_TRAFFIC"
        if self.attribution_gap_count > self.completed_referral_count:
            return "OPTIMISE_ATTRIBUTION"
        if self.completion_gap_count > self.completed_referral_count:
            return "OPTIMISE_COMPLETION"
        return "COMPARABLE"

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "customerJourneyVersionId": self.customer_journey_version_id,
            "customerJourneyCode": self.customer_journey_code,
            "versionNumber": self.version_number,
            "versionStatus": self.version_status,
            "templateCode": self.template_code,
            "templateVersion": self.template_version,
            "publishedAt": _isoformat(self.published_at),
            "campaignCount": self.campaign_count,
            "activeCampaignCount": self.active_campaign_count,
            "referralCount": self.referral_count,
            "attributedReferralCount": self.attributed_referral_count,
            "completedReferralCount": self.completed_referral_count,
            "progressEventCount": self.progress_event_count,
            "highValueEventCount": self.high_value_event_count,
            "attributionGapCount": self.attribution_gap_count,
            "completionGapCount": self.completion_gap_count,
            "attributionRate": self.attribution_rate,
            "completionRate": self.completion_rate,
            "performanceSignal": self.performance_signal,
            "guardrails": list(JOURNEY_ANALYTICS_GUARDRAILS),
            "redactions": list(JOURNEY_ANALYTICS_REDACTIONS),
        }


@dataclass(frozen=True)
class JourneyAnalyticsReadModel:
    account_id: str
    version_count: int
    versions: tuple[JourneyVersionAnalytics, ...]
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
            "guardrails": list(JOURNEY_ANALYTICS_GUARDRAILS),
            "redactions": list(JOURNEY_ANALYTICS_REDACTIONS),
            "noRawIdentityOrEventPayloadConfirmed": True,
            "noRewardPayoutDetailConfirmed": True,
            "noProviderDispatchConfirmed": True,
            "noAuthBillingSettlementOrMoneyActionConfirmed": True,
        }


async def build_referral_saas_journey_analytics_read_model(
    *,
    account_id: str,
    tenant_code: str,
    limit: int = 50,
    data_window_start: datetime | None = None,
    data_window_end: datetime | None = None,
) -> JourneyAnalyticsReadModel:
    safe_account_id = _required_text(account_id, "account_id")
    safe_tenant_code = _required_text(tenant_code, "tenant_code")
    safe_limit = _safe_limit(limit)

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            WITH versions AS (
                SELECT
                    cv.customer_journey_version_id,
                    cv.account_id,
                    cv.customer_journey_code,
                    cv.version_number,
                    cv.version_status,
                    cv.published_at,
                    tv.template_code,
                    tv.template_version
                FROM referral_saas_customer_journey_versions cv
                JOIN referral_saas_journey_template_versions tv
                    ON tv.journey_template_version_id = cv.journey_template_version_id
                WHERE cv.account_id = $1
                  AND cv.version_status IN ('PUBLISHED', 'ACTIVE', 'SUPERSEDED')
                  AND cv.archived_at IS NULL
                ORDER BY cv.published_at DESC, cv.version_number DESC
                LIMIT $4
            ),
            active_bindings AS (
                SELECT DISTINCT
                    b.customer_journey_version_id,
                    UPPER(b.campaign_code) AS campaign_code,
                    COALESCE(mc.is_active, false) AS campaign_is_active
                FROM referral_saas_campaign_journey_bindings b
                LEFT JOIN marketing_campaigns mc
                    ON UPPER(mc.campaign_code) = UPPER(b.campaign_code)
                   AND UPPER(COALESCE(mc.tenant_code, '')) = UPPER($2)
                WHERE b.account_id = $1
                  AND b.binding_status = 'ACTIVE'
                  AND b.unbound_at IS NULL
            ),
            campaign_counts AS (
                SELECT
                    customer_journey_version_id,
                    COUNT(DISTINCT campaign_code) AS campaign_count,
                    COUNT(DISTINCT campaign_code) FILTER (WHERE campaign_is_active)
                        AS active_campaign_count
                FROM active_bindings
                GROUP BY customer_journey_version_id
            ),
            referral_evidence AS (
                SELECT DISTINCT
                    ab.customer_journey_version_id,
                    ri.referral_track_id,
                    COALESCE(ri.is_complete, false) AS is_complete,
                    CASE
                        WHEN ca.campaign_track_id IS NOT NULL THEN true
                        WHEN drl.route_id IS NOT NULL THEN true
                        ELSE false
                    END AS has_attribution_evidence
                FROM active_bindings ab
                JOIN referral_instances ri
                    ON UPPER(ri.tenant_code) = UPPER($2)
                LEFT JOIN campaign_referral_links crl
                    ON crl.referral_track_id = ri.referral_track_id
                LEFT JOIN campaign_attributions ca
                    ON ca.campaign_track_id = crl.campaign_track_id
                   AND UPPER(COALESCE(ca.tenant_code, '')) = UPPER(ri.tenant_code)
                LEFT JOIN distribution_route_referral_links drl
                    ON drl.referral_track_id = ri.referral_track_id
                   AND UPPER(COALESCE(drl.tenant_code, '')) = UPPER(ri.tenant_code)
                LEFT JOIN distribution_opportunities o
                    ON o.opportunity_id = drl.opportunity_id
                   AND UPPER(COALESCE(o.tenant_code, '')) = UPPER(ri.tenant_code)
                WHERE UPPER(COALESCE(ca.campaign_code, o.campaign_code, '')) =
                    ab.campaign_code
                  AND ($3::timestamptz IS NULL OR ri.created_at >= $3)
                  AND ($5::timestamptz IS NULL OR ri.created_at <= $5)
            ),
            referral_counts AS (
                SELECT
                    customer_journey_version_id,
                    COUNT(DISTINCT referral_track_id) AS referral_count,
                    COUNT(DISTINCT referral_track_id) FILTER (
                        WHERE has_attribution_evidence
                    ) AS attributed_referral_count,
                    COUNT(DISTINCT referral_track_id) FILTER (
                        WHERE is_complete
                    ) AS completed_referral_count
                FROM referral_evidence
                GROUP BY customer_journey_version_id
            ),
            progress_counts AS (
                SELECT
                    re.customer_journey_version_id,
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
                GROUP BY re.customer_journey_version_id
            )
            SELECT
                v.customer_journey_version_id,
                v.customer_journey_code,
                v.version_number,
                v.version_status,
                v.template_code,
                v.template_version,
                v.published_at,
                COALESCE(cc.campaign_count, 0) AS campaign_count,
                COALESCE(cc.active_campaign_count, 0) AS active_campaign_count,
                COALESCE(rc.referral_count, 0) AS referral_count,
                COALESCE(rc.attributed_referral_count, 0) AS attributed_referral_count,
                COALESCE(rc.completed_referral_count, 0) AS completed_referral_count,
                COALESCE(pc.progress_event_count, 0) AS progress_event_count,
                COALESCE(pc.high_value_event_count, 0) AS high_value_event_count
            FROM versions v
            LEFT JOIN campaign_counts cc
                ON cc.customer_journey_version_id = v.customer_journey_version_id
            LEFT JOIN referral_counts rc
                ON rc.customer_journey_version_id = v.customer_journey_version_id
            LEFT JOIN progress_counts pc
                ON pc.customer_journey_version_id = v.customer_journey_version_id
            ORDER BY v.published_at DESC, v.version_number DESC
            """,
            safe_account_id,
            safe_tenant_code,
            data_window_start,
            safe_limit,
            data_window_end,
        )

    versions = tuple(_analytics_from_row(row) for row in rows)
    return JourneyAnalyticsReadModel(
        account_id=safe_account_id,
        version_count=len(versions),
        versions=versions,
        summary=_build_summary(versions),
        data_window_start=data_window_start,
        data_window_end=data_window_end,
    )


def _analytics_from_row(row: Mapping[str, Any]) -> JourneyVersionAnalytics:
    return JourneyVersionAnalytics(
        customer_journey_version_id=str(row["customer_journey_version_id"]),
        customer_journey_code=str(row["customer_journey_code"]),
        version_number=int(row["version_number"] or 0),
        version_status=str(row["version_status"]),
        template_code=str(row["template_code"]),
        template_version=str(row["template_version"]),
        published_at=row["published_at"],
        campaign_count=int(row["campaign_count"] or 0),
        active_campaign_count=int(row["active_campaign_count"] or 0),
        referral_count=int(row["referral_count"] or 0),
        attributed_referral_count=int(row["attributed_referral_count"] or 0),
        completed_referral_count=int(row["completed_referral_count"] or 0),
        progress_event_count=int(row["progress_event_count"] or 0),
        high_value_event_count=int(row["high_value_event_count"] or 0),
    )


def _build_summary(versions: tuple[JourneyVersionAnalytics, ...]) -> dict[str, Any]:
    referral_count = sum(version.referral_count for version in versions)
    attributed_count = sum(version.attributed_referral_count for version in versions)
    completed_count = sum(version.completed_referral_count for version in versions)
    high_value_event_count = sum(version.high_value_event_count for version in versions)
    campaign_count = sum(version.campaign_count for version in versions)

    return {
        "journeyVersionsCompared": len(versions),
        "campaignCount": campaign_count,
        "referralCount": referral_count,
        "attributedReferralCount": attributed_count,
        "completedReferralCount": completed_count,
        "highValueEventCount": high_value_event_count,
        "attributionGapCount": max(0, referral_count - attributed_count),
        "completionGapCount": max(0, referral_count - completed_count),
        "attributionRate": _safe_rate(attributed_count, referral_count),
        "completionRate": _safe_rate(completed_count, referral_count),
        "analyticsSignal": _summary_signal(versions),
    }


def _summary_signal(versions: tuple[JourneyVersionAnalytics, ...]) -> str:
    if not versions:
        return "NO_PUBLISHED_VERSIONS"
    if all(version.referral_count <= 0 for version in versions):
        return "NO_TRAFFIC"
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
    return max(1, min(int(limit), MAX_JOURNEY_ANALYTICS_LIMIT))


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
