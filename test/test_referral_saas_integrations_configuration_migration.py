from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = (
    ROOT / "dp" / "migrations" / "087_referral_saas_integrations_configuration.sql"
)

EXPECTED_COLUMNS = {
    "integration_configuration_id",
    "account_id",
    "account_tenant_id",
    "external_ref_id",
    "tenant_code",
    "configuration_status",
    "api_environment",
    "webhook_intent",
    "message_providers",
    "safe_setup_posture",
    "reason_code",
    "correlation_id",
    "idempotency_key_hash",
    "request_payload_hash",
    "created_by_ref",
    "created_by_role",
    "updated_by_ref",
    "redactions",
    "created_at",
    "updated_at",
    "archived_at",
}

EXPECTED_INDEXES = {
    "idx_referral_saas_integration_configurations_idem",
    "idx_referral_saas_integration_configurations_account",
    "idx_referral_saas_integration_configurations_tenant",
    "idx_referral_saas_integration_configurations_correlation",
}

FORBIDDEN_TOKENS = (
    "provider_secret",
    "signing_secret",
    "api_key",
    "raw_webhook_payload",
    "invite_delivery",
    "credential_creation",
    "auth_claim",
    "campaign_activation",
    "billing_event",
    "money_movement",
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


def _column_names(table_name: str) -> set[str]:
    block = _extract_parenthesized_block(
        _sql(),
        rf"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+{table_name}\s*\(",
    )
    columns: set[str] = set()
    for line in block.splitlines():
        stripped = line.strip().rstrip(",")
        if not stripped or stripped.upper().startswith("CONSTRAINT"):
            continue
        column_name = stripped.split(maxsplit=1)[0]
        if re.fullmatch(r"[a-z_][a-z0-9_]*", column_name):
            columns.add(column_name)
    return columns


def test_integrations_configuration_migration_creates_safe_runtime_table() -> None:
    assert (
        _column_names("referral_saas_integration_configurations")
        == EXPECTED_COLUMNS
    )


def test_integrations_configuration_migration_adds_scope_and_idempotency_indexes() -> None:
    sql = _sql()
    for index_name in EXPECTED_INDEXES:
        assert index_name in sql
    assert "account_id, idempotency_key_hash" in sql


def test_integrations_configuration_migration_does_not_store_live_secrets() -> None:
    lowered_sql = _sql().lower()
    for token in FORBIDDEN_TOKENS:
        assert token not in lowered_sql
