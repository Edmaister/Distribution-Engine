from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = ROOT / "dp" / "migrations" / "086_referral_saas_support_cases.sql"

EXPECTED_SUPPORT_CASE_COLUMNS = {
    "support_case_id",
    "account_id",
    "account_tenant_id",
    "external_ref_id",
    "tenant_code",
    "category",
    "priority",
    "status",
    "title",
    "summary",
    "source_surface",
    "assignee_ref",
    "reason_code",
    "correlation_id",
    "idempotency_key_hash",
    "request_payload_hash",
    "created_by_ref",
    "created_by_role",
    "updated_by_ref",
    "metadata",
    "redactions",
    "created_at",
    "updated_at",
    "closed_at",
    "archived_at",
}

EXPECTED_EVIDENCE_COLUMNS = {
    "evidence_link_id",
    "support_case_id",
    "account_id",
    "evidence_type",
    "evidence_ref",
    "safe_status",
    "warning_code",
    "missing_evidence_code",
    "metadata",
    "redactions",
    "created_at",
}

EXPECTED_INDEXES = {
    "idx_referral_saas_support_cases_idem",
    "idx_referral_saas_support_cases_account",
    "idx_referral_saas_support_cases_tenant",
    "idx_referral_saas_support_cases_status",
    "idx_referral_saas_support_cases_correlation",
    "idx_referral_saas_support_case_evidence_case",
}

FORBIDDEN_TOKENS = (
    "repair_command",
    "replay_command",
    "retry_command",
    "campaign_activation",
    "invite_delivery",
    "credential_creation",
    "auth_claim",
    "billing_event",
    "money_movement",
    "wallet",
    "payout",
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


def test_support_case_migration_creates_safe_case_tables() -> None:
    assert _column_names("referral_saas_support_cases") == EXPECTED_SUPPORT_CASE_COLUMNS
    assert (
        _column_names("referral_saas_support_case_evidence_links")
        == EXPECTED_EVIDENCE_COLUMNS
    )


def test_support_case_migration_keeps_status_and_category_bounded() -> None:
    sql = _sql()
    for value in (
        "VALIDATION_RECOVERY",
        "PROGRESS_DIAGNOSTIC",
        "ATTRIBUTION_REVIEW",
        "READINESS_BLOCKER",
        "REPORTING_FRESHNESS",
        "INTEGRATION_HEALTH",
        "ACCESS_SCOPE",
        "MANUAL_REVIEW_REQUIRED",
        "OPEN",
        "INVESTIGATING",
        "WAITING",
        "RESOLVED",
        "CLOSED",
    ):
        assert value in sql


def test_support_case_migration_adds_idempotency_and_scope_indexes() -> None:
    sql = _sql()
    for index_name in EXPECTED_INDEXES:
        assert index_name in sql
    assert "account_id, idempotency_key_hash" in sql


def test_support_case_migration_does_not_add_repair_or_money_columns() -> None:
    lowered_sql = _sql().lower()
    for token in FORBIDDEN_TOKENS:
        assert token not in lowered_sql
