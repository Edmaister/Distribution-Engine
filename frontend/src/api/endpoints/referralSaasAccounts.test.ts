import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest } from "../client";
import {
  createReferralSaasAccountFromDraft,
  getReferralSaasAccountMembershipPosture,
  listReferralSaasAccounts,
  recordReferralSaasMembershipInvitationIntent,
  resolveReferralSaasAccount,
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
});
