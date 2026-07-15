from __future__ import annotations

from contextlib import asynccontextmanager

import pytest

from services.onboarding import onboarding_draft_repository as repo


class FakeConn:
    def __init__(self, *, rows=None, fetchrow_rows=None):
        self.rows = list(rows or [])
        self.fetchrow_rows = list(fetchrow_rows or [])
        self.fetchrow_calls = []
        self.fetch_calls = []

    async def fetchrow(self, query, *params):
        self.fetchrow_calls.append((query, params))
        if self.fetchrow_rows:
            return self.fetchrow_rows.pop(0)
        return None

    async def fetch(self, query, *params):
        self.fetch_calls.append((query, params))
        return self.rows


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(repo, "db_connection", fake_db_connection)


def _draft_row(**overrides):
    row = {
        "draft_id": "draft-uuid",
        "draft_ref": "draft_001",
        "draft_version": 1,
        "external_tenant_ref": "tenant-ext-1",
        "organisation_ref": "org-1",
        "status": "DRAFT_CREATED",
        "metadata": {},
        "safe_summary": {},
        "redactions": [],
    }
    row.update(overrides)
    return row


@pytest.mark.asyncio
async def test_create_and_read_draft_by_external_references(monkeypatch):
    conn = FakeConn(fetchrow_rows=[_draft_row(), _draft_row()])
    patch_db(monkeypatch, conn)

    created = await repo.create_draft(
        draft_ref="draft_001",
        external_tenant_ref="tenant-ext-1",
        organisation_ref="org-1",
        producer_ref="producer-1",
        created_by_ref="actor-1",
        created_by_role="PLATFORM_OPERATOR",
        safe_summary={"sections": ["company"]},
    )
    fetched = await repo.get_draft_by_ref("draft_001")

    assert created["draft_ref"] == "draft_001"
    assert fetched["external_tenant_ref"] == "tenant-ext-1"
    assert len(conn.fetchrow_calls) == 2
    assert "tenant_code" not in conn.fetchrow_calls[0][0]
    assert "INSERT INTO onboarding_drafts" in conn.fetchrow_calls[0][0]
    assert "SELECT *" in conn.fetchrow_calls[1][0]


@pytest.mark.asyncio
async def test_list_drafts_returns_safe_selector_rows(monkeypatch):
    conn = FakeConn(rows=[_draft_row(source="ADMIN_ONBOARDING")])
    patch_db(monkeypatch, conn)

    rows = await repo.list_drafts(
        external_tenant_ref="tenant-ext-1",
        organisation_ref="org-1",
        status="DRAFT_CREATED",
        limit=100,
    )

    query, params = conn.fetch_calls[0]
    assert rows[0]["draft_ref"] == "draft_001"
    assert params == ("tenant-ext-1", "org-1", "DRAFT_CREATED", 50)
    assert "FROM onboarding_drafts" in query
    assert "ORDER BY updated_at DESC, created_at DESC" in query
    assert "tenant_code" not in query
    assert "created_by_ref" not in query


@pytest.mark.asyncio
async def test_create_draft_rejects_obvious_secret_payload(monkeypatch):
    conn = FakeConn(fetchrow_rows=[_draft_row()])
    patch_db(monkeypatch, conn)

    with pytest.raises(repo.UnsafeDraftPayloadError, match="api_key"):
        await repo.create_draft(
            draft_ref="draft_001",
            external_tenant_ref="tenant-ext-1",
            organisation_ref="org-1",
            created_by_ref="actor-1",
            created_by_role="PLATFORM_OPERATOR",
            metadata={"api_key": "not-for-drafts"},
        )

    assert conn.fetchrow_calls == []


@pytest.mark.asyncio
async def test_upsert_and_read_draft_section(monkeypatch):
    section_row = {
        "section_id": "section-uuid",
        "draft_id": "draft-uuid",
        "section_key": "company",
        "section_status": "IN_PROGRESS",
        "section_payload": {"organisation_ref": "org-1"},
        "payload_hash": "payload-hash",
    }
    conn = FakeConn(fetchrow_rows=[section_row], rows=[section_row])
    patch_db(monkeypatch, conn)

    upserted = await repo.upsert_draft_section(
        draft_id="draft-uuid",
        section_key="company",
        section_status="IN_PROGRESS",
        section_payload={"organisation_ref": "org-1"},
        payload_hash="payload-hash",
        redaction_summary={"redactions": []},
    )
    sections = await repo.get_draft_sections("draft-uuid")

    assert upserted["section_key"] == "company"
    assert sections == [section_row]
    assert "ON CONFLICT (draft_id, section_key)" in conn.fetchrow_calls[0][0]
    assert "ORDER BY section_key" in conn.fetch_calls[0][0]


@pytest.mark.asyncio
async def test_upsert_draft_section_rejects_live_action_payload(monkeypatch):
    conn = FakeConn()
    patch_db(monkeypatch, conn)

    with pytest.raises(repo.UnsafeDraftPayloadError, match="deliver_webhook"):
        await repo.upsert_draft_section(
            draft_id="draft-uuid",
            section_key="webhook_api",
            section_status="DRAFT",
            section_payload={"deliver_webhook": True},
        )

    assert conn.fetchrow_calls == []


