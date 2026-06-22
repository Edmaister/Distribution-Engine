from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from services import outcome_trace_service as service


class FakeConnection:
    def __init__(self, *, fetchrow_result=None, fetch_results=None):
        self.fetchrow_result = fetchrow_result
        self.fetch_results = list(fetch_results or [])
        self.fetchrow_calls = []
        self.fetch_calls = []

    async def fetchrow(self, query, *args):
        self.fetchrow_calls.append((query, args))
        return self.fetchrow_result

    async def fetch(self, query, *args):
        self.fetch_calls.append((query, args))
        if not self.fetch_results:
            return []
        return self.fetch_results.pop(0)


class FakeConnectionContext:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _outcome():
    return {
        "referral_track_id": "11111111-1111-4111-8111-111111111111",
        "tenant_code": "FNB",
        "referral_code": "REF-CODE",
        "status": "COMPLETED",
        "is_complete": True,
        "product": "Transactional",
        "sub_product": "DDA13",
        "journey_code": "BANKING_TRANSACTIONAL",
        "journey_version": "v1",
        "validated_at": datetime(2026, 1, 1),
        "created_at": datetime(2026, 1, 1),
        "updated_at": datetime(2026, 1, 2),
        "completed_at": datetime(2026, 1, 3),
        "referrer_code_id": "22222222-2222-4222-8222-222222222222",
        "referrer_display_ref": "safe_handle",
        "sticker": "TEST",
        "segment": "TEST_SEGMENT",
    }


def _full_fetch_results():
    return [
        [
            {
                "source_type": "CAMPAIGN_REFERRAL_LINK",
                "campaign_track_id": "33333333-3333-4333-8333-333333333333",
                "campaign_code": "CAMP-001",
                "tenant_code": "FNB",
                "campaign_track_status": "ATTRIBUTED",
                "source_confidence": "MEDIUM",
            }
        ],
        [
            {
                "source_type": "ROUTE_REFERRAL_LINK",
                "route_id": "44444444-4444-4444-8444-444444444444",
                "tenant_code": "FNB",
                "distributor_id": "55555555-5555-4555-8555-555555555555",
                "distributor_code": "DIST-001",
                "distributor_name": "Distribution Partner",
                "opportunity_id": "66666666-6666-4666-8666-666666666666",
                "opportunity_code": "OPP-001",
                "campaign_code": "CAMP-001",
                "sponsor_code": "SPONSOR-001",
                "link_status": "ACTIVE",
                "source_confidence": "MEDIUM",
            }
        ],
        [{"source": "REFERRAL_PROGRESS_EVENT", "event_type": "ACCOUNT_OPENED"}],
        [{"source": "ENTERPRISE_EVENT_INBOX", "event_type": "ACCOUNT_OPENED"}],
        [
            {
                "source": "referral_rewards",
                "reward_id": "77777777-7777-4777-8777-777777777777",
                "reward_type": "REFERRER",
                "amount": Decimal("100.00"),
            }
        ],
        [
            {
                "commission_event_id": "88888888-8888-4888-8888-888888888888",
                "commission_status": "CREDITED",
                "commission_amount": Decimal("25.00"),
                "source_event_id": "11111111-1111-4111-8111-111111111111",
            }
        ],
        [
            {
                "source": "marketplace_funding_allocations",
                "funding_id": "99999999-9999-4999-8999-999999999999",
                "status": "RESERVED",
                "amount": Decimal("100.00"),
            }
        ],
        [
            {
                "audit_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                "status": "SUCCESS",
                "idempotency_key": "fulfilment:reward-1",
                "correlation_id": "11111111-1111-4111-8111-111111111111",
            }
        ],
        [
            {
                "settlement_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                "status": "SETTLED",
                "amount": Decimal("100.00"),
                "exception_count": 0,
                "reversal_count": 0,
            }
        ],
        [
            {
                "source": "admin_audit_log",
                "audit_id": "audit-1",
                "action_domain": "fulfilment",
                "action_type": "replay",
                "action_status": "SUCCESS",
                "target_type": "fulfilment_audit",
                "target_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                "correlation_id": "11111111-1111-4111-8111-111111111111",
                "error_message": "raw provider timeout detail",
            }
        ],
        [
            {
                "source": "referral_processing_audit",
                "audit_id": "audit-2",
                "event_id": "event-1",
                "event_type": "ACCOUNT_OPENED",
                "processing_status": "PROCESSED",
            }
        ],
        [
            {
                "delivery_id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                "delivery_status": "SENT",
            }
        ],
    ]


