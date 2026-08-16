from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "dp" / "migrations"
MIGRATION_NAME = "099_referral_saas_customer_product_offering_catalogue.sql"
MIGRATION_PATH = MIGRATION_DIR / MIGRATION_NAME

EXPECTED_TABLES = {
    "referral_saas_customer_product_lines": {
        "customer_product_line_id",
        "account_id",
        "external_product_line_ref",
        "product_line_name",
        "product_line_category",
        "operating_jurisdiction_code",
        "lifecycle_status",
        "description",
        "safe_summary",
        "governance_metadata",
        "payload_hash",
        "idempotency_key_hash",
        "correlation_id",
        "created_by_ref",
        "updated_by_ref",
        "created_at",
        "updated_at",
        "archived_at",
    },
    "referral_saas_customer_product_offerings": {
        "customer_product_offering_id",
        "account_id",
        "customer_product_line_id",
        "external_offering_ref",
        "offering_name",
        "offering_family",
        "operating_jurisdiction_code",
        "lifecycle_status",
        "description",
        "safe_summary",
        "governance_metadata",
        "payload_hash",
        "idempotency_key_hash",
        "correlation_id",
        "created_by_ref",
        "updated_by_ref",
        "created_at",
        "updated_at",
        "archived_at",
    },
    "referral_saas_customer_product_catalogue_idempotency_keys": {
        "product_catalogue_idempotency_id",
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
    "referral_saas_customer_product_catalogue_audit": {
        "product_catalogue_audit_id",
        "account_id",
        "customer_product_line_id",
        "customer_product_offering_id",
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
    "idx_referral_saas_customer_product_lines_active_ref",
    "idx_referral_saas_customer_product_lines_account",
    "idx_referral_saas_customer_product_offerings_active_ref",
    "idx_referral_saas_customer_product_offerings_line",
    "idx_referral_saas_customer_product_catalogue_idempotency_unique",
    "idx_referral_saas_customer_product_catalogue_audit_account",
    "idx_referral_saas_customer_product_catalogue_audit_correlation",
}

FORBIDDEN_COLUMN_NAMES = {
    "tenant_code",
    "product_code",
    "sub_product_code",
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


def test_customer_product_catalogue_migration_is_ordered_after_programme_runtime_binding() -> None:
    migration_names = sorted(
        path.name
        for path in MIGRATION_DIR.glob("*.sql")
        if path.name.split("_", 1)[0].isdigit()
    )

    assert MIGRATION_NAME in migration_names
    assert migration_names.index("098_referral_runtime_programme_version_binding.sql") < (
        migration_names.index(MIGRATION_NAME)
    )
    assert migration_names.index(MIGRATION_NAME) < migration_names.index("999_indexes.sql")


def test_customer_product_catalogue_tables_are_present_with_expected_columns() -> None:
    for table_name, expected_columns in EXPECTED_TABLES.items():
        assert _column_names(table_name) == expected_columns


def test_customer_product_catalogue_is_account_scoped_and_jurisdiction_aware() -> None:
    for table_name in (
        "referral_saas_customer_product_lines",
        "referral_saas_customer_product_offerings",
        "referral_saas_customer_product_catalogue_audit",
    ):
        block = _table_block(table_name)
        assert "account_id UUID" in block
        assert "REFERENCES platform_accounts(account_id)" in block

    assert "operating_jurisdiction_code TEXT NOT NULL" in _table_block(
        "referral_saas_customer_product_lines"
    )
    assert "operating_jurisdiction_code TEXT NOT NULL" in _table_block(
        "referral_saas_customer_product_offerings"
    )


def test_customer_product_lines_store_customer_taxonomy_not_amplifi_packaging() -> None:
    block = _table_block("referral_saas_customer_product_lines")

    assert "external_product_line_ref TEXT NOT NULL" in block
    assert "product_line_name TEXT NOT NULL" in block
    assert "product_line_category TEXT NOT NULL" in block
    assert "safe_summary JSONB NOT NULL DEFAULT '{}'::jsonb" in block
    assert "governance_metadata JSONB NOT NULL DEFAULT '{}'::jsonb" in block
    assert "payload_hash TEXT NOT NULL" in block
    assert "created_by_ref TEXT NOT NULL" in block
    assert "product_code" not in _column_names("referral_saas_customer_product_lines")
    assert "sub_product_code" not in _column_names("referral_saas_customer_product_lines")


def test_customer_product_offerings_bind_to_lines_without_runtime_side_effects() -> None:
    block = _table_block("referral_saas_customer_product_offerings")

    assert "customer_product_line_id UUID NOT NULL" in block
    assert "REFERENCES referral_saas_customer_product_lines" in block
    assert "external_offering_ref TEXT NOT NULL" in block
    assert "offering_name TEXT NOT NULL" in block
    assert "payload_hash TEXT NOT NULL" in block
    assert "money" in _sql().lower()


def test_customer_product_catalogue_idempotency_audit_and_indexes_are_present() -> None:
    sql = _sql()
    idempotency_block = _table_block(
        "referral_saas_customer_product_catalogue_idempotency_keys"
    )
    audit_block = _table_block("referral_saas_customer_product_catalogue_audit")

    assert "idempotency_key_hash TEXT NOT NULL" in idempotency_block
    assert "request_payload_hash TEXT NOT NULL" in idempotency_block
    assert "response_payload_hash TEXT" in idempotency_block
    assert "evidence_summary JSONB NOT NULL DEFAULT '{}'::jsonb" in audit_block
    assert "redactions JSONB NOT NULL DEFAULT '[]'::jsonb" in audit_block
    assert "COALESCE(account_id, '00000000-0000-0000-0000-000000000000'::uuid)" in sql

    for index_name in EXPECTED_INDEXES:
        assert f"CREATE INDEX IF NOT EXISTS {index_name}" in sql or (
            f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name}" in sql
        )


def test_customer_product_catalogue_status_constraints_are_present() -> None:
    sql = _sql()

    assert "CHECK (lifecycle_status IN ('DRAFT', 'ACTIVE', 'SUSPENDED', 'RETIRED', 'ARCHIVED'))" in sql
    assert "CHECK (response_status IN ('SUCCESS', 'REPLAY', 'CONFLICT', 'FAILED', 'BLOCKED'))" in sql
    assert "CHECK (event_status IN ('RECORDED', 'DUPLICATE', 'DENIED', 'FAILED', 'BLOCKED'))" in sql


def test_schema_does_not_add_unsafe_customer_product_catalogue_columns() -> None:
    for table_name in EXPECTED_TABLES:
        assert _column_names(table_name).isdisjoint(FORBIDDEN_COLUMN_NAMES)
