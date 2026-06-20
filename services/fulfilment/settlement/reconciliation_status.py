from enum import Enum


class ReconciliationStatus(str, Enum):
    MATCHED = "MATCHED"
    MISSING = "MISSING"
    DUPLICATE = "DUPLICATE"
    OVERPAID = "OVERPAID"
    UNDERPAID = "UNDERPAID"