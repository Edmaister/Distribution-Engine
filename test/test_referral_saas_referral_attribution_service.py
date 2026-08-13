from __future__ import annotations

import pytest

from services.referral_saas_referral_registry_service import ReferralSaasReferralSummary
from services.referral_saas_referrer_identity_service import ReferralSaasSafeReferrerIdentity
from services import referral_saas_referral_attribution_service as svc

pytestmark = pytest.mark.asyncio


def _summary(**overrides) -> ReferralSaasReferralSummary:
    values = {
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
    values.update(overrides)
    return ReferralSaasReferralSummary(**values)


def _referrer(**overrides) -> ReferralSaasSafeReferrerIdentity:
    values = {
        "safe_referrer_key": "REFERRER_SAFE",
        "display_label": "safe-handle",
        "public_referrer_handle": "safe-handle",
        "masked_referrer_identifier": "referrer-...SAFE",
        "referral_count": 2,
        "open_referral_count": 1,
        "completed_referral_count": 1,
        "attributed_referral_count": 2,
        "missing_evidence_count": 0,
        "campaign_count": 1,
        "campaigns": ["SUMMER-2026"],
        "first_seen_at": "2026-07-31T00:00:00+00:00",
        "last_seen_at": "2026-08-02T00:00:00+00:00",
        "status_breakdown": [{"value": "Validated", "count": 2}],
        "progress_breakdown": [{"value": "MID", "count": 2}],
        "dimensions": [],
        "missing_evidence": [],
    }
    values.update(overrides)
    return ReferralSaasSafeReferrerIdentity(**values)


async def test_referral_attribution_projects_who_got_credit_without_raw_identity(monkeypatch):
    async def fake_referrals(*, tenant_code: str, limit: int):
        assert tenant_code == "FNB"
        assert limit == 50
        return [_summary()]

    async def fake_referrers(*, tenant_code: str, limit: int):
        assert tenant_code == "FNB"
        assert limit == 50
        return [_referrer()]

    monkeypatch.setattr(svc, "list_referral_saas_account_referrals", fake_referrals)
    monkeypatch.setattr(svc, "list_referral_saas_safe_referrer_identities", fake_referrers)

    projection = await svc.build_referral_saas_account_referral_attribution_projection(
        tenant_code="FNB",
        limit=50,
    )

    payload = projection.to_safe_dict()
    assert payload["status"] == "READY"
    assert payload["creditedReferralCount"] == 1
    assert payload["referralProjections"][0]["creditStatus"] == "CREDITED"
    assert payload["referralProjections"][0]["confidence"] == "HIGH"
    assert payload["referrerProjections"][0]["safeReferrerKey"] == "REFERRER_SAFE"
    assert "tenantCode" not in str(payload)
    assert "rawReferrerUcn" not in str(payload)
    assert "raw_progress_payload" in payload["redactions"]


async def test_referral_attribution_marks_missing_credit_evidence(monkeypatch):
    async def fake_referrals(*, tenant_code: str, limit: int):
        return [
            _summary(
                referral_code=None,
                public_referrer_handle=None,
                campaign_code=None,
                accepted_terms=False,
                progress_event_count=0,
                has_attribution_evidence=False,
            )
        ]

    async def fake_referrers(*, tenant_code: str, limit: int):
        return [_referrer(attributed_referral_count=0, missing_evidence=["ATTRIBUTION_EVIDENCE_MISSING"])]

    monkeypatch.setattr(svc, "list_referral_saas_account_referrals", fake_referrals)
    monkeypatch.setattr(svc, "list_referral_saas_safe_referrer_identities", fake_referrers)

    projection = await svc.build_referral_saas_account_referral_attribution_projection(
        tenant_code="FNB",
        limit=200,
    )

    payload = projection.to_safe_dict()
    assert payload["status"] == "NEEDS_EVIDENCE"
    assert payload["missingEvidenceCount"] == 1
    assert payload["referralProjections"][0]["creditStatus"] == "NEEDS_EVIDENCE"
    assert payload["referralProjections"][0]["confidence"] == "LOW"
    assert "ATTRIBUTION_EVIDENCE_MISSING" in payload["referralProjections"][0]["gaps"]
    assert payload["referrerProjections"][0]["creditStatus"] == "NEEDS_EVIDENCE"
