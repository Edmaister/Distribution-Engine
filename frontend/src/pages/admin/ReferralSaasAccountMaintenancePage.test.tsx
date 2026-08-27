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
  createReferralSaasAccountReportDeliverySchedule,
  createReferralSaasAccountReportExportFile,
  createReferralSaasAccountReportExportRequest,
  downloadReferralSaasAccountReportExportFile,
  getReferralSaasAccountReportDeliveryScheduleReadiness,
  getReferralSaasAccountReport,
  listReferralSaasAccountReportDeliverySchedules,
  previewReferralSaasAccountReportExport,
  updateReferralSaasAccountReportDeliverySchedule,
} from "../../api/endpoints/referralSaasReports";
import {
  addReferralSaasAccountSupportCaseNote,
  changeReferralSaasAccountSupportCaseStatus,
  createReferralSaasAccountSupportCase,
  createReferralSaasAccountCampaignSetup,
  bindReferralSaasAccountCampaignJourneyVersion,
  createReferralSaasProgrammeDraft,
  decideReferralSaasProgrammeDraftReview,
  getReferralSaasAccountProgrammeAnalytics,
  getReferralSaasAccountProgrammeCatalogue,
  getReferralSaasCustomerProductCatalogue,
  getReferralSaasAccountCampaignReadiness,
  getReferralSaasAccountSupportCaseRepairReplayReadiness,
  getReferralSaasAccountMembershipPosture,
  getReferralSaasIntegrationConfiguration,
  getReferralSaasIntegrationExecutionReadiness,
  getReferralSaasProviderVaultReadiness,
  getReferralSaasLoginCompletionReadiness,
  getReferralSaasMembershipActivationReadiness,
  getReferralSaasTechnicalSetupReadiness,
  listReferralSaasAccountJourneyDrafts,
  listReferralSaasAccountJourneyVersions,
  listReferralSaasAccountProgrammes,
  listReferralSaasIntegrationCredentialRequests,
  listReferralSaasAccountSupportCases,
  listReferralSaasAccountCampaigns,
  listReferralSaasAccounts,
  listReferralSaasJourneyTemplates,
  publishReferralSaasAccountJourneyDraft,
  publishReferralSaasProgrammeDraft,
  recordReferralSaasAccountCampaignReviewDecision,
  recordReferralSaasApiAccessVerification,
  recordReferralSaasIntegrationCredentialRequest,
  recordReferralSaasIntegrationCredentialExecutionCheck,
  recordReferralSaasIntegrationCredentialReviewDecision,
  recordReferralSaasMessageProviderTest,
  recordReferralSaasWebhookTestDispatch,
  recordReferralSaasMembershipInvitationIntent,
  requestReferralSaasAccountCampaignActivation,
  requestReferralSaasAccountFoundationActivation,
  requestReferralSaasAccessProvisioning,
  requestReferralSaasLoginCompletionIntent,
  requestReferralSaasMembershipActivation,
  requestReferralSaasMembershipInvitationDelivery,
  saveReferralSaasAccountJourneyDraft,
  saveReferralSaasCustomerProductLine,
  saveReferralSaasCustomerProductOffering,
  saveReferralSaasIntegrationConfiguration,
  submitReferralSaasProgrammeDraftReview,
  submitReferralSaasAccountCampaignReview,
  cancelReferralSaasMembershipInvitationIntent,
  updateReferralSaasMembershipInvitationIntent,
  updateReferralSaasAccountCampaignPolicySettings,
  updateReferralSaasAccountProfile,
  updateReferralSaasProgrammeDraft,
  validateReferralSaasAccountJourneyDraft,
  validateReferralSaasProgrammeDraft,
  validateReferralSaasIntegrationConfiguration,
  type ReferralSaasAccountCampaignReviewResponse,
  type ReferralSaasAccountCampaignActivationResponse,
  type ReferralSaasAccountCampaignPolicySettingsResponse,
  type ReferralSaasAccountMembershipPostureResponse,
  type ReferralSaasAccountCampaignListResponse,
  type ReferralSaasAccountRegistryResponse,
  type ReferralSaasAccountCampaignReadinessResponse,
  type ReferralSaasMembershipActivationReadinessResponse,
  type ReferralSaasLoginCompletionReadinessResponse,
  type ReferralSaasIntegrationExecutionReadinessResponse,
  type ReferralSaasIntegrationCredentialRequestListResponse,
  type ReferralSaasProviderVaultReadinessResponse,
  type ReferralSaasTechnicalSetupReadinessResponse,
  type ReferralSaasCustomerJourneyDraftCommandResponse,
  type ReferralSaasCustomerJourneyDraftListResponse,
  type ReferralSaasCustomerJourneyDraftValidationResponse,
  type ReferralSaasCustomerJourneyPublishResponse,
  type ReferralSaasCustomerJourneyVersionListResponse,
  type ReferralSaasJourneyTemplateCatalogueResponse,
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
  createReferralSaasAccountReportDeliverySchedule: vi.fn(),
  createReferralSaasAccountReportExportFile: vi.fn(),
  createReferralSaasAccountReportExportRequest: vi.fn(),
  deleteReferralSaasAccountReportExportFile: vi.fn(),
  downloadReferralSaasAccountReportExportFile: vi.fn(),
  getReferralSaasAccountReportDeliveryScheduleReadiness: vi.fn(),
  getReferralSaasAccountReport: vi.fn(),
  listReferralSaasAccountReportDeliverySchedules: vi.fn(),
  previewReferralSaasAccountReportExport: vi.fn(),
  updateReferralSaasAccountReportDeliverySchedule: vi.fn(),
}));
vi.mock("../../api/endpoints/referralSaasAccounts", () => ({
  addReferralSaasAccountSupportCaseNote: vi.fn(),
  assignReferralSaasAccountSupportCase: vi.fn(),
  bindReferralSaasAccountCampaignJourneyVersion: vi.fn(),
  changeReferralSaasAccountSupportCaseStatus: vi.fn(),
  createReferralSaasAccountSupportCase: vi.fn(),
  createReferralSaasAccountCampaignSetup: vi.fn(),
  getReferralSaasAccountCampaignReadiness: vi.fn(),
  createReferralSaasProgrammeDraft: vi.fn(),
  decideReferralSaasProgrammeDraftReview: vi.fn(),
  getReferralSaasAccountProgrammeAnalytics: vi.fn(),
  getReferralSaasAccountProgrammeCatalogue: vi.fn(),
  getReferralSaasCustomerProductCatalogue: vi.fn(),
  getReferralSaasAccountSupportCaseRepairReplayReadiness: vi.fn(),
  getReferralSaasAccountMembershipPosture: vi.fn(),
  getReferralSaasIntegrationConfiguration: vi.fn(),
  getReferralSaasIntegrationExecutionReadiness: vi.fn(),
  getReferralSaasProviderVaultReadiness: vi.fn(),
  getReferralSaasLoginCompletionReadiness: vi.fn(),
  getReferralSaasMembershipActivationReadiness: vi.fn(),
  getReferralSaasTechnicalSetupReadiness: vi.fn(),
  listReferralSaasAccountJourneyDrafts: vi.fn(),
  listReferralSaasAccountJourneyVersions: vi.fn(),
  listReferralSaasAccountProgrammes: vi.fn(),
  listReferralSaasIntegrationCredentialRequests: vi.fn(),
  listReferralSaasAccountSupportCases: vi.fn(),
  listReferralSaasAccountCampaigns: vi.fn(),
  listReferralSaasAccounts: vi.fn(),
  listReferralSaasJourneyTemplates: vi.fn(),
  publishReferralSaasAccountJourneyDraft: vi.fn(),
  publishReferralSaasProgrammeDraft: vi.fn(),
  recordReferralSaasAccountCampaignReviewDecision: vi.fn(),
  recordReferralSaasApiAccessVerification: vi.fn(),
  recordReferralSaasIntegrationCredentialRequest: vi.fn(),
  recordReferralSaasIntegrationCredentialExecutionCheck: vi.fn(),
  recordReferralSaasIntegrationCredentialReviewDecision: vi.fn(),
  recordReferralSaasMessageProviderTest: vi.fn(),
  recordReferralSaasWebhookTestDispatch: vi.fn(),
  recordReferralSaasMembershipInvitationIntent: vi.fn(),
  recordReferralSaasAccountCampaignLifecycleCommand: vi.fn(),
  requestReferralSaasAccountCampaignActivation: vi.fn(),
  requestReferralSaasAccountFoundationActivation: vi.fn(),
  requestReferralSaasAccessProvisioning: vi.fn(),
  requestReferralSaasLoginCompletionIntent: vi.fn(),
  requestReferralSaasMembershipInvitationDelivery: vi.fn(),
  requestReferralSaasMembershipActivation: vi.fn(),
  saveReferralSaasAccountJourneyDraft: vi.fn(),
  saveReferralSaasCustomerProductLine: vi.fn(),
  saveReferralSaasCustomerProductOffering: vi.fn(),
  saveReferralSaasIntegrationConfiguration: vi.fn(),
  submitReferralSaasProgrammeDraftReview: vi.fn(),
  submitReferralSaasAccountCampaignReview: vi.fn(),
  cancelReferralSaasMembershipInvitationIntent: vi.fn(),
  updateReferralSaasMembershipInvitationIntent: vi.fn(),
  updateReferralSaasAccountCampaignPolicySettings: vi.fn(),
  updateReferralSaasAccountProfile: vi.fn(),
  updateReferralSaasProgrammeDraft: vi.fn(),
  validateReferralSaasAccountJourneyDraft: vi.fn(),
  validateReferralSaasProgrammeDraft: vi.fn(),
  validateReferralSaasIntegrationConfiguration: vi.fn(),
}));

const mockedGetAdminOnboardingDrafts = vi.mocked(getAdminOnboardingDrafts);
const mockedGetAdminOnboardingState = vi.mocked(getAdminOnboardingState);
const mockedIssueReferralSaasAccountCampaignCode = vi.mocked(issueReferralSaasAccountCampaignCode);
const mockedValidateReferralSaasAccountCampaignCode = vi.mocked(validateReferralSaasAccountCampaignCode);
const mockedGetReferralSaasAccountReport = vi.mocked(getReferralSaasAccountReport);
const mockedPreviewReferralSaasAccountReportExport = vi.mocked(previewReferralSaasAccountReportExport);
const mockedCreateReferralSaasAccountReportDeliverySchedule = vi.mocked(
  createReferralSaasAccountReportDeliverySchedule,
);
const mockedListReferralSaasAccountReportDeliverySchedules = vi.mocked(
  listReferralSaasAccountReportDeliverySchedules,
);
const mockedUpdateReferralSaasAccountReportDeliverySchedule = vi.mocked(
  updateReferralSaasAccountReportDeliverySchedule,
);
const mockedGetReferralSaasAccountReportDeliveryScheduleReadiness = vi.mocked(
  getReferralSaasAccountReportDeliveryScheduleReadiness,
);
const mockedCreateReferralSaasAccountReportExportRequest = vi.mocked(createReferralSaasAccountReportExportRequest);
const mockedCreateReferralSaasAccountReportExportFile = vi.mocked(createReferralSaasAccountReportExportFile);
const mockedDownloadReferralSaasAccountReportExportFile = vi.mocked(downloadReferralSaasAccountReportExportFile);
const mockedAddReferralSaasAccountSupportCaseNote = vi.mocked(addReferralSaasAccountSupportCaseNote);
const mockedChangeReferralSaasAccountSupportCaseStatus = vi.mocked(changeReferralSaasAccountSupportCaseStatus);
const mockedCreateReferralSaasAccountSupportCase = vi.mocked(createReferralSaasAccountSupportCase);
const mockedCreateReferralSaasAccountCampaignSetup = vi.mocked(createReferralSaasAccountCampaignSetup);
const mockedBindReferralSaasAccountCampaignJourneyVersion = vi.mocked(
  bindReferralSaasAccountCampaignJourneyVersion,
);
const mockedCreateReferralSaasProgrammeDraft = vi.mocked(createReferralSaasProgrammeDraft);
const mockedDecideReferralSaasProgrammeDraftReview = vi.mocked(decideReferralSaasProgrammeDraftReview);
const mockedGetReferralSaasAccountProgrammeAnalytics = vi.mocked(getReferralSaasAccountProgrammeAnalytics);
const mockedGetReferralSaasAccountProgrammeCatalogue = vi.mocked(getReferralSaasAccountProgrammeCatalogue);
const mockedGetReferralSaasCustomerProductCatalogue = vi.mocked(getReferralSaasCustomerProductCatalogue);
const mockedSaveReferralSaasCustomerProductLine = vi.mocked(saveReferralSaasCustomerProductLine);
const mockedSaveReferralSaasCustomerProductOffering = vi.mocked(saveReferralSaasCustomerProductOffering);
const mockedGetReferralSaasAccountCampaignReadiness = vi.mocked(getReferralSaasAccountCampaignReadiness);
const mockedGetReferralSaasAccountSupportCaseRepairReplayReadiness = vi.mocked(
  getReferralSaasAccountSupportCaseRepairReplayReadiness,
);
const mockedGetReferralSaasAccountMembershipPosture = vi.mocked(getReferralSaasAccountMembershipPosture);
const mockedGetReferralSaasIntegrationConfiguration = vi.mocked(getReferralSaasIntegrationConfiguration);
const mockedGetReferralSaasIntegrationExecutionReadiness = vi.mocked(getReferralSaasIntegrationExecutionReadiness);
const mockedGetReferralSaasProviderVaultReadiness = vi.mocked(getReferralSaasProviderVaultReadiness);
const mockedGetReferralSaasLoginCompletionReadiness = vi.mocked(getReferralSaasLoginCompletionReadiness);
const mockedGetReferralSaasMembershipActivationReadiness = vi.mocked(getReferralSaasMembershipActivationReadiness);
const mockedGetReferralSaasTechnicalSetupReadiness = vi.mocked(getReferralSaasTechnicalSetupReadiness);
const mockedListReferralSaasAccountJourneyDrafts = vi.mocked(listReferralSaasAccountJourneyDrafts);
const mockedListReferralSaasAccountJourneyVersions = vi.mocked(listReferralSaasAccountJourneyVersions);
const mockedListReferralSaasAccountProgrammes = vi.mocked(listReferralSaasAccountProgrammes);
const mockedListReferralSaasIntegrationCredentialRequests = vi.mocked(listReferralSaasIntegrationCredentialRequests);
const mockedListReferralSaasAccountSupportCases = vi.mocked(listReferralSaasAccountSupportCases);
const mockedListReferralSaasAccountCampaigns = vi.mocked(listReferralSaasAccountCampaigns);
const mockedListReferralSaasAccounts = vi.mocked(listReferralSaasAccounts);
const mockedListReferralSaasJourneyTemplates = vi.mocked(listReferralSaasJourneyTemplates);
const mockedPublishReferralSaasAccountJourneyDraft = vi.mocked(publishReferralSaasAccountJourneyDraft);
const mockedPublishReferralSaasProgrammeDraft = vi.mocked(publishReferralSaasProgrammeDraft);
const mockedRecordReferralSaasAccountCampaignReviewDecision = vi.mocked(recordReferralSaasAccountCampaignReviewDecision);
const mockedRecordReferralSaasApiAccessVerification = vi.mocked(recordReferralSaasApiAccessVerification);
const mockedRecordReferralSaasIntegrationCredentialRequest = vi.mocked(recordReferralSaasIntegrationCredentialRequest);
const mockedRecordReferralSaasIntegrationCredentialExecutionCheck = vi.mocked(
  recordReferralSaasIntegrationCredentialExecutionCheck,
);
const mockedRecordReferralSaasIntegrationCredentialReviewDecision = vi.mocked(
  recordReferralSaasIntegrationCredentialReviewDecision,
);
const mockedRecordReferralSaasMessageProviderTest = vi.mocked(recordReferralSaasMessageProviderTest);
const mockedRecordReferralSaasWebhookTestDispatch = vi.mocked(recordReferralSaasWebhookTestDispatch);
const mockedRecordReferralSaasMembershipInvitationIntent = vi.mocked(recordReferralSaasMembershipInvitationIntent);
const mockedRequestReferralSaasAccountCampaignActivation = vi.mocked(requestReferralSaasAccountCampaignActivation);
const mockedRequestReferralSaasAccountFoundationActivation = vi.mocked(requestReferralSaasAccountFoundationActivation);
const mockedRequestReferralSaasAccessProvisioning = vi.mocked(requestReferralSaasAccessProvisioning);
const mockedRequestReferralSaasLoginCompletionIntent = vi.mocked(requestReferralSaasLoginCompletionIntent);
const mockedRequestReferralSaasMembershipInvitationDelivery = vi.mocked(requestReferralSaasMembershipInvitationDelivery);
const mockedRequestReferralSaasMembershipActivation = vi.mocked(requestReferralSaasMembershipActivation);
const mockedSaveReferralSaasAccountJourneyDraft = vi.mocked(saveReferralSaasAccountJourneyDraft);
const mockedSaveReferralSaasIntegrationConfiguration = vi.mocked(saveReferralSaasIntegrationConfiguration);
const mockedSubmitReferralSaasProgrammeDraftReview = vi.mocked(submitReferralSaasProgrammeDraftReview);
const mockedSubmitReferralSaasAccountCampaignReview = vi.mocked(submitReferralSaasAccountCampaignReview);
const mockedCancelReferralSaasMembershipInvitationIntent = vi.mocked(cancelReferralSaasMembershipInvitationIntent);
const mockedUpdateReferralSaasMembershipInvitationIntent = vi.mocked(updateReferralSaasMembershipInvitationIntent);
const mockedUpdateReferralSaasAccountCampaignPolicySettings = vi.mocked(updateReferralSaasAccountCampaignPolicySettings);
const mockedUpdateReferralSaasAccountProfile = vi.mocked(updateReferralSaasAccountProfile);
const mockedUpdateReferralSaasProgrammeDraft = vi.mocked(updateReferralSaasProgrammeDraft);
const mockedValidateReferralSaasAccountJourneyDraft = vi.mocked(validateReferralSaasAccountJourneyDraft);
const mockedValidateReferralSaasProgrammeDraft = vi.mocked(validateReferralSaasProgrammeDraft);
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

