from datetime import datetime, timezone, timedelta

from services.fulfilment_circuit_breaker_service import (
    CircuitState,
    can_execute_provider,
    get_circuit,
    get_circuit_snapshot,
    record_provider_failure,
    record_provider_success,
    reset_all_circuits,
    reset_circuit,
)


def setup_function():
    reset_all_circuits()


def test_get_circuit_creates_default_closed_circuit():
    circuit = get_circuit("cash_provider")

    assert circuit.provider_key == "CASH_PROVIDER"
    assert circuit.state == CircuitState.CLOSED
    assert circuit.failure_count == 0
    assert circuit.failure_threshold == 5
    assert circuit.opened_at is None
    assert circuit.cooldown_seconds == 300


def test_reset_circuit_resets_state():
    record_provider_failure("CASH_PROVIDER")
    circuit = reset_circuit("CASH_PROVIDER")

    assert circuit.provider_key == "CASH_PROVIDER"
    assert circuit.state == CircuitState.CLOSED
    assert circuit.failure_count == 0
    assert circuit.opened_at is None


def test_can_execute_provider_when_closed():
    assert can_execute_provider(provider_key="CASH_PROVIDER") is True


def test_record_provider_failure_increments_count():
    circuit = record_provider_failure("CASH_PROVIDER")

    assert circuit.failure_count == 1
    assert circuit.state == CircuitState.CLOSED


def test_record_provider_failure_opens_circuit_at_threshold():
    now = datetime(2026, 5, 29, 12, 0, 0, tzinfo=timezone.utc)

    for _ in range(5):
        circuit = record_provider_failure("CASH_PROVIDER", now=now)

    assert circuit.failure_count == 5
    assert circuit.state == CircuitState.OPEN
    assert circuit.opened_at == now


def test_can_execute_provider_when_open_before_cooldown():
    now = datetime(2026, 5, 29, 12, 0, 0, tzinfo=timezone.utc)

    for _ in range(5):
        record_provider_failure("CASH_PROVIDER", now=now)

    assert can_execute_provider(
        provider_key="CASH_PROVIDER",
        now=now + timedelta(seconds=299),
    ) is False


def test_can_execute_provider_transitions_to_half_open_after_cooldown():
    opened_at = datetime(2026, 5, 29, 12, 0, 0, tzinfo=timezone.utc)

    for _ in range(5):
        record_provider_failure("CASH_PROVIDER", now=opened_at)

    assert can_execute_provider(
        provider_key="CASH_PROVIDER",
        now=opened_at + timedelta(seconds=300),
    ) is True

    circuit = get_circuit("CASH_PROVIDER")

    assert circuit.state == CircuitState.HALF_OPEN


def test_can_execute_provider_when_half_open():
    circuit = get_circuit("CASH_PROVIDER")
    circuit.state = CircuitState.HALF_OPEN

    assert can_execute_provider(provider_key="CASH_PROVIDER") is True


def test_can_execute_provider_when_open_without_opened_at():
    circuit = get_circuit("CASH_PROVIDER")
    circuit.state = CircuitState.OPEN
    circuit.opened_at = None

    assert can_execute_provider(provider_key="CASH_PROVIDER") is False


def test_record_provider_success_closes_and_resets_circuit():
    for _ in range(5):
        record_provider_failure("CASH_PROVIDER")

    circuit = record_provider_success("CASH_PROVIDER")

    assert circuit.state == CircuitState.CLOSED
    assert circuit.failure_count == 0
    assert circuit.opened_at is None


def test_get_circuit_snapshot():
    opened_at = datetime(2026, 5, 29, 12, 0, 0, tzinfo=timezone.utc)

    for _ in range(5):
        record_provider_failure("CASH_PROVIDER", now=opened_at)

    snapshot = get_circuit_snapshot("CASH_PROVIDER")

    assert snapshot == {
        "provider_key": "CASH_PROVIDER",
        "state": "OPEN",
        "failure_count": 5,
        "failure_threshold": 5,
        "opened_at": "2026-05-29T12:00:00+00:00",
        "cooldown_seconds": 300,
    }


def test_reset_all_circuits_clears_state():
    record_provider_failure("CASH_PROVIDER")

    reset_all_circuits()

    circuit = get_circuit("CASH_PROVIDER")

    assert circuit.failure_count == 0
    assert circuit.state == CircuitState.CLOSED