from __future__ import annotations

from types import SimpleNamespace

import pytest

from services.fulfilment import resolver as resolver_mod
from services.fulfilment import service as service_mod
from services.fulfilment.base import (
    FulfilmentRequest,
    FulfilmentResult,
    FulfilmentStatus,
)
from services.fulfilment.resolver import (
    FulfilmentPolicy,
    FulfilmentPolicyNotFoundError,
    _row_to_policy,
)


class FakeConnection:
    def __init__(self, row=None):
        self.row = row
        self.executed_sql = None
        self.executed_args = None

    async def fetchrow(self, sql, *args):
        self.executed_sql = sql
        self.executed_args = args
        return self.row


class FakeAcquire:
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakePool:
    def __init__(self, connection):
        self.connection = connection

    def acquire(self):
        return FakeAcquire(self.connection)


def _policy_row(metadata=None):
    return {
        "fulfilment_policy_id": "policy-123",
        "tenant_code": "FNB",
        "reward_type": "CASH",
        "journey_code": None,
        "journey_version": None,
        "product_code": None,
        "execution_model": "PLATFORM_EXECUTES",
        "funding_model": "PRE_FUNDED_WALLET",
        "settlement_model": "REAL_TIME",
        "provider_key": "CASH_PROVIDER",
        "sla_seconds": 300,
        "max_retries": 3,
        "retry_backoff_seconds": 60,
        "metadata": metadata,
    }


def _cash_policy(provider_key="CASH_PROVIDER"):
    return FulfilmentPolicy(
        fulfilment_policy_id="policy-123",
        tenant_code="FNB",
        reward_type="CASH",
        journey_code=None,
        journey_version=None,
        product_code=None,
        execution_model="PLATFORM_EXECUTES",
        funding_model="PRE_FUNDED_WALLET",
        settlement_model="REAL_TIME",
        provider_key=provider_key,
        sla_seconds=300,
        max_retries=3,
        retry_backoff_seconds=60,
        metadata={"source": "test"},
    )


def _routing(
    selected_provider_key="CASH_PROVIDER",
    reason="PRIMARY_AVAILABLE",
    fallback_used=False,
):
    return SimpleNamespace(
        requested_provider_key="CASH_PROVIDER",
        selected_provider_key=selected_provider_key,
        reason=reason,
        fallback_used=fallback_used,
    )


class FakeProvider:
    def __init__(self):
        self.received_request = None

    async def fulfil(self, request):
        self.received_request = request
        return FulfilmentResult(
            status=FulfilmentStatus.PENDING,
            provider_reference="FAKE-REF-123",
            message="Fake fulfilment completed",
            metadata={"provider_key": request.provider_key},
        )


def _patch_funding(monkeypatch, funding_calls: dict):
    async def fake_reserve_reward_funding(**kwargs):
        funding_calls["reserve"] = kwargs
        return {"reserved": True, "already_reserved": False}

    async def fake_settle_reward_funding(**kwargs):
        funding_calls["settle"] = kwargs
        return {"settled": True}

    async def fake_release_reward_funding(**kwargs):
        funding_calls["release"] = kwargs
        return {"released": True}

    monkeypatch.setattr(service_mod, "reserve_reward_funding", fake_reserve_reward_funding)
    monkeypatch.setattr(service_mod, "settle_reward_funding", fake_settle_reward_funding)
    monkeypatch.setattr(service_mod, "release_reward_funding", fake_release_reward_funding)


def test_row_to_policy_maps_all_fields():
    policy = _row_to_policy(_policy_row(metadata={"channel": "wallet"}))

    assert policy == FulfilmentPolicy(
        fulfilment_policy_id="policy-123",
        tenant_code="FNB",
        reward_type="CASH",
        journey_code=None,
        journey_version=None,
        product_code=None,
        execution_model="PLATFORM_EXECUTES",
        funding_model="PRE_FUNDED_WALLET",
        settlement_model="REAL_TIME",
        provider_key="CASH_PROVIDER",
        sla_seconds=300,
        max_retries=3,
        retry_backoff_seconds=60,
        metadata={"channel": "wallet"},
    )


