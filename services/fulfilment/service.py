from __future__ import annotations

from services.dlq_service import publish_to_dlq
from services.fulfilment.base import (
    FulfilmentRequest,
    FulfilmentResult,
    FulfilmentStatus,
)
from services.fulfilment.factory import get_fulfilment_provider
from services.fulfilment.resolver import resolve_fulfilment_policy
from services.fulfilment_audit_service import (
    create_fulfilment_audit_record,
    get_existing_audit_by_idempotency_key,
    increment_fulfilment_attempt,
    mark_fulfilment_failed,
    mark_fulfilment_processing,
    mark_fulfilment_success,
)
from services.fulfilment_idempotency import build_fulfilment_idempotency_key
from services.fulfilment_metrics_service import (
    record_fulfilment_dlq,
    record_fulfilment_duplicate_skipped,
    record_fulfilment_failed,
    record_fulfilment_retry,
    record_fulfilment_success,
)

from services.fulfilment_circuit_breaker_service import (
    can_execute_provider,
    record_provider_failure,
    record_provider_success,
)

from services.fulfilment_retry_scheduler_service import (
    schedule_fulfilment_retry,
)
from services.fulfilment_retry_policy_service import (
    get_retry_policy,
    should_retry,
)
from services.fulfilment_provider_routing_service import resolve_provider
from services.fulfilment.settlement.service import record_pending_settlement
from services.funding.orchestrator import (
    reserve_reward_funding,
    release_reward_funding,
    settle_reward_funding,
)


