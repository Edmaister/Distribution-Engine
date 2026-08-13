from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.referral_saas_referral_registry_service import (
    REFERRAL_REGISTRY_REDACTIONS,
    ReferralSaasReferralSummary,
    list_referral_saas_account_referrals,
)
from services.referral_saas_referrer_identity_service import (
    REFERRER_IDENTITY_REDACTIONS,
    ReferralSaasSafeReferrerIdentity,
    list_referral_saas_safe_referrer_identities,
)


REFERRAL_ATTRIBUTION_GUARDRAILS = [
    "CUSTOMER_SCOPED_REFERRAL_ATTRIBUTION_ONLY",
    "ACCOUNT_SCOPE_RESOLVED_INTERNALLY",
    "SAFE_REFERRER_DIMENSIONS_ONLY",
    "NO_TENANT_CODE_EXPOSURE",
    "NO_RAW_UCN_EXPOSURE",
    "NO_RAW_CUSTOMER_IDENTIFIER_EXPOSURE",
    "NO_RAW_PROGRESS_PAYLOAD_EXPOSURE",
    "NO_EVENT_HASH_EXPOSURE",
    "NO_ATTRIBUTION_MUTATION",
    "NO_REPAIR_REPLAY_REASSIGNMENT",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_WEBHOOK_DELIVERY",
    "NO_BILLING_OR_MONEY_MOVEMENT",
]
REFERRAL_ATTRIBUTION_REDACTIONS = sorted(
    {
        *REFERRAL_REGISTRY_REDACTIONS,
        *REFERRER_IDENTITY_REDACTIONS,
        "raw_attribution_payload",
        "raw_identity_match_reason",
    }
)


@dataclass(frozen=True)
class ReferralSaasReferralCreditProjection:
    referral_track_id: str
    referral_code: str | None
    public_referrer_handle: str | None
    campaign_code: str | None
    credit_status: str
    confidence: str
    progress_event_count: int
    accepted_terms_confirmed: bool
    attribution_evidence_present: bool
    evidence: list[str]
    gaps: list[str]
    explanation: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "referralTrackId": self.referral_track_id,
            "referralCode": self.referral_code,
            "publicReferrerHandle": self.public_referrer_handle,
            "campaignCode": self.campaign_code,
            "creditStatus": self.credit_status,
            "confidence": self.confidence,
            "progressEventCount": self.progress_event_count,
            "acceptedTermsConfirmed": self.accepted_terms_confirmed,
            "attributionEvidencePresent": self.attribution_evidence_present,
            "evidence": self.evidence,
            "gaps": self.gaps,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class ReferralSaasReferrerCreditProjection:
    safe_referrer_key: str
    display_label: str
    masked_referrer_identifier: str
    credit_status: str
    confidence: str
    referral_count: int
    attributed_referral_count: int
    completed_referral_count: int
    campaign_count: int
    evidence: list[str]
    gaps: list[str]
    explanation: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "safeReferrerKey": self.safe_referrer_key,
            "displayLabel": self.display_label,
            "maskedReferrerIdentifier": self.masked_referrer_identifier,
            "creditStatus": self.credit_status,
            "confidence": self.confidence,
            "referralCount": self.referral_count,
            "attributedReferralCount": self.attributed_referral_count,
            "completedReferralCount": self.completed_referral_count,
            "campaignCount": self.campaign_count,
            "evidence": self.evidence,
            "gaps": self.gaps,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class ReferralSaasReferralAttributionSummary:
    status: str
    referral_count: int
    referrer_count: int
    credited_referral_count: int
    high_confidence_count: int
    missing_evidence_count: int
    plain_language: str
    referral_projections: list[ReferralSaasReferralCreditProjection]
    referrer_projections: list[ReferralSaasReferrerCreditProjection]
    guardrails: list[str]
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "referralCount": self.referral_count,
            "referrerCount": self.referrer_count,
            "creditedReferralCount": self.credited_referral_count,
            "highConfidenceCount": self.high_confidence_count,
            "missingEvidenceCount": self.missing_evidence_count,
            "plainLanguage": self.plain_language,
            "referralProjections": [
                projection.to_safe_dict() for projection in self.referral_projections
            ],
            "referrerProjections": [
                projection.to_safe_dict() for projection in self.referrer_projections
            ],
            "guardrails": self.guardrails,
            "redactions": self.redactions,
        }


async def build_referral_saas_account_referral_attribution_projection(
    *,
    tenant_code: str,
    limit: int = 50,
) -> ReferralSaasReferralAttributionSummary:
    safe_limit = max(1, min(int(limit or 50), 100))
    referrals = await list_referral_saas_account_referrals(
        tenant_code=tenant_code,
        limit=safe_limit,
    )
    referrers = await list_referral_saas_safe_referrer_identities(
        tenant_code=tenant_code,
        limit=safe_limit,
    )
    referral_projections = [_to_referral_credit(referral) for referral in referrals]
    referrer_projections = [_to_referrer_credit(referrer) for referrer in referrers]
    credited_referral_count = sum(
        1
        for projection in referral_projections
        if projection.credit_status in {"CREDITED", "CREDITABLE"}
    )
    high_confidence_count = sum(
        1 for projection in referral_projections if projection.confidence == "HIGH"
    )
    missing_evidence_count = sum(
        1
        for projection in referral_projections
        if projection.credit_status == "NEEDS_EVIDENCE"
    )
    status = _summary_status(
        referral_count=len(referral_projections),
        high_confidence_count=high_confidence_count,
        missing_evidence_count=missing_evidence_count,
    )
    return ReferralSaasReferralAttributionSummary(
        status=status,
        referral_count=len(referral_projections),
        referrer_count=len(referrer_projections),
        credited_referral_count=credited_referral_count,
        high_confidence_count=high_confidence_count,
        missing_evidence_count=missing_evidence_count,
        plain_language=_plain_language(
            referral_count=len(referral_projections),
            referrer_count=len(referrer_projections),
            credited_referral_count=credited_referral_count,
            missing_evidence_count=missing_evidence_count,
        ),
        referral_projections=referral_projections,
        referrer_projections=referrer_projections,
        guardrails=REFERRAL_ATTRIBUTION_GUARDRAILS,
        redactions=REFERRAL_ATTRIBUTION_REDACTIONS,
    )


