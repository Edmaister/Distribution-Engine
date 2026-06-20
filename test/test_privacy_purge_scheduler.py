from __future__ import annotations

import services.privacy_purge_scheduler as mod


def test_run_privacy_purge_success(monkeypatch):
    calls = []

    def fake_purge_expired_data(tenant_code: str):
        calls.append(tenant_code)
        return {
            "status": "purged",
            "tenant_code": tenant_code,
            "retention_days": 1825,
            "deleted_referral_instances": 0,
            "deleted_referrer_codes": 0,
        }

    monkeypatch.setattr(mod, "purge_expired_data", fake_purge_expired_data)

    result = mod.run_privacy_purge()

    assert result["status"] == "completed"
    assert calls == ["FNB", "DEFAULT"]
    assert len(result["results"]) == 2
    assert result["results"][0]["status"] == "purged"
    assert result["results"][0]["tenant_code"] == "FNB"
    assert result["results"][1]["tenant_code"] == "DEFAULT"


def test_run_privacy_purge_handles_failure(monkeypatch):
    def fake_purge_expired_data(tenant_code: str):
        if tenant_code == "FNB":
            raise RuntimeError("database unavailable")

        return {
            "status": "purged",
            "tenant_code": tenant_code,
            "retention_days": 1825,
            "deleted_referral_instances": 0,
            "deleted_referrer_codes": 0,
        }

    monkeypatch.setattr(mod, "purge_expired_data", fake_purge_expired_data)

    result = mod.run_privacy_purge()

    assert result["status"] == "completed"
    assert len(result["results"]) == 2

    assert result["results"][0]["status"] == "failed"
    assert result["results"][0]["tenant_code"] == "FNB"
    assert "database unavailable" in result["results"][0]["error"]

    assert result["results"][1]["status"] == "purged"
    assert result["results"][1]["tenant_code"] == "DEFAULT"


def test_run_privacy_purge_all_failures(monkeypatch):
    def fake_purge_expired_data(tenant_code: str):
        raise RuntimeError(f"{tenant_code} failed")

    monkeypatch.setattr(mod, "purge_expired_data", fake_purge_expired_data)

    result = mod.run_privacy_purge()

    assert result["status"] == "completed"
    assert len(result["results"]) == 2

    assert result["results"][0]["status"] == "failed"
    assert result["results"][0]["tenant_code"] == "FNB"
    assert "FNB failed" in result["results"][0]["error"]

    assert result["results"][1]["status"] == "failed"
    assert result["results"][1]["tenant_code"] == "DEFAULT"
    assert "DEFAULT failed" in result["results"][1]["error"]