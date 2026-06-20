from services.fulfilment_retry_policy_service import (
    DEFAULT_RETRY_POLICY,
    FulfilmentRetryPolicy,
    get_next_retry_delay_seconds,
    get_retry_policy,
    is_non_retryable_error,
    is_retryable_error,
    should_retry,
)


def test_get_retry_policy_returns_default_when_provider_missing():
    policy = get_retry_policy(None)

    assert policy == DEFAULT_RETRY_POLICY


def test_get_retry_policy_returns_default_for_unknown_provider():
    policy = get_retry_policy("UNKNOWN_PROVIDER")

    assert policy == DEFAULT_RETRY_POLICY


def test_get_retry_policy_is_case_insensitive():
    policy = get_retry_policy("cash_provider")

    assert policy.provider_key == "CASH_PROVIDER"
    assert policy.max_attempts == 3
    assert policy.backoff_seconds == 60


def test_get_retry_policy_cash_provider():
    policy = get_retry_policy("CASH_PROVIDER")

    assert policy.provider_key == "CASH_PROVIDER"
    assert policy.max_attempts == 3
    assert policy.backoff_seconds == 60


def test_get_retry_policy_voucher_provider():
    policy = get_retry_policy("VOUCHER_PROVIDER")

    assert policy.provider_key == "VOUCHER_PROVIDER"
    assert policy.max_attempts == 5
    assert policy.backoff_seconds == 30


def test_get_retry_policy_ebucks_provider():
    policy = get_retry_policy("EBUCKS_PROVIDER")

    assert policy.provider_key == "EBUCKS_PROVIDER"
    assert policy.max_attempts == 2
    assert policy.backoff_seconds == 300


def test_get_retry_policy_tenant_instruction_provider():
    policy = get_retry_policy("TENANT_INSTRUCTION_PROVIDER")

    assert policy.provider_key == "TENANT_INSTRUCTION_PROVIDER"
    assert policy.max_attempts == 1
    assert policy.backoff_seconds == 0
    assert policy.retryable_error_codes == set()


def test_is_non_retryable_error_true():
    policy = get_retry_policy("CASH_PROVIDER")

    assert is_non_retryable_error(
        policy=policy,
        error_code="INVALID_ACCOUNT",
    ) is True


def test_is_non_retryable_error_false_when_missing():
    policy = get_retry_policy("CASH_PROVIDER")

    assert is_non_retryable_error(
        policy=policy,
        error_code=None,
    ) is False


def test_is_non_retryable_error_false_when_retryable():
    policy = get_retry_policy("CASH_PROVIDER")

    assert is_non_retryable_error(
        policy=policy,
        error_code="TIMEOUT",
    ) is False


def test_is_retryable_error_true_for_known_retryable():
    policy = get_retry_policy("CASH_PROVIDER")

    assert is_retryable_error(
        policy=policy,
        error_code="TIMEOUT",
    ) is True


def test_is_retryable_error_true_when_missing_error_code():
    policy = get_retry_policy("CASH_PROVIDER")

    assert is_retryable_error(
        policy=policy,
        error_code=None,
    ) is True


def test_is_retryable_error_false_for_non_retryable():
    policy = get_retry_policy("CASH_PROVIDER")

    assert is_retryable_error(
        policy=policy,
        error_code="INVALID_ACCOUNT",
    ) is False


def test_is_retryable_error_false_for_unknown_error_code():
    policy = get_retry_policy("CASH_PROVIDER")

    assert is_retryable_error(
        policy=policy,
        error_code="UNKNOWN_ERROR",
    ) is False


def test_is_retryable_error_false_when_policy_has_no_retryables():
    policy = get_retry_policy("TENANT_INSTRUCTION_PROVIDER")

    assert is_retryable_error(
        policy=policy,
        error_code="TIMEOUT",
    ) is False


def test_should_retry_true_before_max_attempts():
    policy = get_retry_policy("CASH_PROVIDER")

    assert should_retry(
        policy=policy,
        attempt_no=2,
        error_code="TIMEOUT",
    ) is True


def test_should_retry_false_at_max_attempts():
    policy = get_retry_policy("CASH_PROVIDER")

    assert should_retry(
        policy=policy,
        attempt_no=3,
        error_code="TIMEOUT",
    ) is False


def test_should_retry_false_for_non_retryable_error():
    policy = get_retry_policy("CASH_PROVIDER")

    assert should_retry(
        policy=policy,
        attempt_no=1,
        error_code="INVALID_ACCOUNT",
    ) is False


def test_should_retry_false_for_unknown_error():
    policy = get_retry_policy("CASH_PROVIDER")

    assert should_retry(
        policy=policy,
        attempt_no=1,
        error_code="UNKNOWN_ERROR",
    ) is False


def test_should_retry_true_when_error_code_missing_and_attempt_available():
    policy = get_retry_policy("CASH_PROVIDER")

    assert should_retry(
        policy=policy,
        attempt_no=1,
        error_code=None,
    ) is True


def test_get_next_retry_delay_seconds_first_attempt():
    policy = get_retry_policy("CASH_PROVIDER")

    assert get_next_retry_delay_seconds(
        policy=policy,
        attempt_no=1,
    ) == 60


def test_get_next_retry_delay_seconds_second_attempt():
    policy = get_retry_policy("CASH_PROVIDER")

    assert get_next_retry_delay_seconds(
        policy=policy,
        attempt_no=2,
    ) == 120


def test_get_next_retry_delay_seconds_zero_attempt():
    policy = get_retry_policy("CASH_PROVIDER")

    assert get_next_retry_delay_seconds(
        policy=policy,
        attempt_no=0,
    ) == 60


def test_custom_policy_supported():
    policy = FulfilmentRetryPolicy(
        provider_key="CUSTOM",
        max_attempts=4,
        backoff_seconds=15,
        retryable_error_codes={"TEMP"},
        non_retryable_error_codes={"BAD"},
    )

    assert should_retry(
        policy=policy,
        attempt_no=1,
        error_code="TEMP",
    ) is True

    assert should_retry(
        policy=policy,
        attempt_no=1,
        error_code="BAD",
    ) is False