from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "dp" / "migrations"
MIGRATION_NAME = "096_referral_saas_programme_configuration.sql"
MIGRATION_PATH = MIGRATION_DIR / MIGRATION_NAME

EXPECTED_TABLES = {
    "referral_saas_programme_drafts": {
        "programme_draft_id",
        "account_id",
        "source_programme_version_id",
        "customer_journey_version_id",
        "programme_name",
        "programme_description",
        "operating_jurisdiction_code",
        "product_code",
        "sub_product_code",
        "programme_status",
        "draft_version",
        "campaign_defaults",
        "incentive_refs",
        "engagement_refs",
        "integration_readiness_snapshot",
        "commercial_entitlement_snapshot",
        "validation_result_id",
        "last_validation_status",
        "review_status",
        "effective_from",
        "effective_to",
        "configuration_checksum",
        "payload_hash",
        "idempotency_key_hash",
        "correlation_id",
        "created_by_ref",
        "updated_by_ref",
        "created_at",
        "updated_at",
        "archived_at",
    },
    "referral_saas_programme_versions": {
        "programme_version_id",
        "account_id",
        "programme_draft_id",
        "source_programme_version_id",
        "customer_journey_version_id",
        "programme_code",
        "programme_name",
        "programme_description",
        "operating_jurisdiction_code",
        "product_code",
        "sub_product_code",
        "version_number",
        "version_status",
        "published_configuration_snapshot",
        "campaign_defaults_snapshot",
        "incentive_refs_snapshot",
        "engagement_refs_snapshot",
        "integration_readiness_snapshot",
        "commercial_entitlement_snapshot",
        "validation_result_id",
        "review_status",
        "reviewed_by_ref",
        "reviewed_at",
        "review_reason",
        "effective_from",
        "effective_to",
        "configuration_checksum",
        "payload_hash",
        "published_by_ref",
        "published_at",
        "retired_by_ref",
        "retired_at",
        "retirement_reason",
        "rollback_from_version_id",
        "safe_summary",
        "governance_metadata",
        "created_at",
    },
    "referral_saas_programme_validation_results": {
        "programme_validation_result_id",
        "account_id",
        "programme_draft_id",
        "programme_version_id",
        "customer_journey_version_id",
        "validation_status",
        "publish_allowed",
        "campaign_binding_allowed",
        "plain_language_summary",
        "blockers",
        "warnings",
        "configuration_snapshot",
        "guardrails",
        "payload_hash",
        "idempotency_key_hash",
        "correlation_id",
        "validated_by_ref",
        "created_at",
    },
    "referral_saas_programme_configuration_idempotency_keys": {
        "programme_config_idempotency_id",
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
    "referral_saas_programme_configuration_audit": {
        "programme_configuration_audit_id",
        "account_id",
        "programme_draft_id",
        "programme_version_id",
        "programme_validation_result_id",
        "customer_journey_version_id",
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
    "idx_referral_saas_programme_drafts_account",
    "idx_referral_saas_programme_drafts_journey_version",
    "idx_referral_saas_programme_versions_account",
    "idx_referral_saas_programme_versions_active",
    "idx_referral_saas_programme_versions_journey_version",
    "idx_referral_saas_programme_validation_results_draft",
    "idx_referral_saas_programme_config_idempotency_unique",
    "idx_referral_saas_programme_configuration_audit_account",
    "idx_referral_saas_programme_configuration_audit_correlation",
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


def test_programme_configuration_migration_is_ordered_after_journey_foundation() -> None:
    migration_names = sorted(
        path.name
        for path in MIGRATION_DIR.glob("*.sql")
        if path.name.split("_", 1)[0].isdigit()
    )

    assert MIGRATION_NAME in migration_names
    assert migration_names.index("095_referral_saas_journey_incentive_bindings.sql") < (
        migration_names.index(MIGRATION_NAME)
    )
    assert migration_names.index(MIGRATION_NAME) < migration_names.index("999_indexes.sql")


def test_programme_configuration_tables_are_present_with_expected_columns() -> None:
    for table_name, expected_columns in EXPECTED_TABLES.items():
        assert _column_names(table_name) == expected_columns


def test_programme_tables_are_account_scoped_and_bind_published_journey_versions() -> None:
    sql = _sql()

    for table_name in (
        "referral_saas_programme_drafts",
        "referral_saas_programme_versions",
        "referral_saas_programme_validation_results",
        "referral_saas_programme_configuration_audit",
    ):
        block = _table_block(table_name)
        assert "account_id UUID" in block
        assert "REFERENCES platform_accounts(account_id)" in block

    assert (
        "customer_journey_version_id UUID NOT NULL\n"
        "        REFERENCES referral_saas_customer_journey_versions"
    ) in sql
    assert "tenant_code" not in sql.lower()


def test_programme_versions_have_immutable_publish_and_effective_date_metadata() -> None:
    block = _table_block("referral_saas_programme_versions")

    assert "version_number INTEGER NOT NULL" in block
    assert "published_configuration_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb" in block
    assert "configuration_checksum TEXT NOT NULL" in block
    assert "payload_hash TEXT NOT NULL" in block
    assert "published_by_ref TEXT NOT NULL" in block
    assert "published_at TIMESTAMPTZ NOT NULL DEFAULT NOW()" in block
    assert "effective_from DATE NOT NULL" in block
    assert "effective_to DATE" in block
    assert "UNIQUE (account_id, programme_code, version_number)" in block
    assert "CHECK (effective_to IS NULL OR effective_to > effective_from)" in block
    assert "updated_at" not in block


def test_programme_drafts_can_store_complete_safe_configuration_intent() -> None:
    block = _table_block("referral_saas_programme_drafts")

    assert "programme_name TEXT NOT NULL" in block
    assert "operating_jurisdiction_code TEXT NOT NULL" in block
    assert "product_code TEXT NOT NULL DEFAULT 'REFERRAL_SAAS'" in block
    assert "sub_product_code TEXT NOT NULL" in block
    assert "campaign_defaults JSONB NOT NULL DEFAULT '{}'::jsonb" in block
    assert "incentive_refs JSONB NOT NULL DEFAULT '[]'::jsonb" in block
    assert "engagement_refs JSONB NOT NULL DEFAULT '[]'::jsonb" in block
    assert "integration_readiness_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb" in block
    assert "commercial_entitlement_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb" in block
    assert "payload_hash TEXT NOT NULL" in block
    assert "draft_version INTEGER NOT NULL DEFAULT 1" in block


def test_validation_idempotency_audit_and_replay_controls_are_present() -> None:
    validation_block = _table_block("referral_saas_programme_validation_results")
    idempotency_block = _table_block(
        "referral_saas_programme_configuration_idempotency_keys"
    )
    audit_block = _table_block("referral_saas_programme_configuration_audit")
    sql = _sql()

    assert "publish_allowed BOOLEAN NOT NULL DEFAULT FALSE" in validation_block
    assert "campaign_binding_allowed BOOLEAN NOT NULL DEFAULT FALSE" in validation_block
    assert "plain_language_summary TEXT NOT NULL" in validation_block
    assert "blockers JSONB NOT NULL DEFAULT '[]'::jsonb" in validation_block
    assert "warnings JSONB NOT NULL DEFAULT '[]'::jsonb" in validation_block
    assert "configuration_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb" in validation_block
    assert "guardrails JSONB NOT NULL DEFAULT '[]'::jsonb" in validation_block
    assert "idempotency_key_hash TEXT NOT NULL" in idempotency_block
    assert "request_payload_hash TEXT NOT NULL" in idempotency_block
    assert "response_payload_hash TEXT" in idempotency_block
    assert "evidence_summary JSONB NOT NULL DEFAULT '{}'::jsonb" in audit_block
    assert "redactions JSONB NOT NULL DEFAULT '[]'::jsonb" in audit_block
    assert "idx_referral_saas_programme_config_idempotency_unique" in sql
    assert "COALESCE(account_id, '00000000-0000-0000-0000-000000000000'::uuid)" in sql


def test_status_constraints_indexes_and_replay_safe_constraints_are_present() -> None:
    sql = _sql()

    for table_name in EXPECTED_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" in sql

    for index_name in EXPECTED_INDEXES:
        assert f"CREATE INDEX IF NOT EXISTS {index_name}" in sql or (
            f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name}" in sql
        )

    assert "CHECK (programme_status IN ('DRAFT', 'VALIDATION_FAILED', 'VALIDATED', 'READY_FOR_REVIEW', 'APPROVED_FOR_PUBLISH', 'BLOCKED', 'DISCARDED', 'ARCHIVED'))" in sql
    assert "CHECK (version_status IN ('PUBLISHED', 'ACTIVE', 'RETIRED', 'ROLLBACK_READY', 'ARCHIVED'))" in sql
    assert "CHECK (validation_status IN ('READY', 'NEEDS_ATTENTION', 'BLOCKED', 'FAILED'))" in sql
    assert "CHECK (response_status IN ('SUCCESS', 'REPLAY', 'CONFLICT', 'FAILED', 'BLOCKED'))" in sql
    assert "pg_constraint" in sql
    assert "referral_saas_programme_drafts_source_version_fk" in sql
    assert "referral_saas_programme_drafts_validation_result_fk" in sql
    assert "referral_saas_programme_versions_validation_result_fk" in sql


def test_schema_does_not_add_unsafe_programme_configuration_columns() -> None:
    for table_name in EXPECTED_TABLES:
        assert _column_names(table_name).isdisjoint(FORBIDDEN_COLUMN_NAMES)
