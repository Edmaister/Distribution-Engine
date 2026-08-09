from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


PROVIDER_VAULT_EXECUTION_READY = "PROVIDER_VAULT_EXECUTION_READY"
PROVIDER_VAULT_BLOCKED_VAULT_NOT_CONFIGURED = (
    "PROVIDER_VAULT_BLOCKED_VAULT_NOT_CONFIGURED"
)
PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED = (
    "PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED"
)


@dataclass(frozen=True)
class ProviderVaultRuntimeRequest:
    account_id: str
    tenant_code: str
    credential_request_ref: str
    approved_request_version: str
    execution_intent: str
    execution_mode: str
    provider_key: str
    environment: str
    capability: str
    reason_code: str
    command_payload_hash: str
    actor_ref: str
    actor_role: str | None


@dataclass(frozen=True)
class ProviderVaultRuntimeResult:
    command_status: str
    blocked_reason: str | None
    next_action: str
    plain_language_summary: str
    provider_runtime_reference: str | None = None
    opaque_vault_reference: str | None = None
    adapter_ref: str | None = None
    vault_adapter_ref: str | None = None


ProviderVaultRuntimeAdapter = Callable[
    [ProviderVaultRuntimeRequest], Awaitable[ProviderVaultRuntimeResult]
]

_ADAPTERS: dict[tuple[str, str, str], ProviderVaultRuntimeAdapter] = {}
_VAULT_ADAPTER_REF: str | None = None


def provider_vault_runtime_key(
    *,
    provider_key: str,
    environment: str,
    capability: str,
) -> tuple[str, str, str]:
    return (provider_key.strip().lower(), environment.strip().upper(), capability.strip().upper())


def configure_provider_vault_runtime(
    *,
    vault_adapter_ref: str | None = None,
) -> None:
    global _VAULT_ADAPTER_REF
    _VAULT_ADAPTER_REF = vault_adapter_ref.strip() if vault_adapter_ref else None


def register_provider_vault_runtime_adapter(
    *,
    provider_key: str,
    environment: str,
    capability: str,
    adapter: ProviderVaultRuntimeAdapter,
) -> None:
    _ADAPTERS[
        provider_vault_runtime_key(
            provider_key=provider_key,
            environment=environment,
            capability=capability,
        )
    ] = adapter


def clear_provider_vault_runtime_adapters() -> None:
    _ADAPTERS.clear()
    configure_provider_vault_runtime(vault_adapter_ref=None)


async def execute_provider_vault_runtime(
    request: ProviderVaultRuntimeRequest,
) -> ProviderVaultRuntimeResult:
    adapter = _ADAPTERS.get(
        provider_vault_runtime_key(
            provider_key=request.provider_key,
            environment=request.environment,
            capability=request.capability,
        )
    )
    if adapter is None:
        return ProviderVaultRuntimeResult(
            command_status=PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED,
            blocked_reason=PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED,
            next_action=(
                "Configure an approved runtime adapter for this provider, "
                "environment, and capability before execution can run."
            ),
            plain_language_summary=(
                "Provider/vault execution gates passed, but no approved runtime "
                "adapter is configured for this provider. No provider was called, "
                "no vault was written, and no secret was exposed."
            ),
        )

    if _VAULT_ADAPTER_REF is None:
        return ProviderVaultRuntimeResult(
            command_status=PROVIDER_VAULT_BLOCKED_VAULT_NOT_CONFIGURED,
            blocked_reason=PROVIDER_VAULT_BLOCKED_VAULT_NOT_CONFIGURED,
            next_action=(
                "Configure an approved vault adapter before provider credential "
                "references can be recorded."
            ),
            plain_language_summary=(
                "Provider/vault execution gates passed, but no approved vault "
                "adapter is configured. No provider was called, no vault was "
                "written, and no secret was exposed."
            ),
        )

    result = await adapter(request)
    if result.command_status != PROVIDER_VAULT_EXECUTION_READY:
        return result

    return ProviderVaultRuntimeResult(
        command_status=result.command_status,
        blocked_reason=result.blocked_reason,
        next_action=result.next_action,
        plain_language_summary=result.plain_language_summary,
        provider_runtime_reference=result.provider_runtime_reference,
        opaque_vault_reference=result.opaque_vault_reference,
        adapter_ref=result.adapter_ref,
        vault_adapter_ref=result.vault_adapter_ref or _VAULT_ADAPTER_REF,
    )


__all__ = [
    "PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED",
    "PROVIDER_VAULT_BLOCKED_VAULT_NOT_CONFIGURED",
    "PROVIDER_VAULT_EXECUTION_READY",
    "ProviderVaultRuntimeRequest",
    "ProviderVaultRuntimeResult",
    "clear_provider_vault_runtime_adapters",
    "configure_provider_vault_runtime",
    "execute_provider_vault_runtime",
    "register_provider_vault_runtime_adapter",
]
