from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class EnterpriseEventIngestRequest(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    event_type: str = Field(..., alias="eventType")
    source: Optional[str] = None
    source_system: Optional[str] = Field(None, alias="sourceSystem")
    source_event_id: Optional[str] = Field(None, alias="sourceEventId")
    tenant_code: Optional[str] = Field(None, alias="tenantCode")
    referral_track_id: Optional[str] = Field(None, alias="referralTrackId")
    correlation_id: Optional[str] = Field(None, alias="correlationId")
    occurred_at: Optional[Any] = Field(None, alias="occurredAt")


class EnterpriseEventIngestResponse(BaseModel):
    status: str
    processingStatus: str
    eventType: str
    progressEventType: Optional[str] = None
    journeyCode: Optional[str] = None
    journeyVersion: Optional[str] = None
    dedupeKey: str
    queued: bool
