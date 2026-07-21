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
  getReferralSaasAccountMembershipPosture,
  getReferralSaasMembershipActivationReadiness,
  getReferralSaasTechnicalSetupReadiness,
  listReferralSaasAccounts,
  recordReferralSaasMembershipInvitationIntent,
  updateReferralSaasAccountProfile,
  type ReferralSaasAccountMembershipPostureResponse,
  type ReferralSaasAccountRegistryResponse,
  type ReferralSaasMembershipActivationReadinessResponse,
  type ReferralSaasTechnicalSetupReadinessResponse,
} from "../../api/endpoints/referralSaasAccounts";
import { ReferralSaasAccountMaintenancePage } from "./ReferralSaasAccountMaintenancePage";

vi.mock("../../api/endpoints/adminOnboarding", () => ({
  getAdminOnboardingDrafts: vi.fn(),
  getAdminOnboardingState: vi.fn(),
}));
vi.mock("../../api/endpoints/referralSaasAccounts", () => ({
  getReferralSaasAccountMembershipPosture: vi.fn(),
  getReferralSaasMembershipActivationReadiness: vi.fn(),
  getReferralSaasTechnicalSetupReadiness: vi.fn(),
  listReferralSaasAccounts: vi.fn(),
  recordReferralSaasMembershipInvitationIntent: vi.fn(),
  updateReferralSaasAccountProfile: vi.fn(),
}));

