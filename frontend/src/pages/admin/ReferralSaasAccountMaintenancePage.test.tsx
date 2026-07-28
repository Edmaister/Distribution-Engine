import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  getAdminOnboardingDrafts,
  getAdminOnboardingState,
  type AdminOnboardingDraftSelectorResponse,
  type AdminOnboardingStateResponse,
} from "../../api/endpoints/adminOnboarding";
import {
  issueReferralSaasAccountCampaignCode,
  validateReferralSaasAccountCampaignCode,
} from "../../api/endpoints/referralSaasLinks";
import {
  getReferralSaasAccountReport,
  previewReferralSaasAccountReportExport,
} from "../../api/endpoints/referralSaasReports";
import {
  createReferralSaasAccountCampaignSetup,
  getReferralSaasAccountCampaignReadiness,
  getReferralSaasAccountMembershipPosture,
  getReferralSaasIntegrationConfiguration,
  getReferralSaasIntegrationExecutionReadiness,
  getReferralSaasMembershipActivationReadiness,
  getReferralSaasTechnicalSetupReadiness,
  listReferralSaasAccountCampaigns,
  listReferralSaasAccounts,
  recordReferralSaasAccountCampaignReviewDecision,
  recordReferralSaasMembershipInvitationIntent,
  requestReferralSaasAccountCampaignActivation,
  requestReferralSaasAccountFoundationActivation,
  requestReferralSaasAccessProvisioning,
  requestReferralSaasMembershipActivation,
  requestReferralSaasMembershipInvitationDelivery,
  saveReferralSaasIntegrationConfiguration,
  submitReferralSaasAccountCampaignReview,
  cancelReferralSaasMembershipInvitationIntent,
  updateReferralSaasMembershipInvitationIntent,
  updateReferralSaasAccountCampaignPolicySettings,
  updateReferralSaasAccountProfile,
  validateReferralSaasIntegrationConfiguration,
  type ReferralSaasAccountCampaignReviewResponse,
  type ReferralSaasAccountCampaignActivationResponse,
  type ReferralSaasAccountCampaignPolicySettingsResponse,
  type ReferralSaasAccountMembershipPostureResponse,
  type ReferralSaasAccountCampaignListResponse,
  type ReferralSaasAccountRegistryResponse,
  type ReferralSaasAccountCampaignReadinessResponse,
  type ReferralSaasMembershipActivationReadinessResponse,
  type ReferralSaasIntegrationExecutionReadinessResponse,
  type ReferralSaasTechnicalSetupReadinessResponse,
} from "../../api/endpoints/referralSaasAccounts";
import { ReferralSaasAccountMaintenancePage } from "./ReferralSaasAccountMaintenancePage";

vi.mock("../../api/endpoints/adminOnboarding", () => ({
  getAdminOnboardingDrafts: vi.fn(),
  getAdminOnboardingState: vi.fn(),
}));
vi.mock("../../api/endpoints/referralSaasLinks", () => ({
  issueReferralSaasAccountCampaignCode: vi.fn(),
  validateReferralSaasAccountCampaignCode: vi.fn(),
}));
vi.mock("../../api/endpoints/referralSaasReports", () => ({
  getReferralSaasAccountReport: vi.fn(),
  previewReferralSaasAccountReportExport: vi.fn(),
}));
vi.mock("../../api/endpoints/referralSaasAccounts", () => ({
  createReferralSaasAccountCampaignSetup: vi.fn(),
  getReferralSaasAccountCampaignReadiness: vi.fn(),
  getReferralSaasAccountMembershipPosture: vi.fn(),
  getReferralSaasIntegrationConfiguration: vi.fn(),
  getReferralSaasIntegrationExecutionReadiness: vi.fn(),
  getReferralSaasMembershipActivationReadiness: vi.fn(),
  getReferralSaasTechnicalSetupReadiness: vi.fn(),
  listReferralSaasAccountCampaigns: vi.fn(),
  listReferralSaasAccounts: vi.fn(),
  recordReferralSaasAccountCampaignReviewDecision: vi.fn(),
  recordReferralSaasMembershipInvitationIntent: vi.fn(),
  requestReferralSaasAccountCampaignActivation: vi.fn(),
  requestReferralSaasAccountFoundationActivation: vi.fn(),
  requestReferralSaasAccessProvisioning: vi.fn(),
  requestReferralSaasMembershipInvitationDelivery: vi.fn(),
  requestReferralSaasMembershipActivation: vi.fn(),
  saveReferralSaasIntegrationConfiguration: vi.fn(),
  submitReferralSaasAccountCampaignReview: vi.fn(),
  cancelReferralSaasMembershipInvitationIntent: vi.fn(),
  updateReferralSaasMembershipInvitationIntent: vi.fn(),
  updateReferralSaasAccountCampaignPolicySettings: vi.fn(),
  updateReferralSaasAccountProfile: vi.fn(),
  validateReferralSaasIntegrationConfiguration: vi.fn(),
}));

const mockedGetAdminOnboardingDrafts = vi.mocked(getAdminOnboardingDrafts);
const mockedGetAdminOnboardingState = vi.mocked(getAdminOnboardingState);
const mockedIssueReferralSaasAccountCampaignCode = vi.mocked(issueReferralSaasAccountCampaignCode);
const mockedValidateReferralSaasAccountCampaignCode = vi.mocked(validateReferralSaasAccountCampaignCode);
const mockedGetReferralSaasAccountReport = vi.mocked(getReferralSaasAccountReport);
const mockedPreviewReferralSaasAccountReportExport = vi.mocked(previewReferralSaasAccountReportExport);
const mockedCreateReferralSaasAccountCampaignSetup = vi.mocked(createReferralSaasAccountCampaignSetup);
const mockedGetReferralSaasAccountCampaignReadiness = vi.mocked(getReferralSaasAccountCampaignReadiness);
const mockedGetReferralSaasAccountMembershipPosture = vi.mocked(getReferralSaasAccountMembershipPosture);
const mockedGetReferralSaasIntegrationConfiguration = vi.mocked(getReferralSaasIntegrationConfiguration);
const mockedGetReferralSaasIntegrationExecutionReadiness = vi.mocked(getReferralSaasIntegrationExecutionReadiness);
const mockedGetReferralSaasMembershipActivationReadiness = vi.mocked(getReferralSaasMembershipActivationReadiness);
const mockedGetReferralSaasTechnicalSetupReadiness = vi.mocked(getReferralSaasTechnicalSetupReadiness);
const mockedListReferralSaasAccountCampaigns = vi.mocked(listReferralSaasAccountCampaigns);
const mockedListReferralSaasAccounts = vi.mocked(listReferralSaasAccounts);
const mockedRecordReferralSaasAccountCampaignReviewDecision = vi.mocked(recordReferralSaasAccountCampaignReviewDecision);
const mockedRecordReferralSaasMembershipInvitationIntent = vi.mocked(recordReferralSaasMembershipInvitationIntent);
const mockedRequestReferralSaasAccountCampaignActivation = vi.mocked(requestReferralSaasAccountCampaignActivation);
const mockedRequestReferralSaasAccountFoundationActivation = vi.mocked(requestReferralSaasAccountFoundationActivation);
const mockedRequestReferralSaasAccessProvisioning = vi.mocked(requestReferralSaasAccessProvisioning);
const mockedRequestReferralSaasMembershipInvitationDelivery = vi.mocked(requestReferralSaasMembershipInvitationDelivery);
const mockedRequestReferralSaasMembershipActivation = vi.mocked(requestReferralSaasMembershipActivation);
const mockedSaveReferralSaasIntegrationConfiguration = vi.mocked(saveReferralSaasIntegrationConfiguration);
const mockedSubmitReferralSaasAccountCampaignReview = vi.mocked(submitReferralSaasAccountCampaignReview);
const mockedCancelReferralSaasMembershipInvitationIntent = vi.mocked(cancelReferralSaasMembershipInvitationIntent);
const mockedUpdateReferralSaasMembershipInvitationIntent = vi.mocked(updateReferralSaasMembershipInvitationIntent);
const mockedUpdateReferralSaasAccountCampaignPolicySettings = vi.mocked(updateReferralSaasAccountCampaignPolicySettings);
const mockedUpdateReferralSaasAccountProfile = vi.mocked(updateReferralSaasAccountProfile);
const mockedValidateReferralSaasIntegrationConfiguration = vi.mocked(validateReferralSaasIntegrationConfiguration);

function renderWorkspace(ui: ReactElement, initialEntry = "/admin/referral-saas/account-maintenance") {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: <Outlet context={{ refreshKey: 0 }} />,
        children: [
          { index: true, element: <div>Index</div> },
          { path: "admin/referral-saas/account-setup", element: <div>Account Setup Target</div> },
          { path: "admin/referral-saas/account-maintenance", element: ui },
          { path: "admin/referral-saas/account-maintenance/:accountId", element: ui },
          { path: "admin/referral-saas/account-maintenance/:accountId/:customerModule", element: ui },
          { path: "admin/referral-saas/account-maintenance/:accountId/:customerModule/:customerSubModule", element: ui },
          { path: "admin/referral-saas/campaigns", element: <div>Campaign Target</div> },
          { path: "admin/referral-saas/link-codes", element: <div>Links Target</div> },
          { path: "admin/referral-saas/attribution-trace", element: <div>Trace Target</div> },
          { path: "admin/referral-saas/progress-status", element: <div>Progress Target</div> },
          { path: "admin/referral-saas/reports", element: <div>Reports Target</div> },
          { path: "admin/referral-saas/support", element: <div>Support Target</div> },
        ],
      },
    ],
    { initialEntries: [initialEntry] },
  );

  return render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

function mockMaintenanceState(): AdminOnboardingStateResponse {
  return {
    status: "ok",
    guardrail: "Read-only onboarding state projection.",
    onboarding_state: {
      contract_version: "onboarding.v1",
      scope: {
        external_tenant_ref: "demo-platform-operator",
        organisation_ref: "demo-organisation",
        resolved_tenant: { status: "AVAILABLE" },
      },
      sections: {},
      readiness: {},
      missing_evidence: [],
      guardrails: ["NO_ACCOUNT_CREATION", "NO_LIVE_ACTIONS", "NO_VALUE_TRANSFER"],
      redactions: ["INTERNAL_IDENTIFIER", "SECRETS_REDACTED"],
      source_warnings: [],
    },
    readiness: {
      contract_version: "onboarding.v1",
      overall_status: "GO_LIVE_DISABLED",
      categories: [
        {
          category: "ACCOUNT_PROFILE",
          display_label: "Account profile",
          status: "READY",
          safe_display_status: {
            status: "READY",
            label: "Ready",
            action_required: false,
            go_live_enabled: false,
          },
          evidence_summary: "Organisation profile and primary contact are captured.",
          blockers: [],
          next_actions: ["Review tenant link before campaign setup."],
        },
        {
          category: "MEMBERSHIP",
          display_label: "Membership and roles",
          status: "MISSING_EVIDENCE",
          safe_display_status: {
            status: "NEEDS_ATTENTION",
            label: "Needs evidence",
            action_required: true,
            go_live_enabled: false,
          },
          evidence_summary: "Owner and campaign manager role-family intent is incomplete.",
          blockers: ["Invite evidence is not complete."],
          next_actions: ["Draft owner and campaign manager access."],
        },
        {
          category: "CAMPAIGN_READINESS",
          display_label: "Campaign readiness",
          status: "READY",
          safe_display_status: {
            status: "READY",
            label: "Ready",
            action_required: false,
            go_live_enabled: false,
          },
          evidence_summary: "Campaign setup is ready for a test campaign.",
          blockers: [],
          next_actions: ["Open campaign readiness."],
        },
      ],
      summary: {
        ready_count: 2,
        in_progress_count: 0,
        blocked_count: 1,
        missing_evidence_count: 2,
        permission_limited_count: 0,
        go_live_disabled_count: 1,
        total_count: 3,
      },
      guardrails: ["NO_ACCOUNT_CREATION"],
      missing_evidence: [],
      source_warnings: [],
      redactions: ["INTERNAL_IDENTIFIER"],
    },
  };
}

