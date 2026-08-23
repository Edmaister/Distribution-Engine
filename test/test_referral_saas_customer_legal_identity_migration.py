from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = ROOT / "dp" / "migrations" / "104_referral_saas_customer_legal_identity.sql"


def test_customer_legal_identity_migration_is_bounded_and_backfills_existing_accounts():
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "ALTER TABLE platform_accounts" in sql
    assert "ALTER TABLE platform_organisations" in sql
    for column in (
        "legal_organisation_name",
        "trading_name",
        "registration_number",
    ):
        assert sql.count(f"ADD COLUMN IF NOT EXISTS {column} TEXT") == 2

    assert "SET legal_organisation_name = account_name" in sql
    assert "SET legal_organisation_name = organisation_name" in sql
    assert sql.count("ALTER COLUMN legal_organisation_name SET NOT NULL") == 2
    assert "idx_platform_accounts_registration_number" in sql