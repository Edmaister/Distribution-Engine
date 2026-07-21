from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from utils.db import db_connection


MAX_CAMPAIGN_LIST_LIMIT = 100


@dataclass(frozen=True)
class ReferralSaasCampaignSummary:
    campaign_code: str
    name: str
    segment: str
    status: str
    lifecycle: str
    starts_at: str | None
    ends_at: str | None
    max_uses: int | None
    uses_count: int
    policy_status: str
    created_at: str | None
    updated_at: str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "campaignCode": self.campaign_code,
            "name": self.name,
            "segment": self.segment,
            "status": self.status,
            "lifecycle": self.lifecycle,
            "startsAt": self.starts_at,
            "endsAt": self.ends_at,
            "maxUses": self.max_uses,
            "usesCount": self.uses_count,
            "policyStatus": self.policy_status,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }


def _as_iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    return None


def _as_aware_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    return None


def _campaign_lifecycle(*, is_active: bool, starts_at: Any, ends_at: Any) -> str:
    now = datetime.now(timezone.utc)
    safe_starts_at = _as_aware_utc(starts_at)
    safe_ends_at = _as_aware_utc(ends_at)
    if not is_active:
        return "PAUSED"
    if safe_starts_at and safe_starts_at > now:
        return "SCHEDULED"
    if safe_ends_at and safe_ends_at < now:
        return "EXPIRED"
    return "ACTIVE"


def _campaign_status(*, lifecycle: str, policy_status: str) -> str:
    if lifecycle in {"PAUSED", "EXPIRED"}:
        return lifecycle
    if policy_status != "ACTIVE_POLICY":
        return "NEEDS_POLICY"
    return lifecycle


def _to_campaign_summary(row: dict[str, Any]) -> ReferralSaasCampaignSummary:
    is_active = bool(row.get("is_active"))
    lifecycle = _campaign_lifecycle(
        is_active=is_active,
        starts_at=row.get("starts_at"),
        ends_at=row.get("ends_at"),
    )
    active_policy_count = int(row.get("active_policy_count") or 0)
    policy_status = "ACTIVE_POLICY" if active_policy_count > 0 else "NO_ACTIVE_POLICY"
    return ReferralSaasCampaignSummary(
        campaign_code=str(row["campaign_code"]),
        name=str(row["name"]),
        segment=str(row["segment"]),
        status=_campaign_status(lifecycle=lifecycle, policy_status=policy_status),
        lifecycle=lifecycle,
        starts_at=_as_iso(row.get("starts_at")),
        ends_at=_as_iso(row.get("ends_at")),
        max_uses=int(row["max_uses"]) if row.get("max_uses") is not None else None,
        uses_count=int(row.get("uses_count") or 0),
        policy_status=policy_status,
        created_at=_as_iso(row.get("created_at")),
        updated_at=_as_iso(row.get("updated_at")),
    )


async def list_referral_saas_account_campaigns(
    *,
    tenant_code: str,
    limit: int = 50,
) -> list[ReferralSaasCampaignSummary]:
    safe_tenant_code = str(tenant_code or "").strip()
    if not safe_tenant_code:
        return []
    safe_limit = max(1, min(int(limit or 50), MAX_CAMPAIGN_LIST_LIMIT))
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                campaign.campaign_code,
                campaign.name,
                campaign.segment,
                campaign.is_active,
                campaign.starts_at,
                campaign.ends_at,
                campaign.max_uses,
                campaign.uses_count,
                campaign.created_at,
                campaign.updated_at,
                COUNT(policy.campaign_code) FILTER (WHERE policy.is_active = TRUE)
                    AS active_policy_count
            FROM marketing_campaigns campaign
            LEFT JOIN marketing_campaign_policies policy
                ON UPPER(policy.campaign_code) = UPPER(campaign.campaign_code)
               AND (
                    policy.tenant_code IS NULL
                    OR UPPER(policy.tenant_code) = UPPER($1)
               )
            WHERE UPPER(campaign.tenant_code) = UPPER($1)
            GROUP BY
                campaign.campaign_code,
                campaign.name,
                campaign.segment,
                campaign.is_active,
                campaign.starts_at,
                campaign.ends_at,
                campaign.max_uses,
                campaign.uses_count,
                campaign.created_at,
                campaign.updated_at
            ORDER BY campaign.updated_at DESC, campaign.created_at DESC, campaign.campaign_code ASC
            LIMIT $2
            """,
            safe_tenant_code,
            safe_limit,
        )
    return [_to_campaign_summary(dict(row)) for row in rows]


async def get_referral_saas_account_campaign(
    *,
    tenant_code: str,
    campaign_code: str,
) -> ReferralSaasCampaignSummary | None:
    safe_tenant_code = str(tenant_code or "").strip()
    safe_campaign_code = str(campaign_code or "").strip()
    if not safe_tenant_code or not safe_campaign_code:
        return None
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                campaign.campaign_code,
                campaign.name,
                campaign.segment,
                campaign.is_active,
                campaign.starts_at,
                campaign.ends_at,
                campaign.max_uses,
                campaign.uses_count,
                campaign.created_at,
                campaign.updated_at,
                COUNT(policy.campaign_code) FILTER (WHERE policy.is_active = TRUE)
                    AS active_policy_count
            FROM marketing_campaigns campaign
            LEFT JOIN marketing_campaign_policies policy
                ON UPPER(policy.campaign_code) = UPPER(campaign.campaign_code)
               AND (
                    policy.tenant_code IS NULL
                    OR UPPER(policy.tenant_code) = UPPER($1)
               )
            WHERE UPPER(campaign.tenant_code) = UPPER($1)
              AND UPPER(campaign.campaign_code) = UPPER($2)
            GROUP BY
                campaign.campaign_code,
                campaign.name,
                campaign.segment,
                campaign.is_active,
                campaign.starts_at,
                campaign.ends_at,
                campaign.max_uses,
                campaign.uses_count,
                campaign.created_at,
                campaign.updated_at
            LIMIT 1
            """,
            safe_tenant_code,
            safe_campaign_code,
        )
    return _to_campaign_summary(dict(row)) if row else None