def test_row_to_policy_defaults_metadata_to_empty_dict():
    policy = _row_to_policy(_policy_row(metadata=None))

    assert policy.metadata == {}


@pytest.mark.asyncio
async def test_resolve_fulfilment_policy_returns_policy(monkeypatch):
    fake_connection = FakeConnection(row=_policy_row())
    fake_pool = FakePool(fake_connection)

    monkeypatch.setattr(resolver_mod, "get_async_pool", lambda: fake_pool)

    policy = await resolver_mod.resolve_fulfilment_policy(
        tenant_code="FNB",
        reward_type="CASH",
    )

    assert policy.provider_key == "CASH_PROVIDER"
    assert fake_connection.executed_args == ("FNB", "CASH", None, None, None)
    assert "FROM fulfilment_policies" in fake_connection.executed_sql
    assert "tenant_code = $1" in fake_connection.executed_sql
    assert "reward_type = $2" in fake_connection.executed_sql


@pytest.mark.asyncio
async def test_resolve_fulfilment_policy_prefers_vertical_context(monkeypatch):
    row = _policy_row(
        metadata={"vertical": "INSURANCE"},
    )
    row.update(
        {
            "journey_code": "INSURANCE_POLICY",
            "journey_version": "v1",
            "product_code": "INSURANCE",
            "provider_key": "TENANT_INSTRUCTION_PROVIDER",
            "execution_model": "TENANT_EXECUTES",
            "settlement_model": "BATCH_SETTLEMENT",
        }
    )
    fake_connection = FakeConnection(row=row)
    fake_pool = FakePool(fake_connection)

    monkeypatch.setattr(resolver_mod, "get_async_pool", lambda: fake_pool)

    policy = await resolver_mod.resolve_fulfilment_policy(
        tenant_code="FNB",
        reward_type="CASH",
        journey_code="INSURANCE_POLICY",
        journey_version="v1",
        product_code="INSURANCE",
    )

    assert policy.provider_key == "TENANT_INSTRUCTION_PROVIDER"
    assert policy.journey_code == "INSURANCE_POLICY"
    assert policy.product_code == "INSURANCE"
    assert fake_connection.executed_args == (
        "FNB",
        "CASH",
        "INSURANCE_POLICY",
        "v1",
        "INSURANCE",
    )
    assert "journey_code = $3 OR journey_code IS NULL" in fake_connection.executed_sql


@pytest.mark.asyncio
async def test_resolve_fulfilment_policy_raises_when_missing(monkeypatch):
    fake_connection = FakeConnection(row=None)
    fake_pool = FakePool(fake_connection)

    monkeypatch.setattr(resolver_mod, "get_async_pool", lambda: fake_pool)

    with pytest.raises(
        FulfilmentPolicyNotFoundError,
        match="No active fulfilment policy found",
    ):
        await resolver_mod.resolve_fulfilment_policy(
            tenant_code="FNB",
            reward_type="EBUCKS",
        )


