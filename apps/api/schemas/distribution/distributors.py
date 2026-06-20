from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CreateDistributorRequest(BaseModel):
    tenant_code: str
    distributor_code: str
    distributor_name: str
    distributor_type: str
    contact_email: str | None = None
    contact_phone: str | None = None
    channels: list[str] | None = None
    segments: list[str] | None = None
    regions: list[str] | None = None
    capabilities: dict[str, Any] | None = None
    eligibility: dict[str, Any] | None = None
    operating_limits: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class UpdateDistributorProfileRequest(BaseModel):
    distributor_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    channels: list[str] | None = None
    segments: list[str] | None = None
    regions: list[str] | None = None
    capabilities: dict[str, Any] | None = None
    eligibility: dict[str, Any] | None = None
    operating_limits: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
