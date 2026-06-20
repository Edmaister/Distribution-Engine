from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class CreateComplianceReviewRequest(BaseModel):
    distributor_id: str
    review_type: str
    reviewer: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] | None = None


class CompleteComplianceReviewRequest(BaseModel):
    review_result: str
    reviewer: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] | None = None


class ComplianceReviewResponse(BaseModel):
    review_id: UUID
    tenant_code: str
    distributor_id: UUID
    distributor_code: str
    review_type: str
    review_status: str
    review_result: str | None = None
    reviewer: str | None = None
    notes: str | None = None
    metadata: dict[str, Any]
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CreateDisputeRequest(BaseModel):
    route_id: str
    raised_by: str
    reason_code: str
    description: str | None = None
    metadata: dict[str, Any] | None = None


class ResolveDisputeRequest(BaseModel):
    dispute_status: str = "RESOLVED"
    resolved_by: str | None = None
    resolution_notes: str | None = None
    metadata: dict[str, Any] | None = None


class DisputeResponse(BaseModel):
    dispute_id: UUID
    tenant_code: str
    route_id: UUID | None = None
    opportunity_id: UUID | None = None
    distributor_id: UUID | None = None
    raised_by: str
    reason_code: str
    description: str | None = None
    dispute_status: str
    resolution_notes: str | None = None
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class DistributorGovernanceActionRequest(BaseModel):
    action_type: str
    reason_code: str | None = None
    actor: str | None = None
    notes: str | None = None
    operating_limits: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class GovernanceAuditResponse(BaseModel):
    audit_id: UUID
    tenant_code: str
    distributor_id: UUID | None = None
    route_id: UUID | None = None
    dispute_id: UUID | None = None
    compliance_review_id: UUID | None = None
    action_type: str
    reason_code: str | None = None
    actor: str | None = None
    notes: str | None = None
    before_state: dict[str, Any]
    after_state: dict[str, Any]
    metadata: dict[str, Any]
    created_at: datetime


class DistributorGovernanceActionResponse(BaseModel):
    distributor: dict[str, Any]
    audit: GovernanceAuditResponse