@pytest.mark.asyncio
async def test_get_outcome_trace_returns_contract_shape_for_complete_source_trail(
    monkeypatch,
):
    conn = FakeConnection(
        fetchrow_result=_outcome(), fetch_results=_full_fetch_results()
    )
    monkeypatch.setattr(service, "db_connection", lambda: FakeConnectionContext(conn))

    result = await service.get_outcome_trace(
        tenant_code="fnb",
        referral_track_id="11111111-1111-4111-8111-111111111111",
        identity={"role": "ADMIN"},
    )

    assert conn.fetchrow_calls[0][1] == (
        "11111111-1111-4111-8111-111111111111",
        "FNB",
    )
    assert result["trace_id"] == (
        "outcome:referral_track_id:11111111-1111-4111-8111-111111111111"
    )
    assert result["trace_type"] == "OUTCOME"
    assert result["tenant_code"] == "FNB"
    assert result["trace_completeness"] == "COMPLETE"
    assert result["sections"]["outcome"]["status"] == "COMPLETED"
    assert (
        result["sections"]["participants"]["items"][0]["safe_display_ref"]
        == "safe_handle"
    )
    assert (
        result["sections"]["participants"]["items"][1]["participant_type"]
        == "DISTRIBUTOR"
    )
    assert result["sections"]["reward"]["count"] == 1
    assert result["sections"]["fulfilment"]["items"][0]["status"] == "SUCCESS"
    assert (
        result["sections"]["fulfilment"]["items"][0]["operator_safe_status"]["status"]
        == "FULFILLED"
    )
    assert (
        result["sections"]["fulfilment"]["items"][0]["external_safe_status"]["status"]
        == "FULFILLED"
    )
    assert result["sections"]["settlement"]["items"][0]["status"] == "SETTLED"
    assert (
        result["sections"]["settlement"]["items"][0]["operator_safe_status"]["status"]
        == "SETTLED"
    )
    assert (
        result["sections"]["settlement"]["items"][0]["external_safe_status"]["status"]
        == "SETTLED"
    )
    assert result["missing_evidence"] == []
    assert result["support_trace"]["audit_reference_count"] == 3
    assert result["support_trace"]["correlation_reference_count"] >= 4
    assert {
        item["audit_id"] for item in result["support_trace"]["audit_references"]
    } == {
        "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        "audit-1",
        "audit-2",
    }
    assert any(
        item["reference_type"] == "idempotency_key"
        and item["value"] == "fulfilment:reward-1"
        for item in result["support_trace"]["correlation_references"]
    )
    assert "raw provider timeout detail" not in str(result["support_trace"])
    assert "referrer_ucn" not in result["sections"]["outcome"]
    assert "referee_ucn" not in result["sections"]["outcome"]


@pytest.mark.asyncio
async def test_get_outcome_trace_returns_missing_evidence_for_broken_trail(monkeypatch):
    conn = FakeConnection(
        fetchrow_result=_outcome(),
        fetch_results=[
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
        ],
    )
    monkeypatch.setattr(service, "db_connection", lambda: FakeConnectionContext(conn))

    result = await service.get_outcome_trace(
        tenant_code="FNB",
        referral_track_id="11111111-1111-4111-8111-111111111111",
        identity={"role": "ADMIN"},
    )

    assert result["trace_completeness"] == "PARTIAL"
    codes_by_section = {
        item["section"]: item["code"] for item in result["missing_evidence"]
    }
    assert codes_by_section["attribution"] == "NO_SOURCE_EVIDENCE"
    assert codes_by_section["events"] == "NO_SOURCE_EVIDENCE"
    assert codes_by_section["reward"] == "NO_SOURCE_EVIDENCE"
    assert codes_by_section["commission"] == "JOIN_AMBIGUOUS"
    assert codes_by_section["funding"] == "JOIN_AMBIGUOUS"
    assert codes_by_section["fulfilment"] == "NO_SOURCE_EVIDENCE"
    assert codes_by_section["settlement"] == "NO_SOURCE_EVIDENCE"
    assert codes_by_section["audit"] == "NO_SOURCE_EVIDENCE"
    assert codes_by_section["webhooks"] == "JOIN_AMBIGUOUS"
    assert result["support_trace"]["missing_audit_evidence"] == [
        item for item in result["missing_evidence"] if item["section"] == "audit"
    ]


@pytest.mark.asyncio
async def test_get_outcome_trace_raises_for_tenant_scoped_missing_outcome(monkeypatch):
    conn = FakeConnection(fetchrow_result=None)
    monkeypatch.setattr(service, "db_connection", lambda: FakeConnectionContext(conn))

    with pytest.raises(service.OutcomeTraceNotFound):
        await service.get_outcome_trace(
            tenant_code="FNB",
            referral_track_id="11111111-1111-4111-8111-111111111111",
            identity={"role": "ADMIN"},
        )


@pytest.mark.asyncio
async def test_get_outcome_trace_supports_requested_sections(monkeypatch):
    conn = FakeConnection(
        fetchrow_result=_outcome(),
        fetch_results=[
            [],
            [],
            [],
            [],
            [
                {
                    "source": "referral_rewards",
                    "reward_id": "77777777-7777-4777-8777-777777777777",
                    "reward_type": "REFERRER",
                }
            ],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
        ],
    )
    monkeypatch.setattr(service, "db_connection", lambda: FakeConnectionContext(conn))

    result = await service.get_outcome_trace(
        tenant_code="FNB",
        referral_track_id="11111111-1111-4111-8111-111111111111",
        identity={"role": "ADMIN"},
        include_sections=["reward"],
    )

    assert set(result["sections"]) == {"outcome", "reward"}
    assert result["sections"]["reward"]["count"] == 1
    assert any(
        item["section"] == "funding" and item["code"] == "SECTION_NOT_REQUESTED"
        for item in result["missing_evidence"]
    )
