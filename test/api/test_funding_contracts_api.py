from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.api.main import app

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


pytestmark = pytest.mark.asyncio


def unique_code(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


async def test_create_and_get_funding_contract():
    sponsor_code = unique_code("BOXER")

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        create_response = await client.post(
            "/admin/funding/contracts",
            json={
                "tenant_code": "FNB",
                "sponsor_code": sponsor_code,
                "sponsor_name": "Boxer",
                "contract_name": "FY27 Boxer Acquisition",
                "contract_value": "1000000.00",
                "start_date": "2026-01-01",
                "end_date": "2027-12-31",
                "currency": "ZAR",
                "metadata": {"source": "test"},
            },
        )

        assert create_response.status_code == 200
        body = create_response.json()

        assert body["status"] == "ok"
        contract = body["contract"]

        assert contract["tenant_code"] == "FNB"
        assert contract["sponsor_code"] == sponsor_code
        assert contract["contract_value"] == "1000000.00"
        assert contract["remaining_amount"] == "1000000.00"
        assert contract["committed_amount"] == "0.00"
        assert contract["utilised_amount"] == "0.00"

        contract_id = contract["contract_id"]

        get_response = await client.get(
            f"/admin/funding/contracts/{contract_id}",
        )

        assert get_response.status_code == 200
        fetched = get_response.json()["contract"]

        assert fetched["contract_id"] == contract_id
        assert fetched["sponsor_code"] == sponsor_code


async def test_list_funding_contracts():
    sponsor_code = unique_code("MTN")

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        await client.post(
            "/admin/funding/contracts",
            json={
                "tenant_code": "FNB",
                "sponsor_code": sponsor_code,
                "sponsor_name": "MTN",
                "contract_name": "MTN Airtime Rewards",
                "contract_value": "500000.00",
                "start_date": "2026-01-01",
                "end_date": "2027-12-31",
            },
        )

        response = await client.get(
            "/admin/funding/contracts",
            params={
                "tenant_code": "FNB",
                "sponsor_code": sponsor_code,
            },
        )

        assert response.status_code == 200
        body = response.json()

        assert body["status"] == "ok"
        assert body["tenant_code"] == "FNB"
        assert body["count"] >= 1
        assert any(
            item["sponsor_code"] == sponsor_code
            for item in body["items"]
        )


async def test_get_active_contract():
    sponsor_code = unique_code("TOYOTA")

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        await client.post(
            "/admin/funding/contracts",
            json={
                "tenant_code": "FNB",
                "sponsor_code": sponsor_code,
                "sponsor_name": "Toyota",
                "contract_name": "Toyota Vehicle Rewards",
                "contract_value": "750000.00",
                "start_date": "2026-01-01",
                "end_date": "2027-12-31",
            },
        )

        response = await client.get(
            "/admin/funding/contracts/active",
            params={
                "tenant_code": "FNB",
                "sponsor_code": sponsor_code,
                "as_of_date": "2026-06-01",
            },
        )

        assert response.status_code == 200
        body = response.json()

        assert body["status"] == "ok"
        assert body["contract"]["sponsor_code"] == sponsor_code
        assert body["contract"]["status"] == "ACTIVE"


async def test_commit_release_and_utilise_contract_budget():
    sponsor_code = unique_code("BOXER")

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        create_response = await client.post(
            "/admin/funding/contracts",
            json={
                "tenant_code": "FNB",
                "sponsor_code": sponsor_code,
                "sponsor_name": "Boxer",
                "contract_name": "Boxer Rewards",
                "contract_value": "1000.00",
                "start_date": "2026-01-01",
                "end_date": "2027-12-31",
            },
        )

        contract_id = create_response.json()["contract"]["contract_id"]

        commit_response = await client.post(
            f"/admin/funding/contracts/{contract_id}/commit",
            json={
                "amount": "300.00",
                "reward_id": str(uuid4()),
                "allocation_id": str(uuid4()),
                "correlation_id": "corr-contract-commit",
                "metadata": {"step": "commit"},
            },
        )

        assert commit_response.status_code == 200
        committed = commit_response.json()["contract"]

        assert committed["committed_amount"] == "300.00"
        assert committed["remaining_amount"] == "700.00"

        release_response = await client.post(
            f"/admin/funding/contracts/{contract_id}/release",
            json={
                "amount": "100.00",
                "correlation_id": "corr-contract-release",
            },
        )

        assert release_response.status_code == 200
        released = release_response.json()["contract"]

        assert released["committed_amount"] == "200.00"
        assert released["remaining_amount"] == "800.00"

        utilise_response = await client.post(
            f"/admin/funding/contracts/{contract_id}/utilise",
            json={
                "amount": "200.00",
                "correlation_id": "corr-contract-utilise",
            },
        )

        assert utilise_response.status_code == 200
        utilised = utilise_response.json()["contract"]

        assert utilised["committed_amount"] == "0.00"
        assert utilised["utilised_amount"] == "200.00"
        assert utilised["remaining_amount"] == "800.00"


async def test_contract_budget_exceeded_returns_409():
    sponsor_code = unique_code("DISCOVERY")

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        create_response = await client.post(
            "/admin/funding/contracts",
            json={
                "tenant_code": "FNB",
                "sponsor_code": sponsor_code,
                "sponsor_name": "Discovery",
                "contract_name": "Discovery Health Rewards",
                "contract_value": "100.00",
                "start_date": "2026-01-01",
                "end_date": "2027-12-31",
            },
        )

        contract_id = create_response.json()["contract"]["contract_id"]

        response = await client.post(
            f"/admin/funding/contracts/{contract_id}/commit",
            json={
                "amount": "150.00",
            },
        )

        assert response.status_code == 409
        assert "insufficient" in response.json()["detail"].lower()


async def test_suspend_activate_and_cancel_contract():
    sponsor_code = unique_code("SHOPRITE")

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        create_response = await client.post(
            "/admin/funding/contracts",
            json={
                "tenant_code": "FNB",
                "sponsor_code": sponsor_code,
                "sponsor_name": "Shoprite",
                "contract_name": "Shoprite Grocery Rewards",
                "contract_value": "1000.00",
                "start_date": "2026-01-01",
                "end_date": "2027-12-31",
            },
        )

        contract_id = create_response.json()["contract"]["contract_id"]

        suspend_response = await client.post(
            f"/admin/funding/contracts/{contract_id}/suspend",
        )

        assert suspend_response.status_code == 200
        assert suspend_response.json()["contract"]["status"] == "SUSPENDED"

        activate_response = await client.post(
            f"/admin/funding/contracts/{contract_id}/activate",
        )

        assert activate_response.status_code == 200
        assert activate_response.json()["contract"]["status"] == "ACTIVE"

        cancel_response = await client.post(
            f"/admin/funding/contracts/{contract_id}/cancel",
        )

        assert cancel_response.status_code == 200
        assert cancel_response.json()["contract"]["status"] == "CANCELLED"


async def test_get_contract_ledger():
    sponsor_code = unique_code("VODACOM")

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        create_response = await client.post(
            "/admin/funding/contracts",
            json={
                "tenant_code": "FNB",
                "sponsor_code": sponsor_code,
                "sponsor_name": "Vodacom",
                "contract_name": "Vodacom Data Rewards",
                "contract_value": "1000.00",
                "start_date": "2026-01-01",
                "end_date": "2027-12-31",
            },
        )

        contract_id = create_response.json()["contract"]["contract_id"]

        await client.post(
            f"/admin/funding/contracts/{contract_id}/commit",
            json={
                "amount": "100.00",
                "correlation_id": "corr-ledger-test",
            },
        )

        ledger_response = await client.get(
            f"/admin/funding/contracts/{contract_id}/ledger",
        )

        assert ledger_response.status_code == 200
        body = ledger_response.json()

        assert body["status"] == "ok"
        assert body["contract_id"] == contract_id
        assert body["count"] >= 2

        event_types = {item["event_type"] for item in body["items"]}

        assert "CONTRACT_CREATED" in event_types
        assert "BUDGET_COMMITTED" in event_types

async def test_get_missing_contract_returns_404():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/funding/contracts/{uuid4()}",
        )

        assert response.status_code == 404