function mockJourneyTemplateCatalogue(): ReferralSaasJourneyTemplateCatalogueResponse {
  return {
    status: "ok",
    templateCount: 1,
    statusFilter: ["APPROVED"],
    includeArchived: false,
    templates: [
      {
        journeyTemplateId: "tmpl-001",
        templateCode: "REFERRAL_STANDARD",
        templateName: "Standard referral journey",
        templateFamily: "REFERRAL",
        ownerScope: "AMPLIFI",
        status: "APPROVED",
        safeSummary: {
          description: "Referral journey with customer referral, qualification, and conversion milestones.",
        },
        governanceMetadata: {
          approvalStatus: "APPROVED",
        },
        versionCount: 1,
        versions: [
          {
            journeyTemplateVersionId: "tmpl-ver-001",
            templateVersion: "1.0.0",
            status: "APPROVED",
            milestoneCount: 3,
            transitionRuleCount: 2,
            evidenceRequirementCount: 3,
            allowedConfigurationSections: [
              "milestones",
              "transitions",
              "evidence",
              "rewards",
              "attribution",
            ],
            approvedByRef: "amplifi-admin",
            approvedAt: "2026-07-19T00:00:00",
            createdByRef: "amplifi-admin",
            createdAt: "2026-07-19T00:00:00",
            updatedAt: "2026-07-19T00:00:00",
            archivedAt: null,
          },
        ],
        createdByRef: "amplifi-admin",
        updatedByRef: "amplifi-admin",
        createdAt: "2026-07-19T00:00:00",
        updatedAt: "2026-07-19T00:00:00",
        archivedAt: null,
      },
    ],
    guardrails: ["READ_ONLY_TEMPLATE_CATALOGUE", "NO_RUNTIME_EXECUTION"],
    redactions: ["INTERNAL_TENANT_IDENTIFIER"],
    noTenantDataConfirmed: true,
    noCustomerConfigurationWriteConfirmed: true,
    noRuntimeExecutionConfirmed: true,
    noCampaignBindingConfirmed: true,
    noProviderAuthBillingOrMoneyActionConfirmed: true,
  };
}

function mockJourneyDraftList(): ReferralSaasCustomerJourneyDraftListResponse {
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
    count: 0,
    drafts: [],
    guardrail: "Account-scoped journey drafts only.",
    guardrails: ["NO_RUNTIME_JOURNEY_MUTATION", "NO_CAMPAIGN_ACTIVATION"],
    redactions: ["INTERNAL_TENANT_IDENTIFIER"],
    noRuntimeJourneyMutationConfirmed: true,
    noCampaignActivationConfirmed: true,
    noProviderDispatchConfirmed: true,
    noAuthBillingOrMoneyActionConfirmed: true,
  };
}

function mockJourneyDraftCommandResponse(): ReferralSaasCustomerJourneyDraftCommandResponse {
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
    commandStatus: "DRAFT_SAVED",
    idempotencyStatus: "NEW_REQUEST",
    draft: {
      customerJourneyDraftId: "draft-001",
      accountId: "acct-gabs",
      journeyTemplateVersionId: "tmpl-ver-001",
      templateCode: "REFERRAL_STANDARD",
      templateVersion: "1.0.0",
      draftName: "Standard referral journey for Gaborone Partners",
      draftStatus: "DRAFT",
      draftVersion: 1,
      configurationPayload: {
        milestones: [{ code: "REFERRED" }, { code: "QUALIFIED" }, { code: "CONVERTED" }],
      },
      lastValidationStatus: "NOT_VALIDATED",
      payloadHash: "hash-001",
      createdByRef: "amplifi-admin",
      updatedByRef: "amplifi-admin",
      createdAt: "2026-07-19T00:00:00",
      updatedAt: "2026-07-19T00:00:00",
      archivedAt: null,
      guardrails: ["NO_RUNTIME_JOURNEY_MUTATION"],
      redactions: ["INTERNAL_TENANT_IDENTIFIER"],
      noRuntimeJourneyMutationConfirmed: true,
      noCampaignBindingConfirmed: true,
      noCampaignActivationConfirmed: true,
      noProviderDispatchConfirmed: true,
      noAuthBillingOrMoneyActionConfirmed: true,
    },
    guardrail: "Draft only.",
    guardrails: ["NO_RUNTIME_JOURNEY_MUTATION"],
    redactions: ["INTERNAL_TENANT_IDENTIFIER"],
    noRuntimeJourneyMutationConfirmed: true,
    noCampaignBindingConfirmed: true,
    noCampaignActivationConfirmed: true,
    noProviderDispatchConfirmed: true,
    noAuthBillingOrMoneyActionConfirmed: true,
  };
}

function mockJourneyValidationResponse(): ReferralSaasCustomerJourneyDraftValidationResponse {
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
    validation: {
      journeyValidationResultId: "validation-001",
      accountId: "acct-gabs",
      customerJourneyDraftId: "draft-001",
      journeyTemplateVersionId: "tmpl-ver-001",
      validationStatus: "VALIDATION_PASSED",
      blockers: [],
      warnings: [],
      safeSummary: {
        simulation: {
          simulatedMilestonePath: ["REFERRED", "QUALIFIED", "CONVERTED"],
        },
      },
      payloadHash: "hash-001",
      createdAt: "2026-07-19T00:00:00",
      guardrails: ["NO_RUNTIME_JOURNEY_MUTATION"],
      redactions: ["INTERNAL_TENANT_IDENTIFIER"],
      noRuntimeJourneyMutationConfirmed: true,
      noCampaignActivationConfirmed: true,
      noProviderDispatchConfirmed: true,
      noAuthBillingOrMoneyActionConfirmed: true,
    },
    guardrail: "Validation only.",
    guardrails: ["NO_RUNTIME_JOURNEY_MUTATION"],
    redactions: ["INTERNAL_TENANT_IDENTIFIER"],
    noRuntimeJourneyMutationConfirmed: true,
    noCampaignActivationConfirmed: true,
    noProviderDispatchConfirmed: true,
    noAuthBillingOrMoneyActionConfirmed: true,
  };
}

function mockJourneyPublishResponse(): ReferralSaasCustomerJourneyPublishResponse {
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
    commandStatus: "PUBLISHED",
    idempotencyStatus: "NEW_REQUEST",
    version: {
      customerJourneyVersionId: "journey-version-001",
      accountId: "acct-gabs",
      customerJourneyDraftId: "draft-001",
      journeyTemplateVersionId: "tmpl-ver-001",
      templateCode: "REFERRAL_STANDARD",
      templateVersion: "1.0.0",
      customerJourneyCode: "GABS_REFERRAL_STANDARD",
      versionNumber: 1,
      versionStatus: "PUBLISHED",
      publishedConfigurationPayload: {
        milestones: [{ code: "REFERRED" }, { code: "QUALIFIED" }, { code: "CONVERTED" }],
      },
      payloadHash: "hash-001",
      publishedByRef: "amplifi-admin",
      publishedAt: "2026-07-19T00:00:00",
      archivedByRef: null,
      archivedAt: null,
      archiveReason: null,
      rollbackFromVersionId: null,
      safeSummary: {},
      governanceMetadata: {},
      createdAt: "2026-07-19T00:00:00",
      guardrails: ["NO_RUNTIME_JOURNEY_MUTATION"],
      redactions: ["INTERNAL_TENANT_IDENTIFIER"],
      noRuntimeJourneyMutationConfirmed: true,
      noCampaignBindingConfirmed: true,
      noCampaignActivationConfirmed: true,
      noProviderDispatchConfirmed: true,
      noAuthBillingOrMoneyActionConfirmed: true,
    },
    archiveBlockers: [],
    guardrail: "Published version only.",
    guardrails: ["NO_RUNTIME_JOURNEY_MUTATION"],
    redactions: ["INTERNAL_TENANT_IDENTIFIER"],
    noRuntimeJourneyMutationConfirmed: true,
    noCampaignBindingConfirmed: true,
    noCampaignActivationConfirmed: true,
    noProviderDispatchConfirmed: true,
    noAuthBillingOrMoneyActionConfirmed: true,
  };
}

function mockJourneyVersionList(): ReferralSaasCustomerJourneyVersionListResponse {
  const publishResponse = mockJourneyPublishResponse();
  return {
    status: "ok",
    context: "setup",
    account: publishResponse.account,
    count: 1,
    versions: [publishResponse.version],
    guardrail: "Published customer journey versions only.",
    guardrails: ["READ_ONLY_JOURNEY_VERSION_LIST"],
    redactions: ["INTERNAL_TENANT_IDENTIFIER"],
    noRuntimeJourneyMutationConfirmed: true,
    noCampaignBindingConfirmed: true,
    noCampaignActivationConfirmed: true,
    noProviderDispatchConfirmed: true,
    noAuthBillingOrMoneyActionConfirmed: true,
  };
}

function mockProgrammeCatalogue() {
  return {
    status: "ok",
    context: "setup" as const,
    account: {
      accountId: "acct-gabs",
      accountCode: "ACC-2201",
      accountName: "Gaborone Partners",
      accountStatus: "ACTIVE",
      onboardingStatus: "APPROVED",
    },
    productCode: "REFERRAL_SAAS",
    subProductCodes: ["RMCA_BUNDLE", "REFERRAL_ONLY"],
    customerProductLines: [
      {
        customerProductLineId: "product-line-001",
        accountId: "acct-gabs",
        externalProductLineRef: "TRANSACTIONAL_BANKING",
        productLineName: "Transactional banking",
        productLineCategory: "Banking and financial services",
        operatingJurisdictionCode: "BW",
        lifecycleStatus: "ACTIVE",
        description: "Everyday banking referral products.",
        safeSummary: {},
        governanceMetadata: {},
        offerings: [
          {
            customerProductOfferingId: "offering-001",
            accountId: "acct-gabs",
            customerProductLineId: "product-line-001",
            externalOfferingRef: "EASY_ACCOUNT",
            offeringName: "Easy Account",
            offeringFamily: "Current account",
            operatingJurisdictionCode: "BW",
            lifecycleStatus: "ACTIVE",
            description: "Entry-level current account offering.",
            safeSummary: {},
            governanceMetadata: {},
            createdAt: "2026-07-19T00:00:00",
            updatedAt: "2026-07-19T00:00:00",
            archivedAt: null,
            guardrails: ["ACCOUNT_SCOPED_PRODUCT_CATALOGUE"],
            redactions: ["internal_tenant_identifier"],
          },
        ],
        createdAt: "2026-07-19T00:00:00",
        updatedAt: "2026-07-19T00:00:00",
        archivedAt: null,
        guardrails: ["ACCOUNT_SCOPED_PRODUCT_CATALOGUE"],
        redactions: ["internal_tenant_identifier"],
      },
    ],
    customerJourneyVersions: [
      {
        customerJourneyVersionId: "journey-version-001",
        customerJourneyCode: "GABS_REFERRAL_STANDARD",
        versionNumber: 1,
        versionStatus: "PUBLISHED",
        templateCode: "REFERRAL_STANDARD",
        templateVersion: "1.0.0",
        safeSummary: {},
        governanceMetadata: {},
        publishedAt: "2026-07-19T00:00:00",
      },
    ],
    guardrail: "Approved building-block catalogue only.",
    guardrails: ["NO_PROVIDER_DISPATCH"],
    redactions: ["internal_tenant_identifier"],
  };
}

