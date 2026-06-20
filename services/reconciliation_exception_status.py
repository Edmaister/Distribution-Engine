from enum import Enum


class ReconciliationExceptionStatus(str, Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    REOPENED = "REOPENED"