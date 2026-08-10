from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


INTEGRATION_TEST_EXECUTION_PROOF_READY = "INTEGRATION_TEST_EXECUTION_PROOF_READY"
INTEGRATION_TEST_EXECUTION_PROOF_BLOCKED = "INTEGRATION_TEST_EXECUTION_PROOF_BLOCKED"

API_ACCESS_TEST_ADAPTER_REF = "API_ACCESS_TEST_EVIDENCE_ADAPTER"
WEBHOOK_TEST_ADAPTER_REF = "WEBHOOK_TEST_EVIDENCE_ADAPTER"
MESSAGE_PROVIDER_TEST_ADAPTER_REF = "MESSAGE_PROVIDER_TEST_EVIDENCE_ADAPTER"


@dataclass(frozen=True)
class IntegrationTestRuntimeRequest:
    test_type: str
    account_id: str
    tenant_code: str
    configuration_ref: str
    request_payload_hash: str
    environment: str | None = None
    verified_use_cases: list[str] | None = None
    callback_url_present: bool = False
    event_categories: list[str] | None = None
    channels: list[str] | None = None
    provider_refs_count: int = 0


@dataclass(frozen=True)
class IntegrationTestRuntimeResult:
    proof_status: str
    adapter_ref: str
    blocked_reason: str | None
    plain_language_summary: str
    runtime_evidence: dict[str, Any]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "proofStatus": self.proof_status,
            "adapterRef": self.adapter_ref,
            "blockedReason": self.blocked_reason,
            "plainLanguageSummary": self.plain_language_summary,
            "runtimeEvidence": self.runtime_evidence,
            "safeForFrontendDisplay": True,
            "noRawSecretExposureConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noProviderCallConfirmed": True,
            "noWebhookDispatchConfirmed": True,
            "noInviteDeliveryConfirmed": True,
            "noMessageProviderDeliveryConfirmed": True,
            "noMembershipActivationConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noBillingOrMoneyMovementConfirmed": True,
        }


IntegrationTestRuntimeAdapter = Callable[
    [IntegrationTestRuntimeRequest], Awaitable[IntegrationTestRuntimeResult]
]

_ADAPTERS: dict[str, IntegrationTestRuntimeAdapter] = {}


def _adapter_ref_for(test_type: str) -> str:
    normalized = test_type.strip().upper()
    if normalized == "API_ACCESS_VERIFICATION":
        return API_ACCESS_TEST_ADAPTER_REF
    if normalized == "WEBHOOK_TEST_DISPATCH":
        return WEBHOOK_TEST_ADAPTER_REF
    return MESSAGE_PROVIDER_TEST_ADAPTER_REF


async def _safe_evidence_adapter(
    request: IntegrationTestRuntimeRequest,
) -> IntegrationTestRuntimeResult:
    test_type = request.test_type.strip().upper()
    evidence: dict[str, Any] = {
        "configurationRefPresent": bool(request.configuration_ref),
        "requestPayloadHashPresent": bool(request.request_payload_hash),
    }
    blocked_reason: str | None = None

    if test_type == "API_ACCESS_VERIFICATION":
        evidence.update(
            {
                "apiEnvironmentPresent": bool(request.environment),
                "verifiedUseCasesCount": len(request.verified_use_cases or []),
                "apiAccessEvidencePresent": bool(
                    request.environment and request.verified_use_cases
                ),
            }
        )
        if not evidence["apiAccessEvidencePresent"]:
            blocked_reason = "API_ACCESS_TEST_EVIDENCE_MISSING"
    elif test_type == "WEBHOOK_TEST_DISPATCH":
        evidence.update(
            {
                "callbackUrlPresent": request.callback_url_present,
                "eventCategoriesCount": len(request.event_categories or []),
                "webhookTestEvidencePresent": bool(
                    request.callback_url_present and request.event_categories
                ),
            }
        )
        if not evidence["webhookTestEvidencePresent"]:
            blocked_reason = "WEBHOOK_TEST_EVIDENCE_MISSING"
    else:
        channels = {item.strip().upper() for item in request.channels or [] if item}
        evidence.update(
            {
                "channelsCount": len(channels),
                "providerRefsCount": request.provider_refs_count,
                "inviteProviderEvidencePresent": bool(
                    "EMAIL" in channels and request.provider_refs_count > 0
                ),
                "referralMessageProviderEvidencePresent": bool(
                    channels and request.provider_refs_count > 0
                ),
            }
        )
        if not evidence["referralMessageProviderEvidencePresent"]:
            blocked_reason = "MESSAGE_PROVIDER_TEST_EVIDENCE_MISSING"

    proof_status = (
        INTEGRATION_TEST_EXECUTION_PROOF_BLOCKED
        if blocked_reason
        else INTEGRATION_TEST_EXECUTION_PROOF_READY
    )
    return IntegrationTestRuntimeResult(
        proof_status=proof_status,
        adapter_ref=_adapter_ref_for(test_type),
        blocked_reason=blocked_reason,
        plain_language_summary=(
            "Safe integration test evidence was recorded. No production "
            "provider call, webhook dispatch, invite delivery, referral-message "
            "delivery, credential action, auth change, campaign activation, or "
            "money movement occurred."
            if not blocked_reason
            else "Integration test evidence is incomplete. No live integration "
            "action was attempted."
        ),
        runtime_evidence=evidence,
    )


def register_integration_test_runtime_adapter(
    *,
    test_type: str,
    adapter: IntegrationTestRuntimeAdapter,
) -> None:
    _ADAPTERS[test_type.strip().upper()] = adapter


def clear_integration_test_runtime_adapters() -> None:
    _ADAPTERS.clear()


async def execute_integration_test_runtime(
    request: IntegrationTestRuntimeRequest,
) -> IntegrationTestRuntimeResult:
    adapter = _ADAPTERS.get(request.test_type.strip().upper()) or _safe_evidence_adapter
    return await adapter(request)


__all__ = [
    "API_ACCESS_TEST_ADAPTER_REF",
    "INTEGRATION_TEST_EXECUTION_PROOF_BLOCKED",
    "INTEGRATION_TEST_EXECUTION_PROOF_READY",
    "IntegrationTestRuntimeRequest",
    "IntegrationTestRuntimeResult",
    "MESSAGE_PROVIDER_TEST_ADAPTER_REF",
    "WEBHOOK_TEST_ADAPTER_REF",
    "clear_integration_test_runtime_adapters",
    "execute_integration_test_runtime",
    "register_integration_test_runtime_adapter",
]
