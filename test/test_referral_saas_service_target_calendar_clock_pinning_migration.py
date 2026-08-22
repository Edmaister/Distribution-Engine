from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "dp" / "migrations"
MIGRATION_NAME = "103_referral_saas_service_target_calendar_clock_pinning.sql"


def _sql() -> str:
    return (MIGRATION_DIR / MIGRATION_NAME).read_text(encoding="utf-8")


def test_clock_calendar_pinning_migration_is_ordered() -> None:
    names = sorted(
        path.name for path in MIGRATION_DIR.glob("*.sql")
        if path.name.split("_", 1)[0].isdigit()
    )
    assert names.index(
        "102_referral_saas_service_target_business_calendars.sql"
    ) < names.index(MIGRATION_NAME) < names.index("999_indexes.sql")


def test_clock_calendar_pin_is_immutable_evidence_complete_or_absent() -> None:
    sql = _sql()
    for field in (
        "service_target_calendar_version_id UUID",
        "calendar_code TEXT",
        "calendar_version_number INTEGER",
        "calendar_timezone TEXT",
    ):
        assert field in sql
    assert "REFERENCES referral_saas_service_target_calendar_versions" in sql
    assert "referral_saas_service_target_clock_calendar_pin_ck" in sql
    assert "calendar_version_number > 0" in sql
    assert "WHERE service_target_calendar_version_id IS NOT NULL" in sql


def test_clock_calendar_pin_does_not_cross_product_boundaries() -> None:
    sql = _sql().lower()
    for forbidden in (
        "funding_", "settlement_", "wallet", "payout", "invoice",
        "commission", "money_amount", "on delete cascade",
    ):
        assert forbidden not in sql
