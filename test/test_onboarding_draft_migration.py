from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "dp" / "migrations"
MIGRATION_NAME = "080_onboarding_draft_persistence.sql"
MIGRATION_PATH = MIGRATION_DIR / MIGRATION_NAME

EXPECTED_TABLES = {
    "onboarding_drafts": {
        "draft_id",
        "draft_ref",
        "contract_version",
        "status",
        "draft_version",
        "external_tenant_ref",
        "organisation_ref",
        "producer_ref",
        "sponsor_ref",
        "distributor_ref",
        "campaign_code",
        "opportunity_ref",
        "created_by_ref",
        "created_by_role",
        "updated_by_ref",
        "source",
        "correlation_id",
        "safe_summary",
        "metadata",
        "redactions",
        "created_at",
        "updated_at",
        "expires_at",
        "discarded_at",
    },
    "onboarding_draft_sections": {
        "section_id",
        "draft_id",
        "section_key",
        "section_status",
        "section_version",
        "section_payload",
        "payload_hash",
        "redaction_summary",
        "missing_evidence",
        "source_warnings",
        "created_at",
        "updated_at",
    },
    "onboarding_draft_validation_results": {
        "validation_id",
        "draft_id",
        "draft_version",
        "validation_scope",
        "validation_type",
        "validation_status",
        "safe_error_code",
        "section_key",
        "field_name",
        "message",
        "safe_errors",
        "missing_evidence",
        "blockers",
        "warnings",
        "readiness_preview",
        "details",
        "correlation_id",
        "validated_at",
    },
    "onboarding_draft_idempotency_keys": {
        "idempotency_id",
        "draft_id",
        "draft_ref",
        "idempotency_key_hash",
        "scope_hash",
        "actor_ref",
        "external_tenant_ref",
        "operation_type",
        "request_hash",
        "response_hash",
        "result_status",
        "correlation_id",
        "first_seen_at",
        "last_seen_at",
        "expires_at",
    },
    "onboarding_draft_audit_links": {
        "audit_link_id",
        "draft_id",
        "draft_ref",
        "draft_version",
        "action_type",
        "action_status",
        "actor_ref",
        "actor_role",
        "audit_ref",
        "event_ref",
        "idempotency_id",
        "correlation_id",
        "before_state_hash",
        "after_state_hash",
        "changed_sections",
        "redactions",
        "evidence_type",
        "evidence_summary",
        "created_at",
    },
}

EXPECTED_INDEXES = {
    "idx_onboarding_drafts_external_scope",
    "idx_onboarding_drafts_active_scope",
    "idx_onboarding_drafts_status",
    "idx_onboarding_drafts_created",
    "idx_onboarding_drafts_updated",
    "idx_onboarding_drafts_correlation",
    "idx_onboarding_drafts_expires",
    "idx_onboarding_draft_sections_lookup",
    "idx_onboarding_draft_sections_status",
    "idx_onboarding_draft_sections_payload_hash",
    "idx_onboarding_draft_sections_updated",
    "idx_onboarding_draft_validation_results_lookup",
    "idx_onboarding_draft_validation_results_version",
    "idx_onboarding_draft_validation_results_type",
    "idx_onboarding_draft_validation_results_status",
    "idx_onboarding_draft_validation_results_error",
    "idx_onboarding_draft_validation_results_created",
    "idx_onboarding_draft_validation_results_correlation",
    "idx_onboarding_draft_idempotency_keys_key",
    "idx_onboarding_draft_idempotency_keys_actor_scope",
    "idx_onboarding_draft_idempotency_keys_draft",
    "idx_onboarding_draft_idempotency_keys_draft_ref",
    "idx_onboarding_draft_idempotency_keys_request",
    "idx_onboarding_draft_idempotency_keys_correlation",
    "idx_onboarding_draft_idempotency_keys_expires",
    "idx_onboarding_draft_audit_links_draft",
    "idx_onboarding_draft_audit_links_draft_ref",
    "idx_onboarding_draft_audit_links_action",
    "idx_onboarding_draft_audit_links_status",
    "idx_onboarding_draft_audit_links_actor",
    "idx_onboarding_draft_audit_links_audit_ref",
    "idx_onboarding_draft_audit_links_event_ref",
    "idx_onboarding_draft_audit_links_idempotency",
    "idx_onboarding_draft_audit_links_correlation",
    "idx_onboarding_draft_audit_links_created",
}

