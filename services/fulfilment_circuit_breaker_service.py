from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitBreakerState:
    provider_key: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    failure_threshold: int = 5
    opened_at: datetime | None = None
    cooldown_seconds: int = 300


_CIRCUITS: dict[str, CircuitBreakerState] = {}


def get_circuit(
    provider_key: str,
) -> CircuitBreakerState:
    key = provider_key.upper()

    if key not in _CIRCUITS:
        _CIRCUITS[key] = CircuitBreakerState(
            provider_key=key,
        )

    return _CIRCUITS[key]


def reset_circuit(
    provider_key: str,
) -> CircuitBreakerState:
    key = provider_key.upper()

    _CIRCUITS[key] = CircuitBreakerState(
        provider_key=key,
    )

    return _CIRCUITS[key]


def can_execute_provider(
    *,
    provider_key: str,
    now: datetime | None = None,
) -> bool:
    circuit = get_circuit(provider_key)
    current_time = now or datetime.now(timezone.utc)

    if circuit.state == CircuitState.CLOSED:
        return True

    if circuit.state == CircuitState.HALF_OPEN:
        return True

    if circuit.state == CircuitState.OPEN:
        if not circuit.opened_at:
            return False

        elapsed = current_time - circuit.opened_at

        if elapsed >= timedelta(seconds=circuit.cooldown_seconds):
            circuit.state = CircuitState.HALF_OPEN
            return True

        return False

    return False


def record_provider_success(
    provider_key: str,
) -> CircuitBreakerState:
    circuit = get_circuit(provider_key)

    circuit.state = CircuitState.CLOSED
    circuit.failure_count = 0
    circuit.opened_at = None

    return circuit


def record_provider_failure(
    provider_key: str,
    *,
    now: datetime | None = None,
) -> CircuitBreakerState:
    circuit = get_circuit(provider_key)
    current_time = now or datetime.now(timezone.utc)

    circuit.failure_count += 1

    if circuit.failure_count >= circuit.failure_threshold:
        circuit.state = CircuitState.OPEN
        circuit.opened_at = current_time

    return circuit


def get_circuit_snapshot(
    provider_key: str,
) -> dict:
    circuit = get_circuit(provider_key)

    return {
        "provider_key": circuit.provider_key,
        "state": circuit.state.value,
        "failure_count": circuit.failure_count,
        "failure_threshold": circuit.failure_threshold,
        "opened_at": circuit.opened_at.isoformat() if circuit.opened_at else None,
        "cooldown_seconds": circuit.cooldown_seconds,
    }


def reset_all_circuits() -> None:
    _CIRCUITS.clear()