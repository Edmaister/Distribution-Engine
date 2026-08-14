from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "dp" / "migrations"
MIGRATION_NAME = "094_referral_saas_journey_configuration.sql"
MIGRATION_PATH = MIGRATION_DIR / MIGRATION_NAME

EXPECTED_TABLES = {
    "referral_saas_journey_templates": {
        "journey_template_id",
        "template_code",
        "template_name",
        "template_family",
        "owner_scope",
        "status",
        "safe_summary",
        "governance_metadata",
        "created_by_ref",
        "updated_by_ref",
        "created_at",
        "updated_at",
        "archived_at",
    },
    "referral_saas_journey_template_versions": {
        "journey_template_version_id",
        "journey_template_id",
        "template_code",
        "template_version",
        "status",
        "definition_payload",
        "milestone_schema",
        "transition_rules",
        "evidence_requirements",
        "allowed_configuration_schema",
        "payload_hash",
        "approved_by_ref",
        "approved_at",
        "created_by_ref",
        "created_at",
        "updated_at",
        "archived_at",
    },
    "referral_saas_customer_journey_drafts": {
        "customer_journey_draft_id",
        "account_id",
        "journey_template_version_id",
        "draft_name",
        "draft_status",
        "draft_version",
        "configuration_payload",
        "payload_hash",
        "last_validation_status",
        "idempotency_key_hash",
        "correlation_id",
        "created_by_ref",
        "updated_by_ref",
        "created_at",
        "updated_at",
        "archived_at",
    },
    "referral_saas_customer_journey_versions": {
        "customer_journey_version_id",
        "account_id",
        "customer_journey_draft_id",
        "journey_template_version_id",
        "customer_journey_code",
        "version_number",
        "version_status",
        "published_configuration_payload",
        "payload_hash",
        "published_by_ref",
        "published_at",
        "archived_by_ref",
        "archived_at",
        "archive_reason",
        "rollback_from_version_id",
        "safe_summary",
        "governance_metadata",
        "created_at",
    },
    "referral_saas_journey_validation_results": {
        "journey_validation_result_id",
        "account_id",
        "customer_journey_draft_id",
        "journey_template_version_id",
        "validation_status",
        "blockers",
        "warnings",
        "safe_summary",
        "payload_hash",
        "idempotency_key_hash",
        "correlation_id",
        "validated_by_ref",
        "created_at",
    },
    "referral_saas_campaign_journey_bindings": {
        "campaign_journey_binding_id",
        "account_id",
        "campaign_code",
        "customer_journey_version_id",
        "binding_status",
        "binding_payload_hash",
        "idempotency_key_hash",
        "correlation_id",
        "bound_by_ref",
        "bound_at",
        "unbound_by_ref",
        "unbound_at",
        "safe_summary",
        "governance_metadata",
    },
    "referral_saas_journey_configuration_idempotency_keys": {
        "journey_config_idempotency_id",
        "account_id",
        "operation_type",
        "idempotency_key_hash",
        "request_payload_hash",
        "response_payload_hash",
        "resource_type",
        "resource_id",
        "response_status",
        "expires_at",
        "created_at",
    },
    "referral_saas_journey_configuration_audit": {
        "journey_configuration_audit_id",
        "account_id",
        "journey_template_id",
        "journey_template_version_id",
        "customer_journey_draft_id",
        "customer_journey_version_id",
        "campaign_journey_binding_id",
        "event_type",
        "event_status",
        "actor_ref",
        "actor_role",
        "previous_status",
        "next_status",
        "reason_code",
        "correlation_id",
        "idempotency_key_hash",
        "evidence_summary",
        "redactions",
        "created_at",
    },
}

EXPECTED_INDEXES = {
    "idx_referral_saas_journey_templates_status",
    "idx_referral_saas_journey_template_versions_template",
    "idx_referral_saas_customer_journey_drafts_account",
    "idx_referral_saas_customer_journey_versions_account",
    "idx_referral_saas_customer_journey_versions_active",
    "idx_referral_saas_journey_validation_results_draft",
    "idx_referral_saas_campaign_journey_bindings_account",
    "idx_referral_saas_campaign_journey_bindings_active",
    "idx_referral_saas_journey_config_idempotency_unique",
    "idx_referral_saas_journey_configuration_audit_account",
    "idx_referral_saas_journey_configuration_audit_correlation",
}

FORBIDDEN_COLUMN_NAMES = {
    "tenant_code",
    "ucn",
    "raw_ucn",
    "raw_identity",
    "raw_event_payload",
    "provider_payload",
    "secret",
    "secret_value",
    "credential",
    "credential_value",
    "auth_claim",
    "billing_account",
    "wallet_id",
    "payout_id",
    "settlement_id",
    "invoice_id",
    "money_amount",
}


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


