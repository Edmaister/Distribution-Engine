from datetime import datetime, timezone

import pytest

from services.referral_saas_operational_service_target_service import (
    ServiceTargetPolicyValidationError,
    _normalise_code,
    _validate_policy_values,
    hash_request_payload,
)


def test_policy_codes_are_canonical_and_payload_hash_is_stable():
    assert _normalise_code("support case", "workType") == "SUPPORT_CASE"
    assert hash_request_payload({"b": 2, "a": 1}) == hash_request_payload({"a": 1, "b": 2})


@pytest.mark.parametrize(
    ("target", "warning"),
    [(0, 0), (30, -1), (30, 30), (30, 31)],
)
def test_policy_duration_and_warning_threshold_fail_closed(target: int, warning: int):
    with pytest.raises(ServiceTargetPolicyValidationError):
        _validate_policy_values(
            business_timezone="UTC",
            target_duration_minutes=target,
            warning_threshold_minutes=warning,
            effective_from=datetime(2026, 8, 22, tzinfo=timezone.utc),
            effective_to=None,
            approved_pause_reasons=[],
        )


def test_policy_requires_timezone_aware_effective_window():
    with pytest.raises(ServiceTargetPolicyValidationError, match="timezone offset"):
        _validate_policy_values(
            business_timezone="UTC",
            target_duration_minutes=120,
            warning_threshold_minutes=30,
            effective_from=datetime(2026, 8, 22),
            effective_to=None,
            approved_pause_reasons=[],
        )


def test_policy_rejects_unknown_business_timezone():
    with pytest.raises(ServiceTargetPolicyValidationError, match="IANA timezone"):
        _validate_policy_values(
            business_timezone="South Africa Time",
            target_duration_minutes=120,
            warning_threshold_minutes=30,
            effective_from=datetime(2026, 8, 22, tzinfo=timezone.utc),
            effective_to=None,
            approved_pause_reasons=[],
        )
