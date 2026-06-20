from __future__ import annotations

from typing import Any

try:
    from utils.metrics import (
        fulfilment_success_inc,
        fulfilment_failed_inc,
        fulfilment_retry_inc,
        fulfilment_dlq_inc,
        fulfilment_duplicate_skipped_inc,
    )
except Exception:
    fulfilment_success_inc = None
    fulfilment_failed_inc = None
    fulfilment_retry_inc = None
    fulfilment_dlq_inc = None
    fulfilment_duplicate_skipped_inc = None


def _safe_call(metric_func: Any, **labels: Any) -> None:
    if not metric_func:
        return

    try:
        metric_func(**labels)
    except Exception:
        return


def record_fulfilment_success(
    *,
    tenant_code: str,
    reward_type: str,
    provider_key: str,
) -> None:
    _safe_call(
        fulfilment_success_inc,
        tenant_code=tenant_code,
        reward_type=reward_type,
        provider_key=provider_key,
    )


def record_fulfilment_failed(
    *,
    tenant_code: str,
    reward_type: str,
    provider_key: str,
    retryable: bool,
) -> None:
    _safe_call(
        fulfilment_failed_inc,
        tenant_code=tenant_code,
        reward_type=reward_type,
        provider_key=provider_key,
        retryable=str(retryable).lower(),
    )


def record_fulfilment_retry(
    *,
    tenant_code: str,
    reward_type: str,
    provider_key: str,
) -> None:
    _safe_call(
        fulfilment_retry_inc,
        tenant_code=tenant_code,
        reward_type=reward_type,
        provider_key=provider_key,
    )


def record_fulfilment_dlq(
    *,
    tenant_code: str,
    reward_type: str,
    provider_key: str,
) -> None:
    _safe_call(
        fulfilment_dlq_inc,
        tenant_code=tenant_code,
        reward_type=reward_type,
        provider_key=provider_key,
    )


def record_fulfilment_duplicate_skipped(
    *,
    tenant_code: str,
    reward_type: str,
    provider_key: str,
) -> None:
    _safe_call(
        fulfilment_duplicate_skipped_inc,
        tenant_code=tenant_code,
        reward_type=reward_type,
        provider_key=provider_key,
    )