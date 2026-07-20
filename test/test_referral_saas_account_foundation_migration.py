from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "dp" / "migrations"
MIGRATION_NAME = "082_referral_saas_account_foundation.sql"
MIGRATION_PATH = MIGRATION_DIR / MIGRATION_NAME

EXPECTED_TABLES = {
    "platform_accounts": {
        "account_id",
        "account_code",
        "account_name",
        "account_type",
        "status",
        "onboarding_status",
        "primary_external_tenant_ref",
        "safe_summary",
        "metadata",
        "created_by_ref",
        "updated_by_ref",
        "created_at",
        "updated_at",
        "archived_at",
    },
    "platform_organisations": {
        "organisation_id",
        "account_id",
        "organisation_ref",
        "organisation_name",
        "organisation_type",
        "status",
        "safe_summary",
        "metadata",
        "created_at",
        "updated_at",
        "archived_at",
    },
    "platform_account_tenants": {
        "account_tenant_id",
        "account_id",
        "tenant_code",
        "relationship_type",
        "is_primary",
        "status",
        "safe_summary",
        "metadata",
        "created_at",
        "updated_at",
        "archived_at",
    },
    "platform_external_tenant_refs": {
        "external_ref_id",
        "account_id",
        "account_tenant_id",
        "tenant_code",
        "ref_type",
        "external_ref",
        "status",
        "source_system",
        "valid_from",
        "valid_until",
        "safe_summary",
        "metadata",
        "created_at",
        "updated_at",
        "rotated_at",
        "archived_at",
    },
    "platform_users": {
        "user_id",
        "subject",
        "email_hash",
        "display_name",
        "status",
        "metadata",
        "created_at",
        "updated_at",
        "last_seen_at",
        "archived_at",
    },
    "platform_memberships": {
        "membership_id",
        "account_id",
        "tenant_code",
        "user_id",
        "client_id",
        "role_family",
        "permission_set",
        "status",
        "seat_id",
        "invited_by_ref",
        "accepted_by_ref",
        "disabled_by_ref",
        "metadata",
        "created_at",
        "updated_at",
        "invited_at",
        "accepted_at",
        "disabled_at",
        "archived_at",
    },
    "platform_seats": {
        "seat_id",
        "account_id",
        "seat_type",
        "status",
        "assigned_membership_id",
        "metadata",
        "created_at",
        "updated_at",
        "archived_at",
    },
    "platform_account_audit_events": {
        "account_audit_event_id",
        "account_id",
        "account_tenant_id",
        "external_ref_id",
        "membership_id",
        "tenant_code",
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
    "idx_platform_account_tenants_unique_active_link",
    "idx_platform_account_tenants_primary_owner",
    "idx_platform_account_tenants_primary_per_account",
    "idx_platform_external_tenant_refs_active_ref",
    "idx_platform_external_tenant_refs_scope",
    "idx_platform_external_tenant_refs_status",
    "idx_platform_organisations_active_ref",
    "idx_platform_organisations_account",
    "idx_platform_accounts_status",
    "idx_platform_accounts_primary_external_ref",
    "idx_platform_memberships_active_user_role",
    "idx_platform_memberships_active_client_role",
    "idx_platform_memberships_account_status",
    "idx_platform_memberships_tenant_status",
    "idx_platform_seats_assigned_membership",
    "idx_platform_seats_account_status",
    "idx_platform_account_audit_events_account",
    "idx_platform_account_audit_events_tenant",
    "idx_platform_account_audit_events_external_ref",
    "idx_platform_account_audit_events_membership",
    "idx_platform_account_audit_events_correlation",
}

FORBIDDEN_ACTION_TOKENS = (
    "campaign_activation",
    "go_live",
    "webhook_delivery",
    "wallet",
    "funding",
    "fulfilment",
    "settlement",
    "commission",
    "invoice",
    "payout",
    "reward_application",
    "repair",
    "replay",
    "retry",
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


def test_account_foundation_migration_is_ordered_after_onboarding_drafts() -> None:
    migration_names = sorted(
        path.name
        for path in MIGRATION_DIR.glob("*.sql")
        if path.name.split("_", 1)[0].isdigit()
    )

    assert MIGRATION_NAME in migration_names
    assert migration_names.index("081_funding_reconciliation_run_correlation.sql") < (
        migration_names.index(MIGRATION_NAME)
    )
    assert migration_names.index(MIGRATION_NAME) < migration_names.index(
        "083_referral_saas_account_operating_jurisdiction.sql"
    )
    assert migration_names.index("083_referral_saas_account_operating_jurisdiction.sql") < (
        migration_names.index("084_referral_saas_campaign_manager_role_family.sql")
    )


def test_account_foundation_tables_and_key_columns_are_declared() -> None:
    sql = _sql()

    for table_name, expected_columns in EXPECTED_TABLES.items():
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" in sql
        assert expected_columns <= _column_names(table_name)
        assert "PRIMARY KEY DEFAULT gen_random_uuid()" in _table_block(table_name)


def test_account_foundation_references_existing_tenant_partition() -> None:
    sql = _sql()

    assert "tenant_code TEXT NOT NULL REFERENCES tenants(tenant_code)" in sql
    assert "tenant_code TEXT REFERENCES tenants(tenant_code)" in sql
    assert "account_id UUID NOT NULL REFERENCES platform_accounts(account_id)" in sql
    assert "client_id TEXT REFERENCES partner_clients(client_id)" in sql


def test_account_foundation_lifecycle_constraints_are_declared() -> None:
    sql = _sql()

    for constraint_name in (
        "platform_accounts_status_chk",
        "platform_account_tenants_status_chk",
        "platform_external_tenant_refs_status_chk",
        "platform_memberships_status_chk",
        "platform_seats_status_chk",
    ):
        assert f"CONSTRAINT {constraint_name} CHECK" in sql

    for status in (
        "PENDING_ONBOARDING",
        "PENDING_SETUP",
        "ACTIVE",
        "SUSPENDED",
        "DISABLED",
        "ROTATED",
        "ARCHIVED",
    ):
        assert f"'{status}'" in sql


def test_account_foundation_membership_role_families_include_referral_saas_roles() -> None:
    sql = _sql()

    for role_family in (
        "DISTRIBUTION_ADMIN",
        "CAMPAIGN_MANAGER",
        "SUPPORT",
    ):
        assert f"'{role_family}'" in sql


def test_account_foundation_uniqueness_and_lookup_indexes_are_declared() -> None:
    sql = _sql()

    for index_name in EXPECTED_INDEXES:
        assert (
            f"CREATE INDEX IF NOT EXISTS {index_name}" in sql
            or f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name}" in sql
        )

    assert "ON platform_external_tenant_refs (ref_type, external_ref)" in sql
    assert "WHERE status = 'ACTIVE'" in sql
    assert "ON platform_account_tenants (tenant_code)" in sql
    assert "relationship_type = 'OWNER'" in sql


def test_account_foundation_is_additive_and_avoids_live_actions() -> None:
    sql_upper = _sql().upper()

    assert "DROP TABLE" not in sql_upper
    assert "DROP COLUMN" not in sql_upper
    assert "DELETE FROM" not in sql_upper
    assert "TRUNCATE" not in sql_upper
    assert "UPDATE " not in sql_upper
    assert "INSERT INTO" not in sql_upper

    all_columns = set().union(
        *(_column_names(table_name) for table_name in EXPECTED_TABLES)
    )
    for name in set(EXPECTED_TABLES) | all_columns:
        for forbidden_token in FORBIDDEN_ACTION_TOKENS:
            assert forbidden_token not in name


def test_onboarding_drafts_are_not_reused_as_account_tables() -> None:
    sql = _sql()

    assert "REFERENCES onboarding_drafts" not in sql
    assert "onboarding_draft_id" not in sql
