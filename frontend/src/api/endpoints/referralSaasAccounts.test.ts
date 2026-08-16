import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest } from "../client";
import {
  addReferralSaasAccountSupportCaseNote,
  changeReferralSaasAccountSupportCaseStatus,
  createReferralSaasAccountSupportCase,
  createReferralSaasAccountCampaignSetup,
  createReferralSaasAccountFromDraft,
  createReferralSaasProgrammeDraft,
  getReferralSaasAccountProgrammeAnalytics,
  getReferralSaasAccountProgrammeCatalogue,
  getReferralSaasAccountCampaign,
  getReferralSaasAccountCampaignAttribution,
  getReferralSaasAccountCampaignReadiness,
  getReferralSaasAccountMembershipPosture,
  getReferralSaasIntegrationExecutionReadiness,
  getReferralSaasProviderVaultReadiness,
  getReferralSaasLoginCompletionReadiness,
  getReferralSaasMembershipActivationReadiness,
  getReferralSaasProductionActivation,
  getReferralSaasTechnicalSetupReadiness,
  getReferralSaasWorkspaceOverview,
  listReferralSaasAccountSupportCases,
  getReferralSaasAccountSupportCaseRepairReplayReadiness,
  listReferralSaasOperatorSupportQueue,
  listReferralSaasIntegrationCredentialRequests,
  listReferralSaasAccountCampaigns,
  listReferralSaasAccountProgrammes,
  listReferralSaasAccounts,
  publishReferralSaasProgrammeDraft,
  recordReferralSaasApiAccessVerification,
  recordReferralSaasIntegrationCredentialRequest,
  recordReferralSaasIntegrationCredentialExecutionCheck,
  recordReferralSaasIntegrationCredentialReviewDecision,
  recordReferralSaasMessageProviderTest,
  recordReferralSaasAccountCampaignReviewDecision,
  cancelReferralSaasMembershipInvitationIntent,
  requestReferralSaasAccountFoundationActivation,
  requestReferralSaasAccountCampaignActivation,
  requestReferralSaasAccessProvisioning,
  requestReferralSaasLoginCompletionIntent,
  recordReferralSaasMembershipInvitationIntent,
  requestReferralSaasMembershipActivation,
  requestReferralSaasMembershipInvitationDelivery,
  resolveReferralSaasAccount,
  submitReferralSaasAccountCampaignReview,
  updateReferralSaasMembershipInvitationIntent,
  updateReferralSaasAccountCampaignPolicySettings,
  updateReferralSaasAccountProfile,
  validateReferralSaasProgrammeDraft,
} from "./referralSaasAccounts";

vi.mock("../client", () => ({
  apiRequest: vi.fn(),
}));

const mockedApiRequest = vi.mocked(apiRequest);

