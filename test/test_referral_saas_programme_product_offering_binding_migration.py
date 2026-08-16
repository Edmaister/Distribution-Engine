from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = (
    ROOT
    / "dp"
    / "migrations"
    / "100_referral_saas_programme_product_offering_binding.sql"
)


def _migration_sql() -> str:
    return MIGRATION_PATH.read_text(encoding="utf-8")


def test_programme_product_offering_binding_migration_exists() -> None:
    sql = _migration_sql()

    assert "TASK-409" in sql
    assert "referral_saas_programme_drafts" in sql
    assert "referral_saas_programme_versions" in sql


def test_programme_drafts_and_versions_gain_customer_product_binding_columns() -> None:
    sql = _migration_sql()

    assert "customer_product_line_id UUID" in sql
    assert "customer_product_offering_id UUID" in sql
    assert "referral_saas_programme_drafts_product_line_fk" in sql
    assert "referral_saas_programme_drafts_product_offering_fk" in sql
    assert "referral_saas_programme_versions_product_line_fk" in sql
    assert "referral_saas_programme_versions_product_offering_fk" in sql


def test_programme_product_binding_migration_preserves_package_fields() -> None:
    sql = _migration_sql()

    assert "product_code/sub_product_code columns remain Amplifi service packaging" in sql
    assert "idx_referral_saas_programme_drafts_product_offering" in sql
    assert "idx_referral_saas_programme_versions_product_offering" in sql
    assert "referral_saas_programme_drafts_product_binding_pair_ck" in sql
    assert "referral_saas_programme_versions_product_binding_pair_ck" in sql
