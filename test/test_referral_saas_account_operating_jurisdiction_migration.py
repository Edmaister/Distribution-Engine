from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = (
    ROOT / "dp" / "migrations" / "083_referral_saas_account_operating_jurisdiction.sql"
)


def _sql() -> str:
    return MIGRATION_PATH.read_text(encoding="utf-8")


def test_operating_jurisdiction_migration_is_additive() -> None:
    sql = _sql()
    sql_upper = sql.upper()

    assert "ALTER TABLE platform_accounts" in sql
    assert "ADD COLUMN IF NOT EXISTS operating_jurisdiction_code" in sql
    assert "DEFAULT 'ZA'" in sql
    assert "DROP " not in sql_upper
    assert "DELETE FROM" not in sql_upper
    assert "TRUNCATE" not in sql_upper


def test_operating_jurisdiction_codes_are_bounded_and_indexed() -> None:
    sql = _sql()

    assert "platform_accounts_operating_jurisdiction_chk" in sql
    for code in ("'ZA'", "'BW'", "'NA'", "'ZM'", "'OTHER'"):
        assert code in sql
    assert "idx_platform_accounts_operating_jurisdiction" in sql
    assert "ON platform_accounts (operating_jurisdiction_code, status)" in sql