@pytest.mark.asyncio
async def test_fulfil_reward_resolves_policy_and_executes_provider(monkeypatch):
    policy = _cash_policy()
    fake_provider = FakeProvider()
    success_call = {}
    settlement_call = {}
    funding_calls = {}

    _patch_funding(monkeypatch, funding_calls)

    async def fake_resolve_fulfilment_policy(*, tenant_code, reward_type, **_context):
        assert tenant_code == "FNB"
        assert reward_type == "CASH"
        return policy

    async def fake_get_existing_audit_by_idempotency_key(key):
        assert key == "FNB:NO_TRACK_ID:CASH:123456789:ACCOUNT_OPENED"
        return None

    async def fake_create_fulfilment_audit_record(**kwargs):
        assert kwargs["tenant_code"] == "FNB"
        assert kwargs["referral_track_id"] is None
        assert kwargs["referee_ucn"] == "123456789"
        assert kwargs["reward_type"] == "CASH"
        assert kwargs["fulfilment_provider"] == "CASH_PROVIDER"
        assert kwargs["max_attempts"] == 3
        assert kwargs["idempotency_key"] == (
            "FNB:NO_TRACK_ID:CASH:123456789:ACCOUNT_OPENED"
        )
        return {"audit_id": "audit-123", "status": "PENDING"}

    async def fake_mark_fulfilment_processing(**kwargs):
        assert kwargs["audit_id"] == "audit-123"

    async def fake_mark_fulfilment_success(**kwargs):
        assert kwargs["audit_id"] == "audit-123"
        assert kwargs["provider_reference"] == "FAKE-REF-123"

    async def fake_record_pending_settlement(**kwargs):
        settlement_call.update(kwargs)
        return {"settlement_id": "settlement-123"}

    def fake_resolve_provider(provider_key):
        assert provider_key == "CASH_PROVIDER"
        return _routing()

    def fake_record_provider_success(provider_key):
        success_call["provider_key"] = provider_key

    monkeypatch.setattr(service_mod, "resolve_fulfilment_policy", fake_resolve_fulfilment_policy)
    monkeypatch.setattr(service_mod, "get_fulfilment_provider", lambda provider_key: fake_provider)
    monkeypatch.setattr(service_mod, "get_existing_audit_by_idempotency_key", fake_get_existing_audit_by_idempotency_key)
    monkeypatch.setattr(service_mod, "create_fulfilment_audit_record", fake_create_fulfilment_audit_record)
    monkeypatch.setattr(service_mod, "mark_fulfilment_processing", fake_mark_fulfilment_processing)
    monkeypatch.setattr(service_mod, "mark_fulfilment_success", fake_mark_fulfilment_success)
    monkeypatch.setattr(service_mod, "record_pending_settlement", fake_record_pending_settlement)
    monkeypatch.setattr(service_mod, "resolve_provider", fake_resolve_provider)
    monkeypatch.setattr(service_mod, "record_provider_success", fake_record_provider_success)

    request = FulfilmentRequest(
        tenant_code="FNB",
        reward_id="reward-123",
        reward_type="CASH",
        reward_value=100.0,
        recipient_ucn="123456789",
        currency="ZAR",
        journey_code="MAIN_BANK_SWITCH",
        milestone_code="ACCOUNT_OPENED",
        product_code="DDA13",
        metadata={"correlation_id": "corr-123"},
    )

    result = await service_mod.fulfil_reward(request)

    assert result.status == FulfilmentStatus.PENDING
    assert result.provider_reference == "FAKE-REF-123"
    assert success_call["provider_key"] == "CASH_PROVIDER"

    assert funding_calls["reserve"]["reward_id"] == "reward-123"
    assert funding_calls["reserve"]["tenant_code"] == "FNB"
    assert funding_calls["reserve"]["amount"] == 100.0
    assert funding_calls["reserve"]["correlation_id"] == "audit-123"

    assert funding_calls["settle"]["reward_id"] == "reward-123"
    assert funding_calls["settle"]["correlation_id"] == "audit-123"
    assert "release" not in funding_calls

    assert settlement_call["tenant_code"] == "FNB"
    assert settlement_call["reward_id"] == "reward-123"
    assert settlement_call["audit_id"] == "audit-123"
    assert settlement_call["provider_key"] == "CASH_PROVIDER"
    assert settlement_call["provider_reference"] == "FAKE-REF-123"
    assert settlement_call["amount"] == 100.0
    assert settlement_call["currency"] == "ZAR"

    enriched = fake_provider.received_request

    assert enriched.provider_key == "CASH_PROVIDER"
    assert enriched.execution_model == "PLATFORM_EXECUTES"
    assert enriched.funding_model == "PRE_FUNDED_WALLET"
    assert enriched.settlement_model == "REAL_TIME"

    assert enriched.metadata["correlation_id"] == "corr-123"
    assert enriched.metadata["fulfilment_policy_id"] == "policy-123"
    assert enriched.metadata["fulfilment_policy_metadata"] == {"source": "test"}
    assert enriched.metadata["idempotency_key"] == (
        "FNB:NO_TRACK_ID:CASH:123456789:ACCOUNT_OPENED"
    )
    assert enriched.metadata["requested_provider_key"] == "CASH_PROVIDER"
    assert enriched.metadata["selected_provider_key"] == "CASH_PROVIDER"
    assert enriched.metadata["provider_routing_reason"] == "PRIMARY_AVAILABLE"
    assert enriched.metadata["fallback_used"] is False


