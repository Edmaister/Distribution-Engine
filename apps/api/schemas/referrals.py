from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict


# -----------------------------
# Issue / Get-or-create code
# -----------------------------
class ReferralCodeIssue(BaseModel):
    referrer_ucn: str
    sticker: str
    tenant: str
    segment: str
    preferred_handle: Optional[str] = None

    accepted_terms: bool = Field(
        ...,
        alias="acceptedTerms",
        description="Referrer must accept terms before a referral code can be created."
    )


class ReferralCodeIssueResponse(BaseModel):
    referral_code: Optional[str] = Field(None, description="Issued referral code.")
    gaming_handle: Optional[str] = Field(None, description="Allocated handle.")
    created: bool = Field(..., description="True if a new code was created; false if existing returned.")
    message: Optional[str] = Field(None, description="Human-readable status message.")
    error_code: Optional[str] = Field(None, description="Preferred error format, null when no error.")


# -----------------------------
# Validate referral code
# -----------------------------
class ReferralValidate(BaseModel):
    tenant_code: str = Field(
        ...,
        alias="tenantCode",
        description="Tenant code for white-label routing and validation."
    )
    referral_code: str = Field(
        ...,
        alias="referralCode",
        description="Referral code scanned/entered by the user."
    )
    accepted_terms: bool = Field(
        ...,
        alias="acceptedTerms",
        description="Confirms the referred customer accepted the referral terms and conditions."
    )
    alias_value: Optional[str] = Field(
        None,
        alias="alias",
        description="Optional referee-chosen alias used for privacy-safe progress tracking. If omitted, a safe alias will be auto-generated."
    )
    device_fingerprint: Optional[str] = Field(
        None,
        alias="deviceFingerprint",
        description="Device fingerprint (scan telemetry)."
    )
    ip_address: Optional[str] = Field(
        None,
        alias="ipAddress",
        description="Client IP address (scan telemetry)."
    )
    qr_code: Optional[str] = Field(
        None,
        alias="qrCode",
        description="Raw QR payload (optional, for telemetry/audit)."
    )


class ReferralValidateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    valid: bool = Field(
        ...,
        description="True if the referral validation request passed all checks and a validated referral instance was created."
    )
    referral_track_id: Optional[str] = Field(
        None,
        alias="referralTrackId",
        description="Golden thread for the validated referral instance."
    )
    message: str = Field(
        ...,
        description="Human-readable outcome message."
    )
    error_code: Optional[str] = Field(
        None,
        alias="errorCode",
        description="Preferred error format, null when no error."
    )
    validation_outcome: str = Field(
        ...,
        alias="validationOutcome",
        description="High-level validation result."
    )
    alias_value: Optional[str] = Field(
        None,
        alias="alias",
        description="Final accepted alias linked to the validated referral instance, whether user-provided or auto-generated."
    )
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional fields for diagnostics and metadata, for example tenant_code, referrer_code_id, and aliasSource (USER_PROVIDED or AUTO_GENERATED)."
    )


# -----------------------------
# Capture referee UCN
# -----------------------------
class RefereeUCNCapture(BaseModel):
    referral_track_id: str = Field(..., description="Referral track id from validate response.")
    referee_ucn: str = Field(..., description="Referee's UCN (raw).")


class RefereeUCNCaptureResponse(BaseModel):
    message: str = Field(..., description="Outcome message.")
    referral_track_id: Optional[str] = Field(None, description="Referral track id that was updated.")
    error_code: Optional[str] = Field(None, description="Preferred error format, null when no error.")