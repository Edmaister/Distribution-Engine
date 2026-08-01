from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = (
    ROOT / "dp" / "migrations" / "089_referral_saas_support_case_lifecycle.sql"
)

EXPECTED_NOTE_COLUMNS = {
    "support_case_note_id",
    "support_case_id",
    "account_id",
    "note_type",
    "note_text",
    "reason_code",
    "correlation_id",
    "idempotency_key_hash",
    "request_payload_hash",
    "created_by_ref",
    "created_by_role",
    "metadata",
    "redactions",
    "created_at",
    "archived_at",
}

EXPECTED_STATUS_EVENT_COLUMNS = {
    "support_case_status_event_id",
    "support_case_id",
    "account_id",
    "from_status",
    "to_status",
    "transition_reason",
    "reason_code",
    "correlation_id",
    "idempotency_key_hash",
    "request_payload_hash",
    "changed_by_ref",
    "changed_by_role",
    "metadata",
    "redactions",
    "created_at",
    "archived_at",
}

EXPECTED_INDEXES = {
    "idx_referral_saas_support_case_notes_idem",
    "idx_referral_saas_support_case_notes_case",
    "idx_referral_saas_support_case_notes_account",
    "idx_referral_saas_support_case_status_idem",
    "idx_referral_saas_support_case_status_case",
    "idx_referral_saas_support_case_status_account",
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


def test_support_case_lifecycle_migration_adds_notes_and_status_events() -> None:
    assert (
        _column_names("referral_saas_support_case_notes") == EXPECTED_NOTE_COLUMNS
    )
    assert (
        _column_names("referral_saas_support_case_status_events")
        == EXPECTED_STATUS_EVENT_COLUMNS
    )


def test_support_case_lifecycle_migration_bounds_statuses_and_note_types() -> None:
    sql = _sql()
    for value in (
        "OPERATOR_NOTE",
        "CUSTOMER_UPDATE",
        "EVIDENCE_SUMMARY",
        "RESOLUTION_NOTE",
        "OPEN",
        "INVESTIGATING",
        "WAITING",
        "RESOLVED",
        "CLOSED",
    ):
        assert value in sql


def test_support_case_lifecycle_migration_adds_idempotency_indexes() -> None:
    sql = _sql()
    for index_name in EXPECTED_INDEXES:
        assert index_name in sql
    assert "support_case_id, idempotency_key_hash" in sql


def test_support_case_lifecycle_migration_does_not_add_side_effect_columns() -> None:
    lowered_sql = _sql().lower()
    for token in FORBIDDEN_TOKENS:
        assert token not in lowered_sql
