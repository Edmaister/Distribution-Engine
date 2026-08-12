from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from services import referral_saas_referral_registry_service as svc

pytestmark = pytest.mark.asyncio


class FakeConnection:
    def __init__(self, *, fetch_results=None, fetchrow_results=None):
        self.fetch_results = list(fetch_results or [])
        self.fetchrow_results = list(fetchrow_results or [])
        self.fetch_calls = []
        self.fetchrow_calls = []

    async def fetch(self, query, *args):
        self.fetch_calls.append((query, args))
        if not self.fetch_results:
            raise AssertionError(f"Unexpected fetch call: {query}")
        return self.fetch_results.pop(0)

    async def fetchrow(self, query, *args):
        self.fetchrow_calls.append((query, args))
        if not self.fetchrow_results:
            raise AssertionError(f"Unexpected fetchrow call: {query}")
        return self.fetchrow_results.pop(0)


def patch_db(monkeypatch, connection):
    @asynccontextmanager
    async def fake_db_connection():
        yield connection

    monkeypatch.setattr(svc, "db_connection", fake_db_connection)


def _referral_row(**overrides):
    row = {
        "referral_track_id": uuid4(),
        "referral_code": "REF-123",
        "public_referrer_handle": "edwin",
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
        "validated_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
        "completed_at": None,
        "created_at": datetime(2026, 7, 31, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 8, 2, tzinfo=timezone.utc),
        "last_progress_at": datetime(2026, 8, 2, tzinfo=timezone.utc),
        "progress_event_count": 2,
        "has_attribution_evidence": True,
    }
    row.update(overrides)
    return row


async def test_referral_registry_lists_safe_customer_scoped_projection(monkeypatch):
    conn = FakeConnection(fetch_results=[[_referral_row()]])
    patch_db(monkeypatch, conn)

    referrals = await svc.list_referral_saas_account_referrals(
        tenant_code="FNB",
        limit=200,
    )

    assert len(referrals) == 1
    safe_payload = referrals[0].to_safe_dict()
    assert safe_payload["referralCode"] == "REF-123"
    assert safe_payload["publicReferrerHandle"] == "edwin"
    assert safe_payload["missingEvidence"] == []
    assert "tenantCode" not in safe_payload
    assert "referrerUcn" not in safe_payload
    assert "refereeUcn" not in safe_payload
    query, args = conn.fetch_calls[0]
    assert "WHERE UPPER(ri.tenant_code) = UPPER($1)" in query
    assert args == ("FNB", svc.MAX_REFERRAL_REGISTRY_LIMIT)


async def test_referral_registry_marks_missing_evidence_without_raw_payloads(monkeypatch):
    conn = FakeConnection(
        fetch_results=[
            [
                _referral_row(
                    referral_code=None,
                    public_referrer_handle=None,
                    campaign_code=None,
                    accepted_terms=False,
                    progress_event_count=0,
                    has_attribution_evidence=False,
                )
            ]
        ]
    )
    patch_db(monkeypatch, conn)

    referral = (
        await svc.list_referral_saas_account_referrals(
            tenant_code="FNB",
            limit=50,
        )
    )[0]

    safe_payload = referral.to_safe_dict()
    assert safe_payload["missingEvidence"] == [
        "REFERRAL_CODE_MISSING",
        "SAFE_REFERRER_HANDLE_MISSING",
        "CAMPAIGN_LINK_MISSING",
        "ACCEPTED_TERMS_NOT_CONFIRMED",
        "PROGRESS_TIMELINE_MISSING",
        "ATTRIBUTION_EVIDENCE_MISSING",
    ]
    assert "raw_progress_payload" in safe_payload["redactions"]


async def test_referral_detail_returns_safe_timeline(monkeypatch):
    referral_track_id = uuid4()
    conn = FakeConnection(
        fetchrow_results=[_referral_row(referral_track_id=referral_track_id)],
        fetch_results=[
            [
                {
                    "event_type": "APPLICATION_STARTED",
                    "occurred_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
                    "source_system": "progress-api",
                    "meta": {"raw": "not returned"},
                    "event_payload_hash": "not-returned",
                }
            ]
        ],
    )
    patch_db(monkeypatch, conn)

    detail = await svc.get_referral_saas_account_referral(
        tenant_code="FNB",
        referral_track_id=str(referral_track_id),
    )

    assert detail is not None
    safe_payload = detail.to_safe_dict()
    assert safe_payload["referralTrackId"] == str(referral_track_id)
    assert safe_payload["timeline"] == [
        {
            "eventType": "APPLICATION_STARTED",
            "occurredAt": "2026-08-01T00:00:00+00:00",
            "sourceSystem": "progress-api",
        }
    ]
    assert "meta" not in safe_payload["timeline"][0]
    assert "eventPayloadHash" not in safe_payload["timeline"][0]