@pytest.mark.asyncio
async def test_fulfil_reward_creates_settlement_record(monkeypatch):
    policy = _cash_policy()
    fake_provider = FakeProvider()
    settlement_call = {}
    funding_calls = {}

    _patch_funding(monkeypatch, funding_calls)

    async def fake_resolve_fulfilment_policy(*, tenant_code, reward_type, **_context):
        return policy

    async def fake_get_existing_audit_by_idempotency_key(key):
        return None

    async def fake_create_fulfilment_audit_record(**kwargs):
        return {"audit_id": "audit-123", "status": "PENDING"}

    async def fake_mark_fulfilment_processing(**kwargs):
        return None

    async def fake_mark_fulfilment_success(**kwargs):
        return None

    async def fake_record_pending_settlement(**kwargs):
        settlement_call.update(kwargs)
        return {"settlement_id": "settlement-123"}

    def fake_resolve_provider(provider_key):
        return _routing()

    monkeypatch.setattr(service_mod, "resolve_fulfilment_policy", fake_resolve_fulfilment_policy)
    monkeypatch.setattr(service_mod, "get_existing_audit_by_idempotency_key", fake_get_existing_audit_by_idempotency_key)
    monkeypatch.setattr(service_mod, "create_fulfilment_audit_record", fake_create_fulfilment_audit_record)
    monkeypatch.setattr(service_mod, "mark_fulfilment_processing", fake_mark_fulfilment_processing)
    monkeypatch.setattr(service_mod, "mark_fulfilment_success", fake_mark_fulfilment_success)
    monkeypatch.setattr(service_mod, "record_pending_settlement", fake_record_pending_settlement)
    monkeypatch.setattr(service_mod, "resolve_provider", fake_resolve_provider)
    monkeypatch.setattr(service_mod, "get_fulfilment_provider", lambda provider_key: fake_provider)

    request = FulfilmentRequest(
        tenant_code="FNB",
        reward_id="reward-123",
        reward_type="CASH",
        reward_value=100.0,
        recipient_ucn="123456789",
        currency="ZAR",
        journey_code="MAIN_BANK_SWITCH",
        milestone_code="ACCOUNT_OPENED",
        product_code="DDA13",
        metadata={},
    )

    await service_mod.fulfil_reward(request)

    assert funding_calls["reserve"]["reward_id"] == "reward-123"
    assert funding_calls["settle"]["reward_id"] == "reward-123"
    assert "release" not in funding_calls

    assert settlement_call["tenant_code"] == "FNB"
    assert settlement_call["reward_id"] == "reward-123"
    assert settlement_call["provider_key"] == "CASH_PROVIDER"
    assert settlement_call["amount"] == 100.0