async def test_get_missing_active_contract_returns_404():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/funding/contracts/active",
            params={
                "tenant_code": "FNB",
                "sponsor_code": unique_code("MISSING"),
                "as_of_date": "2026-06-01",
            },
        )

        assert response.status_code == 404


async def test_commit_suspended_contract_returns_400():
    sponsor_code = unique_code("SUSPENDED")

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        create_response = await client.post(
            "/admin/funding/contracts",
            json={
                "tenant_code": "FNB",
                "sponsor_code": sponsor_code,
                "sponsor_name": "Suspended Sponsor",
                "contract_name": "Suspended Contract",
                "contract_value": "1000.00",
                "start_date": "2026-01-01",
                "end_date": "2027-12-31",
            },
        )

        contract_id = create_response.json()["contract"]["contract_id"]

        await client.post(f"/admin/funding/contracts/{contract_id}/suspend")

        response = await client.post(
            f"/admin/funding/contracts/{contract_id}/commit",
            json={"amount": "100.00"},
        )

        assert response.status_code == 400
        assert "not active" in response.json()["detail"].lower()


async def test_commit_expired_contract_returns_400():
    sponsor_code = unique_code("EXPIRED")

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        create_response = await client.post(
            "/admin/funding/contracts",
            json={
                "tenant_code": "FNB",
                "sponsor_code": sponsor_code,
                "sponsor_name": "Expired Sponsor",
                "contract_name": "Expired Contract",
                "contract_value": "1000.00",
                "start_date": "2020-01-01",
                "end_date": "2020-12-31",
            },
        )

        contract_id = create_response.json()["contract"]["contract_id"]

        response = await client.post(
            f"/admin/funding/contracts/{contract_id}/commit",
            json={"amount": "100.00"},
        )

        assert response.status_code == 400
        assert "outside valid date range" in response.json()["detail"].lower()