FORBIDDEN_LIVE_ACTION_COLUMN_TOKENS = (
    "api_key",
    "credential",
    "secret",
    "signing",
    "token",
    "webhook_delivery",
    "funding",
    "wallet",
    "fulfilment",
    "settlement",
    "retry",
    "go_live",
    "money",
)


def _sql() -> str:
    return MIGRATION_PATH.read_text(encoding="utf-8")


def _extract_parenthesized_block(sql: str, start_pattern: str) -> str:
    match = re.search(start_pattern, sql, flags=re.IGNORECASE)
    assert match is not None

    start = sql.index("(", match.end() - 1)
    depth = 0
    for index in range(start, len(sql)):
        char = sql[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return sql[start + 1 : index]

    raise AssertionError(f"Could not find end of block for {start_pattern}")


def _table_block(table_name: str) -> str:
    return _extract_parenthesized_block(
        _sql(),
        rf"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+{table_name}\s*\(",
    )


def _column_names(table_name: str) -> set[str]:
    columns: set[str] = set()
    for line in _table_block(table_name).splitlines():
        stripped = line.strip().rstrip(",")
        if not stripped or stripped.upper().startswith("CONSTRAINT"):
            continue

        column_name = stripped.split(maxsplit=1)[0]
        if re.fullmatch(r"[a-z_][a-z0-9_]*", column_name):
            columns.add(column_name)

    return columns


def test_onboarding_draft_migration_is_ordered_after_partner_webhooks() -> None:
    migration_names = sorted(
        path.name
        for path in MIGRATION_DIR.glob("*.sql")
        if path.name.split("_", 1)[0].isdigit()
    )

    assert MIGRATION_NAME in migration_names
    assert migration_names.index("079_partner_webhook_alert_notifications.sql") < (
        migration_names.index(MIGRATION_NAME)
    )
    assert migration_names.index(MIGRATION_NAME) < migration_names.index(
        "999_indexes.sql"
    )


def test_onboarding_draft_tables_and_key_columns_are_declared() -> None:
    sql = _sql()

    for table_name, expected_columns in EXPECTED_TABLES.items():
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" in sql
        assert expected_columns <= _column_names(table_name)
        assert "PRIMARY KEY DEFAULT gen_random_uuid()" in _table_block(table_name)


def test_onboarding_draft_foreign_keys_are_declared() -> None:
    assert "draft_id UUID NOT NULL REFERENCES onboarding_drafts(draft_id)" in _sql()
    assert "draft_id UUID REFERENCES onboarding_drafts(draft_id)" in _sql()
    assert (
        "idempotency_id UUID REFERENCES onboarding_draft_idempotency_keys"
        "(idempotency_id)"
    ) in _sql()


def test_onboarding_draft_uniqueness_constraints_are_declared() -> None:
    sql = _sql()

    assert "CONSTRAINT onboarding_drafts_draft_ref_key UNIQUE (draft_ref)" in sql
    assert "UNIQUE (draft_id, section_key)" in sql
    assert "UNIQUE (idempotency_key_hash, scope_hash)" in sql
    assert "CREATE UNIQUE INDEX IF NOT EXISTS idx_onboarding_drafts_active_scope" in sql


def test_onboarding_draft_indexes_cover_required_lookup_patterns() -> None:
    sql = _sql()

    for index_name in EXPECTED_INDEXES:
        assert (
            f"CREATE INDEX IF NOT EXISTS {index_name}" in sql
            or f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name}" in sql
        )


def test_tenant_code_is_not_introduced_as_draft_column() -> None:
    all_columns = set().union(
        *(_column_names(table_name) for table_name in EXPECTED_TABLES)
    )

    assert "tenant_code" not in all_columns


def test_idempotency_uses_hash_fields_not_raw_keys() -> None:
    columns = _column_names("onboarding_draft_idempotency_keys")

    assert {"idempotency_key_hash", "scope_hash", "request_hash"} <= columns
    assert "idempotency_key" not in columns
    assert "request_payload" not in columns
    assert "response_payload" not in columns


def test_migration_does_not_add_live_action_tables_or_columns() -> None:
    table_names = set(EXPECTED_TABLES)
    all_columns = set().union(
        *(_column_names(table_name) for table_name in EXPECTED_TABLES)
    )

    for name in table_names | all_columns:
        for forbidden_token in FORBIDDEN_LIVE_ACTION_COLUMN_TOKENS:
            assert forbidden_token not in name