@pytest.mark.asyncio
async def test_fulfil_reward_uses_fallback_provider(monkeypatch):
    policy = _cash_policy()
    fake_provider = FakeProvider()
    success_call = {}
    funding_calls = {}

    _patch_funding(monkeypatch, funding_calls)

    async def fake_resolve_fulfilment_policy(*, tenant_code, reward_type, **_context):
        return policy

    async def fake_get_existing_audit_by_idempotency_key(key):
        return None

    async def fake_create_fulfilment_audit_record(**kwargs):
        return {"audit_id": "audit-123", "status": "PENDING"}

    async def fake_mark_fulfilment_processing(**kwargs):
        return None

    async def fake_mark_fulfilment_success(**kwargs):
        return None

    async def fake_record_pending_settlement(**kwargs):
        return {"settlement_id": "settlement-123"}

    def fake_resolve_provider(provider_key):
        return _routing(
            selected_provider_key="CASH_PROVIDER_SECONDARY",
            reason="PRIMARY_CIRCUIT_OPEN_FALLBACK_AVAILABLE",
            fallback_used=True,
        )

    def fake_get_fulfilment_provider(provider_key):
        assert provider_key == "CASH_PROVIDER_SECONDARY"
        return fake_provider

    def fake_record_provider_success(provider_key):
        success_call["provider_key"] = provider_key

    monkeypatch.setattr(service_mod, "resolve_fulfilment_policy", fake_resolve_fulfilment_policy)
    monkeypatch.setattr(service_mod, "get_existing_audit_by_idempotency_key", fake_get_existing_audit_by_idempotency_key)
    monkeypatch.setattr(service_mod, "create_fulfilment_audit_record", fake_create_fulfilment_audit_record)
    monkeypatch.setattr(service_mod, "mark_fulfilment_processing", fake_mark_fulfilment_processing)
    monkeypatch.setattr(service_mod, "mark_fulfilment_success", fake_mark_fulfilment_success)
    monkeypatch.setattr(service_mod, "record_pending_settlement", fake_record_pending_settlement)
    monkeypatch.setattr(service_mod, "resolve_provider", fake_resolve_provider)
    monkeypatch.setattr(service_mod, "get_fulfilment_provider", fake_get_fulfilment_provider)
    monkeypatch.setattr(service_mod, "record_provider_success", fake_record_provider_success)

    request = FulfilmentRequest(
        tenant_code="FNB",
        reward_id="reward-123",
        reward_type="CASH",
        reward_value=100.0,
        recipient_ucn="123456789",
        currency="ZAR",
        journey_code="MAIN_BANK_SWITCH",
        milestone_code="ACCOUNT_OPENED",
        product_code="DDA13",
        metadata={},
    )

    result = await service_mod.fulfil_reward(request)

    assert result.provider_reference == "FAKE-REF-123"
    assert success_call["provider_key"] == "CASH_PROVIDER_SECONDARY"
    assert funding_calls["reserve"]["reward_id"] == "reward-123"
    assert funding_calls["settle"]["reward_id"] == "reward-123"
    assert "release" not in funding_calls

    assert fake_provider.received_request.provider_key == "CASH_PROVIDER_SECONDARY"
    assert fake_provider.received_request.metadata["requested_provider_key"] == "CASH_PROVIDER"
    assert fake_provider.received_request.metadata["selected_provider_key"] == "CASH_PROVIDER_SECONDARY"
    assert (
        fake_provider.received_request.metadata["provider_routing_reason"]
        == "PRIMARY_CIRCUIT_OPEN_FALLBACK_AVAILABLE"
    )
    assert fake_provider.received_request.metadata["fallback_used"] is True


