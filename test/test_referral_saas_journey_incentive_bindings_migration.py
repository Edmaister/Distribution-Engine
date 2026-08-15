from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = (
    ROOT / "dp" / "migrations" / "095_referral_saas_journey_incentive_bindings.sql"
)


def _sql() -> str:
    return MIGRATION_PATH.read_text(encoding="utf-8")


def test_customer_journey_incentive_binding_table_is_account_scoped() -> None:
    sql = _sql()

    assert "CREATE TABLE IF NOT EXISTS referral_saas_customer_journey_incentive_bindings" in sql
    assert "account_id UUID NOT NULL REFERENCES platform_accounts(account_id)" in sql
    assert (
        "customer_journey_version_id UUID NOT NULL\n"
        "        REFERENCES referral_saas_customer_journey_versions"
    ) in sql
    assert "tenant_code" not in sql.lower()


def test_customer_journey_incentive_binding_catalogue_controls_are_present() -> None:
    sql = _sql()

    assert "incentive_type TEXT NOT NULL" in sql
    assert "catalogue_ref TEXT NOT NULL" in sql
    assert "binding_payload_hash TEXT NOT NULL" in sql
    assert "safe_summary JSONB NOT NULL DEFAULT '{}'::jsonb" in sql
    assert "governance_metadata JSONB NOT NULL DEFAULT '{}'::jsonb" in sql
    assert (
        "CHECK (incentive_type IN ('REWARD_POLICY', 'MISSION', 'BADGE', 'LEADERBOARD'))"
        in sql
    )
    assert "CHECK (binding_status IN ('ACTIVE', 'ARCHIVED'))" in sql


def test_customer_journey_incentive_binding_active_uniqueness_is_present() -> None:
    sql = _sql()

    assert "idx_referral_saas_customer_journey_incentive_active" in sql
    assert "UPPER(catalogue_ref)" in sql
    assert "WHERE binding_status = 'ACTIVE'" in sql
    assert "idx_referral_saas_customer_journey_incentive_version" in sql