async def fulfil_reward(
    request: FulfilmentRequest,
) -> FulfilmentResult:
    policy = await resolve_fulfilment_policy(
        tenant_code=request.tenant_code,
        reward_type=request.reward_type,
        journey_code=request.journey_code,
        product_code=request.product_code,
    )

    retry_policy = get_retry_policy(
        policy.provider_key,
    )

    idempotency_key = build_fulfilment_idempotency_key(
        tenant_code=request.tenant_code,
        referral_track_id=request.metadata.get("referral_track_id"),
        reward_type=request.reward_type,
        beneficiary_ucn=request.recipient_ucn,
        journey_stage=request.milestone_code,
    )

    existing = await get_existing_audit_by_idempotency_key(idempotency_key)

    if existing:
        record_fulfilment_duplicate_skipped(
            tenant_code=request.tenant_code,
            reward_type=request.reward_type,
            provider_key=policy.provider_key,
        )

        return FulfilmentResult(
            status=FulfilmentStatus.SKIPPED_DUPLICATE,
            provider_reference=existing.get("provider_reference"),
        )

    audit = await create_fulfilment_audit_record(
        tenant_code=request.tenant_code,
        referral_track_id=request.metadata.get("referral_track_id"),
        referrer_ucn=request.metadata.get("referrer_ucn"),
        referee_ucn=request.recipient_ucn,
        reward_type=request.reward_type,
        fulfilment_provider=policy.provider_key,
        idempotency_key=idempotency_key,
        correlation_id=request.reward_id,
        event_type="REWARD_FULFILMENT_REQUESTED",
        max_attempts=retry_policy.max_attempts,
    )

    audit_id = audit["audit_id"]

    await mark_fulfilment_processing(audit_id=audit_id)

    try:
        enriched_request = FulfilmentRequest(
            tenant_code=request.tenant_code,
            reward_id=request.reward_id,
            reward_type=request.reward_type,
            reward_value=request.reward_value,
            recipient_ucn=request.recipient_ucn,
            currency=request.currency,
            journey_code=request.journey_code,
            milestone_code=request.milestone_code,
            product_code=request.product_code,
            provider_key=policy.provider_key,
            execution_model=policy.execution_model,
            funding_model=policy.funding_model,
            settlement_model=policy.settlement_model,
            metadata={
                **request.metadata,
                "fulfilment_policy_id": policy.fulfilment_policy_id,
                "fulfilment_policy_metadata": policy.metadata,
                "idempotency_key": idempotency_key,
            },
        )

        routing = resolve_provider(policy.provider_key)

        if routing.reason == "NO_AVAILABLE_PROVIDER":
            raise RuntimeError(
                f"No available provider for: {policy.provider_key}"
            )

        provider = get_fulfilment_provider(
            routing.selected_provider_key
        )

        enriched_request = FulfilmentRequest(
            **{
                **enriched_request.__dict__,
                "provider_key": routing.selected_provider_key,
                "metadata": {
                    **enriched_request.metadata,
                    "requested_provider_key": routing.requested_provider_key,
                    "selected_provider_key": routing.selected_provider_key,
                    "provider_routing_reason": routing.reason,
                    "fallback_used": routing.fallback_used,
                },
            }
        )

        await reserve_reward_funding(
            reward_id=request.reward_id,
            tenant_code=request.tenant_code,
            amount=request.reward_value,
            correlation_id=audit_id,
        )

        result = await provider.fulfil(enriched_request)

        record_provider_success(routing.selected_provider_key)

        await mark_fulfilment_success(
            audit_id=audit_id,
            provider_reference=result.provider_reference,
            provider_status=result.status,
            provider_response={
                "status": result.status,
            },
        )

        await settle_reward_funding(
            reward_id=request.reward_id,
            correlation_id=audit_id,
        )

        await record_pending_settlement(
            tenant_code=request.tenant_code,
            reward_id=request.reward_id,
            audit_id=audit_id,
            provider_key=routing.selected_provider_key,
            provider_reference=result.provider_reference,
            amount=request.reward_value,
            currency=request.currency or "ZAR",
            period_id=getattr(request, "period_id", None),
        )

        record_fulfilment_success(
            tenant_code=request.tenant_code,
            reward_type=request.reward_type,
            provider_key=policy.provider_key,
        )

        return result

    except Exception as exc:
        failed_provider_key = (
            locals().get("routing").selected_provider_key
            if "routing" in locals()
            else policy.provider_key
        )

        try:
            await release_reward_funding(
                reward_id=request.reward_id,
                correlation_id=audit_id,
            )
        except Exception:
            pass

        record_provider_failure(failed_provider_key)

        attempt = await increment_fulfilment_attempt(
            audit_id=audit_id,
        )

        retryable = should_retry(
            policy=retry_policy,
            attempt_no=attempt["attempt_no"],
        )

        if retryable:
            record_fulfilment_retry(
                tenant_code=request.tenant_code,
                reward_type=request.reward_type,
                provider_key=policy.provider_key,
            )

            await schedule_fulfilment_retry(
                tenant_code=request.tenant_code,
                reward_id=request.reward_id,
                reward_type=request.reward_type,
                reward_value=request.reward_value,
                recipient_ucn=request.recipient_ucn,
                currency=request.currency,
                journey_code=request.journey_code,
                milestone_code=request.milestone_code,
                product_code=request.product_code,
                audit_id=audit_id,
                idempotency_key=idempotency_key,
                attempt_no=attempt["attempt_no"],
                max_attempts=attempt["max_attempts"],
                policy=retry_policy,
                failure_reason=str(exc),
                metadata=request.metadata,
            )

        await mark_fulfilment_failed(
            audit_id=audit_id,
            failure_reason=str(exc),
            retryable=retryable,
        )

        record_fulfilment_failed(
            tenant_code=request.tenant_code,
            reward_type=request.reward_type,
            provider_key=policy.provider_key,
            retryable=retryable,
        )

        if not retryable:
            record_fulfilment_dlq(
                tenant_code=request.tenant_code,
                reward_type=request.reward_type,
                provider_key=policy.provider_key,
            )

            await publish_to_dlq(
                event={
                    "eventType": "REWARD_FULFILMENT_REQUESTED",
                    "rewardId": request.reward_id,
                    "tenantCode": request.tenant_code,
                    "rewardType": request.reward_type,
                    "recipientUcn": request.recipient_ucn,
                    "idempotencyKey": idempotency_key,
                    "auditId": audit_id,
                    "attemptNo": attempt["attempt_no"],
                    "maxAttempts": attempt["max_attempts"],
                },
                error=str(exc),
            )

        raise