function mockDraftSelector(): AdminOnboardingDraftSelectorResponse {
  return {
    status: "ok",
    count: 1,
    items: [
      {
        draft_ref: "draft_referral_saas_setup",
        draft_version: 2,
        draft_status: "READY_FOR_REVIEW",
        external_tenant_ref: "demo-platform-operator",
        organisation_ref: "demo-organisation",
        readiness_status: "GO_LIVE_DISABLED",
        validation_status: "VALID",
        missing_evidence_count: 1,
        blocker_count: 0,
        redactions: ["internal_identifier"],
      },
    ],
    guardrails: ["READ_ONLY_DRAFT_SELECTOR", "NO_ACCOUNT_CREATION"],
    redactions: ["internal_identifier"],
  };
}

function mockAccountRegistry(): ReferralSaasAccountRegistryResponse {
  return {
    status: "ok",
    count: 3,
    accounts: [
      {
        accountId: "acct-fnb",
        accountCode: "ACCT_FNB",
        accountName: "FNB Referral SaaS",
        accountType: "ORGANISATION",
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
          {
            refType: "organisation_ref",
            externalRef: "fnb-org",
            referenceStatus: "ACTIVE",
          },
        ],
        createdAt: "2026-07-19T00:00:00",
        updatedAt: "2026-07-19T01:00:00",
      },
      {
        accountId: "acct-gabs",
        accountCode: "ACC-2201",
        accountName: "Gaborone Partners",
        accountType: "ORGANISATION",
        accountStatus: "ACTIVE",
        onboardingStatus: "APPROVED",
        operatingJurisdictionCode: "BW",
        primaryExternalTenantRef: "gabs-platform",
        externalReferences: [
          {
            refType: "external_tenant_ref",
            externalRef: "gabs-platform",
            referenceStatus: "ACTIVE",
          },
          {
            refType: "organisation_ref",
            externalRef: "gabs-org",
            referenceStatus: "ACTIVE",
          },
        ],
        createdAt: "2026-07-19T00:00:00",
        updatedAt: "2026-07-19T01:00:00",
      },
      {
        accountId: "acct-cape",
        accountCode: "ACC-1770",
        accountName: "Cape Commerce Hub",
        accountType: "ORGANISATION",
        accountStatus: "ACTIVE",
        onboardingStatus: "APPROVED",
        operatingJurisdictionCode: "ZA",
        primaryExternalTenantRef: "cape-commerce",
        externalReferences: [
          {
            refType: "external_tenant_ref",
            externalRef: "cape-commerce",
            referenceStatus: "ACTIVE",
          },
          {
            refType: "organisation_ref",
            externalRef: "cape-hub",
            referenceStatus: "ACTIVE",
          },
        ],
        createdAt: "2026-07-19T00:00:00",
        updatedAt: "2026-07-19T01:00:00",
      },
    ],
    guardrail: "Read-only Referral SaaS account registry.",
    redactions: ["internal_tenant_identifier"],
  };
}

function mockMembershipPosture(): ReferralSaasAccountMembershipPostureResponse {
  return {
    status: "ok",
    context: "setup",
    account: {
      accountId: "acct-gabs",
      accountCode: "ACC-2201",
      accountName: "Gaborone Partners",
      accountStatus: "ACTIVE",
      onboardingStatus: "APPROVED",
    },
    membershipPosture: {
      accountId: "acct-gabs",
      totalMemberships: 1,
      invitedCount: 1,
      activeCount: 0,
      suspendedCount: 0,
      disabledCount: 0,
      archivedCount: 0,
      roleFamilies: [
        {
          roleFamily: "DISTRIBUTION_ADMIN",
          invitedCount: 1,
          activeCount: 0,
          suspendedCount: 0,
          disabledCount: 0,
          archivedCount: 0,
        },
      ],
      memberships: [
        {
          membershipRef: "membership-1",
          actorType: "USER",
          subject: "owner@gabs.example",
          displayName: "Gaborone owner",
          roleFamily: "DISTRIBUTION_ADMIN",
          permissionSet: "REFERRAL_SAAS_ACCOUNT_ADMIN",
          status: "INVITED",
          deliveryStatus: "DELIVERY_NOT_CONFIGURED",
          recipientContactStatus: "CONTACT_REFERENCE_PRESENT",
        },
      ],
      currentActor: {
        status: "NO_MEMBERSHIP_EVIDENCE",
        roleFamily: null,
        permissionSet: null,
        canOperateSetup: false,
        evidence: "No active account membership matched the current actor.",
      },
      guardrails: ["NO_INVITE_DELIVERY", "NO_AUTH_CLAIM_CHANGE"],
      redactions: ["INTERNAL_TENANT_IDENTIFIER"],
      noMembershipWriteConfirmed: false,
      noInviteDeliveryConfirmed: true,
    },
    guardrail: "Read-only Referral SaaS account membership posture.",
    no_membership_write_confirmed: false,
    no_invite_delivery_confirmed: true,
  };
}

function mockDisabledMembershipPosture(): ReferralSaasAccountMembershipPostureResponse {
  const base = mockMembershipPosture();
  return {
    ...base,
    membershipPosture: {
      ...base.membershipPosture,
      totalMemberships: 1,
      invitedCount: 0,
      activeCount: 0,
      disabledCount: 1,
      roleFamilies: [
        {
          roleFamily: "DISTRIBUTION_ADMIN",
          invitedCount: 0,
          activeCount: 0,
          suspendedCount: 0,
          disabledCount: 1,
          archivedCount: 0,
        },
      ],
      memberships: [
        {
          ...base.membershipPosture.memberships[0],
          status: "DISABLED",
        },
      ],
    },
  };
}

