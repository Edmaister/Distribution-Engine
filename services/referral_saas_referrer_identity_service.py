from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from services.referral_saas_referral_registry_service import (
    MAX_REFERRAL_REGISTRY_LIMIT,
    ReferralSaasReferralSummary,
    list_referral_saas_account_referrals,
)


MAX_REFERRER_DIRECTORY_LIMIT = 100
REFERRER_IDENTITY_GUARDRAILS = [
    "CUSTOMER_SCOPED_REFERRER_DIRECTORY",
    "ACCOUNT_SCOPE_RESOLVED_INTERNALLY",
    "SAFE_REFERRER_KEY_ONLY",
    "NO_TENANT_CODE_EXPOSURE",
    "NO_RAW_UCN_EXPOSURE",
    "NO_RAW_CUSTOMER_IDENTIFIER_EXPOSURE",
    "NO_SECRET_OR_TOKEN_EXPOSURE",
    "NO_REFERRAL_MUTATION",
    "NO_REPAIR_REPLAY_REASSIGNMENT",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_WEBHOOK_DELIVERY",
    "NO_BILLING_OR_MONEY_MOVEMENT",
]
REFERRER_IDENTITY_REDACTIONS = [
    "internal_tenant_identifier",
    "raw_referrer_ucn",
    "raw_referee_ucn",
    "raw_customer_identifier",
    "raw_progress_payload",
    "event_payload_hash",
    "dedupe_key",
    "secret",
    "token",
]


@dataclass(frozen=True)
class ReferralSaasReferrerDimension:
    name: str
    values: list[dict[str, Any]]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "values": self.values,
        }


@dataclass(frozen=True)
class ReferralSaasSafeReferrerIdentity:
    safe_referrer_key: str
    display_label: str
    public_referrer_handle: str | None
    masked_referrer_identifier: str
    referral_count: int
    open_referral_count: int
    completed_referral_count: int
    attributed_referral_count: int
    missing_evidence_count: int
    campaign_count: int
    campaigns: list[str]
    first_seen_at: str | None
    last_seen_at: str | None
    status_breakdown: list[dict[str, Any]]
    progress_breakdown: list[dict[str, Any]]
    dimensions: list[ReferralSaasReferrerDimension]
    missing_evidence: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "safeReferrerKey": self.safe_referrer_key,
            "displayLabel": self.display_label,
            "publicReferrerHandle": self.public_referrer_handle,
            "maskedReferrerIdentifier": self.masked_referrer_identifier,
            "referralCount": self.referral_count,
            "openReferralCount": self.open_referral_count,
            "completedReferralCount": self.completed_referral_count,
            "attributedReferralCount": self.attributed_referral_count,
            "missingEvidenceCount": self.missing_evidence_count,
            "campaignCount": self.campaign_count,
            "campaigns": self.campaigns,
            "firstSeenAt": self.first_seen_at,
            "lastSeenAt": self.last_seen_at,
            "statusBreakdown": self.status_breakdown,
            "progressBreakdown": self.progress_breakdown,
            "dimensions": [dimension.to_safe_dict() for dimension in self.dimensions],
            "missingEvidence": self.missing_evidence,
            "redactions": REFERRER_IDENTITY_REDACTIONS,
        }


@dataclass(frozen=True)
class ReferralSaasSafeReferrerDetail:
    identity: ReferralSaasSafeReferrerIdentity
    referrals: list[ReferralSaasReferralSummary]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            **self.identity.to_safe_dict(),
            "referrals": [referral.to_safe_dict() for referral in self.referrals],
        }


async def list_referral_saas_safe_referrer_identities(
    *,
    tenant_code: str,
    limit: int = 50,
) -> list[ReferralSaasSafeReferrerIdentity]:
    referrals = await list_referral_saas_account_referrals(
        tenant_code=tenant_code,
        limit=min(max(1, int(limit or 50)), MAX_REFERRAL_REGISTRY_LIMIT),
    )
    return _build_referrer_identities(referrals)[:MAX_REFERRER_DIRECTORY_LIMIT]


async def get_referral_saas_safe_referrer_identity(
    *,
    tenant_code: str,
    safe_referrer_key: str,
    limit: int = 100,
) -> ReferralSaasSafeReferrerDetail | None:
    identities = await list_referral_saas_safe_referrer_identities(
        tenant_code=tenant_code,
        limit=limit,
    )
    target_key = str(safe_referrer_key or "").strip().upper()
    identity = next(
        (
            candidate
            for candidate in identities
            if candidate.safe_referrer_key.upper() == target_key
        ),
        None,
    )
    if identity is None:
        return None
    referrals = await list_referral_saas_account_referrals(
        tenant_code=tenant_code,
        limit=min(max(1, int(limit or 100)), MAX_REFERRAL_REGISTRY_LIMIT),
    )
    grouped = _group_referrals(referrals)
    return ReferralSaasSafeReferrerDetail(
        identity=identity,
        referrals=grouped.get(identity.safe_referrer_key, []),
    )


