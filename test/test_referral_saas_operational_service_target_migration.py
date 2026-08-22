from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "dp" / "migrations"
MIGRATION_NAME = "101_referral_saas_operational_service_targets.sql"
MIGRATION_PATH = MIGRATION_DIR / MIGRATION_NAME

EXPECTED_TABLES = {
    "referral_saas_operational_service_target_policies",
    "referral_saas_operational_service_target_clocks",
    "referral_saas_operational_service_target_pause_events",
    "referral_saas_operational_service_target_audit",
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


def test_service_target_migration_is_ordered_before_index_rollup() -> None:
    names = sorted(
        path.name
        for path in MIGRATION_DIR.glob("*.sql")
        if path.name.split("_", 1)[0].isdigit()
    )
    assert names.index("100_referral_saas_programme_product_offering_binding.sql") < names.index(
        MIGRATION_NAME
    ) < names.index("999_indexes.sql")


def test_service_target_foundation_has_all_governed_evidence_tables() -> None:
    sql = _sql()
    for table_name in EXPECTED_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" in sql


def test_policy_is_effective_dated_versioned_and_not_seeded() -> None:
    block = _table_block("referral_saas_operational_service_target_policies")
    for field in (
        "policy_code TEXT NOT NULL",
        "version_number INTEGER NOT NULL",
        "operating_jurisdiction_code TEXT NOT NULL",
        "work_type TEXT NOT NULL",
        "work_category TEXT NOT NULL",
        "priority TEXT NOT NULL",
        "business_timezone TEXT NOT NULL",
        "target_duration_minutes INTEGER NOT NULL",
        "warning_threshold_minutes INTEGER NOT NULL",
        "business_calendar_ref TEXT",
        "approved_pause_reasons JSONB",
        "effective_from TIMESTAMPTZ NOT NULL",
        "effective_to TIMESTAMPTZ",
        "approved_by_ref TEXT",
    ):
        assert field in block
    assert "INSERT INTO referral_saas_operational_service_target_policies" not in _sql()


def test_resolved_clock_preserves_policy_version_and_server_times() -> None:
    block = _table_block("referral_saas_operational_service_target_clocks")
    assert "support_case_id UUID NOT NULL UNIQUE" in block
    assert "REFERENCES referral_saas_support_cases(support_case_id)" in block
    assert "service_target_policy_id UUID NOT NULL" in block
    assert "policy_version_number INTEGER NOT NULL" in block
    for field in (
        "started_at TIMESTAMPTZ NOT NULL",
        "warning_at TIMESTAMPTZ NOT NULL",
        "due_at TIMESTAMPTZ NOT NULL",
        "accumulated_paused_seconds BIGINT NOT NULL",
        "completed_at TIMESTAMPTZ",
        "breached_at TIMESTAMPTZ",
    ):
        assert field in block


def test_pause_and_audit_evidence_are_actor_and_idempotency_bound() -> None:
    pause = _table_block("referral_saas_operational_service_target_pause_events")
    audit = _table_block("referral_saas_operational_service_target_audit")
    for block in (pause, audit):
        assert "actor_ref TEXT NOT NULL" in block
        assert "actor_role TEXT NOT NULL" in block
        assert "correlation_id TEXT NOT NULL" in block
        assert "idempotency_key_hash TEXT NOT NULL" in block
        assert "request_payload_hash TEXT NOT NULL" in block
        assert "redactions JSONB NOT NULL" in block
    assert "event_type IN ('PAUSED', 'RESUMED')" in pause


def test_service_target_schema_does_not_cross_product_or_money_boundaries() -> None:
    sql = _sql().lower()
    assert "provider_sla_metrics" not in sql
    for forbidden in (
        "funding_",
        "settlement_",
        "wallet",
        "payout",
        "invoice",
        "commission",
        "money_amount",
    ):
        assert forbidden not in sql
