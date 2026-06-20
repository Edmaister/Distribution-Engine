from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FulfilmentRetryPolicy:
    provider_key: str
    max_attempts: int
    backoff_seconds: int
    retryable_error_codes: set[str]
    non_retryable_error_codes: set[str]


DEFAULT_RETRY_POLICY = FulfilmentRetryPolicy(
    provider_key="DEFAULT",
    max_attempts=3,
    backoff_seconds=60,
    retryable_error_codes={
        "TIMEOUT",
        "PROVIDER_UNAVAILABLE",
        "RATE_LIMITED",
        "TEMPORARY_FAILURE",
    },
    non_retryable_error_codes={
        "INVALID_ACCOUNT",
        "INVALID_RECIPIENT",
        "INVALID_REWARD",
        "CONFIGURATION_ERROR",
    },
)


PROVIDER_RETRY_POLICIES = {
    "CASH_PROVIDER": FulfilmentRetryPolicy(
        provider_key="CASH_PROVIDER",
        max_attempts=3,
        backoff_seconds=60,
        retryable_error_codes=DEFAULT_RETRY_POLICY.retryable_error_codes,
        non_retryable_error_codes=DEFAULT_RETRY_POLICY.non_retryable_error_codes,
    ),
    "VOUCHER_PROVIDER": FulfilmentRetryPolicy(
        provider_key="VOUCHER_PROVIDER",
        max_attempts=5,
        backoff_seconds=30,
        retryable_error_codes=DEFAULT_RETRY_POLICY.retryable_error_codes,
        non_retryable_error_codes=DEFAULT_RETRY_POLICY.non_retryable_error_codes,
    ),
    "EBUCKS_PROVIDER": FulfilmentRetryPolicy(
        provider_key="EBUCKS_PROVIDER",
        max_attempts=2,
        backoff_seconds=300,
        retryable_error_codes=DEFAULT_RETRY_POLICY.retryable_error_codes,
        non_retryable_error_codes=DEFAULT_RETRY_POLICY.non_retryable_error_codes,
    ),
    "TENANT_INSTRUCTION_PROVIDER": FulfilmentRetryPolicy(
        provider_key="TENANT_INSTRUCTION_PROVIDER",
        max_attempts=1,
        backoff_seconds=0,
        retryable_error_codes=set(),
        non_retryable_error_codes=DEFAULT_RETRY_POLICY.non_retryable_error_codes,
    ),
}


def get_retry_policy(
    provider_key: str | None,
) -> FulfilmentRetryPolicy:
    if not provider_key:
        return DEFAULT_RETRY_POLICY

    return PROVIDER_RETRY_POLICIES.get(
        provider_key.upper(),
        DEFAULT_RETRY_POLICY,
    )


def is_non_retryable_error(
    *,
    policy: FulfilmentRetryPolicy,
    error_code: str | None,
) -> bool:
    if not error_code:
        return False

    return error_code.upper() in policy.non_retryable_error_codes


def is_retryable_error(
    *,
    policy: FulfilmentRetryPolicy,
    error_code: str | None,
) -> bool:
    if not error_code:
        return True

    if error_code.upper() in policy.non_retryable_error_codes:
        return False

    if not policy.retryable_error_codes:
        return False

    return error_code.upper() in policy.retryable_error_codes


def should_retry(
    *,
    policy: FulfilmentRetryPolicy,
    attempt_no: int,
    error_code: str | None = None,
) -> bool:
    if is_non_retryable_error(
        policy=policy,
        error_code=error_code,
    ):
        return False

    if not is_retryable_error(
        policy=policy,
        error_code=error_code,
    ):
        return False

    return attempt_no < policy.max_attempts


def get_next_retry_delay_seconds(
    *,
    policy: FulfilmentRetryPolicy,
    attempt_no: int,
) -> int:
    if attempt_no <= 0:
        return policy.backoff_seconds

    return policy.backoff_seconds * attempt_no