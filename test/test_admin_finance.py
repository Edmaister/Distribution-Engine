from fastapi.testclient import TestClient

from apps.api.main import app
import apps.api.routers.admin_finance as finance_router


client = TestClient(app)
ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


def test_get_finance_reconciliation_metrics(monkeypatch):
    async def fake_get_reconciliation_metrics(**kwargs):
        return {
            "total_runs": 1,
            "total_records": 100,
            "matched_count": 95,
            "match_rate": 95.0,
        }

    monkeypatch.setattr(
        finance_router,
        "get_reconciliation_metrics",
        fake_get_reconciliation_metrics,
    )

    response = client.get(
        "/admin/finance/reconciliation/metrics",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["metrics"]["total_runs"] == 1
    assert payload["metrics"]["match_rate"] == 95.0


def test_get_finance_reconciliation_metrics_requires_admin_key():
    response = client.get("/admin/finance/reconciliation/metrics")

    assert response.status_code == 401


def test_get_finance_wallet_overview(monkeypatch):
    async def fake_get_network_wallet_overview(**kwargs):
        return {
            "tenant_code": kwargs["tenant_code"],
            "producer_wallets": {
                "wallet_count": 2,
                "available_balance": "1000.00",
                "reserved_balance": "250.00",
            },
            "distributor_wallets": {
                "wallet_count": 3,
                "available_balance": "400.00",
                "held_balance": "150.00",
            },
            "network": {
                "wallet_count": 5,
                "demand_liability": "550.00",
                "net_available_position": "450.00",
            },
        }

    monkeypatch.setattr(
        finance_router,
        "get_network_wallet_overview",
        fake_get_network_wallet_overview,
    )

    response = client.get(
        "/admin/finance/wallets/overview",
        params={"tenant_code": "FNB"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["overview"]["tenant_code"] == "FNB"
    assert payload["overview"]["network"]["wallet_count"] == 5


def test_get_finance_wallet_overview_requires_admin_key():
    response = client.get("/admin/finance/wallets/overview")

    assert response.status_code == 401


def test_get_finance_outcome_money_map(monkeypatch):
    async def fake_get_outcome_money_map(**kwargs):
        return {
            "tenant_code": kwargs["tenant_code"],
            "sponsor_code": kwargs["sponsor_code"],
            "distributor_code": kwargs["distributor_code"],
            "limit": kwargs["limit"],
            "summary": {
                "completed_outcome_count": 2,
                "ready_count": 1,
                "attention_count": 1,
                "money_completion_rate": "0.5000",
            },
            "journey": [],
            "items": [],
        }

    monkeypatch.setattr(
        finance_router,
        "get_outcome_money_map",
        fake_get_outcome_money_map,
    )

    response = client.get(
        "/admin/finance/outcome-money-map",
        params={
            "tenant_code": "FNB",
            "sponsor_code": "FNB",
            "distributor_code": "DIST-001",
            "limit": 25,
        },
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["outcome_money"]["tenant_code"] == "FNB"
    assert payload["outcome_money"]["sponsor_code"] == "FNB"
    assert payload["outcome_money"]["distributor_code"] == "DIST-001"
    assert payload["outcome_money"]["limit"] == 25
    assert payload["outcome_money"]["summary"]["ready_count"] == 1


def test_get_finance_outcome_money_map_requires_admin_key():
    response = client.get("/admin/finance/outcome-money-map")

    assert response.status_code == 401


def test_resolve_finance_outcome_settlement_exceptions(monkeypatch):
    captured = {}

    async def fake_resolve_outcome_settlement_exceptions(**kwargs):
        captured.update(kwargs)
        return {
            "referral_track_id": kwargs["referral_track_id"],
            "tenant_code": kwargs["tenant_code"],
            "resolved_count": 1,
            "items": [{"exception_id": "exception-1", "status": "RESOLVED"}],
        }

    monkeypatch.setattr(
        finance_router,
        "resolve_outcome_settlement_exceptions",
        fake_resolve_outcome_settlement_exceptions,
    )

    response = client.post(
        "/admin/finance/outcome-money-map/11111111-1111-1111-1111-111111111111/settlement-exceptions/resolve",
        json={"resolved_by": "ops-user", "tenant_code": "FNB"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["repair"]["resolved_count"] == 1
    assert captured == {
        "referral_track_id": "11111111-1111-1111-1111-111111111111",
        "resolved_by": "ops-user",
        "tenant_code": "FNB",
    }


def test_resolve_finance_outcome_settlement_exceptions_requires_admin_key():
    response = client.post(
        "/admin/finance/outcome-money-map/11111111-1111-1111-1111-111111111111/settlement-exceptions/resolve",
        json={"resolved_by": "ops-user", "tenant_code": "FNB"},
    )

    assert response.status_code == 401


def test_create_finance_outcome_invoice_evidence(monkeypatch):
    captured = {}

    async def fake_create_outcome_invoice_evidence(**kwargs):
        captured.update(kwargs)
        return {
            "referral_track_id": kwargs["referral_track_id"],
            "tenant_code": kwargs["tenant_code"],
            "invoice_id": "invoice-1",
            "line_count": 1,
            "invoice_amount": "100.00",
        }

    monkeypatch.setattr(
        finance_router,
        "create_outcome_invoice_evidence",
        fake_create_outcome_invoice_evidence,
    )

    response = client.post(
        "/admin/finance/outcome-money-map/11111111-1111-1111-1111-111111111111/invoice-evidence",
        json={"created_by": "ops-user", "tenant_code": "FNB"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["repair"]["line_count"] == 1
    assert captured == {
        "referral_track_id": "11111111-1111-1111-1111-111111111111",
        "created_by": "ops-user",
        "tenant_code": "FNB",
    }


def test_create_finance_outcome_reward_evidence(monkeypatch):
    captured = {}

    async def fake_create_outcome_reward_evidence(**kwargs):
        captured.update(kwargs)
        return {
            "referral_track_id": kwargs["referral_track_id"],
            "tenant_code": kwargs["tenant_code"],
            "reward_count": 1,
            "reward_amount": "100.00",
            "items": [{"reward_id": "reward-1"}],
        }

    monkeypatch.setattr(
        finance_router,
        "create_outcome_reward_evidence",
        fake_create_outcome_reward_evidence,
    )

    response = client.post(
        "/admin/finance/outcome-money-map/11111111-1111-1111-1111-111111111111/reward-evidence",
        json={"created_by": "ops-user", "tenant_code": "FNB"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["repair"]["reward_count"] == 1
    assert captured == {
        "referral_track_id": "11111111-1111-1111-1111-111111111111",
        "created_by": "ops-user",
        "tenant_code": "FNB",
    }


def test_create_finance_outcome_commission_evidence(monkeypatch):
    captured = {}

    async def fake_create_outcome_commission_evidence(**kwargs):
        captured.update(kwargs)
        return {
            "referral_track_id": kwargs["referral_track_id"],
            "tenant_code": kwargs["tenant_code"],
            "commission_count": 1,
            "commission_amount": "10.00",
            "items": [{"commission_event_id": "commission-1"}],
        }

    monkeypatch.setattr(
        finance_router,
        "create_outcome_commission_evidence",
        fake_create_outcome_commission_evidence,
    )

    response = client.post(
        "/admin/finance/outcome-money-map/11111111-1111-1111-1111-111111111111/commission-evidence",
        json={"created_by": "ops-user", "tenant_code": "FNB"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["repair"]["commission_count"] == 1
    assert captured == {
        "referral_track_id": "11111111-1111-1111-1111-111111111111",
        "created_by": "ops-user",
        "tenant_code": "FNB",
    }


def test_create_finance_outcome_wallet_evidence(monkeypatch):
    captured = {}

    async def fake_create_outcome_wallet_evidence(**kwargs):
        captured.update(kwargs)
        return {
            "referral_track_id": kwargs["referral_track_id"],
            "tenant_code": kwargs["tenant_code"],
            "wallet_movement_count": 1,
            "wallet_movement_amount": "10.00",
            "items": [{"ledger_id": "ledger-1"}],
        }

    monkeypatch.setattr(
        finance_router,
        "create_outcome_wallet_evidence",
        fake_create_outcome_wallet_evidence,
    )

    response = client.post(
        "/admin/finance/outcome-money-map/11111111-1111-1111-1111-111111111111/wallet-evidence",
        json={"created_by": "ops-user", "tenant_code": "FNB"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["repair"]["wallet_movement_count"] == 1
    assert captured == {
        "referral_track_id": "11111111-1111-1111-1111-111111111111",
        "created_by": "ops-user",
        "tenant_code": "FNB",
    }


def test_create_finance_outcome_invoice_evidence_requires_admin_key():
    response = client.post(
        "/admin/finance/outcome-money-map/11111111-1111-1111-1111-111111111111/invoice-evidence",
        json={"created_by": "ops-user", "tenant_code": "FNB"},
    )

    assert response.status_code == 401


def test_create_finance_outcome_reward_evidence_requires_admin_key():
    response = client.post(
        "/admin/finance/outcome-money-map/11111111-1111-1111-1111-111111111111/reward-evidence",
        json={"created_by": "ops-user", "tenant_code": "FNB"},
    )

    assert response.status_code == 401


def test_create_finance_outcome_commission_evidence_requires_admin_key():
    response = client.post(
        "/admin/finance/outcome-money-map/11111111-1111-1111-1111-111111111111/commission-evidence",
        json={"created_by": "ops-user", "tenant_code": "FNB"},
    )

    assert response.status_code == 401


def test_create_finance_outcome_wallet_evidence_requires_admin_key():
    response = client.post(
        "/admin/finance/outcome-money-map/11111111-1111-1111-1111-111111111111/wallet-evidence",
        json={"created_by": "ops-user", "tenant_code": "FNB"},
    )

    assert response.status_code == 401


def test_create_finance_outcome_settlement_evidence(monkeypatch):
    captured = {}

    async def fake_create_outcome_settlement_evidence(**kwargs):
        captured.update(kwargs)
        return {
            "referral_track_id": kwargs["referral_track_id"],
            "tenant_code": kwargs["tenant_code"],
            "settlement_count": 1,
            "settled_amount": "100.00",
            "items": [{"settlement_id": "settlement-1", "status": "SETTLED"}],
        }

    monkeypatch.setattr(
        finance_router,
        "create_outcome_settlement_evidence",
        fake_create_outcome_settlement_evidence,
    )

    response = client.post(
        "/admin/finance/outcome-money-map/11111111-1111-1111-1111-111111111111/settlement-evidence",
        json={"created_by": "ops-user", "tenant_code": "FNB"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["repair"]["settlement_count"] == 1
    assert captured == {
        "referral_track_id": "11111111-1111-1111-1111-111111111111",
        "created_by": "ops-user",
        "tenant_code": "FNB",
    }


def test_create_finance_outcome_settlement_evidence_requires_admin_key():
    response = client.post(
        "/admin/finance/outcome-money-map/11111111-1111-1111-1111-111111111111/settlement-evidence",
        json={"created_by": "ops-user", "tenant_code": "FNB"},
    )

    assert response.status_code == 401