def test_journey_configuration_migration_is_ordered_after_runtime_adapter_work() -> None:
    migration_names = sorted(
        path.name
        for path in MIGRATION_DIR.glob("*.sql")
        if path.name.split("_", 1)[0].isdigit()
    )

    assert MIGRATION_NAME in migration_names
    assert migration_names.index("093_referral_saas_report_export_deletion_status.sql") < (
        migration_names.index(MIGRATION_NAME)
    )
    assert migration_names.index(MIGRATION_NAME) < migration_names.index("999_indexes.sql")


def test_journey_configuration_tables_are_present_with_expected_columns() -> None:
    for table_name, expected_columns in EXPECTED_TABLES.items():
        assert _column_names(table_name) == expected_columns


def test_customer_scoped_tables_reference_platform_account_not_tenant_code() -> None:
    sql = _sql()

    for table_name in (
        "referral_saas_customer_journey_drafts",
        "referral_saas_customer_journey_versions",
        "referral_saas_journey_validation_results",
        "referral_saas_campaign_journey_bindings",
        "referral_saas_journey_configuration_audit",
    ):
        block = _table_block(table_name)
        assert "account_id UUID" in block
        assert "REFERENCES platform_accounts(account_id)" in block

    assert "tenant_code" not in sql.lower()


def test_published_customer_journey_versions_have_immutable_publish_metadata() -> None:
    block = _table_block("referral_saas_customer_journey_versions")

    assert "version_number INTEGER NOT NULL" in block
    assert "published_configuration_payload JSONB NOT NULL DEFAULT '{}'::jsonb" in block
    assert "payload_hash TEXT NOT NULL" in block
    assert "published_by_ref TEXT NOT NULL" in block
    assert "published_at TIMESTAMPTZ NOT NULL DEFAULT NOW()" in block
    assert "UNIQUE (account_id, customer_journey_code, version_number)" in block


def test_validation_campaign_binding_audit_and_idempotency_fields_are_present() -> None:
    validation_block = _table_block("referral_saas_journey_validation_results")
    binding_block = _table_block("referral_saas_campaign_journey_bindings")
    idempotency_block = _table_block("referral_saas_journey_configuration_idempotency_keys")
    audit_block = _table_block("referral_saas_journey_configuration_audit")

    assert "blockers JSONB NOT NULL DEFAULT '[]'::jsonb" in validation_block
    assert "warnings JSONB NOT NULL DEFAULT '[]'::jsonb" in validation_block
    assert "safe_summary JSONB NOT NULL DEFAULT '{}'::jsonb" in validation_block
    assert "campaign_code TEXT NOT NULL" in binding_block
    assert "customer_journey_version_id UUID NOT NULL REFERENCES referral_saas_customer_journey_versions" in binding_block
    assert "idempotency_key_hash TEXT NOT NULL" in idempotency_block
    assert "request_payload_hash TEXT NOT NULL" in idempotency_block
    assert "response_payload_hash TEXT" in idempotency_block
    assert "evidence_summary JSONB NOT NULL DEFAULT '{}'::jsonb" in audit_block
    assert "redactions JSONB NOT NULL DEFAULT '[]'::jsonb" in audit_block


def test_status_constraints_and_indexes_are_present() -> None:
    sql = _sql()

    for table_name in EXPECTED_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" in sql

    for index_name in EXPECTED_INDEXES:
        assert f"CREATE INDEX IF NOT EXISTS {index_name}" in sql or (
            f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name}" in sql
        )

    assert "CHECK (owner_scope IN ('AMPLIFI_GOVERNED'))" in sql
    assert "CHECK (draft_status IN ('DRAFT', 'VALIDATION_FAILED', 'VALIDATED', 'READY_FOR_REVIEW', 'PUBLISHED', 'DISCARDED', 'ARCHIVED'))" in sql
    assert "CHECK (version_status IN ('PUBLISHED', 'ACTIVE', 'SUPERSEDED', 'ARCHIVED'))" in sql
    assert "CHECK (binding_status IN ('DRAFT', 'ACTIVE', 'SUPERSEDED', 'ARCHIVED'))" in sql
    assert "CHECK (response_status IN ('SUCCESS', 'REPLAY', 'CONFLICT', 'FAILED'))" in sql


def test_schema_does_not_add_unsafe_configuration_storage_columns() -> None:
    for table_name in EXPECTED_TABLES:
        assert _column_names(table_name).isdisjoint(FORBIDDEN_COLUMN_NAMES)