@pytest.mark.asyncio
async def test_fulfil_reward_skips_duplicate_audit(monkeypatch):
    policy = _cash_policy()

    async def fake_resolve_fulfilment_policy(*, tenant_code, reward_type, **_context):
        return policy

    async def fake_get_existing_audit_by_idempotency_key(key):
        return {
            "audit_id": "audit-123",
            "status": "SUCCESS",
            "provider_reference": "PROVIDER-REF-123",
        }

    def fail_if_provider_called(provider_key):
        raise AssertionError("Provider should not be called for duplicate fulfilment")

    async def fail_if_funding_called(**kwargs):
        raise AssertionError("Funding should not be called for duplicate fulfilment")

    monkeypatch.setattr(service_mod, "resolve_fulfilment_policy", fake_resolve_fulfilment_policy)
    monkeypatch.setattr(service_mod, "get_existing_audit_by_idempotency_key", fake_get_existing_audit_by_idempotency_key)
    monkeypatch.setattr(service_mod, "get_fulfilment_provider", fail_if_provider_called)
    monkeypatch.setattr(service_mod, "reserve_reward_funding", fail_if_funding_called)
    monkeypatch.setattr(service_mod, "settle_reward_funding", fail_if_funding_called)
    monkeypatch.setattr(service_mod, "release_reward_funding", fail_if_funding_called)

    request = FulfilmentRequest(
        tenant_code="FNB",
        reward_id="reward-123",
        reward_type="CASH",
        reward_value=100.0,
        recipient_ucn="123456789",
        currency="ZAR",
        journey_code="MAIN_BANK_SWITCH",
        milestone_code="ACCOUNT_OPENED",
        product_code="DDA13",
        metadata={},
    )

    result = await service_mod.fulfil_reward(request)

    assert result.status == FulfilmentStatus.SKIPPED_DUPLICATE
    assert result.provider_reference == "PROVIDER-REF-123"


@pytest.mark.asyncio
async def test_fulfil_reward_marks_failed_retryable_when_provider_fails(monkeypatch):
    policy = _cash_policy()
    funding_calls = {}

    _patch_funding(monkeypatch, funding_calls)

    class FailingProvider:
        async def fulfil(self, request):
            raise RuntimeError("provider timeout")

    async def fake_resolve_fulfilment_policy(*, tenant_code, reward_type, **_context):
        return policy

    async def fake_get_existing_audit_by_idempotency_key(key):
        return None

    async def fake_create_fulfilment_audit_record(**kwargs):
        assert kwargs["max_attempts"] == 3
        return {"audit_id": "audit-123", "status": "PENDING"}

    async def fake_mark_fulfilment_processing(**kwargs):
        assert kwargs["audit_id"] == "audit-123"

    async def fake_increment_fulfilment_attempt(**kwargs):
        assert kwargs["audit_id"] == "audit-123"
        return {
            "attempt_no": 2,
            "max_attempts": 3,
            "retries_exhausted": False,
        }

    failure_call = {}
    retry_schedule_call = {}
    failure_circuit_call = {}

    async def fake_mark_fulfilment_failed(**kwargs):
        failure_call.update(kwargs)

    async def fake_schedule_fulfilment_retry(**kwargs):
        retry_schedule_call.update(kwargs)
        return {
            "status": "retry_scheduled",
            "audit_id": kwargs["audit_id"],
        }

    def fake_resolve_provider(provider_key):
        return _routing()

    def fake_record_provider_failure(provider_key):
        failure_circuit_call["provider_key"] = provider_key

    monkeypatch.setattr(service_mod, "resolve_fulfilment_policy", fake_resolve_fulfilment_policy)
    monkeypatch.setattr(service_mod, "get_fulfilment_provider", lambda provider_key: FailingProvider())
    monkeypatch.setattr(service_mod, "get_existing_audit_by_idempotency_key", fake_get_existing_audit_by_idempotency_key)
    monkeypatch.setattr(service_mod, "create_fulfilment_audit_record", fake_create_fulfilment_audit_record)
    monkeypatch.setattr(service_mod, "mark_fulfilment_processing", fake_mark_fulfilment_processing)
    monkeypatch.setattr(service_mod, "increment_fulfilment_attempt", fake_increment_fulfilment_attempt)
    monkeypatch.setattr(service_mod, "mark_fulfilment_failed", fake_mark_fulfilment_failed)
    monkeypatch.setattr(service_mod, "schedule_fulfilment_retry", fake_schedule_fulfilment_retry)
    monkeypatch.setattr(service_mod, "resolve_provider", fake_resolve_provider)
    monkeypatch.setattr(service_mod, "record_provider_failure", fake_record_provider_failure)

    request = FulfilmentRequest(
        tenant_code="FNB",
        reward_id="reward-123",
        reward_type="CASH",
        reward_value=100.0,
        recipient_ucn="123456789",
        currency="ZAR",
        journey_code="MAIN_BANK_SWITCH",
        milestone_code="ACCOUNT_OPENED",
        product_code="DDA13",
        metadata={},
    )

    with pytest.raises(RuntimeError, match="provider timeout"):
        await service_mod.fulfil_reward(request)

    assert funding_calls["reserve"]["reward_id"] == "reward-123"
    assert funding_calls["release"]["reward_id"] == "reward-123"
    assert "settle" not in funding_calls

    assert failure_circuit_call["provider_key"] == "CASH_PROVIDER"
    assert failure_call["audit_id"] == "audit-123"
    assert failure_call["failure_reason"] == "provider timeout"
    assert failure_call["retryable"] is True
    assert retry_schedule_call["audit_id"] == "audit-123"