async def test_release_more_than_committed_returns_409():
    sponsor_code = unique_code("RELEASE")

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        create_response = await client.post(
            "/admin/funding/contracts",
            json={
                "tenant_code": "FNB",
                "sponsor_code": sponsor_code,
                "sponsor_name": "Release Sponsor",
                "contract_name": "Release Contract",
                "contract_value": "1000.00",
                "start_date": "2026-01-01",
                "end_date": "2027-12-31",
            },
        )

        contract_id = create_response.json()["contract"]["contract_id"]

        response = await client.post(
            f"/admin/funding/contracts/{contract_id}/release",
            json={"amount": "100.00"},
        )

        assert response.status_code == 409
        assert "insufficient committed" in response.json()["detail"].lower()


async def test_utilise_more_than_committed_returns_409():
    sponsor_code = unique_code("UTILISE")

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        create_response = await client.post(
            "/admin/funding/contracts",
            json={
                "tenant_code": "FNB",
                "sponsor_code": sponsor_code,
                "sponsor_name": "Utilise Sponsor",
                "contract_name": "Utilise Contract",
                "contract_value": "1000.00",
                "start_date": "2026-01-01",
                "end_date": "2027-12-31",
            },
        )

        contract_id = create_response.json()["contract"]["contract_id"]

        response = await client.post(
            f"/admin/funding/contracts/{contract_id}/utilise",
            json={"amount": "100.00"},
        )

        assert response.status_code == 409
        assert "insufficient committed" in response.json()["detail"].lower()


async def test_contract_ledger_missing_contract_returns_404():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/funding/contracts/{uuid4()}/ledger",
        )

        assert response.status_code == 404


async def test_status_change_missing_contracts_return_404():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        missing_id = str(uuid4())

        suspend_response = await client.post(
            f"/admin/funding/contracts/{missing_id}/suspend",
        )
        assert suspend_response.status_code == 404

        activate_response = await client.post(
            f"/admin/funding/contracts/{missing_id}/activate",
        )
        assert activate_response.status_code == 404

        cancel_response = await client.post(
            f"/admin/funding/contracts/{missing_id}/cancel",
        )
        assert cancel_response.status_code == 404


async def test_create_contract_validation_error_returns_422():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/contracts",
            json={
                "tenant_code": "FNB",
                "sponsor_code": unique_code("BAD"),
                "sponsor_name": "Bad Sponsor",
                "contract_name": "Bad Contract",
                "contract_value": "0.00",
                "start_date": "2026-01-01",
                "end_date": "2027-12-31",
            },
        )

        assert response.status_code == 422


async def test_budget_movement_validation_error_returns_422():
    sponsor_code = unique_code("BADMOVE")

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        create_response = await client.post(
            "/admin/funding/contracts",
            json={
                "tenant_code": "FNB",
                "sponsor_code": sponsor_code,
                "sponsor_name": "Bad Movement Sponsor",
                "contract_name": "Bad Movement Contract",
                "contract_value": "1000.00",
                "start_date": "2026-01-01",
                "end_date": "2027-12-31",
            },
        )

        contract_id = create_response.json()["contract"]["contract_id"]

        response = await client.post(
            f"/admin/funding/contracts/{contract_id}/commit",
            json={"amount": "0.00"},
        )

        assert response.status_code == 422

async def test_generic_funding_contract_error_returns_400(monkeypatch):
    from apps.api.routers import funding_contracts

    async def raise_generic_error(**kwargs):
        raise funding_contracts.FundingContractError("Generic contract error")

    monkeypatch.setattr(
        funding_contracts,
        "create_funding_contract",
        raise_generic_error,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/contracts",
            json={
                "tenant_code": "FNB",
                "sponsor_code": unique_code("GENERIC"),
                "sponsor_name": "Generic Sponsor",
                "contract_name": "Generic Contract",
                "contract_value": "1000.00",
                "start_date": "2026-01-01",
                "end_date": "2027-12-31",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Generic contract error"

async def test_unexpected_contract_error_returns_500(monkeypatch):
    from apps.api.routers import funding_contracts

    async def raise_unexpected_error(**kwargs):
        raise RuntimeError("Unexpected boom")

    monkeypatch.setattr(
        funding_contracts,
        "create_funding_contract",
        raise_unexpected_error,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/contracts",
            json={
                "tenant_code": "FNB",
                "sponsor_code": unique_code("UNEXPECTED"),
                "sponsor_name": "Unexpected Sponsor",
                "contract_name": "Unexpected Contract",
                "contract_value": "1000.00",
                "start_date": "2026-01-01",
                "end_date": "2027-12-31",
            },
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Unexpected funding contract error"
