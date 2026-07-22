from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest

from services import referral_saas_campaign_service as svc

pytestmark = pytest.mark.asyncio


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeCommandConnection:
    def __init__(self, fetchrow_results):
        self.fetchrow_results = list(fetchrow_results)
        self.fetchrow_calls = []

    async def fetchrow(self, query, *args):
        self.fetchrow_calls.append((query, args))
        if not self.fetchrow_results:
            raise AssertionError(f"Unexpected fetchrow call: {query}")
        return self.fetchrow_results.pop(0)

    def transaction(self):
        return FakeTransaction()


def patch_db(monkeypatch, connection):
    @asynccontextmanager
    async def fake_db_connection():
        yield connection

    monkeypatch.setattr(svc, "db_connection", fake_db_connection)


async def test_campaign_setup_create_records_inactive_campaign_and_audit(monkeypatch):
    conn = FakeCommandConnection(
        [
            None,
            None,
            {
                "campaign_code": "FNB-RETAIL-SUMMER-1234",
                "name": "Summer Referral",
                "segment": "Retail",
                "is_active": False,
                "starts_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
                "ends_at": None,
                "max_uses": 100,
            },
            {"account_audit_event_id": "audit-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.create_referral_saas_account_campaign_setup(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
        name="Summer Referral",
        segment="Retail",
        starts_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        max_uses=100,
        reason_code="CUSTOMER_PROFILE_CAMPAIGN_SETUP",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "CAMPAIGN_SETUP_DRAFT_RECORDED"
    assert safe_payload["campaign"]["setupStatus"] == "DRAFT"
    assert safe_payload["campaign"]["isActive"] is False
    assert safe_payload["idempotency"]["status"] == "RECORDED"
    assert "NO_CAMPAIGN_ACTIVATION" in safe_payload["guardrails"]
    joined_queries = "\n".join(query for query, _ in conn.fetchrow_calls)
    assert "INSERT INTO marketing_campaigns" in joined_queries
    assert "FALSE" in joined_queries
    assert "INSERT INTO platform_account_audit_events" in joined_queries
    assert "tenant_code" in joined_queries


async def test_campaign_setup_create_replays_matching_idempotency(monkeypatch):
    conn = FakeCommandConnection(
        [
            {
                "account_audit_event_id": "audit-1",
                "event_status": "RECORDED",
                "evidence_summary": {
                    "campaign_code": "FNB-RETAIL-SUMMER-1234",
                    "name": "Summer Referral",
                    "segment": "Retail",
                    "setup_status": "DRAFT",
                    "is_active": False,
                    "command_payload_hash": "payload-hash",
                },
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.create_referral_saas_account_campaign_setup(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
        name="Summer Referral",
        segment="Retail",
        reason_code="CUSTOMER_PROFILE_CAMPAIGN_SETUP",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "CAMPAIGN_SETUP_DRAFT_REPLAYED"
    assert safe_payload["campaign"]["campaignCode"] == "FNB-RETAIL-SUMMER-1234"
    assert safe_payload["idempotency"]["status"] == "REPLAYED"
    assert len(conn.fetchrow_calls) == 1


async def test_campaign_setup_create_conflicts_on_idempotency_payload_mismatch(
    monkeypatch,
):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                {
                    "account_audit_event_id": "audit-1",
                    "evidence_summary": {
                        "campaign_code": "FNB-RETAIL-SUMMER-1234",
                        "command_payload_hash": "original-hash",
                    },
                }
            ]
        ),
    )

    with pytest.raises(svc.CampaignSetupIdempotencyConflict):
        await svc.create_referral_saas_account_campaign_setup(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            external_reference_status="ACTIVE",
            name="Summer Referral",
            segment="Retail",
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_SETUP",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="new-hash",
        )


async def test_campaign_setup_create_rejects_duplicate_campaign(monkeypatch):
    patch_db(
        monkeypatch,
        FakeCommandConnection([None, {"campaign_code": "FNB-EXISTING"}]),
    )

    with pytest.raises(svc.CampaignSetupDuplicate):
        await svc.create_referral_saas_account_campaign_setup(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            external_reference_status="ACTIVE",
            name="Summer Referral",
            segment="Retail",
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_SETUP",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="payload-hash",
        )

