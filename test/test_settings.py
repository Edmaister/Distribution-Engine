from __future__ import annotations

import pytest
from fastapi import HTTPException

import utils.security as mod


@pytest.fixture(autouse=True)
def reset_keys(monkeypatch):
    from apps.api.settings import get_settings

    settings = get_settings()

    # Only patch fields that ACTUALLY exist in Settings
    monkeypatch.setattr(settings, "admin_api_key", "admin-key")
    monkeypatch.setattr(settings, "finance_admin_api_key", "finance-key")
    monkeypatch.setattr(settings, "distribution_admin_api_key", "distribution-key")
    monkeypatch.setattr(settings, "system_admin_api_key", "system-key")
    monkeypatch.setattr(settings, "partner_api_key", "partner-key")
    monkeypatch.setattr(settings, "fnb_partner_api_key", "fnb-user-key")
    monkeypatch.setattr(settings, "pnp_partner_api_key", "pnp-user-key")
    monkeypatch.setattr(settings, "fnb_producer_api_key", "producer-key")
    monkeypatch.setattr(settings, "fnb_producer_code", "INSURECO")
    monkeypatch.setattr(settings, "fnb_distributor_api_key", "distributor-key")
    monkeypatch.setattr(settings, "fnb_distributor_code", "DIST-INSURANCE-ADVOCATE")
    monkeypatch.setattr(settings, "fnb_consumer_api_key", "consumer-key")


# -----------------------------
# BASIC HELPERS / ERRORS
# -----------------------------
def test_configured_keys_empty():
    assert mod._configured_keys(None) == []


def test_configured_keys_splits_and_strips():
    assert mod._configured_keys("one, two ,three") == ["one", "two", "three"]


def test_is_valid_key_true():
    assert mod._is_valid_key("two", "one,two,three") is True


def test_is_valid_key_false():
    assert mod._is_valid_key("bad", "one,two,three") is False


def test_unauthorized():
    with pytest.raises(HTTPException) as exc:
        mod._unauthorized()

    assert exc.value.status_code == 401


def test_server_config_error():
    with pytest.raises(HTTPException) as exc:
        mod._server_config_error("TEST")

    assert exc.value.status_code == 500


# -----------------------------
# ADMIN
# -----------------------------
def test_require_admin_success():
    result = mod.require_admin_key(x_api_key="admin-key")

    assert result["authenticated"] is True
    assert result["role"] == "ADMIN"
    assert result["tenant_code"] == "INTERNAL"


def test_require_admin_success_test_key():
    result = mod.require_admin_key(x_api_key="test-admin-key")

    assert result["authenticated"] is True
    assert result["role"] == "ADMIN"


def test_require_admin_test_key_rejected_in_prod(monkeypatch):
    from apps.api.settings import get_settings

    settings = get_settings()

    monkeypatch.setattr(settings, "app_env", "prod")

    with pytest.raises(HTTPException) as exc:
        mod.require_admin_key(x_api_key="test-admin-key")

    assert exc.value.status_code == 401


def test_require_admin_invalid():
    with pytest.raises(HTTPException) as exc:
        mod.require_admin_key(x_api_key="bad-key")

    assert exc.value.status_code == 401


def test_require_admin_missing_config(monkeypatch):
    from apps.api.settings import get_settings

    settings = get_settings()

    # Remove ALL admin keys (including test keys)
    monkeypatch.setattr(settings, "admin_api_key", None)
    monkeypatch.setattr(mod, "TEST_ADMIN_KEYS", "")

    with pytest.raises(HTTPException) as exc:
        mod.require_admin_key(x_api_key="anything")

    assert exc.value.status_code == 500


# -----------------------------
# SCOPED ADMIN
# -----------------------------
def test_require_finance_admin_success():
    result = mod.require_finance_admin_key(x_api_key="finance-key")

    assert result["authenticated"] is True
    assert result["role"] == "FINANCE_ADMIN"
    assert result["tenant_code"] == "INTERNAL"


def test_require_finance_admin_allows_platform_admin():
    result = mod.require_finance_admin_key(x_api_key="admin-key")

    assert result["role"] == "ADMIN"


def test_require_finance_admin_rejects_distribution_admin():
    with pytest.raises(HTTPException) as exc:
        mod.require_finance_admin_key(x_api_key="distribution-key")

    assert exc.value.status_code == 403


def test_require_distribution_admin_success():
    result = mod.require_distribution_admin_key(x_api_key="distribution-key")

    assert result["role"] == "DISTRIBUTION_ADMIN"


def test_require_distribution_admin_allows_test_key():
    result = mod.require_distribution_admin_key(x_api_key="test-distribution-admin-key")

    assert result["role"] == "DISTRIBUTION_ADMIN"


def test_require_distribution_admin_rejects_test_key_in_prod(monkeypatch):
    from apps.api.settings import get_settings

    settings = get_settings()

    monkeypatch.setattr(settings, "app_env", "prod")

    with pytest.raises(HTTPException) as exc:
        mod.require_distribution_admin_key(x_api_key="test-distribution-admin-key")

    assert exc.value.status_code == 401


