from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FulfilmentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_FINAL = "FAILED_FINAL"
    DLQ = "DLQ"
    SKIPPED = "SKIPPED"
    SKIPPED_DUPLICATE = "SKIPPED_DUPLICATE"


@dataclass(frozen=True)
class FulfilmentRequest:
    tenant_code: str
    reward_id: str
    reward_type: str
    reward_value: float
    recipient_ucn: str | None = None
    currency: str | None = None
    journey_code: str | None = None
    milestone_code: str | None = None
    product_code: str | None = None
    provider_key: str | None = None
    execution_model: str | None = None
    funding_model: str | None = None
    settlement_model: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FulfilmentResult:
    status: FulfilmentStatus
    provider_reference: str | None = None
    message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class FulfilmentProvider(ABC):
    provider_key: str

    @abstractmethod
    async def fulfil(self, request: FulfilmentRequest) -> FulfilmentResult:
        raise NotImplementedError