def _to_referral_credit(
    referral: ReferralSaasReferralSummary,
) -> ReferralSaasReferralCreditProjection:
    evidence = _referral_evidence(referral)
    gaps = _referral_gaps(referral)
    credit_status = _referral_credit_status(referral, gaps)
    confidence = _confidence(credit_status, gaps)
    label = referral.public_referrer_handle or referral.referral_code or "a safe referrer"
    explanation = (
        f"{label} has {confidence.lower()} confidence credit evidence for "
        f"{referral.campaign_code or 'an unlinked campaign'}."
        if credit_status in {"CREDITED", "CREDITABLE"}
        else f"This referral needs more evidence before credit can be explained safely."
    )
    return ReferralSaasReferralCreditProjection(
        referral_track_id=referral.referral_track_id,
        referral_code=referral.referral_code,
        public_referrer_handle=referral.public_referrer_handle,
        campaign_code=referral.campaign_code,
        credit_status=credit_status,
        confidence=confidence,
        progress_event_count=referral.progress_event_count,
        accepted_terms_confirmed=referral.accepted_terms,
        attribution_evidence_present=referral.has_attribution_evidence,
        evidence=evidence,
        gaps=gaps,
        explanation=explanation,
    )


def _to_referrer_credit(
    referrer: ReferralSaasSafeReferrerIdentity,
) -> ReferralSaasReferrerCreditProjection:
    gaps = _referrer_gaps(referrer)
    credit_status = "CREDITED" if referrer.attributed_referral_count else "NEEDS_EVIDENCE"
    confidence = _confidence(credit_status, gaps)
    evidence = [
        f"{referrer.referral_count} referral record(s).",
        f"{referrer.attributed_referral_count} attributed referral record(s).",
        f"{referrer.campaign_count} campaign dimension(s).",
    ]
    explanation = (
        f"{referrer.display_label} can be explained as a credited referrer across "
        f"{referrer.attributed_referral_count} attributed referral record(s)."
        if referrer.attributed_referral_count
        else f"{referrer.display_label} is visible in safe referrer dimensions, but credit evidence is incomplete."
    )
    return ReferralSaasReferrerCreditProjection(
        safe_referrer_key=referrer.safe_referrer_key,
        display_label=referrer.display_label,
        masked_referrer_identifier=referrer.masked_referrer_identifier,
        credit_status=credit_status,
        confidence=confidence,
        referral_count=referrer.referral_count,
        attributed_referral_count=referrer.attributed_referral_count,
        completed_referral_count=referrer.completed_referral_count,
        campaign_count=referrer.campaign_count,
        evidence=evidence,
        gaps=gaps,
        explanation=explanation,
    )


def _referral_evidence(referral: ReferralSaasReferralSummary) -> list[str]:
    evidence: list[str] = []
    if referral.referral_code:
        evidence.append("Referral code is present.")
    if referral.public_referrer_handle:
        evidence.append("Safe referrer handle is present.")
    if referral.campaign_code:
        evidence.append("Campaign link is present.")
    if referral.accepted_terms:
        evidence.append("Accepted terms are confirmed.")
    if referral.progress_event_count:
        evidence.append(f"{referral.progress_event_count} progress event(s) are present.")
    if referral.has_attribution_evidence:
        evidence.append("Campaign attribution evidence is present.")
    return evidence


def _referral_gaps(referral: ReferralSaasReferralSummary) -> list[str]:
    return list(referral.to_safe_dict().get("missingEvidence", []))


def _referrer_gaps(referrer: ReferralSaasSafeReferrerIdentity) -> list[str]:
    gaps = list(referrer.missing_evidence)
    if referrer.attributed_referral_count == 0:
        gaps.append("ATTRIBUTED_REFERRAL_EVIDENCE_MISSING")
    return sorted(set(gaps))


def _referral_credit_status(
    referral: ReferralSaasReferralSummary,
    gaps: list[str],
) -> str:
    if referral.has_attribution_evidence and not gaps:
        return "CREDITED"
    if referral.has_attribution_evidence:
        return "CREDITABLE"
    return "NEEDS_EVIDENCE"


def _confidence(status: str, gaps: list[str]) -> str:
    if status == "CREDITED" and not gaps:
        return "HIGH"
    if status in {"CREDITED", "CREDITABLE"} and len(gaps) <= 2:
        return "MEDIUM"
    return "LOW"


def _summary_status(
    *,
    referral_count: int,
    high_confidence_count: int,
    missing_evidence_count: int,
) -> str:
    if referral_count == 0:
        return "NO_REFERRALS"
    if missing_evidence_count:
        return "NEEDS_EVIDENCE"
    if high_confidence_count:
        return "READY"
    return "REVIEW"


def _plain_language(
    *,
    referral_count: int,
    referrer_count: int,
    credited_referral_count: int,
    missing_evidence_count: int,
) -> str:
    if referral_count == 0:
        return "No referral credit evidence is available yet for this customer."
    return (
        f"{credited_referral_count} of {referral_count} referral record(s) can be "
        f"explained across {referrer_count} safe referrer dimension(s). "
        f"{missing_evidence_count} referral record(s) still need evidence before credit can be explained safely."
    )