function mockProgrammeDraftCommand() {
  return {
    status: "ok",
    context: "setup" as const,
    account: mockProgrammeCatalogue().account,
    commandStatus: "DRAFT_SAVED",
    idempotencyStatus: "NEW_REQUEST",
    draft: {
      programmeDraftId: "programme-draft-001",
      accountId: "acct-gabs",
      customerJourneyVersionId: "journey-version-001",
      programmeName: "Gaborone Partners referral programme",
      programmeDescription: "Referral management and campaign attribution programme.",
      operatingJurisdictionCode: "BW",
      productCode: "REFERRAL_SAAS",
      subProductCode: "RMCA_BUNDLE",
      customerProductLineId: "product-line-001",
      customerProductOfferingId: "offering-001",
      customerProductBinding: {
        customerProductLineId: "product-line-001",
        customerProductOfferingId: "offering-001",
        externalProductLineRef: "TRANSACTIONAL_BANKING",
        productLineName: "Transactional banking",
        productLineCategory: "Banking and financial services",
        externalOfferingRef: "EASY_ACCOUNT",
        offeringName: "Easy Account",
        offeringFamily: "Current account",
        operatingJurisdictionCode: "BW",
        productLineStatus: "ACTIVE",
        offeringStatus: "ACTIVE",
      },
      programmeStatus: "DRAFT",
      draftVersion: 1,
      campaignDefaults: { campaignPurpose: "Customer referral acquisition", attributionWindowDays: 30 },
      incentiveRefs: [],
      engagementRefs: [],
      integrationReadinessSnapshot: {},
      commercialEntitlementSnapshot: {},
      lastValidationStatus: "NOT_VALIDATED",
      reviewStatus: "NOT_SUBMITTED",
      effectiveFrom: null,
      effectiveTo: null,
      createdAt: "2026-08-16T00:00:00",
      updatedAt: "2026-08-16T00:00:00",
      archivedAt: null,
      guardrails: ["NO_CAMPAIGN_ACTIVATION"],
      redactions: ["internal_tenant_identifier"],
    },
    guardrail: "Programme draft only.",
    guardrails: ["NO_CAMPAIGN_ACTIVATION"],
    redactions: ["internal_tenant_identifier"],
  };
}

function mockProgrammeValidation() {
  return {
    status: "ok",
    context: "setup" as const,
    account: mockProgrammeCatalogue().account,
    validation: {
      programmeValidationResultId: "programme-validation-001",
      programmeDraftId: "programme-draft-001",
      validationStatus: "VALIDATION_PASSED",
      publishAllowed: true,
      campaignBindingAllowed: true,
      plainLanguageSummary: "Programme package is ready to publish.",
      blockers: [],
      warnings: [],
      configurationSnapshot: {},
      simulation: { simulatedMilestonePath: ["REFERRED", "QUALIFIED", "CONVERTED"] },
      guardrails: ["NO_CAMPAIGN_ACTIVATION"],
      redactions: ["internal_tenant_identifier"],
    },
    guardrail: "Programme validation only.",
    guardrails: ["NO_CAMPAIGN_ACTIVATION"],
    redactions: ["internal_tenant_identifier"],
  };
}

function mockProgrammeLifecycle(commandStatus = "PUBLISHED") {
  return {
    status: "ok",
    context: "setup" as const,
    account: mockProgrammeCatalogue().account,
    commandStatus,
    idempotencyStatus: "NEW_REQUEST",
    resource: {},
    programmeVersion: {
      programmeVersionId: "programme-version-001",
      accountId: "acct-gabs",
      programmeCode: "GABS_PROGRAMME_001",
      programmeName: "Gaborone Partners referral programme",
      programmeDescription: "Referral management and campaign attribution programme.",
      operatingJurisdictionCode: "BW",
      productCode: "REFERRAL_SAAS",
      subProductCode: "RMCA_BUNDLE",
      customerProductLineId: "product-line-001",
      customerProductOfferingId: "offering-001",
      customerProductBinding: {
        customerProductLineId: "product-line-001",
        customerProductOfferingId: "offering-001",
        externalProductLineRef: "TRANSACTIONAL_BANKING",
        productLineName: "Transactional banking",
        productLineCategory: "Banking and financial services",
        externalOfferingRef: "EASY_ACCOUNT",
        offeringName: "Easy Account",
        offeringFamily: "Current account",
        operatingJurisdictionCode: "BW",
        productLineStatus: "ACTIVE",
        offeringStatus: "ACTIVE",
      },
      versionNumber: 1,
      versionStatus: "PUBLISHED",
      customerJourneyVersionId: "journey-version-001",
      campaignDefaultsSnapshot: { campaignPurpose: "Customer referral acquisition", attributionWindowDays: 30 },
      incentiveRefsSnapshot: [],
      engagementRefsSnapshot: [],
      integrationReadinessSnapshot: {},
      commercialEntitlementSnapshot: {},
      effectiveFrom: null,
      effectiveTo: null,
      safeSummary: {},
      governanceMetadata: {},
      publishedAt: "2026-08-16T00:00:00",
      retiredAt: null,
      guardrails: ["NO_CAMPAIGN_ACTIVATION"],
      redactions: ["internal_tenant_identifier"],
    },
    plainLanguageSummary: "Programme version published for campaign setup.",
    guardrail: "Programme lifecycle only.",
    guardrails: ["NO_CAMPAIGN_ACTIVATION"],
    redactions: ["internal_tenant_identifier"],
  };
}

function mockProgrammeList() {
  return {
    status: "ok",
    context: "setup" as const,
    account: mockProgrammeCatalogue().account,
    count: 1,
    programmes: [mockProgrammeLifecycle().programmeVersion],
    guardrail: "Read-only programme list.",
    guardrails: ["READ_ONLY_PROGRAMME_LIST"],
    redactions: ["internal_tenant_identifier"],
  };
}

function mockProgrammeAnalytics() {
  return {
    status: "ok",
    context: "setup" as const,
    account: mockProgrammeCatalogue().account,
    programmeAnalytics: {
      versionCount: 1,
      versions: [
        {
          programmeVersionId: "programme-version-001",
          programmeCode: "GABS_PROGRAMME_001",
          programmeName: "Gaborone Partners referral programme",
          versionNumber: 1,
          versionStatus: "PUBLISHED",
          campaignCount: 1,
          activeCampaignCount: 0,
          referralCount: 12,
          attributedReferralCount: 9,
          completedReferralCount: 4,
          attributionRate: 0.75,
          completionRate: 0.33,
          performanceSignal: "BASELINE",
        },
      ],
      reportingDimensions: {
        productLineCount: 1,
        productOfferingCount: 2,
        runtimeCampaignCount: 3,
        approvedCampaignOverrideReferralCount: 4,
        effectiveRuleSnapshotCount: 12,
        overrideRate: 0.33,
        snapshotCoverageRate: 1,
      },
      summary: {},
      dataWindowStart: null,
      dataWindowEnd: null,
      guardrails: ["READ_ONLY_PROGRAMME_ANALYTICS"],
      redactions: ["internal_tenant_identifier"],
    },
    guardrail: "Read-only programme analytics.",
    guardrails: ["READ_ONLY_PROGRAMME_ANALYTICS"],
    redactions: ["internal_tenant_identifier"],
  };
}