@pytest.mark.asyncio
async def test_update_draft_uses_expected_version_and_increments(monkeypatch):
    updated_row = _draft_row(draft_version=2, status="DRAFT_UPDATED")
    conn = FakeConn(fetchrow_rows=[updated_row])
    patch_db(monkeypatch, conn)

    updated = await repo.update_draft_metadata_or_status(
        draft_ref="draft_001",
        expected_draft_version=1,
        status="DRAFT_UPDATED",
        metadata={"note": "safe"},
        updated_by_ref="actor-2",
    )

    query, params = conn.fetchrow_calls[0]
    assert updated["draft_version"] == 2
    assert "draft_version = draft_version + 1" in query
    assert "WHERE draft_ref = $1" in query
    assert "AND draft_version = $2" in query
    assert params[0:3] == ("draft_001", 1, "DRAFT_UPDATED")


@pytest.mark.asyncio
async def test_update_draft_stale_version_raises(monkeypatch):
    conn = FakeConn(fetchrow_rows=[None])
    patch_db(monkeypatch, conn)

    with pytest.raises(repo.StaleDraftVersionError):
        await repo.update_draft_metadata_or_status(
            draft_ref="draft_001",
            expected_draft_version=99,
            status="DRAFT_UPDATED",
        )


@pytest.mark.asyncio
async def test_record_validation_result(monkeypatch):
    validation_row = {
        "validation_id": "validation-uuid",
        "draft_id": "draft-uuid",
        "validation_scope": "readiness",
        "validation_status": "BLOCKED",
        "safe_errors": [{"code": "MISSING_EVIDENCE"}],
    }
    conn = FakeConn(fetchrow_rows=[validation_row])
    patch_db(monkeypatch, conn)

    result = await repo.record_validation_result(
        draft_id="draft-uuid",
        draft_version=1,
        validation_scope="readiness",
        validation_status="BLOCKED",
        safe_errors=[{"code": "MISSING_EVIDENCE"}],
        readiness_preview={"status": "REVIEW_ONLY"},
    )

    assert result["validation_status"] == "BLOCKED"
    assert "INSERT INTO onboarding_draft_validation_results" in conn.fetchrow_calls[0][0]


@pytest.mark.asyncio
async def test_record_and_get_idempotency_reference_uses_hash_fields(monkeypatch):
    idem_row = {
        "idempotency_id": "idem-uuid",
        "idempotency_key_hash": "key-hash",
        "scope_hash": "scope-hash",
        "request_hash": "request-hash",
        "result_status": "SUCCESS",
    }
    conn = FakeConn(fetchrow_rows=[idem_row, idem_row])
    patch_db(monkeypatch, conn)

    recorded = await repo.record_idempotency_reference(
        idempotency_key_hash="key-hash",
        scope_hash="scope-hash",
        actor_ref="actor-1",
        external_tenant_ref="tenant-ext-1",
        operation_type="ONBOARDING_DRAFT_CREATE",
        request_hash="request-hash",
        response_hash="response-hash",
        result_status="SUCCESS",
    )
    fetched = await repo.get_idempotency_reference(
        idempotency_key_hash="key-hash",
        scope_hash="scope-hash",
    )

    insert_query = conn.fetchrow_calls[0][0]
    assert recorded["idempotency_key_hash"] == "key-hash"
    assert fetched["scope_hash"] == "scope-hash"
    assert "idempotency_key_hash" in insert_query
    assert "scope_hash" in insert_query
    assert "idempotency_key TEXT" not in insert_query
    assert "request_payload" not in insert_query


@pytest.mark.asyncio
async def test_create_audit_link_reference_only(monkeypatch):
    audit_row = {
        "audit_link_id": "audit-link-uuid",
        "draft_id": "draft-uuid",
        "draft_ref": "draft_001",
        "action_type": "ONBOARDING_DRAFT_UPDATE",
        "action_status": "SUCCESS",
        "audit_ref": "audit-ref-only",
        "event_ref": None,
    }
    conn = FakeConn(fetchrow_rows=[audit_row])
    patch_db(monkeypatch, conn)

    result = await repo.create_audit_link_reference(
        draft_id="draft-uuid",
        draft_ref="draft_001",
        draft_version=2,
        action_type="ONBOARDING_DRAFT_UPDATE",
        action_status="SUCCESS",
        actor_ref="actor-1",
        actor_role="PLATFORM_OPERATOR",
        correlation_id="corr-1",
        evidence_type="AUDIT_REFERENCE",
        audit_ref="audit-ref-only",
        changed_sections=["company"],
        evidence_summary={"summary": "reference only"},
    )

    assert result["audit_ref"] == "audit-ref-only"
    assert result["event_ref"] is None
    assert "INSERT INTO onboarding_draft_audit_links" in conn.fetchrow_calls[0][0]


def test_payload_guard_allows_intent_fields_but_blocks_live_action_fields():
    safe = repo._ensure_safe_payload(
        {
            "funding_model_intention": "review later",
            "go_live_target_status": "review only",
            "selected_webhook_event_categories": ["campaign"],
        }
    )

    assert safe["funding_model_intention"] == "review later"

    with pytest.raises(repo.UnsafeDraftPayloadError, match="wallet"):
        repo._ensure_safe_payload({"wallet_account_number": "unsafe"})


def test_repository_module_does_not_define_route_or_live_action_helpers():
    public_names = {
        name
        for name in dir(repo)
        if not name.startswith("_") and callable(getattr(repo, name))
    }

    forbidden_name_parts = (
        "route",
        "publish",
        "invite",
        "credential",
        "webhook_delivery",
        "fund",
        "fulfil",
        "settle",
        "retry",
        "wallet",
        "go_live",
    )
    for name in public_names:
        for forbidden in forbidden_name_parts:
            assert forbidden not in name
