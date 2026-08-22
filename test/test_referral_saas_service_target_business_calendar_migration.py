from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "dp" / "migrations"
MIGRATION_NAME = "102_referral_saas_service_target_business_calendars.sql"
MIGRATION_PATH = MIGRATION_DIR / MIGRATION_NAME

EXPECTED_TABLES = {
    "referral_saas_service_target_calendar_versions",
    "referral_saas_service_target_calendar_weekly_intervals",
    "referral_saas_service_target_calendar_date_exceptions",
    "referral_saas_service_target_calendar_audit",
}


def _sql() -> str:
    return MIGRATION_PATH.read_text(encoding="utf-8")


def _table_block(table_name: str) -> str:
    sql = _sql()
    match = re.search(
        rf"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+{table_name}\s*\(",
        sql,
        flags=re.IGNORECASE,
    )
    assert match is not None
    start = sql.index("(", match.end() - 1)
    depth = 0
    for index in range(start, len(sql)):
        if sql[index] == "(":
            depth += 1
        elif sql[index] == ")":
            depth -= 1
            if depth == 0:
                return sql[start + 1 : index]
    raise AssertionError(f"Could not find table block for {table_name}")


def test_business_calendar_migration_is_ordered_after_service_targets() -> None:
    names = sorted(
        path.name
        for path in MIGRATION_DIR.glob("*.sql")
        if path.name.split("_", 1)[0].isdigit()
    )
    assert names.index("101_referral_saas_operational_service_targets.sql") < names.index(
        MIGRATION_NAME
    ) < names.index("999_indexes.sql")


def test_business_calendar_schema_has_all_bounded_evidence_tables() -> None:
    sql = _sql()
    for table_name in EXPECTED_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" in sql


def test_calendar_versions_are_scoped_versioned_and_governed() -> None:
    block = _table_block("referral_saas_service_target_calendar_versions")
    for field in (
        "calendar_code TEXT NOT NULL",
        "version_number INTEGER NOT NULL",
        "scope_type TEXT NOT NULL",
        "account_id UUID REFERENCES platform_accounts(account_id)",
        "business_timezone TEXT NOT NULL",
        "lifecycle_status TEXT NOT NULL",
        "effective_from TIMESTAMPTZ NOT NULL",
        "effective_to TIMESTAMPTZ",
        "created_by_ref TEXT NOT NULL",
        "reviewed_by_ref TEXT",
        "approved_by_ref TEXT",
        "idempotency_key_hash TEXT NOT NULL",
        "request_payload_hash TEXT NOT NULL",
        "redactions JSONB NOT NULL",
    ):
        assert field in block
    assert "scope_type = 'GLOBAL' AND account_id IS NULL" in block
    assert "scope_type = 'ACCOUNT' AND account_id IS NOT NULL" in block
    assert "'DRAFT', 'IN_REVIEW', 'APPROVED', 'RETIRED'" in block


def test_weekly_intervals_are_local_day_bounded_and_non_overnight() -> None:
    block = _table_block("referral_saas_service_target_calendar_weekly_intervals")
    assert "local_day_of_week SMALLINT NOT NULL" in block
    assert "local_start_time TIME NOT NULL" in block
    assert "local_end_time TIME NOT NULL" in block
    assert "local_day_of_week BETWEEN 1 AND 7" in block
    assert "local_start_time < local_end_time" in block


def test_date_exceptions_distinguish_closures_from_working_intervals() -> None:
    block = _table_block("referral_saas_service_target_calendar_date_exceptions")
    assert "local_date DATE NOT NULL" in block
    assert "exception_type IN ('CLOSED', 'WORKING_INTERVAL')" in block
    assert "exception_type = 'CLOSED'" in block
    assert "local_start_time IS NULL" in block
    assert "exception_type = 'WORKING_INTERVAL'" in block
    assert "local_start_time < local_end_time" in block
    assert "idx_referral_saas_service_target_calendar_one_closure" in _sql()


def test_calendar_audit_is_actor_idempotency_and_redaction_bound() -> None:
    block = _table_block("referral_saas_service_target_calendar_audit")
    for field in (
        "actor_ref TEXT NOT NULL",
        "actor_role TEXT NOT NULL",
        "correlation_id TEXT NOT NULL",
        "idempotency_key_hash TEXT NOT NULL",
        "request_payload_hash TEXT NOT NULL",
        "evidence_summary JSONB NOT NULL",
        "redactions JSONB NOT NULL",
    ):
        assert field in block


def test_calendar_schema_is_inert_and_does_not_cross_product_boundaries() -> None:
    sql = _sql().lower()
    assert "insert into referral_saas_service_target_calendar" not in sql
    assert "alter table referral_saas_operational_service_target_clocks" not in sql
    assert "on delete cascade" not in sql
    for forbidden in (
        "provider_sla_metrics",
        "funding_",
        "settlement_",
        "wallet",
        "payout",
        "invoice",
        "commission",
        "money_amount",
    ):
        assert forbidden not in sql
