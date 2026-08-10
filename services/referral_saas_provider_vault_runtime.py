from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


PLATFORM_REFERENCE_PROVIDER_KEY = "PLATFORM_REFERENCE"
PLATFORM_REFERENCE_ADAPTER_REF = "PLATFORM_REFERENCE"
PLATFORM_VAULT_REFERENCE_ADAPTER_REF = "PLATFORM_VAULT_REFERENCE"
PLATFORM_REFERENCE_CAPABILITY = "REFERRAL_SAAS_PROVIDER_REFERENCE"
PLATFORM_REFERENCE_ENVIRONMENTS = frozenset({"SANDBOX", "STAGING", "PRODUCTION"})

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


def _opaque_reference(prefix: str, request: ProviderVaultRuntimeRequest) -> str:
    digest = hashlib.sha256(
        "|".join(
            [
                request.account_id,
                request.tenant_code,
                request.credential_request_ref,
                request.approved_request_version,
                request.provider_key.strip().upper(),
                request.environment.strip().upper(),
                request.capability.strip().upper(),
                request.command_payload_hash,
            ]
        ).encode("utf-8")
    ).hexdigest()[:32]
    return f"{prefix}_{digest}"


async def _platform_reference_adapter(
    request: ProviderVaultRuntimeRequest,
) -> ProviderVaultRuntimeResult:
    provider_reference = _opaque_reference("prv_ref", request)
    vault_reference = _opaque_reference("vault_ref", request)
    return ProviderVaultRuntimeResult(
        command_status=PROVIDER_VAULT_EXECUTION_READY,
        blocked_reason=None,
        next_action=(
            "Use the recorded opaque references as provider/vault readiness "
            "evidence. Vendor provider dispatch and managed vault execution "
            "remain separate governed workflows."
        ),
        plain_language_summary=(
            "Platform reference provider/vault references were recorded. No "
            "raw secret was accepted, no live provider was called, and no vault "
            "secret was written."
        ),
        provider_runtime_reference=provider_reference,
        opaque_vault_reference=vault_reference,
        adapter_ref=PLATFORM_REFERENCE_ADAPTER_REF,
        vault_adapter_ref=PLATFORM_VAULT_REFERENCE_ADAPTER_REF,
    )


def _builtin_adapter_for(
    *,
    provider_key: str,
    environment: str,
    capability: str,
) -> ProviderVaultRuntimeAdapter | None:
    provider, runtime_environment, runtime_capability = provider_vault_runtime_key(
        provider_key=provider_key,
        environment=environment,
        capability=capability,
    )
    if (
        provider == PLATFORM_REFERENCE_PROVIDER_KEY.lower()
        and runtime_environment in PLATFORM_REFERENCE_ENVIRONMENTS
        and runtime_capability == PLATFORM_REFERENCE_CAPABILITY
    ):
        return _platform_reference_adapter
    return None


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
    adapter_key = provider_vault_runtime_key(
        provider_key=request.provider_key,
        environment=request.environment,
        capability=request.capability,
    )
    adapter = _ADAPTERS.get(adapter_key) or _builtin_adapter_for(
        provider_key=request.provider_key,
        environment=request.environment,
        capability=request.capability,
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

    vault_adapter_ref = _VAULT_ADAPTER_REF
    if adapter is _platform_reference_adapter:
        vault_adapter_ref = vault_adapter_ref or PLATFORM_VAULT_REFERENCE_ADAPTER_REF

    if vault_adapter_ref is None:
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
        vault_adapter_ref=result.vault_adapter_ref or vault_adapter_ref,
    )


__all__ = [
    "PLATFORM_REFERENCE_ADAPTER_REF",
    "PLATFORM_REFERENCE_CAPABILITY",
    "PLATFORM_REFERENCE_ENVIRONMENTS",
    "PLATFORM_REFERENCE_PROVIDER_KEY",
    "PLATFORM_VAULT_REFERENCE_ADAPTER_REF",
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