def _build_referrer_identities(
    referrals: list[ReferralSaasReferralSummary],
) -> list[ReferralSaasSafeReferrerIdentity]:
    grouped = _group_referrals(referrals)
    identities = [
        _to_referrer_identity(safe_referrer_key, grouped_referrals)
        for safe_referrer_key, grouped_referrals in grouped.items()
    ]
    return sorted(
        identities,
        key=lambda identity: (
            identity.last_seen_at or "",
            identity.referral_count,
            identity.display_label,
        ),
        reverse=True,
    )


def _group_referrals(
    referrals: list[ReferralSaasReferralSummary],
) -> dict[str, list[ReferralSaasReferralSummary]]:
    grouped: dict[str, list[ReferralSaasReferralSummary]] = defaultdict(list)
    for referral in referrals:
        grouped[_safe_referrer_key(referral)].append(referral)
    return dict(grouped)


def _to_referrer_identity(
    safe_referrer_key: str,
    referrals: list[ReferralSaasReferralSummary],
) -> ReferralSaasSafeReferrerIdentity:
    sorted_referrals = sorted(
        referrals,
        key=lambda referral: _last_seen(referral) or "",
        reverse=True,
    )
    representative = sorted_referrals[0]
    campaigns = sorted(
        {
            str(referral.campaign_code)
            for referral in referrals
            if referral.campaign_code
        }
    )
    missing_evidence = sorted(
        {
            missing
            for referral in referrals
            for missing in referral.to_safe_dict().get("missingEvidence", [])
        }
    )
    status_counter = Counter(
        referral.display_status or referral.status or "UNKNOWN"
        for referral in referrals
    )
    progress_counter = Counter(
        referral.progress_band or "NO_PROGRESS_BAND"
        for referral in referrals
    )
    return ReferralSaasSafeReferrerIdentity(
        safe_referrer_key=safe_referrer_key,
        display_label=_display_label(representative),
        public_referrer_handle=representative.public_referrer_handle,
        masked_referrer_identifier=_masked_identifier(safe_referrer_key),
        referral_count=len(referrals),
        open_referral_count=sum(1 for referral in referrals if not referral.is_complete),
        completed_referral_count=sum(1 for referral in referrals if referral.is_complete),
        attributed_referral_count=sum(
            1 for referral in referrals if referral.has_attribution_evidence
        ),
        missing_evidence_count=len(missing_evidence),
        campaign_count=len(campaigns),
        campaigns=campaigns,
        first_seen_at=min(
            (seen for seen in (_first_seen(referral) for referral in referrals) if seen),
            default=None,
        ),
        last_seen_at=max(
            (seen for seen in (_last_seen(referral) for referral in referrals) if seen),
            default=None,
        ),
        status_breakdown=_counter_breakdown(status_counter),
        progress_breakdown=_counter_breakdown(progress_counter),
        dimensions=[
            ReferralSaasReferrerDimension("campaign", _value_counts(campaigns)),
            ReferralSaasReferrerDimension(
                "journey", _dimension_counts(referrals, "journey_code")
            ),
            ReferralSaasReferrerDimension(
                "product", _dimension_counts(referrals, "product")
            ),
            ReferralSaasReferrerDimension(
                "sub_product", _dimension_counts(referrals, "sub_product")
            ),
        ],
        missing_evidence=missing_evidence,
    )


def _safe_referrer_key(referral: ReferralSaasReferralSummary) -> str:
    seed = (
        referral.public_referrer_handle
        or referral.referral_code
        or referral.referral_track_id
        or "UNKNOWN_REFERRER"
    )
    digest = hashlib.sha256(str(seed).strip().lower().encode("utf-8")).hexdigest()
    return f"REFERRER_{digest[:16].upper()}"


def _display_label(referral: ReferralSaasReferralSummary) -> str:
    if referral.public_referrer_handle:
        return referral.public_referrer_handle
    if referral.referral_code:
        return f"Referral code {referral.referral_code}"
    return "Unidentified referrer"


def _masked_identifier(safe_referrer_key: str) -> str:
    suffix = str(safe_referrer_key or "")[-6:]
    return f"referrer-...{suffix}" if suffix else "referrer-hidden"


def _first_seen(referral: ReferralSaasReferralSummary) -> str | None:
    return referral.created_at or referral.validated_at or referral.updated_at


def _last_seen(referral: ReferralSaasReferralSummary) -> str | None:
    return (
        referral.last_progress_at
        or referral.completed_at
        or referral.updated_at
        or referral.validated_at
        or referral.created_at
    )


def _counter_breakdown(counter: Counter[str]) -> list[dict[str, Any]]:
    return [
        {"label": label, "count": count}
        for label, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]


def _value_counts(values: list[str]) -> list[dict[str, Any]]:
    return [{"label": value, "count": 1} for value in values]


def _dimension_counts(
    referrals: list[ReferralSaasReferralSummary],
    attribute_name: str,
) -> list[dict[str, Any]]:
    counter = Counter(
        str(value)
        for referral in referrals
        if (value := getattr(referral, attribute_name, None))
    )
    return _counter_breakdown(counter)
