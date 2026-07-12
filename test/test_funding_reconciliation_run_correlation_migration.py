from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "dp" / "migrations"
MIGRATION_NAME = "081_funding_reconciliation_run_correlation.sql"
MIGRATION_PATH = MIGRATION_DIR / MIGRATION_NAME


def _sql() -> str:
    return MIGRATION_PATH.read_text(encoding="utf-8")


def test_funding_reconciliation_correlation_migration_is_ordered() -> None:
    migration_names = sorted(
        path.name
        for path in MIGRATION_DIR.glob("*.sql")
        if path.name.split("_", 1)[0].isdigit()
    )

    assert MIGRATION_NAME in migration_names
    assert migration_names.index("080_onboarding_draft_persistence.sql") < (
        migration_names.index(MIGRATION_NAME)
    )
    assert migration_names.index(MIGRATION_NAME) < migration_names.index(
        "999_indexes.sql"
    )


def test_funding_reconciliation_runs_correlation_column_is_additive() -> None:
    sql = _sql()

    assert "ALTER TABLE IF EXISTS funding_reconciliation_runs" in sql
    assert "ADD COLUMN IF NOT EXISTS correlation_id TEXT" in sql
    assert "DROP COLUMN" not in sql.upper()
    assert "DROP TABLE" not in sql.upper()
    assert "DELETE FROM" not in sql.upper()
    assert "TRUNCATE" not in sql.upper()


def test_funding_reconciliation_runs_correlation_index_is_guarded() -> None:
    sql = _sql()

    assert (
        "CREATE INDEX IF NOT EXISTS idx_funding_reconciliation_runs_correlation"
        in sql
    )
    assert "ON funding_reconciliation_runs(correlation_id)" in sql
