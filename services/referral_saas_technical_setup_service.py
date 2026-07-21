from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.channel_readiness_service import get_channel_readiness


TECHNICAL_SETUP_GUARDRAILS = (
    "READ_ONLY_TECHNICAL_SETUP_READINESS",
    "NO_PROVIDER_SECRET_EXPOSURE",
    "NO_CREDENTIAL_CREATION",
    "NO_WEBHOOK_DISPATCH",
    "NO_INVITE_DELIVERY",
    "NO_MEMBERSHIP_ACTIVATION",
    "NO_AUTH_CLAIM_CHANGE",
    "NO_SEAT_ASSIGNMENT",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_GO_LIVE_ACTION",
    "NO_MONEY_MOVEMENT",
)

TECHNICAL_SETUP_REDACTIONS = (
    "internal_tenant_identifier",
    "provider_secret",
    "raw_recipient",
    "email_hash",
)


@dataclass(frozen=True)
class ReferralSaasTechnicalSetupCapability:
    code: str
    label: str
    status: str
    required_channels: tuple[str, ...]
    ready_channels: tuple[str, ...]
    missing_channels: tuple[str, ...]
    approved_provider_refs: tuple[str, ...]
    missing_approval_channels: tuple[str, ...]
    next_action: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "label": self.label,
            "status": self.status,
            "requiredChannels": list(self.required_channels),
            "readyChannels": list(self.ready_channels),
            "missingChannels": list(self.missing_channels),
            "approvedProviderRefs": list(self.approved_provider_refs),
            "missingApprovalChannels": list(self.missing_approval_channels),
            "nextAction": self.next_action,
        }


@dataclass(frozen=True)
class ReferralSaasTechnicalSetupReadiness:
    account_id: str
    overall_status: str
    provider_status: str
    channel_summary: dict[str, Any]
    capabilities: tuple[ReferralSaasTechnicalSetupCapability, ...]
    guardrails: tuple[str, ...] = TECHNICAL_SETUP_GUARDRAILS
    redactions: tuple[str, ...] = TECHNICAL_SETUP_REDACTIONS

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "accountId": self.account_id,
            "overallStatus": self.overall_status,
            "providerStatus": self.provider_status,
            "channelSummary": self.channel_summary,
            "capabilities": [capability.to_safe_dict() for capability in self.capabilities],
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noCredentialCreationConfirmed": True,
            "noWebhookDispatchConfirmed": True,
            "noInviteDeliveryConfirmed": True,
            "noMembershipActivationConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noMoneyMovementConfirmed": True,
        }


def build_referral_saas_technical_setup_readiness(
    *,
    account_id: str,
    account_status: str,
    tenant_link_status: str | None,
    external_reference_status: str | None,
) -> ReferralSaasTechnicalSetupReadiness:
    channel_readiness = get_channel_readiness()
    channels_by_code = {
        str(item["channel_code"]).upper(): item for item in channel_readiness["items"]
    }
    capabilities = (
        _capability(
            code="MEMBERSHIP_INVITE_DELIVERY",
            label="People invite delivery",
            required_channels=("EMAIL",),
            channels_by_code=channels_by_code,
            requires_referral_saas_approval=True,
            next_action_when_ready="Email provider is configured and approved for Referral SaaS. Delivery still requires the guarded invite-delivery command.",
            next_action_when_blocked="Configure and approve the Email provider for Referral SaaS before sending account access invites.",
        ),
        _capability(
            code="REFERRAL_JOURNEY_MESSAGES",
            label="Referral journey messages",
            required_channels=("WHATSAPP", "SMS", "USSD"),
            channels_by_code=channels_by_code,
            requires_referral_saas_approval=False,
            next_action_when_ready="Journey channels are configured. Campaign setup can choose the correct channel later.",
            next_action_when_blocked="Configure at least one journey channel before live customer messaging.",
        ),
    )
    provider_status = (
        "READY"
        if all(capability.status == "READY" for capability in capabilities)
        else "ATTENTION"
    )
    posture_blockers = _posture_blockers(
        account_status=account_status,
        tenant_link_status=tenant_link_status,
        external_reference_status=external_reference_status,
    )
    overall_status = (
        "BLOCKED_BY_ACCOUNT_POSTURE"
        if posture_blockers
        else "READY"
        if provider_status == "READY"
        else "PROVIDER_CONFIGURATION_REQUIRED"
    )

    return ReferralSaasTechnicalSetupReadiness(
        account_id=account_id,
        overall_status=overall_status,
        provider_status=provider_status,
        channel_summary={
            "count": channel_readiness["summary"]["count"],
            "readyCount": channel_readiness["summary"]["ready_count"],
            "attentionCount": channel_readiness["summary"]["attention_count"],
            "supportedChannels": channel_readiness["summary"]["supported_channels"],
            "approvedInviteProviderCount": len(capabilities[0].approved_provider_refs),
            "postureBlockers": posture_blockers,
        },
        capabilities=capabilities,
    )


def _capability(
    *,
    code: str,
    label: str,
    required_channels: tuple[str, ...],
    channels_by_code: dict[str, dict[str, Any]],
    requires_referral_saas_approval: bool,
    next_action_when_ready: str,
    next_action_when_blocked: str,
) -> ReferralSaasTechnicalSetupCapability:
    ready_channels = tuple(
        channel
        for channel in required_channels
        if channels_by_code.get(channel, {}).get("provider_configured") is True
    )
    missing_channels = tuple(
        channel for channel in required_channels if channel not in ready_channels
    )
    approved_provider_refs = tuple(
        str(channels_by_code[channel].get("provider_ref") or channel)
        for channel in required_channels
        if channels_by_code.get(channel, {}).get("approved_for_referral_saas") is True
    )
    missing_approval_channels = (
        tuple(
            channel
            for channel in required_channels
            if channel in ready_channels
            and channels_by_code.get(channel, {}).get("approved_for_referral_saas")
            is not True
        )
        if requires_referral_saas_approval
        else ()
    )
    is_ready = not missing_channels and not missing_approval_channels
    return ReferralSaasTechnicalSetupCapability(
        code=code,
        label=label,
        status="READY" if is_ready else "ATTENTION",
        required_channels=required_channels,
        ready_channels=ready_channels,
        missing_channels=missing_channels,
        approved_provider_refs=approved_provider_refs,
        missing_approval_channels=missing_approval_channels,
        next_action=next_action_when_ready
        if is_ready
        else next_action_when_blocked,
    )


def _posture_blockers(
    *,
    account_status: str,
    tenant_link_status: str | None,
    external_reference_status: str | None,
) -> list[str]:
    blockers: list[str] = []
    if str(account_status or "").upper() not in {"ACTIVE", "PENDING_ONBOARDING"}:
        blockers.append("ACCOUNT_NOT_READY")
    if str(tenant_link_status or "").upper() not in {"ACTIVE", "PENDING_SETUP"}:
        blockers.append("TENANT_LINK_NOT_READY")
    if str(external_reference_status or "").upper() != "ACTIVE":
        blockers.append("EXTERNAL_REFERENCE_NOT_ACTIVE")
    return blockers
