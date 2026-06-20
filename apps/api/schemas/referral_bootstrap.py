from typing import Optional
from pydantic import BaseModel, Field


class ReferralBootstrapRequest(BaseModel):
    referrerUcn: str = Field(..., min_length=1)
    tenantCode: str = Field(..., min_length=1)


class ReferralBootstrapResponse(BaseModel):
    referrerUcn: str
    tenantCode: str
    exists: bool
    referralCode: Optional[str] = None
    alias: Optional[str] = None
    acceptedTerms: bool
    requiresTermsAcceptance: bool
    qrEligible: bool
    message: str


class AcceptTermsRequest(BaseModel):
    referrerUcn: str = Field(..., min_length=1)
    tenantCode: str = Field(..., min_length=1)


class AcceptTermsResponse(BaseModel):
    referrerUcn: str
    tenantCode: str
    acceptedTerms: bool
    acceptedTermsAt: Optional[str] = None
    message: str