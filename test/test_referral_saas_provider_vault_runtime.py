import pytest

from services.referral_saas_provider_vault_runtime import (
    PLATFORM_REFERENCE_ADAPTER_REF,
    PLATFORM_REFERENCE_CAPABILITY,
    PLATFORM_REFERENCE_PROVIDER_KEY,
    PLATFORM_VAULT_REFERENCE_ADAPTER_REF,
    PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED,
    PROVIDER_VAULT_BLOCKED_VAULT_NOT_CONFIGURED,
    PROVIDER_VAULT_EXECUTION_READY,
    VENDOR_MANAGED_PROVIDER_ADAPTER_REF,
    ProviderVaultRuntimeRequest,
    ProviderVaultRuntimeResult,
    clear_provider_vault_runtime_adapters,
    configure_provider_vault_runtime,
    configure_vendor_managed_provider_vault_runtime,
    execute_provider_vault_runtime,
    register_provider_vault_runtime_adapter,
)


def _request() -> ProviderVaultRuntimeRequest:
    return ProviderVaultRuntimeRequest(
        account_id="acct-1",
        tenant_code="tenant-1",
        credential_request_ref="credreq-1",
        approved_request_version="credreq-1",
        execution_intent="CREATE_PROVIDER_VAULT_REFERENCE",
        execution_mode="SAFE_RUNTIME_EXECUTION",
        provider_key="sendgrid",
        environment="SANDBOX",
        capability="REFERRAL_SAAS_PROVIDER_REFERENCE",
        reason_code="PROVIDER_VAULT_RUNTIME_EXECUTION",
        command_payload_hash="hash-1",
        actor_ref="admin-1",
        actor_role="ADMIN",
    )


def _platform_reference_request(
    *,
    environment: str = "SANDBOX",
    capability: str = PLATFORM_REFERENCE_CAPABILITY,
) -> ProviderVaultRuntimeRequest:
    return ProviderVaultRuntimeRequest(
        account_id="acct-1",
        tenant_code="tenant-1",
        credential_request_ref="credreq-1",
        approved_request_version="credreq-1",
        execution_intent="CREATE_PROVIDER_VAULT_REFERENCE",
        execution_mode="SAFE_RUNTIME_EXECUTION",
        provider_key=PLATFORM_REFERENCE_PROVIDER_KEY,
        environment=environment,
        capability=capability,
        reason_code="PROVIDER_VAULT_RUNTIME_EXECUTION",
        command_payload_hash="hash-1",
        actor_ref="admin-1",
        actor_role="ADMIN",
    )


def _vendor_managed_request(
    *,
    provider_key: str = "sendgrid",
    environment: str = "SANDBOX",
    capability: str = "REFERRAL_SAAS_PROVIDER_REFERENCE",
) -> ProviderVaultRuntimeRequest:
    return ProviderVaultRuntimeRequest(
        account_id="acct-1",
        tenant_code="tenant-1",
        credential_request_ref="credreq-1",
        approved_request_version="credreq-1",
        execution_intent="CREATE_PROVIDER_VAULT_REFERENCE",
        execution_mode="SAFE_RUNTIME_EXECUTION",
        provider_key=provider_key,
        environment=environment,
        capability=capability,
        reason_code="PROVIDER_VAULT_RUNTIME_EXECUTION",
        command_payload_hash="hash-1",
        actor_ref="admin-1",
        actor_role="ADMIN",
    )


@pytest.fixture(autouse=True)
def reset_runtime_registry():
    clear_provider_vault_runtime_adapters()
    yield
    clear_provider_vault_runtime_adapters()


@pytest.mark.asyncio
async def test_provider_vault_runtime_blocks_without_provider_adapter() -> None:
    result = await execute_provider_vault_runtime(_request())

    assert result.command_status == PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED
    assert result.blocked_reason == PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED
    assert result.provider_runtime_reference is None
    assert result.opaque_vault_reference is None


@pytest.mark.asyncio
async def test_provider_vault_runtime_vendor_managed_blocks_without_allowlist() -> None:
    configure_provider_vault_runtime(vault_adapter_ref="managed-vault::adapter")

    result = await execute_provider_vault_runtime(_vendor_managed_request())

    assert result.command_status == PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED
    assert result.blocked_reason == PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED
    assert result.provider_runtime_reference is None
    assert result.opaque_vault_reference is None


@pytest.mark.asyncio
async def test_provider_vault_runtime_vendor_managed_blocks_without_managed_vault() -> None:
    configure_vendor_managed_provider_vault_runtime(provider_keys=["sendgrid"])

    result = await execute_provider_vault_runtime(_vendor_managed_request())

    assert result.command_status == PROVIDER_VAULT_BLOCKED_VAULT_NOT_CONFIGURED
    assert result.blocked_reason == PROVIDER_VAULT_BLOCKED_VAULT_NOT_CONFIGURED
    assert result.provider_runtime_reference is None
    assert result.opaque_vault_reference is None


@pytest.mark.asyncio
async def test_provider_vault_runtime_vendor_managed_returns_opaque_references() -> None:
    configure_vendor_managed_provider_vault_runtime(
        provider_keys=["SENDGRID"],
        vault_adapter_ref="managed-vault::adapter",
    )

    result = await execute_provider_vault_runtime(_vendor_managed_request())

    assert result.command_status == PROVIDER_VAULT_EXECUTION_READY
    assert result.blocked_reason is None
    assert result.adapter_ref == f"{VENDOR_MANAGED_PROVIDER_ADAPTER_REF}:SENDGRID"
    assert result.vault_adapter_ref == "managed-vault::adapter"
    assert result.provider_runtime_reference is not None
    assert result.provider_runtime_reference.startswith("vendor_prv_ref_")
    assert result.opaque_vault_reference is not None
    assert result.opaque_vault_reference.startswith("managed_vault_ref_")
    assert "acct-1" not in result.provider_runtime_reference
    assert "tenant-1" not in result.provider_runtime_reference
    assert "credreq-1" not in result.provider_runtime_reference
    assert "acct-1" not in result.opaque_vault_reference
    assert "tenant-1" not in result.opaque_vault_reference
    assert "credreq-1" not in result.opaque_vault_reference
    assert "No raw secret was accepted" in result.plain_language_summary
    assert "no vendor provider was called" in result.plain_language_summary