def test_require_system_admin_success():
    result = mod.require_system_admin_key(x_api_key="system-key")

    assert result["role"] == "SYSTEM_ADMIN"


# -----------------------------
# PARTNER
# -----------------------------
def test_require_partner_fnb_partner_key():
    result = mod.require_partner_key(x_api_key="fnb-user-key")

    assert result["authenticated"] is True
    assert result["role"] == "PARTNER"
    assert result["tenant_code"] == "FNB"


def test_require_partner_pnp_partner_key():
    result = mod.require_partner_key(x_api_key="pnp-user-key")

    assert result["authenticated"] is True
    assert result["role"] == "PARTNER"
    assert result["tenant_code"] == "PNP"


def test_require_partner_test_key_maps_to_fnb():
    result = mod.require_partner_key(x_api_key="test-partner-key")

    assert result["role"] == "PARTNER"
    assert result["tenant_code"] == "FNB"


def test_require_partner_test_key_rejected_in_prod(monkeypatch):
    from apps.api.settings import get_settings

    settings = get_settings()

    monkeypatch.setattr(settings, "app_env", "prod")

    with pytest.raises(HTTPException) as exc:
        mod.require_partner_key(x_api_key="test-partner-key")

    assert exc.value.status_code == 401


def test_require_partner_invalid():
    with pytest.raises(HTTPException) as exc:
        mod.require_partner_key(x_api_key="bad-key")

    assert exc.value.status_code == 401


# -----------------------------
# ADMIN OR PARTNER
# -----------------------------
def test_admin_or_partner_admin():
    result = mod.require_admin_or_partner_key(x_api_key="admin-key")

    assert result["role"] == "ADMIN"
    assert result["tenant_code"] == "INTERNAL"


def test_admin_or_partner_test_admin():
    result = mod.require_admin_or_partner_key(x_api_key="test-admin-key")

    assert result["role"] == "ADMIN"


def test_admin_or_partner_fnb():
    result = mod.require_admin_or_partner_key(x_api_key="fnb-user-key")

    assert result["role"] == "PARTNER"
    assert result["tenant_code"] == "FNB"


def test_admin_or_partner_pnp():
    result = mod.require_admin_or_partner_key(x_api_key="pnp-user-key")

    assert result["role"] == "PARTNER"
    assert result["tenant_code"] == "PNP"


def test_admin_or_partner_invalid():
    with pytest.raises(HTTPException) as exc:
        mod.require_admin_or_partner_key(x_api_key="bad-key")

    assert exc.value.status_code == 401


# -----------------------------
# ROLE-SCOPED PROOF KEYS
# -----------------------------
def test_admin_partner_or_producer_key_maps_configured_key():
    result = mod.require_admin_partner_or_producer_key(x_api_key="producer-key")

    assert result["role"] == "PRODUCER"
    assert result["tenant_code"] == "FNB"
    assert result["producer_code"] == "INSURECO"


def test_admin_partner_or_producer_key_maps_local_test_key():
    result = mod.require_admin_partner_or_producer_key(
        x_api_key="test-fnb-producer-insureco-key"
    )

    assert result["role"] == "PRODUCER"
    assert result["tenant_code"] == "FNB"
    assert result["producer_code"] == "INSURECO"


def test_admin_partner_or_distributor_key_maps_configured_key():
    result = mod.require_admin_partner_or_distributor_key(x_api_key="distributor-key")

    assert result["role"] == "DISTRIBUTOR"
    assert result["tenant_code"] == "FNB"
    assert result["distributor_code"] == "DIST-INSURANCE-ADVOCATE"


def test_admin_partner_or_distributor_key_maps_local_test_key():
    result = mod.require_admin_partner_or_distributor_key(
        x_api_key="test-fnb-distributor-insurance-advocate-key"
    )

    assert result["role"] == "DISTRIBUTOR"
    assert result["tenant_code"] == "FNB"
    assert result["distributor_code"] == "DIST-INSURANCE-ADVOCATE"


def test_admin_partner_or_consumer_key_maps_configured_key():
    result = mod.require_admin_partner_or_consumer_key(x_api_key="consumer-key")

    assert result["role"] == "CONSUMER"
    assert result["tenant_code"] == "FNB"


def test_admin_partner_or_consumer_key_maps_local_test_key():
    result = mod.require_admin_partner_or_consumer_key(x_api_key="test-fnb-consumer-key")

    assert result["role"] == "CONSUMER"
    assert result["tenant_code"] == "FNB"


# -----------------------------
# ANY KEY
# -----------------------------
def test_require_any_key_admin():
    result = mod.require_any_key(x_api_key="admin-key")

    assert result["role"] == "ADMIN"


def test_require_any_key_partner_fnb():
    result = mod.require_any_key(x_api_key="fnb-user-key")

    assert result["role"] == "PARTNER"
    assert result["tenant_code"] == "FNB"


def test_require_any_key_partner_pnp():
    result = mod.require_any_key(x_api_key="pnp-user-key")

    assert result["role"] == "PARTNER"
    assert result["tenant_code"] == "PNP"


def test_require_any_key_invalid():
    with pytest.raises(HTTPException) as exc:
        mod.require_any_key(x_api_key="bad-key")

    assert exc.value.status_code == 401