function mockCampaignJourneyBindingResponse() {
  return {
    status: "ok",
    context: "setup" as const,
    account: {
      accountId: "acct-gabs",
      accountCode: "ACC-2201",
      accountName: "Gaborone Partners",
      accountStatus: "ACTIVE",
      onboardingStatus: "APPROVED",
    },
    commandStatus: "BOUND",
    idempotencyStatus: "NEW_REQUEST",
    journeyBinding: {
      campaignJourneyBindingId: "binding-001",
      accountId: "acct-gabs",
      campaignCode: "BW-REFERRAL-SPRING-1234",
      customerJourneyVersionId: "journey-version-001",
      bindingStatus: "BOUND",
      bindingPayloadHash: "binding-hash-001",
      boundByRef: "amplifi-admin",
      boundAt: "2026-07-19T00:00:00",
      customerJourneyCode: "GABS_REFERRAL_STANDARD",
      versionNumber: 1,
      templateCode: "REFERRAL_STANDARD",
      templateVersion: "1.0.0",
      versionStatus: "PUBLISHED",
      activationGateSatisfied: true,
      guardrails: ["NO_CAMPAIGN_ACTIVATION"],
      redactions: ["INTERNAL_TENANT_IDENTIFIER"],
      noRuntimeJourneyMutationConfirmed: true,
      noCampaignActivationConfirmed: true,
      noProviderDispatchConfirmed: true,
      noAuthBillingOrMoneyActionConfirmed: true,
    },
    guardrail: "Campaign journey binding only.",
    guardrails: ["NO_CAMPAIGN_ACTIVATION"],
    redactions: ["INTERNAL_TENANT_IDENTIFIER"],
    noRuntimeJourneyMutationConfirmed: true,
    noCampaignActivationConfirmed: true,
    noProviderDispatchConfirmed: true,
    noAuthBillingOrMoneyActionConfirmed: true,
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

function mockLoginCompletionReadiness(
  status = "LOGIN_COMPLETION_BLOCKED_SEAT_NOT_ASSIGNED",
): ReferralSaasLoginCompletionReadinessResponse {
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
    loginCompletionReadiness: {
      loginCompletionStatus: status,
      accountRef: "acct-gabs",
      membershipRef: "membership-1",
      person: {
        subject: "owner@gabs.example",
        displayName: "Gaborone owner",
        responsibilities: ["DISTRIBUTION_ADMIN"],
      },
      seat: {
        seatAssignmentStatus: status === "LOGIN_COMPLETION_READY" ? "SEAT_ASSIGNED" : "SEAT_NOT_ASSIGNED",
      },
      identity: {
        identityProviderStatus: status === "LOGIN_COMPLETION_READY" ? "AUTH_PROVIDER_READY" : "AUTH_PROVIDER_PENDING",
        authClaimStatus: "AUTH_CLAIMS_NOT_PROPAGATED",
        permissionProfile: "REFERRAL_SAAS_ACCOUNT_ADMIN",
      },
      blockers: status === "LOGIN_COMPLETION_READY" ? [] : ["SEAT_NOT_ASSIGNED"],
      nextActions:
        status === "LOGIN_COMPLETION_READY"
          ? ["Record governed login completion evidence if this person must sign in."]
          : ["Assign the platform seat before login completion."],
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
  };
}

function mockLoginCompletionIntent(status = "LOGIN_COMPLETION_RECORDED") {
  return {
    status: "ok",
    context: "setup" as const,
    account: mockLoginCompletionReadiness().account,
    loginCompletionIntent: {
      commandStatus: "SUCCESS",
      loginCompletionStatus: status,
      membership: {
        membershipRef: "membership-1",
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
          label: "Record webhook test evidence",
          status: "READY",
          nextStep: "Record governed webhook callback test evidence for this customer.",
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

function mockReadyMessageProviderIntegrationExecutionReadiness(): ReferralSaasIntegrationExecutionReadinessResponse {
  const response = mockReadyIntegrationExecutionReadiness();
  return {
    ...response,
    integrationExecutionReadiness: {
      ...response.integrationExecutionReadiness,
      readyActions: [
        ...response.integrationExecutionReadiness.readyActions,
        {
          actionRef: "MESSAGE_PROVIDER_TEST",
          label: "Check message provider delivery",
          status: "READY",
          nextStep: "Record governed provider delivery evidence for this customer.",
          reason: "Requires selected channels and approved provider references.",
        },
      ],
      executionActions: response.integrationExecutionReadiness.executionActions.map((action) =>
        action.actionRef === "MESSAGE_PROVIDER_TEST"
          ? {
              ...action,
              status: "READY",
              nextStep: "Record governed provider delivery evidence for this customer.",
            }
          : action,
      ),
    },
  };
}

function mockProviderVaultReadiness(
  status = "PROVIDER_VAULT_BLOCKED_REQUEST_NOT_APPROVED",
): ReferralSaasProviderVaultReadinessResponse {
  const ready = status === "PROVIDER_VAULT_EXECUTION_READY";
  return {
    status: "ok",
    context: "setup",
    account: mockTechnicalSetupReadiness().account,
    integrationConfiguration: mockIntegrationConfigurationSave().integrationConfigurationResult.configuration,
    providerVaultReadiness: {
      readinessStatus: status,
      plainLanguageSummary: ready
        ? "Approved credential request evidence is ready for a future governed provider/vault executor."
        : "Provider/vault execution is blocked until the listed customer setup and credential request evidence is complete.",
      credentialRequests: ready
        ? [
            {
              credentialRequestRef: "credential-request-1",
              capability: "MESSAGE_PROVIDER",
              requestType: "PROVIDER_CREDENTIAL",
              environment: "SANDBOX",
              reviewStatus: "REVIEW_APPROVED",
              readinessStatus: "PROVIDER_VAULT_EXECUTION_READY",
              readyForExecution: true,
              plainLanguageSummary:
                "This approved request is ready for a future governed provider/vault executor. This read endpoint did not call a provider or write a vault.",
              blockers: [],
              nextActions: [
                {
                  actionRef: "PROVIDER_VAULT_EXECUTOR_HANDOFF",
                  label: "Prepare provider/vault executor handoff",
                  status: "READY",
                  nextStep: "Use a governed executor workflow when provider/vault adapters exist.",
                  reason: "Approved credential request and saved customer Integrations configuration are aligned.",
                },
              ],
              configurationRef: "integration-config-1",
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
          ]
        : [],
      blockers: ready
        ? []
        : [
            {
              code: "CREDENTIAL_REQUEST_NOT_APPROVED",
              message: "Approve at least one credential request before provider/vault execution readiness.",
            },
          ],
      readyActions: ready
        ? [
            {
              actionRef: "PROVIDER_VAULT_EXECUTOR_HANDOFF",
              label: "Prepare provider/vault executor handoff",
              status: "READY",
              nextStep: "Use a governed executor workflow when provider/vault adapters exist.",
              reason: "Approved credential request and saved configuration are aligned.",
            },
          ]
        : [],
      configurationRef: "integration-config-1",
      configurationStatus: "INTEGRATION_CONFIGURATION_SAVED",
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
  };
}

function mockApiAccessVerificationResponse() {
  return {
    status: "accepted",
    context: "setup" as const,
    account: mockTechnicalSetupReadiness().account,
    integrationApiAccessVerification: {
      verificationStatus: "API_ACCESS_VERIFICATION_RECORDED",
      configurationRef: "integration-config-1",
      accountRef: "acct-gabs",
      apiEnvironment: "LOCAL_DEVELOPMENT",
      verifiedUseCases: ["CAMPAIGN_READ", "REFERRAL_CODE_VALIDATE", "REPORT_READ"],
      idempotency: { status: "NEW_REQUEST" },
      audit: { accountAuditEventId: "audit-api-access-1" },
      plainLanguageSummary:
        "API-access verification evidence was recorded for the selected customer without credential creation.",
      guardrails: ["NO_CREDENTIAL_CREATION", "NO_PROVIDER_CALL"],
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
    guardrails: ["NO_CREDENTIAL_CREATION", "NO_PROVIDER_CALL"],
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
  };
}

function mockWebhookTestDispatchResponse() {
  return {
    status: "accepted",
    context: "setup" as const,
    account: mockTechnicalSetupReadiness().account,
    integrationWebhookTestDispatch: {
      dispatchStatus: "WEBHOOK_TEST_DISPATCH_RECORDED",
      configurationRef: "integration-config-1",
      accountRef: "acct-gabs",
      callbackUrlPresent: true,
      eventCategories: ["REFERRAL", "ATTRIBUTION"],
      idempotency: { status: "WEBHOOK_TEST_DISPATCH_RECORDED" },
      audit: { accountAuditEventId: "audit-webhook-test-1" },
      plainLanguageSummary:
        "Webhook test-dispatch evidence was recorded for the selected customer. No webhook was dispatched.",
      guardrails: ["NO_WEBHOOK_DISPATCH", "NO_CREDENTIAL_CREATION"],
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
    guardrail: "Webhook test-dispatch evidence recorded for the selected customer only.",
    guardrails: ["NO_WEBHOOK_DISPATCH", "NO_CREDENTIAL_CREATION"],
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
  };
}

function mockMessageProviderTestResponse() {
  return {
    status: "accepted",
    context: "setup" as const,
    account: mockTechnicalSetupReadiness().account,
    integrationMessageProviderTest: {
      testStatus: "MESSAGE_PROVIDER_TEST_RECORDED",
      configurationRef: "integration-config-1",
      accountRef: "acct-gabs",
      channels: ["EMAIL"],
      providerRefs: ["provider-approved-email"],
      idempotency: { status: "MESSAGE_PROVIDER_TEST_RECORDED" },
      audit: { accountAuditEventId: "audit-message-provider-test-1" },
      plainLanguageSummary:
        "Message-provider test evidence was recorded for the selected customer. No provider was called and no message was sent.",
      guardrails: ["NO_MESSAGE_PROVIDER_DELIVERY", "NO_PROVIDER_CALL"],
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
    guardrails: ["NO_MESSAGE_PROVIDER_DELIVERY", "NO_PROVIDER_CALL"],
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
  };
}

function mockIntegrationCredentialRequest() {
  return {
    credentialRequestRef: "credential-request-1",
    accountRef: "acct-gabs",
    configurationRef: "integration-config-1",
    credentialRequestStatus: "REQUEST_RECORDED",
    reviewStatus: "PENDING_REVIEW",
    requestType: "API_KEY_CREATE",
    capability: "REFERRAL_SAAS_API_ACCESS",
    environment: "LOCAL_DEVELOPMENT",
    intendedUse: ["CAMPAIGN_READ", "REFERRAL_CODE_VALIDATE", "REPORT_READ"],
    requestedFor: {
      customerName: "Gaborone Partners",
      configurationRef: "integration-config-1",
      requestedBy: "AMPLIFI_ADMIN",
      requestReason: "Customer integration credential setup",
    },
    safeRequestPosture: {
      credentialLifecycle: "REQUEST_ONLY",
    },
    reasonCode: "CUSTOMER_CREDENTIAL_REQUEST",
    correlationId: "customer-profile-integrations-credential-request-acct-gabs",
    createdByRef: "test-admin-key",
    createdByRole: "AMPLIFI_ADMIN",
    createdAt: "2026-07-31T00:00:00Z",
    updatedAt: "2026-07-31T00:00:00Z",
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
  };
}

function mockIntegrationCredentialRequestList(
  credentialRequests = [mockIntegrationCredentialRequest()],
): ReferralSaasIntegrationCredentialRequestListResponse {
  return {
    status: "ok",
    context: "setup",
    account: mockTechnicalSetupReadiness().account,
    credentialRequests,
    guardrail: "Credential setup requests are listed for the selected customer only.",
    guardrails: ["CUSTOMER_SCOPED_CREDENTIAL_REQUESTS", "NO_CREDENTIAL_CREATION"],
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
  };
}

function mockIntegrationCredentialRequestResponse() {
  return {
    status: "accepted",
    context: "setup" as const,
    account: mockTechnicalSetupReadiness().account,
    integrationCredentialRequestResult: {
      commandStatus: "CREDENTIAL_REQUEST_RECORDED",
      credentialRequest: mockIntegrationCredentialRequest(),
      idempotency: { status: "NEW_REQUEST" },
      audit: { accountAuditEventId: "audit-credential-request-1" },
      plainLanguageSummary:
        "Credential setup request was recorded for the selected customer. No credential was created, revealed, stored, or sent.",
      guardrails: ["NO_CREDENTIAL_CREATION", "NO_CREDENTIAL_REVEAL_OR_DOWNLOAD", "NO_PROVIDER_CALL"],
      redactions: ["provider_secret"],
    },
    guardrail: "Credential setup request recorded for the selected customer only.",
    guardrails: ["NO_CREDENTIAL_CREATION", "NO_CREDENTIAL_REVEAL_OR_DOWNLOAD", "NO_PROVIDER_CALL"],
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
  };
}

function mockIntegrationCredentialReviewDecisionResponse(reviewStatus = "REVIEW_APPROVED") {
  return {
    status: "accepted",
    context: "setup" as const,
    account: mockTechnicalSetupReadiness().account,
    integrationCredentialReviewDecisionResult: {
      commandStatus: "CREDENTIAL_REQUEST_REVIEW_RECORDED",
      credentialRequest: {
        ...mockIntegrationCredentialRequest(),
        reviewStatus,
      },
      reviewStatus,
      idempotency: { status: "CREDENTIAL_REQUEST_REVIEW_RECORDED" },
      audit: { accountAuditEventId: "audit-credential-review-1" },
      plainLanguageSummary:
        "Credential request was approved for later governed execution. No secret was created, revealed, stored, downloaded, or sent.",
      guardrails: ["NO_CREDENTIAL_CREATION", "NO_CREDENTIAL_REVEAL_OR_DOWNLOAD", "NO_PROVIDER_CALL"],
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
    guardrails: ["NO_CREDENTIAL_CREATION", "NO_CREDENTIAL_REVEAL_OR_DOWNLOAD", "NO_PROVIDER_CALL"],
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
  };
}

function mockIntegrationCredentialExecutionCheckResponse() {
  return {
    status: "accepted",
    context: "setup" as const,
    account: mockTechnicalSetupReadiness().account,
    integrationCredentialExecutionCheckResult: {
      commandStatus: "CREDENTIAL_EXECUTION_CHECK_RECORDED",
      credentialRequest: {
        ...mockIntegrationCredentialRequest(),
        reviewStatus: "REVIEW_APPROVED",
      },
      executionCheckStatus: "CREDENTIAL_EXECUTION_CHECK_RECORDED",
      idempotency: { status: "CREDENTIAL_EXECUTION_CHECK_RECORDED" },
      audit: { accountAuditEventId: "audit-credential-execution-1" },
      plainLanguageSummary:
        "Approved credential setup was checked for later governed execution. No credential was created, revealed, stored, downloaded, or sent.",
      guardrails: ["NO_CREDENTIAL_CREATION", "NO_CREDENTIAL_REVEAL_OR_DOWNLOAD", "NO_PROVIDER_CALL"],
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
    guardrail: "Credential execution check recorded for the selected customer.",
    guardrails: ["NO_CREDENTIAL_CREATION", "NO_CREDENTIAL_REVEAL_OR_DOWNLOAD", "NO_PROVIDER_CALL"],
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
    campaign_capability_enforced_confirmed: true,
    required_campaign_capability: "REFERRAL_SAAS_CAMPAIGN_READ",
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
    campaign_capability_enforced_confirmed: true,
    required_campaign_capability: "REFERRAL_SAAS_CAMPAIGN_POLICY_WRITE",
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
    campaign_capability_enforced_confirmed: true,
    required_campaign_capability:
      status === "REVIEW_APPROVED"
        ? "REFERRAL_SAAS_CAMPAIGN_REVIEW_DECIDE"
        : "REFERRAL_SAAS_CAMPAIGN_REVIEW_SUBMIT",
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
    campaign_capability_enforced_confirmed: true,
    required_campaign_capability: "REFERRAL_SAAS_CAMPAIGN_ACTIVATE",
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
    window.URL.createObjectURL = vi.fn(() => "blob:customer-report-export");
    window.URL.revokeObjectURL = vi.fn();
    mockedGetAdminOnboardingDrafts.mockResolvedValue(mockDraftSelector());
    mockedGetAdminOnboardingState.mockResolvedValue(mockMaintenanceState());
    mockedGetReferralSaasAccountMembershipPosture.mockResolvedValue(mockMembershipPosture());
    mockedGetReferralSaasIntegrationConfiguration.mockResolvedValue(mockIntegrationConfigurationRead());
    mockedGetReferralSaasIntegrationExecutionReadiness.mockResolvedValue(mockIntegrationExecutionReadiness());
    mockedGetReferralSaasProviderVaultReadiness.mockResolvedValue(mockProviderVaultReadiness());
    mockedGetReferralSaasMembershipActivationReadiness.mockResolvedValue(mockMembershipActivationReadiness());
    mockedGetReferralSaasLoginCompletionReadiness.mockResolvedValue(mockLoginCompletionReadiness());
    mockedGetReferralSaasTechnicalSetupReadiness.mockResolvedValue(mockTechnicalSetupReadiness());
    mockedListReferralSaasJourneyTemplates.mockResolvedValue(mockJourneyTemplateCatalogue());
    mockedListReferralSaasAccountJourneyDrafts.mockResolvedValue(mockJourneyDraftList());
    mockedListReferralSaasAccountJourneyVersions.mockResolvedValue(mockJourneyVersionList());
    mockedSaveReferralSaasAccountJourneyDraft.mockResolvedValue(mockJourneyDraftCommandResponse());
    mockedValidateReferralSaasAccountJourneyDraft.mockResolvedValue(mockJourneyValidationResponse());
    mockedPublishReferralSaasAccountJourneyDraft.mockResolvedValue(mockJourneyPublishResponse());
    mockedBindReferralSaasAccountCampaignJourneyVersion.mockResolvedValue(mockCampaignJourneyBindingResponse());
    mockedGetReferralSaasAccountProgrammeCatalogue.mockResolvedValue(mockProgrammeCatalogue());
    mockedGetReferralSaasCustomerProductCatalogue.mockResolvedValue({
      ...mockProgrammeCatalogue(),
      productLines: mockProgrammeCatalogue().customerProductLines,
      count: 1,
    });
    mockedSaveReferralSaasCustomerProductLine.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: mockProgrammeCatalogue().account,
      commandStatus: "SAVED",
      idempotencyStatus: "NEW_REQUEST",
      guardrail: "Customer product catalogue only.",
    });
    mockedSaveReferralSaasCustomerProductOffering.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: mockProgrammeCatalogue().account,
      commandStatus: "SAVED",
      idempotencyStatus: "NEW_REQUEST",
      guardrail: "Customer product catalogue only.",
    });
    mockedListReferralSaasAccountProgrammes.mockResolvedValue(mockProgrammeList());
    mockedGetReferralSaasAccountProgrammeAnalytics.mockResolvedValue(mockProgrammeAnalytics());
    mockedCreateReferralSaasProgrammeDraft.mockResolvedValue(mockProgrammeDraftCommand());
    mockedUpdateReferralSaasProgrammeDraft.mockResolvedValue(mockProgrammeDraftCommand());
    mockedValidateReferralSaasProgrammeDraft.mockResolvedValue(mockProgrammeValidation());
    mockedSubmitReferralSaasProgrammeDraftReview.mockResolvedValue(mockProgrammeLifecycle("READY_FOR_REVIEW"));
    mockedDecideReferralSaasProgrammeDraftReview.mockResolvedValue(mockProgrammeLifecycle("APPROVED"));
    mockedPublishReferralSaasProgrammeDraft.mockResolvedValue(mockProgrammeLifecycle("PUBLISHED"));
    mockedListReferralSaasIntegrationCredentialRequests.mockResolvedValue(mockIntegrationCredentialRequestList([]));
    mockedListReferralSaasAccountSupportCases.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACCT_GABS",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
      },
      supportCases: [],
      guardrails: ["NO_REPAIR_REPLAY_RETRY"],
      redactions: ["internal_tenant_identifier"],
      no_tenant_code_exposure_confirmed: true,
      no_product_state_mutation_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });
    mockedGetReferralSaasAccountSupportCaseRepairReplayReadiness.mockResolvedValue({
      status: "ok",
      context: "support",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACCT_GABS",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
      },
      repairReplayReadiness: {
        caseRef: "case-support-1",
        accountRef: "acct-gabs",
        category: "VALIDATION_RECOVERY",
        status: "OPEN",
        overallStatus: "REVIEW_REQUIRED",
        actionSummary: "Readiness only.",
        owningWorkflow: "links_and_codes",
        allowedActions: [
          {
            action: "READ_ONLY_DIAGNOSTIC",
            status: "AVAILABLE",
            label: "Review support evidence",
            reasonCode: "EVIDENCE_AVAILABLE",
          },
          {
            action: "GOVERNED_REPAIR",
            status: "BLOCKED",
            label: "Repair validation evidence",
            reasonCode: "FUTURE_GOVERNED_COMMAND_REQUIRED",
          },
        ],
        requiredEvidence: ["support_case_link", "before_state_hash"],
        supportCase: {
          caseRef: "case-support-1",
          accountRef: "acct-gabs",
          category: "VALIDATION_RECOVERY",
          priority: "HIGH",
          status: "OPEN",
          title: "Referral code validation failed",
          summary: "The branch pilot cannot validate a safe referral code.",
          sourceSurface: "support_hub",
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
    mockedCreateReferralSaasAccountReportExportRequest.mockResolvedValue({
      status: "accepted",
      reportExport: {
        exportRequest: {
          exportRequestId: "export-1",
          format: "csv",
          rowCount: 1,
          storageStatus: "NOT_STORED",
          downloadStatus: "NOT_AVAILABLE",
          downloadUrl: null,
        },
        file: {},
      },
    });
    mockedCreateReferralSaasAccountReportExportFile.mockResolvedValue({
      status: "stored",
      reportExport: {
        exportRequest: {
          exportRequestId: "export-1",
          format: "csv",
          rowCount: 1,
          storageStatus: "STORED",
          downloadStatus: "AVAILABLE",
          downloadUrl: null,
        },
        file: {
          fileName: "campaign-performance-export-1.csv",
          contentType: "text/csv",
          contentSha256: "sha256-safe",
          byteSize: 64,
          storageMode: "INLINE_DB",
        },
      },
    });
    mockedDownloadReferralSaasAccountReportExportFile.mockResolvedValue({
      status: "downloaded",
      reportExport: {
        exportRequest: {
          exportRequestId: "export-1",
          format: "csv",
          rowCount: 1,
          storageStatus: "STORED",
          downloadStatus: "AVAILABLE",
          downloadUrl: null,
        },
        file: {
          fileName: "campaign-performance-export-1.csv",
          contentType: "text/csv",
          contentSha256: "sha256-safe",
          byteSize: 64,
          storageMode: "INLINE_DB",
          content: "campaign_code,metric_name,value\nCAMP001,referrals.completed_count,4\n",
        },
      },
    });
    mockedListReferralSaasAccountReportDeliverySchedules.mockResolvedValue({
      status: "ok",
      deliverySchedules: [
        {
          commandStatus: "REPORT_DELIVERY_SCHEDULE_RECORDED",
          deliverySchedule: {
            scheduleId: "schedule-1",
            cadence: "WEEKLY",
            timezone: "Africa/Johannesburg",
            format: "csv",
            redactionProfile: "tenant_safe",
            recipientContactRefs: ["contact-owner"],
            retentionDays: 7,
            scheduleStatus: "READY",
            deliveryStatus: "NOT_REQUESTED",
            campaignRef: "CAMP001",
            nextRunAt: null,
            lastRunAt: null,
            blockedReasons: [],
            warnings: ["LIVE_DELIVERY_WORKER_NOT_ENABLED"],
          },
          readiness: {
            status: "READY",
            blockedReasons: [],
            warnings: ["LIVE_DELIVERY_WORKER_NOT_ENABLED"],
          },
          noLiveDeliveryExecutedConfirmed: true,
          noEmailSentConfirmed: true,
          noWebhookDispatchConfirmed: true,
          noCredentialOrAuthChangeConfirmed: true,
          noCampaignActivationConfirmed: true,
          noBillingOrMoneyMovementConfirmed: true,
        },
      ],
      account_scope: {
        source: "selected_customer_account",
        account_ref: "acct-gabs",
        external_tenant_ref: "gabs-platform",
      },
      guardrails: ["NO_LIVE_DELIVERY_EXECUTION"],
      redactions: ["internal_tenant_identifier"],
      no_live_delivery_executed_confirmed: true,
    });
    mockedCreateReferralSaasAccountReportDeliverySchedule.mockResolvedValue({
      status: "accepted",
      reportDeliverySchedule: {
        commandStatus: "REPORT_DELIVERY_SCHEDULE_RECORDED",
        deliverySchedule: {
          scheduleId: "schedule-2",
          cadence: "WEEKLY",
          timezone: "Africa/Johannesburg",
          format: "csv",
          redactionProfile: "tenant_safe",
          recipientContactRefs: ["contact-owner"],
          retentionDays: 7,
          scheduleStatus: "READY",
          deliveryStatus: "NOT_REQUESTED",
          campaignRef: "CAMP001",
          nextRunAt: null,
          lastRunAt: null,
          blockedReasons: [],
          warnings: ["LIVE_DELIVERY_WORKER_NOT_ENABLED"],
        },
        readiness: {
          status: "READY",
          blockedReasons: [],
          warnings: ["LIVE_DELIVERY_WORKER_NOT_ENABLED"],
        },
      },
      guardrail: "Report delivery schedule intent recorded.",
      no_live_delivery_executed_confirmed: true,
      no_email_sent_confirmed: true,
      no_webhook_dispatch_confirmed: true,
      no_credential_or_auth_change_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });
    mockedUpdateReferralSaasAccountReportDeliverySchedule.mockResolvedValue({
      status: "accepted",
      reportDeliverySchedule: {
        commandStatus: "REPORT_DELIVERY_SCHEDULE_UPDATED",
        deliverySchedule: {
          scheduleId: "schedule-1",
          scheduleStatus: "PAUSED",
        },
        readiness: {
          status: "PAUSED",
          blockedReasons: [],
          warnings: ["LIVE_DELIVERY_WORKER_NOT_ENABLED"],
        },
      },
      guardrail: "Report delivery schedule updated.",
      no_live_delivery_executed_confirmed: true,
      no_email_sent_confirmed: true,
      no_webhook_dispatch_confirmed: true,
      no_credential_or_auth_change_confirmed: true,
      no_campaign_activation_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });
    mockedGetReferralSaasAccountReportDeliveryScheduleReadiness.mockResolvedValue({
      status: "ok",
      reportDeliveryScheduleReadiness: {
        scheduleId: "schedule-1",
        readiness: {
          status: "READY",
          blockedReasons: [],
          warnings: ["LIVE_DELIVERY_WORKER_NOT_ENABLED"],
        },
      },
      no_live_delivery_executed_confirmed: true,
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
    mockedRecordReferralSaasApiAccessVerification.mockResolvedValue(mockApiAccessVerificationResponse());
    mockedRecordReferralSaasIntegrationCredentialRequest.mockResolvedValue(mockIntegrationCredentialRequestResponse());
    mockedRecordReferralSaasIntegrationCredentialReviewDecision.mockResolvedValue(
      mockIntegrationCredentialReviewDecisionResponse(),
    );
    mockedRecordReferralSaasIntegrationCredentialExecutionCheck.mockResolvedValue(
      mockIntegrationCredentialExecutionCheckResponse(),
    );
    mockedRecordReferralSaasWebhookTestDispatch.mockResolvedValue(mockWebhookTestDispatchResponse());
    mockedRecordReferralSaasMessageProviderTest.mockResolvedValue(mockMessageProviderTestResponse());
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
      campaign_capability_enforced_confirmed: true,
      required_campaign_capability: "REFERRAL_SAAS_CAMPAIGN_CREATE",
      no_campaign_activation_confirmed: true,
      no_link_generation_confirmed: true,
      no_validation_track_created_confirmed: true,
      no_policy_write_confirmed: true,
      no_webhook_delivery_confirmed: true,
      no_money_movement_confirmed: true,
    });
    mockedCreateReferralSaasAccountSupportCase.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACCT_GABS",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
      },
      supportCase: {
        commandStatus: "RECORDED",
        supportCase: {
          caseRef: "case-support-1",
          accountRef: "acct-gabs",
          category: "VALIDATION_RECOVERY",
          priority: "HIGH",
          status: "OPEN",
          title: "Referral code validation failed",
          summary: "The branch pilot cannot validate a safe referral code.",
          sourceSurface: "support_hub",
          createdByRef: "operator",
          evidenceLinks: [],
          redactions: ["internal_tenant_identifier"],
        },
        idempotency: { status: "NEW_REQUEST" },
        audit: { accountAuditEventId: "audit-support-1" },
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
    expect(screen.getByText(/permitted to support in South Africa/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Create customer" })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-setup",
    );
    expect(screen.getByRole("searchbox", { name: "Search customers" })).toBeInTheDocument();
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

  it("searches customers using business-facing identifiers", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />);

    const search = await screen.findByRole("searchbox", { name: "Search customers" });
    fireEvent.change(search, { target: { value: "cape" } });

    expect(screen.getByText("1 customer")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Cape Commerce Hub/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /FNB Referral SaaS/ })).not.toBeInTheDocument();
    expect(screen.getByText("Select a customer to continue")).toBeInTheDocument();

    fireEvent.change(search, { target: { value: "not-a-customer" } });
    expect(screen.getByText("No matching customers")).toBeInTheDocument();
    expect(screen.getByText(/Try another name or reference in South Africa/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Clear" }));
    expect(screen.getByText("2 customers")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /FNB Referral SaaS/ })).toBeInTheDocument();
  });

  it("filters customers by jurisdiction and opens the selected customer home", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />);
    fireEvent.click(await screen.findByRole("button", { name: /Botswana/ }));
    fireEvent.click(screen.getByRole("button", { name: /Gaborone Partners/ }));
    fireEvent.click(screen.getByRole("link", { name: "Open customer profile" }));

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.getByLabelText("Selected customer context")).toHaveTextContent("Botswana");
    expect(screen.getByLabelText("Selected customer context")).toHaveTextContent("ACC-2201");
    expect(await screen.findByRole("heading", { name: "Readiness progression" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Account establishment/ })).not.toHaveAttribute("aria-current");
    expect(screen.getByRole("link", { name: /People & access/ })).toHaveAttribute("aria-current", "step");
    expect(screen.getByRole("heading", { name: "Continue in this customer context" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Readiness summary" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Products & programmes/ })).toHaveAttribute("href", "/admin/referral-saas/account-maintenance/acct-gabs/programmes");
    expect(screen.getByRole("link", { name: /Referral operations/ })).toHaveAttribute("href", "/admin/referral-saas/account-maintenance/acct-gabs/referrals");
  });

  it("exposes guarded customer foundation activation before seat provisioning", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-fnb");

    expect(await screen.findByRole("heading", { name: "FNB Referral SaaS" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Activate the customer foundation" })).toBeInTheDocument();
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

  it("opens People and Access as its own customer page from readiness progression", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs");
    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("link", { name: /People & access/ }));
    expect(await screen.findByRole("heading", { name: "People and access" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Customer home" })).toHaveAttribute("href", "/admin/referral-saas/account-maintenance/acct-gabs");
    expect(screen.queryByRole("heading", { name: "Readiness summary" })).not.toBeInTheDocument();
  });

  it("marks People and Access complete after required access is accepted", async () => {
    mockedGetReferralSaasAccountMembershipPosture.mockResolvedValue(mockAcceptedRequiredMembershipPosture());
    mockedGetReferralSaasMembershipActivationReadiness.mockResolvedValue(mockAcceptedRequiredMembershipActivationReadiness());
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs");
    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    const peopleStage = screen.getByRole("link", { name: /People & access/ });
    expect(peopleStage).toHaveAttribute("href", "/admin/referral-saas/account-maintenance/acct-gabs/people");
    expect(peopleStage).toHaveTextContent("ACCESS_READY");
    expect(peopleStage).toHaveClass("complete");
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
    expect(screen.getByText("Optional platform login")).toBeInTheDocument();
    expect(container.textContent).toContain("Finish confirming the required customer responsibilities first.");
    expect(container.textContent).toContain("Only continue here when a confirmed person must sign in to Amplifi.");
    expect(container.textContent).toContain("Next: Add the person who owns this responsibility.");
    fireEvent.click(screen.getByRole("button", { name: "Show access diagnostics" }));
    expect(await screen.findByText("Readiness")).toBeInTheDocument();
    expect(container.textContent).toContain("Contact: CONTACT_REFERENCE_PRESENT");
    expect(screen.getAllByText(/Campaign Manager/i).length).toBeGreaterThan(0);
    expect(screen.getByText("Configure an approved invitation delivery provider before sending invites.")).toBeInTheDocument();
    expect(screen.getAllByText("Gaborone owner").length).toBeGreaterThan(0);
    expect(screen.getAllByText("owner@gabs.example").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Send invite email" })).toBeDisabled();
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
    const deliveryButton = await screen.findByRole("button", { name: "Send invite email" });
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
    expect(await screen.findByText("Invite delivery updated.")).toBeInTheDocument();
    expect(screen.getByText(/No login was activated, no seat was assigned, no permission claims changed/i)).toBeInTheDocument();
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
    expect(container.textContent).toContain("Next: Confirmed for customer work. Assign a platform seat only if this person must sign in.");
    expect(screen.getByText("Optional platform login")).toBeInTheDocument();
    expect(container.textContent).toContain("Finish confirming the required customer responsibilities first.");
    expect(screen.getByText("First assign a platform seat for capacity and audit.")).toBeInTheDocument();
    expect(screen.getByText("Then record whether login is required or not required.")).toBeInTheDocument();
    expect(screen.getByText("Optional platform login steps")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Assign platform seat" })).toBeEnabled();
  });

  it("requests optional platform seat assignment after access has been confirmed", async () => {
    mockedGetReferralSaasAccountMembershipPosture.mockResolvedValue(mockActiveMembershipPosture());
    mockedGetReferralSaasMembershipActivationReadiness
      .mockResolvedValueOnce(mockActiveMembershipActivationReadiness())
      .mockResolvedValue(mockSeatProvisionedMembershipActivationReadiness());
    const { container } = renderWorkspace(
      <ReferralSaasAccountMaintenancePage />,
      "/admin/referral-saas/account-maintenance/acct-gabs/people",
    );

    expect(await screen.findByRole("heading", { name: "People and access" })).toBeInTheDocument();
    const provisioningButton = await screen.findByRole("button", { name: "Assign platform seat" });
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
    expect(await screen.findByText("Platform seat recorded.")).toBeInTheDocument();
    expect(container.textContent).toContain("Seat assigned");
    expect(JSON.stringify(mockedRequestReferralSaasAccessProvisioning.mock.calls)).not.toMatch(
      /tenantCode|sendInvite|credential|authClaims|goLive|wallet|settlement|money/i,
    );
  });

  it("records governed login completion after a platform seat and provider evidence are ready", async () => {
    mockedGetReferralSaasAccountMembershipPosture.mockResolvedValue(mockActiveMembershipPosture());
    mockedGetReferralSaasMembershipActivationReadiness.mockResolvedValue(mockSeatProvisionedMembershipActivationReadiness());
    mockedGetReferralSaasLoginCompletionReadiness.mockResolvedValue(mockLoginCompletionReadiness("LOGIN_COMPLETION_READY"));
    mockedGetReferralSaasTechnicalSetupReadiness.mockResolvedValue(mockTechnicalSetupReadinessWithInviteProvider());
    mockedRequestReferralSaasLoginCompletionIntent.mockResolvedValue(mockLoginCompletionIntent());

    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/people");

    expect(await screen.findByRole("heading", { name: "People and access" })).toBeInTheDocument();
    const loginCompletionButton = await screen.findByRole("button", { name: "Record login completion" });
    expect(loginCompletionButton).toBeEnabled();

    fireEvent.click(loginCompletionButton);

    await waitFor(() => expect(mockedRequestReferralSaasLoginCompletionIntent).toHaveBeenCalledTimes(1));
    expect(mockedRequestReferralSaasLoginCompletionIntent.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      membershipRef: "membership-1",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      loginCompletion: {
        intent: "PLATFORM_LOGIN_REQUIRED",
        identitySubjectRef: "customer-profile-login-identity-acct-gabs-membership-1-owner-gabs-example",
        authProviderRef: "mail-provider-1",
        seatEvidenceRef: "customer-profile-login-seat-evidence-acct-gabs-membership-1-distribution-admin",
        permissionProfile: "REFERRAL_SAAS_ACCOUNT_ADMIN",
        operatorReason:
          "Amplifi Admin recorded governed login completion evidence from the selected customer People and Access page.",
      },
      reasonCode: "CUSTOMER_PROFILE_LOGIN_COMPLETION_INTENT",
      correlationId: "customer-profile-login-completion-acct-gabs",
      idempotencyKey: "customer-profile-login-completion-acct-gabs-membership-1-distribution-admin-platform-login-required",
    });
    expect(await screen.findByText("Login decision recorded.")).toBeInTheDocument();
    expect(screen.getByText(/No invitation email was sent, no credential was created, no auth claim changed/i)).toBeInTheDocument();
    expect(JSON.stringify(mockedRequestReferralSaasLoginCompletionIntent.mock.calls)).not.toMatch(
      /tenantCode|sendInvite|credentialValue|authClaims|goLive|wallet|settlement|money/i,
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
    expect(screen.getByText(/Plan the customer's API, webhook, and message connection/i)).toBeInTheDocument();
    expect(await screen.findAllByText("Draft plan")).toHaveLength(2);
    expect(screen.getByText(/Save the connection plan before verification can start/i)).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Plan" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "Verify" })).toHaveAttribute("aria-selected", "false");
    expect(screen.getByText("1. API connection")).toBeInTheDocument();
    expect(screen.getByText("2. Webhook")).toBeInTheDocument();
    expect(screen.getByText("3. Messages")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Validate plan" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save connection plan" })).toBeInTheDocument();
    expect(screen.getByText("People invite delivery")).toBeInTheDocument();
    expect(screen.getByText("Configure and approve the Email provider for Referral SaaS before sending account access invites.")).toBeInTheDocument();
    expect(screen.getByText("Referral journey messages")).toBeInTheDocument();
    expect(screen.getByText(/Saves a non-secret connection plan and records safe verification checks/i)).toBeInTheDocument();
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
    expect(screen.queryByRole("heading", { name: "Customer readiness" })).not.toBeInTheDocument();
  });

  it("opens Journeys as a customer-scoped configuration page", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/journeys");

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Journey configuration" })).toBeInTheDocument();
    expect(screen.getByText(/Select an approved template, save this customer's draft/i)).toBeInTheDocument();
    expect(await screen.findByText("Standard referral journey")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save journey draft" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Validate draft" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Publish journey version" })).toBeDisabled();
    expect(mockedListReferralSaasJourneyTemplates).toHaveBeenCalledWith({
      statuses: ["APPROVED"],
      limit: 50,
    });
    expect(mockedListReferralSaasAccountJourneyDrafts).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      refType: "external_tenant_ref",
      externalRef: "gabs-platform",
      context: "setup",
      limit: 50,
    });
  });

  it("opens Programmes as the simple customer-scoped configuration workspace", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/programmes");

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Programme workspace" })).toBeInTheDocument();
    expect(screen.getByText(/A programme is the governed package a campaign uses/i)).toBeInTheDocument();
    expect(screen.getByText(/Do this next: Choose the customer product first/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "How this stays simple" })).toBeInTheDocument();
    expect(screen.getByText("Customer product")).toBeInTheDocument();
    expect(screen.getByText("Referral programme")).toBeInTheDocument();
    expect(screen.getByText("Campaign")).toBeInTheDocument();
    expect(screen.getByText("Campaign-specific changes")).toBeInTheDocument();
    expect(screen.getByText("Reporting")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Customer product and offering" })).toBeInTheDocument();
    expect(screen.getByText(/Amplifi package codes stay behind the scenes/i)).toBeInTheDocument();
    fireEvent.change(await screen.findByLabelText("Customer product line"), {
      target: { value: "product-line-001" },
    });
    fireEvent.change(await screen.findByLabelText("Customer product offering"), {
      target: { value: "offering-001" },
    });
    expect((await screen.findAllByText("Gaborone Partners referral programme")).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole("button", { name: "Validate programme" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Publish programme version" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Save programme draft" }));
    await waitFor(() => expect(mockedCreateReferralSaasProgrammeDraft).toHaveBeenCalledTimes(1));
    expect(mockedCreateReferralSaasProgrammeDraft).toHaveBeenCalledWith(
      expect.objectContaining({
        accountRef: "acct-gabs",
        body: expect.objectContaining({
          customerProductLineId: "product-line-001",
          customerProductOfferingId: "offering-001",
          productCode: "REFERRAL_SAAS",
          subProductCode: "RMCA_BUNDLE",
        }),
      }),
    );
    expect(screen.getByText("Published programme versions")).toBeInTheDocument();
    expect(screen.getByText("Programme performance")).toBeInTheDocument();
    expect(screen.getByText(/Journey: Standard referral/i)).toBeInTheDocument();
    expect(screen.queryByText(/journey-version-001/i)).not.toBeInTheDocument();
    expect(screen.getByText("Products measured")).toBeInTheDocument();
    expect(screen.getByText("Campaign changes measured")).toBeInTheDocument();
    expect(screen.queryByText("effectiveRuleSnapshot")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Continue to Campaigns" })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/campaigns",
    );
    expect(mockedGetReferralSaasAccountProgrammeCatalogue).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      refType: "external_tenant_ref",
      externalRef: "gabs-platform",
      context: "setup",
      limit: 50,
    });
    expect(mockedListReferralSaasAccountProgrammes).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      refType: "external_tenant_ref",
      externalRef: "gabs-platform",
      context: "setup",
      includeRetired: true,
      limit: 50,
    });
    expect(mockedGetReferralSaasAccountProgrammeAnalytics).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      refType: "external_tenant_ref",
      externalRef: "gabs-platform",
      context: "setup",
      limit: 50,
    });
  });

  it("opens Products as a business-facing customer catalogue workspace", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/products");

    expect(await screen.findByRole("heading", { name: "Products and offerings" })).toBeInTheDocument();
    expect((await screen.findAllByText("Transactional banking")).length).toBeGreaterThan(0);
    expect(screen.getByText("Easy Account")).toBeInTheDocument();
    expect(screen.getByText("Reference: TRANSACTIONAL_BANKING")).toBeInTheDocument();
    expect(screen.getByText("Reference: EASY_ACCOUNT")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Add product line" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Add offering" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Continue to Programmes" })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/programmes",
    );
    expect(mockedGetReferralSaasCustomerProductCatalogue).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      refType: "external_tenant_ref",
      externalRef: "gabs-platform",
      context: "setup",
    });
  });

  it("saves, validates, and publishes a customer journey draft without live side effects", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/journeys");

    expect(await screen.findByRole("heading", { name: "Journey configuration" })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Milestone codes"), {
      target: { value: "REFERRED, QUALIFIED, WON" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save journey draft" }));

    await waitFor(() => expect(mockedSaveReferralSaasAccountJourneyDraft).toHaveBeenCalledTimes(1));
    expect(mockedSaveReferralSaasAccountJourneyDraft).toHaveBeenCalledWith(
      expect.objectContaining({
        accountRef: "acct-gabs",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: "gabs-platform",
          context: "setup",
        },
        templateCode: "REFERRAL_STANDARD",
        templateVersion: "1.0.0",
      }),
    );
    const saveRequest = mockedSaveReferralSaasAccountJourneyDraft.mock.calls[0][0];
    expect(saveRequest.configurationPayload).toMatchObject({
      milestones: [{ code: "REFERRED" }, { code: "QUALIFIED" }, { code: "WON" }],
      transitions: [
        { from: "REFERRED", to: "QUALIFIED" },
        { from: "QUALIFIED", to: "CONVERTED" },
      ],
      evidence: [{ code: "CUSTOMER_REFERENCE" }, { code: "ACCEPTED_TERMS" }, { code: "OUTCOME_EVENT" }],
      attribution: { attributionWindowDays: 30 },
    });
    expect(JSON.stringify(saveRequest)).not.toMatch(/tenantCode|tenant_code|providerSecret|billing|money/i);

    fireEvent.click(await screen.findByRole("button", { name: "Validate draft" }));
    await waitFor(() => expect(mockedValidateReferralSaasAccountJourneyDraft).toHaveBeenCalledTimes(1));
    expect(await screen.findByText("Simulated path")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Publish journey version" }));
    await waitFor(() => expect(mockedPublishReferralSaasAccountJourneyDraft).toHaveBeenCalledTimes(1));
    expect(await screen.findByText("Published journey version.")).toBeInTheDocument();
  });

  it("validates and saves Integrations configuration without live side effects", async () => {
    mockedGetReferralSaasIntegrationExecutionReadiness
      .mockResolvedValueOnce(mockIntegrationExecutionReadiness())
      .mockResolvedValueOnce(mockReadyIntegrationExecutionReadiness());
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/integrations");

    expect(await screen.findByRole("heading", { name: "Integrations" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Validate plan" }));

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

    fireEvent.click(screen.getByRole("button", { name: "Save connection plan" }));
    await waitFor(() => expect(mockedSaveReferralSaasIntegrationConfiguration).toHaveBeenCalledTimes(1));
    expect(mockedSaveReferralSaasIntegrationConfiguration.mock.calls[0][0]).toMatchObject({
      accountRef: "acct-gabs",
      reasonCode: "CUSTOMER_INTEGRATION_CONFIGURATION",
      correlationId: "customer-profile-integrations-acct-gabs",
    });
    expect(await screen.findByText(/Integrations setup updated/i)).toBeInTheDocument();
    expect(screen.getByText(/Connection plan saved. Run verification checks next/i)).toBeInTheDocument();
    expect(await screen.findByText("Verification checks")).toBeInTheDocument();
    expect(screen.getByText("API access check")).toBeInTheDocument();
    expect(screen.getByText(/governed live verification checks/i)).toBeInTheDocument();
    expect(mockedGetReferralSaasIntegrationExecutionReadiness).toHaveBeenCalledTimes(2);
  });

  it("records API access verification from Integrations when the readiness action is ready", async () => {
    mockedGetReferralSaasIntegrationConfiguration.mockResolvedValue({
      ...mockIntegrationConfigurationRead(),
      integrationConfiguration: mockIntegrationConfigurationSave().integrationConfigurationResult.configuration,
    });
    mockedGetReferralSaasIntegrationExecutionReadiness.mockResolvedValue(mockReadyIntegrationExecutionReadiness());

    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/integrations");

    expect(await screen.findByRole("heading", { name: "Integrations" })).toBeInTheDocument();
    expect(await screen.findAllByText("Ready to verify")).toHaveLength(2);
    fireEvent.click(screen.getByRole("tab", { name: "Verify" }));
    const action = await screen.findByRole("button", { name: "Record API check" });
    fireEvent.click(action);

    await waitFor(() => expect(mockedRecordReferralSaasApiAccessVerification).toHaveBeenCalledTimes(1));
    expect(mockedRecordReferralSaasApiAccessVerification).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      verification: {
        verificationType: "API_ACCESS_VERIFICATION",
        configurationRef: "integration-config-1",
        environment: "LOCAL_DEVELOPMENT",
        authMethod: "API_KEY",
        intendedUseCases: ["CAMPAIGN_READ", "REFERRAL_CODE_VALIDATE", "REPORT_READ"],
        noSecretOrCredentialStorageConfirmed: true,
        noCredentialCreationConfirmed: true,
        noCredentialLifecycleConfirmed: true,
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
      reasonCode: "CUSTOMER_API_ACCESS_VERIFICATION",
      correlationId: "customer-profile-integrations-api-verification-acct-gabs",
      idempotencyKey:
        "customer-profile-integrations-api-verification-acct-gabs-integration-config-1-local-development-api-key-campaign-read-referral-code-validate-report-read",
    });
    expect(JSON.stringify(mockedRecordReferralSaasApiAccessVerification.mock.calls)).not.toMatch(
      /tenantCode|tenant_code|clientSecret|credentialValue|apiKeyValue|webhookSecret/i,
    );
    expect(
      await screen.findByText(/API-access verification evidence was recorded/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/without credential creation/i)).toBeInTheDocument();
    expect(mockedGetReferralSaasIntegrationExecutionReadiness).toHaveBeenCalledTimes(2);
  });

  it("records webhook test evidence from Integrations when the readiness action is ready", async () => {
    mockedGetReferralSaasIntegrationConfiguration.mockResolvedValue({
      ...mockIntegrationConfigurationRead(),
      integrationConfiguration: mockIntegrationConfigurationSave().integrationConfigurationResult.configuration,
    });
    mockedGetReferralSaasIntegrationExecutionReadiness.mockResolvedValue(mockReadyIntegrationExecutionReadiness());

    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/integrations");

    expect(await screen.findByRole("heading", { name: "Integrations" })).toBeInTheDocument();
    expect(await screen.findAllByText("Ready to verify")).toHaveLength(2);
    fireEvent.click(screen.getByRole("tab", { name: "Verify" }));
    const action = await screen.findByRole("button", { name: "Record webhook test" });
    fireEvent.click(action);

    await waitFor(() => expect(mockedRecordReferralSaasWebhookTestDispatch).toHaveBeenCalledTimes(1));
    expect(mockedRecordReferralSaasWebhookTestDispatch).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      webhookTest: {
        testType: "WEBHOOK_TEST_DISPATCH",
        configurationRef: "integration-config-1",
        callbackUrlPresent: true,
        eventCategories: ["CAMPAIGN", "REFERRAL", "PROGRESS"],
        noSecretOrCredentialStorageConfirmed: true,
        noCredentialCreationConfirmed: true,
        noCredentialLifecycleConfirmed: true,
        noWebhookDispatchConfirmed: true,
        noProviderCallConfirmed: true,
        noInviteDeliveryConfirmed: true,
        noMessageProviderDeliveryConfirmed: true,
        noMembershipActivationConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noCampaignActivationConfirmed: true,
        noGoLiveActionConfirmed: true,
        noBillingOrMoneyMovementConfirmed: true,
      },
      reasonCode: "CUSTOMER_WEBHOOK_TEST_DISPATCH",
      correlationId: "customer-profile-integrations-webhook-test-acct-gabs",
      idempotencyKey:
        "customer-profile-integrations-webhook-test-acct-gabs-integration-config-1-http-localhost-8000-webhooks-referral-saas-campaign-referral-progress",
    });
    expect(JSON.stringify(mockedRecordReferralSaasWebhookTestDispatch.mock.calls)).not.toMatch(
      /tenantCode|tenant_code|clientSecret|credentialValue|apiKeyValue|webhookSecret|signing/i,
    );
    expect(await screen.findByText(/Webhook test-dispatch evidence was recorded/i)).toBeInTheDocument();
    expect(screen.getByText(/No webhook was dispatched/i)).toBeInTheDocument();
    expect(mockedGetReferralSaasIntegrationExecutionReadiness).toHaveBeenCalledTimes(2);
  });

  it("records message provider check evidence from Integrations when the readiness action is ready", async () => {
    mockedGetReferralSaasIntegrationConfiguration.mockResolvedValue({
      ...mockIntegrationConfigurationRead(),
      integrationConfiguration: mockIntegrationConfigurationSave().integrationConfigurationResult.configuration,
    });
    mockedGetReferralSaasIntegrationExecutionReadiness.mockResolvedValue(
      mockReadyMessageProviderIntegrationExecutionReadiness(),
    );

    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/integrations");

    expect(await screen.findByRole("heading", { name: "Integrations" })).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText("Optional approved provider reference"), {
      target: { value: "provider-approved-email" },
    });
    fireEvent.click(screen.getByRole("tab", { name: "Verify" }));
    const action = await screen.findByRole("button", { name: "Record provider check" });
    fireEvent.click(action);

    await waitFor(() => expect(mockedRecordReferralSaasMessageProviderTest).toHaveBeenCalledTimes(1));
    expect(mockedRecordReferralSaasMessageProviderTest).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      messageProviderTest: {
        testType: "MESSAGE_PROVIDER_TEST",
        configurationRef: "integration-config-1",
        channels: ["EMAIL"],
        providerRefs: ["provider-approved-email"],
        noSecretOrCredentialStorageConfirmed: true,
        noCredentialCreationConfirmed: true,
        noCredentialLifecycleConfirmed: true,
        noWebhookDispatchConfirmed: true,
        noProviderCallConfirmed: true,
        noInviteDeliveryConfirmed: true,
        noMessageProviderDeliveryConfirmed: true,
        noMembershipActivationConfirmed: true,
        noSeatAssignmentConfirmed: true,
        noAuthClaimChangeConfirmed: true,
        noCampaignActivationConfirmed: true,
        noGoLiveActionConfirmed: true,
        noBillingOrMoneyMovementConfirmed: true,
      },
      reasonCode: "CUSTOMER_MESSAGE_PROVIDER_TEST",
      correlationId: "customer-profile-integrations-message-provider-test-acct-gabs",
      idempotencyKey:
        "customer-profile-integrations-message-provider-test-acct-gabs-integration-config-1-email-provider-approved-email",
    });
    expect(JSON.stringify(mockedRecordReferralSaasMessageProviderTest.mock.calls)).not.toMatch(
      /tenantCode|tenant_code|clientSecret|credentialValue|apiKeyValue|webhookSecret|wallet|settlementAccount|payout/i,
    );
    expect(await screen.findByText(/Message-provider test evidence was recorded/i)).toBeInTheDocument();
    expect(screen.getByText(/No provider was called and no message was sent/i)).toBeInTheDocument();
    expect(mockedGetReferralSaasIntegrationExecutionReadiness).toHaveBeenCalledTimes(2);
  });

  it("records credential setup requests from Integrations without creating credentials", async () => {
    mockedGetReferralSaasIntegrationConfiguration.mockResolvedValue({
      ...mockIntegrationConfigurationRead(),
      integrationConfiguration: mockIntegrationConfigurationSave().integrationConfigurationResult.configuration,
    });
    mockedGetReferralSaasIntegrationExecutionReadiness.mockResolvedValue(mockReadyIntegrationExecutionReadiness());
    mockedListReferralSaasIntegrationCredentialRequests
      .mockResolvedValueOnce(mockIntegrationCredentialRequestList([]))
      .mockResolvedValueOnce(mockIntegrationCredentialRequestList([mockIntegrationCredentialRequest()]));

    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/integrations");

    expect(await screen.findByRole("heading", { name: "Integrations" })).toBeInTheDocument();
    expect(await screen.findAllByText("Ready to verify")).toHaveLength(2);
    fireEvent.click(screen.getByRole("tab", { name: "Verify" }));
    const action = await screen.findByRole("button", { name: "Request credential setup" });
    fireEvent.click(action);

    await waitFor(() => expect(mockedRecordReferralSaasIntegrationCredentialRequest).toHaveBeenCalledTimes(1));
    expect(mockedRecordReferralSaasIntegrationCredentialRequest).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      credentialRequest: {
        requestType: "API_KEY_CREATE",
        capability: "REFERRAL_SAAS_API_ACCESS",
        environment: "LOCAL_DEVELOPMENT",
        intendedUse: ["CAMPAIGN_READ", "REFERRAL_CODE_VALIDATE", "REPORT_READ"],
        requestedFor: {
          customerName: "Gaborone Partners",
          configurationRef: "integration-config-1",
          requestedBy: "AMPLIFI_ADMIN",
          requestReason: "Customer integration credential setup",
        },
      },
      reasonCode: "CUSTOMER_CREDENTIAL_REQUEST",
      correlationId: "customer-profile-integrations-credential-request-acct-gabs",
      idempotencyKey:
        "customer-profile-integrations-credential-request-acct-gabs-integration-config-1-api-key-create-referral-saas-api-access-local-development-campaign-read-referral-code-validate-report-read",
    });
    expect(JSON.stringify(mockedRecordReferralSaasIntegrationCredentialRequest.mock.calls)).not.toMatch(
      /tenantCode|tenant_code|clientSecret|credentialValue|apiKeyValue|webhookSecret|vault|download|money/i,
    );
    expect(await screen.findByText(/Credential setup request was recorded/i)).toBeInTheDocument();
    expect(screen.getByText(/No credential was created, revealed, stored, or sent/i)).toBeInTheDocument();
    await waitFor(() => expect(mockedListReferralSaasIntegrationCredentialRequests).toHaveBeenCalledTimes(2));
  });

  it("reviews credential setup requests from Integrations when they are ready for approval", async () => {
    mockedGetReferralSaasIntegrationConfiguration.mockResolvedValue({
      ...mockIntegrationConfigurationRead(),
      integrationConfiguration: mockIntegrationConfigurationSave().integrationConfigurationResult.configuration,
    });
    mockedGetReferralSaasIntegrationExecutionReadiness.mockResolvedValue(mockReadyIntegrationExecutionReadiness());
    mockedListReferralSaasIntegrationCredentialRequests.mockResolvedValue(
      mockIntegrationCredentialRequestList([
        {
          ...mockIntegrationCredentialRequest(),
          reviewStatus: "READY_FOR_REVIEW",
        },
      ]),
    );

    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/integrations");

    expect(await screen.findByRole("heading", { name: "Integrations" })).toBeInTheDocument();
    expect(await screen.findAllByText("Ready to verify")).toHaveLength(2);
    fireEvent.click(screen.getByRole("tab", { name: "Verify" }));
    await waitFor(() => expect(screen.getByRole("tab", { name: "Verify" })).toHaveAttribute("aria-selected", "true"));
    expect(await screen.findByText(/credential-request-1/)).toBeInTheDocument();
    const action = await screen.findByRole("button", { name: "Approve request" });
    fireEvent.click(action);

    await waitFor(() => expect(mockedRecordReferralSaasIntegrationCredentialReviewDecision).toHaveBeenCalledTimes(1));
    expect(mockedRecordReferralSaasIntegrationCredentialReviewDecision).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      credentialRequestRef: "credential-request-1",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      reviewDecision: {
        decision: "APPROVED",
        reason:
          "Amplifi Admin reviewed this credential setup request and approved it for later governed execution.",
      },
      reasonCode: "CUSTOMER_CREDENTIAL_REQUEST_APPROVED",
      correlationId:
        "customer-profile-integrations-credential-review-acct-gabs-credential-request-1-approved",
      idempotencyKey:
        "customer-profile-integrations-credential-review-acct-gabs-credential-request-1-approved",
    });
    expect(JSON.stringify(mockedRecordReferralSaasIntegrationCredentialReviewDecision.mock.calls)).not.toMatch(
      /tenantCode|tenant_code|clientSecret|credentialValue|apiKeyValue|webhookSecret|vault|download|providerCall|money/i,
    );
    expect(await screen.findByText(/Credential request was approved for later governed execution/i)).toBeInTheDocument();
    await waitFor(() => expect(mockedListReferralSaasIntegrationCredentialRequests).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(mockedGetReferralSaasIntegrationExecutionReadiness).toHaveBeenCalledTimes(2));
  });

  it("checks approved credential setup requests from Integrations without executing credentials", async () => {
    mockedGetReferralSaasIntegrationConfiguration.mockResolvedValue({
      ...mockIntegrationConfigurationRead(),
      integrationConfiguration: mockIntegrationConfigurationSave().integrationConfigurationResult.configuration,
    });
    mockedGetReferralSaasIntegrationExecutionReadiness.mockResolvedValue(mockReadyIntegrationExecutionReadiness());
    mockedListReferralSaasIntegrationCredentialRequests.mockResolvedValue(
      mockIntegrationCredentialRequestList([
        {
          ...mockIntegrationCredentialRequest(),
          reviewStatus: "REVIEW_APPROVED",
        },
      ]),
    );

    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/integrations");

    expect(await screen.findByRole("heading", { name: "Integrations" })).toBeInTheDocument();
    expect(await screen.findAllByText("Ready to verify")).toHaveLength(2);
    fireEvent.click(screen.getByRole("tab", { name: "Verify" }));
    await waitFor(() => expect(screen.getByRole("tab", { name: "Verify" })).toHaveAttribute("aria-selected", "true"));
    expect(await screen.findByText(/credential-request-1/)).toBeInTheDocument();
    const action = await screen.findByRole("button", { name: "Check approved setup" });
    fireEvent.click(action);

    await waitFor(() => expect(mockedRecordReferralSaasIntegrationCredentialExecutionCheck).toHaveBeenCalledTimes(1));
    expect(mockedRecordReferralSaasIntegrationCredentialExecutionCheck).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      credentialRequestRef: "credential-request-1",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      executionCheck: {
        reason:
          "Amplifi Admin checked that this approved credential setup request is ready for later governed execution.",
        reasonCode: "CUSTOMER_CREDENTIAL_EXECUTION_READY_CHECK",
      },
      reasonCode: "CUSTOMER_CREDENTIAL_EXECUTION_READY_CHECK",
      correlationId:
        "customer-profile-integrations-credential-execution-check-acct-gabs-credential-request-1",
      idempotencyKey:
        "customer-profile-integrations-credential-execution-check-acct-gabs-credential-request-1",
    });
    expect(JSON.stringify(mockedRecordReferralSaasIntegrationCredentialExecutionCheck.mock.calls)).not.toMatch(
      /tenantCode|tenant_code|clientSecret|credentialValue|apiKeyValue|webhookSecret|vault|download|providerCall|money/i,
    );
    expect(await screen.findByText(/Approved credential setup was checked for later governed execution/i)).toBeInTheDocument();
    await waitFor(() => expect(mockedListReferralSaasIntegrationCredentialRequests).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(mockedGetReferralSaasIntegrationExecutionReadiness).toHaveBeenCalledTimes(2));
  });

  it("keeps the previous Technical Setup route as an Integrations compatibility alias", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/technical");

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Integrations" })).toBeInTheDocument();
  });

  it("shows provider vault handoff readiness from Integrations without live execution controls", async () => {
    mockedGetReferralSaasIntegrationConfiguration.mockResolvedValue({
      ...mockIntegrationConfigurationRead(),
      integrationConfiguration: mockIntegrationConfigurationSave().integrationConfigurationResult.configuration,
    });
    mockedGetReferralSaasIntegrationExecutionReadiness.mockResolvedValue(mockReadyIntegrationExecutionReadiness());
    mockedListReferralSaasIntegrationCredentialRequests.mockResolvedValue(
      mockIntegrationCredentialRequestList([
        {
          ...mockIntegrationCredentialRequest(),
          reviewStatus: "REVIEW_APPROVED",
        },
      ]),
    );
    mockedGetReferralSaasProviderVaultReadiness.mockResolvedValue(
      mockProviderVaultReadiness("PROVIDER_VAULT_EXECUTION_READY"),
    );

    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/integrations");

    expect(await screen.findByRole("heading", { name: "Integrations" })).toBeInTheDocument();
    expect(await screen.findAllByText("Ready to verify")).toHaveLength(2);
    fireEvent.click(screen.getByRole("tab", { name: "Verify" }));
    await waitFor(() => expect(screen.getByRole("tab", { name: "Verify" })).toHaveAttribute("aria-selected", "true"));

    expect(await screen.findByRole("heading", { name: "Secure provider handoff" })).toBeInTheDocument();
    expect(screen.getByText(/Approved credential request evidence is ready/i)).toBeInTheDocument();
    expect(screen.getAllByText("Ready for handoff").length).toBeGreaterThan(0);
    expect(screen.getByText(/No secret is shown, no credential is created or downloaded/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Run governed provider/i })).not.toBeInTheDocument();
    expect(mockedGetReferralSaasProviderVaultReadiness).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      refType: "external_tenant_ref",
      externalRef: "gabs-platform",
      context: "setup",
    });
    expect(JSON.stringify(mockedGetReferralSaasProviderVaultReadiness.mock.calls)).not.toMatch(
      /tenantCode|tenant_code|clientSecret|credentialValue|apiKeyValue|webhookSecret|download|providerCall|money/i,
    );
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

  it("records selected-customer support cases from the support page", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/support");

    expect(await screen.findByRole("heading", { name: "Gaborone Partners" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Support cases" })).toBeInTheDocument();
    await waitFor(() =>
      expect(mockedListReferralSaasAccountSupportCases).toHaveBeenCalledWith({
        accountRef: "acct-gabs",
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
        limit: 50,
      }),
    );

    fireEvent.change(screen.getByLabelText("What needs help?"), {
      target: { value: "VALIDATION_RECOVERY" },
    });
    fireEvent.change(screen.getByLabelText("Priority"), {
      target: { value: "HIGH" },
    });
    fireEvent.change(screen.getByLabelText("Case title"), {
      target: { value: "Referral code validation failed" },
    });
    fireEvent.change(screen.getByLabelText("What happened?"), {
      target: { value: "The branch pilot cannot validate a safe referral code." },
    });
    fireEvent.change(screen.getByLabelText("Safe evidence type"), {
      target: { value: "LINK_CODE_INSPECTION" },
    });
    fireEvent.change(screen.getByLabelText("Safe evidence reference"), {
      target: { value: "link-check-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Record support case" }));

    await waitFor(() => expect(mockedCreateReferralSaasAccountSupportCase).toHaveBeenCalled());
    expect(mockedCreateReferralSaasAccountSupportCase.mock.calls[0]?.[0]).toEqual(
      expect.objectContaining({
        accountRef: "acct-gabs",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: "gabs-platform",
          context: "setup",
        },
        category: "VALIDATION_RECOVERY",
        priority: "HIGH",
        title: "Referral code validation failed",
        summary: "The branch pilot cannot validate a safe referral code.",
        sourceSurface: "support_hub",
        reasonCode: "CUSTOMER_SUPPORT_CASE_CREATED",
        correlationId: "customer-profile-support-case-acct-gabs",
        evidenceLinks: [
          {
            evidenceType: "LINK_CODE_INSPECTION",
            evidenceRef: "link-check-1",
            safeStatus: "CUSTOMER_SCOPED",
            redactions: ["internal_tenant_identifier"],
          },
        ],
      }),
    );
    expect(await screen.findByText("Support case recorded.")).toBeInTheDocument();
    expect(screen.getByText(/No repair, replay, retry/i)).toBeInTheDocument();
    expect(JSON.stringify(mockedCreateReferralSaasAccountSupportCase.mock.calls)).not.toMatch(
      /tenant_code|credential|billing|money/i,
    );
  });

  it("shows selected-customer support-case repair/replay readiness without unsafe action buttons", async () => {
    mockedListReferralSaasAccountSupportCases.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACCT_GABS",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
      },
      supportCases: [
        {
          caseRef: "case-support-1",
          accountRef: "acct-gabs",
          category: "PROGRESS_DIAGNOSTIC",
          priority: "HIGH",
          status: "OPEN",
          title: "Progress event missing",
          summary: "The customer cannot see progress.",
          sourceSurface: "progress_status",
          createdByRef: "operator",
          evidenceLinks: [
            {
              evidenceType: "PROGRESS_STATUS",
              evidenceRef: "progress-evidence-1",
              safeStatus: "CUSTOMER_SCOPED",
              redactions: ["internal_tenant_identifier"],
            },
          ],
          redactions: ["internal_tenant_identifier"],
        },
      ],
      guardrails: ["NO_REPAIR_REPLAY_RETRY"],
      redactions: ["internal_tenant_identifier"],
      no_tenant_code_exposure_confirmed: true,
      no_product_state_mutation_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });
    mockedGetReferralSaasAccountSupportCaseRepairReplayReadiness.mockResolvedValue({
      status: "ok",
      context: "support",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACCT_GABS",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
      },
      repairReplayReadiness: {
        caseRef: "case-support-1",
        accountRef: "acct-gabs",
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
          caseRef: "case-support-1",
          accountRef: "acct-gabs",
          category: "PROGRESS_DIAGNOSTIC",
          priority: "HIGH",
          status: "OPEN",
          title: "Progress event missing",
          summary: "The customer cannot see progress.",
          sourceSurface: "progress_status",
          createdByRef: "operator",
          evidenceLinks: [
            {
              evidenceType: "PROGRESS_STATUS",
              evidenceRef: "progress-evidence-1",
              safeStatus: "CUSTOMER_SCOPED",
              redactions: ["internal_tenant_identifier"],
            },
          ],
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

    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/support");

    expect(await screen.findByRole("heading", { name: "Support cases" })).toBeInTheDocument();
    expect(await screen.findByText("Repair/replay readiness")).toBeInTheDocument();
    expect(screen.getByText("Review support evidence")).toBeInTheDocument();
    expect(screen.getByText("Replay stored progress evidence")).toBeInTheDocument();
    expect(screen.getByText("progress-evidence-1")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open evidence area" })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/progress?external_tenant_ref=gabs-platform&organisation_ref=gabs-org",
    );
    await waitFor(() =>
      expect(mockedGetReferralSaasAccountSupportCaseRepairReplayReadiness).toHaveBeenCalledWith({
        accountRef: "acct-gabs",
        caseRef: "case-support-1",
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "support",
      }),
    );
    expect(screen.queryByRole("button", { name: /^repair/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^replay/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^retry/i })).not.toBeInTheDocument();
    expect(JSON.stringify(mockedGetReferralSaasAccountSupportCaseRepairReplayReadiness.mock.calls)).not.toMatch(
      /provider_dispatch|credential|auth_claim|campaign_activation|billing|money/i,
    );
  });

  it("adds selected-customer support case notes from the support page", async () => {
    mockedListReferralSaasAccountSupportCases.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACCT_GABS",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
      },
      supportCases: [
        {
          caseRef: "case-support-1",
          accountRef: "acct-gabs",
          category: "VALIDATION_RECOVERY",
          priority: "HIGH",
          status: "OPEN",
          title: "Referral code validation failed",
          summary: "The branch pilot cannot validate a safe referral code.",
          sourceSurface: "support_hub",
          createdByRef: "operator",
          evidenceLinks: [],
          redactions: ["internal_tenant_identifier"],
        },
      ],
      guardrails: ["NO_REPAIR_REPLAY_RETRY"],
      redactions: ["internal_tenant_identifier"],
      no_tenant_code_exposure_confirmed: true,
      no_product_state_mutation_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });
    mockedAddReferralSaasAccountSupportCaseNote.mockResolvedValue({
      status: "ok",
      context: "support",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACCT_GABS",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
      },
      supportCaseLifecycle: {
        commandStatus: "RECORDED",
        supportCase: {
          caseRef: "case-support-1",
          accountRef: "acct-gabs",
          category: "VALIDATION_RECOVERY",
          priority: "HIGH",
          status: "OPEN",
          title: "Referral code validation failed",
          summary: "The branch pilot cannot validate a safe referral code.",
          sourceSurface: "support_hub",
          createdByRef: "operator",
          evidenceLinks: [],
          redactions: ["internal_tenant_identifier"],
        },
        note: {
          noteRef: "note-support-1",
          supportCaseRef: "case-support-1",
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

    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/support");

    expect(await screen.findByText("Referral code validation failed")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Add note" }));
    fireEvent.change(screen.getByLabelText("Support case note"), {
      target: { value: "Called the customer and confirmed the branch test scope." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save note" }));

    await waitFor(() => expect(mockedAddReferralSaasAccountSupportCaseNote).toHaveBeenCalledTimes(1));
    expect(mockedAddReferralSaasAccountSupportCaseNote.mock.calls[0]?.[0]).toEqual(
      expect.objectContaining({
        accountRef: "acct-gabs",
        caseRef: "case-support-1",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: "gabs-platform",
          context: "support",
        },
        noteType: "OPERATOR_NOTE",
        noteText: "Called the customer and confirmed the branch test scope.",
      }),
    );
    expect(mockedAddReferralSaasAccountSupportCaseNote.mock.calls[0]?.[0]).toEqual(
      expect.objectContaining({
        correlationId: expect.stringContaining("support-note-case-support-1-"),
        idempotencyKey: expect.stringContaining("support-note-acct-gabs-case-support-1-"),
      }),
    );
    expect(await screen.findByText("Support case updated.")).toBeInTheDocument();
    expect(screen.getByText(/Note added to Referral code validation failed/i)).toBeInTheDocument();
    expect(JSON.stringify(mockedAddReferralSaasAccountSupportCaseNote.mock.calls)).not.toMatch(
      /tenant_code|credential|billing|money/i,
    );
  });

  it("changes selected-customer support case status from the support page", async () => {
    mockedListReferralSaasAccountSupportCases.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACCT_GABS",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
      },
      supportCases: [
        {
          caseRef: "case-support-1",
          accountRef: "acct-gabs",
          category: "VALIDATION_RECOVERY",
          priority: "HIGH",
          status: "OPEN",
          title: "Referral code validation failed",
          summary: "The branch pilot cannot validate a safe referral code.",
          sourceSurface: "support_hub",
          createdByRef: "operator",
          evidenceLinks: [],
          redactions: ["internal_tenant_identifier"],
        },
      ],
      guardrails: ["NO_REPAIR_REPLAY_RETRY"],
      redactions: ["internal_tenant_identifier"],
      no_tenant_code_exposure_confirmed: true,
      no_product_state_mutation_confirmed: true,
      no_billing_or_money_movement_confirmed: true,
    });
    mockedChangeReferralSaasAccountSupportCaseStatus.mockResolvedValue({
      status: "ok",
      context: "support",
      account: {
        accountId: "acct-gabs",
        accountCode: "ACCT_GABS",
        accountName: "Gaborone Partners",
        accountStatus: "ACTIVE",
      },
      supportCaseLifecycle: {
        commandStatus: "RECORDED",
        supportCase: {
          caseRef: "case-support-1",
          accountRef: "acct-gabs",
          category: "VALIDATION_RECOVERY",
          priority: "HIGH",
          status: "INVESTIGATING",
          title: "Referral code validation failed",
          summary: "The branch pilot cannot validate a safe referral code.",
          sourceSurface: "support_hub",
          createdByRef: "operator",
          evidenceLinks: [],
          redactions: ["internal_tenant_identifier"],
        },
        statusEvent: {
          statusEventRef: "status-support-1",
          supportCaseRef: "case-support-1",
          fromStatus: "OPEN",
          toStatus: "INVESTIGATING",
          transitionReason: "Evidence reviewed and assigned to support.",
          changedByRef: "operator",
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

    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/support");

    expect(await screen.findByText("Referral code validation failed")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Change status" }));
    fireEvent.change(screen.getByLabelText("Support case status"), {
      target: { value: "INVESTIGATING" },
    });
    fireEvent.change(screen.getByLabelText("Support case status reason"), {
      target: { value: "Evidence reviewed and assigned to support." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save status" }));

    await waitFor(() => expect(mockedChangeReferralSaasAccountSupportCaseStatus).toHaveBeenCalledTimes(1));
    expect(mockedChangeReferralSaasAccountSupportCaseStatus.mock.calls[0]?.[0]).toEqual(
      expect.objectContaining({
        accountRef: "acct-gabs",
        caseRef: "case-support-1",
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: "gabs-platform",
          context: "support",
        },
        status: "INVESTIGATING",
        transitionReason: "Evidence reviewed and assigned to support.",
      }),
    );
    expect(mockedChangeReferralSaasAccountSupportCaseStatus.mock.calls[0]?.[0]).toEqual(
      expect.objectContaining({
        correlationId: expect.stringContaining("support-status-case-support-1-"),
        idempotencyKey: expect.stringContaining("support-status-acct-gabs-case-support-1-"),
      }),
    );
    expect(await screen.findByText("Support case updated.")).toBeInTheDocument();
    expect(screen.getByText(/Referral code validation failed moved to Investigating/i)).toBeInTheDocument();
    expect(JSON.stringify(mockedChangeReferralSaasAccountSupportCaseStatus.mock.calls)).not.toMatch(
      /tenant_code|credential|billing|money/i,
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
    fireEvent.change(screen.getByRole("combobox", { name: /Published programme/i }), {
      target: { value: "programme-version-001" },
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
        programmeVersionId: "programme-version-001",
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
    expect(mockedBindReferralSaasAccountCampaignJourneyVersion).not.toHaveBeenCalled();
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
    await waitFor(() => expect(mockedListReferralSaasAccountReportDeliverySchedules).toHaveBeenCalledTimes(1));
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
    expect(mockedListReferralSaasAccountReportDeliverySchedules.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      reportType: "campaign_performance",
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

    fireEvent.click(screen.getByRole("button", { name: /Prepare CSV/i }));
    await waitFor(() => expect(mockedCreateReferralSaasAccountReportExportRequest).toHaveBeenCalledTimes(1));
    expect(mockedCreateReferralSaasAccountReportExportRequest.mock.calls[0][0]).toEqual({
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
      correlationId: "customer-report-export-request-acct-gabs-campaign-performance-camp001-csv",
      idempotencyKey: "customer-report-export-request-acct-gabs-campaign-performance-camp001-csv",
    });
    await waitFor(() => expect(mockedCreateReferralSaasAccountReportExportFile).toHaveBeenCalledTimes(1));
    expect(mockedCreateReferralSaasAccountReportExportFile.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      reportType: "campaign_performance",
      exportRequestId: "export-1",
      correlationId: "customer-report-export-file-acct-gabs-campaign-performance-export-1",
      idempotencyKey: "customer-report-export-file-acct-gabs-campaign-performance-export-1",
    });
    expect(await screen.findByText("campaign-performance-export-1.csv")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Download file/i }));
    await waitFor(() => expect(mockedDownloadReferralSaasAccountReportExportFile).toHaveBeenCalledTimes(1));
    expect(mockedDownloadReferralSaasAccountReportExportFile.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      exportRequestId: "export-1",
      correlationId: "customer-report-export-download-acct-gabs-export-1",
    });
    expect(await screen.findByText("Download started.")).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: "5. Schedule delivery intent" })).toBeInTheDocument();
    expect(screen.getByText(/This does not send a report today/i)).toBeInTheDocument();
    expect(screen.getByText("Intent only")).toBeInTheDocument();
    expect(await screen.findByText("contact-owner")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Recipient contact reference"), {
      target: { value: "contact-owner" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Save schedule intent/i }));
    await waitFor(() => expect(mockedCreateReferralSaasAccountReportDeliverySchedule).toHaveBeenCalledTimes(1));
    expect(mockedCreateReferralSaasAccountReportDeliverySchedule.mock.calls[0][0]).toEqual({
      accountRef: "acct-gabs",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      reportType: "campaign_performance",
      cadence: "weekly",
      timezone: "Africa/Johannesburg",
      format: "csv",
      redactionProfile: "tenant_safe",
      recipientContactRefs: ["contact-owner"],
      retentionDays: 7,
      campaignRef: "CAMP001",
      scheduleStatus: "ready",
      reasonCode: "CUSTOMER_PROFILE_REPORT_DELIVERY_SCHEDULE_UI",
      correlationId:
        "customer-report-delivery-schedule-acct-gabs-campaign-performance-camp001-weekly-africa-johannesburg-csv-7-contact-owner",
      idempotencyKey:
        "customer-report-delivery-schedule-acct-gabs-campaign-performance-camp001-weekly-africa-johannesburg-csv-7-contact-owner",
    });
    expect(await screen.findByText("Schedule intent saved.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Check readiness" }));
    await waitFor(() => expect(mockedGetReferralSaasAccountReportDeliveryScheduleReadiness).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      scheduleId: "schedule-1",
    }));
    fireEvent.click(screen.getByRole("button", { name: "Pause" }));
    await waitFor(() => expect(mockedUpdateReferralSaasAccountReportDeliverySchedule).toHaveBeenCalledWith({
      accountRef: "acct-gabs",
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: "gabs-platform",
        context: "setup",
      },
      scheduleId: "schedule-1",
      scheduleStatus: "paused",
      reasonCode: "CUSTOMER_PROFILE_REPORT_DELIVERY_SCHEDULE_PAUSED",
      correlationId: "customer-report-delivery-schedule-update-acct-gabs-schedule-1-paused",
      idempotencyKey: "customer-report-delivery-schedule-update-acct-gabs-schedule-1-paused",
    }));
    expect(await screen.findByText("Schedule updated.")).toBeInTheDocument();
    expect(screen.queryByText("Reports Target")).not.toBeInTheDocument();
    expect(
      JSON.stringify([
        mockedGetReferralSaasAccountReport.mock.calls,
        mockedCreateReferralSaasAccountReportExportRequest.mock.calls,
        mockedCreateReferralSaasAccountReportExportFile.mock.calls,
        mockedDownloadReferralSaasAccountReportExportFile.mock.calls,
        mockedCreateReferralSaasAccountReportDeliverySchedule.mock.calls,
        mockedUpdateReferralSaasAccountReportDeliverySchedule.mock.calls,
        mockedGetReferralSaasAccountReportDeliveryScheduleReadiness.mock.calls,
      ]),
    ).not.toMatch(/tenantCode|tenant_code|billing|money|credential|campaignActivation/i);
  });

  it("saves selected customer profile settings through the maintenance command", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/settings");

    expect(await screen.findByRole("navigation", { name: "Account establishment stages" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Account establishment" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Organisation/ }));
    expect(screen.getByRole("button", { name: /Organisation/ })).toHaveAttribute("aria-current", "step");
    expect(screen.getByText("ACC-2201")).toBeInTheDocument();
    expect(screen.getByText(/immutable references remain controlled/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Maintain organisation" }));

    fireEvent.change(screen.getByLabelText("Customer name"), {
      target: { value: "Gaborone Partners Updated" },
    });
    fireEvent.change(screen.getByLabelText("Customer type"), {
      target: { value: "ENTERPRISE_CUSTOMER" },
    });
    fireEvent.change(screen.getByLabelText("Industry"), {
      target: { value: "AUTOMOTIVE" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save organisation" }));

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

  it("moves through backend-grounded Account establishment evidence stages", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />, "/admin/referral-saas/account-maintenance/acct-gabs/settings");

    expect(await screen.findByRole("navigation", { name: "Account establishment stages" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Account establishment" })).toBeInTheDocument();
    expect(screen.getByText("Account establishment evidence")).toHaveClass("sr-only");
    fireEvent.click(screen.getByRole("button", { name: /Jurisdiction & environment/ }));
    expect(screen.getByRole("heading", { name: "Jurisdiction and environment" })).toBeInTheDocument();
    expect(screen.getByText("Botswana")).toBeInTheDocument();

    expect(screen.getByRole("link", { name: "Open integrations" })).toHaveClass("secondary");
    fireEvent.click(screen.getByRole("button", { name: "Continue to Agreement" }));
    expect(screen.getByRole("button", { name: /Agreement/ })).toHaveClass("selected");
    expect(screen.getByRole("button", { name: /Organisation/ })).toHaveClass("complete");
    expect(screen.getByRole("heading", { name: "Effective commercial agreement" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open entitlement evidence" })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/commercial",
    );

    fireEvent.click(screen.getByRole("button", { name: "Continue to Activation" }));
    expect(screen.getByRole("heading", { name: /Partner account/ })).toBeInTheDocument();
    expect(screen.getByText("Production decision")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /View activation decision|Review activation/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-maintenance/acct-gabs/health",
    );
  });
  it("keeps prototype workspace destinations scoped to the selected customer context", async () => {
    renderWorkspace(<ReferralSaasAccountMaintenancePage />);
    fireEvent.click(await screen.findByRole("button", { name: /FNB Referral SaaS/ }));
    fireEvent.click(screen.getByRole("link", { name: "Open customer profile" }));
    expect(await screen.findByRole("heading", { name: "Continue in this customer context" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Products & programmes/ })).toHaveAttribute("href", "/admin/referral-saas/account-maintenance/acct-fnb/programmes");
    expect(screen.getByRole("link", { name: /Referral operations/ })).toHaveAttribute("href", "/admin/referral-saas/account-maintenance/acct-fnb/referrals");
    expect(screen.getByRole("link", { name: /Attribution & reporting/ })).toHaveAttribute("href", "/admin/referral-saas/account-maintenance/acct-fnb/attribution");
    expect(screen.getAllByRole("link", { name: /Campaigns/ }).some((link) => link.getAttribute("href") === "/admin/referral-saas/account-maintenance/acct-fnb/campaigns")).toBe(true);
    expect(screen.queryByRole("heading", { name: "What you can do for this customer" })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Readiness summary" })).toBeInTheDocument();
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
