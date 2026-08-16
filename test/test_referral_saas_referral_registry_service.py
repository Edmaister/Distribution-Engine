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
        "programme_version_id": None,
        "programme_code": None,
        "programme_name": None,
        "programme_version_number": None,
        "customer_journey_version_id": None,
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
    assert safe_payload["programmeVersion"] == {"bindingStatus": "LEGACY_OR_UNBOUND"}
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


async def test_referral_registry_returns_safe_programme_runtime_metadata(monkeypatch):
    programme_version_id = uuid4()
    customer_journey_version_id = uuid4()
    conn = FakeConnection(
        fetch_results=[
            [
                _referral_row(
                    programme_version_id=programme_version_id,
                    programme_code="HOME_LOAN",
                    programme_name="Home Loan Referral",
                    programme_version_number=3,
                    customer_journey_version_id=customer_journey_version_id,
                    raw_programme_config={"must": "not leak"},
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
    assert safe_payload["programmeVersion"] == {
        "bindingStatus": "BOUND_AT_REFERRAL_CREATION",
        "programmeVersionId": str(programme_version_id),
        "programmeCode": "HOME_LOAN",
        "programmeName": "Home Loan Referral",
        "versionNumber": 3,
        "customerJourneyVersionId": str(customer_journey_version_id),
    }
    assert "raw_programme_config" not in safe_payload


async def test_referral_detail_returns_safe_timeline(monkeypatch):
    referral_track_id = uuid4()
    conn = FakeConnection(
        fetchrow_results=[_referral_row(referral_track_id=referral_track_id)],
        fetch_results=[
            [
                {
                    "sequence": 1,
                    "event_type": "APPLICATION_STARTED",
                    "occurred_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
                    "received_at": datetime(2026, 8, 1, 0, 1, tzinfo=timezone.utc),
                    "source_system": "progress-api",
                    "source_event_id": "source-event-1",
                    "meta": {"raw": "not returned"},
                    "event_payload_hash": "not-returned",
                    "dedupe_key": "not-returned",
                    "idempotency_version": 1,
                    "source_inbox_status": "QUEUED",
                    "source_inbox_event_present": True,
                    "source_inbox_dedupe_present": True,
                    "source_inbox_payload_hash_present": True,
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
            "sequence": 1,
            "eventType": "APPLICATION_STARTED",
            "occurredAt": "2026-08-01T00:00:00+00:00",
            "receivedAt": "2026-08-01T00:01:00+00:00",
            "sourceSystem": "progress-api",
            "sourceEventPresent": True,
            "dedupeEvidence": "SOURCE_EVENT_AND_DEDUPE_KEY_PRESENT",
            "payloadHashPresent": True,
            "sourceInboxStatus": "QUEUED",
            "sourceEvidence": [
                "SOURCE_SYSTEM_PRESENT",
                "SOURCE_EVENT_PRESENT",
                "DEDUPE_KEY_PRESENT",
                "PAYLOAD_HASH_PRESENT",
                "SOURCE_INBOX_QUEUED",
            ],
            "missingEvidence": [],
            "recoveryPosture": "READY_FOR_SUPPORT_AND_ATTRIBUTION",
        }
    ]
    assert safe_payload["timelineEvidenceSummary"] == {
        "eventCount": 1,
        "sourceMatchedCount": 1,
        "missingSourceEvidenceCount": 0,
        "missingIdempotencyEvidenceCount": 0,
        "duplicateReplayCount": 0,
        "failedOrDelayedCount": 0,
        "missingEvidence": [],
        "recoveryPosture": "READY_FOR_SUPPORT_AND_ATTRIBUTION",
    }
    assert "meta" not in safe_payload["timeline"][0]
    assert "eventPayloadHash" not in safe_payload["timeline"][0]
    assert "sourceEventId" not in safe_payload["timeline"][0]
    assert "dedupeKey" not in safe_payload["timeline"][0]


async def test_referral_detail_marks_missing_source_and_idempotency_evidence(monkeypatch):
    referral_track_id = uuid4()
    conn = FakeConnection(
        fetchrow_results=[_referral_row(referral_track_id=referral_track_id)],
        fetch_results=[
            [
                {
                    "sequence": 1,
                    "event_type": "APPLICATION_STARTED",
                    "occurred_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
                    "received_at": None,
                    "source_system": None,
                    "source_event_id": None,
                    "event_payload_hash": None,
                    "dedupe_key": None,
                    "idempotency_version": None,
                    "source_inbox_status": None,
                    "source_inbox_event_present": False,
                    "source_inbox_dedupe_present": False,
                    "source_inbox_payload_hash_present": False,
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
    assert safe_payload["timeline"][0]["missingEvidence"] == [
        "SOURCE_SYSTEM_MISSING",
        "SOURCE_EVENT_ID_MISSING",
        "DEDUPE_KEY_MISSING",
        "PAYLOAD_HASH_MISSING",
        "SOURCE_INBOX_EVIDENCE_MISSING",
    ]
    assert safe_payload["timeline"][0]["recoveryPosture"] == "CHECK_SOURCE_PROVENANCE"
    assert safe_payload["timelineEvidenceSummary"]["missingSourceEvidenceCount"] == 1
    assert safe_payload["timelineEvidenceSummary"]["missingIdempotencyEvidenceCount"] == 1
    assert safe_payload["timelineEvidenceSummary"]["recoveryPosture"] == "CHECK_SOURCE_PROVENANCE"


async def test_referral_detail_surfaces_dedupe_replay_without_raw_keys(monkeypatch):
    referral_track_id = uuid4()
    conn = FakeConnection(
        fetchrow_results=[_referral_row(referral_track_id=referral_track_id)],
        fetch_results=[
            [
                {
                    "sequence": 1,
                    "event_type": "APPLICATION_STARTED",
                    "occurred_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
                    "received_at": datetime(2026, 8, 1, 0, 1, tzinfo=timezone.utc),
                    "source_system": "progress-api",
                    "source_event_id": "source-event-1",
                    "event_payload_hash": "hidden",
                    "dedupe_key": "hidden",
                    "idempotency_version": 1,
                    "source_inbox_status": "DUPLICATE",
                    "source_inbox_event_present": True,
                    "source_inbox_dedupe_present": True,
                    "source_inbox_payload_hash_present": True,
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
    assert safe_payload["timeline"][0]["recoveryPosture"] == "DEDUPE_REPLAY_RECORDED"
    assert safe_payload["timelineEvidenceSummary"]["duplicateReplayCount"] == 1
    assert safe_payload["timelineEvidenceSummary"]["recoveryPosture"] == "DEDUPE_REPLAY_RECORDED"
    assert "eventPayloadHash" not in safe_payload["timeline"][0]
    assert "dedupeKey" not in safe_payload["timeline"][0]