const mockedGetAdminOnboardingDrafts = vi.mocked(getAdminOnboardingDrafts);
const mockedGetAdminOnboardingState = vi.mocked(getAdminOnboardingState);
const mockedGetReferralSaasAccountMembershipPosture = vi.mocked(getReferralSaasAccountMembershipPosture);
const mockedGetReferralSaasMembershipActivationReadiness = vi.mocked(getReferralSaasMembershipActivationReadiness);
const mockedGetReferralSaasTechnicalSetupReadiness = vi.mocked(getReferralSaasTechnicalSetupReadiness);
const mockedListReferralSaasAccounts = vi.mocked(listReferralSaasAccounts);
const mockedRecordReferralSaasMembershipInvitationIntent = vi.mocked(recordReferralSaasMembershipInvitationIntent);
const mockedUpdateReferralSaasAccountProfile = vi.mocked(updateReferralSaasAccountProfile);

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
          actorType: "USER",
          subject: "owner@gabs.example",
          displayName: "Gaborone owner",
          roleFamily: "DISTRIBUTION_ADMIN",
          permissionSet: "REFERRAL_SAAS_ACCOUNT_ADMIN",
          status: "INVITED",
          deliveryStatus: "DELIVERY_NOT_CONFIGURED",
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
          subject: "owner@gabs.example",
          displayName: "Gaborone owner",
          roleFamily: "DISTRIBUTION_ADMIN",
          membershipStatus: "INVITED",
          deliveryStatus: "DELIVERY_NOT_CONFIGURED",
          deliveryReadiness: "BLOCKED",
          activationReadiness: "BLOCKED",
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
          nextAction: "Configure the Email provider before sending account access invites.",
        },
        {
          code: "REFERRAL_JOURNEY_MESSAGES",
          label: "Referral journey messages",
          status: "READY",
          requiredChannels: ["WHATSAPP", "SMS", "USSD"],
          readyChannels: ["WHATSAPP"],
          missingChannels: [],
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

describe("ReferralSaasAccountMaintenancePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedGetAdminOnboardingDrafts.mockResolvedValue(mockDraftSelector());
    mockedGetAdminOnboardingState.mockResolvedValue(mockMaintenanceState());
    mockedGetReferralSaasAccountMembershipPosture.mockResolvedValue(mockMembershipPosture());
    mockedGetReferralSaasMembershipActivationReadiness.mockResolvedValue(mockMembershipActivationReadiness());
    mockedGetReferralSaasTechnicalSetupReadiness.mockResolvedValue(mockTechnicalSetupReadiness());
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
    expect(screen.getByText("Only accounts in South Africa.")).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: /FNB Referral SaaS/ })).toBeInTheDocument();
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
    expect(screen.getByText("Only accounts in Botswana.")).toBeInTheDocument();
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
    expect(screen.getByText("This is the customer home. Campaigns, links, reports, attribution, and support stay inside this customer context.")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Health at a glance" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Do this next" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Add who can manage this account/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/people",
    );
    expect(screen.getByRole("link", { name: /Check technical setup/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/technical",
    );
    expect(screen.queryByRole("heading", { name: "People and access" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Open Campaigns/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/campaigns",
    );
    expect(await screen.findByText("Everything opens against Gaborone Partners until you switch customer.")).toBeInTheDocument();
    expect(screen.getByText(/Not on this page: customer settings form, people invite form, or full health table/i)).toBeInTheDocument();
  });

  it("opens People and Access as its own customer page from the next-best action", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs");

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("link", { name: /Add who can manage this account/ }));

    expect(await screen.findByRole("heading", { name: "People and access" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Customer home" })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs",
    );
    expect(screen.queryByRole("heading", { name: "Health at a glance" })).not.toBeInTheDocument();
  });

  it("records customer-scoped people access intent without leaving Customer Profile", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/people");

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "People and access" })).toBeInTheDocument();
    expect(screen.getByText(/It does not send an email, activate login, assign a seat, or change auth permissions/i)).toBeInTheDocument();
    expect(screen.getByText(/Used as the access identity for this customer/i)).toBeInTheDocument();
    expect(await screen.findByText("Access activation readiness")).toBeInTheDocument();
    expect(screen.getByText(/responsibility still needs to be named for this customer/i)).toBeInTheDocument();
    expect(screen.getByText("Ready to invite")).toBeInTheDocument();
    expect(screen.getByText("Ready to activate")).toBeInTheDocument();
    expect(screen.getAllByText(/Campaign Manager/i).length).toBeGreaterThan(0);
    expect(screen.getByText("Configure an approved invitation delivery provider before sending invites.")).toBeInTheDocument();
    expect(screen.getAllByText("Gaborone owner").length).toBeGreaterThan(0);
    expect(screen.getAllByText("owner@gabs.example").length).toBeGreaterThan(0);
    expect(mockedGetReferralSaasMembershipActivationReadiness).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      refType: "external_tenant_ref",
      externalRef: "gabs-platform",
      context: "setup",
    });

    fireEvent.change(screen.getByLabelText("Person name"), {
      target: { value: "Gaborone campaign owner" },
    });
    fireEvent.change(screen.getByLabelText(/Work email/), {
      target: { value: "Gabs.Campaign.Owner@Example.COM" },
    });
    fireEvent.change(screen.getByLabelText("Access responsibility"), {
      target: { value: "Campaign manager" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Record access intent" }));

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
        displayName: "Gaborone campaign owner",
      },
      membership: {
        roleFamily: "CAMPAIGN_MANAGER",
        permissionSet: "REFERRAL_SAAS_CAMPAIGN_MANAGER",
        tenantScope: "PRIMARY_ACCOUNT_TENANT",
      },
      reasonCode: "CUSTOMER_PROFILE_ACCESS_MAINTENANCE",
      correlationId: "customer-profile-access-acct-gabs",
      idempotencyKey: "customer-profile-access-acct-gabs-gabs-campaign-owner-example-com-campaign-manager",
    });
    expect(await screen.findByText("Access intent saved.")).toBeInTheDocument();
    expect(screen.getByText(/No invitation email, login activation, seat assignment, or auth claim change was performed/i)).toBeInTheDocument();
    expect(mockedGetReferralSaasMembershipActivationReadiness).toHaveBeenCalledTimes(2);
  });

  it("opens Technical Setup as its own read-only customer page", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/technical");

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Technical setup" })).toBeInTheDocument();
    expect(screen.getByText(/Check provider readiness for invites and referral messages/i)).toBeInTheDocument();
    expect(await screen.findByText("Ready providers")).toBeInTheDocument();
    expect(screen.getByText("Need setup")).toBeInTheDocument();
    expect(screen.getByText("Supported channels")).toBeInTheDocument();
    expect(screen.getByText("People invite delivery")).toBeInTheDocument();
    expect(screen.getByText("Configure the Email provider before sending account access invites.")).toBeInTheDocument();
    expect(screen.getByText("Referral journey messages")).toBeInTheDocument();
    expect(screen.getByText(/No credentials are created, no webhook is dispatched, no invite is sent/i)).toBeInTheDocument();
    expect(mockedGetReferralSaasTechnicalSetupReadiness).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      refType: "external_tenant_ref",
      externalRef: "gabs-platform",
      context: "setup",
    });
    expect(screen.queryByRole("heading", { name: "Health at a glance" })).not.toBeInTheDocument();
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
    expect(screen.getByRole("link", { name: /Technical setup/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-fnb/technical",
    );
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