@pytest.mark.asyncio
async def test_fulfil_reward_publishes_to_dlq_when_retries_exhausted(monkeypatch):
    policy = _cash_policy()
    funding_calls = {}

    _patch_funding(monkeypatch, funding_calls)

    class FailingProvider:
        async def fulfil(self, request):
            raise RuntimeError("provider hard failure")

    async def fake_resolve_fulfilment_policy(*, tenant_code, reward_type, **_context):
        return policy

    async def fake_get_existing_audit_by_idempotency_key(key):
        return None

    async def fake_create_fulfilment_audit_record(**kwargs):
        return {"audit_id": "audit-123", "status": "PENDING"}

    async def fake_mark_fulfilment_processing(**kwargs):
        return None

    async def fake_increment_fulfilment_attempt(**kwargs):
        return {
            "attempt_no": 3,
            "max_attempts": 3,
            "retries_exhausted": True,
        }

    failure_call = {}
    dlq_call = {}
    failure_circuit_call = {}

    async def fake_mark_fulfilment_failed(**kwargs):
        failure_call.update(kwargs)

    async def fake_publish_to_dlq(**kwargs):
        dlq_call.update(kwargs)

    def fake_resolve_provider(provider_key):
        return _routing()

    def fake_record_provider_failure(provider_key):
        failure_circuit_call["provider_key"] = provider_key

    monkeypatch.setattr(service_mod, "resolve_fulfilment_policy", fake_resolve_fulfilment_policy)
    monkeypatch.setattr(service_mod, "get_fulfilment_provider", lambda provider_key: FailingProvider())
    monkeypatch.setattr(service_mod, "get_existing_audit_by_idempotency_key", fake_get_existing_audit_by_idempotency_key)
    monkeypatch.setattr(service_mod, "create_fulfilment_audit_record", fake_create_fulfilment_audit_record)
    monkeypatch.setattr(service_mod, "mark_fulfilment_processing", fake_mark_fulfilment_processing)
    monkeypatch.setattr(service_mod, "increment_fulfilment_attempt", fake_increment_fulfilment_attempt)
    monkeypatch.setattr(service_mod, "mark_fulfilment_failed", fake_mark_fulfilment_failed)
    monkeypatch.setattr(service_mod, "publish_to_dlq", fake_publish_to_dlq)
    monkeypatch.setattr(service_mod, "resolve_provider", fake_resolve_provider)
    monkeypatch.setattr(service_mod, "record_provider_failure", fake_record_provider_failure)

    request = FulfilmentRequest(
        tenant_code="FNB",
        reward_id="reward-123",
        reward_type="CASH",
        reward_value=100.0,
        recipient_ucn="123456789",
        currency="ZAR",
        journey_code="MAIN_BANK_SWITCH",
        milestone_code="ACCOUNT_OPENED",
        product_code="DDA13",
        metadata={},
    )

    with pytest.raises(RuntimeError, match="provider hard failure"):
        await service_mod.fulfil_reward(request)

    assert funding_calls["reserve"]["reward_id"] == "reward-123"
    assert funding_calls["release"]["reward_id"] == "reward-123"
    assert "settle" not in funding_calls

    assert failure_circuit_call["provider_key"] == "CASH_PROVIDER"
    assert failure_call["audit_id"] == "audit-123"
    assert failure_call["failure_reason"] == "provider hard failure"
    assert failure_call["retryable"] is False
    assert dlq_call["error"] == "provider hard failure"


