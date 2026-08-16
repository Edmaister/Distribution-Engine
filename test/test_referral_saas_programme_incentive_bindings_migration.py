from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "dp" / "migrations"
MIGRATION_NAME = "097_referral_saas_programme_incentive_bindings.sql"
MIGRATION_PATH = MIGRATION_DIR / MIGRATION_NAME

EXPECTED_COLUMNS = {
    "programme_incentive_binding_id",
    "account_id",
    "programme_version_id",
    "binding_type",
    "catalogue_type",
    "catalogue_ref",
    "catalogue_version_ref",
    "effective_from",
    "effective_to",
    "binding_status",
    "binding_payload_hash",
    "idempotency_key_hash",
    "correlation_id",
    "bound_by_ref",
    "bound_at",
    "archived_by_ref",
    "archived_at",
    "safe_summary",
    "governance_metadata",
}


def _sql() -> str:
    return MIGRATION_PATH.read_text(encoding="utf-8")


def _table_block() -> str:
    sql = _sql()
    match = re.search(
        r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+referral_saas_programme_incentive_bindings\s*\(",
        sql,
        flags=re.IGNORECASE,
    )
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
    raise AssertionError("Could not find programme incentive binding table block")


def _column_names() -> set[str]:
    columns: set[str] = set()
    for line in _table_block().splitlines():
        stripped = line.strip().rstrip(",")
        if not stripped or stripped.upper().startswith("CONSTRAINT"):
            continue
        column_name = stripped.split(maxsplit=1)[0]
        if re.fullmatch(r"[a-z_][a-z0-9_]*", column_name):
            columns.add(column_name)
    return columns


def test_programme_incentive_binding_migration_is_ordered_after_programme_foundation() -> None:
    migration_names = sorted(
        path.name
        for path in MIGRATION_DIR.glob("*.sql")
        if path.name.split("_", 1)[0].isdigit()
    )

    assert MIGRATION_NAME in migration_names
    assert migration_names.index("096_referral_saas_programme_configuration.sql") < (
        migration_names.index(MIGRATION_NAME)
    )
    assert migration_names.index(MIGRATION_NAME) < migration_names.index("999_indexes.sql")


def test_programme_incentive_binding_table_is_account_and_programme_scoped() -> None:
    block = _table_block()

    assert _column_names() == EXPECTED_COLUMNS
    assert "account_id UUID NOT NULL REFERENCES platform_accounts(account_id)" in block
    assert (
        "programme_version_id UUID NOT NULL\n"
        "        REFERENCES referral_saas_programme_versions(programme_version_id)"
    ) in block
    assert "binding_type IN ('INCENTIVE', 'ENGAGEMENT')" in block
    assert "catalogue_type IN ('REWARD_POLICY', 'MISSION', 'BADGE', 'LEADERBOARD')" in block
    assert "effective_from DATE NOT NULL" in block
    assert "CHECK (effective_to IS NULL OR effective_to > effective_from)" in block


def test_programme_incentive_binding_indexes_and_money_guardrails_are_present() -> None:
    sql = _sql()

    assert "idx_referral_saas_programme_incentive_active" in sql
    assert "idx_referral_saas_programme_incentive_version" in sql
    assert "WHERE binding_status = 'ACTIVE'" in sql
    assert "does not apply rewards" in sql
    assert "pay out" in sql
    assert "move money" in sql
    assert "wallet" not in _table_block().lower()
    assert "payout" not in _table_block().lower()
    assert "settlement" not in _table_block().lower()