function mockMembershipActivationReadiness(): ReferralSaasMembershipActivationReadinessResponse {
  return {
    status: "ok",
    context: "setup",
    account: {
      accountId: "acct-gabs",
      accountCode: "ACC-2201",
      accountName: "Gaborone Partners",
      accountStatus: "ACTIVE",
      onboardingStatus: "APPROVED",
    },
    activationReadiness: {
      accountId: "acct-gabs",
      overallStatus: "ACTION_REQUIRED",
      activeCount: 0,
      invitedCount: 1,
      deliveryReadyCount: 0,
      activationReadyCount: 0,
      missingRoleFamilies: ["CAMPAIGN_MANAGER"],
      items: [
        {
          membershipRef: "membership-1",
          subject: "owner@gabs.example",
          displayName: "Gaborone owner",
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
      guardrails: ["READ_ONLY_ACTIVATION_READINESS", "NO_INVITE_DELIVERY"],
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
  };
}

function mockMembershipActivationReadinessMissingAll(): ReferralSaasMembershipActivationReadinessResponse {
  const base = mockMembershipActivationReadiness();
  return {
    ...base,
    activationReadiness: {
      ...base.activationReadiness,
      invitedCount: 0,
      missingRoleFamilies: ["DISTRIBUTION_ADMIN", "CAMPAIGN_MANAGER"],
      items: [
        {
          ...base.activationReadiness.items[0],
          membershipStatus: "DISABLED",
          deliveryReadiness: "BLOCKED",
          activationReadiness: "BLOCKED",
          blockers: ["MEMBERSHIP_DISABLED"],
          nextAction: "Record a new access intent if this responsibility is still required.",
        },
      ],
    },
  };
}

function mockActiveMembershipPosture(): ReferralSaasAccountMembershipPostureResponse {
  const base = mockMembershipPosture();
  return {
    ...base,
    membershipPosture: {
      ...base.membershipPosture,
      invitedCount: 0,
      activeCount: 1,
      roleFamilies: [
        {
          ...base.membershipPosture.roleFamilies[0],
          invitedCount: 0,
          activeCount: 1,
        },
      ],
      memberships: [
        {
          ...base.membershipPosture.memberships[0],
          status: "ACTIVE",
        },
      ],
    },
  };
}

function mockActiveMembershipActivationReadiness(): ReferralSaasMembershipActivationReadinessResponse {
  const base = mockMembershipActivationReadiness();
  return {
    ...base,
    activationReadiness: {
      ...base.activationReadiness,
      activeCount: 1,
      invitedCount: 0,
      activationReadyCount: 0,
      items: [
        {
          ...base.activationReadiness.items[0],
          membershipStatus: "ACTIVE",
          deliveryReadiness: "DELIVERY_NOT_REQUIRED",
          activationReadiness: "ACTIVE",
          provisioningReadiness: "READY_TO_PROVISION_SEAT",
          blockers: [],
          nextAction:
            "Membership is active. Provision a seat before login access is live; auth claims remain a separate governed workflow.",
        },
      ],
    },
  };
}

function mockSeatProvisionedMembershipActivationReadiness(): ReferralSaasMembershipActivationReadinessResponse {
  const base = mockActiveMembershipActivationReadiness();
  return {
    ...base,
    activationReadiness: {
      ...base.activationReadiness,
      items: [
        {
          ...base.activationReadiness.items[0],
          provisioningReadiness: "SEAT_ASSIGNED",
          seatAssignmentStatus: "SEAT_ASSIGNED",
          nextAction:
            "Seat is assigned. Configure auth claims through the separate governed workflow before login access is live.",
        },
      ],
    },
  };
}

function mockAcceptedRequiredMembershipPosture(): ReferralSaasAccountMembershipPostureResponse {
  const base = mockMembershipPostureAfterCampaignManagerSave();
  return {
    ...base,
    membershipPosture: {
      ...base.membershipPosture,
      invitedCount: 0,
      activeCount: 2,
      roleFamilies: base.membershipPosture.roleFamilies.map((role) => ({
        ...role,
        invitedCount: 0,
        activeCount: 1,
      })),
      memberships: base.membershipPosture.memberships.map((membership) => ({
        ...membership,
        status: "ACTIVE",
      })),
    },
  };
}

function mockAcceptedRequiredMembershipActivationReadiness(): ReferralSaasMembershipActivationReadinessResponse {
  const base = mockMembershipActivationReadinessAfterCampaignManagerSave();
  return {
    ...base,
    activationReadiness: {
      ...base.activationReadiness,
      overallStatus: "ACCESS_READY",
      activeCount: 2,
      invitedCount: 0,
      missingRoleFamilies: [],
      items: base.activationReadiness.items.map((item) => ({
        ...item,
        membershipStatus: "ACTIVE",
        deliveryReadiness: "DELIVERY_NOT_REQUIRED",
        activationReadiness: "ACTIVE",
        provisioningReadiness: "READY_TO_PROVISION_SEAT",
        blockers: [],
        nextAction:
          "Membership is active. Provision a seat before login access is live; auth claims remain a separate governed workflow.",
      })),
    },
  };
}

function mockMembershipPostureAfterCampaignManagerSave(): ReferralSaasAccountMembershipPostureResponse {
  const base = mockMembershipPosture();
  return {
    ...base,
    membershipPosture: {
      ...base.membershipPosture,
      totalMemberships: 2,
      invitedCount: 2,
      roleFamilies: [
        ...base.membershipPosture.roleFamilies,
        {
          roleFamily: "CAMPAIGN_MANAGER",
          invitedCount: 1,
          activeCount: 0,
          suspendedCount: 0,
          disabledCount: 0,
          archivedCount: 0,
        },
      ],
      memberships: [
        ...base.membershipPosture.memberships,
        {
          membershipRef: "membership-campaign-manager",
          actorType: "USER",
          subject: "gabs.campaign.owner@example.com",
          displayName: "Gaborone campaign owner",
          roleFamily: "CAMPAIGN_MANAGER",
          permissionSet: "REFERRAL_SAAS_CAMPAIGN_MANAGER",
          status: "INVITED",
          deliveryStatus: "DELIVERY_NOT_CONFIGURED",
          recipientContactStatus: "CONTACT_REFERENCE_PRESENT",
        },
      ],
    },
  };
}

function mockMembershipActivationReadinessAfterCampaignManagerSave(): ReferralSaasMembershipActivationReadinessResponse {
  const base = mockMembershipActivationReadiness();
  return {
    ...base,
    activationReadiness: {
      ...base.activationReadiness,
      invitedCount: 2,
      missingRoleFamilies: [],
      items: [
        ...base.activationReadiness.items,
        {
          membershipRef: "membership-campaign-manager",
          subject: "gabs.campaign.owner@example.com",
          displayName: "Gaborone campaign owner",
          roleFamily: "CAMPAIGN_MANAGER",
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
    },
  };
}

function mockTechnicalSetupReadiness(): ReferralSaasTechnicalSetupReadinessResponse {
  return {
    status: "ok",
    context: "setup",
    account: {
      accountId: "acct-gabs",
      accountCode: "ACC-2201",
      accountName: "Gaborone Partners",
      accountStatus: "ACTIVE",
      onboardingStatus: "APPROVED",
    },
    technicalSetupReadiness: {
      accountId: "acct-gabs",
      overallStatus: "PROVIDER_CONFIGURATION_REQUIRED",
      providerStatus: "ATTENTION",
      channelSummary: {
        count: 4,
        readyCount: 1,
        attentionCount: 3,
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
        {
          code: "REFERRAL_JOURNEY_MESSAGES",
          label: "Referral journey messages",
          status: "READY",
          requiredChannels: ["WHATSAPP", "SMS", "USSD"],
          readyChannels: ["WHATSAPP"],
          missingChannels: [],
          approvedProviderRefs: [],
          missingApprovalChannels: [],
          nextAction: "Referral journey message providers are ready for checked channels.",
        },
      ],
      guardrails: ["READ_ONLY_TECHNICAL_SETUP_READINESS", "NO_INVITE_DELIVERY"],
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
  };
}

function mockTechnicalSetupReadinessWithInviteProvider(): ReferralSaasTechnicalSetupReadinessResponse {
  const readiness = mockTechnicalSetupReadiness();
  return {
    ...readiness,
    technicalSetupReadiness: {
      ...readiness.technicalSetupReadiness,
      overallStatus: "READY",
      channelSummary: {
        ...readiness.technicalSetupReadiness.channelSummary,
        approvedInviteProviderCount: 1,
      },
      capabilities: readiness.technicalSetupReadiness.capabilities.map((capability) =>
        capability.code === "MEMBERSHIP_INVITE_DELIVERY"
          ? {
              ...capability,
              status: "READY",
              readyChannels: ["EMAIL"],
              missingChannels: [],
              approvedProviderRefs: ["mail-provider-1"],
              nextAction: "People invite delivery provider is ready for a guarded request check.",
            }
          : capability,
      ),
    },
  };
}

function mockIntegrationConfigurationRead() {
  const readiness = mockTechnicalSetupReadiness();
  return {
    status: "ok",
    context: "setup" as const,
    account: readiness.account,
    integrationConfiguration: null,
    technicalSetupReadiness: readiness.technicalSetupReadiness,
    guardrail: "Selected-customer Integrations configuration view.",
    guardrails: ["CUSTOMER_SCOPED_INTEGRATIONS_CONFIGURATION", "NO_SECRET_OR_CREDENTIAL_STORAGE"],
    redactions: ["internal_tenant_identifier", "tenant_code", "provider_secret"],
    no_secret_or_credential_storage_confirmed: true,
    no_credential_creation_confirmed: true,
    no_webhook_dispatch_confirmed: true,
    no_invite_delivery_confirmed: true,
    no_membership_activation_confirmed: true,
    no_seat_assignment_confirmed: true,
    no_auth_claim_change_confirmed: true,
    no_campaign_activation_confirmed: true,
    no_go_live_action_confirmed: true,
    no_billing_or_money_movement_confirmed: true,
  };
}

function mockIntegrationExecutionReadiness(): ReferralSaasIntegrationExecutionReadinessResponse {
  return {
    status: "ok",
    context: "setup",
    account: mockTechnicalSetupReadiness().account,
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
  };
}

function mockReadyIntegrationExecutionReadiness(): ReferralSaasIntegrationExecutionReadinessResponse {
  const response = mockIntegrationExecutionReadiness();
  return {
    ...response,
    integrationConfiguration: mockIntegrationConfigurationSave().integrationConfigurationResult.configuration,
    integrationExecutionReadiness: {
      ...response.integrationExecutionReadiness,
      executionStatus: "INTEGRATION_EXECUTION_READY",
      plainLanguageSummary:
        "Saved Integrations setup can move into governed live verification checks. No live action has been run by this endpoint.",
      blockers: [],
      configurationRef: "integration-config-1",
      configurationStatus: "INTEGRATION_CONFIGURATION_SAVED",
      readyActions: [
        {
          actionRef: "API_ACCESS_VERIFICATION",
          label: "Verify API access",
          status: "READY",
          nextStep: "Run a governed API-access verification command in a later task.",
          reason: "Requires saved environment, auth method, and intended API use cases.",
        },
      ],
      executionActions: [
        {
          actionRef: "API_ACCESS_VERIFICATION",
          label: "Verify API access",
          status: "READY",
          nextStep: "Run a governed API-access verification command in a later task.",
          reason: "Requires saved environment, auth method, and intended API use cases.",
        },
        {
          actionRef: "WEBHOOK_TEST_DISPATCH",
          label: "Run webhook test dispatch",
          status: "READY",
          nextStep: "Run a guarded webhook test-dispatch command in a later task.",
          reason: "Requires an approved callback URL and selected event categories.",
        },
        {
          actionRef: "MESSAGE_PROVIDER_TEST",
          label: "Check message provider delivery",
          status: "MISSING_EVIDENCE",
          nextStep: "Run a governed provider delivery check in a later task.",
          reason: "Requires selected channels and approved provider references.",
        },
        {
          actionRef: "CREDENTIAL_REQUEST",
          label: "Request governed credentials",
          status: "READY",
          nextStep: "Submit a governed credential lifecycle request in a later task.",
          reason: "Requires the selected auth method without browser-supplied secrets.",
        },
      ],
    },
  };
}

function mockIntegrationConfigurationValidation() {
  return {
    status: "ok",
    context: "setup" as const,
    account: mockTechnicalSetupReadiness().account,
    validation: {
      commandStatus: "INTEGRATION_CONFIGURATION_VALIDATED",
      safeSetupPosture: { blockers: [] },
      guardrails: ["CUSTOMER_SCOPED_INTEGRATIONS_CONFIGURATION", "NO_SECRET_OR_CREDENTIAL_STORAGE"],
      redactions: ["internal_tenant_identifier", "tenant_code", "provider_secret"],
      noSecretOrCredentialStorageConfirmed: true,
      noCredentialCreationConfirmed: true,
      noWebhookDispatchConfirmed: true,
      noInviteDeliveryConfirmed: true,
      noMembershipActivationConfirmed: true,
      noSeatAssignmentConfirmed: true,
      noAuthClaimChangeConfirmed: true,
      noCampaignActivationConfirmed: true,
      noGoLiveActionConfirmed: true,
      noBillingOrMoneyMovementConfirmed: true,
    },
    guardrail: "Selected-customer Integrations configuration saved.",
    guardrails: ["CUSTOMER_SCOPED_INTEGRATIONS_CONFIGURATION", "NO_SECRET_OR_CREDENTIAL_STORAGE"],
    redactions: ["internal_tenant_identifier", "tenant_code", "provider_secret"],
    no_configuration_saved_confirmed: true,
    no_secret_or_credential_storage_confirmed: true,
    no_credential_creation_confirmed: true,
    no_webhook_dispatch_confirmed: true,
    no_invite_delivery_confirmed: true,
    no_billing_or_money_movement_confirmed: true,
  };
}

function mockIntegrationConfigurationSave() {
  return {
    status: "accepted",
    context: "setup" as const,
    account: mockTechnicalSetupReadiness().account,
    integrationConfigurationResult: {
      commandStatus: "INTEGRATION_CONFIGURATION_SAVED",
      configuration: {
        configurationRef: "integration-config-1",
        accountRef: "acct-gabs",
        configurationStatus: "INTEGRATION_CONFIGURATION_SAVED",
        apiEnvironment: {
          environment: "LOCAL_DEVELOPMENT",
          authMethod: "API_KEY",
          useCases: ["CAMPAIGN_READ", "REFERRAL_CODE_VALIDATE", "REPORT_READ"],
        },
        webhookIntent: {
          callbackUrl: "http://localhost:8000/webhooks/referral-saas",
          eventCategories: ["CAMPAIGN", "REFERRAL", "PROGRESS"],
          deliveryMode: "DRAFT_ONLY",
        },
        messageProviders: {
          channels: ["EMAIL"],
          providerRefs: [],
          approvalIntent: "DRAFT_ONLY",
        },
        safeSetupPosture: { blockers: [] },
        reasonCode: "CUSTOMER_INTEGRATION_CONFIGURATION",
        correlationId: "customer-profile-integrations-acct-gabs",
        createdByRef: "amplifi-admin",
        createdByRole: "ADMIN",
        createdAt: "2026-07-20T00:00:00",
        updatedAt: "2026-07-20T00:00:00",
        redactions: ["internal_tenant_identifier", "tenant_code", "provider_secret"],
      },
      validation: mockIntegrationConfigurationValidation().validation,
      idempotency: { status: "INTEGRATION_CONFIGURATION_SAVED" },
      audit: { accountAuditEventId: "audit-integrations-1" },
      guardrails: ["CUSTOMER_SCOPED_INTEGRATIONS_CONFIGURATION", "NO_SECRET_OR_CREDENTIAL_STORAGE"],
      redactions: ["internal_tenant_identifier", "tenant_code", "provider_secret"],
    },
    guardrail: "Selected-customer Integrations configuration saved.",
    guardrails: ["CUSTOMER_SCOPED_INTEGRATIONS_CONFIGURATION", "NO_SECRET_OR_CREDENTIAL_STORAGE"],
    redactions: ["internal_tenant_identifier", "tenant_code", "provider_secret"],
    no_secret_or_credential_storage_confirmed: true,
    no_credential_creation_confirmed: true,
    no_webhook_dispatch_confirmed: true,
    no_invite_delivery_confirmed: true,
    no_membership_activation_confirmed: true,
    no_seat_assignment_confirmed: true,
    no_auth_claim_change_confirmed: true,
    no_campaign_activation_confirmed: true,
    no_go_live_action_confirmed: true,
    no_billing_or_money_movement_confirmed: true,
  };
}

function mockCampaignReadiness(): ReferralSaasAccountCampaignReadinessResponse {
  return {
    status: "ok",
    context: "setup",
    account: {
      accountId: "acct-gabs",
      accountCode: "ACC-2201",
      accountName: "Gaborone Partners",
      accountStatus: "ACTIVE",
      onboardingStatus: "APPROVED",
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
      unknowns: [],
    },
    guardrail: "Read-only Referral SaaS customer-scoped campaign readiness.",
    redactions: ["internal_tenant_identifier"],
    no_campaign_mutation_confirmed: true,
    no_policy_write_confirmed: true,
    no_link_generation_confirmed: true,
    no_campaign_activation_confirmed: true,
    no_money_movement_confirmed: true,
  };
}

function mockCampaignList(): ReferralSaasAccountCampaignListResponse {
  return {
    status: "ok",
    context: "setup",
    account: {
      accountId: "acct-gabs",
      accountCode: "ACC-2201",
      accountName: "Gaborone Partners",
      accountStatus: "ACTIVE",
      onboardingStatus: "APPROVED",
    },
    count: 2,
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
      {
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
    ],
    guardrail: "Read-only Referral SaaS customer-scoped campaign list.",
    redactions: ["internal_tenant_identifier"],
    no_campaign_mutation_confirmed: true,
    no_policy_write_confirmed: true,
    no_link_generation_confirmed: true,
    no_campaign_activation_confirmed: true,
    no_money_movement_confirmed: true,
  };
}

function mockCampaignPolicySettings(): ReferralSaasAccountCampaignPolicySettingsResponse {
  return {
    status: "ok",
    context: "setup",
    account: {
      accountId: "acct-gabs",
      accountCode: "ACC-2201",
      accountName: "Gaborone Partners",
      accountStatus: "ACTIVE",
      onboardingStatus: "APPROVED",
    },
    policySettings: {
      commandStatus: "POLICY_SETTINGS_RECORDED",
      accountRef: "acct-gabs",
      campaignRef: "CAMP002",
      policySettings: {
        version: 2,
        setupStatus: "POLICY_SETTINGS_READY",
        attributionWindowDays: 45,
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
  };
}

function mockCampaignReview(status = "READY_FOR_REVIEW"): ReferralSaasAccountCampaignReviewResponse {
  return {
    status: "ok",
    context: "setup",
    account: {
      accountId: "acct-gabs",
      accountCode: "ACC-2201",
      accountName: "Gaborone Partners",
      accountStatus: "ACTIVE",
      onboardingStatus: "APPROVED",
    },
    campaignReview: {
      commandStatus: status === "REVIEW_APPROVED" ? "CAMPAIGN_REVIEW_DECISION_RECORDED" : "CAMPAIGN_REVIEW_SUBMITTED",
      accountRef: "acct-gabs",
      campaignRef: "CAMP002",
      previousReviewStatus: status === "REVIEW_APPROVED" ? "READY_FOR_REVIEW" : "POLICY_SETTINGS_READY",
      reviewStatus: status,
      setupStatus: "POLICY_SETTINGS_READY",
      readinessStatus: "READY_WITH_WARNINGS",
      activationEligibility:
        status === "REVIEW_APPROVED" ? "ELIGIBLE_FOR_FUTURE_ACTIVATION" : "NOT_ELIGIBLE_UNTIL_REVIEW_APPROVED",
      activationStatus: "INACTIVE",
      reviewerAction: status === "REVIEW_APPROVED" ? "Prepare activation request" : "Record review decision",
      idempotency: { status: "RECORDED" },
      audit: { accountAuditEventId: "audit-campaign-review-1" },
      nextActions: status === "REVIEW_APPROVED" ? ["Prepare activation request"] : ["Record review decision"],
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
  };
}

function mockCampaignActivation(): ReferralSaasAccountCampaignActivationResponse {
  return {
    status: "ok",
    context: "setup",
    account: {
      accountId: "acct-gabs",
      accountCode: "ACC-2201",
      accountName: "Gaborone Partners",
      accountStatus: "ACTIVE",
      onboardingStatus: "APPROVED",
    },
    campaignActivation: {
      commandStatus: "CAMPAIGN_ACTIVATION_ACCEPTED",
      accountRef: "acct-gabs",
      campaignRef: "CAMP002",
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
      nextActions: [
        "Open customer campaign operations",
        "Create or issue links and codes through the customer-scoped Links module",
        "Monitor readiness, attribution, progress, and reporting separately",
      ],
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
  };
}

describe("ReferralSaasAccountMaintenancePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedGetAdminOnboardingDrafts.mockResolvedValue(mockDraftSelector());
    mockedGetAdminOnboardingState.mockResolvedValue(mockMaintenanceState());
    mockedGetReferralSaasAccountMembershipPosture.mockResolvedValue(mockMembershipPosture());
    mockedGetReferralSaasIntegrationConfiguration.mockResolvedValue(mockIntegrationConfigurationRead());
    mockedGetReferralSaasIntegrationExecutionReadiness.mockResolvedValue(mockIntegrationExecutionReadiness());
    mockedGetReferralSaasMembershipActivationReadiness.mockResolvedValue(mockMembershipActivationReadiness());
    mockedGetReferralSaasTechnicalSetupReadiness.mockResolvedValue(mockTechnicalSetupReadiness());
    mockedListReferralSaasAccountCampaigns.mockResolvedValue(mockCampaignList());
    mockedGetReferralSaasAccountReport.mockResolvedValue({
      status: "ok",
      report: {
        report_type: "campaign_performance",
        metrics: [
          {
            campaign_code: "CAMP001",
            metric_name: "referrals.completed_count",
            value: 4,
            status: "AVAILABLE",
          },
        ],
        warnings: [],
      },
      account_scope: {
        source: "selected_customer_account",
        account_ref: "acct-gabs",
        external_tenant_ref: "gabs-platform",
      },
      guardrail: "Customer-scoped report wrapper.",
    });
    mockedPreviewReferralSaasAccountReportExport.mockResolvedValue({
      status: "ok",
      export_preview: {
        status: "PREVIEW_READY",
        sample_rows: [
          {
            campaign_code: "CAMP001",
            metric_name: "referrals.completed_count",
            value: 4,
          },
        ],
      },
      account_scope: {
        source: "selected_customer_account",
        account_ref: "acct-gabs",
        external_tenant_ref: "gabs-platform",
      },
      guardrail: "Preview only.",
    });
    mockedGetReferralSaasAccountCampaignReadiness.mockResolvedValue(mockCampaignReadiness());
    mockedUpdateReferralSaasAccountCampaignPolicySettings.mockResolvedValue(mockCampaignPolicySettings());
    mockedSubmitReferralSaasAccountCampaignReview.mockResolvedValue(mockCampaignReview());
    mockedRecordReferralSaasAccountCampaignReviewDecision.mockResolvedValue(mockCampaignReview("REVIEW_APPROVED"));
    mockedRequestReferralSaasAccountCampaignActivation.mockResolvedValue(mockCampaignActivation());
    mockedRequestReferralSaasAccountFoundationActivation.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-fnb",
        accountCode: "ACCT_FNB",
        accountName: "FNB Referral SaaS",
        accountStatus: "ACTIVE",
        onboardingStatus: "APPROVED",
      },
      activation: {
        accountId: "acct-fnb",
        accountCode: "ACCT_FNB",
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
    mockedIssueReferralSaasAccountCampaignCode.mockResolvedValue({
      status: "ok",
      linkCode: {
        issueStatus: "CREATED",
        referralCode: "REF123",
        publicHandle: "gabs-owner",
        sourceType: "REFERRAL_CODE",
      },
      no_tenant_code_exposure_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_webhook_delivery_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });
    mockedValidateReferralSaasAccountCampaignCode.mockResolvedValue({
      status: "ok",
      validation: {
        validationStatus: "VALIDATED",
        referralTrackId: "track-1",
        message: "Referral code validated",
      },
      no_tenant_code_exposure_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_webhook_delivery_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });
    mockedValidateReferralSaasIntegrationConfiguration.mockResolvedValue(mockIntegrationConfigurationValidation());
    mockedSaveReferralSaasIntegrationConfiguration.mockResolvedValue(mockIntegrationConfigurationSave());
    mockedListReferralSaasAccounts.mockResolvedValue(mockAccountRegistry());
    mockedRecordReferralSaasMembershipInvitationIntent.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACC-2201",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
        onboardingStatus: "APPROVED",
      },
      invitation: {
        commandStatus: "INVITATION_INTENT_RECORDED",
        membership: {
          membershipRef: "membership-1",
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
          status: "NEW_REQUEST",
        },
        auditEventId: "audit-1",
        guardrails: ["NO_INVITE_DELIVERY"],
        redactions: ["INTERNAL_TENANT_IDENTIFIER"],
        noInviteDeliveryConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noMoneyMovementConfirmed: true,
      },
      guardrails: ["NO_INVITE_DELIVERY"],
      redactions: ["INTERNAL_TENANT_IDENTIFIER"],
      no_invite_delivery_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_money_movement_confirmed: true,
    });
    mockedRequestReferralSaasMembershipInvitationDelivery.mockResolvedValue({
      status: "blocked",
      context: "setup",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACC-2201",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
        onboardingStatus: "APPROVED",
      },
      deliveryRequest: {
        commandStatus: "DELIVERY_PROVIDER_NOT_CONFIGURED",
        membership: {
          membershipRef: "membership-1",
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
    mockedRequestReferralSaasMembershipActivation.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACC-2201",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
        onboardingStatus: "APPROVED",
      },
      activationRequest: {
        commandStatus: "MEMBERSHIP_ACTIVATED",
        membership: {
          membershipRef: "membership-1",
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
    mockedRequestReferralSaasAccessProvisioning.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACC-2201",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
        onboardingStatus: "APPROVED",
      },
      accessProvisioning: {
        commandStatus: "PROVISIONING_REQUEST_RECORDED",
        membership: {
          membershipRef: "membership-1",
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
    mockedUpdateReferralSaasMembershipInvitationIntent.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACC-2201",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
        onboardingStatus: "APPROVED",
      },
      invitation: {
        commandStatus: "INVITATION_INTENT_UPDATED",
        membership: {
          membershipRef: "membership-1",
          previousStatus: "INVITED",
          status: "INVITED",
          previousRoleFamily: "DISTRIBUTION_ADMIN",
          roleFamily: "CAMPAIGN_MANAGER",
          previousPermissionSet: "REFERRAL_SAAS_ACCOUNT_ADMIN",
          permissionSet: "REFERRAL_SAAS_CAMPAIGN_MANAGER",
          canOperateSetup: false,
        },
        lifecycle: {
          status: "INVITATION_INTENT_UPDATED",
          nextAction: "Review the updated access intent before invite delivery.",
        },
        idempotency: {
          status: "RECORDED",
        },
        auditEventId: "audit-update-1",
        guardrails: ["NO_INVITE_DELIVERY"],
        redactions: ["INTERNAL_TENANT_IDENTIFIER", "email_hash"],
        noInviteDeliveryConfirmed: true,
        noMembershipActivationConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noMoneyMovementConfirmed: true,
      },
      guardrails: ["NO_INVITE_DELIVERY"],
      redactions: ["INTERNAL_TENANT_IDENTIFIER", "email_hash"],
      no_invite_delivery_confirmed: true,
      no_membership_activation_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_money_movement_confirmed: true,
    });
    mockedCancelReferralSaasMembershipInvitationIntent.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACC-2201",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
        onboardingStatus: "APPROVED",
      },
      invitation: {
        commandStatus: "INVITATION_INTENT_CANCELLED",
        membership: {
          membershipRef: "membership-1",
          previousStatus: "INVITED",
          status: "DISABLED",
          previousRoleFamily: "DISTRIBUTION_ADMIN",
          roleFamily: "DISTRIBUTION_ADMIN",
          previousPermissionSet: "REFERRAL_SAAS_ACCOUNT_ADMIN",
          permissionSet: "REFERRAL_SAAS_ACCOUNT_ADMIN",
          canOperateSetup: false,
        },
        lifecycle: {
          status: "INVITATION_INTENT_CANCELLED",
          nextAction: "Record a new access intent if this customer still needs that responsibility.",
        },
        idempotency: {
          status: "RECORDED",
        },
        auditEventId: "audit-cancel-1",
        guardrails: ["NO_INVITE_DELIVERY"],
        redactions: ["INTERNAL_TENANT_IDENTIFIER"],
        noInviteDeliveryConfirmed: true,
        noMembershipActivationConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noMoneyMovementConfirmed: true,
      },
      guardrails: ["NO_INVITE_DELIVERY"],
      redactions: ["INTERNAL_TENANT_IDENTIFIER"],
      no_invite_delivery_confirmed: true,
      no_membership_activation_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_money_movement_confirmed: true,
    });
    mockedUpdateReferralSaasAccountProfile.mockResolvedValue({
      status: "ok",
      profile: {
        accountId: "acct-gabs",
        accountCode: "ACC-2201",
        accountName: "Gaborone Partners Updated",
        accountType: "ORGANISATION",
        accountStatus: "ACTIVE",
        onboardingStatus: "APPROVED",
        operatingJurisdictionCode: "BW",
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
    mockedCreateReferralSaasAccountCampaignSetup.mockResolvedValue({
      status: "created",
      context: "setup",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACC-2201",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
        onboardingStatus: "APPROVED",
      },
      campaignSetup: {
        commandStatus: "CAMPAIGN_SETUP_DRAFT_RECORDED",
        accountRef: "acct-gabs",
        campaign: {
          campaignRef: "BW-REFERRAL-SPRING-1234",
          campaignCode: "BW-REFERRAL-SPRING-1234",
          name: "Spring referral pilot",
          segment: "Retail banking customers",
          setupStatus: "DRAFT",
          isActive: false,
          startsAt: null,
          endsAt: null,
          maxUses: 100,
        },
        idempotency: { status: "RECORDED" },
        audit: { accountAuditEventId: "audit-campaign-1" },
        nextActions: [
          "Complete policy and attribution settings",
          "Run campaign readiness",
          "Review before activation",
        ],
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
  });

  afterEach(() => {
    cleanup();
  });

  it("starts with jurisdiction selection before scoped customer work", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />);

    expect(await screen.findByRole("heading", { name: "Find the customer to work on" })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "1. Where do you operate?" })).toBeInTheDocument();
    expect(screen.getByText("Pick the country. You will only see customers in that market.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /South Africa/ })).toHaveTextContent("2 accounts");
    expect(screen.getByRole("button", { name: /Botswana/ })).toHaveTextContent("1 account");
    expect(screen.getByRole("button", { name: /Zambia/ })).toHaveTextContent("0 accounts");
    expect(await screen.findByRole("heading", { name: "2. Which customer?" })).toBeInTheDocument();
    expect(screen.getByText(/Only accounts in South Africa/)).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: /FNB Referral SaaS/ })).toBeInTheDocument();
    expect(screen.getAllByText("Customer reference")[0]).toBeInTheDocument();
    expect(screen.getAllByText("Organisation reference")[0]).toBeInTheDocument();
    expect(screen.getAllByText("Account code")[0]).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /FNB Referral SaaS/ })).toHaveTextContent("fnb-referrals");
    expect(screen.getByRole("button", { name: /FNB Referral SaaS/ })).toHaveTextContent("fnb-org");
    expect(screen.getByRole("button", { name: /FNB Referral SaaS/ })).toHaveTextContent("ACCT_FNB");
    expect(screen.getByRole("link", { name: "Open customer profile" })).toHaveAttribute("aria-disabled", "true");
    expect(screen.queryByRole("heading", { name: "Client workspace" })).not.toBeInTheDocument();
    expect(mockedListReferralSaasAccounts).toHaveBeenCalledWith(50);
    expect(JSON.stringify(mockedListReferralSaasAccounts.mock.calls)).not.toMatch(
      /tenant_code|api_key|client_secret/i,
    );
  });

  it("filters customers by jurisdiction and opens the selected customer home", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />);

    fireEvent.click(await screen.findByRole("button", { name: /Botswana/ }));
    expect(screen.getByText(/Only accounts in Botswana/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Gaborone Partners/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /FNB Referral SaaS/ })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Gaborone Partners/ }));
    expect(screen.getByRole("link", { name: "Open customer profile" })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs",
    );
    fireEvent.click(screen.getByRole("link", { name: "Open customer profile" }));

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.getByLabelText("Selected customer context")).toHaveTextContent("Botswana");
    expect(screen.getByLabelText("Selected customer context")).toHaveTextContent("Operating jurisdiction");
    expect(screen.getByLabelText("Selected customer context")).toHaveTextContent("Account status");
    expect(screen.getByLabelText("Selected customer context")).toHaveTextContent("Account code");
    expect(screen.getByLabelText("Selected customer context")).toHaveTextContent("Customer reference");
    expect(screen.getByLabelText("Selected customer context")).toHaveTextContent("Organisation reference");
    expect(screen.getByLabelText("Selected customer context")).toHaveTextContent("gabs-platform");
    expect(screen.getByLabelText("Selected customer context")).toHaveTextContent("gabs-org");
    expect(screen.getByText("This is the customer home. Campaigns, links, reports, attribution, and support stay inside this customer context.")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Health at a glance" })).toBeInTheDocument();
    expect(screen.getByText("Green")).toBeInTheDocument();
    expect(screen.getByText("Red")).toBeInTheDocument();
    expect(screen.getByText("Amber")).toBeInTheDocument();
    expect(screen.getByText("No action needed")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Fix first: Add who can manage this account/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/people",
    );
    expect(screen.getByRole("link", { name: /Review later: Open Campaigns/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/campaigns",
    );
    expect(screen.getByRole("heading", { name: "Do this next" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /^Add who can manage this account/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/people",
    );
    expect(screen.getByRole("link", { name: /Check integrations/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/integrations",
    );
    expect(screen.queryByRole("heading", { name: "People and access" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /^Open Campaigns/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/campaigns",
    );
    expect(await screen.findByText("Everything opens against Gaborone Partners until you switch customer.")).toBeInTheDocument();
    expect(screen.getByText(/Not on this page: customer settings form, people invite form, or full health table/i)).toBeInTheDocument();
  });

  it("exposes guarded customer foundation activation before seat provisioning", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-fnb");

    expect(await screen.findByRole("heading", { name: "FNB Referral SaaS" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Account foundation" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Activate customer foundation" })).toBeInTheDocument();
    expect(screen.getByText(/creates bounded platform seat capacity/i)).toBeInTheDocument();
    expect(screen.getByText(/does not assign seats, send invites, create credentials/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Activate foundation" }));

    await waitFor(() => expect(mockedRequestReferralSaasAccountFoundationActivation).toHaveBeenCalledTimes(1));
    expect(mockedRequestReferralSaasAccountFoundationActivation.mock.calls[0][0]).toEqual({
      accountRef: "acct-fnb",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "fnb-referrals",
        context: "setup",
      },
      activation: {
        seatTypes: ["ADMIN", "OPERATOR"],
      },
      reasonCode: "CUSTOMER_ACCOUNT_FOUNDATION_ACTIVATION",
      correlationId: "customer-profile-account-foundation-activation-acct-fnb",
      idempotencyKey: "customer-profile-account-foundation-activation-acct-fnb-v1",
    });
    expect(await screen.findByText("Customer foundation activated.")).toBeInTheDocument();
    expect(screen.getByText(/seat.*available for later provisioning/i)).toBeInTheDocument();
    expect(JSON.stringify(mockedRequestReferralSaasAccountFoundationActivation.mock.calls)).not.toMatch(
      /tenantCode|tenant_code|membershipWrite|seatAssignment|sendInvite|credential|authClaim|campaignActivation|goLive|billing|money/i,
    );
  });

  it("does not show a customer foundation activation result for a different selected account", async () => {
    mockedRequestReferralSaasAccountFoundationActivation.mockResolvedValueOnce({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-rmca",
        accountCode: "ACCT_RMCA",
        accountName: "Test FNB RMCA 002",
        accountStatus: "ACTIVE",
        onboardingStatus: "APPROVED",
      },
      activation: {
        accountId: "acct-rmca",
        accountCode: "ACCT_RMCA",
        accountName: "Test FNB RMCA 002",
        previousAccountStatus: "PENDING_ONBOARDING",
        accountStatus: "ACTIVE",
        previousOnboardingStatus: "READY_FOR_REVIEW",
        onboardingStatus: "APPROVED",
        previousTenantLinkStatus: "PENDING_SETUP",
        tenantLinkStatus: "ACTIVE",
        seatCapacity: { seatTypes: ["ADMIN", "OPERATOR"], createdSeatCount: 2 },
        commandStatus: "ACCOUNT_FOUNDATION_ACTIVATED",
        auditEventId: "audit-account-activation-rmca",
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
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-fnb");

    expect(await screen.findByRole("heading", { name: "FNB Referral SaaS" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Activate foundation" }));

    await waitFor(() => expect(mockedRequestReferralSaasAccountFoundationActivation).toHaveBeenCalledTimes(1));
    await waitFor(() =>
      expect(screen.queryByText("Customer foundation activated.")).not.toBeInTheDocument(),
    );
    expect(screen.queryByText(/Test FNB RMCA 002 foundation/i)).not.toBeInTheDocument();
  });

  it("opens People and Access as its own customer page from the next-best action", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs");

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("link", { name: /^Add who can manage this account/ }));

    expect(await screen.findByRole("heading", { name: "People and access" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Customer home" })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs",
    );
    expect(screen.queryByRole("heading", { name: "Health at a glance" })).not.toBeInTheDocument();
  });

  it("does not keep people access as the customer-home blocker after required access is accepted", async () => {
    mockedGetReferralSaasAccountMembershipPosture.mockResolvedValue(mockAcceptedRequiredMembershipPosture());
    mockedGetReferralSaasMembershipActivationReadiness.mockResolvedValue(
      mockAcceptedRequiredMembershipActivationReadiness(),
    );

    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs");

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Fix first: Add who can manage this account/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /^Add who can manage this account/ })).not.toBeInTheDocument();
    expect(screen.getByText("No blocker")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /^Check integrations/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/integrations",
    );
    expect(screen.getByText("People and access").closest(".customer-function-card")).toHaveTextContent("Ready");
    expect(screen.getByText("People and access").closest(".customer-function-card")).toHaveTextContent(
      "Required customer managers are confirmed.",
    );
    expect(screen.getByText("Roles still missing").closest(".kpi-card")).toHaveTextContent("0");
  });

  it("records customer-scoped people access intent without leaving Customer Profile", async () => {
    mockedGetReferralSaasAccountMembershipPosture
      .mockResolvedValueOnce(mockMembershipPosture())
      .mockResolvedValue(mockMembershipPostureAfterCampaignManagerSave());
    mockedGetReferralSaasMembershipActivationReadiness
      .mockResolvedValueOnce(mockMembershipActivationReadiness())
      .mockResolvedValue(mockMembershipActivationReadinessAfterCampaignManagerSave());
    mockedRecordReferralSaasMembershipInvitationIntent.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACC-2201",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
        onboardingStatus: "APPROVED",
      },
      invitation: {
        commandStatus: "INVITATION_INTENT_RECORDED",
        membership: {
          membershipRef: "membership-campaign-manager",
          status: "INVITED",
          roleFamily: "CAMPAIGN_MANAGER",
          permissionSet: "REFERRAL_SAAS_CAMPAIGN_MANAGER",
          canOperateSetup: false,
        },
        delivery: {
          status: "DELIVERY_NOT_CONFIGURED",
          nextAction: "Configure approved invitation delivery provider",
        },
        idempotency: {
          status: "NEW_REQUEST",
        },
        auditEventId: "audit-campaign-manager",
        guardrails: ["NO_INVITE_DELIVERY"],
        redactions: ["INTERNAL_TENANT_IDENTIFIER"],
        noInviteDeliveryConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noMoneyMovementConfirmed: true,
      },
      guardrails: ["NO_INVITE_DELIVERY"],
      redactions: ["INTERNAL_TENANT_IDENTIFIER"],
      no_invite_delivery_confirmed: true,
      no_auth_claim_change_confirmed: true,
      no_seat_assignment_confirmed: true,
      no_money_movement_confirmed: true,
    });
    const { container } = renderWorkspace(
      <ReferralSaasAccountMaintenancePage />,
      "/admin/referral-saas/account-maintenance/acct-gabs/people",
    );

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "People and access" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Add person" }));
    expect(screen.getByText(/This saves intent only/i)).toBeInTheDocument();
    expect(screen.getByText(/Used as the access identity for this customer/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Example: John Doe")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.getByText("People setup needs attention")).toBeInTheDocument();
    expect(screen.getByText("Still need Campaign manager.")).toBeInTheDocument();
    expect(screen.getByText("Platform login setup")).toBeInTheDocument();
    expect(container.textContent).toContain("Finish confirming the required customer responsibilities first.");
    expect(container.textContent).toContain("Use platform login setup only when a confirmed person needs to sign in to Amplifi.");
    expect(container.textContent).toContain("Next: Add the person who owns this responsibility.");
    fireEvent.click(screen.getByRole("button", { name: "Show access diagnostics" }));
    expect(await screen.findByText("Readiness")).toBeInTheDocument();
    expect(container.textContent).toContain("Contact: CONTACT_REFERENCE_PRESENT");
    expect(screen.getAllByText(/Campaign Manager/i).length).toBeGreaterThan(0);
    expect(screen.getByText("Configure an approved invitation delivery provider before sending invites.")).toBeInTheDocument();
    expect(screen.getAllByText("Gaborone owner").length).toBeGreaterThan(0);
    expect(screen.getAllByText("owner@gabs.example").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Check invite delivery" })).toBeDisabled();
    expect(screen.getByText("Provider not approved")).toBeInTheDocument();
    expect(mockedGetReferralSaasMembershipActivationReadiness).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      refType: "external_tenant_ref",
      externalRef: "gabs-platform",
      context: "setup",
    });

    fireEvent.click(screen.getByRole("button", { name: "Add person" }));
    fireEvent.change(screen.getByLabelText("Person name"), {
      target: { value: "Gaborone campaign owner" },
    });
    fireEvent.change(screen.getByLabelText(/Work email/), {
      target: { value: "Gabs.Campaign.Owner@Example.COM" },
    });
    fireEvent.change(screen.getByLabelText("Responsibility"), {
      target: { value: "Campaign manager" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save person intent" }));

    await waitFor(() => expect(mockedRecordReferralSaasMembershipInvitationIntent).toHaveBeenCalledTimes(1));
    expect(mockedRecordReferralSaasMembershipInvitationIntent.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      actor: {
        actorType: "USER",
        subject: "gabs.campaign.owner@example.com",
        emailHash: expect.any(String),
        displayName: "Gaborone campaign owner",
      },
      membership: {
        roleFamily: "CAMPAIGN_MANAGER",
        permissionSet: "REFERRAL_SAAS_CAMPAIGN_MANAGER",
        tenantScope: "PRIMARY_ACCOUNT_TENANT",
      },
      reasonCode: "CUSTOMER_PROFILE_ACCESS_MAINTENANCE",
      correlationId: "customer-profile-access-acct-gabs",
      idempotencyKey: expect.stringMatching(
        /^customer-profile-access-acct-gabs-gabs-campaign-owner-example-com-gaborone-campaign-owner-campaign-manager-/,
      ),
    });
    expect(await screen.findByText("Access intent saved.")).toBeInTheDocument();
    expect((await screen.findAllByText("Gaborone campaign owner")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("gabs.campaign.owner@example.com").length).toBeGreaterThan(0);
    expect(screen.getByText("People are confirmed")).toBeInTheDocument();
    expect(screen.getByText(/No invitation email, login activation, seat assignment, or auth claim change was performed/i)).toBeInTheDocument();
    expect(mockedGetReferralSaasMembershipActivationReadiness).toHaveBeenCalledTimes(2);
  });

  it("hides removed access intents from the primary People and Access list", async () => {
    mockedGetReferralSaasAccountMembershipPosture
      .mockResolvedValueOnce(mockMembershipPosture())
      .mockResolvedValue(mockDisabledMembershipPosture());
    mockedGetReferralSaasMembershipActivationReadiness
      .mockResolvedValueOnce(mockMembershipActivationReadiness())
      .mockResolvedValue(mockMembershipActivationReadinessMissingAll());

    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/people");

    expect(await screen.findByRole("heading", { name: "People and access" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getAllByText("Gaborone owner").length).toBeGreaterThan(0));

    fireEvent.click(screen.getByRole("button", { name: "Remove" }));

    await waitFor(() => expect(mockedCancelReferralSaasMembershipInvitationIntent).toHaveBeenCalledTimes(1));
    expect(await screen.findByText("Access intent updated.")).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByText("Gaborone owner")).not.toBeInTheDocument());
    expect(screen.getByText("People setup needs attention")).toBeInTheDocument();
    expect(screen.getAllByText("Account owner").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Campaign manager").length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: "Add" }).length).toBeGreaterThanOrEqual(2);
  });

  it("checks invite delivery from People and Access when provider and contact evidence are ready", async () => {
    mockedGetReferralSaasTechnicalSetupReadiness.mockResolvedValue(mockTechnicalSetupReadinessWithInviteProvider());
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/people");

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Show access diagnostics" }));
    const deliveryButton = await screen.findByRole("button", { name: "Check invite delivery" });
    expect(deliveryButton).toBeEnabled();

    fireEvent.click(deliveryButton);

    await waitFor(() => expect(mockedRequestReferralSaasMembershipInvitationDelivery).toHaveBeenCalledTimes(1));
    expect(mockedRequestReferralSaasMembershipInvitationDelivery.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      membershipRef: "membership-1",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      delivery: {
        providerRef: "mail-provider-1",
        channel: "EMAIL",
        templateRef: "referral-saas-account-invite-v1",
      },
      reasonCode: "CUSTOMER_PROFILE_INVITE_DELIVERY_REQUEST",
      correlationId: "customer-profile-invite-delivery-acct-gabs",
      idempotencyKey: "customer-profile-invite-delivery-acct-gabs-membership-1-distribution-admin",
    });
    expect(await screen.findByText("Invite delivery checked.")).toBeInTheDocument();
    expect(screen.getByText(/No email was sent, no login was activated, no seat was assigned/i)).toBeInTheDocument();
    expect(JSON.stringify(mockedRequestReferralSaasMembershipInvitationDelivery.mock.calls)).not.toMatch(
      /recipientHash|tenantCode|sendInvite|activate|seat|money/i,
    );
  });

  it("records accepted access from People and Access through the activation boundary", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/people");

    expect(await screen.findByRole("heading", { name: "People and access" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Show access diagnostics" }));
    const activationButton = await screen.findByRole("button", { name: "Record accepted access" });
    expect(activationButton).toBeEnabled();
    expect(screen.getByText("Will validate gates")).toBeInTheDocument();

    fireEvent.click(activationButton);

    await waitFor(() => expect(mockedRequestReferralSaasMembershipActivation).toHaveBeenCalledTimes(1));
    expect(mockedRequestReferralSaasMembershipActivation.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      membershipRef: "membership-1",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      activation: {
        acceptedSubject: "owner@gabs.example",
        acceptanceEvidenceRef: "customer-profile-accepted-acct-gabs-membership-1",
      },
      reasonCode: "CUSTOMER_PROFILE_ACCESS_ACCEPTANCE",
      correlationId: "customer-profile-access-activation-acct-gabs",
      idempotencyKey: "customer-profile-access-activation-acct-gabs-membership-1-distribution-admin",
    });
    expect(await screen.findByText("Accepted access recorded.")).toBeInTheDocument();
    expect(screen.getByText(/No invite email was sent, no seat was assigned, no auth claim changed/i)).toBeInTheDocument();
    expect(JSON.stringify(mockedRequestReferralSaasMembershipActivation.mock.calls)).not.toMatch(
      /tenantCode|sendInvite|seatId|authClaims|goLive|wallet|settlement|money/i,
    );
  });

  it("shows accepted access separately from login and seat provisioning", async () => {
    mockedGetReferralSaasAccountMembershipPosture.mockResolvedValue(mockActiveMembershipPosture());
    mockedGetReferralSaasMembershipActivationReadiness.mockResolvedValue(mockActiveMembershipActivationReadiness());
    const { container } = renderWorkspace(
      <ReferralSaasAccountMaintenancePage />,
      "/admin/referral-saas/account-maintenance/acct-gabs/people",
    );

    expect(await screen.findByRole("heading", { name: "People and access" })).toBeInTheDocument();
    expect(screen.getAllByText("Confirmed").length).toBeGreaterThan(0);
    expect(screen.getByText("Still need Campaign manager.")).toBeInTheDocument();
    expect(container.textContent).toContain("Next: Confirmed for customer work. Set up platform login later only if this person must sign in.");
    expect(screen.getByText("Platform login setup")).toBeInTheDocument();
    expect(container.textContent).toContain("Finish confirming the required customer responsibilities first.");
    expect(screen.getByText("Use it for Amplifi sign-in access.")).toBeInTheDocument();
    expect(screen.getByText("Skip it when the person only owns the relationship outside the platform.")).toBeInTheDocument();
    expect(screen.getByText("Optional login setup")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Set up platform login" })).toBeEnabled();
  });

  it("requests optional platform login setup after access has been confirmed", async () => {
    mockedGetReferralSaasAccountMembershipPosture.mockResolvedValue(mockActiveMembershipPosture());
    mockedGetReferralSaasMembershipActivationReadiness
      .mockResolvedValueOnce(mockActiveMembershipActivationReadiness())
      .mockResolvedValue(mockSeatProvisionedMembershipActivationReadiness());
    const { container } = renderWorkspace(
      <ReferralSaasAccountMaintenancePage />,
      "/admin/referral-saas/account-maintenance/acct-gabs/people",
    );

    expect(await screen.findByRole("heading", { name: "People and access" })).toBeInTheDocument();
    const provisioningButton = await screen.findByRole("button", { name: "Set up platform login" });
    expect(provisioningButton).toBeEnabled();

    fireEvent.click(provisioningButton);

    await waitFor(() => expect(mockedRequestReferralSaasAccessProvisioning).toHaveBeenCalledTimes(1));
    expect(mockedRequestReferralSaasAccessProvisioning.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      membershipRef: "membership-1",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      provisioning: {
        seatType: "ADMIN",
        seatAssignmentEvidenceRef: "customer-profile-seat-provisioning-evidence-acct-gabs-membership-1-distribution-admin",
        operatorNotes:
          "Amplifi Admin requested governed seat provisioning from the selected customer People and Access page.",
      },
      reasonCode: "CUSTOMER_PROFILE_ACCESS_PROVISIONING_REQUEST",
      correlationId: "customer-profile-access-provisioning-acct-gabs",
      idempotencyKey: "customer-profile-access-provisioning-acct-gabs-membership-1-distribution-admin-admin",
    });
    expect(await screen.findByText("Login setup recorded.")).toBeInTheDocument();
    expect(container.textContent).toContain("Platform login set up");
    expect(JSON.stringify(mockedRequestReferralSaasAccessProvisioning.mock.calls)).not.toMatch(
      /tenantCode|sendInvite|credential|authClaims|goLive|wallet|settlement|money/i,
    );
  });

  it("lets Amplifi Admin record manual access acceptance from the edit drawer", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/people");

    expect(await screen.findByRole("heading", { name: "People and access" })).toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: "Edit" }));
    expect(screen.getByRole("heading", { name: "Edit person access" })).toBeInTheDocument();
    expect(screen.getByText("Manual access acceptance")).toBeInTheDocument();
    expect(screen.getAllByText(/does not send email, assign a seat, or change login permissions/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/This is separate from Save person details/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save person details" })).toBeInTheDocument();
    const manualAcceptanceButton = screen.getByRole("button", { name: "Record accepted access" });
    expect(manualAcceptanceButton).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Acceptance evidence"), {
      target: { value: "Approved by customer admin on onboarding call" },
    });
    expect(manualAcceptanceButton).toBeEnabled();
    fireEvent.click(manualAcceptanceButton);

    await waitFor(() => expect(mockedRequestReferralSaasMembershipActivation).toHaveBeenCalledTimes(1));
    expect(mockedRequestReferralSaasMembershipActivation.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      membershipRef: "membership-1",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      activation: {
        acceptedSubject: "owner@gabs.example",
        acceptanceEvidenceRef:
          "manual-access-acceptance-acct-gabs-membership-1-owner-gabs-example-approved-by-customer-admin-on-onboarding-call",
      },
      reasonCode: "AMPLIFI_ADMIN_MANUAL_ACCESS_ACCEPTANCE",
      correlationId: "customer-profile-access-activation-acct-gabs",
      idempotencyKey:
        "customer-profile-access-activation-acct-gabs-membership-1-owner-gabs-example-approved-by-customer-admin-on-onboarding-call-distribution-admin",
    });
    expect(await screen.findByText("Accepted access recorded.")).toBeInTheDocument();
  });

  it("opens Integrations as a customer-scoped configuration page", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/integrations");

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Integrations" })).toBeInTheDocument();
    expect(screen.getByText(/Save safe setup evidence for API, webhook, invite delivery, and referral-message connections/i)).toBeInTheDocument();
    expect(await screen.findByText("Ready providers")).toBeInTheDocument();
    expect(screen.getByText("Need setup")).toBeInTheDocument();
    expect(screen.getByText("Supported channels")).toBeInTheDocument();
    expect(screen.getByText("Saved setup evidence")).toBeInTheDocument();
    expect(screen.getByText("1. API access intent")).toBeInTheDocument();
    expect(screen.getByText("2. Webhook intent")).toBeInTheDocument();
    expect(screen.getByText("3. Message provider intent")).toBeInTheDocument();
    expect(screen.getByText("4. Live readiness check")).toBeInTheDocument();
    expect(screen.getByText(/Save Integrations setup evidence before live verification can start/i)).toBeInTheDocument();
    expect(screen.getByText("Save Integrations setup")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Validate setup" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save setup evidence" })).toBeInTheDocument();
    expect(screen.getByText("People invite delivery")).toBeInTheDocument();
    expect(screen.getByText("Configure and approve the Email provider for Referral SaaS before sending account access invites.")).toBeInTheDocument();
    expect(screen.getByText("Referral journey messages")).toBeInTheDocument();
    expect(screen.getByText(/No credentials are created, no webhook is dispatched, no invite is sent/i)).toBeInTheDocument();
    expect(mockedGetReferralSaasIntegrationConfiguration).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      refType: "external_tenant_ref",
      externalRef: "gabs-platform",
      context: "setup",
    });
    expect(mockedGetReferralSaasIntegrationExecutionReadiness).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      refType: "external_tenant_ref",
      externalRef: "gabs-platform",
      context: "setup",
    });
    expect(mockedGetReferralSaasTechnicalSetupReadiness).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      refType: "external_tenant_ref",
      externalRef: "gabs-platform",
      context: "setup",
    });
    expect(screen.queryByRole("heading", { name: "Health at a glance" })).not.toBeInTheDocument();
  });

  it("validates and saves Integrations configuration without live side effects", async () => {
    mockedGetReferralSaasIntegrationExecutionReadiness
      .mockResolvedValueOnce(mockIntegrationExecutionReadiness())
      .mockResolvedValueOnce(mockReadyIntegrationExecutionReadiness());
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/integrations");

    expect(await screen.findByRole("heading", { name: "Integrations" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Validate setup" }));

    await waitFor(() => expect(mockedValidateReferralSaasIntegrationConfiguration).toHaveBeenCalledTimes(1));
    expect(mockedValidateReferralSaasIntegrationConfiguration).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      apiEnvironment: {
        environment: "LOCAL_DEVELOPMENT",
        authMethod: "API_KEY",
        useCases: ["CAMPAIGN_READ", "REFERRAL_CODE_VALIDATE", "REPORT_READ"],
      },
      webhookIntent: {
        callbackUrl: "http://localhost:8000/webhooks/referral-saas",
        eventCategories: ["CAMPAIGN", "REFERRAL", "PROGRESS"],
        deliveryMode: "DRAFT_ONLY",
      },
      messageProviders: {
        channels: ["EMAIL"],
        providerRefs: [],
        approvalIntent: "DRAFT_ONLY",
      },
      reasonCode: "CUSTOMER_INTEGRATION_CONFIGURATION",
      correlationId: "customer-profile-integrations-acct-gabs",
      idempotencyKey:
        "customer-profile-integrations-acct-gabs-local-development-api-key-campaign-read-referral-code-validate-report-read-http-localhost-8000-webhooks-referral-saas-campaign-referral-progress-email-email",
    });
    expect(JSON.stringify(mockedValidateReferralSaasIntegrationConfiguration.mock.calls)).not.toMatch(
      /tenantCode|tenant_code|secret|credential|apiKey/i,
    );

    fireEvent.click(screen.getByRole("button", { name: "Save setup evidence" }));
    await waitFor(() => expect(mockedSaveReferralSaasIntegrationConfiguration).toHaveBeenCalledTimes(1));
    expect(mockedSaveReferralSaasIntegrationConfiguration.mock.calls[0][0]).toMatchObject({
      accountRef: "acct-gabs",
      reasonCode: "CUSTOMER_INTEGRATION_CONFIGURATION",
      correlationId: "customer-profile-integrations-acct-gabs",
    });
    expect(await screen.findByText(/Integrations setup updated/i)).toBeInTheDocument();
    expect(screen.getByText(/no credentials, webhook dispatch, invite delivery, campaign activation, billing, or money movement occurred/i)).toBeInTheDocument();
    expect(await screen.findByText("Verify API access")).toBeInTheDocument();
    expect(screen.getByText(/governed live verification checks/i)).toBeInTheDocument();
    expect(mockedGetReferralSaasIntegrationExecutionReadiness).toHaveBeenCalledTimes(2);
  });

  it("keeps the previous Technical Setup route as an Integrations compatibility alias", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/technical");

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Integrations" })).toBeInTheDocument();
  });

  it("opens Campaigns as a customer-scoped readiness page without tenant code entry", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/campaigns");

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Campaigns" })).toBeInTheDocument();
    expect(screen.getByText(/Check campaign readiness inside this customer profile/i)).toBeInTheDocument();
    expect(screen.getByText("No tenant code entry")).toBeInTheDocument();
    expect(await screen.findByText("Campaigns for this customer")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Create campaign setup" })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/campaigns/new",
    );
    expect(
      screen.getAllByRole("link", { name: "Policy settings" }).some(
        (link) =>
          link.getAttribute("href") ===
          "/admin/referral-saas/account-maintenance/acct-gabs/campaigns/settings",
      ),
    ).toBe(true);
    expect(await screen.findByRole("button", { name: "Summer Referrals" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Partner Pilot" })).toBeInTheDocument();
    expect(
      screen.getAllByRole("link", { name: "Policy settings" }).some(
        (link) =>
          link.getAttribute("href") ===
          "/admin/referral-saas/account-maintenance/acct-gabs/campaigns/settings?campaign=CAMP002",
      ),
    ).toBe(true);
    await waitFor(() => expect(screen.getByLabelText("Selected campaign code")).toHaveValue("CAMP001"));
    expect(await screen.findByText("Campaign posture")).toBeInTheDocument();
    expect(screen.getByText("Ready With Warnings")).toBeInTheDocument();
    expect(screen.getByText("Reporting Baseline Pending")).toBeInTheDocument();
    expect(screen.getByText("Reporting setup can follow after campaign checks.")).toBeInTheDocument();
    expect(screen.getByText(/No campaign is created, no policy is changed, no links are generated/i)).toBeInTheDocument();
    expect(screen.queryByText("Campaign Target")).not.toBeInTheDocument();
    expect(mockedGetReferralSaasAccountCampaignReadiness).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      campaignCode: "CAMP001",
      refType: "external_tenant_ref",
      externalRef: "gabs-platform",
      operation: "CONTROL_PLANE_VIEW",
      context: "setup",
      opportunityId: "",
      includeEvidence: true,
    });
    expect(mockedListReferralSaasAccountCampaigns).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      refType: "external_tenant_ref",
      externalRef: "gabs-platform",
      context: "setup",
      limit: 50,
    });
    expect(JSON.stringify(mockedGetReferralSaasAccountCampaignReadiness.mock.calls)).not.toMatch(
      /tenantCode|tenant_code|activateCampaign|money/i,
    );
  });

  it("saves a selected-customer campaign setup draft from its own page", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/campaigns/new");

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Create campaign setup" })).toBeInTheDocument();
    expect(screen.getByText(/Save an inactive campaign setup draft for this customer/i)).toBeInTheDocument();
    expect(screen.getByText("No tenant code entry")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Campaign name"), {
      target: { value: "Spring referral pilot" },
    });
    fireEvent.change(screen.getByLabelText("Audience or segment"), {
      target: { value: "Retail banking customers" },
    });
    fireEvent.change(screen.getByLabelText("Maximum referrals"), {
      target: { value: "100" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save campaign setup" }));

    await waitFor(() => expect(mockedCreateReferralSaasAccountCampaignSetup).toHaveBeenCalledTimes(1));
    expect(mockedCreateReferralSaasAccountCampaignSetup.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      campaign: {
        name: "Spring referral pilot",
        segment: "Retail banking customers",
        startsAt: null,
        endsAt: null,
        maxUses: 100,
      },
      setupIntent: {
        reason: "CUSTOMER_PROFILE_CAMPAIGN_SETUP",
      },
      correlationId: "customer-profile-campaign-create-acct-gabs",
      idempotencyKey: "customer-profile-campaign-create-acct-gabs-spring-referral-pilot-retail-banking-customers",
    });
    expect(await screen.findByText("Campaign setup saved.")).toBeInTheDocument();
    expect(screen.getByText(/inactive draft/i)).toBeInTheDocument();
    expect(screen.getByText("Complete policy and attribution settings")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Complete policy settings" })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/campaigns/settings?campaign=BW-REFERRAL-SPRING-1234",
    );
    expect(JSON.stringify(mockedCreateReferralSaasAccountCampaignSetup.mock.calls)).not.toMatch(
      /tenantCode|tenant_code|isActive|activateCampaign|policyWrite|linkGeneration|money/i,
    );
  });

  it("saves selected-customer campaign policy settings from its own page", async () => {
    renderWorkspace(
      <ReferralSaasAccountMaintenancePage />,
      "/admin/referral-saas/account-maintenance/acct-gabs/campaigns/settings?campaign=CAMP002",
    );

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Campaign policy settings" })).toBeInTheDocument();
    expect(screen.getByText(/Configure attribution, eligibility, product windows/i)).toBeInTheDocument();
    expect(screen.getByText("No tenant code entry")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText("Campaign")).toHaveValue("CAMP002"));

    fireEvent.change(screen.getByLabelText("Policy version"), {
      target: { value: "2" },
    });
    fireEvent.change(screen.getByLabelText("Attribution window"), {
      target: { value: "45" },
    });
    fireEvent.change(screen.getByLabelText("Eligibility rule"), {
      target: { value: "PRODUCT_HOLDING_REQUIRED" },
    });
    fireEvent.change(screen.getByLabelText("Product window"), {
      target: { value: "60" },
    });
    fireEvent.change(screen.getByLabelText("Accepted terms required"), {
      target: { value: "true" },
    });
    fireEvent.change(screen.getByLabelText("Reward visibility notes"), {
      target: { value: "Show estimated reward only after attribution." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save policy settings" }));

    await waitFor(() => expect(mockedUpdateReferralSaasAccountCampaignPolicySettings).toHaveBeenCalledTimes(1));
    expect(mockedUpdateReferralSaasAccountCampaignPolicySettings.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      campaignCode: "CAMP002",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      policySettings: {
        version: 2,
        attributionWindowDays: 45,
        eligibilityRules: [{ rule: "PRODUCT_HOLDING_REQUIRED", enabled: true }],
        productWindows: { default: { days: 60 } },
        productRules: { default: { requiresAcceptedTerms: true } },
        rewardVisibility: {
          mode: "configured_without_payment",
          notes: "Show estimated reward only after attribution.",
        },
      },
      setupIntent: {
        requestedStatus: "POLICY_SETTINGS_RECORDED",
        reason: "CUSTOMER_PROFILE_CAMPAIGN_POLICY_SETTINGS",
      },
      reasonCode: "CUSTOMER_PROFILE_CAMPAIGN_POLICY_SETTINGS",
      correlationId: "customer-profile-campaign-policy-acct-gabs",
      idempotencyKey: "customer-profile-campaign-policy-acct-gabs-camp002-2-45",
    });
    expect(await screen.findByText("Policy settings saved.")).toBeInTheDocument();
    expect(screen.getByText(/No links were generated, no campaign was activated/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Submit for review" })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/campaigns/review?campaign=CAMP002",
    );
    expect(JSON.stringify(mockedUpdateReferralSaasAccountCampaignPolicySettings.mock.calls)).not.toMatch(
      /tenantCode|tenant_code|isActive|activate|linkGeneration|webhook|wallet|settlement|money/i,
    );
  });

  it("submits selected-customer campaign review from its own page", async () => {
    renderWorkspace(
      <ReferralSaasAccountMaintenancePage />,
      "/admin/referral-saas/account-maintenance/acct-gabs/campaigns/review?campaign=CAMP002",
    );

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Campaign review" })).toBeInTheDocument();
    expect(screen.getByText(/Approval only makes future activation eligible/i)).toBeInTheDocument();
    expect(screen.getByText("No tenant code entry")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText("Campaign")).toHaveValue("CAMP002"));

    fireEvent.change(screen.getByLabelText("Review summary"), {
      target: { value: "Campaign setup and policy settings are ready." },
    });
    fireEvent.change(screen.getByLabelText("Operator notes"), {
      target: { value: "Policy reviewed." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Submit campaign for review" }));

    await waitFor(() => expect(mockedSubmitReferralSaasAccountCampaignReview).toHaveBeenCalledTimes(1));
    expect(mockedSubmitReferralSaasAccountCampaignReview.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      campaignCode: "CAMP002",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      reviewSubmission: {
        setupSummary: "Campaign setup and policy settings are ready.",
        requestedReviewStatus: "READY_FOR_REVIEW",
        operatorNotes: "Policy reviewed.",
      },
      reasonCode: "CUSTOMER_PROFILE_CAMPAIGN_REVIEW_SUBMISSION",
      correlationId: "customer-profile-campaign-review-submit-acct-gabs",
      idempotencyKey: "customer-profile-campaign-review-submit-acct-gabs-camp002",
    });
    expect(await screen.findByText("Campaign review recorded.")).toBeInTheDocument();
    expect(screen.getAllByText("Record review decision").length).toBeGreaterThan(0);
    expect(screen.getByText(/Approval does not activate the campaign/i)).toBeInTheDocument();
    expect(JSON.stringify(mockedSubmitReferralSaasAccountCampaignReview.mock.calls)).not.toMatch(
      /tenantCode|tenant_code|isActive|activate|linkGeneration|webhook|seat|authClaim|wallet|settlement|money/i,
    );
  });

  it("records selected-customer campaign review decision without activation", async () => {
    renderWorkspace(
      <ReferralSaasAccountMaintenancePage />,
      "/admin/referral-saas/account-maintenance/acct-gabs/campaigns/review?campaign=CAMP002",
    );

    expect(await screen.findByRole("heading", { name: "Campaign review" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText("Campaign")).toHaveValue("CAMP002"));

    fireEvent.change(screen.getByLabelText("Review decision"), {
      target: { value: "APPROVED" },
    });
    fireEvent.change(screen.getByLabelText("Reviewer reference"), {
      target: { value: "operator-1" },
    });
    fireEvent.change(screen.getByLabelText("Decision reason"), {
      target: { value: "Reviewed and approved." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Record review decision" }));

    await waitFor(() => expect(mockedRecordReferralSaasAccountCampaignReviewDecision).toHaveBeenCalledTimes(1));
    expect(mockedRecordReferralSaasAccountCampaignReviewDecision.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      campaignCode: "CAMP002",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      reviewDecision: {
        decision: "APPROVED",
        reason: "Reviewed and approved.",
        reviewerRef: "operator-1",
      },
      reasonCode: "CUSTOMER_PROFILE_CAMPAIGN_REVIEW_DECISION",
      correlationId: "customer-profile-campaign-review-decision-acct-gabs",
      idempotencyKey: "customer-profile-campaign-review-decision-acct-gabs-camp002-approved",
    });
    expect(await screen.findByText("Campaign review recorded.")).toBeInTheDocument();
    expect(screen.getAllByText("Prepare activation request").length).toBeGreaterThan(0);
    expect(screen.getByText(/Approval does not activate the campaign/i)).toBeInTheDocument();
    expect(JSON.stringify(mockedRecordReferralSaasAccountCampaignReviewDecision.mock.calls)).not.toMatch(
      /tenantCode|tenant_code|isActive|activate|linkGeneration|webhook|seat|authClaim|wallet|settlement|money/i,
    );
  });

  it("keeps selected-customer campaign activation disabled until review approval", async () => {
    mockedRecordReferralSaasAccountCampaignReviewDecision.mockResolvedValue(mockCampaignReview("REVIEW_BLOCKED"));
    renderWorkspace(
      <ReferralSaasAccountMaintenancePage />,
      "/admin/referral-saas/account-maintenance/acct-gabs/campaigns/review?campaign=CAMP002",
    );

    expect(await screen.findByRole("heading", { name: "Campaign review" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText("Campaign")).toHaveValue("CAMP002"));

    fireEvent.change(screen.getByLabelText("Review decision"), {
      target: { value: "BLOCKED" },
    });
    fireEvent.change(screen.getByLabelText("Reviewer reference"), {
      target: { value: "operator-1" },
    });
    fireEvent.change(screen.getByLabelText("Decision reason"), {
      target: { value: "Policy needs more work." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Record review decision" }));

    expect(await screen.findByText("Campaign review recorded.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Activate campaign" })).toBeDisabled();
    expect(screen.getByText(/Approve the campaign review before requesting activation/i)).toBeInTheDocument();
    expect(mockedRequestReferralSaasAccountCampaignActivation).not.toHaveBeenCalled();
  });

  it("requests selected-customer campaign activation after review approval", async () => {
    renderWorkspace(
      <ReferralSaasAccountMaintenancePage />,
      "/admin/referral-saas/account-maintenance/acct-gabs/campaigns/review?campaign=CAMP002",
    );

    expect(await screen.findByRole("heading", { name: "Campaign review" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText("Campaign")).toHaveValue("CAMP002"));

    fireEvent.change(screen.getByLabelText("Review decision"), {
      target: { value: "APPROVED" },
    });
    fireEvent.change(screen.getByLabelText("Reviewer reference"), {
      target: { value: "operator-1" },
    });
    fireEvent.change(screen.getByLabelText("Decision reason"), {
      target: { value: "Reviewed and approved." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Record review decision" }));

    const activationButton = await screen.findByRole("button", { name: "Activate campaign" });
    expect(activationButton).toBeEnabled();
    expect(screen.getByText(/does not create links, validation tracks, webhooks, credentials, access, billing, or money movement/i)).toBeInTheDocument();
    fireEvent.click(activationButton);

    await waitFor(() => expect(mockedRequestReferralSaasAccountCampaignActivation).toHaveBeenCalledTimes(1));
    expect(mockedRequestReferralSaasAccountCampaignActivation.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      campaignCode: "CAMP002",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      activationRequest: {
        requestedLifecycleStatus: "ACTIVE",
        reviewStatus: "REVIEW_APPROVED",
        goLiveReason: "Campaign review approved inside selected customer campaign module.",
        operatorNotes: "Activation request is customer scoped and leaves adjacent workflows separate.",
      },
      reasonCode: "CUSTOMER_PROFILE_CAMPAIGN_ACTIVATION_REQUEST",
      correlationId: "customer-profile-campaign-activation-acct-gabs",
      idempotencyKey: "customer-profile-campaign-activation-acct-gabs-camp002",
    });
    expect(await screen.findByText("Campaign activated.")).toBeInTheDocument();
    expect(screen.getByText(/continue with customer-scoped links, readiness monitoring, attribution, progress, and reports/i)).toBeInTheDocument();
    expect(JSON.stringify(mockedRequestReferralSaasAccountCampaignActivation.mock.calls)).not.toMatch(
      /tenantCode|tenant_code|linkGeneration|webhookDelivery|credential|billing|wallet|settlement|moneyMovement/i,
    );
  });

  it("issues and validates links inside the selected customer campaign context", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/links");

    expect(await screen.findByRole("heading", { name: "Links and codes" })).toBeInTheDocument();
    expect(screen.getByText(/without entering tenant code/i)).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Summer Referrals" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Partner Pilot" })).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Referrer customer reference"), {
      target: { value: "5555555555" },
    });
    fireEvent.change(screen.getByLabelText("Channel or placement"), {
      target: { value: "qr001" },
    });
    fireEvent.change(screen.getByLabelText("Preferred public handle"), {
      target: { value: "gabs-owner" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Issue or reuse code" }));

    await waitFor(() => expect(mockedIssueReferralSaasAccountCampaignCode).toHaveBeenCalledTimes(1));
    expect(mockedIssueReferralSaasAccountCampaignCode.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      campaignCode: "CAMP001",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      referrerUcn: "5555555555",
      sticker: "QR001",
      segment: "REFERRAL",
      preferredHandle: "gabs-owner",
      acceptedTerms: true,
    });

    expect(await screen.findByDisplayValue("REF123")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Customer alias"), {
      target: { value: "gabs-customer" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Validate code" }));

    await waitFor(() => expect(mockedValidateReferralSaasAccountCampaignCode).toHaveBeenCalledTimes(1));
    expect(mockedValidateReferralSaasAccountCampaignCode.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      campaignCode: "CAMP001",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      referralCode: "REF123",
      acceptedTerms: true,
      alias: "gabs-customer",
    });
    expect(await screen.findByText("Validation checked.")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Open current links and codes workspace/i })).not.toBeInTheDocument();
    expect(JSON.stringify(mockedIssueReferralSaasAccountCampaignCode.mock.calls)).not.toMatch(
      /tenantCode|tenant_code|campaignActivation|webhook|billing|wallet|settlement|money/i,
    );
  });

  it("opens customer-scoped reports without leaving the selected customer", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/reports");

    expect(await screen.findByRole("heading", { name: "Reports" })).toBeInTheDocument();
    expect(screen.getByText(/without entering tenant code/i)).toBeInTheDocument();
    expect((await screen.findAllByText("Campaign performance")).length).toBeGreaterThan(0);
    expect(screen.getByText("No tenant code entry")).toBeInTheDocument();

    await waitFor(() => expect(mockedGetReferralSaasAccountReport).toHaveBeenCalledTimes(1));
    expect(mockedGetReferralSaasAccountReport.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      reportType: "campaign_performance",
      filters: undefined,
    });

    fireEvent.change(screen.getByLabelText("Campaign filter"), {
      target: { value: "CAMP001" },
    });
    await waitFor(() =>
      expect(mockedGetReferralSaasAccountReport).toHaveBeenLastCalledWith({
        accountRef: "acct-gabs",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: "gabs-platform",
          context: "setup",
        },
        reportType: "campaign_performance",
        filters: { campaign_code: "CAMP001" },
      }),
    );

    fireEvent.click(screen.getByRole("button", { name: /Preview CSV/i }));
    await waitFor(() => expect(mockedPreviewReferralSaasAccountReportExport).toHaveBeenCalledTimes(1));
    expect(mockedPreviewReferralSaasAccountReportExport.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      reportType: "campaign_performance",
      format: "csv",
      redactionProfile: "tenant_safe",
      filters: { campaign_code: "CAMP001" },
      rowLimit: 100,
    });
    expect(screen.queryByText("Reports Target")).not.toBeInTheDocument();
    expect(JSON.stringify(mockedGetReferralSaasAccountReport.mock.calls)).not.toMatch(/tenantCode|tenant_code/i);
  });

  it("saves selected customer profile settings through the maintenance command", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/settings");

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Customer settings" })).toBeInTheDocument();
    expect(screen.getByText(/Changing them is reference rotation, not profile maintenance/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Customer name"), {
      target: { value: "Gaborone Partners Updated" },
    });
    fireEvent.change(screen.getByLabelText("Customer type"), {
      target: { value: "ENTERPRISE_CUSTOMER" },
    });
    fireEvent.change(screen.getByLabelText("Industry"), {
      target: { value: "AUTOMOTIVE" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save customer profile" }));

    await waitFor(() => expect(mockedUpdateReferralSaasAccountProfile).toHaveBeenCalledTimes(1));
    expect(mockedUpdateReferralSaasAccountProfile.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      profile: {
        accountName: "Gaborone Partners Updated",
        accountType: "ORGANISATION",
        operatingJurisdictionCode: "BW",
        customerType: "ENTERPRISE_CUSTOMER",
        industry: "AUTOMOTIVE",
      },
      correlationId: "customer-profile-settings-acct-gabs",
      idempotencyKey: "customer-profile-settings-acct-gabs-gaborone-partners-updated-bw-enterprise-customer-automotive",
    });
    expect(await screen.findByText("Customer profile saved.")).toBeInTheDocument();
    expect(screen.getByText(/Customer identifiers stayed unchanged/i)).toBeInTheDocument();
    expect(JSON.stringify(mockedUpdateReferralSaasAccountProfile.mock.calls)).not.toMatch(
      /externalTenantRef|organisationRef|tenantCode|activate|money/i,
    );
  });

  it("keeps customer functions scoped to the selected customer context", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />);

    fireEvent.click(await screen.findByRole("button", { name: /FNB Referral SaaS/ }));
    fireEvent.click(screen.getByRole("link", { name: "Open customer profile" }));
    expect(await screen.findByRole("heading", { name: "What you can do for this customer" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Customer settings/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-fnb/settings",
    );
    expect(
      screen
        .getAllByRole("link", { name: /People and access/ })
        .some((link) => link.getAttribute("href") === "/admin/referral-saas/account-maintenance/acct-fnb/people"),
    ).toBe(true);
    expect(screen.queryByRole("link", { name: /^Account setup$/ })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Links and codes/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-fnb/links",
    );
    expect(screen.getByRole("link", { name: /Reports/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-fnb/reports",
    );
    expect(screen.getByRole("link", { name: /Integrations/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-fnb/integrations",
    );
    expect(
      screen
        .getAllByRole("link", { name: /Campaigns/ })
        .some((link) => link.getAttribute("href") === "/admin/referral-saas/account-maintenance/acct-fnb/campaigns"),
    ).toBe(true);
    expect(screen.getByRole("link", { name: /Attribution/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-fnb/attribution",
    );
    expect(screen.getByText(/Those live on their own customer routes so the home stays short/i)).toBeInTheDocument();
  });

  it("keeps manual lookup local until the tester checks the customer", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />);

    await screen.findByRole("heading", { name: "1. Where do you operate?" });
    await waitFor(() => expect(mockedGetAdminOnboardingState).toHaveBeenCalledTimes(1));

    fireEvent.click(screen.getByText("Manual customer lookup"));
    fireEvent.change(screen.getByLabelText("Customer reference"), {
      target: { value: "fnb-referral-account" },
    });
    fireEvent.change(screen.getByLabelText("Organisation reference"), {
      target: { value: "fnb-demo-org" },
    });

    expect(screen.getByText("Changes not checked")).toBeInTheDocument();
    expect(mockedGetAdminOnboardingState).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "Check customer" }));

    await waitFor(() =>
      expect(mockedGetAdminOnboardingState).toHaveBeenLastCalledWith({
        external_tenant_ref: "fnb-referral-account",
        organisation_ref: "fnb-demo-org",
      }),
    );
    expect(JSON.stringify(mockedGetAdminOnboardingState.mock.calls)).not.toMatch(
      /account_ref|tenant_code|api_key|client_secret/i,
    );
  });

  it("retains setup drafts as fallback evidence, not the primary workspace", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />);

    expect(await screen.findByRole("heading", { name: "Setup draft fallback" })).toBeInTheDocument();
    expect(screen.getByText("Use this only when saved setup evidence exists but the customer has not become a durable customer profile yet.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /demo-organisation/ })).toBeInTheDocument();
    expect(mockedGetAdminOnboardingDrafts).toHaveBeenCalledWith({
      external_tenant_ref: "demo-platform-operator",
      organisation_ref: "demo-organisation",
      limit: 10,
    });
  });
});
