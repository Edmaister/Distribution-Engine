from enum import Enum


class SettlementStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SETTLED = "SETTLED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"
    DISPUTED = "DISPUTED"


VALID_SETTLEMENT_STATUSES = {
    status.value
    for status in SettlementStatus
}