@pytest.mark.asyncio
async def test_provider_vault_runtime_vendor_managed_unsupported_capability_blocks() -> None:
    configure_vendor_managed_provider_vault_runtime(
        provider_keys=["sendgrid"],
        vault_adapter_ref="managed-vault::adapter",
    )

    result = await execute_provider_vault_runtime(
        _vendor_managed_request(capability="REFERRAL_MESSAGE_DELIVERY")
    )

    assert result.command_status == PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED
    assert result.blocked_reason == PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED
    assert result.provider_runtime_reference is None
    assert result.opaque_vault_reference is None


@pytest.mark.asyncio
async def test_provider_vault_runtime_blocks_without_vault_adapter() -> None:
    async def fake_adapter(
        request: ProviderVaultRuntimeRequest,
    ) -> ProviderVaultRuntimeResult:
        return ProviderVaultRuntimeResult(
            command_status=PROVIDER_VAULT_EXECUTION_READY,
            blocked_reason=None,
            next_action="Provider and vault references are ready.",
            plain_language_summary="Provider/vault runtime execution completed safely.",
            provider_runtime_reference=f"provider::{request.provider_key}",
            opaque_vault_reference="vault::opaque",
            adapter_ref="adapter::sendgrid",
        )

    register_provider_vault_runtime_adapter(
        provider_key="sendgrid",
        environment="SANDBOX",
        capability="REFERRAL_SAAS_PROVIDER_REFERENCE",
        adapter=fake_adapter,
    )

    result = await execute_provider_vault_runtime(_request())

    assert result.command_status == PROVIDER_VAULT_BLOCKED_VAULT_NOT_CONFIGURED
    assert result.blocked_reason == PROVIDER_VAULT_BLOCKED_VAULT_NOT_CONFIGURED
    assert result.provider_runtime_reference is None
    assert result.opaque_vault_reference is None


@pytest.mark.asyncio
async def test_provider_vault_runtime_can_handoff_to_registered_adapter() -> None:
    async def fake_adapter(
        request: ProviderVaultRuntimeRequest,
    ) -> ProviderVaultRuntimeResult:
        return ProviderVaultRuntimeResult(
            command_status=PROVIDER_VAULT_EXECUTION_READY,
            blocked_reason=None,
            next_action="Provider and vault references are ready.",
            plain_language_summary="Provider/vault runtime execution completed safely.",
            provider_runtime_reference=f"provider::{request.provider_key}",
            opaque_vault_reference="vault::opaque",
            adapter_ref="adapter::sendgrid",
        )

    configure_provider_vault_runtime(vault_adapter_ref="vault::adapter")
    register_provider_vault_runtime_adapter(
        provider_key="SENDGRID",
        environment="sandbox",
        capability="referral_saas_provider_reference",
        adapter=fake_adapter,
    )

    result = await execute_provider_vault_runtime(_request())

    assert result.command_status == PROVIDER_VAULT_EXECUTION_READY
    assert result.blocked_reason is None
    assert result.provider_runtime_reference == "provider::sendgrid"
    assert result.opaque_vault_reference == "vault::opaque"
    assert result.adapter_ref == "adapter::sendgrid"
    assert result.vault_adapter_ref == "vault::adapter"


@pytest.mark.asyncio
async def test_provider_vault_runtime_platform_reference_returns_opaque_references() -> None:
    result = await execute_provider_vault_runtime(_platform_reference_request())

    assert result.command_status == PROVIDER_VAULT_EXECUTION_READY
    assert result.blocked_reason is None
    assert result.adapter_ref == PLATFORM_REFERENCE_ADAPTER_REF
    assert result.vault_adapter_ref == PLATFORM_VAULT_REFERENCE_ADAPTER_REF
    assert result.provider_runtime_reference is not None
    assert result.provider_runtime_reference.startswith("prv_ref_")
    assert result.opaque_vault_reference is not None
    assert result.opaque_vault_reference.startswith("vault_ref_")
    assert "acct-1" not in result.provider_runtime_reference
    assert "tenant-1" not in result.provider_runtime_reference
    assert "credreq-1" not in result.provider_runtime_reference
    assert "acct-1" not in result.opaque_vault_reference
    assert "tenant-1" not in result.opaque_vault_reference
    assert "credreq-1" not in result.opaque_vault_reference
    assert "No raw secret was accepted" in result.plain_language_summary


@pytest.mark.asyncio
async def test_provider_vault_runtime_platform_reference_unsupported_environment_blocks() -> None:
    result = await execute_provider_vault_runtime(
        _platform_reference_request(environment="DEV")
    )

    assert result.command_status == PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED
    assert result.blocked_reason == PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED
    assert result.provider_runtime_reference is None
    assert result.opaque_vault_reference is None


@pytest.mark.asyncio
async def test_provider_vault_runtime_platform_reference_unsupported_capability_blocks() -> None:
    result = await execute_provider_vault_runtime(
        _platform_reference_request(capability="REFERRAL_MESSAGE_DELIVERY")
    )

    assert result.command_status == PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED
    assert result.blocked_reason == PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED
    assert result.provider_runtime_reference is None
    assert result.opaque_vault_reference is None
