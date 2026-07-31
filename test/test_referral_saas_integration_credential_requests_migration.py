from __future__ import annotations

from pathlib import Path


MIGRATION = Path(
    "dp/migrations/088_referral_saas_integration_credential_requests.sql"
)


def test_referral_saas_integration_credential_requests_migration_contract():
    sql = MIGRATION.read_text(encoding="utf-8")
    normalised_sql = " ".join(sql.lower().split())

    assert "create table if not exists referral_saas_integration_credential_requests" in normalised_sql
    assert "integration_credential_request_id uuid primary key" in normalised_sql
    assert "account_id uuid not null references platform_accounts" in normalised_sql
    assert "integration_configuration_id uuid not null references referral_saas_integration_configurations" in normalised_sql
    assert "idempotency_key_hash text not null" in normalised_sql
    assert "request_payload_hash text not null" in normalised_sql
    assert "platform_account_audit_events" not in normalised_sql
    assert "idx_referral_saas_credential_requests_account" in normalised_sql
    assert "uq_referral_saas_credential_requests_idempotency" in normalised_sql


def test_referral_saas_integration_credential_requests_do_not_store_secret_material():
    sql = MIGRATION.read_text(encoding="utf-8").lower()

    forbidden_columns = [
        "api_key ",
        "api_secret",
        "access_token",
        "refresh_token",
        "client_secret",
        "private_key",
        "signing_secret",
        "webhook_secret",
        "credential_value",
        "raw_secret",
        "secret_value",
    ]
    for forbidden in forbidden_columns:
        assert forbidden not in sql

    assert "no_secret_or_credential_storage" in sql
    assert "no_vault_write" in sql
    assert "no_provider_call" in sql
    assert "no_credential_lifecycle_execution" in sql