@pytest.mark.asyncio
async def test_fulfil_reward_fails_fast_when_no_provider_available(monkeypatch):
    policy = _cash_policy()
    funding_calls = {}

    _patch_funding(monkeypatch, funding_calls)

    async def fake_resolve_fulfilment_policy(*, tenant_code, reward_type, **_context):
        return policy

    async def fake_get_existing_audit_by_idempotency_key(key):
        return None

    async def fake_create_fulfilment_audit_record(**kwargs):
        return {"audit_id": "audit-123", "status": "PENDING"}

    async def fake_mark_fulfilment_processing(**kwargs):
        return None

    async def fake_increment_fulfilment_attempt(**kwargs):
        return {
            "attempt_no": 1,
            "max_attempts": 3,
            "retries_exhausted": False,
        }

    failure_call = {}
    failure_circuit_call = {}
    retry_schedule_call = {}

    async def fake_mark_fulfilment_failed(**kwargs):
        failure_call.update(kwargs)

    async def fake_schedule_fulfilment_retry(**kwargs):
        retry_schedule_call.update(kwargs)

    def fake_resolve_provider(provider_key):
        return _routing(
            selected_provider_key="CASH_PROVIDER",
            reason="NO_AVAILABLE_PROVIDER",
            fallback_used=False,
        )

    def fake_record_provider_failure(provider_key):
        failure_circuit_call["provider_key"] = provider_key

    def fail_if_provider_loaded(provider_key):
        raise AssertionError("Provider should not be loaded when no provider is available")

    monkeypatch.setattr(service_mod, "resolve_fulfilment_policy", fake_resolve_fulfilment_policy)
    monkeypatch.setattr(service_mod, "get_existing_audit_by_idempotency_key", fake_get_existing_audit_by_idempotency_key)
    monkeypatch.setattr(service_mod, "create_fulfilment_audit_record", fake_create_fulfilment_audit_record)
    monkeypatch.setattr(service_mod, "mark_fulfilment_processing", fake_mark_fulfilment_processing)
    monkeypatch.setattr(service_mod, "increment_fulfilment_attempt", fake_increment_fulfilment_attempt)
    monkeypatch.setattr(service_mod, "mark_fulfilment_failed", fake_mark_fulfilment_failed)
    monkeypatch.setattr(service_mod, "schedule_fulfilment_retry", fake_schedule_fulfilment_retry)
    monkeypatch.setattr(service_mod, "resolve_provider", fake_resolve_provider)
    monkeypatch.setattr(service_mod, "record_provider_failure", fake_record_provider_failure)
    monkeypatch.setattr(service_mod, "get_fulfilment_provider", fail_if_provider_loaded)

    request = FulfilmentRequest(
        tenant_code="FNB",
        reward_id="reward-123",
        reward_type="CASH",
        reward_value=100.0,
        recipient_ucn="123456789",
        currency="ZAR",
        journey_code="MAIN_BANK_SWITCH",
        milestone_code="ACCOUNT_OPENED",
        product_code="DDA13",
        metadata={},
    )

    with pytest.raises(RuntimeError, match="No available provider for: CASH_PROVIDER"):
        await service_mod.fulfil_reward(request)

    assert "reserve" not in funding_calls
    assert "settle" not in funding_calls
    assert funding_calls["release"]["reward_id"] == "reward-123"

    assert failure_circuit_call["provider_key"] == "CASH_PROVIDER"
    assert failure_call["audit_id"] == "audit-123"
    assert failure_call["retryable"] is True
    assert retry_schedule_call["audit_id"] == "audit-123"
