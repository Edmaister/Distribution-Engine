from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = (
    ROOT / "dp" / "migrations" / "098_referral_runtime_programme_version_binding.sql"
)


def _sql() -> str:
    return MIGRATION_PATH.read_text(encoding="utf-8")


def test_referral_runtime_programme_binding_adds_version_identity():
    sql = _sql()

    assert "ALTER TABLE referral_instances" in sql
    assert "ADD COLUMN IF NOT EXISTS programme_version_id UUID" in sql
    assert (
        "REFERENCES referral_saas_programme_versions(programme_version_id)" in sql
    )
    assert "ADD COLUMN IF NOT EXISTS programme_runtime_context JSONB" in sql
    assert "DEFAULT '{}'::jsonb" in sql


def test_referral_runtime_programme_binding_adds_lookup_indexes():
    sql = _sql()

    assert "CREATE INDEX IF NOT EXISTS idx_referral_instances_programme_version" in sql
    assert "ON referral_instances (tenant_code, programme_version_id)" in sql
    assert (
        "CREATE INDEX IF NOT EXISTS idx_referral_instances_programme_runtime_context"
        in sql
    )
    assert "ON referral_instances USING GIN (programme_runtime_context)" in sql
