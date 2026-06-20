from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.api.main import app


ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


pytestmark = pytest.mark.asyncio


async def test_create_budget_adjustment_request(monkeypatch):
    from apps.api.routers import admin_budget_governance

    request_id = str(uuid4())
    contract_id = str(uuid4())
    calls = {}

    async def fake_create_budget_adjustment_request(**kwargs):
        calls.update(kwargs)
        return {
            "request_id": request_id,
            "contract_id": kwargs["contract_id"],
            "requested_amount": kwargs["requested_amount"],
            "request_status": "PENDING",
        }

    monkeypatch.setattr(
        admin_budget_governance,
        "create_budget_adjustment_request",
        fake_create_budget_adjustment_request,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/budget-governance/requests",
            json={
                "contract_id": contract_id,
                "requested_amount": "500000.00",
                "reason": "Campaign expansion",
                "requested_by": "ops@example.com",
                "correlation_id": "budget-corr-1",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["item"]["request_id"] == request_id
    assert body["item"]["requested_amount"] == "500000.00"
    assert calls == {
        "contract_id": contract_id,
        "requested_amount": Decimal("500000.00"),
        "reason": "Campaign expansion",
        "requested_by": "ops@example.com",
        "correlation_id": "budget-corr-1",
        "metadata": {"source": "test"},
    }


async def test_list_budget_adjustment_requests(monkeypatch):
    from apps.api.routers import admin_budget_governance

    request_id = str(uuid4())
    calls = {}

    async def fake_list_budget_adjustment_requests(**kwargs):
        calls.update(kwargs)
        return [
            {
                "request_id": request_id,
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "request_status": "PENDING",
            }
        ]

    monkeypatch.setattr(
        admin_budget_governance,
        "list_budget_adjustment_requests",
        fake_list_budget_adjustment_requests,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/funding/budget-governance/requests",
            params={
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "request_status": "PENDING",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 1
    assert body["items"][0]["request_id"] == request_id
    assert calls == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "contract_id": None,
        "request_status": "PENDING",
        "limit": 25,
    }


async def test_approve_budget_adjustment_request(monkeypatch):
    from apps.api.routers import admin_budget_governance

    request_id = str(uuid4())
    contract_id = str(uuid4())
    calls = {}

    async def fake_approve_budget_adjustment_request(**kwargs):
        calls.update(kwargs)
        return {
            "request": {
                "request_id": kwargs["request_id"],
                "request_status": "APPROVED",
            },
            "contract": {
                "contract_id": contract_id,
                "contract_value": Decimal("1500000.00"),
                "remaining_amount": Decimal("1200000.00"),
            },
        }

    monkeypatch.setattr(
        admin_budget_governance,
        "approve_budget_adjustment_request",
        fake_approve_budget_adjustment_request,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/funding/budget-governance/requests/{request_id}/approve",
            json={
                "decided_by": "finance@example.com",
                "decision_reason": "Approved",
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["request"]["request_status"] == "APPROVED"
    assert body["contract"]["contract_value"] == "1500000.00"
    assert calls == {
        "request_id": request_id,
        "decided_by": "finance@example.com",
        "decision_reason": "Approved",
    }


async def test_reject_budget_adjustment_request(monkeypatch):
    from apps.api.routers import admin_budget_governance

    request_id = str(uuid4())

    async def fake_reject_budget_adjustment_request(**kwargs):
        return {
            "request_id": kwargs["request_id"],
            "request_status": "REJECTED",
            "decision_reason": kwargs["decision_reason"],
        }

    monkeypatch.setattr(
        admin_budget_governance,
        "reject_budget_adjustment_request",
        fake_reject_budget_adjustment_request,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/funding/budget-governance/requests/{request_id}/reject",
            json={
                "decided_by": "finance@example.com",
                "decision_reason": "Insufficient commercial case",
            },
        )

    assert response.status_code == 200
    assert response.json()["item"] == {
        "request_id": request_id,
        "request_status": "REJECTED",
        "decision_reason": "Insufficient commercial case",
    }


async def test_budget_adjustment_invalid_state_returns_409(monkeypatch):
    from apps.api.routers import admin_budget_governance

    async def fake_approve_budget_adjustment_request(**kwargs):
        raise admin_budget_governance.BudgetAdjustmentRequestInvalidState(
            "Budget adjustment request is not pending"
        )

    monkeypatch.setattr(
        admin_budget_governance,
        "approve_budget_adjustment_request",
        fake_approve_budget_adjustment_request,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/funding/budget-governance/requests/{uuid4()}/approve",
            json={},
        )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Budget adjustment request is not pending"
    }


async def test_budget_adjustment_missing_contract_returns_404(monkeypatch):
    from apps.api.routers import admin_budget_governance

    async def fake_create_budget_adjustment_request(**kwargs):
        raise admin_budget_governance.BudgetAdjustmentContractNotFound(
            "Funding contract not found"
        )

    monkeypatch.setattr(
        admin_budget_governance,
        "create_budget_adjustment_request",
        fake_create_budget_adjustment_request,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/budget-governance/requests",
            json={
                "contract_id": str(uuid4()),
                "requested_amount": "1000.00",
            },
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Funding contract not found"}


async def test_create_budget_transfer_request(monkeypatch):
    from apps.api.routers import admin_budget_governance

    request_id = str(uuid4())
    source_contract_id = str(uuid4())
    target_contract_id = str(uuid4())
    calls = {}

    async def fake_create_budget_transfer_request(**kwargs):
        calls.update(kwargs)
        return {
            "request_id": request_id,
            "source_contract_id": kwargs["source_contract_id"],
            "target_contract_id": kwargs["target_contract_id"],
            "requested_amount": kwargs["requested_amount"],
            "request_status": "PENDING",
        }

    monkeypatch.setattr(
        admin_budget_governance,
        "create_budget_transfer_request",
        fake_create_budget_transfer_request,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/budget-governance/transfer-requests",
            json={
                "source_contract_id": source_contract_id,
                "target_contract_id": target_contract_id,
                "requested_amount": "250000.00",
                "reason": "Move unused launch budget",
                "requested_by": "ops@example.com",
                "correlation_id": "transfer-corr-1",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["item"]["request_id"] == request_id
    assert body["item"]["requested_amount"] == "250000.00"
    assert calls == {
        "source_contract_id": source_contract_id,
        "target_contract_id": target_contract_id,
        "requested_amount": Decimal("250000.00"),
        "reason": "Move unused launch budget",
        "requested_by": "ops@example.com",
        "correlation_id": "transfer-corr-1",
        "metadata": {"source": "test"},
    }


async def test_list_budget_transfer_requests(monkeypatch):
    from apps.api.routers import admin_budget_governance

    request_id = str(uuid4())
    source_contract_id = str(uuid4())
    calls = {}

    async def fake_list_budget_transfer_requests(**kwargs):
        calls.update(kwargs)
        return [
            {
                "request_id": request_id,
                "tenant_code": "FNB",
                "source_contract_id": source_contract_id,
                "request_status": "PENDING",
            }
        ]

    monkeypatch.setattr(
        admin_budget_governance,
        "list_budget_transfer_requests",
        fake_list_budget_transfer_requests,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/funding/budget-governance/transfer-requests",
            params={
                "tenant_code": "FNB",
                "source_contract_id": source_contract_id,
                "request_status": "PENDING",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 1
    assert body["items"][0]["request_id"] == request_id
    assert calls == {
        "tenant_code": "FNB",
        "source_contract_id": source_contract_id,
        "target_contract_id": None,
        "request_status": "PENDING",
        "limit": 25,
    }


async def test_approve_budget_transfer_request(monkeypatch):
    from apps.api.routers import admin_budget_governance

    request_id = str(uuid4())
    source_contract_id = str(uuid4())
    target_contract_id = str(uuid4())
    calls = {}

    async def fake_approve_budget_transfer_request(**kwargs):
        calls.update(kwargs)
        return {
            "request": {
                "request_id": kwargs["request_id"],
                "request_status": "APPROVED",
            },
            "source_contract": {
                "contract_id": source_contract_id,
                "remaining_amount": Decimal("750000.00"),
            },
            "target_contract": {
                "contract_id": target_contract_id,
                "remaining_amount": Decimal("1250000.00"),
            },
        }

    monkeypatch.setattr(
        admin_budget_governance,
        "approve_budget_transfer_request",
        fake_approve_budget_transfer_request,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/funding/budget-governance/transfer-requests/{request_id}/approve",
            json={
                "decided_by": "finance@example.com",
                "decision_reason": "Approved",
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["request"]["request_status"] == "APPROVED"
    assert body["source_contract"]["remaining_amount"] == "750000.00"
    assert body["target_contract"]["remaining_amount"] == "1250000.00"
    assert calls == {
        "request_id": request_id,
        "decided_by": "finance@example.com",
        "decision_reason": "Approved",
    }


async def test_reject_budget_transfer_request(monkeypatch):
    from apps.api.routers import admin_budget_governance

    request_id = str(uuid4())

    async def fake_reject_budget_transfer_request(**kwargs):
        return {
            "request_id": kwargs["request_id"],
            "request_status": "REJECTED",
            "decision_reason": kwargs["decision_reason"],
        }

    monkeypatch.setattr(
        admin_budget_governance,
        "reject_budget_transfer_request",
        fake_reject_budget_transfer_request,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/funding/budget-governance/transfer-requests/{request_id}/reject",
            json={
                "decided_by": "finance@example.com",
                "decision_reason": "Keep budgets separate",
            },
        )

    assert response.status_code == 200
    assert response.json()["item"] == {
        "request_id": request_id,
        "request_status": "REJECTED",
        "decision_reason": "Keep budgets separate",
    }


async def test_budget_transfer_invalid_returns_400(monkeypatch):
    from apps.api.routers import admin_budget_governance

    async def fake_create_budget_transfer_request(**kwargs):
        raise admin_budget_governance.BudgetTransferInvalid(
            "Source and target contracts must differ"
        )

    monkeypatch.setattr(
        admin_budget_governance,
        "create_budget_transfer_request",
        fake_create_budget_transfer_request,
    )

    contract_id = str(uuid4())

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/budget-governance/transfer-requests",
            json={
                "source_contract_id": contract_id,
                "target_contract_id": contract_id,
                "requested_amount": "1000.00",
            },
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Source and target contracts must differ"
    }


async def test_budget_transfer_insufficient_budget_returns_409(monkeypatch):
    from apps.api.routers import admin_budget_governance

    async def fake_approve_budget_transfer_request(**kwargs):
        raise admin_budget_governance.BudgetTransferInsufficientBudget(
            "Source contract has insufficient remaining budget"
        )

    monkeypatch.setattr(
        admin_budget_governance,
        "approve_budget_transfer_request",
        fake_approve_budget_transfer_request,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/funding/budget-governance/transfer-requests/{uuid4()}/approve",
            json={},
        )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Source contract has insufficient remaining budget"
    }


async def test_create_budget_exception(monkeypatch):
    from apps.api.routers import admin_budget_governance

    exception_id = str(uuid4())
    contract_id = str(uuid4())
    calls = {}

    async def fake_create_budget_exception(**kwargs):
        calls.update(kwargs)
        return {
            "exception_id": exception_id,
            "contract_id": kwargs["contract_id"],
            "tenant_code": kwargs["tenant_code"],
            "exception_type": kwargs["exception_type"],
            "severity": kwargs["severity"],
            "amount": kwargs["amount"],
            "exception_status": "OPEN",
        }

    monkeypatch.setattr(
        admin_budget_governance,
        "create_budget_exception",
        fake_create_budget_exception,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/budget-governance/exceptions",
            json={
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "contract_id": contract_id,
                "exception_type": "BUDGET_OVERRUN",
                "severity": "CRITICAL",
                "exception_message": "Contract spend exceeded remaining budget",
                "amount": "1500.00",
                "detected_by": "forecast-check",
                "correlation_id": "exception-corr-1",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["item"]["exception_id"] == exception_id
    assert body["item"]["amount"] == "1500.00"
    assert calls == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "contract_id": contract_id,
        "exception_type": "BUDGET_OVERRUN",
        "severity": "CRITICAL",
        "exception_message": "Contract spend exceeded remaining budget",
        "amount": Decimal("1500.00"),
        "detected_by": "forecast-check",
        "correlation_id": "exception-corr-1",
        "metadata": {"source": "test"},
    }


async def test_list_budget_exceptions(monkeypatch):
    from apps.api.routers import admin_budget_governance

    exception_id = str(uuid4())
    calls = {}

    async def fake_list_budget_exceptions(**kwargs):
        calls.update(kwargs)
        return [
            {
                "exception_id": exception_id,
                "tenant_code": "FNB",
                "exception_type": "POLICY_BREACH",
                "exception_status": "OPEN",
            }
        ]

    monkeypatch.setattr(
        admin_budget_governance,
        "list_budget_exceptions",
        fake_list_budget_exceptions,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/funding/budget-governance/exceptions",
            params={
                "tenant_code": "FNB",
                "exception_status": "OPEN",
                "exception_type": "POLICY_BREACH",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 1
    assert body["items"][0]["exception_id"] == exception_id
    assert calls == {
        "tenant_code": "FNB",
        "sponsor_code": None,
        "contract_id": None,
        "exception_status": "OPEN",
        "exception_type": "POLICY_BREACH",
        "limit": 25,
    }


async def test_resolve_budget_exception(monkeypatch):
    from apps.api.routers import admin_budget_governance

    exception_id = str(uuid4())
    calls = {}

    async def fake_resolve_budget_exception(**kwargs):
        calls.update(kwargs)
        return {
            "exception_id": kwargs["exception_id"],
            "exception_status": "RESOLVED",
            "resolution_reason": kwargs["resolution_reason"],
        }

    monkeypatch.setattr(
        admin_budget_governance,
        "resolve_budget_exception",
        fake_resolve_budget_exception,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/funding/budget-governance/exceptions/{exception_id}/resolve",
            json={
                "resolved_by": "finance@example.com",
                "resolution_reason": "Budget increase approved",
            },
        )

    assert response.status_code == 200
    assert response.json()["item"] == {
        "exception_id": exception_id,
        "exception_status": "RESOLVED",
        "resolution_reason": "Budget increase approved",
    }
    assert calls == {
        "exception_id": exception_id,
        "resolved_by": "finance@example.com",
        "resolution_reason": "Budget increase approved",
    }


async def test_waive_budget_exception(monkeypatch):
    from apps.api.routers import admin_budget_governance

    exception_id = str(uuid4())

    async def fake_waive_budget_exception(**kwargs):
        return {
            "exception_id": kwargs["exception_id"],
            "exception_status": "WAIVED",
            "resolution_reason": kwargs["resolution_reason"],
        }

    monkeypatch.setattr(
        admin_budget_governance,
        "waive_budget_exception",
        fake_waive_budget_exception,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/funding/budget-governance/exceptions/{exception_id}/waive",
            json={
                "resolved_by": "finance@example.com",
                "resolution_reason": "Accepted under campaign tolerance",
            },
        )

    assert response.status_code == 200
    assert response.json()["item"] == {
        "exception_id": exception_id,
        "exception_status": "WAIVED",
        "resolution_reason": "Accepted under campaign tolerance",
    }


async def test_budget_exception_invalid_state_returns_409(monkeypatch):
    from apps.api.routers import admin_budget_governance

    async def fake_resolve_budget_exception(**kwargs):
        raise admin_budget_governance.BudgetExceptionInvalidState(
            "Budget exception is not open"
        )

    monkeypatch.setattr(
        admin_budget_governance,
        "resolve_budget_exception",
        fake_resolve_budget_exception,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/funding/budget-governance/exceptions/{uuid4()}/resolve",
            json={},
        )

    assert response.status_code == 409
    assert response.json() == {"detail": "Budget exception is not open"}


async def test_budget_exception_missing_contract_returns_404(monkeypatch):
    from apps.api.routers import admin_budget_governance

    async def fake_create_budget_exception(**kwargs):
        raise admin_budget_governance.BudgetExceptionContractNotFound(
            "Funding contract not found"
        )

    monkeypatch.setattr(
        admin_budget_governance,
        "create_budget_exception",
        fake_create_budget_exception,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/budget-governance/exceptions",
            json={
                "tenant_code": "FNB",
                "contract_id": str(uuid4()),
                "exception_type": "BUDGET_OVERRUN",
                "exception_message": "Missing contract",
            },
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Funding contract not found"}


async def test_create_budget_approval_policy(monkeypatch):
    from apps.api.routers import admin_budget_governance

    policy_id = str(uuid4())
    calls = {}

    async def fake_create_budget_approval_policy(**kwargs):
        calls.update(kwargs)
        return {
            "policy_id": policy_id,
            "tenant_code": kwargs["tenant_code"],
            "sponsor_code": kwargs["sponsor_code"],
            "request_type": kwargs["request_type"],
            "min_amount": kwargs["min_amount"],
            "max_amount": kwargs["max_amount"],
            "approval_level": kwargs["approval_level"],
            "required_role": kwargs["required_role"],
            "policy_status": "ACTIVE",
            "priority": kwargs["priority"],
        }

    monkeypatch.setattr(
        admin_budget_governance,
        "create_budget_approval_policy",
        fake_create_budget_approval_policy,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/budget-governance/approval-policies",
            json={
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "request_type": "BUDGET_INCREASE",
                "min_amount": "500000.00",
                "max_amount": "1000000.00",
                "approval_level": "FINANCE",
                "required_role": "finance_approver",
                "priority": 20,
                "description": "Finance approval for larger budget increases",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["item"]["policy_id"] == policy_id
    assert body["item"]["min_amount"] == "500000.00"
    assert calls == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "request_type": "BUDGET_INCREASE",
        "min_amount": Decimal("500000.00"),
        "max_amount": Decimal("1000000.00"),
        "approval_level": "FINANCE",
        "required_role": "finance_approver",
        "priority": 20,
        "description": "Finance approval for larger budget increases",
        "metadata": {"source": "test"},
    }


async def test_list_budget_approval_policies(monkeypatch):
    from apps.api.routers import admin_budget_governance

    policy_id = str(uuid4())
    calls = {}

    async def fake_list_budget_approval_policies(**kwargs):
        calls.update(kwargs)
        return [
            {
                "policy_id": policy_id,
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "request_type": "BUDGET_TRANSFER",
                "approval_level": "EXECUTIVE",
                "policy_status": "ACTIVE",
            }
        ]

    monkeypatch.setattr(
        admin_budget_governance,
        "list_budget_approval_policies",
        fake_list_budget_approval_policies,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/funding/budget-governance/approval-policies",
            params={
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "request_type": "BUDGET_TRANSFER",
                "policy_status": "ACTIVE",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 1
    assert body["items"][0]["policy_id"] == policy_id
    assert calls == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "request_type": "BUDGET_TRANSFER",
        "policy_status": "ACTIVE",
        "limit": 25,
    }


async def test_evaluate_budget_approval_policy(monkeypatch):
    from apps.api.routers import admin_budget_governance

    policy_id = str(uuid4())
    calls = {}

    async def fake_evaluate_budget_approval_policy(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": kwargs["tenant_code"],
            "sponsor_code": kwargs["sponsor_code"],
            "request_type": kwargs["request_type"],
            "amount": kwargs["amount"],
            "approval_level": "FINANCE",
            "required_role": "finance_approver",
            "policy_required": True,
            "matched_policy": {"policy_id": policy_id},
        }

    monkeypatch.setattr(
        admin_budget_governance,
        "evaluate_budget_approval_policy",
        fake_evaluate_budget_approval_policy,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/budget-governance/approval-policies/evaluate",
            json={
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "request_type": "BUDGET_INCREASE",
                "amount": "750000.00",
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["result"]["approval_level"] == "FINANCE"
    assert body["result"]["required_role"] == "finance_approver"
    assert body["result"]["matched_policy"]["policy_id"] == policy_id
    assert calls == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "request_type": "BUDGET_INCREASE",
        "amount": Decimal("750000.00"),
    }