describe("referralSaasAccounts endpoint client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("resolves a Referral SaaS account through the product account wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountCode: "FNB_REFERRAL_SAAS",
        accountName: "FNB Referral SaaS",
        accountStatus: "ACTIVE",
      },
      guardrail: "Read-only Referral SaaS account resolver.",
    });

    await expect(
      resolveReferralSaasAccount({
        refType: "external_tenant_ref",
        externalRef: " demo-platform-operator ",
        context: "setup",
      }),
    ).resolves.toMatchObject({
      status: "ok",
      account: {
        accountCode: "FNB_REFERRAL_SAAS",
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/accounts/resolve", {
      query: {
        ref_type: "external_tenant_ref",
        external_ref: "demo-platform-operator",
        context: "setup",
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|wallet|settlement|money/,
    );
  });

  it("lists Referral SaaS accounts through the read-only account registry wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      count: 1,
      accounts: [
        {
          accountId: "acct-1",
          accountCode: "ACCT_FNB",
          accountName: "FNB Referral SaaS",
          accountStatus: "PENDING_ONBOARDING",
          onboardingStatus: "READY_FOR_REVIEW",
          operatingJurisdictionCode: "ZA",
          primaryExternalTenantRef: "fnb-referrals",
          externalReferences: [
            {
              refType: "external_tenant_ref",
              externalRef: "fnb-referrals",
              referenceStatus: "ACTIVE",
            },
          ],
        },
      ],
      guardrail: "Read-only Referral SaaS account registry.",
      redactions: ["internal_tenant_identifier"],
    });

    await expect(listReferralSaasAccounts(25)).resolves.toMatchObject({
      count: 1,
      accounts: [{ accountCode: "ACCT_FNB", operatingJurisdictionCode: "ZA" }],
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/accounts", {
      query: {
        limit: 25,
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|wallet|settlement|money_movement/,
    );
  });

  it("reads the customer and partner workspace overview projection", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      workspaceOverview: {
        actor: { role: "PARTNER", visibleAccountCount: 1 },
        selectedAccount: {
          accountId: "acct-1",
          accountCode: "ACCT_FNB",
          accountName: "FNB Referral SaaS",
          accountStatus: "ACTIVE",
          operatingJurisdictionCode: "ZA",
        },
        readiness: { green: 2, red: 0, amber: 1, status: "READY" },
        primaryAction: {
          actionRef: "open_campaigns",
          label: "Open campaigns",
          status: "READY",
          priority: "NEXT",
        },
        worklist: [],
        plainLanguageSummary: "FNB Referral SaaS is ready for customer work.",
        safeToLeave: {
          canLeaveSafely: true,
          reason: "This overview is read-only.",
        },
        redactions: ["internal_tenant_identifier"],
      },
      guardrail: "Read-only Referral SaaS customer and partner workspace overview.",
      redactions: ["internal_tenant_identifier"],
    });

    await expect(
      getReferralSaasWorkspaceOverview({
        selectedAccountRef: " ACCT_FNB ",
        limit: 10,
      }),
    ).resolves.toMatchObject({
      workspaceOverview: {
        selectedAccount: { accountCode: "ACCT_FNB" },
        primaryAction: { label: "Open campaigns" },
        safeToLeave: { canLeaveSafely: true },
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/workspace/overview", {
      query: {
        selected_account_ref: "ACCT_FNB",
        limit: 10,
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|wallet|settlement|money_movement/,
    );
  });

  it("creates a Referral SaaS account from a reviewed setup draft through the guarded product wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "created",
      account: {
        accountCode: "FNB_REFERRAL_SAAS",
        accountName: "FNB Referral SaaS",
        accountStatus: "PENDING_ONBOARDING",
      },
      guardrails: ["DURABLE_ACCOUNT_FOUNDATION_ONLY", "NO_MONEY_MOVEMENT"],
      redactions: ["internal_tenant_identifier"],
      no_adjacent_live_action_confirmed: true,
    });

    await expect(
      createReferralSaasAccountFromDraft({
        draftRef: " draft_referral_saas_setup ",
        internalTenantCode: " FNB ",
        idempotencyKey: "account-create:draft_referral_saas_setup",
      }),
    ).resolves.toMatchObject({
      status: "created",
      account: {
        accountCode: "FNB_REFERRAL_SAAS",
      },
      noAdjacentLiveActionConfirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/accounts/from-draft", {
      method: "POST",
      body: {
        draft_ref: "draft_referral_saas_setup",
        internal_tenant_code: "FNB",
        idempotency_key: "account-create:draft_referral_saas_setup",
        correlation_id: "referral-saas-account-setup-create",
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /client_secret|wallet|settlement|money_movement/,
    );
  });

  it("reads the selected-customer programme workspace through bounded product routes", async () => {
    mockedApiRequest
      .mockResolvedValueOnce({
        status: "ok",
        count: 1,
        programmes: [{ programmeVersionId: "programme-version-1", programmeName: "FNB Referral Programme" }],
      })
      .mockResolvedValueOnce({
        status: "ok",
        productCode: "REFERRAL_SAAS",
        subProductCodes: ["RMCA_BUNDLE"],
        customerJourneyVersions: [{ customerJourneyVersionId: "journey-version-1" }],
      })
      .mockResolvedValueOnce({
        status: "ok",
        programmeAnalytics: {
          versionCount: 1,
          versions: [{ programmeVersionId: "programme-version-1", programmeName: "FNB Referral Programme" }],
        },
      });

    await listReferralSaasAccountProgrammes({
      accountRef: " acct-fnb ",
      refType: "external_tenant_ref",
      externalRef: " fnb-ref ",
      context: "setup",
      includeRetired: true,
      limit: 10,
    });
    await getReferralSaasAccountProgrammeCatalogue({
      accountRef: " acct-fnb ",
      refType: "external_tenant_ref",
      externalRef: " fnb-ref ",
      context: "setup",
      limit: 25,
    });
    await getReferralSaasAccountProgrammeAnalytics({
      accountRef: " acct-fnb ",
      refType: "external_tenant_ref",
      externalRef: " fnb-ref ",
      context: "setup",
      limit: 5,
    });

    expect(mockedApiRequest).toHaveBeenNthCalledWith(1, "v1/referral-saas/accounts/acct-fnb/programmes", {
      query: {
        ref_type: "external_tenant_ref",
        external_ref: "fnb-ref",
        context: "setup",
        includeRetired: true,
        limit: 10,
      },
    });
    expect(mockedApiRequest).toHaveBeenNthCalledWith(2, "v1/referral-saas/accounts/acct-fnb/programmes/catalogue", {
      query: {
        ref_type: "external_tenant_ref",
        external_ref: "fnb-ref",
        context: "setup",
        limit: 25,
      },
    });
    expect(mockedApiRequest).toHaveBeenNthCalledWith(3, "v1/referral-saas/accounts/acct-fnb/programmes/analytics", {
      query: {
        ref_type: "external_tenant_ref",
        external_ref: "fnb-ref",
        context: "setup",
        limit: 5,
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|wallet|settlement|money_movement/,
    );
  });

  it("drives the selected-customer programme draft lifecycle without adjacent live actions", async () => {
    mockedApiRequest
      .mockResolvedValueOnce({ status: "ok", commandStatus: "DRAFT_SAVED", draft: { programmeDraftId: "draft-1" } })
      .mockResolvedValueOnce({
        status: "ok",
        validation: {
          validationStatus: "VALIDATION_PASSED",
          publishAllowed: true,
          blockers: [],
          warnings: [],
        },
      })
      .mockResolvedValueOnce({
        status: "ok",
        commandStatus: "PUBLISHED",
        programmeVersion: { programmeVersionId: "programme-version-1" },
      });
    const accountScope = { refType: "external_tenant_ref", externalRef: "fnb-ref", context: "setup" };

    await createReferralSaasProgrammeDraft({
      accountRef: "acct-fnb",
      body: {
        accountScope,
        programmeName: "FNB Referral Programme",
        customerJourneyVersionId: "journey-version-1",
        campaignDefaults: { attributionWindowDays: 30 },
        idempotencyKey: "programme-draft-1",
      },
    });
    await validateReferralSaasProgrammeDraft({
      accountRef: "acct-fnb",
      draftRef: "draft-1",
      accountScope,
      idempotencyKey: "programme-validate-1",
    });
    await publishReferralSaasProgrammeDraft({
      accountRef: "acct-fnb",
      draftRef: "draft-1",
      accountScope,
      publishReason: "Approved for campaign setup.",
      idempotencyKey: "programme-publish-1",
    });

    expect(mockedApiRequest).toHaveBeenNthCalledWith(1, "v1/referral-saas/accounts/acct-fnb/programmes/drafts", {
      method: "POST",
      body: expect.objectContaining({
        programmeName: "FNB Referral Programme",
        idempotencyKey: "programme-draft-1",
      }),
    });
    expect(mockedApiRequest).toHaveBeenNthCalledWith(
      2,
      "v1/referral-saas/accounts/acct-fnb/programmes/drafts/draft-1/validate",
      {
        method: "POST",
        body: expect.objectContaining({ accountScope, idempotencyKey: "programme-validate-1" }),
      },
    );
    expect(mockedApiRequest).toHaveBeenNthCalledWith(
      3,
      "v1/referral-saas/accounts/acct-fnb/programmes/drafts/draft-1/publish",
      {
        method: "POST",
        body: expect.objectContaining({
          accountScope,
          publishReason: "Approved for campaign setup.",
          idempotencyKey: "programme-publish-1",
        }),
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /client_secret|wallet|settlement|money_movement/,
    );
  });

  it("reads Referral SaaS account membership posture through the read-only wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountCode: "FNB_REFERRAL_SAAS",
        accountName: "FNB Referral SaaS",
      },
      membershipPosture: {
        accountId: "acct-1",
        totalMemberships: 0,
        invitedCount: 0,
        activeCount: 0,
        suspendedCount: 0,
        disabledCount: 0,
        archivedCount: 0,
        roleFamilies: [],
        currentActor: {
          status: "NO_MEMBERSHIP_EVIDENCE",
          roleFamily: null,
          permissionSet: null,
          canOperateSetup: false,
          evidence: "No active account membership matched the current actor.",
        },
        guardrails: ["READ_ONLY_MEMBERSHIP_POSTURE", "NO_INVITE_DELIVERY"],
        redactions: ["internal_tenant_identifier", "user_identifier"],
        noMembershipWriteConfirmed: true,
        noInviteDeliveryConfirmed: true,
      },
      guardrail: "Read-only Referral SaaS account membership posture.",
      no_membership_write_confirmed: true,
      no_invite_delivery_confirmed: true,
    });

    await expect(
      getReferralSaasAccountMembershipPosture({
        refType: "external_tenant_ref",
        externalRef: " demo-platform-operator ",
        context: "setup",
      }),
    ).resolves.toMatchObject({
      membershipPosture: {
        currentActor: {
          status: "NO_MEMBERSHIP_EVIDENCE",
        },
        noInviteDeliveryConfirmed: true,
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/accounts/membership-posture", {
      query: {
        ref_type: "external_tenant_ref",
        external_ref: "demo-platform-operator",
        context: "setup",
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|wallet|settlement|money_movement/,
    );
  });

  it("reads Referral SaaS membership activation readiness without a write action", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
        accountName: "FNB Referral SaaS",
      },
      activationReadiness: {
        accountId: "acct-1",
        overallStatus: "ACTION_REQUIRED",
        activeCount: 0,
        invitedCount: 1,
        deliveryReadyCount: 0,
        activationReadyCount: 0,
        missingRoleFamilies: ["CAMPAIGN_MANAGER"],
        items: [
          {
            subject: "owner@example.test",
            displayName: "Setup Owner",
            roleFamily: "DISTRIBUTION_ADMIN",
            membershipStatus: "INVITED",
            deliveryStatus: "DELIVERY_NOT_CONFIGURED",
            recipientContactStatus: "CONTACT_REFERENCE_PRESENT",
            deliveryReadiness: "BLOCKED",
            activationReadiness: "BLOCKED",
            provisioningReadiness: "WAITING_FOR_MEMBERSHIP_ACTIVATION",
            seatAssignmentStatus: "SEAT_NOT_ASSIGNED",
            authClaimStatus: "AUTH_CLAIMS_NOT_PROPAGATED",
            blockers: ["DELIVERY_PROVIDER_NOT_CONFIGURED"],
            nextAction: "Configure an approved invitation delivery provider before sending invites.",
          },
        ],
        guardrails: ["READ_ONLY_ACTIVATION_READINESS"],
        redactions: ["internal_tenant_identifier"],
        noInviteDeliveryConfirmed: true,
        noMembershipActivationConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noAuthClaimChangeConfirmed: true,
      },
      guardrail: "Read-only Referral SaaS membership activation readiness.",
      no_invite_delivery_confirmed: true,
      no_membership_activation_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_money_movement_confirmed: true,
    });

    await expect(
      getReferralSaasMembershipActivationReadiness({
        accountRef: " acct-1 ",
        refType: "external_tenant_ref",
        externalRef: " fnb-referrals ",
        context: "setup",
      }),
    ).resolves.toMatchObject({
      activationReadiness: {
        overallStatus: "ACTION_REQUIRED",
        noMembershipActivationConfirmed: true,
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/membership-activation-readiness",
      {
        query: {
          ref_type: "external_tenant_ref",
          external_ref: "fnb-referrals",
          context: "setup",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|wallet|settlement|money_movement/,
    );
  });

  it("reads Referral SaaS technical setup readiness without provider or delivery writes", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
        accountName: "FNB Referral SaaS",
      },
      technicalSetupReadiness: {
        accountId: "acct-1",
        overallStatus: "PROVIDER_CONFIGURATION_REQUIRED",
        providerStatus: "ATTENTION",
        channelSummary: {
          count: 4,
          readyCount: 0,
          attentionCount: 4,
          supportedChannels: ["EMAIL", "WHATSAPP", "SMS", "USSD"],
          approvedInviteProviderCount: 0,
          postureBlockers: [],
        },
        capabilities: [
          {
            code: "MEMBERSHIP_INVITE_DELIVERY",
            label: "People invite delivery",
            status: "ATTENTION",
            requiredChannels: ["EMAIL"],
            readyChannels: [],
            missingChannels: ["EMAIL"],
            approvedProviderRefs: [],
            missingApprovalChannels: [],
            nextAction: "Configure and approve the Email provider for Referral SaaS before sending account access invites.",
          },
        ],
        guardrails: ["READ_ONLY_TECHNICAL_SETUP_READINESS"],
        redactions: ["internal_tenant_identifier", "provider_secret"],
        noCredentialCreationConfirmed: true,
        noWebhookDispatchConfirmed: true,
        noInviteDeliveryConfirmed: true,
        noMembershipActivationConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noCampaignActivationConfirmed: true,
        noMoneyMovementConfirmed: true,
      },
      guardrail: "Read-only Referral SaaS technical setup readiness.",
      no_credential_creation_confirmed: true,
      no_webhook_dispatch_confirmed: true,
      no_invite_delivery_confirmed: true,
      no_membership_activation_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_money_movement_confirmed: true,
    });

    await expect(
      getReferralSaasTechnicalSetupReadiness({
        accountRef: " acct-1 ",
        refType: "external_tenant_ref",
        externalRef: " fnb-referrals ",
        context: "setup",
      }),
    ).resolves.toMatchObject({
      technicalSetupReadiness: {
        overallStatus: "PROVIDER_CONFIGURATION_REQUIRED",
        noCredentialCreationConfirmed: true,
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/technical-setup-readiness",
      {
        query: {
          ref_type: "external_tenant_ref",
          external_ref: "fnb-referrals",
          context: "setup",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|wallet|settlement|money_movement/,
    );
  });

  it("reads Referral SaaS login completion readiness for one membership", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
        accountName: "FNB Referral SaaS",
      },
      loginCompletionReadiness: {
        loginCompletionStatus: "LOGIN_COMPLETION_READY",
        accountRef: "acct-1",
        membershipRef: "mbr-1",
        person: {
          subject: "owner@fnb.example",
          displayName: "FNB Owner",
          responsibilities: ["DISTRIBUTION_ADMIN"],
        },
        seat: {
          seatAssignmentStatus: "SEAT_ASSIGNED",
        },
        identity: {
          identityProviderStatus: "AUTH_PROVIDER_READY",
          authClaimStatus: "AUTH_CLAIMS_NOT_PROPAGATED",
          permissionProfile: "REFERRAL_SAAS_ACCOUNT_ADMIN",
        },
        blockers: [],
        nextActions: ["Record governed login completion evidence if this person must sign in."],
        guardrails: ["NO_CREDENTIAL_CREATION", "NO_AUTH_CLAIM_CHANGE"],
        redactions: ["internal_tenant_identifier"],
        noInviteDeliveryConfirmed: true,
        noCredentialCreationConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noCampaignActivationConfirmed: true,
        noGoLiveChangeConfirmed: true,
        noMoneyMovementConfirmed: true,
      },
      guardrail: "Read-only Referral SaaS login completion readiness.",
      guardrails: ["NO_CREDENTIAL_CREATION", "NO_AUTH_CLAIM_CHANGE"],
      redactions: ["internal_tenant_identifier"],
      no_invite_delivery_confirmed: true,
      no_credential_creation_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_go_live_change_confirmed: true,
      no_money_movement_confirmed: true,
    });

    await expect(
      getReferralSaasLoginCompletionReadiness({
        accountRef: " acct-1 ",
        membershipRef: " mbr-1 ",
        refType: "external_tenant_ref",
        externalRef: " fnb-referrals ",
        context: "setup",
      }),
    ).resolves.toMatchObject({
      loginCompletionReadiness: {
        loginCompletionStatus: "LOGIN_COMPLETION_READY",
        noCredentialCreationConfirmed: true,
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/memberships/mbr-1/login-completion-readiness",
      {
        query: {
          ref_type: "external_tenant_ref",
          external_ref: "fnb-referrals",
          context: "setup",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|password|raw_auth|sendinvite|campaignactivation|golive|wallet|settlement|money/,
    );
  });

  it("reads Referral SaaS production activation gates without activating anything", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
        accountName: "FNB Referral SaaS",
      },
      productionActivation: {
        decisionStatus: "PRODUCTION_ACTIVATION_BLOCKED",
        accountId: "acct-1",
        accountName: "FNB Referral SaaS",
        launchAllowed: false,
        disabledReasons: ["COMMERCIAL_ENTITLEMENT"],
        gates: [
          {
            gate: "COMMERCIAL_ENTITLEMENT",
            label: "Commercial entitlement",
            status: "BLOCKED",
            passed: false,
            evidence: "No launch entitlement is configured.",
            nextAction: "Confirm plan and contract before launch.",
            routeHint: "commercial",
          },
        ],
        plainLanguageSummary: "FNB Referral SaaS is blocked before production activation.",
        guardrails: ["BACKEND_PRODUCTION_ACTIVATION_DECISION_REQUIRED"],
        redactions: ["internal_tenant_identifier"],
        noUiOnlyActivationConfirmed: true,
        noCampaignActivationConfirmed: true,
        noGoLiveActionConfirmed: true,
        noBillingOrMoneyMovementConfirmed: true,
      },
      no_ui_only_activation_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_go_live_action_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      getReferralSaasProductionActivation({
        accountRef: " acct-1 ",
        refType: "external_tenant_ref",
        externalRef: " fnb-referrals ",
        context: "setup",
      }),
    ).resolves.toMatchObject({
      productionActivation: {
        launchAllowed: false,
        disabledReasons: ["COMMERCIAL_ENTITLEMENT"],
        noCampaignActivationConfirmed: true,
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/production-activation",
      {
        query: {
          ref_type: "external_tenant_ref",
          external_ref: "fnb-referrals",
          context: "setup",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|password|raw_auth|sendinvite|campaignactivation|golive|wallet|settlement|money/,
    );
  });

  it("reads Referral SaaS integration execution readiness without live provider execution", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
        accountName: "FNB Referral SaaS",
      },
      integrationConfiguration: null,
      integrationExecutionReadiness: {
        executionStatus: "INTEGRATION_EXECUTION_BLOCKED_CONFIGURATION_MISSING",
        plainLanguageSummary: "Save Integrations setup evidence before live verification can start.",
        blockers: [
          {
            code: "CONFIGURATION_MISSING",
            message: "Save the customer's Integrations setup before live verification.",
          },
        ],
        readyActions: [],
        executionActions: [
          {
            actionRef: "SAVE_INTEGRATION_CONFIGURATION",
            label: "Save Integrations setup",
            status: "BLOCKED",
            nextStep: "Open Integrations and save non-secret setup evidence.",
            reason: "No saved configuration exists for this customer.",
          },
        ],
        configurationRef: null,
        configurationStatus: null,
        guardrails: ["READ_ONLY_EXECUTION_READINESS"],
        redactions: ["internal_tenant_identifier", "provider_secret"],
        noSecretOrCredentialStorageConfirmed: true,
        noCredentialCreationConfirmed: true,
        noCredentialLifecycleConfirmed: true,
        noWebhookDispatchConfirmed: true,
        noInviteDeliveryConfirmed: true,
        noMessageProviderDeliveryConfirmed: true,
        noMembershipActivationConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noCampaignActivationConfirmed: true,
        noGoLiveActionConfirmed: true,
        noBillingOrMoneyMovementConfirmed: true,
      },
      guardrail: "Read-only selected-customer Integrations execution readiness.",
      guardrails: ["READ_ONLY_EXECUTION_READINESS"],
      redactions: ["internal_tenant_identifier", "provider_secret"],
      no_secret_or_credential_storage_confirmed: true,
      no_credential_creation_confirmed: true,
      no_credential_lifecycle_confirmed: true,
      no_webhook_dispatch_confirmed: true,
      no_invite_delivery_confirmed: true,
      no_message_provider_delivery_confirmed: true,
      no_membership_activation_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_go_live_action_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      getReferralSaasIntegrationExecutionReadiness({
        accountRef: " acct-1 ",
        refType: "external_tenant_ref",
        externalRef: " fnb-referrals ",
        context: "setup",
      }),
    ).resolves.toMatchObject({
      integrationExecutionReadiness: {
        executionStatus: "INTEGRATION_EXECUTION_BLOCKED_CONFIGURATION_MISSING",
        noCredentialLifecycleConfirmed: true,
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/integrations/execution-readiness",
      {
        query: {
          ref_type: "external_tenant_ref",
          external_ref: "fnb-referrals",
          context: "setup",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|api_key|webhook_secret|wallet|settlement|money_movement/,
    );
  });

  it("records customer-scoped API access verification without secret-bearing payloads", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "accepted",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
        accountName: "FNB Referral SaaS",
      },
      integrationApiAccessVerification: {
        verificationStatus: "API_ACCESS_VERIFICATION_RECORDED",
        configurationRef: "config-1",
        accountRef: "acct-1",
        apiEnvironment: "SANDBOX",
        verifiedUseCases: ["CAMPAIGN_READ"],
        idempotency: { status: "NEW_REQUEST" },
        audit: { accountAuditEventId: "audit-1" },
        plainLanguageSummary: "API-access verification evidence was recorded without credential creation.",
        guardrails: ["NO_CREDENTIAL_CREATION"],
        redactions: ["provider_secret"],
        noSecretOrCredentialStorageConfirmed: true,
        noCredentialCreationConfirmed: true,
        noCredentialLifecycleConfirmed: true,
        noWebhookDispatchConfirmed: true,
        noInviteDeliveryConfirmed: true,
        noMessageProviderDeliveryConfirmed: true,
        noMembershipActivationConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noCampaignActivationConfirmed: true,
        noGoLiveActionConfirmed: true,
        noBillingOrMoneyMovementConfirmed: true,
      },
      guardrail: "API-access verification evidence recorded for the selected customer only.",
      guardrails: ["NO_CREDENTIAL_CREATION"],
      redactions: ["provider_secret"],
      no_secret_or_credential_storage_confirmed: true,
      no_credential_creation_confirmed: true,
      no_credential_lifecycle_confirmed: true,
      no_webhook_dispatch_confirmed: true,
      no_invite_delivery_confirmed: true,
      no_message_provider_delivery_confirmed: true,
      no_membership_activation_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_go_live_action_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      recordReferralSaasApiAccessVerification({
        accountRef: " acct-1 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
          context: "setup",
        },
        verification: {
          verificationType: "API_ACCESS_VERIFICATION",
          environment: "SANDBOX",
          authMethod: "API_KEY",
          intendedUseCases: ["CAMPAIGN_READ"],
          noCredentialCreationConfirmed: true,
          noProviderCallConfirmed: true,
          noWebhookDispatchConfirmed: true,
        },
        reasonCode: " CUSTOMER_API_ACCESS_VERIFICATION ",
        correlationId: " corr-1 ",
        idempotencyKey: " verify-1 ",
      }),
    ).resolves.toMatchObject({
      integrationApiAccessVerification: {
        verificationStatus: "API_ACCESS_VERIFICATION_RECORDED",
        noCredentialCreationConfirmed: true,
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/integrations/api-access/verification",
      {
        method: "POST",
        body: {
          accountScope: {
            refType: "external_tenant_ref",
            externalRef: "fnb-referrals",
            context: "setup",
          },
          verification: {
            verificationType: "API_ACCESS_VERIFICATION",
            environment: "SANDBOX",
            authMethod: "API_KEY",
            intendedUseCases: ["CAMPAIGN_READ"],
            noCredentialCreationConfirmed: true,
            noProviderCallConfirmed: true,
            noWebhookDispatchConfirmed: true,
          },
          reasonCode: "CUSTOMER_API_ACCESS_VERIFICATION",
          correlationId: "corr-1",
          idempotencyKey: "verify-1",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|api_key_value|webhook_secret|wallet|settlement|money_movement/,
    );
  });

  it("records customer-scoped message provider checks without sending messages", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "accepted",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
        accountName: "FNB Referral SaaS",
      },
      integrationMessageProviderTest: {
        testStatus: "MESSAGE_PROVIDER_TEST_RECORDED",
        configurationRef: "config-1",
        accountRef: "acct-1",
        channels: ["EMAIL", "WHATSAPP"],
        providerRefs: ["provider-approved-1"],
        idempotency: { status: "NEW_REQUEST" },
        audit: { accountAuditEventId: "audit-provider-1" },
        plainLanguageSummary:
          "Message-provider test evidence was recorded for the selected customer. No provider was called and no message was sent.",
        guardrails: ["NO_MESSAGE_PROVIDER_DELIVERY"],
        redactions: ["provider_secret"],
        noSecretOrCredentialStorageConfirmed: true,
        noCredentialCreationConfirmed: true,
        noCredentialLifecycleConfirmed: true,
        noWebhookDispatchConfirmed: true,
        noInviteDeliveryConfirmed: true,
        noMessageProviderDeliveryConfirmed: true,
        noMembershipActivationConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noCampaignActivationConfirmed: true,
        noGoLiveActionConfirmed: true,
        noBillingOrMoneyMovementConfirmed: true,
      },
      guardrail: "Message-provider test evidence recorded for the selected customer only.",
      guardrails: ["NO_MESSAGE_PROVIDER_DELIVERY"],
      redactions: ["provider_secret"],
      no_secret_or_credential_storage_confirmed: true,
      no_credential_creation_confirmed: true,
      no_credential_lifecycle_confirmed: true,
      no_webhook_dispatch_confirmed: true,
      no_invite_delivery_confirmed: true,
      no_message_provider_delivery_confirmed: true,
      no_membership_activation_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_go_live_action_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      recordReferralSaasMessageProviderTest({
        accountRef: " acct-1 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
          context: "setup",
        },
        messageProviderTest: {
          testType: "MESSAGE_PROVIDER_TEST",
          configurationRef: "config-1",
          channels: ["EMAIL", "WHATSAPP"],
          providerRefs: ["provider-approved-1"],
          noProviderCallConfirmed: true,
          noInviteDeliveryConfirmed: true,
          noMessageProviderDeliveryConfirmed: true,
        },
        reasonCode: " CUSTOMER_MESSAGE_PROVIDER_TEST ",
        correlationId: " corr-provider-1 ",
        idempotencyKey: " provider-test-1 ",
      }),
    ).resolves.toMatchObject({
      integrationMessageProviderTest: {
        testStatus: "MESSAGE_PROVIDER_TEST_RECORDED",
        noMessageProviderDeliveryConfirmed: true,
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/integrations/message-providers/test-check",
      {
        method: "POST",
        body: {
          accountScope: {
            refType: "external_tenant_ref",
            externalRef: "fnb-referrals",
            context: "setup",
          },
          messageProviderTest: {
            testType: "MESSAGE_PROVIDER_TEST",
            configurationRef: "config-1",
            channels: ["EMAIL", "WHATSAPP"],
            providerRefs: ["provider-approved-1"],
            noProviderCallConfirmed: true,
            noInviteDeliveryConfirmed: true,
            noMessageProviderDeliveryConfirmed: true,
          },
          reasonCode: "CUSTOMER_MESSAGE_PROVIDER_TEST",
          correlationId: "corr-provider-1",
          idempotencyKey: "provider-test-1",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|api_key_value|webhook_secret|credential_value|wallet|settlement|money_movement/,
    );
  });

  it("records customer-scoped credential setup requests without creating credentials", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "accepted",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
        accountName: "FNB Referral SaaS",
      },
      integrationCredentialRequestResult: {
        commandStatus: "CREDENTIAL_REQUEST_RECORDED",
        credentialRequest: {
          credentialRequestRef: "credential-request-1",
          accountRef: "acct-1",
          configurationRef: "config-1",
          credentialRequestStatus: "REQUEST_RECORDED",
          reviewStatus: "PENDING_REVIEW",
          requestType: "API_KEY_CREATE",
          capability: "REFERRAL_SAAS_API_ACCESS",
          environment: "SANDBOX",
          intendedUse: ["CAMPAIGN_READ"],
          requestedFor: {
            customerName: "FNB Referral SaaS",
          },
          safeRequestPosture: {
            credentialLifecycle: "REQUEST_ONLY",
          },
          redactions: ["provider_secret"],
          noSecretOrCredentialStorageConfirmed: true,
          noCredentialCreationConfirmed: true,
          noCredentialLifecycleExecutionConfirmed: true,
          noCredentialRevealOrDownloadConfirmed: true,
          noVaultWriteConfirmed: true,
          noProviderCallConfirmed: true,
          noWebhookDispatchConfirmed: true,
          noInviteDeliveryConfirmed: true,
          noMessageProviderDeliveryConfirmed: true,
          noMembershipActivationConfirmed: true,
          noSeatAssignmentConfirmed: true,
          noAuthClaimChangeConfirmed: true,
          noCampaignActivationConfirmed: true,
          noGoLiveActionConfirmed: true,
          noBillingOrMoneyMovementConfirmed: true,
        },
        idempotency: { status: "NEW_REQUEST" },
        audit: { accountAuditEventId: "audit-credential-1" },
        plainLanguageSummary:
          "Credential setup request was recorded for the selected customer. No credential was created or shown.",
        guardrails: ["NO_CREDENTIAL_CREATION"],
        redactions: ["provider_secret"],
      },
      guardrail: "Credential setup request recorded for the selected customer only.",
      guardrails: ["NO_CREDENTIAL_CREATION"],
      redactions: ["provider_secret"],
      no_secret_or_credential_storage_confirmed: true,
      no_credential_creation_confirmed: true,
      no_credential_lifecycle_execution_confirmed: true,
      no_credential_reveal_or_download_confirmed: true,
      no_vault_write_confirmed: true,
      no_provider_call_confirmed: true,
      no_webhook_dispatch_confirmed: true,
      no_invite_delivery_confirmed: true,
      no_message_provider_delivery_confirmed: true,
      no_membership_activation_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_go_live_action_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      recordReferralSaasIntegrationCredentialRequest({
        accountRef: " acct-1 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
          context: "setup",
        },
        credentialRequest: {
          requestType: " API_KEY_CREATE ",
          capability: " REFERRAL_SAAS_API_ACCESS ",
          environment: " SANDBOX ",
          intendedUse: ["CAMPAIGN_READ"],
          requestedFor: {
            customerName: "FNB Referral SaaS",
          },
        },
        reasonCode: " CUSTOMER_CREDENTIAL_REQUEST ",
        correlationId: " corr-credential-1 ",
        idempotencyKey: " credential-request-1 ",
      }),
    ).resolves.toMatchObject({
      integrationCredentialRequestResult: {
        commandStatus: "CREDENTIAL_REQUEST_RECORDED",
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/integrations/credential-requests",
      {
        method: "POST",
        body: {
          accountScope: {
            refType: "external_tenant_ref",
            externalRef: "fnb-referrals",
            context: "setup",
          },
          credentialRequest: {
            requestType: "API_KEY_CREATE",
            capability: "REFERRAL_SAAS_API_ACCESS",
            environment: "SANDBOX",
            intendedUse: ["CAMPAIGN_READ"],
            requestedFor: {
              customerName: "FNB Referral SaaS",
            },
          },
          reasonCode: "CUSTOMER_CREDENTIAL_REQUEST",
          correlationId: "corr-credential-1",
          idempotencyKey: "credential-request-1",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|api_key_value|webhook_secret|credential_value|vault|download|money_movement/,
    );
  });

  it("lists customer-scoped credential setup requests", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
        accountName: "FNB Referral SaaS",
      },
      credentialRequests: [],
      guardrail: "Credential setup requests are listed for the selected customer only.",
      guardrails: ["CUSTOMER_SCOPED_CREDENTIAL_REQUESTS"],
      redactions: ["provider_secret"],
      no_secret_or_credential_storage_confirmed: true,
      no_credential_creation_confirmed: true,
      no_credential_lifecycle_execution_confirmed: true,
      no_credential_reveal_or_download_confirmed: true,
      no_vault_write_confirmed: true,
      no_provider_call_confirmed: true,
      no_webhook_dispatch_confirmed: true,
      no_invite_delivery_confirmed: true,
      no_message_provider_delivery_confirmed: true,
      no_membership_activation_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_go_live_action_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      listReferralSaasIntegrationCredentialRequests({
        accountRef: " acct-1 ",
        refType: "external_tenant_ref",
        externalRef: " fnb-referrals ",
        context: "setup",
        limit: 20,
      }),
    ).resolves.toMatchObject({
      credentialRequests: [],
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/integrations/credential-requests",
      {
        query: {
          ref_type: "external_tenant_ref",
          external_ref: "fnb-referrals",
          context: "setup",
          limit: 20,
        },
      },
    );
  });

  it("records customer-scoped credential setup review decisions without executing credential lifecycle", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "accepted",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
        accountName: "FNB Referral SaaS",
      },
      integrationCredentialReviewDecisionResult: {
        commandStatus: "CREDENTIAL_REQUEST_REVIEW_RECORDED",
        credentialRequest: {
          credentialRequestRef: "credential-request-1",
          accountRef: "acct-1",
          credentialRequestStatus: "REQUEST_RECORDED",
          reviewStatus: "REVIEW_APPROVED",
          requestType: "API_KEY_CREATE",
          capability: "REFERRAL_SAAS_API_ACCESS",
          environment: "SANDBOX",
          intendedUse: ["CAMPAIGN_READ"],
          requestedFor: {},
          safeRequestPosture: {},
          redactions: ["provider_secret"],
          noSecretOrCredentialStorageConfirmed: true,
          noCredentialCreationConfirmed: true,
          noCredentialLifecycleExecutionConfirmed: true,
          noCredentialRevealOrDownloadConfirmed: true,
          noVaultWriteConfirmed: true,
          noProviderCallConfirmed: true,
          noWebhookDispatchConfirmed: true,
          noInviteDeliveryConfirmed: true,
          noMessageProviderDeliveryConfirmed: true,
          noMembershipActivationConfirmed: true,
          noSeatAssignmentConfirmed: true,
          noAuthClaimChangeConfirmed: true,
          noCampaignActivationConfirmed: true,
          noGoLiveActionConfirmed: true,
          noBillingOrMoneyMovementConfirmed: true,
        },
        reviewStatus: "REVIEW_APPROVED",
        idempotency: { status: "CREDENTIAL_REQUEST_REVIEW_RECORDED" },
        audit: { accountAuditEventId: "audit-credential-review-1" },
        plainLanguageSummary:
          "Credential request was approved for later governed execution. No secret was created, revealed, stored, downloaded, or sent.",
        guardrails: ["NO_CREDENTIAL_CREATION"],
        redactions: ["provider_secret"],
        noSecretOrCredentialStorageConfirmed: true,
        noCredentialCreationConfirmed: true,
        noCredentialLifecycleExecutionConfirmed: true,
        noCredentialRevealOrDownloadConfirmed: true,
        noVaultWriteConfirmed: true,
        noProviderCallConfirmed: true,
        noWebhookDispatchConfirmed: true,
        noInviteDeliveryConfirmed: true,
        noMessageProviderDeliveryConfirmed: true,
        noMembershipActivationConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noCampaignActivationConfirmed: true,
        noGoLiveActionConfirmed: true,
        noBillingOrMoneyMovementConfirmed: true,
      },
      guardrail: "Credential request review decision recorded for the selected customer.",
      guardrails: ["NO_CREDENTIAL_CREATION"],
      redactions: ["provider_secret"],
      no_secret_or_credential_storage_confirmed: true,
      no_credential_creation_confirmed: true,
      no_credential_lifecycle_execution_confirmed: true,
      no_credential_reveal_or_download_confirmed: true,
      no_vault_write_confirmed: true,
      no_provider_call_confirmed: true,
      no_webhook_dispatch_confirmed: true,
      no_invite_delivery_confirmed: true,
      no_message_provider_delivery_confirmed: true,
      no_membership_activation_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_go_live_action_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      recordReferralSaasIntegrationCredentialReviewDecision({
        accountRef: " acct-1 ",
        credentialRequestRef: " credential-request-1 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
          context: "setup",
        },
        reviewDecision: {
          decision: "APPROVED",
          reason: " Reviewed for later governed execution. ",
        },
        reasonCode: " CUSTOMER_CREDENTIAL_REQUEST_APPROVED ",
        correlationId: " corr-credential-review-1 ",
        idempotencyKey: " credential-review-1 ",
      }),
    ).resolves.toMatchObject({
      integrationCredentialReviewDecisionResult: {
        commandStatus: "CREDENTIAL_REQUEST_REVIEW_RECORDED",
        reviewStatus: "REVIEW_APPROVED",
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/integrations/credential-requests/credential-request-1/review-decisions",
      {
        method: "POST",
        body: {
          accountScope: {
            refType: "external_tenant_ref",
            externalRef: "fnb-referrals",
            context: "setup",
          },
          reviewDecision: {
            decision: "APPROVED",
            reason: "Reviewed for later governed execution.",
          },
          reasonCode: "CUSTOMER_CREDENTIAL_REQUEST_APPROVED",
          correlationId: "corr-credential-review-1",
          idempotencyKey: "credential-review-1",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|api_key_value|webhook_secret|credential_value|vault|download|provider_call|money_movement/,
    );
  });

  it("records customer-scoped credential execution checks without executing credential lifecycle", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "accepted",
      context: "setup",
      integrationCredentialExecutionCheckResult: {
        commandStatus: "CREDENTIAL_EXECUTION_CHECK_RECORDED",
        executionCheckStatus: "CREDENTIAL_EXECUTION_CHECK_RECORDED",
        plainLanguageSummary:
          "Approved credential setup was checked for later governed execution. No credential was created, revealed, stored, downloaded, or sent.",
        noSecretOrCredentialStorageConfirmed: true,
        noCredentialCreationConfirmed: true,
        noCredentialLifecycleExecutionConfirmed: true,
        noCredentialRevealOrDownloadConfirmed: true,
        noVaultWriteConfirmed: true,
        noProviderCallConfirmed: true,
        noWebhookDispatchConfirmed: true,
        noInviteDeliveryConfirmed: true,
        noMessageProviderDeliveryConfirmed: true,
        noMembershipActivationConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noCampaignActivationConfirmed: true,
        noGoLiveActionConfirmed: true,
        noBillingOrMoneyMovementConfirmed: true,
      },
      guardrail: "Credential execution check recorded for the selected customer.",
      guardrails: ["NO_CREDENTIAL_CREATION"],
      redactions: ["provider_secret"],
      no_secret_or_credential_storage_confirmed: true,
      no_credential_creation_confirmed: true,
      no_credential_lifecycle_execution_confirmed: true,
      no_credential_reveal_or_download_confirmed: true,
      no_vault_write_confirmed: true,
      no_provider_call_confirmed: true,
      no_webhook_dispatch_confirmed: true,
      no_invite_delivery_confirmed: true,
      no_message_provider_delivery_confirmed: true,
      no_membership_activation_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_go_live_action_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      recordReferralSaasIntegrationCredentialExecutionCheck({
        accountRef: " acct-1 ",
        credentialRequestRef: " credential-request-1 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
          context: "setup",
        },
        executionCheck: {
          reason: " Checked for later governed execution. ",
          reasonCode: " CUSTOMER_CREDENTIAL_EXECUTION_READY_CHECK ",
        },
        reasonCode: " CUSTOMER_CREDENTIAL_EXECUTION_READY_CHECK ",
        correlationId: " corr-credential-execution-check-1 ",
        idempotencyKey: " credential-execution-check-1 ",
      }),
    ).resolves.toMatchObject({
      integrationCredentialExecutionCheckResult: {
        commandStatus: "CREDENTIAL_EXECUTION_CHECK_RECORDED",
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/integrations/credential-requests/credential-request-1/execution-checks",
      {
        method: "POST",
        body: {
          accountScope: {
            refType: "external_tenant_ref",
            externalRef: "fnb-referrals",
            context: "setup",
          },
          executionCheck: {
            reason: "Checked for later governed execution.",
            reasonCode: "CUSTOMER_CREDENTIAL_EXECUTION_READY_CHECK",
          },
          reasonCode: "CUSTOMER_CREDENTIAL_EXECUTION_READY_CHECK",
          correlationId: "corr-credential-execution-check-1",
          idempotencyKey: "credential-execution-check-1",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|api_key_value|webhook_secret|credential_value|vault|download|provider_call|money_movement/,
    );
  });

  it("reads provider/vault readiness without executing providers or exposing secrets", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "ACCT_FNB",
        accountName: "FNB Referral SaaS",
      },
      providerVaultReadiness: {
        readinessStatus: "PROVIDER_VAULT_EXECUTION_READY",
        plainLanguageSummary:
          "Approved credential request evidence is ready for a future governed provider/vault executor.",
        credentialRequests: [
          {
            credentialRequestRef: "credential-request-1",
            capability: "MESSAGE_PROVIDER",
            requestType: "PROVIDER_CREDENTIAL",
            environment: "SANDBOX",
            reviewStatus: "REVIEW_APPROVED",
            readinessStatus: "PROVIDER_VAULT_EXECUTION_READY",
            readyForExecution: true,
            plainLanguageSummary: "This approved request is ready for a future governed provider/vault executor.",
            blockers: [],
            nextActions: [
              {
                actionRef: "PROVIDER_VAULT_EXECUTOR_HANDOFF",
                label: "Prepare provider/vault executor handoff",
                status: "READY",
                nextStep: "Use a governed executor workflow when provider/vault adapters exist.",
                reason: "Approved credential request and saved configuration are aligned.",
              },
            ],
            configurationRef: "integration-config-1",
          },
        ],
        blockers: [],
        readyActions: [
          {
            actionRef: "PROVIDER_VAULT_EXECUTOR_HANDOFF",
            label: "Prepare provider/vault executor handoff",
            status: "READY",
            nextStep: "Use a governed executor workflow when provider/vault adapters exist.",
            reason: "Approved credential request and saved configuration are aligned.",
          },
        ],
        guardrails: ["READ_ONLY_PROVIDER_VAULT_READINESS"],
        redactions: ["provider_secret", "vault_reference"],
        noSecretOrCredentialStorageConfirmed: true,
        noCredentialCreationConfirmed: true,
        noCredentialLifecycleExecutionConfirmed: true,
        noCredentialRevealOrDownloadConfirmed: true,
        noVaultWriteConfirmed: true,
        noProviderCallConfirmed: true,
        noWebhookDispatchConfirmed: true,
        noInviteDeliveryConfirmed: true,
        noMessageProviderDeliveryConfirmed: true,
        noMembershipActivationConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noCampaignActivationConfirmed: true,
        noGoLiveActionConfirmed: true,
        noBillingOrMoneyMovementConfirmed: true,
      },
      guardrail: "Read-only selected-customer provider/vault readiness.",
      guardrails: ["READ_ONLY_PROVIDER_VAULT_READINESS"],
      redactions: ["provider_secret", "vault_reference"],
      no_secret_or_credential_storage_confirmed: true,
      no_credential_creation_confirmed: true,
      no_credential_lifecycle_execution_confirmed: true,
      no_credential_reveal_or_download_confirmed: true,
      no_vault_write_confirmed: true,
      no_provider_call_confirmed: true,
      no_webhook_dispatch_confirmed: true,
      no_invite_delivery_confirmed: true,
      no_message_provider_delivery_confirmed: true,
      no_membership_activation_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_go_live_action_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      getReferralSaasProviderVaultReadiness({
        accountRef: " acct-1 ",
        refType: "external_tenant_ref",
        externalRef: " fnb-referrals ",
        context: "setup",
      }),
    ).resolves.toMatchObject({
      providerVaultReadiness: {
        readinessStatus: "PROVIDER_VAULT_EXECUTION_READY",
      },
      no_provider_call_confirmed: true,
      no_vault_write_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/integrations/provider-vault/readiness",
      {
        query: {
          ref_type: "external_tenant_ref",
          external_ref: "fnb-referrals",
          context: "setup",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|api_key_value|webhook_secret|credential_value|download|provider_call|money_movement/,
    );
  });

  it("reads customer-scoped campaign readiness without requiring tenant code entry", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
        accountName: "FNB Referral SaaS",
      },
      readiness: {
        campaign_code: "CAMP001",
        readiness: "READY_WITH_WARNINGS",
        can_proceed: true,
        blockers: [],
        warnings: [
          {
            code: "REPORTING_BASELINE_PENDING",
            message: "Reporting setup can follow after campaign checks.",
          },
        ],
      },
      guardrail: "Read-only Referral SaaS customer-scoped campaign readiness.",
      redactions: ["internal_tenant_identifier"],
      no_campaign_mutation_confirmed: true,
      no_policy_write_confirmed: true,
      no_link_generation_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_money_movement_confirmed: true,
    });

    await expect(
      getReferralSaasAccountCampaignReadiness({
        accountRef: " acct-1 ",
        campaignCode: " CAMP001 ",
        refType: "external_tenant_ref",
        externalRef: " fnb-referrals ",
        operation: "GENERATE_LINKS",
        context: "setup",
        opportunityId: " opp-1 ",
      }),
    ).resolves.toMatchObject({
      readiness: {
        readiness: "READY_WITH_WARNINGS",
      },
      no_campaign_activation_confirmed: true,
      no_money_movement_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/campaigns/CAMP001/readiness",
      {
        query: {
          ref_type: "external_tenant_ref",
          external_ref: "fnb-referrals",
          operation: "GENERATE_LINKS",
          context: "setup",
          opportunity_id: "opp-1",
          include_evidence: true,
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|wallet|settlement|money_movement|activate_campaign/,
    );
  });

  it("lists customer-scoped campaigns without requiring tenant code entry", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
      },
      count: 1,
      campaigns: [
        {
          campaignCode: "CAMP001",
          name: "Summer Referrals",
          segment: "REFERRAL",
          status: "ACTIVE",
          lifecycle: "ACTIVE",
          startsAt: "2026-07-01T00:00:00+00:00",
          endsAt: null,
          maxUses: 100,
          usesCount: 7,
          policyStatus: "ACTIVE_POLICY",
        },
      ],
      guardrail: "Read-only Referral SaaS customer-scoped campaign list.",
      redactions: ["internal_tenant_identifier"],
      no_campaign_mutation_confirmed: true,
      no_policy_write_confirmed: true,
      no_link_generation_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_money_movement_confirmed: true,
    });

    await expect(
      listReferralSaasAccountCampaigns({
        accountRef: " acct-1 ",
        refType: "external_tenant_ref",
        externalRef: " fnb-referrals ",
        context: "setup",
        limit: 25,
      }),
    ).resolves.toMatchObject({
      count: 1,
      campaigns: [{ campaignCode: "CAMP001", policyStatus: "ACTIVE_POLICY" }],
      no_campaign_mutation_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/accounts/acct-1/campaigns", {
      query: {
        ref_type: "external_tenant_ref",
        external_ref: "fnb-referrals",
        context: "setup",
        limit: 25,
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|wallet|settlement|money_movement|activate_campaign/,
    );
  });

  it("reads selected customer campaign attribution without exposing raw event payloads", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
      },
      campaignAttribution: {
        status: "READY",
        campaignCount: 1,
        sourceCount: 1,
        totalInteractions: 4,
        highConfidenceCount: 1,
        missingEvidenceCount: 0,
        conflictCount: 0,
        plainLanguage: "4 campaign interaction(s) found.",
        projections: [
          {
            campaignCode: "CAMP001",
            campaignName: "Summer Referrals",
            segment: "REFERRAL",
            campaignStatus: "ACTIVE",
            sourceChannel: "EMAIL",
            attributionStatus: "ATTRIBUTED",
            confidence: "HIGH",
            interactionCount: 4,
            linkedReferralCount: 3,
            eventCount: 5,
            evidence: ["3 linked referral record(s)."],
            gaps: [],
            explanation: "Summer Referrals has campaign attribution evidence from EMAIL.",
          },
        ],
        guardrails: ["READ_ONLY_CAMPAIGN_ATTRIBUTION"],
        redactions: ["internal_tenant_identifier", "raw_event_payload"],
      },
      guardrail: "Read-only Referral SaaS customer-scoped campaign attribution projection.",
      guardrails: ["READ_ONLY_CAMPAIGN_ATTRIBUTION"],
      redactions: ["internal_tenant_identifier", "raw_event_payload"],
      no_tenant_code_exposure_confirmed: true,
      no_raw_identity_exposure_confirmed: true,
      no_raw_event_payload_exposure_confirmed: true,
      no_attribution_mutation_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_webhook_delivery_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
      campaign_capability_enforced_confirmed: true,
      required_campaign_capability: "REFERRAL_SAAS_CAMPAIGN_READ",
    });

    await expect(
      getReferralSaasAccountCampaignAttribution({
        accountRef: " acct-1 ",
        refType: "external_tenant_ref",
        externalRef: " fnb-referrals ",
        context: "setup",
        limit: 25,
      }),
    ).resolves.toMatchObject({
      campaignAttribution: {
        status: "READY",
        projections: [{ campaignCode: "CAMP001", confidence: "HIGH" }],
      },
      no_raw_event_payload_exposure_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/campaign-attribution",
      {
        query: {
          ref_type: "external_tenant_ref",
          external_ref: "fnb-referrals",
          context: "setup",
          limit: 25,
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|raw_event_payload|client_secret|wallet|settlement|money_movement/,
    );
  });

  it("reads a selected customer-scoped campaign without requiring tenant code entry", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
      },
      campaign: {
        campaignCode: "CAMP002",
        name: "Partner Pilot",
        segment: "PARTNER",
        status: "DRAFT",
        lifecycle: "DRAFT",
        startsAt: null,
        endsAt: null,
        maxUses: null,
        usesCount: 0,
        policyStatus: "NO_ACTIVE_POLICY",
      },
      guardrail: "Read-only Referral SaaS customer-scoped campaign read.",
      redactions: ["internal_tenant_identifier"],
      no_campaign_mutation_confirmed: true,
      no_policy_write_confirmed: true,
      no_link_generation_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_money_movement_confirmed: true,
    });

    await expect(
      getReferralSaasAccountCampaign({
        accountRef: " acct-1 ",
        campaignCode: " CAMP002 ",
        refType: "external_tenant_ref",
        externalRef: " fnb-referrals ",
        context: "setup",
      }),
    ).resolves.toMatchObject({
      campaign: {
        campaignCode: "CAMP002",
        lifecycle: "DRAFT",
      },
      no_campaign_activation_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/accounts/acct-1/campaigns/CAMP002", {
      query: {
        ref_type: "external_tenant_ref",
        external_ref: "fnb-referrals",
        context: "setup",
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|wallet|settlement|money_movement|activate_campaign/,
    );
  });

  it("creates a customer-scoped inactive campaign setup without tenant code entry", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "created",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
      },
      campaignSetup: {
        commandStatus: "CAMPAIGN_SETUP_DRAFT_RECORDED",
        accountRef: "acct-1",
        campaign: {
          campaignRef: "FNB-RETAIL-SPRING-1234",
          campaignCode: "FNB-RETAIL-SPRING-1234",
          name: "Spring Referral Pilot",
          segment: "Retail banking customers",
          setupStatus: "DRAFT",
          isActive: false,
          startsAt: null,
          endsAt: null,
          maxUses: 100,
        },
        idempotency: { status: "RECORDED" },
        audit: { accountAuditEventId: "audit-1" },
        nextActions: ["Complete policy and attribution settings", "Run campaign readiness"],
        guardrails: ["NO_CAMPAIGN_ACTIVATION", "NO_POLICY_WRITE"],
        redactions: ["internal_tenant_identifier"],
      },
      guardrails: ["NO_CAMPAIGN_ACTIVATION", "NO_POLICY_WRITE"],
      redactions: ["internal_tenant_identifier"],
      no_campaign_activation_confirmed: true,
      no_link_generation_confirmed: true,
      no_validation_track_created_confirmed: true,
      no_policy_write_confirmed: true,
      no_webhook_delivery_confirmed: true,
      no_money_movement_confirmed: true,
    });

    await expect(
      createReferralSaasAccountCampaignSetup({
        accountRef: " acct-1 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
          context: "setup",
        },
        campaign: {
          name: " Spring Referral Pilot ",
          segment: " Retail banking customers ",
          startsAt: null,
          endsAt: null,
          maxUses: 100,
        },
        setupIntent: {
          reason: " Customer profile campaign setup ",
        },
        correlationId: "corr-1",
        idempotencyKey: "campaign-create-1",
      }),
    ).resolves.toMatchObject({
      campaignSetup: {
        campaign: {
          setupStatus: "DRAFT",
          isActive: false,
        },
      },
      no_campaign_activation_confirmed: true,
      no_policy_write_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/accounts/acct-1/campaigns", {
      method: "POST",
      body: {
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: "fnb-referrals",
          context: "setup",
        },
        campaign: {
          name: "Spring Referral Pilot",
          segment: "Retail banking customers",
          startsAt: null,
          endsAt: null,
          maxUses: 100,
        },
        setupIntent: {
          reason: "Customer profile campaign setup",
        },
        correlationId: "corr-1",
        idempotencyKey: "campaign-create-1",
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|isactive|activatecampaign|policywrite|linkgeneration|money/,
    );
  });

  it("updates customer-scoped campaign policy settings through the guarded wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
      },
      policySettings: {
        commandStatus: "POLICY_SETTINGS_RECORDED",
        accountRef: "acct-1",
        campaignRef: "CAMP001",
        policySettings: {
          version: 1,
          setupStatus: "POLICY_SETTINGS_READY",
          attributionWindowDays: 30,
          eligibilityRuleCount: 1,
          productWindowCount: 1,
          productRuleCount: 1,
          rewardVisibilityStatus: "CONFIGURED_WITHOUT_PAYMENT",
        },
        idempotency: { status: "RECORDED" },
        audit: { accountAuditEventId: "audit-policy-1" },
        nextActions: ["Run campaign readiness", "Review before activation"],
        guardrails: ["NO_CAMPAIGN_ACTIVATION", "NO_LINK_GENERATION"],
        redactions: ["internal_tenant_identifier"],
      },
      guardrails: ["NO_CAMPAIGN_ACTIVATION", "NO_LINK_GENERATION"],
      redactions: ["internal_tenant_identifier"],
      no_campaign_activation_confirmed: true,
      no_link_generation_confirmed: true,
      no_validation_track_created_confirmed: true,
      no_webhook_delivery_confirmed: true,
      no_money_movement_confirmed: true,
    });

    await expect(
      updateReferralSaasAccountCampaignPolicySettings({
        accountRef: " acct-1 ",
        campaignCode: " CAMP001 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
          context: "setup",
        },
        policySettings: {
          version: 1,
          attributionWindowDays: 30,
          eligibilityRules: [{ rule: " NEW_CUSTOMER_ONLY ", enabled: true }],
          productWindows: { default: { days: 30 } },
          productRules: { default: { requiresAcceptedTerms: true } },
          rewardVisibility: {
            mode: " configured_without_payment ",
            notes: " Visible after attribution ",
          },
        },
        setupIntent: {
          requestedStatus: " POLICY_SETTINGS_RECORDED ",
          reason: " Customer profile policy settings ",
        },
        reasonCode: " Customer profile policy settings ",
        correlationId: "corr-policy-1",
        idempotencyKey: "campaign-policy-1",
      }),
    ).resolves.toMatchObject({
      policySettings: {
        campaignRef: "CAMP001",
        policySettings: {
          attributionWindowDays: 30,
        },
      },
      no_campaign_activation_confirmed: true,
      no_link_generation_confirmed: true,
      no_money_movement_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/accounts/acct-1/campaigns/CAMP001/policy-settings", {
      method: "PUT",
      body: {
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: "fnb-referrals",
          context: "setup",
        },
        policySettings: {
          version: 1,
          attributionWindowDays: 30,
          eligibilityRules: [{ rule: "NEW_CUSTOMER_ONLY", enabled: true }],
          productWindows: { default: { days: 30 } },
          productRules: { default: { requiresAcceptedTerms: true } },
          rewardVisibility: {
            mode: "configured_without_payment",
            notes: "Visible after attribution",
          },
        },
        setupIntent: {
          requestedStatus: "POLICY_SETTINGS_RECORDED",
          reason: "Customer profile policy settings",
        },
        reasonCode: "Customer profile policy settings",
        correlationId: "corr-policy-1",
        idempotencyKey: "campaign-policy-1",
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|isactive|activatecampaign|linkgeneration|webhook|wallet|settlement|money/,
    );
  });

  it("submits a customer-scoped campaign for review through the guarded wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
      },
      campaignReview: {
        commandStatus: "CAMPAIGN_REVIEW_SUBMITTED",
        accountRef: "acct-1",
        campaignRef: "CAMP001",
        previousReviewStatus: "POLICY_SETTINGS_READY",
        reviewStatus: "READY_FOR_REVIEW",
        setupStatus: "POLICY_SETTINGS_READY",
        readinessStatus: "READY_WITH_WARNINGS",
        activationEligibility: "NOT_ELIGIBLE_UNTIL_REVIEW_APPROVED",
        activationStatus: "INACTIVE",
        reviewerAction: "Review campaign setup evidence",
        idempotency: { status: "RECORDED" },
        audit: { accountAuditEventId: "audit-review-1" },
        nextActions: ["Record review decision"],
        guardrails: ["NO_CAMPAIGN_ACTIVATION", "NO_LINK_GENERATION"],
        redactions: ["internal_tenant_identifier"],
      },
      guardrails: ["NO_CAMPAIGN_ACTIVATION", "NO_LINK_GENERATION"],
      redactions: ["internal_tenant_identifier"],
      no_campaign_activation_confirmed: true,
      no_link_generation_confirmed: true,
      no_validation_track_created_confirmed: true,
      no_webhook_delivery_confirmed: true,
      no_invite_or_seat_change_confirmed: true,
      no_money_movement_confirmed: true,
    });

    await expect(
      submitReferralSaasAccountCampaignReview({
        accountRef: " acct-1 ",
        campaignCode: " CAMP001 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
          context: "setup",
        },
        reviewSubmission: {
          setupSummary: " Campaign setup and policy settings are ready. ",
          requestedReviewStatus: " READY_FOR_REVIEW ",
          operatorNotes: " Safe review notes. ",
        },
        reasonCode: " Customer campaign review ",
        correlationId: "corr-review-1",
        idempotencyKey: "campaign-review-1",
      }),
    ).resolves.toMatchObject({
      campaignReview: {
        campaignRef: "CAMP001",
        reviewStatus: "READY_FOR_REVIEW",
      },
      no_campaign_activation_confirmed: true,
      no_money_movement_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/campaigns/CAMP001/review-submissions",
      {
        method: "POST",
        body: {
          accountScope: {
            refType: "external_tenant_ref",
            externalRef: "fnb-referrals",
            context: "setup",
          },
          reviewSubmission: {
            setupSummary: "Campaign setup and policy settings are ready.",
            requestedReviewStatus: "READY_FOR_REVIEW",
            operatorNotes: "Safe review notes.",
          },
          reasonCode: "Customer campaign review",
          correlationId: "corr-review-1",
          idempotencyKey: "campaign-review-1",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|isactive|activatecampaign|linkgeneration|webhook|seat|authclaim|wallet|settlement|money/,
    );
  });

  it("records a customer-scoped campaign review decision through the guarded wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
      },
      campaignReview: {
        commandStatus: "CAMPAIGN_REVIEW_DECISION_RECORDED",
        accountRef: "acct-1",
        campaignRef: "CAMP001",
        previousReviewStatus: "READY_FOR_REVIEW",
        reviewStatus: "REVIEW_APPROVED",
        setupStatus: "POLICY_SETTINGS_READY",
        readinessStatus: "READY_WITH_WARNINGS",
        activationEligibility: "ELIGIBLE_FOR_FUTURE_ACTIVATION",
        activationStatus: "INACTIVE",
        reviewerAction: "Activation remains a separate command",
        idempotency: { status: "RECORDED" },
        audit: { accountAuditEventId: "audit-review-decision-1" },
        nextActions: ["Prepare activation request"],
        guardrails: ["NO_CAMPAIGN_ACTIVATION", "NO_LINK_GENERATION"],
        redactions: ["internal_tenant_identifier"],
      },
      guardrails: ["NO_CAMPAIGN_ACTIVATION", "NO_LINK_GENERATION"],
      redactions: ["internal_tenant_identifier"],
      no_campaign_activation_confirmed: true,
      no_link_generation_confirmed: true,
      no_validation_track_created_confirmed: true,
      no_webhook_delivery_confirmed: true,
      no_invite_or_seat_change_confirmed: true,
      no_money_movement_confirmed: true,
    });

    await expect(
      recordReferralSaasAccountCampaignReviewDecision({
        accountRef: " acct-1 ",
        campaignCode: " CAMP001 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
          context: "setup",
        },
        reviewDecision: {
          decision: "APPROVED",
          reason: " Reviewed and approved. ",
          reviewerRef: " amplifi-admin ",
        },
        reasonCode: " Customer campaign review decision ",
        correlationId: "corr-review-decision-1",
        idempotencyKey: "campaign-review-decision-1",
      }),
    ).resolves.toMatchObject({
      campaignReview: {
        campaignRef: "CAMP001",
        reviewStatus: "REVIEW_APPROVED",
        activationEligibility: "ELIGIBLE_FOR_FUTURE_ACTIVATION",
      },
      no_campaign_activation_confirmed: true,
      no_money_movement_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/campaigns/CAMP001/review-decisions",
      {
        method: "POST",
        body: {
          accountScope: {
            refType: "external_tenant_ref",
            externalRef: "fnb-referrals",
            context: "setup",
          },
          reviewDecision: {
            decision: "APPROVED",
            reason: "Reviewed and approved.",
            reviewerRef: "amplifi-admin",
          },
          reasonCode: "Customer campaign review decision",
          correlationId: "corr-review-decision-1",
          idempotencyKey: "campaign-review-decision-1",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|isactive|activatecampaign|linkgeneration|webhook|seat|authclaim|wallet|settlement|money/,
    );
  });

  it("requests customer-scoped campaign activation through the guarded wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-1",
        accountCode: "FNB_REFERRAL_SAAS",
      },
      campaignActivation: {
        commandStatus: "CAMPAIGN_ACTIVATION_ACCEPTED",
        accountRef: "acct-1",
        campaignRef: "CAMP001",
        campaignActivation: {
          previousLifecycle: "READY_TO_ACTIVATE",
          lifecycle: "ACTIVE",
          reviewStatus: "REVIEW_APPROVED",
          activationEligibility: "ELIGIBLE_FOR_FUTURE_ACTIVATION",
          activationStatus: "ACTIVATION_REQUEST_ACCEPTED",
          readinessStatus: "READY_TO_ACTIVATE",
        },
        idempotency: { status: "RECORDED" },
        audit: { accountAuditEventId: "audit-campaign-activation-1" },
        nextActions: ["Open customer campaign operations"],
        guardrails: ["NO_LINK_GENERATION", "NO_BILLING_OR_MONEY_MOVEMENT"],
        redactions: ["internal_tenant_identifier"],
      },
      guardrails: ["NO_LINK_GENERATION", "NO_BILLING_OR_MONEY_MOVEMENT"],
      redactions: ["internal_tenant_identifier"],
      no_link_generation_confirmed: true,
      no_validation_track_created_confirmed: true,
      no_webhook_delivery_confirmed: true,
      no_invite_or_seat_change_confirmed: true,
      no_credential_creation_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      requestReferralSaasAccountCampaignActivation({
        accountRef: " acct-1 ",
        campaignCode: " CAMP001 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
          context: "setup",
        },
        activationRequest: {
          requestedLifecycleStatus: "ACTIVE",
          reviewStatus: "REVIEW_APPROVED",
          goLiveReason: " Approved campaign review. ",
          operatorNotes: " Activate only this campaign posture. ",
        },
        reasonCode: " Customer campaign activation ",
        correlationId: "corr-activation-1",
        idempotencyKey: "campaign-activation-1",
      }),
    ).resolves.toMatchObject({
      campaignActivation: {
        campaignRef: "CAMP001",
        campaignActivation: {
          lifecycle: "ACTIVE",
          activationStatus: "ACTIVATION_REQUEST_ACCEPTED",
        },
      },
      no_link_generation_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/campaigns/CAMP001/activation-requests",
      {
        method: "POST",
        body: {
          accountScope: {
            refType: "external_tenant_ref",
            externalRef: "fnb-referrals",
            context: "setup",
          },
          activationRequest: {
            requestedLifecycleStatus: "ACTIVE",
            reviewStatus: "REVIEW_APPROVED",
            goLiveReason: "Approved campaign review.",
            operatorNotes: "Activate only this campaign posture.",
            activationWindow: undefined,
          },
          reasonCode: "Customer campaign activation",
          correlationId: "corr-activation-1",
          idempotencyKey: "campaign-activation-1",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|linkgeneration|webhookdelivery|credential|billing|wallet|settlement|moneymovement/,
    );
  });

  it("records Referral SaaS membership invitation intent through the bounded product wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acc_fnb",
        accountCode: "FNB_REFERRAL_SAAS",
      },
      invitation: {
        commandStatus: "INVITATION_INTENT_RECORDED",
        membership: {
          membershipRef: "mbr_1",
          status: "INVITED",
          roleFamily: "DISTRIBUTION_ADMIN",
          permissionSet: "REFERRAL_SAAS_ACCOUNT_ADMIN",
          canOperateSetup: false,
        },
        delivery: {
          status: "DELIVERY_NOT_CONFIGURED",
          nextAction: "Configure approved invitation delivery provider",
        },
        idempotency: {
          status: "RECORDED",
        },
        auditEventId: "audit_1",
        guardrails: ["NO_RAW_EMAIL_STORAGE", "NO_EMAIL_DELIVERY_WITHOUT_PROVIDER"],
        redactions: ["internal_tenant_identifier", "email_hash"],
        noInviteDeliveryConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noMoneyMovementConfirmed: true,
      },
      guardrails: ["NO_RAW_EMAIL_STORAGE", "NO_EMAIL_DELIVERY_WITHOUT_PROVIDER"],
      redactions: ["internal_tenant_identifier", "email_hash"],
      no_invite_delivery_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_money_movement_confirmed: true,
    });

    await expect(
      recordReferralSaasMembershipInvitationIntent({
        accountRef: " acc_fnb ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " demo-platform-operator ",
          context: "setup",
        },
        actor: {
          actorType: "USER",
          subject: " setup-owner ",
          emailHash: " email-hash-only ",
          displayName: " Referral SaaS setup owner ",
        },
        membership: {
          roleFamily: "DISTRIBUTION_ADMIN",
          permissionSet: "REFERRAL_SAAS_ACCOUNT_ADMIN",
        },
        correlationId: "referral-saas-account-setup-membership-invitation",
        idempotencyKey: "membership-invitation:acc_fnb:setup-owner",
      }),
    ).resolves.toMatchObject({
      invitation: {
        commandStatus: "INVITATION_INTENT_RECORDED",
        delivery: {
          status: "DELIVERY_NOT_CONFIGURED",
        },
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/accounts/acc_fnb/membership-invitations", {
      method: "POST",
      body: {
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: "demo-platform-operator",
          context: "setup",
        },
        actor: {
          actorType: "USER",
          subject: "setup-owner",
          clientId: undefined,
          emailHash: "email-hash-only",
          displayName: "Referral SaaS setup owner",
        },
        membership: {
          roleFamily: "DISTRIBUTION_ADMIN",
          permissionSet: "REFERRAL_SAAS_ACCOUNT_ADMIN",
          tenantScope: "PRIMARY_ACCOUNT_TENANT",
        },
        reasonCode: "ACCOUNT_SETUP_USER_ROLE",
        correlationId: "referral-saas-account-setup-membership-invitation",
        idempotencyKey: "membership-invitation:acc_fnb:setup-owner",
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|wallet|settlement|money_movement|send_invite|activate/,
    );
  });

  it("requests Referral SaaS invitation delivery boundary without browser recipient hashes", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "blocked",
      context: "setup",
      account: {
        accountId: "acc_fnb",
        accountCode: "FNB_REFERRAL_SAAS",
      },
      deliveryRequest: {
        commandStatus: "DELIVERY_PROVIDER_NOT_CONFIGURED",
        membership: {
          membershipRef: "mbr_1",
          status: "INVITED",
          roleFamily: "DISTRIBUTION_ADMIN",
          permissionSet: "REFERRAL_SAAS_ACCOUNT_ADMIN",
        },
        delivery: {
          status: "DELIVERY_PROVIDER_NOT_CONFIGURED",
          nextAction: "Configure approved invitation delivery provider before sending email invites.",
          recipientContactStatus: "CONTACT_REFERENCE_PRESENT",
          providerRef: "mail-provider-1",
          channel: "EMAIL",
          templateRef: "referral-saas-account-invite-v1",
        },
        idempotency: {
          status: "RECORDED",
        },
        auditEventId: "audit-delivery-1",
        guardrails: ["NO_EMAIL_DELIVERY_WITHOUT_PROVIDER"],
        redactions: ["recipient_hash", "provider_secret"],
        noInviteDeliveryConfirmed: true,
        noMembershipActivationConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noMoneyMovementConfirmed: true,
      },
      guardrails: ["NO_EMAIL_DELIVERY_WITHOUT_PROVIDER"],
      redactions: ["recipient_hash", "provider_secret"],
      no_invite_delivery_confirmed: true,
      no_membership_activation_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_money_movement_confirmed: true,
    });

    await expect(
      requestReferralSaasMembershipInvitationDelivery({
        accountRef: " acc_fnb ",
        membershipRef: " mbr_1 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
          context: "setup",
        },
        delivery: {
          providerRef: " mail-provider-1 ",
          channel: "EMAIL",
          templateRef: " referral-saas-account-invite-v1 ",
        },
        correlationId: "customer-profile-invite-delivery-acc_fnb",
        idempotencyKey: "customer-profile-invite-delivery-acc_fnb-mbr_1-distribution_admin",
      }),
    ).resolves.toMatchObject({
      deliveryRequest: {
        delivery: {
          recipientContactStatus: "CONTACT_REFERENCE_PRESENT",
        },
      },
      no_invite_delivery_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acc_fnb/membership-invitations/mbr_1/delivery",
      {
        method: "POST",
        body: {
          accountScope: {
            refType: "external_tenant_ref",
            externalRef: "fnb-referrals",
            context: "setup",
          },
          delivery: {
            providerRef: "mail-provider-1",
            channel: "EMAIL",
            templateRef: "referral-saas-account-invite-v1",
          },
          reasonCode: "CUSTOMER_PROFILE_INVITE_DELIVERY_REQUEST",
          correlationId: "customer-profile-invite-delivery-acc_fnb",
          idempotencyKey: "customer-profile-invite-delivery-acc_fnb-mbr_1-distribution_admin",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /recipienthash|tenant_code|client_secret|wallet|settlement|money_movement|send_invite|activate/,
    );
  });

  it("updates an invited Referral SaaS access intent without live invite side effects", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acc_fnb",
        accountCode: "FNB_REFERRAL_SAAS",
      },
      invitation: {
        commandStatus: "INVITATION_INTENT_UPDATED",
        membership: {
          membershipRef: "mbr_1",
          previousStatus: "INVITED",
          status: "INVITED",
          roleFamily: "CAMPAIGN_MANAGER",
          permissionSet: "REFERRAL_SAAS_CAMPAIGN_MANAGER",
        },
        lifecycle: {
          status: "INVITATION_INTENT_UPDATED",
          nextAction: "Review the updated access intent before invite delivery or activation.",
        },
        idempotency: {
          status: "RECORDED",
        },
        guardrails: ["NO_RAW_EMAIL_STORAGE"],
        redactions: ["email_hash"],
        noInviteDeliveryConfirmed: true,
        noMembershipActivationConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noMoneyMovementConfirmed: true,
      },
    });

    await expect(
      updateReferralSaasMembershipInvitationIntent({
        accountRef: " acc_fnb ",
        membershipRef: " mbr_1 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " demo-platform-operator ",
          context: "setup",
        },
        actor: {
          emailHash: " safe-email-hash ",
          displayName: " Campaign Owner ",
        },
        membership: {
          roleFamily: " CAMPAIGN_MANAGER ",
          permissionSet: " REFERRAL_SAAS_CAMPAIGN_MANAGER ",
        },
        correlationId: "corr-1",
        idempotencyKey: "update-1",
      }),
    ).resolves.toMatchObject({
      invitation: {
        commandStatus: "INVITATION_INTENT_UPDATED",
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acc_fnb/membership-invitations/mbr_1",
      {
        method: "PATCH",
        body: {
          accountScope: {
            refType: "external_tenant_ref",
            externalRef: "demo-platform-operator",
            context: "setup",
          },
          actor: {
            emailHash: "safe-email-hash",
            displayName: "Campaign Owner",
          },
          membership: {
            roleFamily: "CAMPAIGN_MANAGER",
            permissionSet: "REFERRAL_SAAS_CAMPAIGN_MANAGER",
          },
          reasonCode: "CUSTOMER_PROFILE_ACCESS_INTENT_UPDATE",
          correlationId: "corr-1",
          idempotencyKey: "update-1",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|wallet|settlement|money_movement|send_invite|activate/,
    );
  });

  it("cancels an invited Referral SaaS access intent as a lifecycle state", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acc_fnb",
        accountCode: "FNB_REFERRAL_SAAS",
      },
      invitation: {
        commandStatus: "INVITATION_INTENT_CANCELLED",
        membership: {
          membershipRef: "mbr_1",
          previousStatus: "INVITED",
          status: "DISABLED",
          roleFamily: "DISTRIBUTION_ADMIN",
          permissionSet: "REFERRAL_SAAS_ACCOUNT_ADMIN",
        },
        lifecycle: {
          status: "INVITATION_INTENT_CANCELLED",
          nextAction: "Record a new access intent if this person should manage the customer again.",
        },
        idempotency: {
          status: "RECORDED",
        },
        guardrails: ["NO_RAW_EMAIL_STORAGE"],
        redactions: ["email_hash"],
        noInviteDeliveryConfirmed: true,
        noMembershipActivationConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noMoneyMovementConfirmed: true,
      },
    });

    await expect(
      cancelReferralSaasMembershipInvitationIntent({
        accountRef: " acc_fnb ",
        membershipRef: " mbr_1 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " demo-platform-operator ",
          context: "setup",
        },
        correlationId: "corr-1",
        idempotencyKey: "cancel-1",
      }),
    ).resolves.toMatchObject({
      invitation: {
        membership: {
          status: "DISABLED",
        },
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acc_fnb/membership-invitations/mbr_1",
      {
        method: "DELETE",
        body: {
          accountScope: {
            refType: "external_tenant_ref",
            externalRef: "demo-platform-operator",
            context: "setup",
          },
          reasonCode: "CUSTOMER_PROFILE_ACCESS_INTENT_CANCEL",
          correlationId: "corr-1",
          idempotencyKey: "cancel-1",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|wallet|settlement|money_movement|send_invite|activate/,
    );
  });

  it("requests Referral SaaS membership activation through the bounded product wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acc_fnb",
        accountCode: "FNB_REFERRAL_SAAS",
      },
      activationRequest: {
        commandStatus: "MEMBERSHIP_ACTIVATED",
        membership: {
          membershipRef: "mbr_1",
          previousStatus: "INVITED",
          status: "ACTIVE",
          roleFamily: "DISTRIBUTION_ADMIN",
          permissionSet: "REFERRAL_SAAS_ACCOUNT_ADMIN",
        },
        activation: {
          status: "MEMBERSHIP_ACTIVATED",
          acceptedSubjectStatus: "ACCEPTED_SUBJECT_MATCHED",
          nextAction: "Membership lifecycle is active. Configure seats and auth claims only through their separate governed workflows.",
        },
        idempotency: {
          status: "RECORDED",
        },
        auditEventId: "audit-activation-1",
        guardrails: ["NO_INVITE_DELIVERY", "NO_AUTH_PROVIDER_WRITE"],
        redactions: ["accepted_subject", "acceptance_evidence_ref"],
        noInviteDeliveryConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noMoneyMovementConfirmed: true,
      },
      guardrails: ["NO_INVITE_DELIVERY", "NO_AUTH_PROVIDER_WRITE"],
      redactions: ["accepted_subject", "acceptance_evidence_ref"],
      no_invite_delivery_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_money_movement_confirmed: true,
    });

    await expect(
      requestReferralSaasMembershipActivation({
        accountRef: " acc_fnb ",
        membershipRef: " mbr_1 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
          context: "setup",
        },
        activation: {
          acceptedSubject: " owner@example.test ",
          acceptanceEvidenceRef: " customer-profile-accepted-acc_fnb-mbr_1 ",
        },
        correlationId: "customer-profile-access-activation-acc_fnb",
        idempotencyKey: "customer-profile-access-activation-acc_fnb-mbr_1-distribution_admin",
      }),
    ).resolves.toMatchObject({
      activationRequest: {
        commandStatus: "MEMBERSHIP_ACTIVATED",
        membership: {
          status: "ACTIVE",
        },
      },
      no_auth_claim_change_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_money_movement_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acc_fnb/memberships/mbr_1/activation",
      {
        method: "POST",
        body: {
          accountScope: {
            refType: "external_tenant_ref",
            externalRef: "fnb-referrals",
            context: "setup",
          },
          activation: {
            acceptedSubject: "owner@example.test",
            acceptanceEvidenceRef: "customer-profile-accepted-acc_fnb-mbr_1",
          },
          reasonCode: "CUSTOMER_PROFILE_MEMBERSHIP_ACTIVATION_REQUEST",
          correlationId: "customer-profile-access-activation-acc_fnb",
          idempotencyKey: "customer-profile-access-activation-acc_fnb-mbr_1-distribution_admin",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|wallet|settlement|money_movement|sendinvite|seatid|authclaims|golive/,
    );
  });

  it("requests Referral SaaS access provisioning through the guarded product wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acc_fnb",
        accountCode: "FNB_REFERRAL_SAAS",
      },
      accessProvisioning: {
        commandStatus: "PROVISIONING_REQUEST_RECORDED",
        membership: {
          membershipRef: "mbr_1",
          roleFamily: "DISTRIBUTION_ADMIN",
          permissionSet: "REFERRAL_SAAS_ACCOUNT_ADMIN",
        },
        seat: {
          seatType: "ADMIN",
          seatAssignmentStatus: "SEAT_ASSIGNED",
          seatRef: "seat-1",
        },
        authClaims: {
          authClaimStatus: "AUTH_CLAIMS_NOT_PROPAGATED",
        },
        provisioning: {
          status: "PROVISIONING_REQUEST_RECORDED",
          nextAction: "Seat assigned. Auth claims remain separate.",
        },
        idempotency: {
          status: "RECORDED",
        },
        auditEventId: "audit-provisioning-1",
        guardrails: ["NO_INVITE_DELIVERY", "NO_AUTH_CLAIM_CHANGE"],
        redactions: ["seat_assignment_evidence_ref"],
        noInviteDeliveryConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noCredentialCreationConfirmed: true,
        noCampaignActivationConfirmed: true,
        noGoLiveChangeConfirmed: true,
        noMoneyMovementConfirmed: true,
      },
      guardrails: ["NO_INVITE_DELIVERY", "NO_AUTH_CLAIM_CHANGE"],
      redactions: ["seat_assignment_evidence_ref"],
      no_invite_delivery_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_credential_creation_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_go_live_change_confirmed: true,
      no_money_movement_confirmed: true,
    });

    await expect(
      requestReferralSaasAccessProvisioning({
        accountRef: " acc_fnb ",
        membershipRef: " mbr_1 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
          context: "setup",
        },
        provisioning: {
          seatType: "ADMIN",
          seatAssignmentEvidenceRef: " seat-evidence-1 ",
          operatorNotes: " Provision account owner seat. ",
        },
        correlationId: "customer-profile-access-provisioning-acc_fnb",
        idempotencyKey: "customer-profile-access-provisioning-acc_fnb-mbr_1-distribution_admin-admin",
      }),
    ).resolves.toMatchObject({
      accessProvisioning: {
        commandStatus: "PROVISIONING_REQUEST_RECORDED",
        seat: {
          seatAssignmentStatus: "SEAT_ASSIGNED",
        },
        authClaims: {
          authClaimStatus: "AUTH_CLAIMS_NOT_PROPAGATED",
        },
      },
      no_auth_claim_change_confirmed: true,
      no_credential_creation_confirmed: true,
      no_money_movement_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acc_fnb/memberships/mbr_1/access-provisioning",
      {
        method: "POST",
        body: {
          accountScope: {
            refType: "external_tenant_ref",
            externalRef: "fnb-referrals",
            context: "setup",
          },
          provisioning: {
            seatType: "ADMIN",
            seatAssignmentEvidenceRef: "seat-evidence-1",
            authProviderRef: undefined,
            authClaimEvidenceRef: undefined,
            operatorNotes: "Provision account owner seat.",
          },
          reasonCode: "CUSTOMER_PROFILE_ACCESS_PROVISIONING_REQUEST",
          correlationId: "customer-profile-access-provisioning-acc_fnb",
          idempotencyKey: "customer-profile-access-provisioning-acc_fnb-mbr_1-distribution_admin-admin",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|password|raw_auth|authclaims|sendinvite|campaignactivation|golive|wallet|settlement|money/,
    );
  });

  it("records Referral SaaS login completion intent without credentials or auth claim mutation", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acc_fnb",
        accountCode: "FNB_REFERRAL_SAAS",
        accountStatus: "ACTIVE",
      },
      loginCompletionIntent: {
        commandStatus: "LOGIN_COMPLETION_RECORDED",
        loginCompletionStatus: "LOGIN_COMPLETION_RECORDED",
        membership: {
          membershipRef: "mbr_1",
          roleFamily: "DISTRIBUTION_ADMIN",
          permissionProfile: "REFERRAL_SAAS_ACCOUNT_ADMIN",
        },
        loginCompletion: {
          intent: "PLATFORM_LOGIN_REQUIRED",
          seatAssignmentStatus: "SEAT_ASSIGNED",
          identityProviderStatus: "AUTH_PROVIDER_READY",
          authClaimStatus: "AUTH_CLAIMS_NOT_PROPAGATED",
          nextAction: "Login completion evidence is recorded; auth claims remain separately governed.",
        },
        idempotency: {
          status: "NEW_REQUEST",
        },
        auditEventId: "audit-login-1",
        guardrails: ["NO_CREDENTIAL_CREATION", "NO_AUTH_CLAIM_CHANGE"],
        redactions: ["internal_tenant_identifier"],
        noInviteDeliveryConfirmed: true,
        noCredentialCreationConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noCampaignActivationConfirmed: true,
        noGoLiveChangeConfirmed: true,
        noMoneyMovementConfirmed: true,
      },
      guardrails: ["NO_CREDENTIAL_CREATION", "NO_AUTH_CLAIM_CHANGE"],
      redactions: ["internal_tenant_identifier"],
      no_invite_delivery_confirmed: true,
      no_credential_creation_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_go_live_change_confirmed: true,
      no_money_movement_confirmed: true,
    });

    await expect(
      requestReferralSaasLoginCompletionIntent({
        accountRef: " acc_fnb ",
        membershipRef: " mbr_1 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
          context: "setup",
        },
        loginCompletion: {
          intent: "PLATFORM_LOGIN_REQUIRED",
          identitySubjectRef: " identity-1 ",
          authProviderRef: " auth-provider-1 ",
          seatEvidenceRef: " seat-evidence-1 ",
          permissionProfile: " REFERRAL_SAAS_ACCOUNT_ADMIN ",
          operatorReason: " Login completion reviewed by Amplifi Admin. ",
        },
        correlationId: "customer-profile-login-completion-acc_fnb",
        idempotencyKey: "customer-profile-login-completion-acc_fnb-mbr_1-distribution-admin-platform-login-required",
      }),
    ).resolves.toMatchObject({
      loginCompletionIntent: {
        commandStatus: "LOGIN_COMPLETION_RECORDED",
        loginCompletionStatus: "LOGIN_COMPLETION_RECORDED",
      },
      no_credential_creation_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_money_movement_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acc_fnb/memberships/mbr_1/login-completion-intents",
      {
        method: "POST",
        body: {
          accountScope: {
            refType: "external_tenant_ref",
            externalRef: "fnb-referrals",
            context: "setup",
          },
          loginCompletion: {
            intent: "PLATFORM_LOGIN_REQUIRED",
            identitySubjectRef: "identity-1",
            authProviderRef: "auth-provider-1",
            seatEvidenceRef: "seat-evidence-1",
            permissionProfile: "REFERRAL_SAAS_ACCOUNT_ADMIN",
            operatorReason: "Login completion reviewed by Amplifi Admin.",
          },
          reasonCode: "CUSTOMER_PROFILE_LOGIN_COMPLETION_INTENT",
          correlationId: "customer-profile-login-completion-acc_fnb",
          idempotencyKey: "customer-profile-login-completion-acc_fnb-mbr_1-distribution-admin-platform-login-required",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|password|raw_auth|authclaims|sendinvite|campaignactivation|golive|wallet|settlement|money/,
    );
  });

  it("requests Referral SaaS account foundation activation through the guarded product wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acc_fnb",
        accountCode: "FNB_REFERRAL_SAAS",
        accountStatus: "PENDING_ONBOARDING",
      },
      activation: {
        accountId: "acc_fnb",
        accountCode: "FNB_REFERRAL_SAAS",
        accountName: "FNB Referral SaaS",
        previousAccountStatus: "PENDING_ONBOARDING",
        accountStatus: "ACTIVE",
        previousOnboardingStatus: "READY_FOR_REVIEW",
        onboardingStatus: "APPROVED",
        previousTenantLinkStatus: "PENDING_SETUP",
        tenantLinkStatus: "ACTIVE",
        seatCapacity: { seatTypes: ["ADMIN", "OPERATOR"], createdSeatCount: 2 },
        commandStatus: "ACCOUNT_FOUNDATION_ACTIVATED",
        auditEventId: "audit-account-activation-1",
        idempotency: { status: "NEW_REQUEST" },
        guardrails: ["NO_MEMBERSHIP_WRITE", "NO_SEAT_ASSIGNMENT"],
        redactions: ["internal_tenant_identifier"],
        noMembershipWriteConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noInviteDeliveryConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noCredentialCreationConfirmed: true,
        noCampaignActivationConfirmed: true,
        noGoLiveActionConfirmed: true,
        noBillingOrMoneyMovementConfirmed: true,
      },
      guardrails: ["NO_MEMBERSHIP_WRITE", "NO_SEAT_ASSIGNMENT"],
      redactions: ["internal_tenant_identifier"],
      no_membership_write_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_invite_delivery_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_credential_creation_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_go_live_action_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      requestReferralSaasAccountFoundationActivation({
        accountRef: " acc_fnb ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
          context: "setup",
        },
        activation: { seatTypes: ["ADMIN", "OPERATOR"] },
        reasonCode: " Activate customer foundation ",
        correlationId: "customer-profile-account-foundation-activation-acc_fnb",
        idempotencyKey: "customer-profile-account-foundation-activation-acc_fnb-v1",
      }),
    ).resolves.toMatchObject({
      activation: {
        commandStatus: "ACCOUNT_FOUNDATION_ACTIVATED",
        accountStatus: "ACTIVE",
        tenantLinkStatus: "ACTIVE",
        seatCapacity: { createdSeatCount: 2 },
      },
      no_membership_write_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/accounts/acc_fnb/activation-requests", {
      method: "POST",
      body: {
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: "fnb-referrals",
          context: "setup",
        },
        activation: {
          seatTypes: ["ADMIN", "OPERATOR"],
        },
        reasonCode: "Activate customer foundation",
        correlationId: "customer-profile-account-foundation-activation-acc_fnb",
        idempotencyKey: "customer-profile-account-foundation-activation-acc_fnb-v1",
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|password|raw_auth|authclaims|sendinvite|membershipwrite|seatassignment|campaignactivation|golive|wallet|settlement|money/,
    );
  });

  it("updates Referral SaaS customer profile settings through the bounded product wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      profile: {
        accountId: "acct-1",
        accountCode: "ACCT_FNB",
        accountName: "FNB Referral SaaS Updated",
        accountType: "ORGANISATION",
        accountStatus: "PENDING_ONBOARDING",
        onboardingStatus: "READY_FOR_REVIEW",
        operatingJurisdictionCode: "ZA",
        customerType: "ENTERPRISE_CUSTOMER",
        industry: "AUTOMOTIVE",
        auditEventId: "audit-1",
        guardrails: ["DURABLE_PROFILE_FIELDS_ONLY", "NO_EXTERNAL_REFERENCE_ROTATION"],
        redactions: ["internal_tenant_identifier"],
      },
      guardrails: ["DURABLE_PROFILE_FIELDS_ONLY", "NO_EXTERNAL_REFERENCE_ROTATION"],
      redactions: ["internal_tenant_identifier"],
      no_external_reference_rotation_confirmed: true,
      no_account_activation_confirmed: true,
      no_membership_write_confirmed: true,
      no_invite_delivery_confirmed: true,
      no_money_movement_confirmed: true,
    });

    await expect(
      updateReferralSaasAccountProfile({
        accountRef: " acct-1 ",
        profile: {
          accountName: " FNB Referral SaaS Updated ",
          accountType: " ORGANISATION ",
          operatingJurisdictionCode: " ZA ",
          customerType: " ENTERPRISE_CUSTOMER ",
          industry: " AUTOMOTIVE ",
        },
        correlationId: "customer-profile-settings-acct-1",
        idempotencyKey: "customer-profile-settings-acct-1",
      }),
    ).resolves.toMatchObject({
      profile: {
        accountName: "FNB Referral SaaS Updated",
        customerType: "ENTERPRISE_CUSTOMER",
      },
      no_external_reference_rotation_confirmed: true,
      no_money_movement_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/accounts/acct-1/profile", {
      method: "PATCH",
      body: {
        profile: {
          accountName: "FNB Referral SaaS Updated",
          accountType: "ORGANISATION",
          operatingJurisdictionCode: "ZA",
          customerType: "ENTERPRISE_CUSTOMER",
          industry: "AUTOMOTIVE",
        },
        correlationId: "customer-profile-settings-acct-1",
        idempotencyKey: "customer-profile-settings-acct-1",
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|externaltenantref|client_secret|wallet|settlement|money_movement|activate/,
    );
  });

  it("lists selected-customer support cases through the account-scoped wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: { accountId: "acct-1", accountCode: "ACCT_FNB" },
      supportCases: [],
      guardrails: ["NO_REPAIR_REPLAY_RETRY"],
      redactions: ["internal_tenant_identifier"],
      no_tenant_code_exposure_confirmed: true,
      no_product_state_mutation_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      listReferralSaasAccountSupportCases({
        accountRef: " acct-1 ",
        refType: "external_tenant_ref",
        externalRef: " fnb-referrals ",
        context: "setup",
        status: " OPEN ",
        limit: 25,
      }),
    ).resolves.toMatchObject({
      supportCases: [],
      no_product_state_mutation_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/accounts/acct-1/support-cases", {
      query: {
        ref_type: "external_tenant_ref",
        external_ref: "fnb-referrals",
        context: "setup",
        status: "OPEN",
        limit: 25,
      },
    });
  });

  it("reads selected-customer support-case repair/replay readiness through the read-only wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "support",
      account: { accountId: "acct-1", accountCode: "ACCT_FNB" },
      repairReplayReadiness: {
        caseRef: "case-1",
        accountRef: "acct-1",
        category: "PROGRESS_DIAGNOSTIC",
        status: "OPEN",
        overallStatus: "REVIEW_REQUIRED",
        actionSummary: "Readiness only.",
        owningWorkflow: "progress_status",
        allowedActions: [
          {
            action: "READ_ONLY_DIAGNOSTIC",
            status: "AVAILABLE",
            label: "Review support evidence",
            reasonCode: "EVIDENCE_AVAILABLE",
          },
          {
            action: "GOVERNED_REPLAY",
            status: "BLOCKED",
            label: "Replay stored progress evidence",
            reasonCode: "FUTURE_GOVERNED_COMMAND_REQUIRED",
          },
        ],
        requiredEvidence: ["support_case_link", "before_state_hash"],
        supportCase: {
          caseRef: "case-1",
          accountRef: "acct-1",
          category: "PROGRESS_DIAGNOSTIC",
          priority: "HIGH",
          status: "OPEN",
          title: "Progress event missing",
          summary: "The customer cannot see progress.",
          createdByRef: "operator",
          evidenceLinks: [],
          redactions: ["internal_tenant_identifier"],
        },
        guardrails: ["READ_ONLY_REPAIR_REPLAY_READINESS"],
        redactions: ["internal_tenant_identifier"],
        no_repair_replay_retry_confirmed: true,
        no_provider_dispatch_confirmed: true,
        no_credential_or_auth_claim_change_confirmed: true,
        no_campaign_activation_confirmed: true,
        no_billing_or_money_movement_confirmed: true,
      },
      guardrail: "Read-only support-case repair/replay readiness.",
      guardrails: ["READ_ONLY_REPAIR_REPLAY_READINESS"],
      redactions: ["internal_tenant_identifier"],
      no_repair_replay_retry_confirmed: true,
      no_provider_dispatch_confirmed: true,
      no_credential_or_auth_claim_change_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_tenant_code_exposure_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      getReferralSaasAccountSupportCaseRepairReplayReadiness({
        accountRef: " acct-1 ",
        caseRef: " case-1 ",
        refType: "external_tenant_ref",
        externalRef: " fnb-referrals ",
        context: "support",
      }),
    ).resolves.toMatchObject({
      repairReplayReadiness: {
        overallStatus: "REVIEW_REQUIRED",
        owningWorkflow: "progress_status",
      },
      no_repair_replay_retry_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/accounts/acct-1/support-cases/case-1/repair-replay-readiness",
      {
        query: {
          ref_type: "external_tenant_ref",
          external_ref: "fnb-referrals",
          context: "support",
        },
      },
    );
    expect(JSON.stringify(mockedApiRequest.mock.calls)).not.toMatch(
      /provider_dispatch|credential_creation|auth_claim|campaign_activation|billing|money/i,
    );
  });

  it("lists the operator aggregate support queue through the read-only wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      operatorScope: {
        surface: "operator_support_queue",
        role: "REFERRAL_SAAS_READER",
      },
      supportQueue: {
        supportCases: [
          {
            caseRef: "CASE-001",
            accountRef: "acct-1",
            customerLabel: "Acme Retail",
            externalTenantRef: "acme-tenant",
            organisationRef: "acme-org",
            category: "ACCESS_SCOPE",
            priority: "HIGH",
            status: "OPEN",
            title: "Owner responsibility missing",
            sourceSurface: "people_access",
            assigneeRef: null,
            createdAt: "2026-08-01T08:00:00Z",
            updatedAt: "2026-08-01T09:00:00Z",
            evidenceLinkCount: 2,
            noteCount: 1,
            latestActivity: "Status OPEN",
            redactions: ["internal_tenant_identifier"],
            nextAction: "Open customer support case",
          },
        ],
        filters: {},
        nextCursor: null,
        guardrails: ["READ_ONLY_QUEUE"],
        redactions: ["internal_tenant_identifier"],
      },
      guardrail: "Operator support queue is a read-only aggregate.",
      guardrails: ["READ_ONLY_QUEUE"],
      redactions: ["internal_tenant_identifier"],
      no_assignment_from_queue_confirmed: true,
      no_case_lifecycle_mutation_confirmed: true,
      no_repair_replay_retry_confirmed: true,
      no_referral_or_campaign_mutation_confirmed: true,
      no_progress_or_attribution_mutation_confirmed: true,
      no_report_or_export_mutation_confirmed: true,
      no_invite_delivery_confirmed: true,
      no_credential_or_auth_claim_change_confirmed: true,
      no_tenant_code_exposure_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      listReferralSaasOperatorSupportQueue({
        status: " OPEN ",
        priority: " HIGH ",
        category: " ACCESS_SCOPE ",
        accountRef: " acct-1 ",
        sourceSurface: " people_access ",
        assigneeRef: " operator-1 ",
        limit: 25,
        cursor: " cursor-1 ",
      }),
    ).resolves.toMatchObject({
      supportQueue: {
        supportCases: [{ caseRef: "CASE-001", accountRef: "acct-1" }],
      },
      no_assignment_from_queue_confirmed: true,
      no_case_lifecycle_mutation_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/operator/support-cases", {
      query: {
        status: "OPEN",
        priority: "HIGH",
        category: "ACCESS_SCOPE",
        account_ref: "acct-1",
        source_surface: "people_access",
        assignee_ref: "operator-1",
        limit: 25,
        cursor: "cursor-1",
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|raw_ucn|client_secret|password|credential|repair|replay|retry|wallet|settlement|money_movement/,
    );
  });

  it("creates selected-customer support cases without repair or adjacent side effects", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: { accountId: "acct-1", accountCode: "ACCT_FNB" },
      supportCase: {
        commandStatus: "RECORDED",
        supportCase: {
          caseRef: "case-1",
          accountRef: "acct-1",
          category: "VALIDATION_RECOVERY",
          priority: "HIGH",
          status: "OPEN",
          title: "Referral code validation failed",
          summary: "Safe customer-facing issue summary.",
          createdByRef: "operator",
          evidenceLinks: [],
          redactions: ["internal_tenant_identifier"],
        },
        idempotency: { status: "NEW_REQUEST" },
        audit: { accountAuditEventId: "audit-1" },
        guardrails: ["NO_REPAIR_REPLAY_RETRY"],
        redactions: ["internal_tenant_identifier"],
      },
      guardrail: "Selected-customer support case recorded.",
      guardrails: ["NO_REPAIR_REPLAY_RETRY"],
      redactions: ["internal_tenant_identifier"],
      no_repair_replay_retry_confirmed: true,
      no_referral_or_campaign_mutation_confirmed: true,
      no_progress_or_attribution_mutation_confirmed: true,
      no_report_or_export_mutation_confirmed: true,
      no_invite_delivery_confirmed: true,
      no_credential_or_auth_claim_change_confirmed: true,
      no_tenant_code_exposure_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      createReferralSaasAccountSupportCase({
        accountRef: " acct-1 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
          context: "setup",
        },
        category: " VALIDATION_RECOVERY ",
        priority: " HIGH ",
        title: " Referral code validation failed ",
        summary: " Safe customer-facing issue summary. ",
        sourceSurface: " support_hub ",
        evidenceLinks: [
          {
            evidenceType: " LINK_CODE_INSPECTION ",
            evidenceRef: " link-check-1 ",
            safeStatus: " CUSTOMER_SCOPED ",
            redactions: ["internal_tenant_identifier"],
          },
        ],
        correlationId: "support-case-acct-1",
        idempotencyKey: "support-case-acct-1-v1",
      }),
    ).resolves.toMatchObject({
      supportCase: {
        supportCase: {
          caseRef: "case-1",
        },
      },
      no_repair_replay_retry_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/accounts/acct-1/support-cases", {
      method: "POST",
      body: {
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: "fnb-referrals",
          context: "setup",
        },
        category: "VALIDATION_RECOVERY",
        priority: "HIGH",
        title: "Referral code validation failed",
        summary: "Safe customer-facing issue summary.",
        sourceSurface: "support_hub",
        evidenceLinks: [
          {
            evidenceType: "LINK_CODE_INSPECTION",
            evidenceRef: "link-check-1",
            safeStatus: "CUSTOMER_SCOPED",
            warningCode: undefined,
            missingEvidenceCode: undefined,
            redactions: ["internal_tenant_identifier"],
          },
        ],
        reasonCode: "CUSTOMER_SUPPORT_CASE_CREATED",
        correlationId: "support-case-acct-1",
        idempotencyKey: "support-case-acct-1-v1",
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|raw_ucn|client_secret|password|credential|repair|replay|retry|wallet|settlement|money_movement/,
    );
  });

  it("adds selected-customer support case notes without repair or adjacent side effects", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "support",
      account: { accountId: "acct-1", accountCode: "ACCT_FNB" },
      supportCaseLifecycle: {
        commandStatus: "RECORDED",
        supportCase: {
          caseRef: "case-1",
          accountRef: "acct-1",
          category: "VALIDATION_RECOVERY",
          priority: "HIGH",
          status: "OPEN",
          title: "Referral code validation failed",
          summary: "Safe customer-facing issue summary.",
          createdByRef: "operator",
          evidenceLinks: [],
          redactions: ["internal_tenant_identifier"],
        },
        note: {
          noteRef: "note-1",
          supportCaseRef: "case-1",
          noteType: "OPERATOR_NOTE",
          noteText: "Called the customer and confirmed the branch test scope.",
          createdByRef: "operator",
          redactions: ["internal_tenant_identifier"],
        },
        idempotency: { status: "NEW_REQUEST" },
        audit: { accountAuditEventId: "audit-note-1" },
        guardrails: ["NO_REPAIR_REPLAY_RETRY"],
        redactions: ["internal_tenant_identifier"],
      },
      guardrail: "Selected-customer support case note recorded.",
      guardrails: ["NO_REPAIR_REPLAY_RETRY"],
      redactions: ["internal_tenant_identifier"],
      no_repair_replay_retry_confirmed: true,
      no_referral_or_campaign_mutation_confirmed: true,
      no_progress_or_attribution_mutation_confirmed: true,
      no_report_or_export_mutation_confirmed: true,
      no_invite_delivery_confirmed: true,
      no_credential_or_auth_claim_change_confirmed: true,
      no_tenant_code_exposure_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      addReferralSaasAccountSupportCaseNote({
        accountRef: " acct-1 ",
        caseRef: " case-1 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
        },
        noteType: " OPERATOR_NOTE ",
        noteText: " Called the customer and confirmed the branch test scope. ",
        correlationId: "support-note-case-1",
        idempotencyKey: "support-note-case-1-v1",
      }),
    ).resolves.toMatchObject({
      supportCaseLifecycle: {
        note: {
          noteRef: "note-1",
        },
      },
      no_repair_replay_retry_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/accounts/acct-1/support-cases/case-1/notes", {
      method: "POST",
      body: {
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: "fnb-referrals",
          context: "support",
        },
        noteType: "OPERATOR_NOTE",
        noteText: "Called the customer and confirmed the branch test scope.",
        reasonCode: "CUSTOMER_SUPPORT_NOTE_ADDED",
        correlationId: "support-note-case-1",
        idempotencyKey: "support-note-case-1-v1",
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|raw_ucn|client_secret|password|credential|repair|replay|retry|wallet|settlement|money_movement/,
    );
  });

  it("changes selected-customer support case status without repair or adjacent side effects", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "support",
      account: { accountId: "acct-1", accountCode: "ACCT_FNB" },
      supportCaseLifecycle: {
        commandStatus: "RECORDED",
        supportCase: {
          caseRef: "case-1",
          accountRef: "acct-1",
          category: "VALIDATION_RECOVERY",
          priority: "HIGH",
          status: "INVESTIGATING",
          title: "Referral code validation failed",
          summary: "Safe customer-facing issue summary.",
          createdByRef: "operator",
          evidenceLinks: [],
          redactions: ["internal_tenant_identifier"],
        },
        statusEvent: {
          statusEventRef: "status-1",
          supportCaseRef: "case-1",
          fromStatus: "OPEN",
          toStatus: "INVESTIGATING",
          transitionReason: "Evidence reviewed and assigned to support.",
          transitionedByRef: "operator",
          redactions: ["internal_tenant_identifier"],
        },
        idempotency: { status: "NEW_REQUEST" },
        audit: { accountAuditEventId: "audit-status-1" },
        guardrails: ["NO_REPAIR_REPLAY_RETRY"],
        redactions: ["internal_tenant_identifier"],
      },
      guardrail: "Selected-customer support case status changed.",
      guardrails: ["NO_REPAIR_REPLAY_RETRY"],
      redactions: ["internal_tenant_identifier"],
      no_repair_replay_retry_confirmed: true,
      no_referral_or_campaign_mutation_confirmed: true,
      no_progress_or_attribution_mutation_confirmed: true,
      no_report_or_export_mutation_confirmed: true,
      no_invite_delivery_confirmed: true,
      no_credential_or_auth_claim_change_confirmed: true,
      no_tenant_code_exposure_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    await expect(
      changeReferralSaasAccountSupportCaseStatus({
        accountRef: " acct-1 ",
        caseRef: " case-1 ",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: " fnb-referrals ",
        },
        status: " INVESTIGATING ",
        transitionReason: " Evidence reviewed and assigned to support. ",
        correlationId: "support-status-case-1",
        idempotencyKey: "support-status-case-1-v1",
      }),
    ).resolves.toMatchObject({
      supportCaseLifecycle: {
        supportCase: {
          status: "INVESTIGATING",
        },
      },
      no_repair_replay_retry_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/accounts/acct-1/support-cases/case-1/status", {
      method: "POST",
      body: {
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: "fnb-referrals",
          context: "support",
        },
        status: "INVESTIGATING",
        transitionReason: "Evidence reviewed and assigned to support.",
        reasonCode: "CUSTOMER_SUPPORT_STATUS_CHANGED",
        correlationId: "support-status-case-1",
        idempotencyKey: "support-status-case-1-v1",
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|raw_ucn|client_secret|password|credential|repair|replay|retry|wallet|settlement|money_movement/,
    );
  });
});
