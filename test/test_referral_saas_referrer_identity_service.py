from __future__ import annotations

import pytest

from services.referral_saas_referral_registry_service import ReferralSaasReferralSummary
from services import referral_saas_referrer_identity_service as svc

pytestmark = pytest.mark.asyncio


def _summary(**overrides) -> ReferralSaasReferralSummary:
    base = {
        "referral_track_id": "track-1",
        "referral_code": "REF-001",
        "public_referrer_handle": "safe-handle",
        "campaign_code": "SUMMER-2026",
        "status": "VALIDATED",
        "display_status": "Validated",
        "progress_percent": 50,
        "progress_band": "MID",
        "next_milestone": "FIRST_PURCHASE",
        "journey_code": "BANKING_REFERRAL",
        "journey_version": 1,
        "product": "Referral",
        "sub_product": "Retail",
        "referee_alias": "Customer A",
        "accepted_terms": True,
        "is_complete": False,
        "validated_at": "2026-08-01T00:00:00+00:00",
        "completed_at": None,
        "created_at": "2026-07-31T00:00:00+00:00",
        "updated_at": "2026-08-02T00:00:00+00:00",
        "last_progress_at": "2026-08-02T00:00:00+00:00",
        "progress_event_count": 2,
        "has_attribution_evidence": True,
    }
    base.update(overrides)
    return ReferralSaasReferralSummary(**base)


async def test_referrer_identity_directory_groups_referrals_without_raw_identity(monkeypatch):
    async def fake_referrals(*, tenant_code: str, limit: int):
        assert tenant_code == "FNB"
        assert limit == 100
        return [
            _summary(referral_track_id="track-1", public_referrer_handle="safe-handle"),
            _summary(
                referral_track_id="track-2",
                referral_code="REF-002",
                public_referrer_handle="safe-handle",
                campaign_code="WINTER-2026",
                is_complete=True,
                completed_at="2026-08-03T00:00:00+00:00",
            ),
        ]

    monkeypatch.setattr(svc, "list_referral_saas_account_referrals", fake_referrals)

    referrers = await svc.list_referral_saas_safe_referrer_identities(
        tenant_code="FNB",
        limit=500,
    )

    assert len(referrers) == 1
    payload = referrers[0].to_safe_dict()
    assert payload["displayLabel"] == "safe-handle"
    assert payload["referralCount"] == 2
    assert payload["campaigns"] == ["SUMMER-2026", "WINTER-2026"]
    assert payload["safeReferrerKey"].startswith("REFERRER_")
    assert payload["maskedReferrerIdentifier"].startswith("referrer-...")
    assert "tenantCode" not in payload
    assert "referrerUcn" not in payload
    assert "rawReferrerUcn" not in payload
    assert "secret" in payload["redactions"]


async def test_referrer_identity_marks_missing_evidence_and_uses_safe_label(monkeypatch):
    async def fake_referrals(*, tenant_code: str, limit: int):
        return [
            _summary(
                referral_track_id="track-missing",
                referral_code=None,
                public_referrer_handle=None,
                campaign_code=None,
                accepted_terms=False,
                progress_event_count=0,
                has_attribution_evidence=False,
            )
        ]

    monkeypatch.setattr(svc, "list_referral_saas_account_referrals", fake_referrals)

    payload = (
        await svc.list_referral_saas_safe_referrer_identities(
            tenant_code="FNB",
            limit=50,
        )
    )[0].to_safe_dict()

    assert payload["displayLabel"] == "Unidentified referrer"
    assert payload["missingEvidence"] == [
        "ACCEPTED_TERMS_NOT_CONFIRMED",
        "ATTRIBUTION_EVIDENCE_MISSING",
        "CAMPAIGN_LINK_MISSING",
        "PROGRESS_TIMELINE_MISSING",
        "REFERRAL_CODE_MISSING",
        "SAFE_REFERRER_HANDLE_MISSING",
    ]
    assert payload["campaignCount"] == 0


async def test_referrer_identity_detail_returns_safe_referrals(monkeypatch):
    referral = _summary(referral_track_id="track-1", public_referrer_handle="safe-handle")

    async def fake_referrals(*, tenant_code: str, limit: int):
        return [referral]

    monkeypatch.setattr(svc, "list_referral_saas_account_referrals", fake_referrals)
    safe_key = (
        await svc.list_referral_saas_safe_referrer_identities(
            tenant_code="FNB",
            limit=50,
        )
    )[0].safe_referrer_key

    detail = await svc.get_referral_saas_safe_referrer_identity(
        tenant_code="FNB",
        safe_referrer_key=safe_key,
    )

    assert detail is not None
    payload = detail.to_safe_dict()
    assert payload["safeReferrerKey"] == safe_key
    assert payload["referrals"][0]["referralTrackId"] == "track-1"
    assert "tenantCode" not in payload["referrals"][0]
