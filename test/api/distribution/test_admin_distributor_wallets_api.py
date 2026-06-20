from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.api.main import app


ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


pytestmark = pytest.mark.asyncio


def wallet_payload(wallet_id: str, distributor_id: str, **overrides):
    payload = {
        "wallet_id": wallet_id,
        "distributor_id": distributor_id,
        "tenant_code": "FNB",
        "distributor_code": "AGENCY_001",
        "currency": "ZAR",
        "current_balance": Decimal("1000.00"),
        "available_balance": Decimal("750.00"),
        "held_balance": Decimal("250.00"),
        "paid_out_balance": Decimal("0.00"),
        "reversed_balance": Decimal("0.00"),
        "status": "ACTIVE",
        "metadata": {"source": "test"},
        "created_at": "2026-06-12T10:00:00",
        "updated_at": "2026-06-12T10:00:00",
    }
    payload.update(overrides)
    return payload


async def test_create_distributor_wallet(monkeypatch):
    from apps.api.routers.distribution import admin_distributor_wallets

    wallet_id = str(uuid4())
    distributor_id = str(uuid4())
    calls = {}

    async def fake_create_distributor_wallet(**kwargs):
        calls.update(kwargs)
        return wallet_payload(
            wallet_id,
            kwargs["distributor_id"],
            current_balance=Decimal("0.00"),
            available_balance=Decimal("0.00"),
            held_balance=Decimal("0.00"),
        )

    monkeypatch.setattr(
        admin_distributor_wallets,
        "create_distributor_wallet",
        fake_create_distributor_wallet,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/distribution/distributor-wallets",
            json={
                "distributor_id": distributor_id,
                "currency": "ZAR",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["wallet_id"] == wallet_id
    assert body["current_balance"] == "0.00"
    assert calls == {
        "distributor_id": distributor_id,
        "currency": "ZAR",
        "metadata": {"source": "test"},
    }


async def test_list_distributor_wallets(monkeypatch):
    from apps.api.routers.distribution import admin_distributor_wallets

    wallet_id = str(uuid4())
    distributor_id = str(uuid4())
    calls = {}

    async def fake_list_distributor_wallets(**kwargs):
        calls.update(kwargs)
        return [wallet_payload(wallet_id, distributor_id)]

    monkeypatch.setattr(
        admin_distributor_wallets,
        "list_distributor_wallets",
        fake_list_distributor_wallets,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/distribution/distributor-wallets",
            params={
                "tenant_code": "FNB",
                "distributor_id": distributor_id,
                "status": "ACTIVE",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    assert response.json()[0]["wallet_id"] == wallet_id
    assert calls == {
        "tenant_code": "FNB",
        "distributor_id": distributor_id,
        "status": "ACTIVE",
        "limit": 25,
    }


@pytest.mark.parametrize(
    ("endpoint", "service_name", "expected_balance"),
    [
        ("credit", "credit_distributor_wallet", "1250.00"),
        ("hold", "hold_distributor_wallet_funds", "500.00"),
        ("release-hold", "release_distributor_wallet_hold", "1000.00"),
        ("payout", "payout_distributor_wallet", "750.00"),
        ("reverse", "reverse_distributor_wallet_earning", "750.00"),
    ],
)
async def test_wallet_movements(monkeypatch, endpoint, service_name, expected_balance):
    from apps.api.routers.distribution import admin_distributor_wallets

    wallet_id = str(uuid4())
    distributor_id = str(uuid4())
    calls = {}

    async def fake_movement(**kwargs):
        calls.update(kwargs)
        return wallet_payload(
            wallet_id,
            distributor_id,
            current_balance=Decimal(expected_balance),
        )

    monkeypatch.setattr(
        admin_distributor_wallets,
        service_name,
        fake_movement,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/distribution/distributor-wallets/{wallet_id}/{endpoint}",
            json={
                "amount": "250.00",
                "correlation_id": "wallet-corr-1",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    assert response.json()["current_balance"] == expected_balance
    assert calls == {
        "wallet_id": wallet_id,
        "amount": Decimal("250.00"),
        "correlation_id": "wallet-corr-1",
        "metadata": {"source": "test"},
    }


async def test_get_wallet_ledger(monkeypatch):
    from apps.api.routers.distribution import admin_distributor_wallets

    wallet_id = str(uuid4())
    distributor_id = str(uuid4())
    ledger_id = str(uuid4())

    async def fake_get_distributor_wallet(**kwargs):
        return wallet_payload(kwargs["wallet_id"], distributor_id)

    async def fake_list_distributor_wallet_ledger(**kwargs):
        return [
            {
                "ledger_id": ledger_id,
                "wallet_id": kwargs["wallet_id"],
                "distributor_id": distributor_id,
                "tenant_code": "FNB",
                "transaction_type": "CREDIT",
                "amount": Decimal("250.00"),
                "balance_before": Decimal("0.00"),
                "balance_after": Decimal("250.00"),
                "correlation_id": "wallet-corr-1",
                "metadata": {"source": "test"},
                "created_at": "2026-06-12T10:00:00",
            }
        ]

    monkeypatch.setattr(
        admin_distributor_wallets,
        "get_distributor_wallet",
        fake_get_distributor_wallet,
    )
    monkeypatch.setattr(
        admin_distributor_wallets,
        "list_distributor_wallet_ledger",
        fake_list_distributor_wallet_ledger,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/distribution/distributor-wallets/{wallet_id}/ledger",
            params={"limit": 25},
        )

    assert response.status_code == 200
    body = response.json()

    assert body[0]["ledger_id"] == ledger_id
    assert body[0]["transaction_type"] == "CREDIT"


async def test_missing_wallet_returns_404(monkeypatch):
    from apps.api.routers.distribution import admin_distributor_wallets

    async def fake_get_distributor_wallet(**kwargs):
        raise admin_distributor_wallets.DistributorWalletNotFound(
            "Distributor wallet not found"
        )

    monkeypatch.setattr(
        admin_distributor_wallets,
        "get_distributor_wallet",
        fake_get_distributor_wallet,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/distribution/distributor-wallets/{uuid4()}",
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Distributor wallet not found"}


async def test_insufficient_wallet_balance_returns_409(monkeypatch):
    from apps.api.routers.distribution import admin_distributor_wallets

    async def fake_hold_distributor_wallet_funds(**kwargs):
        raise admin_distributor_wallets.DistributorWalletInsufficientBalance(
            "Insufficient available wallet balance"
        )

    monkeypatch.setattr(
        admin_distributor_wallets,
        "hold_distributor_wallet_funds",
        fake_hold_distributor_wallet_funds,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/distribution/distributor-wallets/{uuid4()}/hold",
            json={"amount": "250.00"},
        )

    assert response.status_code == 409
    assert response.json() == {"detail": "Insufficient available wallet balance"}
