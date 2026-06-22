from __future__ import annotations

import pytest

from services.fulfilment_safe_status import (
    map_fulfilment_status,
    map_settlement_status,
)


@pytest.mark.parametrize(
    ("raw_status", "operator_status", "external_status"),
    [
        ("PENDING", "PENDING", "PENDING"),
        ("PROCESSING", "IN_PROGRESS", "IN_PROGRESS"),
        ("SUCCESS", "FULFILLED", "FULFILLED"),
        ("FAILED_RETRYABLE", "RETRYABLE_FAILURE", "IN_PROGRESS"),
        ("FAILED_FINAL", "FAILED", "ACTION_REQUIRED"),
        ("DLQ", "ACTION_REQUIRED", "ACTION_REQUIRED"),
        ("SKIPPED_DUPLICATE", "DUPLICATE_NOOP", "FULFILLED"),
    ],
)
def test_fulfilment_status_maps_to_operator_and_external_safe_statuses(
    raw_status,
    operator_status,
    external_status,
):
    operator = map_fulfilment_status(raw_status, surface="operator")
    external = map_fulfilment_status(raw_status, surface="external")

    assert operator["domain"] == "fulfilment"
    assert operator["source_status"] == raw_status
    assert operator["detail_code"] == raw_status
    assert operator["status"] == operator_status

    assert external["domain"] == "fulfilment"
    assert external["status"] == external_status
    assert "source_status" not in external
    assert "detail_code" not in external


@pytest.mark.parametrize(
    ("raw_status", "operator_status", "external_status"),
    [
        ("PENDING", "PENDING", "PENDING"),
        ("PROCESSING", "IN_PROGRESS", "IN_PROGRESS"),
        ("SETTLED", "SETTLED", "SETTLED"),
        ("FAILED", "FAILED", "ACTION_REQUIRED"),
        ("REVERSED", "REVERSED", "ADJUSTED"),
        ("DISPUTED", "DISPUTED", "ACTION_REQUIRED"),
    ],
)
def test_settlement_status_maps_to_operator_and_external_safe_statuses(
    raw_status,
    operator_status,
    external_status,
):
    operator = map_settlement_status(raw_status, surface="operator")
    external = map_settlement_status(raw_status, surface="external")

    assert operator["domain"] == "settlement"
    assert operator["source_status"] == raw_status
    assert operator["detail_code"] == raw_status
    assert operator["status"] == operator_status

    assert external["domain"] == "settlement"
    assert external["status"] == external_status
    assert "source_status" not in external
    assert "detail_code" not in external


@pytest.mark.parametrize(
    "mapper",
    [map_fulfilment_status, map_settlement_status],
)
def test_unknown_statuses_are_safe_for_operator_and_external_surfaces(mapper):
    operator = mapper("PROVIDER_TIMEOUT", surface="operator")
    external = mapper("PROVIDER_TIMEOUT", surface="external")

    assert operator["status"] == "UNKNOWN"
    assert operator["source_status"] == "PROVIDER_TIMEOUT"
    assert operator["action_required"] is True

    assert external["status"] == "UNAVAILABLE"
    assert external["label"] == "Unavailable"
    assert external["action_required"] is False
    assert "PROVIDER_TIMEOUT" not in str(external)


@pytest.mark.parametrize(
    "raw_status",
    ["FAILED_RETRYABLE", "FAILED_FINAL", "DLQ", "REVERSED", "DISPUTED"],
)
def test_external_safe_statuses_do_not_leak_raw_internal_statuses(raw_status):
    fulfilment = map_fulfilment_status(raw_status, surface="external")
    settlement = map_settlement_status(raw_status, surface="external")

    assert raw_status not in str(fulfilment)
    assert raw_status not in str(settlement)
