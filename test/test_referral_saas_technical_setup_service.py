from __future__ import annotations

from types import SimpleNamespace

from services import referral_saas_technical_setup_service as service


def test_referral_saas_technical_setup_readiness_blocks_without_email_provider(
    monkeypatch,
):
    monkeypatch.setattr(
        "services.channel_readiness_service.get_settings",
        lambda: SimpleNamespace(
            channel_email_provider_url=None,
            channel_email_provider_secret=None,
            channel_whatsapp_provider_url=None,
            channel_whatsapp_provider_secret=None,
            channel_sms_provider_url=None,
            channel_sms_provider_secret=None,
            channel_ussd_provider_url=None,
            channel_ussd_provider_secret=None,
        ),
    )

    readiness = service.build_referral_saas_technical_setup_readiness(
        account_id="acct-1",
        account_status="PENDING_ONBOARDING",
        tenant_link_status="PENDING_SETUP",
        external_reference_status="ACTIVE",
    ).to_safe_dict()

    invite_delivery = readiness["capabilities"][0]
    assert readiness["overallStatus"] == "PROVIDER_CONFIGURATION_REQUIRED"
    assert readiness["providerStatus"] == "ATTENTION"
    assert invite_delivery["code"] == "MEMBERSHIP_INVITE_DELIVERY"
    assert invite_delivery["status"] == "ATTENTION"
    assert invite_delivery["missingChannels"] == ["EMAIL"]
    assert "provider_secret" in readiness["redactions"]
    assert readiness["noCredentialCreationConfirmed"] is True
    assert readiness["noInviteDeliveryConfirmed"] is True
    assert readiness["noMembershipActivationConfirmed"] is True
    assert readiness["noMoneyMovementConfirmed"] is True


def test_referral_saas_technical_setup_readiness_reports_ready_when_channels_configured(
    monkeypatch,
):
    monkeypatch.setattr(
        "services.channel_readiness_service.get_settings",
        lambda: SimpleNamespace(
            channel_email_provider_url="https://channels.example/email",
            channel_email_provider_secret="email-secret",
            channel_email_provider_ref="email-provider-1",
            channel_email_provider_approved=True,
            channel_email_provider_scopes="REFERRAL_SAAS",
            channel_whatsapp_provider_url="https://channels.example/whatsapp",
            channel_whatsapp_provider_secret="whatsapp-secret",
            channel_sms_provider_url="https://channels.example/sms",
            channel_sms_provider_secret="sms-secret",
            channel_ussd_provider_url="https://channels.example/ussd",
            channel_ussd_provider_secret="ussd-secret",
        ),
    )

    readiness = service.build_referral_saas_technical_setup_readiness(
        account_id="acct-1",
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
    ).to_safe_dict()

    assert readiness["overallStatus"] == "READY"
    assert readiness["providerStatus"] == "READY"
    assert readiness["channelSummary"]["readyCount"] == 4
    assert readiness["channelSummary"]["approvedInviteProviderCount"] == 1
    assert readiness["capabilities"][0]["readyChannels"] == ["EMAIL"]
    assert readiness["capabilities"][0]["approvedProviderRefs"] == ["email-provider-1"]
    assert readiness["capabilities"][0]["missingApprovalChannels"] == []
    assert readiness["capabilities"][1]["readyChannels"] == [
        "WHATSAPP",
        "SMS",
        "USSD",
    ]


def test_referral_saas_technical_setup_readiness_requires_invite_provider_approval(
    monkeypatch,
):
    monkeypatch.setattr(
        "services.channel_readiness_service.get_settings",
        lambda: SimpleNamespace(
            channel_email_provider_url="https://channels.example/email",
            channel_email_provider_secret="email-secret",
            channel_email_provider_ref="email-provider-1",
            channel_email_provider_approved=False,
            channel_email_provider_scopes="",
            channel_whatsapp_provider_url="https://channels.example/whatsapp",
            channel_whatsapp_provider_secret="whatsapp-secret",
            channel_sms_provider_url="https://channels.example/sms",
            channel_sms_provider_secret="sms-secret",
            channel_ussd_provider_url="https://channels.example/ussd",
            channel_ussd_provider_secret="ussd-secret",
        ),
    )

    readiness = service.build_referral_saas_technical_setup_readiness(
        account_id="acct-1",
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
    ).to_safe_dict()

    invite_delivery = readiness["capabilities"][0]
    assert readiness["overallStatus"] == "PROVIDER_CONFIGURATION_REQUIRED"
    assert readiness["providerStatus"] == "ATTENTION"
    assert readiness["channelSummary"]["readyCount"] == 4
    assert readiness["channelSummary"]["approvedInviteProviderCount"] == 0
    assert invite_delivery["readyChannels"] == ["EMAIL"]
    assert invite_delivery["missingChannels"] == []
    assert invite_delivery["missingApprovalChannels"] == ["EMAIL"]
    assert invite_delivery["approvedProviderRefs"] == []


def test_referral_saas_technical_setup_readiness_keeps_account_posture_separate(
    monkeypatch,
):
    monkeypatch.setattr(
        "services.channel_readiness_service.get_settings",
        lambda: SimpleNamespace(
            channel_email_provider_url="https://channels.example/email",
            channel_email_provider_secret="email-secret",
            channel_email_provider_ref="email-provider-1",
            channel_email_provider_approved=True,
            channel_email_provider_scopes="REFERRAL_SAAS",
            channel_whatsapp_provider_url="https://channels.example/whatsapp",
            channel_whatsapp_provider_secret="whatsapp-secret",
            channel_sms_provider_url="https://channels.example/sms",
            channel_sms_provider_secret="sms-secret",
            channel_ussd_provider_url="https://channels.example/ussd",
            channel_ussd_provider_secret="ussd-secret",
        ),
    )

    readiness = service.build_referral_saas_technical_setup_readiness(
        account_id="acct-1",
        account_status="SUSPENDED",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
    ).to_safe_dict()

    assert readiness["overallStatus"] == "BLOCKED_BY_ACCOUNT_POSTURE"
    assert readiness["providerStatus"] == "READY"
    assert readiness["channelSummary"]["postureBlockers"] == ["ACCOUNT_NOT_READY"]
