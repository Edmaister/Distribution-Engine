import {
  AlertCircle,
  BarChart3,
  Building2,
  CheckCircle2,
  Download,
  FileJson,
  Link as LinkIcon,
  ListChecks,
  PlugZap,
  Route,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Target,
  Users,
} from "lucide-react";
import { Link, useLocation, useParams } from "react-router-dom";
import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import {
  useReferralSaasAccountCampaignList,
  useReferralSaasAccountCampaignAttribution,
  useReferralSaasAccountCampaignReadiness,
  useReferralSaasAccountDraftSelector,
  useReferralSaasAccountMaintenanceState,
  useReferralSaasAccountMembershipPosture,
  useReferralSaasAccountReferralAttribution,
  useReferralSaasAccountReferralDetail,
  useReferralSaasAccountReferralList,
  useReferralSaasAccountReferrerDetail,
  useReferralSaasAccountReferrerList,
  useReferralSaasIdentityLoginReconciliation,
  useReferralSaasLoginCompletionReadiness,
  useReferralSaasMembershipActivationReadiness,
  useReferralSaasAccountRegistry,
  useReferralSaasCommercialEntitlement,
  useReferralSaasProductionActivation,
  useReferralSaasTechnicalSetupReadiness,
} from "../../api/referralSaasAccountQueries";
import {
  activeSessionRole,
  useBackendSession,
} from "../../auth/useBackendSession";
import {
  issueReferralSaasAccountCampaignCode,
  validateReferralSaasAccountCampaignCode,
  type ReferralSaasLinkRecord,
} from "../../api/endpoints/referralSaasLinks";
import {
  createReferralSaasAccountReportExportFile,
  createReferralSaasAccountReportDeliverySchedule,
  createReferralSaasAccountReportExportRequest,
  deleteReferralSaasAccountReportExportFile,
  downloadReferralSaasAccountReportExportFile,
  getReferralSaasAccountReportDeliveryScheduleReadiness,
  getReferralSaasAccountReport,
  listReferralSaasAccountReportDeliverySchedules,
  previewReferralSaasAccountReportExport,
  updateReferralSaasAccountReportDeliverySchedule,
  type ReferralSaasReportDeliveryCadence,
  type ReferralSaasExportFormat,
  type ReferralSaasReportType,
} from "../../api/endpoints/referralSaasReports";
import {
  addReferralSaasAccountSupportCaseNote,
  assignReferralSaasAccountSupportCase,
  cancelReferralSaasMembershipInvitationIntent,
  changeReferralSaasAccountSupportCaseStatus,
  createReferralSaasAccountSupportCase,
  createReferralSaasAccountCampaignSetup,
  createReferralSaasProgrammeDraft,
  decideReferralSaasProgrammeDraftReview,
  getReferralSaasAccountProgrammeAnalytics,
  getReferralSaasAccountProgrammeCatalogue,
  getReferralSaasAccountSupportCaseRepairReplayReadiness,
  listReferralSaasAccountJourneyDrafts,
  listReferralSaasAccountProgrammes,
  listReferralSaasAccountSupportCases,
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
  recordReferralSaasAccountCampaignLifecycleCommand,
  requestReferralSaasAccountCampaignActivation,
  requestReferralSaasAccountFoundationActivation,
  requestReferralSaasAccessProvisioning,
  requestReferralSaasLoginCompletionIntent,
  requestReferralSaasMembershipActivation,
  requestReferralSaasMembershipInvitationDelivery,
  saveReferralSaasAccountJourneyDraft,
  saveReferralSaasIntegrationConfiguration,
  submitReferralSaasProgrammeDraftReview,
  submitReferralSaasAccountCampaignReview,
  updateReferralSaasProgrammeDraft,
  updateReferralSaasMembershipInvitationIntent,
  updateReferralSaasAccountCampaignPolicySettings,
  validateReferralSaasAccountJourneyDraft,
  validateReferralSaasProgrammeDraft,
  validateReferralSaasIntegrationConfiguration,
  type ReferralSaasAccountCampaignActivationResponse,
  type ReferralSaasAccountCampaignReviewResponse,
  type ReferralSaasAccountCampaignPolicySettingsResponse,
  type ReferralSaasCustomerJourneyDraft,
  type ReferralSaasCustomerJourneyDraftValidationResponse,
  type ReferralSaasCustomerJourneyPublishResponse,
  type ReferralSaasCustomerProductBindingSummary,
  type ReferralSaasCustomerProductLineSummary,
  type ReferralSaasCustomerProductOfferingSummary,
  type ReferralSaasJourneyTemplateCatalogueItem,
  type ReferralSaasJourneyTemplateVersionSummary,
  type ReferralSaasProgrammeDraft,
  type ReferralSaasProgrammeLifecycleResponse,
  type ReferralSaasProgrammeValidationResponse,
  type ReferralSaasProgrammeVersion,
  updateReferralSaasAccountProfile,
  getReferralSaasIntegrationConfiguration,
  getReferralSaasIntegrationExecutionReadiness,
  getReferralSaasProviderVaultReadiness,
  listReferralSaasIntegrationCredentialRequests,
  type ReferralSaasAccountCampaignSetupCreateResponse,
  type ReferralSaasCampaignLifecycleAction,
  type ReferralSaasSupportCase,
  type ReferralSaasSupportCaseAssignmentResponse,
  type ReferralSaasSupportCaseCreateResponse,
  type ReferralSaasSupportCaseLifecycleResponse,
  type ReferralSaasSupportCaseRepairReplayAction,
  type ReferralSaasSupportCaseRepairReplayReadiness,
  type ReferralSaasSupportCaseRepairReplayReadinessResponse,
  type ReferralSaasCommercialEntitlementResponse,
  type ReferralSaasProductionActivationResponse,
  type ReferralSaasTechnicalSetupReadinessResponse,
  type ReferralSaasCampaignAttributionProjection,
  type ReferralSaasReferralCreditProjection,
  type ReferralSaasReferrerCreditProjection,
} from "../../api/endpoints/referralSaasAccounts";
import type { CampaignReadinessOperation } from "../../api/endpoints/adminCampaignReadiness";
import { DataTable } from "../../components/DataTable";
import { ErrorPanel } from "../../components/ErrorPanel";
import { KpiCard } from "../../components/KpiCard";
import { LoadingState } from "../../components/LoadingState";
import { StatusBadge } from "../../components/StatusBadge";
import {
  asArray,
  formatDisplay,
  getNestedValue,
  getValue,
  statusTone,
  useRefreshContext,
} from "../pageUtils";

const defaultExternalTenantRef = "demo-platform-operator";
const defaultOrganisationRef = "demo-organisation";
const defaultOperatingMarket = "South Africa";

type AccountRegistry = NonNullable<ReturnType<typeof useReferralSaasAccountRegistry>["data"]>;
type AccountRegistryItem = AccountRegistry["accounts"][number];
type StatusTone = "success" | "warning" | "danger" | "info" | "neutral";
type CustomerModule =
  | "home"
  | "health"
  | "settings"
  | "people"
  | "commercial"
  | "integrations"
  | "technical"
  | "journeys"
  | "programmes"
  | "campaigns"
  | "referrals"
  | "referrers"
  | "links"
  | "reports"
  | "support"
  | "attribution"
  | "progress";
type ProfileDraft = {
  accountId: string;
  accountName: string;
  operatingJurisdictionCode: string;
  customerType: string;
  industry: string;
};

type CampaignSetupDraft = {
  name: string;
  segment: string;
  programmeVersionId: string;
  startsAt: string;
  endsAt: string;
  maxUses: string;
};

type CampaignPolicySettingsDraft = {
  campaignCode: string;
  version: string;
  attributionWindowDays: string;
  eligibilityRule: string;
  productWindowDays: string;
  requiresAcceptedTerms: string;
  rewardVisibilityNotes: string;
};

type CampaignReviewDraft = {
  campaignCode: string;
  setupSummary: string;
  operatorNotes: string;
  decisionReason: string;
  reviewerRef: string;
  decision: "APPROVED" | "BLOCKED";
};

type SupportCaseDraft = {
  category: string;
  priority: string;
  title: string;
  summary: string;
  evidenceType: string;
  evidenceRef: string;
};

type SupportCaseLifecycleDraft = {
  caseRef: string;
  action: "note" | "status";
  noteType: string;
  noteText: string;
  status: string;
  transitionReason: string;
};

type SupportCaseLifecycleMutationInput = SupportCaseLifecycleDraft & {
  requestKey: string;
};

type SupportCaseAssignmentDraft = {
  caseRef: string;
  assigneeRef: string;
  assignmentReason: string;
};

type SupportCaseAssignmentMutationInput = SupportCaseAssignmentDraft & {
  requestKey: string;
};

type ScopedAccountActivationResult = {
  accountId: string;
  message: string;
};

type IntegrationConfigurationDraft = {
  environment: string;
  intendedAuthMethod: string;
  allowedUse: string[];
  callbackUrl: string;
  eventCategories: string[];
  inviteDeliveryChannel: string;
  inviteProviderApprovalRef: string;
  referralMessageChannels: string[];
};

const integrationUseCaseOptions = [
  { value: "CAMPAIGN_READ", label: "Read campaign setup" },
  { value: "CAMPAIGN_WRITE", label: "Create or update campaign setup" },
  { value: "REFERRAL_CODE_ISSUE", label: "Issue referral codes" },
  { value: "REFERRAL_CODE_VALIDATE", label: "Validate referral codes" },
  { value: "PROGRESS_EVENT_INGEST", label: "Receive progress events" },
  { value: "ATTRIBUTION_READ", label: "Read attribution trace" },
  { value: "REPORT_READ", label: "Read reports" },
  { value: "INVITE_DELIVERY", label: "Prepare invite delivery" },
  { value: "REFERRAL_MESSAGE_DELIVERY", label: "Prepare referral messages" },
];

const integrationEventOptions = [
  { value: "CAMPAIGN", label: "Campaign events" },
  { value: "REFERRAL", label: "Referral events" },
  { value: "PROGRESS", label: "Progress events" },
  { value: "ATTRIBUTION", label: "Attribution events" },
  { value: "REPORTING", label: "Reporting events" },
  { value: "SUPPORT", label: "Support events" },
];

const integrationChannelOptions = [
  { value: "EMAIL", label: "Email" },
  { value: "SMS", label: "SMS" },
  { value: "WHATSAPP", label: "WhatsApp" },
  { value: "USSD", label: "USSD" },
];

const customerFunctions = [
  {
    title: "Account health",
    copy: "See what is OK, what is stopping you, and what can wait.",
    letsYou: "Know if this customer is ready to test referrals.",
    route: "health",
    icon: ShieldCheck,
    status: "Needs attention",
    tone: "warning" as StatusTone,
  },
  {
    title: "Customer settings",
    copy: "Review company details, customer identifiers, and operating market.",
    letsYou: "Keep profile work inside this customer context.",
    route: "settings",
    icon: Building2,
    status: "Needs attention",
    tone: "warning" as StatusTone,
  },
  {
    title: "Plan and entitlement",
    copy: "Review whether this customer is allowed for production Referral SaaS use.",
    letsYou: "Keep setup, launch approval, billing, and money boundaries clear.",
    route: "commercial",
    icon: SlidersHorizontal,
    status: "Needs attention",
    tone: "warning" as StatusTone,
  },
  {
    title: "Programmes",
    copy: "Build the versioned package campaigns will use.",
    letsYou: "Combine a published journey with approved product, incentive, and setup defaults.",
    route: "programmes",
    icon: FileJson,
    status: "Needs setup",
    tone: "warning" as StatusTone,
  },
  {
    title: "Campaigns",
    copy: "Set up or review referral campaigns for this customer.",
    letsYou: "Create campaign tests once blockers are clear.",
    route: "campaigns",
    icon: Target,
    status: "Ready",
    tone: "success" as StatusTone,
  },
  {
    title: "Referrals",
    copy: "Inspect referral journeys for this customer.",
    letsYou: "See referral status, missing evidence, and safe timeline anchors.",
    route: "referrals",
    icon: ListChecks,
    status: "Ready",
    tone: "success" as StatusTone,
  },
  {
    title: "Referrers",
    copy: "See who is driving referrals without exposing raw identity.",
    letsYou: "Group referral activity by safe referrer labels and dimensions.",
    route: "referrers",
    icon: Users,
    status: "Ready",
    tone: "success" as StatusTone,
  },
  {
    title: "Links and codes",
    copy: "Issue, share, and validate referral codes.",
    letsYou: "Run real referral entry tests for this customer.",
    route: "links",
    icon: LinkIcon,
    status: "Ready",
    tone: "success" as StatusTone,
  },
  {
    title: "Reports",
    copy: "View referral and campaign performance.",
    letsYou: "See results once reporting setup is finished.",
    route: "reports",
    icon: BarChart3,
    status: "Can wait",
    tone: "warning" as StatusTone,
  },
  {
    title: "People and access",
    copy: "See who can manage this customer account.",
    letsYou: "Put the right owner or campaign manager in place.",
    route: "people",
    icon: Users,
    status: "Needs attention",
    tone: "warning" as StatusTone,
  },
  {
    title: "Integrations",
    copy: "Set up the customer's API, webhook, and message-provider readiness.",
    letsYou: "Know what technical connections are still needed before live invites or message testing.",
    route: "integrations",
    icon: PlugZap,
    status: "Needs attention",
    tone: "warning" as StatusTone,
  },
  {
    title: "Journeys",
    copy: "Choose an approved journey template and prepare this customer's version.",
    letsYou: "Configure milestones, evidence, rewards, and attribution before campaign binding.",
    route: "journeys",
    icon: Route,
    status: "Needs setup",
    tone: "warning" as StatusTone,
  },
  {
    title: "Support hub",
    copy: "Investigate problems for this customer.",
    letsYou: "Trace issues without losing customer context.",
    route: "support",
    icon: ShieldCheck,
    status: "Ready",
    tone: "success" as StatusTone,
  },
  {
    title: "Attribution",
    copy: "Explain why a referral or outcome was attributed.",
    letsYou: "Answer who got credit for this customer.",
    route: "attribution",
    icon: Search,
    status: "Ready",
    tone: "success" as StatusTone,
  },
  {
    title: "Progress status",
    copy: "Check journey milestones for referrals.",
    letsYou: "See how far referred customers have got.",
    route: "progress",
    icon: ListChecks,
    status: "Ready",
    tone: "success" as StatusTone,
  },
];

const configurationProofSteps = [
  {
    title: "Customer product",
    copy: "What this customer sells or wants referrals for, such as an account, insurance product, or partner offer.",
    route: "settings" as CustomerModule,
    action: "Review customer settings",
  },
  {
    title: "Referral programme",
    copy: "The reusable rule package: journey, product scope, default attribution, and approved incentive references.",
    route: "programmes" as CustomerModule,
    action: "Open programmes",
  },
  {
    title: "Campaign",
    copy: "The time-bound market activity that uses a published programme for a channel, audience, and date window.",
    route: "campaigns" as CustomerModule,
    action: "Open campaigns",
  },
  {
    title: "Campaign-specific changes",
    copy: "Approved differences for one campaign only, such as a reward, date, audience, or attribution-window change.",
    route: "campaigns" as CustomerModule,
    action: "Review campaign changes",
  },
  {
    title: "Reporting",
    copy: "The read-only view that separates customer product, programme, campaign, and approved changes in results.",
    route: "reports" as CustomerModule,
    action: "Open reports",
  },
];

function customerFunctionActionLabel(tone: StatusTone, status: string): string {
  const normalizedStatus = status.toLowerCase();
  if (tone === "success" || normalizedStatus === "ready") {
    return "Ready to use";
  }
  if (normalizedStatus.includes("can wait")) {
    return "Review when ready";
  }
  if (normalizedStatus.includes("needs")) {
    return "Fix this";
  }
  return "Open page";
}

const readinessCategoryMap = [
  { code: "ACCOUNT_PROFILE", label: "Account profile" },
  { code: "TENANT_LINK", label: "Tenant link" },
  { code: "MEMBERSHIP", label: "Membership and roles" },
  { code: "CAMPAIGN_READINESS", label: "Campaign readiness" },
  { code: "REPORTING_BASELINE", label: "Reporting baseline" },
];

const customerReportOptions: { value: ReferralSaasReportType; label: string; copy: string }[] = [
  {
    value: "campaign_performance",
    label: "Campaign performance",
    copy: "Campaign-level referral activity and conversion signals.",
  },
  {
    value: "referral_funnel",
    label: "Referral funnel",
    copy: "Where referrals are entering, progressing, and completing.",
  },
  {
    value: "journey_performance",
    label: "Journey performance",
    copy: "High-value event stages, attribution gaps, and completion gaps.",
  },
  {
    value: "link_code_performance",
    label: "Links and codes",
    copy: "Issued referral entry points, status, and usage signals.",
  },
  {
    value: "attribution_quality",
    label: "Attribution quality",
    copy: "Evidence quality for who gets credit.",
  },
  {
    value: "progress_event_health",
    label: "Progress event health",
    copy: "Journey-event ingestion health and missing evidence.",
  },
];

const accessRoleOptions = [
  {
    label: "Account owner",
    roleFamily: "DISTRIBUTION_ADMIN",
    permissionSet: "REFERRAL_SAAS_ACCOUNT_ADMIN",
    copy: "Owns customer setup decisions and can manage day-to-day Referral SaaS operations.",
  },
  {
    label: "Campaign manager",
    roleFamily: "CAMPAIGN_MANAGER",
    permissionSet: "REFERRAL_SAAS_CAMPAIGN_MANAGER",
    copy: "Manages referral campaigns for this customer once setup is ready.",
  },
  {
    label: "Support analyst",
    roleFamily: "SUPPORT",
    permissionSet: "REFERRAL_SAAS_SUPPORT",
    copy: "Can investigate customer support evidence without changing setup or campaign state.",
  },
];

const supportCaseCategoryOptions = [
  {
    value: "VALIDATION_RECOVERY",
    label: "Validation or code issue",
    copy: "A referral code, link, or validation result needs investigation.",
  },
  {
    value: "PROGRESS_DIAGNOSTIC",
    label: "Progress status issue",
    copy: "A referral journey milestone looks missing, delayed, or unclear.",
  },
  {
    value: "ATTRIBUTION_REVIEW",
    label: "Attribution question",
    copy: "The customer needs to understand who got credit and why.",
  },
  {
    value: "READINESS_BLOCKER",
    label: "Readiness blocker",
    copy: "Something is blocking safe campaign or referral testing.",
  },
  {
    value: "REPORTING_FRESHNESS",
    label: "Reporting question",
    copy: "A report, export, or freshness signal needs checking.",
  },
  {
    value: "INTEGRATION_HEALTH",
    label: "Integration setup issue",
    copy: "API, webhook, invite, or message-provider setup needs investigation.",
  },
  {
    value: "ACCESS_SCOPE",
    label: "People or access issue",
    copy: "Customer access, responsibility, or login setup needs investigation.",
  },
  {
    value: "MANUAL_REVIEW_REQUIRED",
    label: "Manual review",
    copy: "A human review is needed before deciding the next action.",
  },
];

const supportCasePriorityOptions = [
  { value: "LOW", label: "Low", copy: "Useful context, but not blocking current customer work." },
  { value: "MEDIUM", label: "Medium", copy: "Needs attention, but safe testing can usually continue." },
  { value: "HIGH", label: "High", copy: "Blocks safe customer testing or a key operator workflow." },
  { value: "CRITICAL", label: "Critical", copy: "Stops launch-readiness or creates urgent customer risk." },
];

const supportCaseEvidenceOptions = [
  { value: "", label: "No evidence link yet" },
  { value: "LINK_CODE_INSPECTION", label: "Link or code inspection" },
  { value: "ATTRIBUTION_TRACE", label: "Attribution trace" },
  { value: "PROGRESS_STATUS", label: "Progress status" },
  { value: "CAMPAIGN_READINESS", label: "Campaign readiness" },
  { value: "REPORTING_EVIDENCE", label: "Reporting evidence" },
  { value: "TECHNICAL_SETUP", label: "Integration setup" },
  { value: "PEOPLE_ACCESS", label: "People and access" },
  { value: "OPERATOR_NOTE", label: "Operator note" },
];

const supportCaseNoteTypeOptions = [
  { value: "OPERATOR_NOTE", label: "Operator note" },
  { value: "CUSTOMER_UPDATE", label: "Customer update" },
  { value: "EVIDENCE_SUMMARY", label: "Evidence summary" },
  { value: "RESOLUTION_NOTE", label: "Resolution note" },
];

const supportCaseStatusOptions = [
  { value: "OPEN", label: "Open" },
  { value: "INVESTIGATING", label: "Investigating" },
  { value: "WAITING", label: "Waiting" },
  { value: "RESOLVED", label: "Resolved" },
  { value: "CLOSED", label: "Closed" },
];

const customerTypeOptions = [
  {
    value: "DIRECT_CUSTOMER",
    label: "Direct customer",
    copy: "The customer buys and operates Referral SaaS directly.",
  },
  {
    value: "ENTERPRISE_CUSTOMER",
    label: "Enterprise customer",
    copy: "The customer has multiple teams, brands, or business units using the product.",
  },
  {
    value: "PARTNER_MANAGED_CUSTOMER",
    label: "Partner-managed customer",
    copy: "A partner or agency manages Referral SaaS activity for this customer.",
  },
];

const industryOptions = [
  { value: "BANKING_FINANCIAL_SERVICES", label: "Banking and financial services" },
  { value: "INSURANCE", label: "Insurance" },
  { value: "TELECOMS", label: "Telecommunications" },
  { value: "RETAIL_ECOMMERCE", label: "Retail and ecommerce" },
  { value: "AUTOMOTIVE", label: "Automotive" },
  { value: "REAL_ESTATE", label: "Real estate" },
  { value: "EDUCATION", label: "Education" },
  { value: "HEALTHCARE", label: "Healthcare" },
  { value: "TRAVEL_HOSPITALITY", label: "Travel and hospitality" },
  { value: "OTHER", label: "Other" },
];

const jurisdictionOptions = [
  { code: "ZA", label: "South Africa" },
  { code: "BW", label: "Botswana" },
  { code: "NA", label: "Namibia" },
  { code: "ZM", label: "Zambia" },
  { code: "OTHER", label: "Other operating market" },
];

export function ReferralSaasAccountMaintenancePage() {
  const { accountId, customerModule, customerSubModule } = useParams<{
    accountId?: string;
    customerModule?: string;
    customerSubModule?: string;
  }>();
  const location = useLocation();
  const { refreshKey } = useRefreshContext();
  const backendSession = useBackendSession(refreshKey, "referral-saas-admin");
  const isAmplifiAdmin = activeSessionRole(backendSession.session, backendSession.status) === "admin";
  const [draftExternalTenantRef, setDraftExternalTenantRef] = useState(defaultExternalTenantRef);
  const [draftOrganisationRef, setDraftOrganisationRef] = useState(defaultOrganisationRef);
  const [appliedExternalTenantRef, setAppliedExternalTenantRef] = useState(defaultExternalTenantRef);
  const [appliedOrganisationRef, setAppliedOrganisationRef] = useState(defaultOrganisationRef);
  const [selectedOperatingMarket, setSelectedOperatingMarket] = useState(defaultOperatingMarket);
  const [pendingAccountId, setPendingAccountId] = useState<string | null>(null);
  const [accessDisplayName, setAccessDisplayName] = useState("");
  const [accessEmail, setAccessEmail] = useState("");
  const [accessRoleLabel, setAccessRoleLabel] = useState(accessRoleOptions[0].label);
  const [isAccessFormOpen, setIsAccessFormOpen] = useState(false);
  const [editingMembershipRef, setEditingMembershipRef] = useState<string | null>(null);
  const [accessCreateAttemptKey, setAccessCreateAttemptKey] = useState(() =>
    newAccessCreateAttemptKey(),
  );
  const [manualAcceptanceEvidence, setManualAcceptanceEvidence] = useState("");
  const [showAccessDiagnostics, setShowAccessDiagnostics] = useState(false);
  const [accessResult, setAccessResult] = useState<string | null>(null);
  const [accessLifecycleResult, setAccessLifecycleResult] = useState<string | null>(null);
  const [deliveryResult, setDeliveryResult] = useState<string | null>(null);
  const [activationResult, setActivationResult] = useState<string | null>(null);
  const [provisioningResult, setProvisioningResult] = useState<string | null>(null);
  const [loginCompletionResult, setLoginCompletionResult] = useState<string | null>(null);
  const [accountActivationResult, setAccountActivationResult] =
    useState<ScopedAccountActivationResult | null>(null);
  const [profileDraft, setProfileDraft] = useState<ProfileDraft | null>(null);
  const [profileResult, setProfileResult] = useState<string | null>(null);
  const [campaignSetupDraft, setCampaignSetupDraft] = useState<CampaignSetupDraft>({
    name: "",
    segment: "Referral acquisition",
    programmeVersionId: "",
    startsAt: "",
    endsAt: "",
    maxUses: "",
  });
  const [campaignSetupResult, setCampaignSetupResult] =
    useState<ReferralSaasAccountCampaignSetupCreateResponse | null>(null);
  const [campaignPolicyDraft, setCampaignPolicyDraft] = useState<CampaignPolicySettingsDraft>({
    campaignCode: "",
    version: "1",
    attributionWindowDays: "30",
    eligibilityRule: "NEW_CUSTOMER_ONLY",
    productWindowDays: "30",
    requiresAcceptedTerms: "true",
    rewardVisibilityNotes: "Reward visibility configured for setup only.",
  });
  const [campaignPolicyResult, setCampaignPolicyResult] =
    useState<ReferralSaasAccountCampaignPolicySettingsResponse | null>(null);
  const [campaignReviewDraft, setCampaignReviewDraft] = useState<CampaignReviewDraft>({
    campaignCode: "",
    setupSummary: "Campaign setup and policy settings are ready for review.",
    operatorNotes: "",
    decisionReason: "Campaign setup, policy settings, and readiness evidence reviewed.",
    reviewerRef: "amplifi-admin",
    decision: "APPROVED",
  });
  const [campaignReviewResult, setCampaignReviewResult] =
    useState<ReferralSaasAccountCampaignReviewResponse | null>(null);
  const [supportCaseDraft, setSupportCaseDraft] = useState<SupportCaseDraft>({
    category: supportCaseCategoryOptions[0].value,
    priority: "MEDIUM",
    title: "",
    summary: "",
    evidenceType: "",
    evidenceRef: "",
  });
  const [supportCaseResult, setSupportCaseResult] =
    useState<ReferralSaasSupportCaseCreateResponse | null>(null);
  const [supportCaseLifecycleDraft, setSupportCaseLifecycleDraft] =
    useState<SupportCaseLifecycleDraft | null>(null);
  const [supportCaseLifecycleResult, setSupportCaseLifecycleResult] =
    useState<ReferralSaasSupportCaseLifecycleResponse | null>(null);
  const [supportCaseAssignmentDraft, setSupportCaseAssignmentDraft] =
    useState<SupportCaseAssignmentDraft | null>(null);
  const [supportCaseAssignmentResult, setSupportCaseAssignmentResult] =
    useState<ReferralSaasSupportCaseAssignmentResponse | null>(null);
  const [supportReadinessCaseRef, setSupportReadinessCaseRef] = useState("");
  const scopeChanged =
    draftExternalTenantRef.trim() !== appliedExternalTenantRef ||
    draftOrganisationRef.trim() !== appliedOrganisationRef;
  const canCheckScope = Boolean(draftExternalTenantRef.trim() && draftOrganisationRef.trim() && scopeChanged);
  const selectedModule = normalizeCustomerModule(customerModule);

  const {
    data: accountRegistry,
    error: accountRegistryError,
    isLoading: isAccountRegistryLoading,
    refetch: refetchAccountRegistry,
  } = useReferralSaasAccountRegistry(50, refreshKey);

  const accountItems = accountRegistry?.accounts || [];
  const selectedAccount =
    accountItems.find((account) => account.accountId === accountId) ||
    findSelectedAccount(accountItems, appliedExternalTenantRef, appliedOrganisationRef);
  const selectedExternalTenantRef = selectedAccount
    ? selectedAccount.primaryExternalTenantRef ||
      findAccountExternalRef(selectedAccount.externalReferences, "external_tenant_ref")
    : appliedExternalTenantRef;
  const selectedOrganisationRef = selectedAccount
    ? findAccountExternalRef(selectedAccount.externalReferences, "organisation_ref")
    : appliedOrganisationRef;
  const { data, error, isLoading } = useReferralSaasAccountMaintenanceState(
    selectedExternalTenantRef,
    selectedOrganisationRef,
    refreshKey,
  );
  const {
    data: draftSelector,
    error: draftSelectorError,
    isLoading: isDraftSelectorLoading,
  } = useReferralSaasAccountDraftSelector(selectedExternalTenantRef, selectedOrganisationRef, refreshKey);
  const {
    data: membershipPosture,
    refetch: refetchMembershipPosture,
  } = useReferralSaasAccountMembershipPosture(
    selectedExternalTenantRef,
    Boolean(accountId && selectedAccount && selectedExternalTenantRef),
    refreshKey,
  );
  const {
    data: activationReadiness,
    refetch: refetchActivationReadiness,
  } = useReferralSaasMembershipActivationReadiness(
    selectedAccount?.accountId || "",
    selectedExternalTenantRef,
    Boolean(accountId && selectedAccount && selectedExternalTenantRef),
    refreshKey,
  );
  const {
    data: identityLoginReconciliation,
    refetch: refetchIdentityLoginReconciliation,
  } = useReferralSaasIdentityLoginReconciliation(
    selectedAccount?.accountId || "",
    selectedExternalTenantRef,
    Boolean(accountId && selectedAccount && selectedExternalTenantRef),
    refreshKey,
  );
  const {
    data: technicalSetupReadiness,
    error: technicalSetupError,
    isLoading: isTechnicalSetupLoading,
  } = useReferralSaasTechnicalSetupReadiness(
    selectedAccount?.accountId || "",
    selectedExternalTenantRef,
    Boolean(accountId && selectedAccount && selectedExternalTenantRef),
    refreshKey,
  );
  const {
    data: commercialEntitlement,
    error: commercialEntitlementError,
    isLoading: isCommercialEntitlementLoading,
  } = useReferralSaasCommercialEntitlement(
    selectedAccount?.accountId || "",
    selectedExternalTenantRef,
    Boolean(accountId && selectedAccount && selectedExternalTenantRef),
    refreshKey,
  );
  const {
    data: productionActivation,
    error: productionActivationError,
    isLoading: isProductionActivationLoading,
  } = useReferralSaasProductionActivation(
    selectedAccount?.accountId || "",
    selectedExternalTenantRef,
    Boolean(accountId && selectedAccount && selectedExternalTenantRef),
    refreshKey,
  );
  const campaignProgrammesQuery = useQuery({
    queryKey: [
      "referral-saas",
      "campaign-programmes",
      selectedAccount?.accountId,
      selectedExternalTenantRef,
      refreshKey,
    ],
    queryFn: () =>
      listReferralSaasAccountProgrammes({
        accountRef: selectedAccount?.accountId || "",
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "setup",
        includeRetired: false,
        limit: 50,
      }),
    enabled: Boolean(accountId && selectedAccount && selectedExternalTenantRef),
    retry: false,
  });
  const loginReadinessMembershipRefs =
    activationReadiness?.activationReadiness.items
      .filter((item) => item.membershipStatus === "ACTIVE")
      .map((item) => item.membershipRef)
      .filter(Boolean) || [];
  const {
    data: loginCompletionReadiness,
    refetch: refetchLoginCompletionReadiness,
  } = useReferralSaasLoginCompletionReadiness(
    selectedAccount?.accountId || "",
    loginReadinessMembershipRefs,
    selectedExternalTenantRef,
    Boolean(accountId && selectedAccount && selectedExternalTenantRef && loginReadinessMembershipRefs.length),
    refreshKey,
  );
  const supportCasesQuery = useQuery({
    queryKey: [
      "referral-saas-account-support-cases",
      selectedAccount?.accountId,
      selectedExternalTenantRef,
      refreshKey,
    ],
    queryFn: () =>
      listReferralSaasAccountSupportCases({
        accountRef: selectedAccount?.accountId || "",
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "setup",
        limit: 50,
      }),
    enabled: Boolean(
      selectedModule === "support" && accountId && selectedAccount && selectedExternalTenantRef,
    ),
  });
  const supportCases = supportCasesQuery.data?.supportCases || [];
  const selectedSupportReadinessCase =
    supportCases.find((supportCase) => supportCase.caseRef === supportReadinessCaseRef) ||
    supportCases[0];
  const supportRepairReplayReadinessQuery = useQuery({
    queryKey: [
      "referral-saas-account-support-case-repair-replay-readiness",
      selectedAccount?.accountId,
      selectedSupportReadinessCase?.caseRef,
      selectedExternalTenantRef,
      refreshKey,
    ],
    queryFn: () =>
      getReferralSaasAccountSupportCaseRepairReplayReadiness({
        accountRef: selectedAccount?.accountId || "",
        caseRef: selectedSupportReadinessCase?.caseRef || "",
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "support",
      }),
    enabled: Boolean(
      selectedModule === "support" &&
        accountId &&
        selectedAccount &&
        selectedExternalTenantRef &&
        selectedSupportReadinessCase?.caseRef,
    ),
  });
  const refreshPeopleAccessReadModels = async () => {
    await Promise.all([
      refetchMembershipPosture(),
      refetchActivationReadiness(),
      refetchLoginCompletionReadiness(),
      refetchIdentityLoginReconciliation(),
    ]);
  };
  const accessMutation = useMutation({
    mutationFn: recordReferralSaasMembershipInvitationIntent,
    onSuccess: async (response) => {
      const savedRole =
        accessRoleOptions.find(
          (option) => option.roleFamily === response.invitation.membership.roleFamily,
        )?.label || formatDisplay(response.invitation.membership.roleFamily);
      await refreshPeopleAccessReadModels();
      setAccessResult(
        `${savedRole} access recorded as ${formatDisplay(
          response.invitation.membership.status,
        )}. No invitation email, login activation, seat assignment, or auth claim change was performed.`,
      );
      resetAccessForm();
    },
  });
  const accessUpdateMutation = useMutation({
    mutationFn: updateReferralSaasMembershipInvitationIntent,
    onSuccess: async (response) => {
      const savedRole =
        accessRoleOptions.find(
          (option) => option.roleFamily === response.invitation.membership.roleFamily,
        )?.label || formatDisplay(response.invitation.membership.roleFamily);
      await refreshPeopleAccessReadModels();
      setAccessLifecycleResult(
        `${savedRole} access changes saved. ${response.invitation.lifecycle.nextAction} No invitation email, login activation, seat assignment, or auth claim change was performed.`,
      );
      resetAccessForm();
    },
  });
  const accessCancelMutation = useMutation({
    mutationFn: cancelReferralSaasMembershipInvitationIntent,
    onSuccess: async (response) => {
      const savedRole =
        accessRoleOptions.find(
          (option) => option.roleFamily === response.invitation.membership.roleFamily,
        )?.label || formatDisplay(response.invitation.membership.roleFamily);
      await refreshPeopleAccessReadModels();
      setAccessLifecycleResult(
        `${savedRole} access intent removed from the active setup path. ${response.invitation.lifecycle.nextAction}`,
      );
      resetAccessForm();
    },
  });
  const deliveryMutation = useMutation({
    mutationFn: requestReferralSaasMembershipInvitationDelivery,
    onSuccess: async (response) => {
      await refreshPeopleAccessReadModels();
      const role = formatDisplay(response.deliveryRequest.membership.roleFamily);
      const deliveryStatus = response.deliveryRequest.delivery.status;
      const providerRef = response.deliveryRequest.delivery.providerDeliveryRef;
      const providerStatus = response.deliveryRequest.delivery.providerStatus;
      const providerDetail = providerRef
        ? ` Provider delivery reference: ${providerRef}.`
        : providerStatus
          ? ` Provider status: ${providerStatus}.`
          : "";
      const deliveryCopy =
        deliveryStatus === "INVITATION_DELIVERY_SENT"
          ? `${role} invite email was sent by the approved provider.${providerDetail} Wait for the person to accept access. No login was activated, no seat was assigned, no permission claims changed, and no money moved.`
          : deliveryStatus === "INVITATION_DELIVERY_FAILED"
            ? `${role} invite email could not be sent.${providerDetail} ${response.deliveryRequest.delivery.nextAction} No login was activated, no seat was assigned, no permission claims changed, and no money moved.`
            : `${role} invite email was not sent. ${response.deliveryRequest.delivery.nextAction} No login was activated, no seat was assigned, no permission claims changed, and no money moved.`;
      setDeliveryResult(
        deliveryCopy,
      );
    },
  });
  const activationMutation = useMutation({
    mutationFn: requestReferralSaasMembershipActivation,
    onSuccess: async (response) => {
      await refreshPeopleAccessReadModels();
      setActivationResult(
        `${formatDisplay(response.activationRequest.membership.roleFamily)} access returned ${formatDisplay(
          response.activationRequest.activation.status,
        )}. ${response.activationRequest.activation.nextAction} No invite email was sent, no seat was assigned, no auth claim changed, and no money moved.`,
      );
      resetAccessForm();
    },
  });
  const provisioningMutation = useMutation({
    mutationFn: requestReferralSaasAccessProvisioning,
    onSuccess: async (response) => {
      await refreshPeopleAccessReadModels();
      const seatStatus = response.accessProvisioning.seat.seatAssignmentStatus;
      const seatOutcome =
        seatStatus === "SEAT_ASSIGNED" ? "Platform seat assigned." : "Platform seat not assigned yet.";
      setProvisioningResult(
        `${formatDisplay(response.accessProvisioning.membership.roleFamily)}: ${seatOutcome} ${response.accessProvisioning.provisioning.nextAction} No invitation email was sent, no credential was created, no login permission changed, no campaign was activated, and no money moved.`,
      );
    },
  });
  const loginCompletionMutation = useMutation({
    mutationFn: requestReferralSaasLoginCompletionIntent,
    onSuccess: async (response) => {
      await refreshPeopleAccessReadModels();
      setLoginCompletionResult(
        `${formatDisplay(response.loginCompletionIntent.membership.roleFamily)} login status returned ${formatDisplay(
          response.loginCompletionIntent.loginCompletionStatus,
        )}. ${response.loginCompletionIntent.loginCompletion.nextAction} No invitation email was sent, no credential was created, no auth claim changed, no campaign was activated, no go-live status changed, and no money moved.`,
      );
    },
  });
  const accountFoundationActivationMutation = useMutation({
    mutationFn: requestReferralSaasAccountFoundationActivation,
    onSuccess: async (response) => {
      await Promise.all([
        refetchAccountRegistry(),
        refetchMembershipPosture(),
        refetchActivationReadiness(),
      ]);
      setAccountActivationResult({
        accountId: response.activation.accountId,
        message: `${response.activation.accountName} foundation is ${formatDisplay(
          response.activation.accountStatus,
        )}; tenant link is ${formatDisplay(
          response.activation.tenantLinkStatus || "UNKNOWN",
        )}; ${formatAreaCount(
          response.activation.seatCapacity.createdSeatCount,
          "seat",
        )} are available for later provisioning. No membership was changed, no seat was assigned, no invite email was sent, no credential was created, no auth claim changed, no campaign was activated, and no money moved.`,
      });
    },
  });
  const profileMutation = useMutation({
    mutationFn: updateReferralSaasAccountProfile,
    onSuccess: (response) => {
      setProfileResult(
        `${response.profile.accountName} was updated. Customer identifiers stayed unchanged, and no account activation, membership, campaign, credential, go-live, or money action was performed.`,
      );
      void refetchAccountRegistry();
    },
  });
  const campaignSetupMutation = useMutation({
    mutationFn: createReferralSaasAccountCampaignSetup,
    onSuccess: (response) => {
      setCampaignSetupResult(response);
    },
  });
  const campaignPolicyMutation = useMutation({
    mutationFn: updateReferralSaasAccountCampaignPolicySettings,
    onSuccess: (response) => {
      setCampaignPolicyResult(response);
    },
  });
  const campaignReviewSubmitMutation = useMutation({
    mutationFn: submitReferralSaasAccountCampaignReview,
    onSuccess: (response) => {
      setCampaignReviewResult(response);
    },
  });
  const campaignReviewDecisionMutation = useMutation({
    mutationFn: recordReferralSaasAccountCampaignReviewDecision,
    onSuccess: (response) => {
      setCampaignReviewResult(response);
    },
  });
  const supportCaseMutation = useMutation({
    mutationFn: createReferralSaasAccountSupportCase,
    onSuccess: async (response) => {
      setSupportCaseResult(response);
      setSupportCaseDraft({
        category: supportCaseCategoryOptions[0].value,
        priority: "MEDIUM",
        title: "",
        summary: "",
        evidenceType: "",
        evidenceRef: "",
      });
      await supportCasesQuery.refetch();
    },
  });
  const supportCaseLifecycleMutation = useMutation({
    mutationFn: (draft: SupportCaseLifecycleMutationInput) => {
      if (!selectedAccount) {
        throw new Error("Select a customer before working support cases.");
      }
      const accountScope = {
        refType: "external_tenant_ref" as const,
        externalRef: selectedExternalTenantRef,
        context: "support" as const,
      };
      const idempotencySuffix = draft.requestKey;
      if (draft.action === "note") {
        return addReferralSaasAccountSupportCaseNote({
          accountRef: selectedAccount.accountId,
          caseRef: draft.caseRef,
          accountScope,
          noteType: draft.noteType,
          noteText: draft.noteText,
          correlationId: `support-note-${draft.caseRef}-${idempotencySuffix}`,
          idempotencyKey: `support-note-${selectedAccount.accountId}-${draft.caseRef}-${idempotencySuffix}`,
        });
      }
      return changeReferralSaasAccountSupportCaseStatus({
        accountRef: selectedAccount.accountId,
        caseRef: draft.caseRef,
        accountScope,
        status: draft.status,
        transitionReason: draft.transitionReason,
        correlationId: `support-status-${draft.caseRef}-${idempotencySuffix}`,
        idempotencyKey: `support-status-${selectedAccount.accountId}-${draft.caseRef}-${idempotencySuffix}`,
      });
    },
    onSuccess: async (response) => {
      setSupportCaseLifecycleResult(response);
      setSupportCaseLifecycleDraft(null);
      await supportCasesQuery.refetch();
    },
  });
  const supportCaseAssignmentMutation = useMutation({
    mutationFn: (draft: SupportCaseAssignmentMutationInput) => {
      if (!selectedAccount) {
        throw new Error("Select a customer before assigning support cases.");
      }
      return assignReferralSaasAccountSupportCase({
        accountRef: selectedAccount.accountId,
        caseRef: draft.caseRef,
        accountScope: {
          refType: "external_tenant_ref",
          externalRef: selectedExternalTenantRef,
          context: "support",
        },
        assigneeRef: draft.assigneeRef,
        assignmentReason: draft.assignmentReason,
        correlationId: `support-assignment-${draft.caseRef}-${draft.requestKey}`,
        idempotencyKey: `support-assignment-${selectedAccount.accountId}-${draft.caseRef}-${draft.requestKey}`,
      });
    },
    onSuccess: async (response) => {
      setSupportCaseAssignmentResult(response);
      setSupportCaseAssignmentDraft(null);
      await supportCasesQuery.refetch();
    },
  });
  const pendingAccount = accountItems.find((account) => account.accountId === pendingAccountId);
  const operatingMarkets = getOperatingMarkets(accountItems);
  const accountsForMarket = accountItems.filter(
    (account) => operatingMarketFromAccount(account).name === selectedOperatingMarket,
  );
  const readiness = data?.readiness;
  const summary = readiness?.summary;
  const categories = asArray(readiness?.categories || []);
  const readyCount = toCount(summary?.ready_count);
  const blockedCount = toCount(summary?.blocked_count);
  const missingEvidenceCount = toCount(summary?.missing_evidence_count);
  const goLiveDisabledCount = toCount(summary?.go_live_disabled_count);
  const overallStatus = formatDisplay(readiness?.overall_status || "go_live_disabled");
  const customerName = selectedAccount?.accountName || formatDisplay(appliedOrganisationRef);
  const selectedCustomerPath = selectedAccount
    ? `/admin/referral-saas/account-maintenance/${encodeURIComponent(selectedAccount.accountId)}`
    : "/admin/referral-saas/account-maintenance";
  const customerQuery = `?external_tenant_ref=${encodeURIComponent(
    selectedExternalTenantRef,
  )}&organisation_ref=${encodeURIComponent(selectedOrganisationRef)}`;
  const isAccountFoundationActive =
    (selectedAccount?.accountStatus || "").toUpperCase() === "ACTIVE";
  const canActivateAccountFoundation = Boolean(
    isAmplifiAdmin && selectedAccount && selectedExternalTenantRef && !isAccountFoundationActive,
  );
  const requestedCampaignCode = new URLSearchParams(location.search).get("campaign") || "";
  const selectedProfileDraft =
    selectedAccount && profileDraft?.accountId === selectedAccount.accountId
      ? profileDraft
      : {
          accountId: selectedAccount?.accountId || "",
          accountName: selectedAccount?.accountName || "",
          operatingJurisdictionCode: selectedAccount?.operatingJurisdictionCode || "ZA",
          customerType: "DIRECT_CUSTOMER",
          industry: "BANKING_FINANCIAL_SERVICES",
        };
  const activeAccessRows = (membershipPosture?.membershipPosture.memberships || []).filter(
    (membership) => !["DISABLED", "ARCHIVED"].includes(getValue(membership, ["status"], "")),
  );
  const missingAccessRoleRows = (activationReadiness?.activationReadiness.missingRoleFamilies || [])
    .filter(
      (roleFamily) =>
        !activeAccessRows.some(
          (membership) => getValue(membership, ["roleFamily"], "") === roleFamily,
        ),
    )
    .map((roleFamily) => {
      const role = roleOptionForFamily(roleFamily);
      return {
        isMissingRole: true,
        membershipRef: `missing-${roleFamily}`,
        subject: "Add a work email for this responsibility",
        displayName: role.label,
        roleFamily,
        permissionSet: role.permissionSet,
        status: "MISSING",
        deliveryStatus: "WAITING_FOR_PERSON",
        recipientContactStatus: "CONTACT_REFERENCE_MISSING",
      };
    });
  const peopleAccessRows = [...activeAccessRows, ...missingAccessRoleRows];
  const activationReadinessByMembershipRef = new Map(
    (activationReadiness?.activationReadiness.items || []).map((item) => [item.membershipRef, item]),
  );
  const editingAccessRow = editingMembershipRef
    ? peopleAccessRows.find((row) => getValue(row, ["membershipRef"], "") === editingMembershipRef)
    : undefined;
  const editingAccessReadiness = editingMembershipRef
    ? activationReadinessByMembershipRef.get(editingMembershipRef)
    : undefined;
  const activeAccessCount = activeAccessRows.filter(
    (membership) => getValue(membership, ["status"], "") === "ACTIVE",
  ).length;
  const missingAccessRoleCount = missingAccessRoleRows.length;
  const hasAcceptedRequiredAccess =
    activationReadiness?.activationReadiness.overallStatus === "ACCESS_READY" ||
    (missingAccessRoleCount === 0 && activeAccessCount > 0);
  const effectiveBlockedCount = Math.max(0, blockedCount - (hasAcceptedRequiredAccess && blockedCount > 0 ? 1 : 0));
  const effectiveMissingEvidenceCount = Math.max(
    0,
    missingEvidenceCount - (hasAcceptedRequiredAccess && missingEvidenceCount > 0 ? 1 : 0),
  );
  const effectiveWaitingCount = Math.max(0, effectiveMissingEvidenceCount - effectiveBlockedCount);
  const doNext = getCustomerNextActions({
    blockedCount: effectiveBlockedCount,
    missingEvidenceCount: effectiveMissingEvidenceCount,
    hasAcceptedRequiredAccess,
    commercialBlocked: Boolean(commercialEntitlement?.commercialEntitlement.productionActivationBlocked),
    hasSeatProvisioningWork: Boolean(
      activationReadiness?.activationReadiness.items.some(
        (item) => item.provisioningReadiness === "READY_TO_PROVISION_SEAT",
      ),
    ),
  });
  const stoppingAction = doNext[0];
  const waitingAction = doNext.find((action) => action.priority === "Later") || doNext[doNext.length - 1];
  const peopleAccessStatus =
    missingAccessRoleCount > 0
      ? `Still need ${formatList(missingAccessRoleRows.map((row) => roleOptionForFamily(getValue(row, ["roleFamily"], "")).label))}.`
      : activeAccessCount > 0
        ? "Required people are confirmed. Campaign work can continue; platform login can be set up later."
        : "People are named, but accepted access is still outstanding.";
  const loginSetupRows = activationReadiness?.activationReadiness.items.filter(
    (item) => item.provisioningReadiness === "READY_TO_PROVISION_SEAT" || item.provisioningReadiness === "SEAT_ASSIGNED",
  ) || [];
  const loginCompletionReadinessByMembershipRef = new Map(
    (loginCompletionReadiness || []).map((item) => [
      item.loginCompletionReadiness.membershipRef,
      item.loginCompletionReadiness,
    ]),
  );
  const identityLoginReconciliationByMembershipRef = new Map(
    (identityLoginReconciliation?.identityLoginReconciliation.people || []).map((person) => [
      person.membershipRef,
      person,
    ]),
  );

  useEffect(() => {
    if (
      selectedModule === "campaigns" &&
      (customerSubModule === "settings" || customerSubModule === "review") &&
      requestedCampaignCode &&
      (campaignPolicyDraft.campaignCode !== requestedCampaignCode ||
        campaignReviewDraft.campaignCode !== requestedCampaignCode)
    ) {
      setCampaignPolicyDraft((current) => ({
        ...current,
        campaignCode: requestedCampaignCode,
      }));
      setCampaignReviewDraft((current) => ({
        ...current,
        campaignCode: requestedCampaignCode,
      }));
      setCampaignPolicyResult(null);
      setCampaignReviewResult(null);
    }
  }, [
    campaignPolicyDraft.campaignCode,
    campaignReviewDraft.campaignCode,
    customerSubModule,
    requestedCampaignCode,
    selectedModule,
  ]);

  function updateProfileDraft(values: Partial<Omit<ProfileDraft, "accountId">>) {
    if (!selectedAccount) {
      return;
    }
    setProfileDraft({
      ...selectedProfileDraft,
      accountId: selectedAccount.accountId,
      ...values,
    });
    setProfileResult(null);
  }

  function submitScope(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextExternalTenantRef = draftExternalTenantRef.trim();
    const nextOrganisationRef = draftOrganisationRef.trim();
    if (!nextExternalTenantRef || !nextOrganisationRef) {
      return;
    }
    setAppliedExternalTenantRef(nextExternalTenantRef);
    setAppliedOrganisationRef(nextOrganisationRef);
    setPendingAccountId(null);
  }

  function selectOperatingMarket(marketName: string) {
    setSelectedOperatingMarket(marketName);
    setPendingAccountId(null);
  }

  function stageAccount(account: AccountRegistryItem) {
    setPendingAccountId(account.accountId);
  }

  function resetAccessForm() {
    setAccessDisplayName("");
    setAccessEmail("");
    setAccessRoleLabel(accessRoleOptions[0].label);
    setEditingMembershipRef(null);
    setAccessCreateAttemptKey(newAccessCreateAttemptKey());
    setManualAcceptanceEvidence("");
    setIsAccessFormOpen(false);
  }

  function roleOptionForLabel(label: string) {
    return accessRoleOptions.find((option) => option.label === label) || accessRoleOptions[0];
  }

  function roleOptionForFamily(roleFamily: string) {
    return (
      accessRoleOptions.find((option) => option.roleFamily === roleFamily) ||
      accessRoleOptions[0]
    );
  }

  function startAddAccessIntent(roleFamily?: string) {
    setAccessResult(null);
    setAccessLifecycleResult(null);
    setAccessDisplayName("");
    setAccessEmail("");
    setAccessRoleLabel(roleFamily ? roleOptionForFamily(roleFamily).label : accessRoleOptions[0].label);
    setEditingMembershipRef(null);
    setAccessCreateAttemptKey(newAccessCreateAttemptKey());
    setManualAcceptanceEvidence("");
    setIsAccessFormOpen(true);
  }

  function startEditAccessIntent(row: Record<string, unknown>) {
    const membershipRef = getValue(row, ["membershipRef"], "");
    const roleFamily = getValue(row, ["roleFamily"], "");
    if (!membershipRef) {
      return;
    }
    setAccessResult(null);
    setAccessLifecycleResult(null);
    setAccessDisplayName(formatDisplay(getValue(row, ["displayName"], "")));
    setAccessEmail(getValue(row, ["subject"], ""));
    setAccessRoleLabel(roleOptionForFamily(roleFamily).label);
    setEditingMembershipRef(membershipRef);
    setManualAcceptanceEvidence("");
    setIsAccessFormOpen(true);
  }

  async function submitAccessIntent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedEmail = accessEmail.trim().toLowerCase();
    if (!selectedAccount || !selectedExternalTenantRef || !isValidEmail(cleanedEmail)) {
      return;
    }
    const selectedRole = roleOptionForLabel(accessRoleLabel);
    const emailHash = await sha256Hex(cleanedEmail);
    const requestBase = {
      accountRef: selectedAccount.accountId,
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "setup",
      },
      actor: {
        actorType: "USER",
        subject: cleanedEmail,
        emailHash,
        displayName: accessDisplayName.trim() || cleanedEmail,
      },
      membership: {
        roleFamily: selectedRole.roleFamily,
        permissionSet: selectedRole.permissionSet,
        tenantScope: "PRIMARY_ACCOUNT_TENANT",
      },
      correlationId: `customer-profile-access-${selectedAccount.accountId}`,
    } as const;

    if (editingMembershipRef) {
      accessUpdateMutation.mutate({
        accountRef: requestBase.accountRef,
        membershipRef: editingMembershipRef,
        accountScope: requestBase.accountScope,
        actor: {
          emailHash,
          displayName: requestBase.actor.displayName,
        },
        membership: {
          roleFamily: selectedRole.roleFamily,
          permissionSet: selectedRole.permissionSet,
        },
        reasonCode: "CUSTOMER_PROFILE_ACCESS_INTENT_UPDATE",
        correlationId: requestBase.correlationId,
        idempotencyKey: safeIdempotencyKey(
          "customer-profile-access-update",
          selectedAccount.accountId,
          editingMembershipRef,
          cleanedEmail,
          requestBase.actor.displayName,
          selectedRole.roleFamily,
        ),
      });
      return;
    }

    accessMutation.mutate({
      ...requestBase,
      reasonCode: "CUSTOMER_PROFILE_ACCESS_MAINTENANCE",
      idempotencyKey: safeIdempotencyKey(
        "customer-profile-access",
        selectedAccount.accountId,
        cleanedEmail,
        requestBase.actor.displayName,
        selectedRole.roleFamily,
        accessCreateAttemptKey,
      ),
    });
  }

  function removeAccessIntent(membershipRef: string, roleFamily: string) {
    if (!selectedAccount || !selectedExternalTenantRef || !membershipRef) {
      return;
    }
    accessCancelMutation.mutate({
      accountRef: selectedAccount.accountId,
      membershipRef,
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "setup",
      },
      reasonCode: "CUSTOMER_PROFILE_ACCESS_INTENT_CANCEL",
      correlationId: `customer-profile-access-cancel-${selectedAccount.accountId}`,
      idempotencyKey: `customer-profile-access-cancel-${selectedAccount.accountId}-${membershipRef}-${roleFamily}`
        .toLowerCase()
        .replace(/[^a-z0-9-]+/g, "-"),
    });
  }

  function requestInviteDeliveryCheck(membershipRef: string, roleFamily: string) {
    const approvedProviderRef = inviteDeliveryProviderRef(technicalSetupReadiness);
    if (!selectedAccount || !selectedExternalTenantRef || !membershipRef || !approvedProviderRef) {
      return;
    }
    deliveryMutation.mutate({
      accountRef: selectedAccount.accountId,
      membershipRef,
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "setup",
      },
      delivery: {
        providerRef: approvedProviderRef,
        channel: "EMAIL",
        templateRef: "referral-saas-account-invite-v1",
      },
      reasonCode: "CUSTOMER_PROFILE_INVITE_DELIVERY_REQUEST",
      correlationId: `customer-profile-invite-delivery-${selectedAccount.accountId}`,
      idempotencyKey: `customer-profile-invite-delivery-${selectedAccount.accountId}-${membershipRef}-${roleFamily}`
        .toLowerCase()
        .replace(/[^a-z0-9-]+/g, "-"),
    });
  }

  function requestAccessActivation(membershipRef: string, subject: string, roleFamily: string) {
    if (!selectedAccount || !selectedExternalTenantRef || !membershipRef || !subject) {
      return;
    }
    activationMutation.mutate({
      accountRef: selectedAccount.accountId,
      membershipRef,
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "setup",
      },
      activation: {
        acceptedSubject: subject,
        acceptanceEvidenceRef: `customer-profile-accepted-${selectedAccount.accountId}-${membershipRef}`,
      },
      reasonCode: "CUSTOMER_PROFILE_ACCESS_ACCEPTANCE",
      correlationId: `customer-profile-access-activation-${selectedAccount.accountId}`,
      idempotencyKey: `customer-profile-access-activation-${selectedAccount.accountId}-${membershipRef}-${roleFamily}`
        .toLowerCase()
        .replace(/[^a-z0-9-]+/g, "-"),
    });
  }

  function requestManualAccessAcceptance() {
    const selectedRole = roleOptionForLabel(accessRoleLabel);
    const cleanedEmail = accessEmail.trim().toLowerCase();
    const evidence = manualAcceptanceEvidence.trim();
    if (
      !isAmplifiAdmin ||
      !selectedAccount ||
      !selectedExternalTenantRef ||
      !editingMembershipRef ||
      !isValidEmail(cleanedEmail) ||
      !evidence
    ) {
      return;
    }
    activationMutation.mutate({
      accountRef: selectedAccount.accountId,
      membershipRef: editingMembershipRef,
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "setup",
      },
      activation: {
        acceptedSubject: cleanedEmail,
        acceptanceEvidenceRef: safeIdempotencyKey(
          "manual-access-acceptance",
          selectedAccount.accountId,
          editingMembershipRef,
          cleanedEmail,
          evidence,
        ),
      },
      reasonCode: "AMPLIFI_ADMIN_MANUAL_ACCESS_ACCEPTANCE",
      correlationId: `customer-profile-access-activation-${selectedAccount.accountId}`,
      idempotencyKey: safeIdempotencyKey(
        "customer-profile-access-activation",
        selectedAccount.accountId,
        editingMembershipRef,
        cleanedEmail,
        evidence,
        selectedRole.roleFamily,
      ),
    });
  }

  function requestAccessProvisioning(membershipRef: string, roleFamily: string) {
    if (!selectedAccount || !selectedExternalTenantRef || !membershipRef) {
      return;
    }
    const seatType = seatTypeForRoleFamily(roleFamily);
    provisioningMutation.mutate({
      accountRef: selectedAccount.accountId,
      membershipRef,
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "setup",
      },
      provisioning: {
        seatType,
        seatAssignmentEvidenceRef: safeIdempotencyKey(
          "customer-profile-seat-provisioning-evidence",
          selectedAccount.accountId,
          membershipRef,
          roleFamily,
        ),
        operatorNotes:
          "Amplifi Admin requested governed seat provisioning from the selected customer People and Access page.",
      },
      reasonCode: "CUSTOMER_PROFILE_ACCESS_PROVISIONING_REQUEST",
      correlationId: `customer-profile-access-provisioning-${selectedAccount.accountId}`,
      idempotencyKey: safeIdempotencyKey(
        "customer-profile-access-provisioning",
        selectedAccount.accountId,
        membershipRef,
        roleFamily,
        seatType,
      ),
    });
  }

  function requestLoginCompletion(
    membershipRef: string,
    roleFamily: string,
    subject: string,
    intent: "PLATFORM_LOGIN_REQUIRED" | "LOGIN_NOT_REQUIRED",
  ) {
    if (!selectedAccount || !selectedExternalTenantRef || !membershipRef) {
      return;
    }
    const authProviderRef = intent === "PLATFORM_LOGIN_REQUIRED"
      ? approvedAuthProviderRef(technicalSetupReadiness)
      : "";
    loginCompletionMutation.mutate({
      accountRef: selectedAccount.accountId,
      membershipRef,
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "setup",
      },
      loginCompletion: {
        intent,
        identitySubjectRef: subject
          ? safeIdempotencyKey("customer-profile-login-identity", selectedAccount.accountId, membershipRef, subject)
          : undefined,
        authProviderRef: authProviderRef || undefined,
        seatEvidenceRef: safeIdempotencyKey(
          "customer-profile-login-seat-evidence",
          selectedAccount.accountId,
          membershipRef,
          roleFamily,
        ),
        permissionProfile: permissionProfileForRoleFamily(roleFamily),
        operatorReason:
          intent === "PLATFORM_LOGIN_REQUIRED"
            ? "Amplifi Admin recorded governed login completion evidence from the selected customer People and Access page."
            : "Amplifi Admin recorded that this confirmed customer contact does not need platform login.",
      },
      reasonCode: "CUSTOMER_PROFILE_LOGIN_COMPLETION_INTENT",
      correlationId: `customer-profile-login-completion-${selectedAccount.accountId}`,
      idempotencyKey: safeIdempotencyKey(
        "customer-profile-login-completion",
        selectedAccount.accountId,
        membershipRef,
        roleFamily,
        intent.toLowerCase(),
      ),
    });
  }

  function activateAccountFoundation() {
    if (!selectedAccount || !selectedExternalTenantRef) {
      return;
    }
    const activationKey = `customer-profile-account-foundation-activation-${selectedAccount.accountId}`;
    accountFoundationActivationMutation.mutate({
      accountRef: selectedAccount.accountId,
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "setup",
      },
      activation: {
        seatTypes: ["ADMIN", "OPERATOR"],
      },
      reasonCode: "CUSTOMER_ACCOUNT_FOUNDATION_ACTIVATION",
      correlationId: activationKey,
      idempotencyKey: `${activationKey}-v1`,
    });
  }

  function submitProfileSettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedAccount || !selectedProfileDraft.accountName.trim()) {
      return;
    }
    profileMutation.mutate({
      accountRef: selectedAccount.accountId,
      profile: {
        accountName: selectedProfileDraft.accountName,
        accountType: selectedAccount.accountType || "ORGANISATION",
        operatingJurisdictionCode: selectedProfileDraft.operatingJurisdictionCode,
        customerType: selectedProfileDraft.customerType,
        industry: selectedProfileDraft.industry,
      },
      correlationId: `customer-profile-settings-${selectedAccount.accountId}`,
      idempotencyKey: `customer-profile-settings-${selectedAccount.accountId}-${selectedProfileDraft.accountName}-${selectedProfileDraft.operatingJurisdictionCode}-${selectedProfileDraft.customerType}-${selectedProfileDraft.industry}`
        .toLowerCase()
        .replace(/[^a-z0-9-]+/g, "-"),
    });
  }

  function updateCampaignSetupDraft(values: Partial<CampaignSetupDraft>) {
    setCampaignSetupDraft((current) => ({
      ...current,
      ...values,
    }));
    setCampaignSetupResult(null);
  }

  function updateCampaignPolicyDraft(values: Partial<CampaignPolicySettingsDraft>) {
    setCampaignPolicyDraft((current) => ({
      ...current,
      ...values,
    }));
    setCampaignPolicyResult(null);
  }

  function updateCampaignReviewDraft(values: Partial<CampaignReviewDraft>) {
    setCampaignReviewDraft((current) => ({
      ...current,
      ...values,
    }));
    setCampaignReviewResult(null);
  }

  function updateSupportCaseDraft(values: Partial<SupportCaseDraft>) {
    setSupportCaseDraft((current) => ({
      ...current,
      ...values,
    }));
    setSupportCaseResult(null);
    setSupportCaseLifecycleResult(null);
    setSupportCaseAssignmentResult(null);
  }

  function submitSupportCase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedTitle = supportCaseDraft.title.trim();
    const cleanedSummary = supportCaseDraft.summary.trim();
    const cleanedEvidenceType = supportCaseDraft.evidenceType.trim();
    const cleanedEvidenceRef = supportCaseDraft.evidenceRef.trim();
    if (!selectedAccount || !selectedExternalTenantRef || !cleanedTitle || !cleanedSummary) {
      return;
    }
    supportCaseMutation.mutate({
      accountRef: selectedAccount.accountId,
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "setup",
      },
      category: supportCaseDraft.category,
      priority: supportCaseDraft.priority,
      title: cleanedTitle,
      summary: cleanedSummary,
      sourceSurface: "support_hub",
      evidenceLinks:
        cleanedEvidenceType && cleanedEvidenceRef
          ? [
              {
                evidenceType: cleanedEvidenceType,
                evidenceRef: cleanedEvidenceRef,
                safeStatus: "CUSTOMER_SCOPED",
                redactions: ["internal_tenant_identifier"],
              },
            ]
          : [],
      reasonCode: "CUSTOMER_SUPPORT_CASE_CREATED",
      correlationId: `customer-profile-support-case-${selectedAccount.accountId}`,
      idempotencyKey: safeIdempotencyKey(
        "customer-profile-support-case",
        selectedAccount.accountId,
        supportCaseDraft.category,
        supportCaseDraft.priority,
        cleanedTitle,
        cleanedSummary,
        cleanedEvidenceType,
        cleanedEvidenceRef,
      ),
    });
  }

  function submitSupportCaseLifecycle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!supportCaseLifecycleDraft) {
      return;
    }
    const cleanedNoteText = supportCaseLifecycleDraft.noteText.trim();
    const cleanedTransitionReason = supportCaseLifecycleDraft.transitionReason.trim();
    if (
      supportCaseLifecycleDraft.action === "note" &&
      (!supportCaseLifecycleDraft.caseRef.trim() || !cleanedNoteText)
    ) {
      return;
    }
    if (
      supportCaseLifecycleDraft.action === "status" &&
      (!supportCaseLifecycleDraft.caseRef.trim() || !cleanedTransitionReason)
    ) {
      return;
    }
    setSupportCaseResult(null);
    supportCaseLifecycleMutation.mutate({
      ...supportCaseLifecycleDraft,
      noteText: cleanedNoteText,
      requestKey: newSupportCaseLifecycleRequestKey(),
      transitionReason: cleanedTransitionReason,
    });
  }

  function submitSupportCaseAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!supportCaseAssignmentDraft) {
      return;
    }
    const cleanedAssigneeRef = supportCaseAssignmentDraft.assigneeRef.trim();
    const cleanedAssignmentReason = supportCaseAssignmentDraft.assignmentReason.trim();
    if (!supportCaseAssignmentDraft.caseRef.trim() || !cleanedAssigneeRef || !cleanedAssignmentReason) {
      return;
    }
    setSupportCaseResult(null);
    setSupportCaseLifecycleResult(null);
    supportCaseAssignmentMutation.mutate({
      ...supportCaseAssignmentDraft,
      assigneeRef: cleanedAssigneeRef,
      assignmentReason: cleanedAssignmentReason,
      requestKey: newSupportCaseAssignmentRequestKey(),
    });
  }

  function submitCampaignSetup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedName = campaignSetupDraft.name.trim();
    const cleanedSegment = campaignSetupDraft.segment.trim();
    const cleanedProgrammeVersionId = campaignSetupDraft.programmeVersionId.trim();
    if (
      !selectedAccount ||
      !selectedExternalTenantRef ||
      !cleanedName ||
      !cleanedSegment ||
      !cleanedProgrammeVersionId
    ) {
      return;
    }
    const cleanedMaxUses = campaignSetupDraft.maxUses.trim();
    campaignSetupMutation.mutate({
      accountRef: selectedAccount.accountId,
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "setup",
      },
      campaign: {
        name: cleanedName,
        segment: cleanedSegment,
        programmeVersionId: cleanedProgrammeVersionId,
        startsAt: campaignSetupDraft.startsAt || null,
        endsAt: campaignSetupDraft.endsAt || null,
        maxUses: cleanedMaxUses ? Number(cleanedMaxUses) : null,
      },
      setupIntent: {
        reason: "CUSTOMER_PROFILE_CAMPAIGN_SETUP",
      },
      correlationId: `customer-profile-campaign-create-${selectedAccount.accountId}`,
      idempotencyKey: `customer-profile-campaign-create-${selectedAccount.accountId}-${cleanedName}-${cleanedSegment}`
        .toLowerCase()
        .replace(/[^a-z0-9-]+/g, "-"),
    });
  }

  function submitCampaignPolicySettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedCampaignCode = campaignPolicyDraft.campaignCode.trim();
    if (!selectedAccount || !selectedExternalTenantRef || !cleanedCampaignCode) {
      return;
    }
    const version = Number(campaignPolicyDraft.version.trim() || "1");
    const attributionWindowDays = Number(campaignPolicyDraft.attributionWindowDays.trim() || "30");
    const productWindowDays = Number(campaignPolicyDraft.productWindowDays.trim() || String(attributionWindowDays));
    const eligibilityRule = campaignPolicyDraft.eligibilityRule.trim() || "NEW_CUSTOMER_ONLY";
    campaignPolicyMutation.mutate({
      accountRef: selectedAccount.accountId,
      campaignCode: cleanedCampaignCode,
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "setup",
      },
      policySettings: {
        version,
        attributionWindowDays,
        eligibilityRules: [
          {
            rule: eligibilityRule,
            enabled: true,
          },
        ],
        productWindows: {
          default: {
            days: productWindowDays,
          },
        },
        productRules: {
          default: {
            requiresAcceptedTerms: campaignPolicyDraft.requiresAcceptedTerms === "true",
          },
        },
        rewardVisibility: {
          mode: "configured_without_payment",
          notes:
            campaignPolicyDraft.rewardVisibilityNotes.trim() ||
            "Reward visibility configured for setup only.",
        },
      },
      setupIntent: {
        requestedStatus: "POLICY_SETTINGS_RECORDED",
        reason: "CUSTOMER_PROFILE_CAMPAIGN_POLICY_SETTINGS",
      },
      reasonCode: "CUSTOMER_PROFILE_CAMPAIGN_POLICY_SETTINGS",
      correlationId: `customer-profile-campaign-policy-${selectedAccount.accountId}`,
      idempotencyKey: `customer-profile-campaign-policy-${selectedAccount.accountId}-${cleanedCampaignCode}-${version}-${attributionWindowDays}`
        .toLowerCase()
        .replace(/[^a-z0-9-]+/g, "-"),
    });
  }

  function submitCampaignReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedCampaignCode = campaignReviewDraft.campaignCode.trim();
    const cleanedSetupSummary = campaignReviewDraft.setupSummary.trim();
    if (!selectedAccount || !selectedExternalTenantRef || !cleanedCampaignCode || !cleanedSetupSummary) {
      return;
    }
    campaignReviewSubmitMutation.mutate({
      accountRef: selectedAccount.accountId,
      campaignCode: cleanedCampaignCode,
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "setup",
      },
      reviewSubmission: {
        setupSummary: cleanedSetupSummary,
        requestedReviewStatus: "READY_FOR_REVIEW",
        operatorNotes: campaignReviewDraft.operatorNotes,
      },
      reasonCode: "CUSTOMER_PROFILE_CAMPAIGN_REVIEW_SUBMISSION",
      correlationId: `customer-profile-campaign-review-submit-${selectedAccount.accountId}`,
      idempotencyKey: `customer-profile-campaign-review-submit-${selectedAccount.accountId}-${cleanedCampaignCode}`
        .toLowerCase()
        .replace(/[^a-z0-9-]+/g, "-"),
    });
  }

  function submitCampaignReviewDecision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedCampaignCode = campaignReviewDraft.campaignCode.trim();
    const cleanedReason = campaignReviewDraft.decisionReason.trim();
    const cleanedReviewerRef = campaignReviewDraft.reviewerRef.trim();
    if (!selectedAccount || !selectedExternalTenantRef || !cleanedCampaignCode || !cleanedReason || !cleanedReviewerRef) {
      return;
    }
    campaignReviewDecisionMutation.mutate({
      accountRef: selectedAccount.accountId,
      campaignCode: cleanedCampaignCode,
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "setup",
      },
      reviewDecision: {
        decision: campaignReviewDraft.decision,
        reason: cleanedReason,
        reviewerRef: cleanedReviewerRef,
      },
      reasonCode: "CUSTOMER_PROFILE_CAMPAIGN_REVIEW_DECISION",
      correlationId: `customer-profile-campaign-review-decision-${selectedAccount.accountId}`,
      idempotencyKey: `customer-profile-campaign-review-decision-${selectedAccount.accountId}-${cleanedCampaignCode}-${campaignReviewDraft.decision}`
        .toLowerCase()
        .replace(/[^a-z0-9-]+/g, "-"),
    });
  }

  const accountFoundationActivationPanel =
    selectedAccount && !isAccountFoundationActive ? (
      <div className="account-foundation-action">
        <div className="account-foundation-action-main">
          <div>
            <h3>Activate customer foundation</h3>
            <p>
              This moves the selected customer from pending setup to an active account and tenant-link posture,
              then creates bounded platform seat capacity. It does not assign seats, send invites, create
              credentials, change auth claims, activate campaigns, bill, or move money.
            </p>
          </div>
          <StatusBadge label="Required before seats" tone="warning" />
        </div>
        <div className="account-foundation-action-footer">
          <button
            className="button"
            disabled={!canActivateAccountFoundation || accountFoundationActivationMutation.isPending}
            onClick={activateAccountFoundation}
            type="button"
          >
            {accountFoundationActivationMutation.isPending ? "Activating foundation" : "Activate foundation"}
          </button>
          {!isAmplifiAdmin ? (
            <span className="table-subtext">Only Amplifi Admin can activate the customer foundation.</span>
          ) : null}
        </div>
        {accountFoundationActivationMutation.error ? (
          <ErrorPanel error={accountFoundationActivationMutation.error} />
        ) : null}
      </div>
    ) : null;
  const scopedAccountActivationResult =
    selectedAccount && accountActivationResult?.accountId === selectedAccount.accountId
      ? accountActivationResult
      : null;
  const accountFoundationActivationResultPanel = scopedAccountActivationResult ? (
    <div className="wizard-summary-strip success">
      <strong>Customer foundation activated.</strong> {scopedAccountActivationResult.message}
    </div>
  ) : null;

  return (
    <>
      <section className="page-header customer-profile-header">
        <div>
          <div className="page-kicker">
            {selectedAccount ? "Referral SaaS > Customer profile" : "Referral SaaS > Open a customer"}
          </div>
          <h1 className="page-title">{accountId && selectedAccount ? customerName : "Find the customer to work on"}</h1>
          <p className="page-copy">
            {accountId && selectedAccount
              ? "This is the customer home. Campaigns, links, reports, attribution, and support stay inside this customer context."
              : "Country first, then account, then open their profile."}
          </p>
          {accountId && selectedAccount ? (
            <div className="customer-context-chips" aria-label="Selected customer context">
              <span className="customer-context-chip">
                <span className="customer-context-label">Operating jurisdiction</span>
                <span className="customer-context-value">{operatingMarketFromAccount(selectedAccount).name}</span>
              </span>
              <span className="customer-context-chip status">
                <span className="customer-context-label">Account status</span>
                <StatusBadge label={formatDisplay(selectedAccount.accountStatus)} tone="success" />
              </span>
              <span className="customer-context-chip">
                <span className="customer-context-label">Account code</span>
                <span className="customer-context-value">{selectedAccount.accountCode}</span>
              </span>
              <span className="customer-context-chip">
                <span className="customer-context-label">Customer reference</span>
                <span className="customer-context-value">{selectedExternalTenantRef}</span>
              </span>
              <span className="customer-context-chip">
                <span className="customer-context-label">Organisation reference</span>
                <span className="customer-context-value">{selectedOrganisationRef}</span>
              </span>
            </div>
          ) : null}
        </div>
        <div className="customer-header-actions">
          {accountId && selectedAccount && selectedModule !== "home" ? (
            <Link className="button secondary" to={selectedCustomerPath}>
              Customer home
            </Link>
          ) : null}
          <Link className="button secondary" to="/admin/referral-saas/account-maintenance">
            Switch customer
          </Link>
          <StatusBadge label="View only where noted" tone="warning" />
        </div>
      </section>

      {isLoading ? <LoadingState label="Loading Referral SaaS customer workspace" /> : null}
      {error ? <ErrorPanel error={error} /> : null}

      {!isLoading && !error ? (
        <>
          {!accountId ? (
          <section className="panel" id="customer-selector">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">1. Where do you operate?</h2>
                <div className="panel-subtitle">
                  Pick the country. You will only see customers in that market.
                </div>
              </div>
              <StatusBadge label="Entry" tone="info" />
            </div>
            <div className="panel-body">
              {isAccountRegistryLoading ? <LoadingState label="Loading customers" /> : null}
              {accountRegistryError ? <ErrorPanel error={accountRegistryError} /> : null}
              {!isAccountRegistryLoading && !accountRegistryError && accountItems.length === 0 ? (
                <div className="empty-state">
                  No customers exist yet. Use Account Setup to create the first customer foundation.
                </div>
              ) : null}
              {!isAccountRegistryLoading && !accountRegistryError && accountItems.length > 0 ? (
                <>
                  <div className="customer-selector-grid market-selector-grid">
                    {operatingMarkets.map((market) => {
                      const selected = market.name === selectedOperatingMarket;
                      return (
                        <button
                          className={`customer-selector-card compact ${selected ? "selected" : ""}`}
                          key={market.name}
                          onClick={() => selectOperatingMarket(market.name)}
                          type="button"
                        >
                          <span className="customer-selector-title">{market.name}</span>
                          <span className="customer-selector-copy">{market.description}</span>
                          <span className="customer-selector-count">{formatAreaCount(market.count, "account")}</span>
                        </button>
                      );
                    })}
                  </div>

                  <div className="customer-picker-step">
                    <h2 className="panel-title">2. Which customer?</h2>
                    <div className="panel-subtitle">
                      Only accounts in {selectedOperatingMarket}. Each card labels the customer reference,
                      organisation reference, and support account code.
                    </div>
                  </div>
                  {accountsForMarket.length === 0 ? (
                    <div className="empty-state">No customers exist in {selectedOperatingMarket} yet.</div>
                  ) : (
                    <div className="customer-selector-grid">
                      {accountsForMarket.map((account) => {
                        const externalTenantRef =
                          account.primaryExternalTenantRef ||
                          findAccountExternalRef(account.externalReferences, "external_tenant_ref");
                        const organisationRef = findAccountExternalRef(account.externalReferences, "organisation_ref");
                        const pending = account.accountId === pendingAccountId;
                        const opened = account.accountId === accountId;
                        const canSelectAccount = Boolean(externalTenantRef && organisationRef);
                        const customerName = account.accountName || externalTenantRef || organisationRef || account.accountCode;
                        return (
                          <button
                            className={`customer-selector-card ${pending || opened ? "selected" : ""}`}
                            disabled={!canSelectAccount}
                            key={account.accountId}
                            onClick={() => stageAccount(account)}
                            type="button"
                          >
                            <span className="customer-selector-heading-row">
                              <span>
                                <span className="customer-selector-label">Customer</span>
                                <span className="customer-selector-title">{customerName}</span>
                              </span>
                              {pending || opened ? <StatusBadge label="Selected" tone="success" /> : null}
                            </span>
                            <span className="customer-selector-fields" aria-label={`${customerName} identifiers`}>
                              <span className="customer-selector-field">
                                <span className="customer-selector-field-label">Customer reference</span>
                                <span className="customer-selector-meta">
                                  {externalTenantRef || "Missing customer reference"}
                                </span>
                              </span>
                              <span className="customer-selector-field">
                                <span className="customer-selector-field-label">Organisation reference</span>
                                <span className="customer-selector-meta">
                                  {organisationRef || "Missing organisation reference"}
                                </span>
                              </span>
                              <span className="customer-selector-field">
                                <span className="customer-selector-field-label">Account code</span>
                                <span className="customer-selector-count">{account.accountCode}</span>
                              </span>
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                  <div className="customer-open-row">
                    <Link
                      aria-disabled={!pendingAccount}
                      className={`button ${pendingAccount ? "" : "disabled"}`}
                      to={pendingAccount ? `/admin/referral-saas/account-maintenance/${pendingAccount.accountId}` : "#"}
                    >
                      Open customer profile
                    </Link>
                  </div>
                </>
              ) : null}
              <details className="wizard-details">
                <summary>Manual customer lookup</summary>
                <form className="account-setup-scope-form" onSubmit={submitScope}>
                  <label className="field">
                    <span>Customer reference</span>
                    <input
                      className="input"
                      onChange={(event) => setDraftExternalTenantRef(event.target.value)}
                      value={draftExternalTenantRef}
                    />
                  </label>
                  <label className="field">
                    <span>Organisation reference</span>
                    <input
                      className="input"
                      onChange={(event) => setDraftOrganisationRef(event.target.value)}
                      value={draftOrganisationRef}
                    />
                  </label>
                  <button className="button" disabled={!canCheckScope} type="submit">
                    Check customer
                  </button>
                  <StatusBadge label={scopeChanged ? "Changes not checked" : "Loaded"} tone={scopeChanged ? "warning" : "success"} />
                </form>
              </details>
            </div>
          </section>
          ) : null}

          {accountId && selectedAccount ? (
            <>
              {selectedModule === "home" && (accountFoundationActivationPanel || accountFoundationActivationResultPanel) ? (
                <section className="panel account-foundation-panel">
                  <div className="panel-header">
                    <div>
                      <h2 className="panel-title">Account foundation</h2>
                      <div className="panel-subtitle">
                        Activate the customer foundation before provisioning platform seats.
                      </div>
                    </div>
                    <StatusBadge label={formatDisplay(selectedAccount.accountStatus)} tone={statusTone(selectedAccount.accountStatus)} />
                  </div>
                  <div className="panel-body">
                    {accountFoundationActivationPanel}
                    {accountFoundationActivationResultPanel}
                  </div>
                </section>
              ) : null}

              {selectedModule === "home" ? (
                <section className="customer-overview-grid">
                  <div className="panel">
                    <div className="panel-header">
                      <div>
                        <h2 className="panel-title">Customer readiness</h2>
                        <div className="panel-subtitle">
                          Green is ready, red blocks safe testing, and amber can wait. Each red or amber item links to the page that resolves it.
                        </div>
                      </div>
                      <StatusBadge label={overallStatus} tone={statusTone(overallStatus)} />
                    </div>
                    <div className="panel-body">
                      <div className="customer-health-strip">
                        <div className="customer-health-card good" aria-label={`${readyCount} green checks looking fine`}>
                          <div className="customer-health-card-top">
                            <span className="customer-rag-dot green" aria-hidden="true" />
                            <span className="customer-health-rag">Green</span>
                          </div>
                          <strong>{readyCount}</strong>
                          <span className="customer-health-label">Looking fine</span>
                          <span className="customer-health-action">No action needed</span>
                        </div>
                        <div className="customer-health-card bad" aria-label={`${effectiveBlockedCount} red blockers stopping referral testing`}>
                          <div className="customer-health-card-top">
                            <span className="customer-rag-dot red" aria-hidden="true" />
                            <span className="customer-health-rag">Red</span>
                          </div>
                          <strong>{effectiveBlockedCount}</strong>
                          <span className="customer-health-label">Stopping you</span>
                          {effectiveBlockedCount > 0 ? (
                            <Link
                              className="customer-health-action-link"
                              to={buildCustomerModuleRoute(selectedCustomerPath, stoppingAction.route, customerQuery)}
                            >
                              Fix first: {stoppingAction.title}
                            </Link>
                          ) : (
                            <span className="customer-health-action">No blocker</span>
                          )}
                        </div>
                        <div className="customer-health-card wait" aria-label={`${effectiveWaitingCount} amber items can wait`}>
                          <div className="customer-health-card-top">
                            <span className="customer-rag-dot amber" aria-hidden="true" />
                            <span className="customer-health-rag">Amber</span>
                          </div>
                          <strong>{effectiveWaitingCount}</strong>
                          <span className="customer-health-label">Can wait</span>
                          <Link
                            className="customer-health-action-link"
                            to={buildCustomerModuleRoute(selectedCustomerPath, waitingAction.route, customerQuery)}
                          >
                            Review later: {waitingAction.title}
                          </Link>
                        </div>
                      </div>
                      <div className={`wizard-summary-strip ${effectiveBlockedCount || effectiveMissingEvidenceCount ? "warning" : "success"}`}>
                        <div>
                          <strong>In plain English:</strong>{" "}
                          {effectiveBlockedCount || effectiveMissingEvidenceCount
                            ? `Most of ${customerName} is ready. Fix the red item before safe referral testing; amber items can be reviewed after the blocker is clear.`
                            : `${customerName} has no visible setup blocker count. Continue with campaign, link/code, attribution, or reporting tests.`}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="panel">
                    <div className="panel-header">
                      <div>
                        <h2 className="panel-title">Do this next</h2>
                        <div className="panel-subtitle">Start with the first item. Each action opens its own customer-scoped page.</div>
                      </div>
                    </div>
                    <div className="panel-body route-list">
                      {doNext.map((action) => (
                        <Link
                          className="route-item route-link"
                          key={action.title}
                          to={buildCustomerModuleRoute(selectedCustomerPath, action.route, customerQuery)}
                        >
                          <div>
                            <div className="route-name">{action.title}</div>
                            <div className="route-path">{action.copy}</div>
                          </div>
                          <div className="route-action-stack">
                            <StatusBadge label={action.priority} tone={action.tone} />
                            <span className="route-action">Open page</span>
                          </div>
                        </Link>
                      ))}
                    </div>
                  </div>
                </section>
              ) : null}

              {selectedModule === "home" ? (
                <section className="panel">
                  <div className="panel-header">
                    <div>
                      <h2 className="panel-title">What you can do for this customer</h2>
                      <div className="panel-subtitle">
                        Choose a service page for {customerName}. The badge tells you whether to use it now, fix it first, or leave it for later.
                      </div>
                    </div>
                    <StatusBadge label="Customer scoped" tone="success" />
                  </div>
                  <div className="panel-body customer-function-grid">
                    {customerFunctions.map((item) => {
                      const displayItem =
                        item.route === "people" && hasAcceptedRequiredAccess
                          ? {
                              ...item,
                              status: "Ready",
                              tone: "success" as StatusTone,
                              copy: "Required customer managers are confirmed.",
                              letsYou: "Move into referral setup while platform login stays optional.",
                            }
                          : item;
                      const Icon = item.icon;
                      const href = buildCustomerModuleRoute(selectedCustomerPath, displayItem.route, customerQuery);
                      const actionLabel = customerFunctionActionLabel(displayItem.tone, displayItem.status);
                      return (
                        <Link
                          className="customer-function-card"
                          key={displayItem.title}
                          to={href}
                        >
                          <div className="customer-function-card-header">
                            <span className="customer-function-title">
                              <Icon size={16} />
                              {displayItem.title}
                            </span>
                            <StatusBadge label={displayItem.status} tone={displayItem.tone} />
                          </div>
                          <p>{displayItem.copy}</p>
                          <div className="customer-function-help">
                            <strong>This lets you:</strong> {displayItem.letsYou}
                          </div>
                          <div className="customer-function-open">{actionLabel} - open page</div>
                        </Link>
                      );
                    })}
                  </div>
                </section>
              ) : null}

              {selectedModule === "home" ? (
                <section className="panel">
                  <div className="panel-header">
                    <div>
                      <h2 className="panel-title">How configuration fits together</h2>
                      <div className="panel-subtitle">
                        Keep the customer product, referral programme, campaign, campaign-specific changes, and reporting separate.
                      </div>
                    </div>
                    <StatusBadge label="Plain language" tone="success" />
                  </div>
                  <div className="panel-body configuration-proof-grid">
                    {configurationProofSteps.map((step, index) => (
                      <Link
                        className="configuration-proof-card"
                        key={step.title}
                        to={buildCustomerModuleRoute(selectedCustomerPath, step.route, customerQuery)}
                      >
                        <span className="configuration-proof-index">{index + 1}</span>
                        <div>
                          <strong>{step.title}</strong>
                          <p>{step.copy}</p>
                          <span>{step.action}</span>
                        </div>
                      </Link>
                    ))}
                  </div>
                </section>
              ) : null}

              {selectedModule === "home" ? (
                <section className="panel">
                  <div className="panel-header">
                    <div>
                      <h2 className="panel-title">People snapshot</h2>
                      <div className="panel-subtitle">Summary only. Open People and access to manage responsibilities.</div>
                    </div>
                    <Link className="button secondary" to={buildCustomerModuleRoute(selectedCustomerPath, "people", customerQuery)}>
                      Open People and access
                    </Link>
                  </div>
                  <div className="panel-body grid-3">
                    <KpiCard label="Active users" value={String(membershipPosture?.membershipPosture.activeCount ?? 0)} footnote="Activated people on this customer" icon={Users} />
                    <KpiCard label="Named or invited" value={String(membershipPosture?.membershipPosture.invitedCount ?? 0)} footnote="Intent recorded without email delivery" icon={CheckCircle2} />
                    <KpiCard label="Roles still missing" value={String(missingAccessRoleCount)} footnote="Owner or campaign manager still needs attention" icon={AlertCircle} />
                  </div>
                </section>
              ) : null}

              {selectedModule === "settings" ? (
              <section className="panel" id="customer-settings">
                <div className="panel-header">
                  <div>
                    <h2 className="panel-title">Customer settings</h2>
                    <div className="panel-subtitle">
                      Maintain profile context from the selected customer home, not from Account Setup.
                    </div>
                  </div>
                  <StatusBadge label="Customer scoped" tone="success" />
                </div>
                <div className="panel-body route-list">
                  <div className="wizard-status-card">
                    <div>
                      <strong>Customer identifiers</strong>
                      <p>
                        {operatingMarketFromAccount(selectedAccount).name} - {selectedExternalTenantRef} / {selectedOrganisationRef}
                      </p>
                      <span className="table-subtext">
                        These references stay read-only here. Changing them is reference rotation, not profile maintenance.
                      </span>
                    </div>
                    <StatusBadge label="Read only" tone="info" />
                  </div>
                  <form className="account-setup-scope-form" onSubmit={submitProfileSettings}>
                    <label className="field">
                      <span>Customer name</span>
                      <input
                        className="input"
                        onChange={(event) => updateProfileDraft({ accountName: event.target.value })}
                        value={selectedProfileDraft.accountName}
                      />
                    </label>
                    <label className="field">
                      <span>Operating jurisdiction</span>
                      <select
                        className="input"
                        onChange={(event) => updateProfileDraft({ operatingJurisdictionCode: event.target.value })}
                        value={selectedProfileDraft.operatingJurisdictionCode}
                      >
                        {jurisdictionOptions.map((option) => (
                          <option key={option.code} value={option.code}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="field">
                      <span>Customer type</span>
                      <select
                        className="input"
                        onChange={(event) => updateProfileDraft({ customerType: event.target.value })}
                        value={selectedProfileDraft.customerType}
                      >
                        {customerTypeOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <div className="wizard-status-card">
                      <div>
                        <strong>
                          {customerTypeOptions.find((option) => option.value === selectedProfileDraft.customerType)
                            ?.label}
                        </strong>
                        <p>
                          {customerTypeOptions.find((option) => option.value === selectedProfileDraft.customerType)
                            ?.copy}
                        </p>
                      </div>
                      <StatusBadge label="Billing-ready category" tone="info" />
                    </div>
                    <label className="field">
                      <span>Industry</span>
                      <select
                        className="input"
                        onChange={(event) => updateProfileDraft({ industry: event.target.value })}
                        value={selectedProfileDraft.industry}
                      >
                        {industryOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <button
                      className="button"
                      disabled={!selectedProfileDraft.accountName.trim() || profileMutation.isPending}
                      type="submit"
                    >
                      {profileMutation.isPending ? "Saving customer profile" : "Save customer profile"}
                    </button>
                  </form>
                  {profileMutation.error ? <ErrorPanel error={profileMutation.error} /> : null}
                  {profileResult ? (
                    <div className="wizard-summary-strip success">
                      <strong>Customer profile saved.</strong> {profileResult}
                    </div>
                  ) : null}
                </div>
              </section>
              ) : null}

              {selectedModule === "people" ? (
              <section className="panel" id="people-access">
                <div className="panel-header">
                  <div>
                    <h2 className="panel-title">People and access</h2>
                    <div className="panel-subtitle">
                      Add and confirm the people responsible for this customer's referral work.
                    </div>
                  </div>
                  <StatusBadge
                    label={missingAccessRoleCount ? `${missingAccessRoleCount} still needed` : "Customer scoped"}
                    tone={missingAccessRoleCount ? "warning" : "success"}
                  />
                </div>
                <div className="panel-body people-access-workspace">
                  {accountFoundationActivationPanel}
                  {accountFoundationActivationResultPanel}
                  <div className="people-access-hero">
                    <div>
                      <strong>{missingAccessRoleCount ? "People setup needs attention" : "People are confirmed"}</strong>
                      <p>{peopleAccessStatus}</p>
                      <div className="people-access-journey" aria-label="People and access lifecycle">
                        {["Still needed", "Added", "Confirmed for work", "Platform login optional"].map((stage) => (
                          <span
                            className={
                              stage === "Confirmed for work" && activeAccessCount
                                ? "current"
                                : stage === "Still needed" && missingAccessRoleCount
                                  ? "current warning"
                                  : ""
                            }
                            key={stage}
                          >
                            {stage}
                          </span>
                        ))}
                      </div>
                    </div>
                    <button className="button compact" onClick={() => startAddAccessIntent()} type="button">
                      Add person
                    </button>
                  </div>
                  {isAccessFormOpen ? (
                    <div
                      aria-label={editingMembershipRef ? "Edit access intent" : "Add access intent"}
                      aria-modal="true"
                      className="side-drawer-backdrop"
                      role="dialog"
                    >
                      <aside className="side-drawer">
                        <form className="account-setup-scope-form drawer-form" onSubmit={submitAccessIntent}>
                          <div className="drawer-header">
                            <div>
                              <h3>{editingMembershipRef ? "Edit person access" : "Add person"}</h3>
                              <p>
                                {editingMembershipRef
                                  ? `Update this person's responsibility for ${customerName}.`
                                  : `Name who should manage ${customerName}.`} This saves intent only.
                              </p>
                            </div>
                            <StatusBadge label="No live invite" tone="warning" />
                          </div>
                          <label className="field">
                            <span>Person name</span>
                            <input
                              className="input"
                              onChange={(event) => setAccessDisplayName(event.target.value)}
                              placeholder="Example: John Doe"
                              value={accessDisplayName}
                            />
                          </label>
                          <label className="field">
                            <span>Work email</span>
                            <input
                              className="input"
                              onChange={(event) => setAccessEmail(event.target.value)}
                              placeholder="Example: owner@customer.com"
                              type="email"
                              value={accessEmail}
                            />
                            <span className="field-hint">
                              Used as the access identity for this customer. No invitation email is sent from this step.
                            </span>
                          </label>
                          <label className="field">
                            <span>Responsibility</span>
                            <select
                              className="input"
                              onChange={(event) => setAccessRoleLabel(event.target.value)}
                              value={accessRoleLabel}
                            >
                              {accessRoleOptions.map((option) => (
                                <option key={option.label} value={option.label}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                          </label>
                          <div className="wizard-status-card">
                            <div>
                              <strong>{accessRoleLabel}</strong>
                              <p>{(accessRoleOptions.find((option) => option.label === accessRoleLabel) || accessRoleOptions[0]).copy}</p>
                            </div>
                            <StatusBadge label="Customer scoped" tone="success" />
                          </div>
                          {editingAccessRow ? (
                            <div className="people-access-drawer-stage">
                              <div>
                                <span className="eyebrow">Current stage</span>
                                <strong>
                                  {peopleAccessStage(asRecord(editingAccessRow), editingAccessReadiness).label}
                                </strong>
                                <p>{peopleAccessNextAction(asRecord(editingAccessRow), editingAccessReadiness)}</p>
                              </div>
                              <StatusBadge
                                label={accessProvisioningLabel(
                                  editingAccessReadiness?.provisioningReadiness || "SEPARATE_WORKFLOW",
                                )}
                                tone={accessProvisioningTone(
                                  editingAccessReadiness?.provisioningReadiness || "SEPARATE_WORKFLOW",
                                )}
                              />
                            </div>
                          ) : null}
                          {editingMembershipRef ? (
                            <div className="wizard-status-card">
                              <div>
                                <strong>Manual access acceptance</strong>
                                <p>
                                  Amplifi Admin can record that this person accepted access outside the invite flow. This
                                  does not send email, assign a seat, or change login permissions.
                                </p>
                                <label className="field">
                                  <span>Acceptance evidence</span>
                                  <textarea
                                    aria-label="Acceptance evidence"
                                    className="input"
                                    onChange={(event) => setManualAcceptanceEvidence(event.target.value)}
                                    placeholder="Example: Approved by customer admin on onboarding call"
                                    rows={3}
                                    value={manualAcceptanceEvidence}
                                  />
                                  <span className="field-hint">
                                    Required for audit. This is separate from Save person details. Use this after the
                                    name, email, and responsibility above are correct.
                                  </span>
                                </label>
                              </div>
                              <div className="action-cell">
                                <StatusBadge
                                  label={isAmplifiAdmin ? "Amplifi Admin only" : "Admin required"}
                                  tone={isAmplifiAdmin ? "info" : "warning"}
                                />
                                <button
                                  className="button secondary compact"
                                  disabled={
                                    !isAmplifiAdmin ||
                                    !manualAcceptanceEvidence.trim() ||
                                    !isValidEmail(accessEmail.trim()) ||
                                    activationMutation.isPending
                                  }
                                  onClick={requestManualAccessAcceptance}
                                  type="button"
                                >
                                  {activationMutation.isPending ? "Recording" : "Record accepted access"}
                                </button>
                              </div>
                            </div>
                          ) : null}
                          <div className="drawer-actions">
                            <button className="button secondary" onClick={resetAccessForm} type="button">
                              Cancel
                            </button>
                            <button
                              className="button"
                              disabled={
                                !isValidEmail(accessEmail.trim()) ||
                                accessMutation.isPending ||
                                accessUpdateMutation.isPending
                              }
                              type="submit"
                            >
                              {accessMutation.isPending || accessUpdateMutation.isPending
                                ? "Saving"
                                : editingMembershipRef
                                  ? "Save person details"
                                  : "Save person intent"}
                            </button>
                          </div>
                        </form>
                      </aside>
                    </div>
                  ) : null}
                  {accessMutation.error ? <ErrorPanel error={accessMutation.error} /> : null}
                  {accessUpdateMutation.error ? <ErrorPanel error={accessUpdateMutation.error} /> : null}
                  {accessCancelMutation.error ? <ErrorPanel error={accessCancelMutation.error} /> : null}
                  {accessResult ? (
                    <div className="wizard-summary-strip success">
                      <strong>Access intent saved.</strong> {accessResult}
                    </div>
                  ) : null}
                  {accessLifecycleResult ? (
                    <div className="wizard-summary-strip success">
                      <strong>Access intent updated.</strong> {accessLifecycleResult}
                    </div>
                  ) : null}
                  {deliveryMutation.error ? <ErrorPanel error={deliveryMutation.error} /> : null}
                  {deliveryResult ? (
                    <div className="wizard-summary-strip success">
                      <strong>Invite delivery updated.</strong> {deliveryResult}
                    </div>
                  ) : null}
                  {activationMutation.error ? <ErrorPanel error={activationMutation.error} /> : null}
                  {activationResult ? (
                    <div className="wizard-summary-strip success">
                      <strong>Accepted access recorded.</strong> {activationResult}
                    </div>
                  ) : null}
                  {peopleAccessRows.length ? (
                    <div className="people-access-list" aria-label="People and access responsibilities">
                      {peopleAccessRows.map((row) => {
                        const membershipRef = getValue(row, ["membershipRef"], "");
                        const roleFamily = getValue(row, ["roleFamily"], "UNKNOWN");
                        const role = roleOptionForFamily(roleFamily);
                        const readiness = activationReadinessByMembershipRef.get(membershipRef);
                        const stage = peopleAccessStage(row as Record<string, unknown>, readiness);
                        const next = peopleAccessNextAction(row as Record<string, unknown>, readiness);
                        const isMissingRole = Boolean((row as Record<string, unknown>).isMissingRole);
                        const canMaintainIntent = getValue(row, ["status"], "") === "INVITED";
                        return (
                          <div
                            className={`people-access-row ${isMissingRole ? "ghost" : ""}`}
                            key={membershipRef || roleFamily}
                          >
                            <div className={`people-access-avatar ${isMissingRole ? "missing" : ""}`}>
                              {isMissingRole
                                ? "?"
                                : initials(formatDisplay(getValue(row, ["displayName"], "Named person")))}
                            </div>
                            <div className="people-access-person">
                              <strong>
                                {isMissingRole
                                  ? role.label
                                  : formatDisplay(getValue(row, ["displayName"], "Named person"))}
                              </strong>
                              <span>
                                {isMissingRole
                                  ? "Required responsibility"
                                  : `${getValue(row, ["subject"], "No email identity returned")} - ${role.label}`}
                              </span>
                              <p>
                                <strong>This lets you:</strong> {role.copy}
                              </p>
                              <p className="people-access-next">
                                Next: <em>{next}</em>
                              </p>
                            </div>
                            <div className="people-access-actions">
                              <StatusBadge label={stage.label} tone={stage.tone} />
                              {isMissingRole ? (
                                <button
                                  className="button secondary compact"
                                  onClick={() => startAddAccessIntent(roleFamily)}
                                  type="button"
                                >
                                  Add
                                </button>
                              ) : (
                                <button
                                  className="button secondary compact"
                                  onClick={() => startEditAccessIntent(row as Record<string, unknown>)}
                                  type="button"
                                >
                                  Review
                                </button>
                              )}
                              {!isMissingRole ? (
                                <div className="action-cell horizontal">
                                  <button
                                    className="button secondary compact"
                                    disabled={!canMaintainIntent}
                                    onClick={() => startEditAccessIntent(row as Record<string, unknown>)}
                                    type="button"
                                  >
                                    Edit
                                  </button>
                                  <button
                                    className="button secondary compact"
                                    disabled={!canMaintainIntent || accessCancelMutation.isPending}
                                    onClick={() => removeAccessIntent(membershipRef, roleFamily)}
                                    type="button"
                                  >
                                    {accessCancelMutation.isPending ? "Removing" : "Remove"}
                                  </button>
                                </div>
                              ) : null}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="wizard-status-card">
                      <div>
                        <strong>No people recorded yet</strong>
                        <p>Add the account owner first, then add a campaign manager if that is a different person.</p>
                      </div>
                      <StatusBadge label="Action needed" tone="warning" />
                    </div>
                  )}
                  <p className="people-access-footnote">
                    Confirming people only records who can manage this customer. It does not send email, create login
                    credentials, assign a paid seat, change permissions, or move money.
                  </p>
                  {activationReadiness ? (
                    <div className="people-access-boundary">
                      <div>
                        <strong>Optional platform login</strong>
                        <p>
                          {missingAccessRoleCount
                            ? "Finish confirming the required customer responsibilities first. "
                            : "Referral work can continue because the required people are confirmed. "}
                          Only continue here when a confirmed person must sign in to Amplifi.
                        </p>
                        <ul className="people-access-login-purpose" aria-label="Platform login setup purpose">
                          <li>First assign a platform seat for capacity and audit.</li>
                          <li>Then record whether login is required or not required.</li>
                          <li>Credentials and auth claims remain in the governed identity workflow.</li>
                        </ul>
                      </div>
                      <StatusBadge
                        label={formatDisplay(activationReadiness.activationReadiness.overallStatus)}
                        tone={statusTone(activationReadiness.activationReadiness.overallStatus)}
                      />
                    </div>
                  ) : null}
                  {provisioningMutation.error ? <ErrorPanel error={provisioningMutation.error} /> : null}
                  {provisioningResult ? (
                    <div className="success-panel">
                      <strong>
                        {provisioningResult.toLowerCase().includes("not assigned")
                          ? "Platform seat could not be assigned."
                          : "Platform seat recorded."}
                      </strong>{" "}
                      {provisioningResult}
                    </div>
                  ) : null}
                  {loginCompletionMutation.error ? <ErrorPanel error={loginCompletionMutation.error} /> : null}
                  {loginCompletionResult ? (
                    <div className="success-panel">
                      <strong>Login decision recorded.</strong> {loginCompletionResult}
                    </div>
                  ) : null}
                  {loginSetupRows.length ? (
                    <div className="people-access-login-setup" aria-label="Optional platform login setup">
                      <div>
                        <strong>Optional platform login steps</strong>
                        <p>
                          These people are confirmed for customer work. Assign a seat only when they need platform
                          access, then record the governed login decision.
                        </p>
                      </div>
                      <div className="people-access-login-list">
                        {loginSetupRows.map((item) => {
                          const membershipRef = getValue(item, ["membershipRef"], "");
                          const roleFamily = getValue(item, ["roleFamily"], "");
                          const subject = getValue(item, ["subject"], "");
                          const seatAssigned = item.provisioningReadiness === "SEAT_ASSIGNED";
                          const loginReadiness = loginCompletionReadinessByMembershipRef.get(membershipRef);
                          const reconciliation = identityLoginReconciliationByMembershipRef.get(membershipRef);
                          const loginStatus = loginReadiness?.loginCompletionStatus || "WAITING_FOR_SEAT";
                          const providerRef = approvedAuthProviderRef(technicalSetupReadiness);
                          const canRecordLoginCompletion = seatAssigned && Boolean(providerRef);
                          return (
                            <div className="people-access-login-row" key={`${membershipRef}-${roleFamily}`}>
                              <div>
                                <strong>{formatDisplay(getValue(item, ["displayName"], "Named person"))}</strong>
                                <span>
                                  {roleOptionForFamily(roleFamily).label} -{" "}
                                  {seatAssigned ? "Seat assigned" : "Seat not assigned"}
                                </span>
                                {reconciliation?.steps.length ? (
                                  <div
                                    aria-label={`${formatDisplay(
                                      getValue(item, ["displayName"], "Named person"),
                                    )} login setup progress`}
                                    className="people-access-login-steps"
                                  >
                                    {reconciliation.steps.map((step) => (
                                      <span
                                        className={`people-access-login-step people-access-login-step-${step.status.toLowerCase()}`}
                                        key={`${membershipRef}-${step.label}`}
                                        title={step.description}
                                      >
                                        {step.label}: {formatDisplay(step.status)}
                                      </span>
                                    ))}
                                  </div>
                                ) : null}
                                <p className="table-subtext">
                                  Login status: {formatDisplay(reconciliation?.loginStatus || loginStatus)}.{" "}
                                  {reconciliation?.nextAction ||
                                    (seatAssigned
                                      ? "Record login only if this person must sign in."
                                      : "Assign the platform seat before any login decision.")}
                                </p>
                              </div>
                              <div className="action-cell horizontal">
                                <button
                                  className="button secondary compact"
                                  disabled={seatAssigned || provisioningMutation.isPending}
                                  onClick={() => requestAccessProvisioning(membershipRef, roleFamily)}
                                  type="button"
                                >
                                  {provisioningMutation.isPending
                                    ? "Assigning"
                                    : seatAssigned
                                      ? "Seat assigned"
                                      : "Assign platform seat"}
                                </button>
                                {seatAssigned ? (
                                  <>
                                    <button
                                      className="button secondary compact"
                                      disabled={loginCompletionMutation.isPending}
                                      onClick={() =>
                                        requestLoginCompletion(membershipRef, roleFamily, subject, "LOGIN_NOT_REQUIRED")
                                      }
                                      type="button"
                                    >
                                      {loginCompletionMutation.isPending ? "Recording" : "Login not required"}
                                    </button>
                                    <button
                                      className="button secondary compact"
                                      disabled={!canRecordLoginCompletion || loginCompletionMutation.isPending}
                                      onClick={() =>
                                        requestLoginCompletion(
                                          membershipRef,
                                          roleFamily,
                                          subject,
                                          "PLATFORM_LOGIN_REQUIRED",
                                        )
                                      }
                                      title={
                                        providerRef
                                          ? "Record governed login completion evidence."
                                          : "Approve identity provider evidence in Integrations first."
                                      }
                                      type="button"
                                    >
                                      {providerRef ? "Record login completion" : "Needs provider evidence"}
                                    </button>
                                  </>
                                ) : null}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ) : null}
                  {activationReadiness?.activationReadiness.items.length ? (
                    <button
                      className="button secondary compact"
                      onClick={() => setShowAccessDiagnostics((current) => !current)}
                      type="button"
                    >
                      {showAccessDiagnostics ? "Hide access diagnostics" : "Show access diagnostics"}
                    </button>
                  ) : null}
                  {showAccessDiagnostics && activationReadiness?.activationReadiness.items.length ? (
                    <DataTable
                      rows={activationReadiness.activationReadiness.items}
                      emptyText="No activation readiness items returned."
                      columns={[
                        {
                          key: "person",
                          header: "Person",
                          render: (row) => (
                            <div>
                              <strong>{formatDisplay(getValue(row, ["displayName"], "Named person"))}</strong>
                              <div className="table-subtext">{formatDisplay(getValue(row, ["subject"], "No email identity returned"))}</div>
                            </div>
                          ),
                        },
                        {
                          key: "responsibility",
                          header: "Responsibility",
                          render: (row) => formatDisplay(getValue(row, ["roleFamily"], "Role")),
                        },
                        {
                          key: "readiness",
                          header: "Readiness",
                          render: (row) => (
                            <div>
                              <StatusBadge
                                label={formatDisplay(getValue(row, ["activationReadiness"], "Blocked"))}
                                tone={statusTone(getValue(row, ["activationReadiness"], "Blocked"))}
                              />
                              <div className="table-subtext">
                                Invite delivery: {formatDisplay(getValue(row, ["deliveryReadiness"], "Blocked"))}
                              </div>
                              <div className="table-subtext">
                                Contact: {formatDisplay(getValue(row, ["recipientContactStatus"], "Contact reference missing"))}
                              </div>
                            </div>
                          ),
                        },
                        {
                          key: "nextAction",
                          header: "Next action",
                          render: (row) => (
                            <span className="table-subtext">
                              {formatDisplay(getValue(row, ["nextAction"], "Review the access setup."))}
                            </span>
                          ),
                        },
                        {
                          key: "provisioning",
                          header: "Provisioning",
                          render: (row) => (
                            <div>
                              <StatusBadge
                                label={formatDisplay(getValue(row, ["provisioningReadiness"], "Separate workflow"))}
                                tone={statusTone(getValue(row, ["provisioningReadiness"], "Separate workflow"))}
                              />
                              <div className="table-subtext">
                                Seat: {formatDisplay(getValue(row, ["seatAssignmentStatus"], "Seat not assigned"))}
                              </div>
                              <div className="table-subtext">
                                Login permissions: {formatDisplay(getValue(row, ["authClaimStatus"], "Auth claims not propagated"))}
                              </div>
                            </div>
                          ),
                        },
                        {
                          key: "deliveryCheck",
                          header: "Invite email",
                          render: (row) => {
                            const membershipRef = getValue(row, ["membershipRef"], "");
                            const roleFamily = getValue(row, ["roleFamily"], "UNKNOWN");
                            const providerRef = inviteDeliveryProviderRef(technicalSetupReadiness);
                            const contactReady =
                              getValue(row, ["recipientContactStatus"], "") === "CONTACT_REFERENCE_PRESENT";
                            const canRequest =
                              Boolean(membershipRef && providerRef && contactReady) &&
                              getValue(row, ["membershipStatus"], "") === "INVITED";
                            const blocker = !contactReady
                              ? "Add work email first"
                              : !providerRef
                                ? "Provider not approved"
                                : "Safe check";
                            return (
                              <div className="action-cell">
                                <button
                                  className="button secondary compact"
                                  disabled={!canRequest || deliveryMutation.isPending}
                                  onClick={() => requestInviteDeliveryCheck(membershipRef, roleFamily)}
                                  type="button"
                                >
                                  {deliveryMutation.isPending ? "Sending" : "Send invite email"}
                                </button>
                                <span className="table-subtext">{blocker}</span>
                              </div>
                            );
                          },
                        },
                        {
                          key: "accessActivation",
                          header: "Accepted access",
                          render: (row) => {
                            const membershipRef = getValue(row, ["membershipRef"], "");
                            const subject = getValue(row, ["subject"], "");
                            const roleFamily = getValue(row, ["roleFamily"], "UNKNOWN");
                            const membershipStatus = getValue(row, ["membershipStatus"], "");
                            const readiness = getValue(row, ["activationReadiness"], "");
                            const canRequest =
                              Boolean(membershipRef && subject) && membershipStatus === "INVITED";
                            const blocker = !subject
                              ? "Missing person identity"
                              : membershipStatus === "ACTIVE"
                                ? "Already active"
                                : membershipStatus !== "INVITED"
                                  ? "Not invited"
                                  : readiness === "READY_TO_ACTIVATE"
                                    ? "Ready"
                                    : "Will validate gates";
                            return (
                              <div className="action-cell">
                                <button
                                  className="button secondary compact"
                                  disabled={!canRequest || activationMutation.isPending}
                                  onClick={() => requestAccessActivation(membershipRef, subject, roleFamily)}
                                  type="button"
                                >
                                  {activationMutation.isPending ? "Recording" : "Record accepted access"}
                                </button>
                                <span className="table-subtext">{blocker}</span>
                              </div>
                            );
                          },
                        },
                      ]}
                    />
                  ) : null}
                </div>
              </section>
              ) : null}

              {selectedModule === "integrations" || selectedModule === "technical" ? (
                <CustomerTechnicalSetupPage
                  account={selectedAccount}
                  customerName={customerName}
                  error={technicalSetupError}
                  externalTenantRef={selectedExternalTenantRef}
                  isLoading={isTechnicalSetupLoading}
                  readiness={technicalSetupReadiness}
                  selectedCustomerPath={selectedCustomerPath}
                />
              ) : null}

              {selectedModule === "journeys" ? (
                <CustomerJourneysPage
                  customerName={customerName}
                  externalTenantRef={selectedExternalTenantRef}
                  selectedAccount={selectedAccount}
                  selectedCustomerPath={selectedCustomerPath}
                />
              ) : null}

              {selectedModule === "programmes" ? (
                <CustomerProgrammesPage
                  customerName={customerName}
                  externalTenantRef={selectedExternalTenantRef}
                  selectedAccount={selectedAccount}
                  selectedCustomerPath={selectedCustomerPath}
                />
              ) : null}

              {selectedModule === "commercial" ? (
                <CustomerCommercialEntitlementPage
                  entitlement={commercialEntitlement}
                  error={commercialEntitlementError}
                  isLoading={isCommercialEntitlementLoading}
                  productionActivation={productionActivation}
                  productionActivationError={productionActivationError}
                  isProductionActivationLoading={isProductionActivationLoading}
                  selectedCustomerPath={selectedCustomerPath}
                />
              ) : null}

              {selectedModule === "health" ? (
              <section className="panel">
                <div className="panel-header">
                  <div>
                    <h2 className="panel-title">Account health detail</h2>
                    <div className="panel-subtitle">Plain-language setup gates for the selected customer.</div>
                  </div>
                  <StatusBadge label={`${goLiveDisabledCount} go-live blockers`} tone={goLiveDisabledCount ? "warning" : "success"} />
                </div>
                <div className="panel-body">
                  {accountFoundationActivationPanel}
                  {accountFoundationActivationResultPanel}
                  <DataTable
                    rows={readinessCategoryMap.map((area) => resolveReadinessArea(area, categories))}
                    emptyText="No readiness categories returned."
                    columns={[
                      {
                        key: "area",
                        header: "Area",
                        render: (row) => <strong>{formatDisplay(getValue(row, ["label"], "Area"))}</strong>,
                      },
                      {
                        key: "status",
                        header: "Status",
                        render: (row) => {
                          const label = formatDisplay(getValue(row, ["status"], "Check"));
                          return <StatusBadge label={label} tone={statusTone(label)} />;
                        },
                      },
                      {
                        key: "evidence",
                        header: "What it means",
                        render: (row) => <span className="table-subtext">{formatDisplay(getValue(row, ["evidence"], "No evidence summary returned."))}</span>,
                      },
                    ]}
                  />
                </div>
              </section>
              ) : null}

              {selectedModule === "campaigns" ? (
                customerSubModule === "new" ? (
                  <CustomerCampaignSetupCreatePage
                    customerName={customerName}
                    draft={campaignSetupDraft}
                    error={campaignSetupMutation.error}
                    isProgrammeVersionLoading={campaignProgrammesQuery.isLoading}
                    isSaving={campaignSetupMutation.isPending}
                    onChange={updateCampaignSetupDraft}
                    onSubmit={submitCampaignSetup}
                    programmeVersionError={campaignProgrammesQuery.error}
                    publishedProgrammes={campaignProgrammesQuery.data?.programmes || []}
                    result={campaignSetupResult}
                    selectedAccount={selectedAccount}
                    selectedCustomerPath={selectedCustomerPath}
                  />
                ) : customerSubModule === "settings" ? (
                  <CustomerCampaignPolicySettingsPage
                    customerName={customerName}
                    draft={campaignPolicyDraft}
                    error={campaignPolicyMutation.error}
                    externalTenantRef={selectedExternalTenantRef}
                    isSaving={campaignPolicyMutation.isPending}
                    onChange={updateCampaignPolicyDraft}
                    onSubmit={submitCampaignPolicySettings}
                    result={campaignPolicyResult}
                    selectedAccount={selectedAccount}
                    selectedCustomerPath={selectedCustomerPath}
                  />
                ) : customerSubModule === "review" ? (
                  <CustomerCampaignReviewPage
                    customerName={customerName}
                    draft={campaignReviewDraft}
                    error={campaignReviewSubmitMutation.error || campaignReviewDecisionMutation.error}
                    externalTenantRef={selectedExternalTenantRef}
                    isDeciding={campaignReviewDecisionMutation.isPending}
                    isSubmitting={campaignReviewSubmitMutation.isPending}
                    onChange={updateCampaignReviewDraft}
                    onDecisionSubmit={submitCampaignReviewDecision}
                    onReviewSubmit={submitCampaignReview}
                    result={campaignReviewResult}
                    selectedAccount={selectedAccount}
                    selectedCustomerPath={selectedCustomerPath}
                  />
                ) : (
                  <CustomerCampaignsPage
                    customerName={customerName}
                    customerQuery={customerQuery}
                    externalTenantRef={selectedExternalTenantRef}
                    selectedAccount={selectedAccount}
                    selectedCustomerPath={selectedCustomerPath}
                  />
                )
              ) : null}

              {selectedModule === "referrals" ? (
                <CustomerReferralsPage
                  customerName={customerName}
                  externalTenantRef={selectedExternalTenantRef}
                  selectedAccount={selectedAccount}
                />
              ) : null}

              {selectedModule === "referrers" ? (
                <CustomerReferrersPage
                  customerName={customerName}
                  externalTenantRef={selectedExternalTenantRef}
                  selectedAccount={selectedAccount}
                />
              ) : null}

              {selectedModule === "links" ? (
                <CustomerLinksAndCodesPage
                  customerName={customerName}
                  externalTenantRef={selectedExternalTenantRef}
                  selectedAccount={selectedAccount}
                  selectedCustomerPath={selectedCustomerPath}
                />
              ) : null}

              {selectedModule === "reports" ? (
                <CustomerReportsPage
                  customerName={customerName}
                  externalTenantRef={selectedExternalTenantRef}
                  selectedAccount={selectedAccount}
                  selectedCustomerPath={selectedCustomerPath}
                />
              ) : null}

              {selectedModule === "support" ? (
                <CustomerSupportCasesPage
                  cases={supportCases}
                  customerName={customerName}
                  customerQuery={customerQuery}
                  draft={supportCaseDraft}
                  error={
                    supportCasesQuery.error ||
                    supportCaseMutation.error ||
                    supportCaseLifecycleMutation.error ||
                    supportCaseAssignmentMutation.error
                  }
                  assignmentDraft={supportCaseAssignmentDraft}
                  assignmentResult={supportCaseAssignmentResult}
                  isLoading={supportCasesQuery.isLoading}
                  isAssignmentSaving={supportCaseAssignmentMutation.isPending}
                  isLifecycleSaving={supportCaseLifecycleMutation.isPending}
                  isReadinessLoading={supportRepairReplayReadinessQuery.isLoading}
                  isSaving={supportCaseMutation.isPending}
                  lifecycleDraft={supportCaseLifecycleDraft}
                  lifecycleResult={supportCaseLifecycleResult}
                  onChange={updateSupportCaseDraft}
                  onAssignmentChange={setSupportCaseAssignmentDraft}
                  onAssignmentSubmit={submitSupportCaseAssignment}
                  onLifecycleChange={setSupportCaseLifecycleDraft}
                  onReadinessCaseChange={setSupportReadinessCaseRef}
                  onLifecycleSubmit={submitSupportCaseLifecycle}
                  onSubmit={submitSupportCase}
                  readiness={supportRepairReplayReadinessQuery.data || null}
                  readinessCaseRef={selectedSupportReadinessCase?.caseRef || ""}
                  readinessError={supportRepairReplayReadinessQuery.error}
                  result={supportCaseResult}
                  selectedCustomerPath={selectedCustomerPath}
                />
              ) : null}

              {selectedModule === "attribution" ? (
                <CustomerCampaignAttributionPage
                  customerName={customerName}
                  externalTenantRef={selectedExternalTenantRef}
                  selectedAccount={selectedAccount}
                  selectedCustomerPath={selectedCustomerPath}
                />
              ) : null}

              {selectedModule === "progress" ? (
                <CustomerModulePage
                  customerName={customerName}
                  customerQuery={customerQuery}
                  module={selectedModule}
                />
              ) : null}

              {selectedModule === "home" ? (
              <section className="customer-context-note">
                Not on this page: customer settings form, people invite form, or full health table. Those live on their own customer routes so the home stays short.
              </section>
              ) : null}
            </>
          ) : (
            <section className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">No customer selected yet</h2>
                  <div className="panel-subtitle">
                    Select a customer above, or create one if the list is empty.
                  </div>
                </div>
                <Link className="button" to="/admin/referral-saas/account-setup">
                  Create customer
                </Link>
              </div>
            </section>
          )}

          {!accountId ? (
          <section className="panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Setup draft fallback</h2>
                <div className="panel-subtitle">
                  Use this only when saved setup evidence exists but the customer has not become a durable customer profile yet.
                </div>
              </div>
              <StatusBadge label={`${draftSelector?.items?.length || 0} drafts`} tone={draftSelector?.items?.length ? "info" : "neutral"} />
            </div>
            <div className="panel-body route-list">
              {isDraftSelectorLoading ? <LoadingState label="Loading setup drafts" /> : null}
              {draftSelectorError ? <ErrorPanel error={draftSelectorError} /> : null}
              {!isDraftSelectorLoading && !draftSelectorError && (draftSelector?.items || []).length === 0 ? (
                <div className="empty-state">
                  No saved setup drafts found for this customer scope.
                </div>
              ) : null}
              {!isDraftSelectorLoading && !draftSelectorError
                ? (draftSelector?.items || []).map((draft) => (
                    <button
                      className="route-item route-link"
                      key={draft.draft_ref}
                      onClick={() => {
                        setDraftExternalTenantRef(draft.external_tenant_ref);
                        setDraftOrganisationRef(draft.organisation_ref);
                        setAppliedExternalTenantRef(draft.external_tenant_ref);
                        setAppliedOrganisationRef(draft.organisation_ref);
                      }}
                      type="button"
                    >
                      <div>
                        <div className="route-name">{draft.organisation_ref || draft.draft_ref}</div>
                        <div className="route-path">
                          {draft.external_tenant_ref} - {formatDisplay(draft.draft_status || "Draft evidence")}
                        </div>
                      </div>
                      <StatusBadge label="Load draft evidence" tone="info" />
                    </button>
                  ))
                : null}
            </div>
          </section>
          ) : null}
        </>
      ) : null}
    </>
  );
}

function CustomerReferralsPage({
  customerName,
  externalTenantRef,
  selectedAccount,
}: {
  customerName: string;
  externalTenantRef: string;
  selectedAccount?: AccountRegistryItem;
}) {
  const { refreshKey } = useRefreshContext();
  const [selectedReferralTrackId, setSelectedReferralTrackId] = useState("");
  const {
    data: referralListResponse,
    error: referralListError,
    isLoading: isReferralListLoading,
  } = useReferralSaasAccountReferralList(
    selectedAccount?.accountId || "",
    externalTenantRef,
    Boolean(selectedAccount && externalTenantRef),
    refreshKey,
  );
  const referrals = referralListResponse?.referrals || [];

  useEffect(() => {
    if (!selectedReferralTrackId.trim() && referrals[0]?.referralTrackId) {
      setSelectedReferralTrackId(referrals[0].referralTrackId);
    }
  }, [referrals, selectedReferralTrackId]);

  const {
    data: referralDetailResponse,
    error: referralDetailError,
    isLoading: isReferralDetailLoading,
  } = useReferralSaasAccountReferralDetail(
    selectedAccount?.accountId || "",
    selectedReferralTrackId,
    externalTenantRef,
    Boolean(selectedAccount && externalTenantRef && selectedReferralTrackId.trim()),
    refreshKey,
  );
  const selectedReferral =
    referralDetailResponse?.referral ||
    referrals.find((referral) => referral.referralTrackId === selectedReferralTrackId);
  const timelineEvidenceSummary = referralDetailResponse?.referral.timelineEvidenceSummary;
  const missingEvidenceCount = referrals.reduce(
    (total, referral) => total + referral.missingEvidence.length,
    0,
  );
  const activeCount = referrals.filter((referral) => !referral.isComplete).length;

  return (
    <section className="panel customer-module-page">
      <div className="panel-header">
        <div>
          <div className="page-kicker">Referral SaaS &gt; {customerName} &gt; Referrals</div>
          <h2 className="panel-title">Referrals</h2>
          <div className="panel-subtitle">
            Inspect customer-scoped referral journeys, safe status, missing evidence, and timeline anchors.
          </div>
        </div>
        <StatusBadge label="Read only" tone="info" />
      </div>
      <div className="panel-body route-list">
        <div className="grid-3">
          <KpiCard
            label="Referrals"
            value={String(referrals.length)}
            footnote="Customer-scoped journeys returned"
            icon={ListChecks}
          />
          <KpiCard
            label="Open journeys"
            value={String(activeCount)}
            footnote="Not marked complete yet"
            icon={Target}
          />
          <KpiCard
            label="Evidence gaps"
            value={String(missingEvidenceCount)}
            footnote="Missing safe proof across returned referrals"
            icon={AlertCircle}
          />
        </div>

        <div className="wizard-status-card">
          <div>
            <strong>What this page does</strong>
            <p>
              Shows the referrals linked to {customerName}, their current state, and the safe evidence we have. It does not repair, replay, reassign, activate campaigns, send webhooks, or move money.
            </p>
          </div>
          <StatusBadge label="Customer scoped" tone="success" />
        </div>

        {isReferralListLoading ? <LoadingState label="Loading customer referrals" /> : null}
        {referralListError ? <ErrorPanel error={referralListError} /> : null}
        <DataTable
          rows={referrals}
          emptyText="No referrals are attached to this customer yet. Create and validate referral journeys from the campaign and link/code workflows first."
          columns={[
            {
              key: "referral",
              header: "Referral",
              render: (row) => {
                const referral = row as (typeof referrals)[number];
                const selected = referral.referralTrackId === selectedReferralTrackId;
                return (
                  <button
                    className={`button ${selected ? "button-primary" : "button-secondary"}`}
                    onClick={() => setSelectedReferralTrackId(referral.referralTrackId)}
                    type="button"
                  >
                    {referral.referralCode || referral.referralTrackId}
                  </button>
                );
              },
            },
            {
              key: "status",
              header: "Status",
              render: (row) => (
                <StatusBadge
                  label={formatDisplay(getValue(row, ["displayStatus"], getValue(row, ["status"], "Unknown")))}
                  tone={statusTone(String(getValue(row, ["status"], "")))}
                />
              ),
            },
            {
              key: "progress",
              header: "Progress",
              render: (row) => (
                <span>
                  {formatDisplay(getValue(row, ["progressPercent"], "0"))}% -{" "}
                  {formatDisplay(getValue(row, ["progressBand"], "No band"))}
                </span>
              ),
            },
            {
              key: "campaign",
              header: "Campaign",
              render: (row) => formatDisplay(getValue(row, ["campaignCode"], "Not linked")),
            },
            {
              key: "missingEvidence",
              header: "Missing evidence",
              render: (row) => {
                const missingEvidence = getNestedValue(row, ["missingEvidence"], []);
                const missing = Array.isArray(missingEvidence) ? missingEvidence : [];
                return missing.length ? (
                  <span className="table-subtext">{missing.map((item) => formatDisplay(item)).join(", ")}</span>
                ) : (
                  <StatusBadge label="Evidence OK" tone="success" />
                );
              },
            },
          ]}
        />

        {isReferralDetailLoading ? <LoadingState label="Loading referral detail" /> : null}
        {referralDetailError ? <ErrorPanel error={referralDetailError} /> : null}
        {selectedReferral ? (
          <div className="wizard-status-card">
            <div>
              <strong>Selected referral detail</strong>
              <p>
                {selectedReferral.referralCode || selectedReferral.referralTrackId} -{" "}
                {formatDisplay(selectedReferral.displayStatus || selectedReferral.status)}.{" "}
                {selectedReferral.nextMilestone
                  ? `Next milestone: ${formatDisplay(selectedReferral.nextMilestone)}.`
                  : "No next milestone returned."}
              </p>
              <p className="muted">
                Public referrer handle:{" "}
                {formatDisplay(selectedReferral.publicReferrerHandle || "Not returned")} | Referee alias:{" "}
                {formatDisplay(selectedReferral.refereeAlias || "Not returned")}
              </p>
            </div>
            <StatusBadge
              label={selectedReferral.missingEvidence.length ? "Evidence gaps" : "Evidence OK"}
              tone={selectedReferral.missingEvidence.length ? "warning" : "success"}
            />
          </div>
        ) : null}

        {timelineEvidenceSummary ? (
          <div className="wizard-status-card">
            <div>
              <strong>Timeline evidence posture</strong>
              <p>
                {timelineEvidencePlainLanguage(timelineEvidenceSummary.recoveryPosture)}{" "}
                {timelineEvidenceSummary.eventCount} event
                {timelineEvidenceSummary.eventCount === 1 ? "" : "s"} returned,{" "}
                {timelineEvidenceSummary.sourceMatchedCount} matched to source inbox evidence.
              </p>
              <p className="muted">
                Missing source proof: {timelineEvidenceSummary.missingSourceEvidenceCount}. Missing idempotency
                proof: {timelineEvidenceSummary.missingIdempotencyEvidenceCount}. Dedupe replays:{" "}
                {timelineEvidenceSummary.duplicateReplayCount}. Failed or delayed source events:{" "}
                {timelineEvidenceSummary.failedOrDelayedCount}.
              </p>
            </div>
            <StatusBadge
              label={formatDisplay(timelineEvidenceSummary.recoveryPosture)}
              tone={timelineEvidenceTone(timelineEvidenceSummary.recoveryPosture)}
            />
          </div>
        ) : null}

        {referralDetailResponse?.referral.timeline ? (
          <DataTable
            rows={referralDetailResponse.referral.timeline}
            emptyText="No progress timeline events returned for this referral yet."
            columns={[
              {
                key: "eventType",
                header: "Timeline step",
                render: (row) => (
                  <div>
                    <strong>
                      #{formatDisplay(getValue(row, ["sequence"], "?"))}{" "}
                      {formatDisplay(getValue(row, ["eventType"], "Unknown"))}
                    </strong>
                    <div className="table-subtext">
                      Source: {formatDisplay(getValue(row, ["sourceSystem"], "Not returned"))}
                    </div>
                  </div>
                ),
              },
              {
                key: "when",
                header: "When",
                render: (row) => (
                  <div>
                    <div>Occurred: {formatDisplay(getValue(row, ["occurredAt"], "Not returned"))}</div>
                    <div className="table-subtext">
                      Received: {formatDisplay(getValue(row, ["receivedAt"], "Not returned"))}
                    </div>
                  </div>
                ),
              },
              {
                key: "safeEvidence",
                header: "Safe evidence",
                render: (row) => {
                  const sourceEvidence = getNestedValue(row, ["sourceEvidence"], []);
                  const missingEvidence = getNestedValue(row, ["missingEvidence"], []);
                  const evidence = Array.isArray(sourceEvidence) ? sourceEvidence : [];
                  const missing = Array.isArray(missingEvidence) ? missingEvidence : [];
                  return (
                    <div>
                      <div>
                        {evidence.length
                          ? evidence.map((item) => formatDisplay(item)).join(", ")
                          : "No source evidence returned"}
                      </div>
                      {missing.length ? (
                        <div className="table-subtext">
                          Missing: {missing.map((item) => formatDisplay(item)).join(", ")}
                        </div>
                      ) : (
                        <div className="table-subtext">No missing event evidence.</div>
                      )}
                    </div>
                  );
                },
              },
              {
                key: "recoveryPosture",
                header: "Recovery posture",
                render: (row) => {
                  const posture = String(getValue(row, ["recoveryPosture"], "UNKNOWN"));
                  return <StatusBadge label={formatDisplay(posture)} tone={timelineEvidenceTone(posture)} />;
                },
              },
            ]}
          />
        ) : null}

        <div className="customer-context-note">
          Redacted here: internal tenant identifiers, raw referrer/referee UCNs, raw progress payloads, event hashes, and dedupe keys.
        </div>
      </div>
    </section>
  );
}

function CustomerReferrersPage({
  customerName,
  externalTenantRef,
  selectedAccount,
}: {
  customerName: string;
  externalTenantRef: string;
  selectedAccount?: AccountRegistryItem;
}) {
  const { refreshKey } = useRefreshContext();
  const [selectedSafeReferrerKey, setSelectedSafeReferrerKey] = useState("");
  const {
    data: referrerListResponse,
    error: referrerListError,
    isLoading: isReferrerListLoading,
  } = useReferralSaasAccountReferrerList(
    selectedAccount?.accountId || "",
    externalTenantRef,
    Boolean(selectedAccount && externalTenantRef),
    refreshKey,
  );
  const referrers = referrerListResponse?.referrers || [];

  useEffect(() => {
    if (!selectedSafeReferrerKey.trim() && referrers[0]?.safeReferrerKey) {
      setSelectedSafeReferrerKey(referrers[0].safeReferrerKey);
    }
  }, [referrers, selectedSafeReferrerKey]);

  const {
    data: referrerDetailResponse,
    error: referrerDetailError,
    isLoading: isReferrerDetailLoading,
  } = useReferralSaasAccountReferrerDetail(
    selectedAccount?.accountId || "",
    selectedSafeReferrerKey,
    externalTenantRef,
    Boolean(selectedAccount && externalTenantRef && selectedSafeReferrerKey.trim()),
    refreshKey,
  );
  const selectedReferrer =
    referrerDetailResponse?.referrer ||
    referrers.find((referrer) => referrer.safeReferrerKey === selectedSafeReferrerKey);
  const referralCount = referrers.reduce((total, referrer) => total + referrer.referralCount, 0);
  const attributedCount = referrers.reduce(
    (total, referrer) => total + referrer.attributedReferralCount,
    0,
  );
  const missingEvidenceCount = referrers.reduce(
    (total, referrer) => total + referrer.missingEvidenceCount,
    0,
  );

  return (
    <section className="panel customer-module-page">
      <div className="panel-header">
        <div>
          <div className="page-kicker">Referral SaaS &gt; {customerName} &gt; Referrers</div>
          <h2 className="panel-title">Referrers</h2>
          <div className="panel-subtitle">
            Group referral activity by privacy-safe referrer labels. Raw identity, tenant identifiers, and customer identifiers stay hidden.
          </div>
        </div>
        <StatusBadge label="Read only" tone="info" />
      </div>
      <div className="panel-body route-list">
        <div className="grid-3">
          <KpiCard
            label="Safe referrers"
            value={String(referrers.length)}
            footnote="Directory rows returned"
            icon={Users}
          />
          <KpiCard
            label="Referral activity"
            value={String(referralCount)}
            footnote="Journeys grouped under safe labels"
            icon={ListChecks}
          />
          <KpiCard
            label="Attribution evidence"
            value={String(attributedCount)}
            footnote={`${missingEvidenceCount} safe evidence gaps`}
            icon={Target}
          />
        </div>

        <div className="wizard-status-card">
          <div>
            <strong>What this page answers</strong>
            <p>
              Which referrers are driving activity for {customerName}, which campaigns they touch, and what safe evidence is still missing. It does not expose raw UCNs, create identities, reassign credit, or change campaigns.
            </p>
          </div>
          <StatusBadge label="Safe dimensions" tone="success" />
        </div>

        {isReferrerListLoading ? <LoadingState label="Loading safe referrer directory" /> : null}
        {referrerListError ? <ErrorPanel error={referrerListError} /> : null}
        <DataTable
          rows={referrers}
          emptyText="No safe referrers are visible for this customer yet. Validate referral journeys first, then return here to group activity."
          columns={[
            {
              key: "referrer",
              header: "Referrer",
              render: (row) => {
                const referrer = row as (typeof referrers)[number];
                const selected = referrer.safeReferrerKey === selectedSafeReferrerKey;
                return (
                  <button
                    className={`button ${selected ? "button-primary" : "button-secondary"}`}
                    onClick={() => setSelectedSafeReferrerKey(referrer.safeReferrerKey)}
                    type="button"
                  >
                    {referrer.displayLabel}
                  </button>
                );
              },
            },
            {
              key: "maskedReferrerIdentifier",
              header: "Safe identifier",
              render: (row) => formatDisplay(getValue(row, ["maskedReferrerIdentifier"], "Hidden")),
            },
            {
              key: "referralCount",
              header: "Referrals",
              render: (row) => getValue(row, ["referralCount"], "0"),
            },
            {
              key: "campaigns",
              header: "Campaigns",
              render: (row) => {
                const campaigns = getNestedValue(row, ["campaigns"], []);
                return Array.isArray(campaigns) && campaigns.length
                  ? campaigns.map((campaign) => formatDisplay(campaign)).join(", ")
                  : "Not linked";
              },
            },
            {
              key: "missingEvidenceCount",
              header: "Evidence",
              render: (row) => {
                const count = Number(getValue(row, ["missingEvidenceCount"], "0"));
                return count ? (
                  <StatusBadge label={`${count} gaps`} tone="warning" />
                ) : (
                  <StatusBadge label="Evidence OK" tone="success" />
                );
              },
            },
          ]}
        />

        {isReferrerDetailLoading ? <LoadingState label="Loading referrer detail" /> : null}
        {referrerDetailError ? <ErrorPanel error={referrerDetailError} /> : null}
        {selectedReferrer ? (
          <div className="wizard-status-card">
            <div>
              <strong>{selectedReferrer.displayLabel}</strong>
              <p>
                {selectedReferrer.referralCount} referrals, {selectedReferrer.completedReferralCount} completed,{" "}
                {selectedReferrer.attributedReferralCount} with attribution evidence.
              </p>
              <p className="muted">
                Safe identifier: {selectedReferrer.maskedReferrerIdentifier}. Last seen:{" "}
                {formatDisplay(selectedReferrer.lastSeenAt || "Not returned")}.
              </p>
            </div>
            <StatusBadge
              label={selectedReferrer.missingEvidenceCount ? "Evidence gaps" : "Evidence OK"}
              tone={selectedReferrer.missingEvidenceCount ? "warning" : "success"}
            />
          </div>
        ) : null}

        {selectedReferrer?.dimensions?.length ? (
          <div className="grid-3">
            {selectedReferrer.dimensions.map((dimension) => (
              <div className="wizard-status-card" key={dimension.name}>
                <div>
                  <strong>{formatDisplay(dimension.name)}</strong>
                  <p>
                    {dimension.values.length
                      ? dimension.values
                          .map((value) => `${formatDisplay(value.label)} (${value.count})`)
                          .join(", ")
                      : "No dimension values returned yet."}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : null}

        {referrerDetailResponse?.referrer.referrals ? (
          <DataTable
            rows={referrerDetailResponse.referrer.referrals}
            emptyText="No referrals are attached to this safe referrer key yet."
            columns={[
              {
                key: "referralTrackId",
                header: "Referral",
                render: (row) => (
                  <strong>
                    {formatDisplay(getValue(row, ["referralCode"], getValue(row, ["referralTrackId"], "Unknown")))}
                  </strong>
                ),
              },
              {
                key: "status",
                header: "Status",
                render: (row) => (
                  <StatusBadge
                    label={formatDisplay(getValue(row, ["displayStatus"], getValue(row, ["status"], "Unknown")))}
                    tone={statusTone(String(getValue(row, ["status"], "")))}
                  />
                ),
              },
              {
                key: "campaignCode",
                header: "Campaign",
                render: (row) => formatDisplay(getValue(row, ["campaignCode"], "Not linked")),
              },
              {
                key: "lastProgressAt",
                header: "Last activity",
                render: (row) => formatDisplay(getValue(row, ["lastProgressAt"], "Not returned")),
              },
            ]}
          />
        ) : null}

        <div className="customer-context-note">
          Redacted here: internal tenant identifiers, raw referrer/referee UCNs, raw customer identifiers, raw progress payloads, event hashes, dedupe keys, secrets, and tokens.
        </div>
      </div>
    </section>
  );
}

function CustomerCampaignsPage({
  customerName,
  customerQuery,
  externalTenantRef,
  selectedAccount,
  selectedCustomerPath,
}: {
  customerName: string;
  customerQuery: string;
  externalTenantRef: string;
  selectedAccount?: AccountRegistryItem;
  selectedCustomerPath: string;
}) {
  const { refreshKey } = useRefreshContext();
  const [campaignListRefreshKey, setCampaignListRefreshKey] = useState(0);
  const [campaignCode, setCampaignCode] = useState("");
  const [operation, setOperation] = useState<CampaignReadinessOperation>("CONTROL_PLANE_VIEW");
  const [opportunityId, setOpportunityId] = useState("");
  const [lifecycleResult, setLifecycleResult] = useState<string | null>(null);
  const campaignRefreshKey = refreshKey + campaignListRefreshKey;
  const {
    data: campaignListResponse,
    error: campaignListError,
    isLoading: isCampaignListLoading,
  } = useReferralSaasAccountCampaignList(
    selectedAccount?.accountId || "",
    externalTenantRef,
    Boolean(selectedAccount && externalTenantRef),
    campaignRefreshKey,
  );
  const campaigns = campaignListResponse?.campaigns || [];
  const lifecycleMutation = useMutation({
    mutationFn: ({
      action,
      selectedCampaignCode,
    }: {
      action: ReferralSaasCampaignLifecycleAction;
      selectedCampaignCode: string;
    }) =>
      recordReferralSaasAccountCampaignLifecycleCommand({
        accountRef: selectedAccount?.accountId || "",
        campaignCode: selectedCampaignCode,
        refType: "external_tenant_ref",
        externalRef: externalTenantRef,
        context: "setup",
        action,
        reason: `${campaignLifecycleActionLabel(action)} campaign from the selected customer campaign workspace.`,
        operatorNotes:
          "Referral SaaS customer-scoped lifecycle command. No links, validation tracks, webhooks, invites, seats, credentials, campaign activation, or money movement requested.",
        idempotencyKey: safeIdempotencyKey(
          "customer-campaign-lifecycle",
          selectedAccount?.accountId || "",
          selectedCampaignCode,
          action,
          new Date().toISOString(),
        ),
        correlationId: safeIdempotencyKey(
          "customer-campaign-lifecycle-correlation",
          selectedAccount?.accountId || "",
          selectedCampaignCode,
          action,
          new Date().toISOString(),
        ),
      }),
    onSuccess: (response) => {
      const lifecycle = response.campaignLifecycle.campaignLifecycle;
      setCampaignCode(response.campaignLifecycle.campaignRef);
      setLifecycleResult(lifecycle.plainLanguage);
      setCampaignListRefreshKey((current) => current + 1);
    },
  });

  useEffect(() => {
    if (!campaignCode.trim() && campaigns[0]?.campaignCode) {
      setCampaignCode(campaigns[0].campaignCode);
    }
  }, [campaignCode, campaigns]);

  const {
    data: campaignReadinessResponse,
    error,
    isLoading,
  } = useReferralSaasAccountCampaignReadiness(
    selectedAccount?.accountId || "",
    campaignCode,
    externalTenantRef,
    operation,
    opportunityId,
    Boolean(selectedAccount && externalTenantRef && campaignCode.trim()),
    refreshKey,
  );
  const readiness = campaignReadinessResponse?.readiness || {};
  const blockers = asArray(getNestedValue(readiness, ["blockers"], []));
  const warnings = asArray(getNestedValue(readiness, ["warnings"], []));
  const unknowns = asArray(getNestedValue(readiness, ["unknowns"], []));
  const readinessStatus = formatCampaignLabel(
    getNestedValue(readiness, ["readiness"], getNestedValue(readiness, ["status"], "Not checked")),
  );
  const canProceed = Boolean(getNestedValue(readiness, ["can_proceed"], getNestedValue(readiness, ["canProceed"], false)));
  const evidenceRows = [
    ...blockers.map((item) => ({ ...asRecord(item), severity: "Blocker" })),
    ...warnings.map((item) => ({ ...asRecord(item), severity: "Warning" })),
    ...unknowns.map((item) => ({ ...asRecord(item), severity: "Unknown" })),
  ];

  return (
    <section className="panel customer-module-page">
      <div className="panel-header">
        <div>
          <div className="page-kicker">Referral SaaS &gt; {customerName} &gt; Campaigns</div>
          <h2 className="panel-title">Campaigns</h2>
          <div className="panel-subtitle">
            Check campaign readiness inside this customer profile before creating links, launching tests, or moving to campaign setup.
          </div>
        </div>
        <div className="customer-header-actions">
          <Link className="button secondary" to={`${selectedCustomerPath}/campaigns/settings`}>
            Policy settings
          </Link>
          <Link className="button secondary" to={`${selectedCustomerPath}/campaigns/review`}>
            Review campaign
          </Link>
          <Link className="button" to={`${selectedCustomerPath}/campaigns/new`}>
            Create campaign setup
          </Link>
          <StatusBadge label="Customer scoped" tone="success" />
        </div>
      </div>
      <div className="panel-body route-list">
        <div className="wizard-status-card">
          <div>
            <strong>Selected customer</strong>
            <p>
              {selectedAccount?.accountCode || "No account code"} - {externalTenantRef || "No customer reference"}
            </p>
          </div>
          <StatusBadge label="No tenant code entry" tone="success" />
        </div>

        <div>
          <h3 className="section-heading">Campaigns for this customer</h3>
          <p className="muted">Choose one campaign before checking readiness. This list is loaded from the selected customer profile.</p>
        </div>
        {isCampaignListLoading ? <LoadingState label="Loading customer campaigns" /> : null}
        {campaignListError ? <ErrorPanel error={campaignListError} /> : null}
        <DataTable
          rows={campaigns}
          emptyText="No campaigns are attached to this customer yet. Use Create campaign setup to save the first inactive campaign draft."
          columns={[
            {
              key: "campaign",
              header: "Campaign",
              render: (row) => {
                const campaign = row as (typeof campaigns)[number];
                const selected = campaign.campaignCode === campaignCode.trim();
                return (
                  <button
                    className={`button ${selected ? "button-primary" : "button-secondary"}`}
                    onClick={() => setCampaignCode(campaign.campaignCode)}
                    type="button"
                  >
                    {campaign.name || campaign.campaignCode}
                  </button>
                );
              },
            },
            {
              key: "campaignCode",
              header: "Code",
              render: (row) => <strong>{formatDisplay(getValue(row, ["campaignCode"], "Unknown"))}</strong>,
            },
            {
              key: "status",
              header: "Status",
              render: (row) => <StatusBadge label={formatDisplay(getValue(row, ["status"], "Unknown"))} tone={statusTone(String(getValue(row, ["status"], "")))} />,
            },
            {
              key: "policyStatus",
              header: "Policy",
              render: (row) => <StatusBadge label={formatDisplay(getValue(row, ["policyStatus"], "Unknown"))} tone={statusTone(String(getValue(row, ["policyStatus"], "")))} />,
            },
            {
              key: "usesCount",
              header: "Uses",
              render: (row) => <span>{formatDisplay(getValue(row, ["usesCount"], "0"))}</span>,
            },
            {
              key: "action",
              header: "Action",
              render: (row) => {
                const campaign = row as (typeof campaigns)[number];
                const actions = campaignLifecycleActionsFor(String(campaign.lifecycle || campaign.status || ""));
                return (
                  <div className="customer-header-actions">
                    <Link
                      className="button button-secondary"
                      to={`${selectedCustomerPath}/campaigns/settings?campaign=${encodeURIComponent(
                        campaign.campaignCode,
                      )}`}
                    >
                      Policy settings
                    </Link>
                    <Link
                      className="button button-secondary"
                      to={`${selectedCustomerPath}/campaigns/review?campaign=${encodeURIComponent(
                        campaign.campaignCode,
                      )}`}
                    >
                      Review
                    </Link>
                    {actions.map((action) => (
                      <button
                        className="button button-secondary"
                        disabled={lifecycleMutation.isPending}
                        key={`${campaign.campaignCode}-${action}`}
                        onClick={() =>
                          lifecycleMutation.mutate({
                            action,
                            selectedCampaignCode: campaign.campaignCode,
                          })
                        }
                        type="button"
                      >
                        {campaignLifecycleActionLabel(action)}
                      </button>
                    ))}
                  </div>
                );
              },
            },
          ]}
        />
        {lifecycleResult ? (
          <div className="wizard-summary-strip success">
            <div>
              <strong>Campaign lifecycle updated.</strong> {lifecycleResult}
            </div>
            <StatusBadge label="Governed command" tone="success" />
          </div>
        ) : null}
        {lifecycleMutation.error ? <ErrorPanel error={lifecycleMutation.error} /> : null}

        <form className="form-grid" onSubmit={(event) => event.preventDefault()}>
          <label>
            Selected campaign code
            <input
              onChange={(event) => setCampaignCode(event.target.value)}
              placeholder="Select a campaign or enter a known code"
              value={campaignCode}
            />
          </label>
          <label>
            Readiness check
            <select
              onChange={(event) => setOperation(event.target.value as CampaignReadinessOperation)}
              value={operation}
            >
              <option value="CONTROL_PLANE_VIEW">Review campaign setup</option>
              <option value="CREATE_TRACK">Create referral track</option>
              <option value="GENERATE_LINKS">Generate links</option>
              <option value="ACTIVATE_CAMPAIGN">Activate campaign</option>
            </select>
          </label>
          <label>
            Opportunity reference
            <input
              onChange={(event) => setOpportunityId(event.target.value)}
              placeholder="Optional"
              value={opportunityId}
            />
          </label>
        </form>

        {isLoading ? <LoadingState label="Checking campaign readiness" /> : null}
        {error ? <ErrorPanel error={error} /> : null}
        {!campaignCode.trim() && !isCampaignListLoading ? (
          <div className="wizard-summary-strip warning">
            <div>
              <strong>In plain English:</strong> Select an existing campaign first. If none exists, campaign creation is the next product workflow.
            </div>
            <StatusBadge label="No campaign selected" tone="warning" />
          </div>
        ) : null}
        {campaignReadinessResponse ? (
          <>
            <div className="grid-3">
              <KpiCard
                label="Campaign posture"
                value={readinessStatus}
                footnote="Resolved through the selected customer account"
                icon={Target}
              />
              <KpiCard
                label="Blockers"
                value={String(blockers.length)}
                footnote="Must be cleared before the selected operation"
                icon={AlertCircle}
              />
              <KpiCard
                label="Warnings"
                value={String(warnings.length + unknowns.length)}
                footnote={canProceed ? "Can proceed with attention" : "Needs review first"}
                icon={ListChecks}
              />
            </div>

            <div className={`wizard-summary-strip ${canProceed ? "success" : "warning"}`}>
              <div>
                <strong>In plain English:</strong>{" "}
                {canProceed
                  ? `${customerName} can continue with ${formatCampaignLabel(operation).toLowerCase()} for ${campaignCode.trim()}.`
                  : `${customerName} has campaign readiness items to resolve before ${formatCampaignLabel(operation).toLowerCase()} for ${campaignCode.trim()}.`}
              </div>
              <StatusBadge label={canProceed ? "Can proceed" : "Needs attention"} tone={canProceed ? "success" : "warning"} />
            </div>

            <DataTable
              rows={evidenceRows}
              emptyText="No blockers or warnings returned for this campaign check."
              columns={[
                {
                  key: "severity",
                  header: "Type",
                  render: (row) => <StatusBadge label={formatDisplay(getValue(row, ["severity"], "Info"))} tone={campaignEvidenceTone(getValue(row, ["severity"], "Info"))} />,
                },
                {
                  key: "code",
                  header: "Readiness item",
                  render: (row) => <strong>{formatCampaignLabel(getValue(row, ["code"], "Campaign check"))}</strong>,
                },
                {
                  key: "message",
                  header: "What it means",
                  render: (row) => <span className="table-subtext">{formatDisplay(getValue(row, ["message"], getValue(row, ["detail"], "No detail returned.")))}</span>,
                },
              ]}
            />

            <div className="wizard-status-card">
              <div>
                <strong>What this page will not do</strong>
                <p>
                  No campaign is created, no policy is changed, no links are generated, no campaign is activated, no go-live action is triggered, and no money moves.
                </p>
              </div>
              <StatusBadge label="Read only" tone="info" />
            </div>
          </>
        ) : null}

        <Link className="button button-secondary" to={`/admin/referral-saas/campaigns${customerQuery}`}>
          Open legacy campaign readiness workspace
        </Link>
      </div>
    </section>
  );
}

function CustomerCampaignAttributionPage({
  customerName,
  externalTenantRef,
  selectedAccount,
  selectedCustomerPath,
}: {
  customerName: string;
  externalTenantRef: string;
  selectedAccount?: AccountRegistryItem;
  selectedCustomerPath: string;
}) {
  const { refreshKey } = useRefreshContext();
  const {
    data: attributionResponse,
    error,
    isLoading,
  } = useReferralSaasAccountCampaignAttribution(
    selectedAccount?.accountId || "",
    externalTenantRef,
    Boolean(selectedAccount && externalTenantRef),
    refreshKey,
  );
  const {
    data: referralAttributionResponse,
    error: referralAttributionError,
    isLoading: isReferralAttributionLoading,
  } = useReferralSaasAccountReferralAttribution(
    selectedAccount?.accountId || "",
    externalTenantRef,
    Boolean(selectedAccount && externalTenantRef),
    refreshKey,
  );
  const attribution = attributionResponse?.campaignAttribution;
  const referralAttribution = referralAttributionResponse?.referralAttribution;
  const projections = attribution?.projections || [];
  const referralProjections = referralAttribution?.referralProjections || [];
  const referrerProjections = referralAttribution?.referrerProjections || [];

  return (
    <section className="panel customer-module-page">
      <div className="panel-header">
        <div>
          <div className="page-kicker">Referral SaaS &gt; {customerName} &gt; Attribution</div>
          <h2 className="panel-title">Attribution</h2>
          <div className="panel-subtitle">
            See which campaign sources drove activity and which referrers can be credited safely.
          </div>
        </div>
        <div className="customer-header-actions">
          <Link className="button secondary" to={`${selectedCustomerPath}/campaigns`}>
            Open campaigns
          </Link>
          <StatusBadge label="Customer scoped" tone="success" />
        </div>
      </div>
      <div className="panel-body route-list">
        {isLoading ? <LoadingState label="Loading campaign attribution" /> : null}
        {isReferralAttributionLoading ? <LoadingState label="Loading referral attribution" /> : null}
        {error ? <ErrorPanel error={error} /> : null}
        {referralAttributionError ? <ErrorPanel error={referralAttributionError} /> : null}

        {attribution ? (
          <>
            <div className="wizard-status-card">
              <div>
                <strong>Campaign attribution</strong>
                <p>Which campaign source, channel, or interaction appears to have driven referral activity.</p>
              </div>
              <StatusBadge label="Campaign evidence" tone="info" />
            </div>
            <div className="grid-4">
              <KpiCard
                label="Campaigns"
                value={String(attribution.campaignCount)}
                footnote="Customer campaigns included in this projection"
                icon={Target}
              />
              <KpiCard
                label="Sources"
                value={String(attribution.sourceCount)}
                footnote="Campaign/source combinations reviewed"
                icon={PlugZap}
              />
              <KpiCard
                label="High confidence"
                value={String(attribution.highConfidenceCount)}
                footnote="Sources with interaction and referral evidence"
                icon={CheckCircle2}
              />
              <KpiCard
                label="Needs evidence"
                value={String(attribution.missingEvidenceCount + attribution.conflictCount)}
                footnote="Missing or conflicting evidence to resolve"
                icon={AlertCircle}
              />
            </div>

            <div className={`wizard-summary-strip ${attribution.conflictCount ? "danger" : attribution.missingEvidenceCount ? "warning" : "success"}`}>
              <div>
                <strong>In plain English:</strong> {attribution.plainLanguage}
              </div>
              <StatusBadge label={formatCampaignLabel(attribution.status)} tone={attributionStatusTone(attribution.status)} />
            </div>

            <DataTable
              rows={projections}
              emptyText="No customer campaign attribution evidence is available yet."
              columns={[
                {
                  key: "campaign",
                  header: "Campaign",
                  render: (row) => {
                    const projection = row as ReferralSaasCampaignAttributionProjection;
                    return (
                      <div>
                        <strong>{formatDisplay(projection.campaignName || projection.campaignCode)}</strong>
                        <div className="table-subtext">
                          {projection.campaignCode} - {formatDisplay(projection.segment)}
                        </div>
                      </div>
                    );
                  },
                },
                {
                  key: "source",
                  header: "Source",
                  render: (row) => formatDisplay((row as ReferralSaasCampaignAttributionProjection).sourceChannel),
                },
                {
                  key: "confidence",
                  header: "Confidence",
                  render: (row) => {
                    const projection = row as ReferralSaasCampaignAttributionProjection;
                    return (
                      <div>
                        <StatusBadge
                          label={formatCampaignLabel(projection.confidence)}
                          tone={attributionConfidenceTone(projection.confidence)}
                        />
                        <div className="table-subtext">{formatCampaignLabel(projection.attributionStatus)}</div>
                      </div>
                    );
                  },
                },
                {
                  key: "evidence",
                  header: "Evidence",
                  render: (row) => {
                    const projection = row as ReferralSaasCampaignAttributionProjection;
                    return (
                      <span className="table-subtext">
                        {projection.interactionCount} interactions, {projection.linkedReferralCount} referrals, {projection.eventCount} events
                      </span>
                    );
                  },
                },
                {
                  key: "explanation",
                  header: "What it means",
                  render: (row) => {
                    const projection = row as ReferralSaasCampaignAttributionProjection;
                    const gaps = projection.gaps.length ? projection.gaps.join(" ") : "No evidence gaps returned.";
                    return (
                      <div>
                        <span>{projection.explanation}</span>
                        <div className="table-subtext">{gaps}</div>
                      </div>
                    );
                  },
                },
              ]}
            />

            <div className="customer-context-note">
              Redacted here: internal tenant identifiers, raw user identifiers, device fingerprints, IP addresses, QR payloads, raw event payloads, secrets, tokens, and money movement details.
            </div>
          </>
        ) : null}

        {referralAttribution ? (
          <>
            <div className="wizard-status-card">
              <div>
                <strong>Referral and referrer attribution</strong>
                <p>Who gets referral credit and why, using safe referrer dimensions instead of raw identity.</p>
              </div>
              <StatusBadge
                label={formatCampaignLabel(referralAttribution.status)}
                tone={attributionStatusTone(referralAttribution.status)}
              />
            </div>

            <div className="grid-4">
              <KpiCard
                label="Referrals"
                value={String(referralAttribution.referralCount)}
                footnote="Referral records reviewed for credit"
                icon={LinkIcon}
              />
              <KpiCard
                label="Referrers"
                value={String(referralAttribution.referrerCount)}
                footnote="Safe referrer dimensions"
                icon={Users}
              />
              <KpiCard
                label="Credited"
                value={String(referralAttribution.creditedReferralCount)}
                footnote="Referral records with explainable credit posture"
                icon={CheckCircle2}
              />
              <KpiCard
                label="Needs evidence"
                value={String(referralAttribution.missingEvidenceCount)}
                footnote="Credit paths needing more proof"
                icon={AlertCircle}
              />
            </div>

            <div className={`wizard-summary-strip ${referralAttribution.missingEvidenceCount ? "warning" : "success"}`}>
              <div>
                <strong>In plain English:</strong> {referralAttribution.plainLanguage}
              </div>
              <StatusBadge label="Who got credit" tone="success" />
            </div>

            <DataTable
              rows={referralProjections}
              emptyText="No referral credit evidence is available yet."
              columns={[
                {
                  key: "referral",
                  header: "Referral",
                  render: (row) => {
                    const projection = row as ReferralSaasReferralCreditProjection;
                    return (
                      <div>
                        <strong>{formatDisplay(projection.referralCode || projection.referralTrackId)}</strong>
                        <div className="table-subtext">
                          {formatDisplay(projection.campaignCode || "No campaign link")}
                        </div>
                      </div>
                    );
                  },
                },
                {
                  key: "referrer",
                  header: "Referrer",
                  render: (row) =>
                    formatDisplay((row as ReferralSaasReferralCreditProjection).publicReferrerHandle || "Safe referrer pending"),
                },
                {
                  key: "credit",
                  header: "Credit posture",
                  render: (row) => {
                    const projection = row as ReferralSaasReferralCreditProjection;
                    return (
                      <div>
                        <StatusBadge
                          label={formatCampaignLabel(projection.confidence)}
                          tone={attributionConfidenceTone(projection.confidence)}
                        />
                        <div className="table-subtext">{formatCampaignLabel(projection.creditStatus)}</div>
                      </div>
                    );
                  },
                },
                {
                  key: "evidence",
                  header: "Evidence",
                  render: (row) => {
                    const projection = row as ReferralSaasReferralCreditProjection;
                    return (
                      <span className="table-subtext">
                        {projection.progressEventCount} progress events, {projection.attributionEvidencePresent ? "attribution evidence" : "no attribution evidence"}
                      </span>
                    );
                  },
                },
                {
                  key: "why",
                  header: "Why",
                  render: (row) => {
                    const projection = row as ReferralSaasReferralCreditProjection;
                    const gaps = projection.gaps.length ? projection.gaps.join(" ") : "No credit evidence gaps returned.";
                    return (
                      <div>
                        <span>{projection.explanation}</span>
                        <div className="table-subtext">{gaps}</div>
                      </div>
                    );
                  },
                },
              ]}
            />

            <DataTable
              rows={referrerProjections}
              emptyText="No safe referrer dimensions are available yet."
              columns={[
                {
                  key: "referrer",
                  header: "Safe referrer",
                  render: (row) => {
                    const projection = row as ReferralSaasReferrerCreditProjection;
                    return (
                      <div>
                        <strong>{formatDisplay(projection.displayLabel)}</strong>
                        <div className="table-subtext">{projection.maskedReferrerIdentifier}</div>
                      </div>
                    );
                  },
                },
                {
                  key: "credit",
                  header: "Credit posture",
                  render: (row) => {
                    const projection = row as ReferralSaasReferrerCreditProjection;
                    return (
                      <div>
                        <StatusBadge
                          label={formatCampaignLabel(projection.creditStatus)}
                          tone={attributionStatusTone(projection.creditStatus)}
                        />
                        <div className="table-subtext">{formatCampaignLabel(projection.confidence)} confidence</div>
                      </div>
                    );
                  },
                },
                {
                  key: "activity",
                  header: "Activity",
                  render: (row) => {
                    const projection = row as ReferralSaasReferrerCreditProjection;
                    return `${projection.attributedReferralCount}/${projection.referralCount} credited referrals, ${projection.campaignCount} campaigns`;
                  },
                },
                {
                  key: "explanation",
                  header: "What it means",
                  render: (row) => {
                    const projection = row as ReferralSaasReferrerCreditProjection;
                    const gaps = projection.gaps.length ? projection.gaps.join(" ") : "No referrer evidence gaps returned.";
                    return (
                      <div>
                        <span>{projection.explanation}</span>
                        <div className="table-subtext">{gaps}</div>
                      </div>
                    );
                  },
                },
              ]}
            />

            <div className="customer-context-note">
              Referral/referrer credit uses safe dimensions only. Raw UCNs, raw customer identifiers, raw progress payloads, event hashes, attribution mutation, repair/replay, webhooks, billing, and money movement stay outside this page.
            </div>
          </>
        ) : null}
      </div>
    </section>
  );
}

function CustomerCampaignSetupCreatePage({
  customerName,
  draft,
  error,
  isProgrammeVersionLoading,
  isSaving,
  onChange,
  onSubmit,
  programmeVersionError,
  publishedProgrammes,
  result,
  selectedAccount,
  selectedCustomerPath,
}: {
  customerName: string;
  draft: CampaignSetupDraft;
  error: unknown;
  isProgrammeVersionLoading: boolean;
  isSaving: boolean;
  onChange: (values: Partial<CampaignSetupDraft>) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  programmeVersionError: unknown;
  publishedProgrammes: ReferralSaasProgrammeVersion[];
  result: ReferralSaasAccountCampaignSetupCreateResponse | null;
  selectedAccount?: AccountRegistryItem;
  selectedCustomerPath: string;
}) {
  const savedCampaign = result?.campaignSetup.campaign;
  const hasPublishedProgrammes = publishedProgrammes.length > 0;
  const selectedProgrammeVersion = publishedProgrammes.find(
    (version) => version.programmeVersionId === draft.programmeVersionId,
  );
  const binding = savedCampaign?.programmeBinding;
  const bindingRecord = asRecord(binding);
  const bindingProgrammeName = formatDisplay(
    String(getValue(bindingRecord, ["programmeName"], selectedProgrammeVersion?.programmeName || "Selected programme")),
  );
  const bindingVersionNumber = String(
    getValue(bindingRecord, ["programmeVersionNumber"], String(selectedProgrammeVersion?.versionNumber || 1)),
  );
  const bindingStatus = formatDisplay(String(getValue(bindingRecord, ["bindingStatus"], "Programme bound")));
  const canSave = Boolean(
    selectedAccount &&
      draft.name.trim() &&
      draft.segment.trim() &&
      draft.programmeVersionId.trim() &&
      hasPublishedProgrammes,
  );

  return (
    <section className="panel customer-module-page">
      <div className="panel-header">
        <div>
          <div className="page-kicker">Referral SaaS &gt; {customerName} &gt; Campaigns &gt; Create</div>
          <h2 className="panel-title">Create campaign setup</h2>
          <div className="panel-subtitle">
            Save an inactive campaign setup draft for this customer. Policy, links, readiness review, and launch stay separate.
          </div>
        </div>
        <StatusBadge label="Draft only" tone="warning" />
      </div>
      <div className="panel-body route-list">
        <div className="wizard-status-card">
          <div>
            <strong>Selected customer</strong>
            <p>
              {selectedAccount?.accountName || customerName} - {selectedAccount?.accountCode || "No account code"}
            </p>
          </div>
          <StatusBadge label="No tenant code entry" tone="success" />
        </div>

        {isProgrammeVersionLoading ? <LoadingState label="Loading published programmes" /> : null}
        {programmeVersionError ? <ErrorPanel error={programmeVersionError} /> : null}
        <form className="form-grid" onSubmit={onSubmit}>
          <div className="wizard-status-card form-grid-span">
            <div>
              <strong>Programme version required</strong>
              <p>
                Choose the published programme that packages this campaign's journey, defaults, incentives, and governance. Campaign activation is blocked until this is set.
              </p>
            </div>
            <StatusBadge
              label={hasPublishedProgrammes ? "Choose programme" : "Publish programme first"}
              tone={hasPublishedProgrammes ? "info" : "warning"}
            />
          </div>
          <label>
            Published programme
            <select
              disabled={!hasPublishedProgrammes}
              onChange={(event) => onChange({ programmeVersionId: event.target.value })}
              value={draft.programmeVersionId}
            >
              <option value="">
                {hasPublishedProgrammes ? "Choose a published programme" : "No published programmes yet"}
              </option>
              {publishedProgrammes.map((version) => (
                <option key={version.programmeVersionId} value={version.programmeVersionId}>
                  {formatDisplay(version.programmeName)} v{version.versionNumber} - {formatDisplay(
                    version.productCode,
                  )} / {formatDisplay(version.subProductCode)}
                </option>
              ))}
            </select>
            <small>
              Only published programmes for this customer are shown. Publish one from Customer settings &gt; Programmes first if this list is empty.
            </small>
          </label>
          <label>
            Campaign name
            <input
              onChange={(event) => onChange({ name: event.target.value })}
              placeholder="Example: Spring referral pilot"
              value={draft.name}
            />
          </label>
          <label>
            Audience or segment
            <input
              onChange={(event) => onChange({ segment: event.target.value })}
              placeholder="Example: Retail banking customers"
              value={draft.segment}
            />
          </label>
          <label>
            Starts on
            <input
              onChange={(event) => onChange({ startsAt: event.target.value })}
              type="date"
              value={draft.startsAt}
            />
          </label>
          <label>
            Ends on
            <input
              onChange={(event) => onChange({ endsAt: event.target.value })}
              type="date"
              value={draft.endsAt}
            />
          </label>
          <label>
            Maximum referrals
            <input
              min="1"
              onChange={(event) => onChange({ maxUses: event.target.value })}
              placeholder="Optional"
              type="number"
              value={draft.maxUses}
            />
          </label>
          <button className="button" disabled={!canSave || isSaving} type="submit">
            {isSaving ? "Saving programme-backed setup" : "Save campaign setup"}
          </button>
        </form>

        {error ? <ErrorPanel error={error} /> : null}
        {result && savedCampaign ? (
          <>
            <div className="wizard-summary-strip success">
              <div>
                <strong>Campaign setup saved.</strong>{" "}
                {savedCampaign.name} is an inactive draft. No links were generated, no policy was changed, no campaign was activated, and no money moved.
              </div>
              <StatusBadge label={formatDisplay(savedCampaign.setupStatus)} tone="success" />
            </div>
            {binding ? (
              <div className="wizard-summary-strip success">
                <div>
                  <strong>Programme version bound.</strong>{" "}
                  {bindingProgrammeName} v{bindingVersionNumber} now defines this campaign's packaged journey, defaults, incentives, and governance.
                </div>
                <StatusBadge label={bindingStatus} tone="success" />
              </div>
            ) : (
              <div className="wizard-summary-strip warning">
                <div>
                  <strong>Campaign saved, programme binding still pending.</strong>{" "}
                  Keep this campaign inactive until the selected published programme version is bound.
                </div>
                <StatusBadge label="Binding pending" tone="warning" />
              </div>
            )}
            <div className="grid-3">
              <KpiCard
                label="Campaign"
                value={savedCampaign.name}
                footnote={savedCampaign.campaignCode}
                icon={Target}
              />
              <KpiCard
                label="Setup state"
                value={formatDisplay(savedCampaign.setupStatus)}
                footnote={savedCampaign.isActive ? "Active" : "Inactive until a later activation step"}
                icon={ShieldCheck}
              />
              <KpiCard
                label="Next work"
                value={String(result.campaignSetup.nextActions.length)}
                footnote="Policy, readiness, and review remain separate"
                icon={ListChecks}
              />
            </div>
            <div className="route-list">
              {result.campaignSetup.nextActions.map((action) => (
                <div className="route-item" key={action}>
                  <div>
                    <div className="route-name">{action}</div>
                    <div className="route-path">Continue from the customer Campaigns page when you are ready.</div>
                  </div>
                  <StatusBadge label="Next" tone="info" />
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="wizard-status-card">
            <div>
              <strong>What this saves</strong>
              <p>
                A customer-scoped inactive campaign draft plus its published programme version binding. The programme carries the journey, defaults, incentives, and governance this campaign must use before activation.
              </p>
            </div>
            <StatusBadge label="Safe create" tone="info" />
          </div>
        )}

        <div className="customer-header-actions">
          <Link className="button secondary" to={`${selectedCustomerPath}/campaigns`}>
            Back to Campaigns
          </Link>
          {savedCampaign ? (
            <Link
              className="button"
              to={`${selectedCustomerPath}/campaigns/settings?campaign=${encodeURIComponent(
                savedCampaign.campaignCode,
              )}`}
            >
              Complete policy settings
            </Link>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function CustomerCampaignPolicySettingsPage({
  customerName,
  draft,
  error,
  externalTenantRef,
  isSaving,
  onChange,
  onSubmit,
  result,
  selectedAccount,
  selectedCustomerPath,
}: {
  customerName: string;
  draft: CampaignPolicySettingsDraft;
  error: unknown;
  externalTenantRef: string;
  isSaving: boolean;
  onChange: (values: Partial<CampaignPolicySettingsDraft>) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  result: ReferralSaasAccountCampaignPolicySettingsResponse | null;
  selectedAccount?: AccountRegistryItem;
  selectedCustomerPath: string;
}) {
  const { refreshKey } = useRefreshContext();
  const {
    data: campaignListResponse,
    error: campaignListError,
    isLoading: isCampaignListLoading,
  } = useReferralSaasAccountCampaignList(
    selectedAccount?.accountId || "",
    externalTenantRef,
    Boolean(selectedAccount && externalTenantRef),
    refreshKey,
  );
  const campaigns = campaignListResponse?.campaigns || [];
  const canSave = Boolean(selectedAccount && draft.campaignCode.trim() && draft.version.trim());
  const savedSettings = result?.policySettings.policySettings;

  return (
    <section className="panel customer-module-page">
      <div className="panel-header">
        <div>
          <div className="page-kicker">Referral SaaS &gt; {customerName} &gt; Campaigns &gt; Policy settings</div>
          <h2 className="panel-title">Campaign policy settings</h2>
          <div className="panel-subtitle">
            Configure attribution, eligibility, product windows, and reward visibility for one selected campaign.
          </div>
        </div>
        <StatusBadge label="Setup only" tone="warning" />
      </div>
      <div className="panel-body route-list">
        <div className="wizard-status-card">
          <div>
            <strong>Selected customer</strong>
            <p>
              {selectedAccount?.accountCode || "No account code"} - {externalTenantRef || "No customer reference"}
            </p>
          </div>
          <StatusBadge label="No tenant code entry" tone="success" />
        </div>

        {isCampaignListLoading ? <LoadingState label="Loading customer campaigns" /> : null}
        {campaignListError ? <ErrorPanel error={campaignListError} /> : null}
        <form className="form-grid" onSubmit={onSubmit}>
          <label>
            Campaign
            <select
              onChange={(event) => onChange({ campaignCode: event.target.value })}
              value={draft.campaignCode}
            >
              <option value="">Select a campaign</option>
              {campaigns.map((campaign) => (
                <option key={campaign.campaignCode} value={campaign.campaignCode}>
                  {campaign.name || campaign.campaignCode} ({campaign.campaignCode})
                </option>
              ))}
            </select>
          </label>
          <label>
            Policy version
            <input
              min="1"
              onChange={(event) => onChange({ version: event.target.value })}
              type="number"
              value={draft.version}
            />
          </label>
          <label>
            Attribution window
            <input
              min="1"
              onChange={(event) => onChange({ attributionWindowDays: event.target.value })}
              type="number"
              value={draft.attributionWindowDays}
            />
          </label>
          <label>
            Eligibility rule
            <select
              onChange={(event) => onChange({ eligibilityRule: event.target.value })}
              value={draft.eligibilityRule}
            >
              <option value="NEW_CUSTOMER_ONLY">New customer only</option>
              <option value="EXISTING_CUSTOMER_ALLOWED">Existing customer allowed</option>
              <option value="PRODUCT_HOLDING_REQUIRED">Product holding required</option>
            </select>
          </label>
          <label>
            Product window
            <input
              min="1"
              onChange={(event) => onChange({ productWindowDays: event.target.value })}
              type="number"
              value={draft.productWindowDays}
            />
          </label>
          <label>
            Accepted terms required
            <select
              onChange={(event) => onChange({ requiresAcceptedTerms: event.target.value })}
              value={draft.requiresAcceptedTerms}
            >
              <option value="true">Required before reward eligibility</option>
              <option value="false">Not required for this setup policy</option>
            </select>
          </label>
          <label>
            Reward visibility notes
            <input
              onChange={(event) => onChange({ rewardVisibilityNotes: event.target.value })}
              placeholder="Example: Show estimated referral reward after successful attribution"
              value={draft.rewardVisibilityNotes}
            />
          </label>
          <button className="button" disabled={!canSave || isSaving} type="submit">
            {isSaving ? "Saving policy settings" : "Save policy settings"}
          </button>
        </form>

        {error ? <ErrorPanel error={error} /> : null}
        {result && savedSettings ? (
          <>
            <div className="wizard-summary-strip success">
              <div>
                <strong>Policy settings saved.</strong> {result.policySettings.campaignRef} is configured for setup.
                No links were generated, no campaign was activated, no webhook was delivered, and no money moved.
              </div>
              <StatusBadge label={formatDisplay(savedSettings.setupStatus)} tone="success" />
            </div>
            <div className="grid-3">
              <KpiCard
                label="Attribution window"
                value={`${savedSettings.attributionWindowDays ?? "Not set"} days`}
                footnote={`Policy version ${savedSettings.version}`}
                icon={SlidersHorizontal}
              />
              <KpiCard
                label="Eligibility rules"
                value={String(savedSettings.eligibilityRuleCount)}
                footnote="Saved against the selected customer campaign"
                icon={ListChecks}
              />
              <KpiCard
                label="Reward visibility"
                value={formatDisplay(savedSettings.rewardVisibilityStatus)}
                footnote="Display policy only, not a payout"
                icon={ShieldCheck}
              />
            </div>
            <div className="route-list">
              {result.policySettings.nextActions.map((action) => (
                <div className="route-item" key={action}>
                  <div>
                    <div className="route-name">{action}</div>
                    <div className="route-path">Continue from this customer's Campaigns page.</div>
                  </div>
                  <StatusBadge label="Next" tone="info" />
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="wizard-status-card">
            <div>
              <strong>What this saves</strong>
              <p>
                Campaign policy evidence for the selected customer. It does not create a tenant code, activate the campaign,
                generate links, create validation tracks, deliver webhooks, or move money.
              </p>
            </div>
            <StatusBadge label="Guarded settings" tone="info" />
          </div>
        )}

        <div className="customer-header-actions">
          <Link className="button secondary" to={`${selectedCustomerPath}/campaigns`}>
            Back to Campaigns
          </Link>
          {result ? (
            <Link
              className="button"
              to={`${selectedCustomerPath}/campaigns/review?campaign=${encodeURIComponent(
                result.policySettings.campaignRef,
              )}`}
            >
              Submit for review
            </Link>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function CustomerCampaignReviewPage({
  customerName,
  draft,
  error,
  externalTenantRef,
  isDeciding,
  isSubmitting,
  onChange,
  onDecisionSubmit,
  onReviewSubmit,
  result,
  selectedAccount,
  selectedCustomerPath,
}: {
  customerName: string;
  draft: CampaignReviewDraft;
  error: unknown;
  externalTenantRef: string;
  isDeciding: boolean;
  isSubmitting: boolean;
  onChange: (values: Partial<CampaignReviewDraft>) => void;
  onDecisionSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onReviewSubmit: (event: FormEvent<HTMLFormElement>) => void;
  result: ReferralSaasAccountCampaignReviewResponse | null;
  selectedAccount?: AccountRegistryItem;
  selectedCustomerPath: string;
}) {
  const { refreshKey } = useRefreshContext();
  const [activationResult, setActivationResult] =
    useState<ReferralSaasAccountCampaignActivationResponse | null>(null);
  const {
    data: campaignListResponse,
    error: campaignListError,
    isLoading: isCampaignListLoading,
    refetch: refetchCampaignList,
  } = useReferralSaasAccountCampaignList(
    selectedAccount?.accountId || "",
    externalTenantRef,
    Boolean(selectedAccount && externalTenantRef),
    refreshKey,
  );
  const campaigns = campaignListResponse?.campaigns || [];
  const canSubmitReview = Boolean(selectedAccount && draft.campaignCode.trim() && draft.setupSummary.trim());
  const canRecordDecision = Boolean(
    selectedAccount &&
      draft.campaignCode.trim() &&
      draft.decisionReason.trim() &&
      draft.reviewerRef.trim(),
  );
  const review = result?.campaignReview;
  const activation = activationResult?.campaignActivation;
  const canRequestActivation = Boolean(
    selectedAccount &&
      externalTenantRef &&
      draft.campaignCode.trim() &&
      review?.reviewStatus === "REVIEW_APPROVED" &&
      review.activationEligibility === "ELIGIBLE_FOR_FUTURE_ACTIVATION" &&
      review.activationStatus !== "ACTIVE",
  );
  const campaignActivationMutation = useMutation({
    mutationFn: requestReferralSaasAccountCampaignActivation,
    onSuccess: (response) => {
      setActivationResult(response);
      void refetchCampaignList();
    },
  });

  function submitCampaignActivation() {
    const cleanedCampaignCode = draft.campaignCode.trim();
    if (!selectedAccount || !externalTenantRef || !cleanedCampaignCode || !canRequestActivation) {
      return;
    }
    campaignActivationMutation.mutate({
      accountRef: selectedAccount.accountId,
      campaignCode: cleanedCampaignCode,
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: externalTenantRef,
        context: "setup",
      },
      activationRequest: {
        requestedLifecycleStatus: "ACTIVE",
        reviewStatus: "REVIEW_APPROVED",
        goLiveReason: "Campaign review approved inside selected customer campaign module.",
        operatorNotes: "Activation request is customer scoped and leaves adjacent workflows separate.",
      },
      reasonCode: "CUSTOMER_PROFILE_CAMPAIGN_ACTIVATION_REQUEST",
      correlationId: `customer-profile-campaign-activation-${selectedAccount.accountId}`,
      idempotencyKey: `customer-profile-campaign-activation-${selectedAccount.accountId}-${cleanedCampaignCode}`
        .toLowerCase()
        .replace(/[^a-z0-9-]+/g, "-"),
    });
  }

  return (
    <section className="panel customer-module-page">
      <div className="panel-header">
        <div>
          <div className="page-kicker">Referral SaaS &gt; {customerName} &gt; Campaigns &gt; Review</div>
          <h2 className="panel-title">Campaign review</h2>
          <div className="panel-subtitle">
            Submit campaign setup evidence and record the review decision. Approval only makes future activation eligible.
          </div>
        </div>
        <StatusBadge label="No activation" tone="warning" />
      </div>
      <div className="panel-body route-list">
        <div className="wizard-status-card">
          <div>
            <strong>Selected customer</strong>
            <p>
              {selectedAccount?.accountCode || "No account code"} - {externalTenantRef || "No customer reference"}
            </p>
          </div>
          <StatusBadge label="No tenant code entry" tone="success" />
        </div>

        {isCampaignListLoading ? <LoadingState label="Loading customer campaigns" /> : null}
        {campaignListError ? <ErrorPanel error={campaignListError} /> : null}
        {error ? <ErrorPanel error={error} /> : null}
        {campaignActivationMutation.error ? <ErrorPanel error={campaignActivationMutation.error} /> : null}

        <form className="form-grid" onSubmit={onReviewSubmit}>
          <label>
            Campaign
            <select
              onChange={(event) => onChange({ campaignCode: event.target.value })}
              value={draft.campaignCode}
            >
              <option value="">Select a campaign</option>
              {campaigns.map((campaign) => (
                <option key={campaign.campaignCode} value={campaign.campaignCode}>
                  {campaign.name || campaign.campaignCode} ({campaign.campaignCode})
                </option>
              ))}
            </select>
          </label>
          <label>
            Review summary
            <textarea
              onChange={(event) => onChange({ setupSummary: event.target.value })}
              placeholder="Summarise the setup and policy evidence being reviewed"
              rows={3}
              value={draft.setupSummary}
            />
          </label>
          <label>
            Operator notes
            <textarea
              onChange={(event) => onChange({ operatorNotes: event.target.value })}
              placeholder="Optional safe notes for the reviewer"
              rows={3}
              value={draft.operatorNotes}
            />
          </label>
          <button className="button" disabled={!canSubmitReview || isSubmitting} type="submit">
            {isSubmitting ? "Submitting campaign review" : "Submit campaign for review"}
          </button>
        </form>

        <form className="form-grid" onSubmit={onDecisionSubmit}>
          <label>
            Review decision
            <select
              onChange={(event) => onChange({ decision: event.target.value as CampaignReviewDraft["decision"] })}
              value={draft.decision}
            >
              <option value="APPROVED">Approve review</option>
              <option value="BLOCKED">Block and return to setup</option>
            </select>
          </label>
          <label>
            Reviewer reference
            <input
              onChange={(event) => onChange({ reviewerRef: event.target.value })}
              placeholder="Example: amplifi-admin"
              value={draft.reviewerRef}
            />
          </label>
          <label>
            Decision reason
            <textarea
              onChange={(event) => onChange({ decisionReason: event.target.value })}
              placeholder="Reason required for approval or block"
              rows={3}
              value={draft.decisionReason}
            />
          </label>
          <button className="button secondary" disabled={!canRecordDecision || isDeciding} type="submit">
            {isDeciding ? "Recording review decision" : "Record review decision"}
          </button>
        </form>

        {review ? (
          <>
            <div className="wizard-summary-strip success">
              <div>
                <strong>Campaign review recorded.</strong>{" "}
                {review.campaignRef} is now {formatDisplay(review.reviewStatus)}. Approval does not activate the campaign.
              </div>
              <StatusBadge label={formatDisplay(review.commandStatus)} tone="success" />
            </div>
            <div className="grid-3">
              <KpiCard
                label="Review state"
                value={formatDisplay(review.reviewStatus)}
                footnote={`Previous: ${formatDisplay(review.previousReviewStatus)}`}
                icon={ShieldCheck}
              />
              <KpiCard
                label="Activation eligibility"
                value={formatDisplay(review.activationEligibility)}
                footnote={formatDisplay(review.activationStatus)}
                icon={Target}
              />
              <KpiCard
                label="Next actions"
                value={String(review.nextActions.length)}
                footnote={review.reviewerAction}
                icon={ListChecks}
              />
            </div>
            <div className="route-list">
              {review.nextActions.map((action) => (
                <div className="route-item" key={action}>
                  <div>
                    <div className="route-name">{action}</div>
                    <div className="route-path">Continue inside this customer's Campaigns module.</div>
                  </div>
                  <StatusBadge label="Next" tone="info" />
                </div>
              ))}
            </div>
            <div className="wizard-status-card">
              <div>
                <strong>Activate reviewed campaign</strong>
                <p>
                  This switches only the selected customer campaign posture after approval. It does not create links,
                  validation tracks, webhooks, credentials, access, billing, or money movement.
                </p>
              </div>
              <button
                className="button"
                disabled={!canRequestActivation || campaignActivationMutation.isPending}
                onClick={submitCampaignActivation}
                type="button"
              >
                {campaignActivationMutation.isPending ? "Requesting activation" : "Activate campaign"}
              </button>
            </div>
            {!canRequestActivation ? (
              <div className="wizard-summary-strip warning">
                <div>
                  <strong>Activation is locked.</strong> Approve the campaign review before requesting activation for
                  this customer.
                </div>
                <StatusBadge label="Review required" tone="warning" />
              </div>
            ) : null}
            {activation ? (
              <div className="wizard-summary-strip success">
                <div>
                  <strong>Campaign activated.</strong> {activation.campaignRef} is now{" "}
                  {formatDisplay(activation.campaignActivation.lifecycle)}. Next, continue with customer-scoped links,
                  readiness monitoring, attribution, progress, and reports.
                </div>
                <StatusBadge label={formatDisplay(activation.campaignActivation.activationStatus)} tone="success" />
              </div>
            ) : null}
          </>
        ) : (
          <div className="wizard-status-card">
            <div>
              <strong>What this records</strong>
              <p>
                Campaign review evidence for this selected customer only. It does not activate campaigns, generate links, create validation tracks, deliver webhooks, change access, bill, or move money.
              </p>
            </div>
            <StatusBadge label="Review only" tone="info" />
          </div>
        )}

        <div className="customer-header-actions">
          <Link className="button secondary" to={`${selectedCustomerPath}/campaigns`}>
            Back to Campaigns
          </Link>
          <Link className="button secondary" to={`${selectedCustomerPath}/campaigns/settings`}>
            Policy settings
          </Link>
        </div>
      </div>
    </section>
  );
}

function customerLinkResultValue(result: ReferralSaasLinkRecord | undefined, path: string[], fallback = "-") {
  if (!result) {
    return fallback;
  }
  const nested = getNestedValue(result, path, undefined);
  if (nested !== undefined && nested !== null && String(nested).trim() !== "") {
    return String(nested);
  }
  return getValue(result, path, fallback);
}

function CustomerLinksAndCodesPage({
  customerName,
  externalTenantRef,
  selectedAccount,
  selectedCustomerPath,
}: {
  customerName: string;
  externalTenantRef: string;
  selectedAccount?: AccountRegistryItem;
  selectedCustomerPath: string;
}) {
  const { refreshKey } = useRefreshContext();
  const [campaignCode, setCampaignCode] = useState("");
  const [referrerUcn, setReferrerUcn] = useState("");
  const [sticker, setSticker] = useState("");
  const [segment, setSegment] = useState("REFERRAL");
  const [preferredHandle, setPreferredHandle] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(true);
  const [referralCode, setReferralCode] = useState("");
  const [alias, setAlias] = useState("");
  const {
    data: campaignListResponse,
    error: campaignListError,
    isLoading: isCampaignListLoading,
  } = useReferralSaasAccountCampaignList(
    selectedAccount?.accountId || "",
    externalTenantRef,
    Boolean(selectedAccount && externalTenantRef),
    refreshKey,
  );
  const campaigns = campaignListResponse?.campaigns || [];
  const activatedCampaigns = campaigns.filter(
    (campaign) => campaign.status === "ACTIVE" && campaign.lifecycle === "ACTIVE",
  );
  const selectedCampaign =
    campaigns.find((campaign) => campaign.campaignCode === campaignCode) || activatedCampaigns[0] || campaigns[0];
  const selectedCampaignCode = selectedCampaign?.campaignCode || campaignCode;
  const selectedCampaignIsActive =
    selectedCampaign?.status === "ACTIVE" && selectedCampaign?.lifecycle === "ACTIVE";
  const accountScope = {
    refType: "external_tenant_ref" as const,
    externalRef: externalTenantRef,
    context: "setup" as const,
  };

  useEffect(() => {
    if (!campaignCode && activatedCampaigns[0]?.campaignCode) {
      setCampaignCode(activatedCampaigns[0].campaignCode);
    }
  }, [activatedCampaigns, campaignCode]);

  const issueMutation = useMutation({
    mutationFn: () =>
      issueReferralSaasAccountCampaignCode({
        accountRef: selectedAccount?.accountId || "",
        campaignCode: selectedCampaignCode,
        accountScope,
        referrerUcn,
        sticker,
        segment,
        preferredHandle,
        acceptedTerms,
      }),
    onSuccess: (result) => {
      const issuedCode =
        customerLinkResultValue(result, ["linkCode", "referralCode"], "") ||
        customerLinkResultValue(result, ["issue", "referralCode"], "");
      if (issuedCode) {
        setReferralCode(issuedCode);
      }
    },
  });

  const validateMutation = useMutation({
    mutationFn: () =>
      validateReferralSaasAccountCampaignCode({
        accountRef: selectedAccount?.accountId || "",
        campaignCode: selectedCampaignCode,
        accountScope,
        referralCode,
        acceptedTerms,
        alias,
      }),
  });

  const issueResult = issueMutation.data;
  const validationResult = validateMutation.data;
  const linkCode = asRecord(getNestedValue(issueResult, ["linkCode"], {}));
  const validation = asRecord(getNestedValue(validationResult, ["validation"], {}));
  const validationStatus = String(validationResult?.status || "Checked");
  const canIssue = Boolean(
    selectedAccount &&
      externalTenantRef &&
      selectedCampaignCode &&
      selectedCampaignIsActive &&
      referrerUcn.trim() &&
      sticker.trim() &&
      segment.trim() &&
      acceptedTerms,
  );
  const canValidate = Boolean(
    selectedAccount &&
      externalTenantRef &&
      selectedCampaignCode &&
      selectedCampaignIsActive &&
      referralCode.trim() &&
      acceptedTerms,
  );

  return (
    <section className="panel customer-module-page">
      <div className="panel-header">
        <div>
          <div className="page-kicker">Referral SaaS &gt; {customerName} &gt; Links and codes</div>
          <h2 className="panel-title">Links and codes</h2>
          <div className="panel-subtitle">
            Select an activated campaign, issue or reuse a referral code, then validate it without entering tenant code.
          </div>
        </div>
        <StatusBadge label="Customer scoped" tone="success" />
      </div>
      <div className="panel-body route-list">
        <div className="wizard-status-card">
          <div>
            <strong>Selected customer</strong>
            <p>
              {selectedAccount?.accountCode || "No account code"} - {externalTenantRef || "No customer reference"}
            </p>
          </div>
          <StatusBadge label="No tenant code entry" tone="success" />
        </div>

        {isCampaignListLoading ? <LoadingState label="Loading activated campaigns" /> : null}
        {campaignListError ? <ErrorPanel error={campaignListError} /> : null}
        {issueMutation.error ? <ErrorPanel error={issueMutation.error} /> : null}
        {validateMutation.error ? <ErrorPanel error={validateMutation.error} /> : null}

        <div>
          <h3 className="section-heading">1. Choose an activated campaign</h3>
          <p className="muted">Only active campaigns can issue or validate referral entry points from this customer page.</p>
        </div>
        <DataTable
          rows={campaigns}
          emptyText="No campaigns are attached to this customer yet. Create and activate a campaign before issuing links or codes."
          columns={[
            {
              key: "campaign",
              header: "Campaign",
              render: (row) => {
                const campaign = row as (typeof campaigns)[number];
                const selected = campaign.campaignCode === selectedCampaignCode;
                const active = campaign.status === "ACTIVE" && campaign.lifecycle === "ACTIVE";
                return (
                  <button
                    className={`button ${selected ? "button-primary" : "button-secondary"}`}
                    disabled={!active}
                    onClick={() => setCampaignCode(campaign.campaignCode)}
                    type="button"
                  >
                    {campaign.name || campaign.campaignCode}
                  </button>
                );
              },
            },
            {
              key: "campaignCode",
              header: "Code",
              render: (row) => <strong>{formatDisplay(getValue(row, ["campaignCode"], "Unknown"))}</strong>,
            },
            {
              key: "status",
              header: "Status",
              render: (row) => <StatusBadge label={formatDisplay(getValue(row, ["status"], "Unknown"))} tone={statusTone(String(getValue(row, ["status"], "")))} />,
            },
            {
              key: "action",
              header: "Next action",
              render: (row) => {
                const active = getValue(row, ["status"], "") === "ACTIVE" && getValue(row, ["lifecycle"], "") === "ACTIVE";
                return (
                  <span className="table-subtext">
                    {active ? "Can issue and validate codes here" : "Activate this campaign before issuing links"}
                  </span>
                );
              },
            },
          ]}
        />

        {!activatedCampaigns.length && !isCampaignListLoading ? (
          <div className="wizard-summary-strip warning">
            <div>
              <strong>In plain English:</strong> {customerName} needs an activated campaign before links or codes can be created.
            </div>
            <Link className="button secondary" to={`${selectedCustomerPath}/campaigns/review`}>
              Review or activate campaign
            </Link>
          </div>
        ) : null}

        <div className="grid-2">
          <form className="form-grid" onSubmit={(event) => event.preventDefault()}>
            <div>
              <h3 className="section-heading">2. Issue or reuse a referral code</h3>
              <p className="muted">This calls the existing Referral SaaS code primitive through selected customer and campaign scope.</p>
            </div>
            <label>
              Referrer customer reference
              <input
                onChange={(event) => setReferrerUcn(event.target.value)}
                placeholder="Example: customer-referrer-001"
                value={referrerUcn}
              />
            </label>
            <label>
              Channel or placement
              <input
                onChange={(event) => setSticker(event.target.value.toUpperCase())}
                placeholder="Example: QR001"
                value={sticker}
              />
            </label>
            <label>
              Segment
              <input
                onChange={(event) => setSegment(event.target.value.toUpperCase())}
                placeholder="Example: REFERRAL"
                value={segment}
              />
            </label>
            <label>
              Preferred public handle
              <input
                onChange={(event) => setPreferredHandle(event.target.value)}
                placeholder="Optional"
                value={preferredHandle}
              />
            </label>
            <label className="checkbox-row">
              <input
                checked={acceptedTerms}
                onChange={(event) => setAcceptedTerms(event.target.checked)}
                type="checkbox"
              />
              <span>Terms accepted for issue and validation tests</span>
            </label>
            <button className="button" disabled={!canIssue || issueMutation.isPending} onClick={() => issueMutation.mutate()} type="button">
              {issueMutation.isPending ? "Issuing code" : "Issue or reuse code"}
            </button>
          </form>

          <form className="form-grid" onSubmit={(event) => event.preventDefault()}>
            <div>
              <h3 className="section-heading">3. Validate the referral code</h3>
              <p className="muted">Validation uses the selected customer account scope internally; no tenant code is entered here.</p>
            </div>
            <label>
              Referral code
              <input
                onChange={(event) => setReferralCode(event.target.value.toUpperCase())}
                placeholder="Filled after issue or paste a known code"
                value={referralCode}
              />
            </label>
            <label>
              Customer alias
              <input
                onChange={(event) => setAlias(event.target.value)}
                placeholder="Optional safe customer alias"
                value={alias}
              />
            </label>
            <button className="button" disabled={!canValidate || validateMutation.isPending} onClick={() => validateMutation.mutate()} type="button">
              {validateMutation.isPending ? "Validating code" : "Validate code"}
            </button>
          </form>
        </div>

        <div className="grid-3">
          <KpiCard
            label="Campaign"
            value={selectedCampaignCode || "None"}
            footnote={selectedCampaignIsActive ? "Activated campaign selected" : "Activation required first"}
            icon={Target}
          />
          <KpiCard
            label="Issued code"
            value={customerLinkResultValue(issueResult, ["linkCode", "referralCode"])}
            footnote={formatDisplay(customerLinkResultValue(issueResult, ["linkCode", "issueStatus"], "Waiting"))}
            icon={LinkIcon}
          />
          <KpiCard
            label="Validation"
            value={formatDisplay(customerLinkResultValue(validationResult, ["validation", "validationStatus"], "Waiting"))}
            footnote={customerLinkResultValue(validationResult, ["validation", "message"], "No validation run yet")}
            icon={ShieldCheck}
          />
        </div>

        {issueResult ? (
          <div className="wizard-summary-strip success">
            <div>
              <strong>Code ready.</strong>{" "}
              {formatDisplay(customerLinkResultValue(linkCode, ["issueStatus"], "Issued"))} for {selectedCampaignCode}.
              This did not activate campaigns, send webhooks, bill, fund, settle, or move money.
            </div>
            <StatusBadge label={formatDisplay(customerLinkResultValue(linkCode, ["sourceType"], "Referral code"))} tone="success" />
          </div>
        ) : null}

        {validationResult ? (
          <div className={`wizard-summary-strip ${validationStatus === "ok" ? "success" : "warning"}`}>
            <div>
              <strong>Validation checked.</strong>{" "}
              {formatDisplay(customerLinkResultValue(validation, ["message"], customerLinkResultValue(validation, ["validationStatus"], "Checked")))}
            </div>
            <StatusBadge
              label={formatDisplay(customerLinkResultValue(validation, ["validationStatus"], validationStatus))}
              tone={statusTone(customerLinkResultValue(validation, ["validationStatus"], validationStatus))}
            />
          </div>
        ) : null}

        <div className="wizard-status-card">
          <div>
            <strong>What this page will not do</strong>
            <p>
              No tenant code is shown or entered, no campaign is activated, no webhook or invite is sent, no credentials are created, and no billing, rewards, funding, fulfilment, settlement, wallet, invoice, payout, or treasury action happens here.
            </p>
          </div>
          <StatusBadge label="Bounded link/code workflow" tone="success" />
        </div>

        <div className="customer-header-actions">
          <Link className="button secondary" to={`${selectedCustomerPath}/campaigns`}>
            Back to Campaigns
          </Link>
          <Link className="button secondary" to={`${selectedCustomerPath}`}>
            Customer home
          </Link>
        </div>
      </div>
    </section>
  );
}

function CustomerCommercialEntitlementPage({
  entitlement,
  error,
  isLoading,
  productionActivation,
  productionActivationError,
  isProductionActivationLoading,
  selectedCustomerPath,
}: {
  entitlement?: ReferralSaasCommercialEntitlementResponse;
  error: unknown;
  isLoading: boolean;
  productionActivation?: ReferralSaasProductionActivationResponse;
  productionActivationError: unknown;
  isProductionActivationLoading: boolean;
  selectedCustomerPath: string;
}) {
  const commercial = entitlement?.commercialEntitlement;
  const activation = productionActivation?.productionActivation;
  const featureRows = commercial?.features || [];
  const nextActionRows = commercial?.nextActions || [];
  const activationGateRows = activation?.gates || [];
  const limitRows = Object.entries(commercial?.limits || {}).map(([key, value]) => ({
    key,
    value: String(value),
  }));

  return (
    <section className="panel customer-module-page" id="commercial-entitlement">
      <div className="panel-header">
        <div>
          <div className="page-kicker">Referral SaaS &gt; Plan and entitlement</div>
          <h2 className="panel-title">Plan and entitlement</h2>
          <div className="panel-subtitle">
            Check whether this customer can move from safe setup into production Referral SaaS use.
          </div>
        </div>
        <StatusBadge
          label={commercial?.productionActivationBlocked ? "Launch blocked" : "Launch allowed"}
          tone={commercial?.productionActivationBlocked ? "warning" : "success"}
        />
      </div>
      <div className="panel-body route-list">
        {isLoading ? <LoadingState label="Checking plan and entitlement posture" /> : null}
        {error ? <ErrorPanel error={error} /> : null}
        {commercial ? (
          <>
            <div className="wizard-status-card">
              <div>
                <strong>In plain English</strong>
                <p>{commercial.plainLanguageSummary}</p>
              </div>
              <StatusBadge label={formatDisplay(commercial.overallStatus)} tone="warning" />
            </div>
            <div className="grid-3">
              <KpiCard
                label="Plan posture"
                value={commercial.plan.planName}
                footnote={formatDisplay(commercial.plan.planCode)}
                icon={SlidersHorizontal}
              />
              <KpiCard
                label="Launch allowed"
                value={commercial.launchAllowed ? "Yes" : "No"}
                footnote={
                  commercial.productionActivationBlocked
                    ? "Commercial entitlement source is still required"
                    : "Commercial launch gate is clear"
                }
                icon={ShieldCheck}
              />
              <KpiCard
                label="Contract source"
                value={formatDisplay(commercial.plan.contractSource)}
                footnote="Reference only, not billing"
                icon={FileJson}
              />
            </div>
            <div className="route-card">
              <div>
                <strong>What this page will not do</strong>
                <p>
                  It does not create subscriptions, billing records, invoices, payments, seats, credentials, campaigns,
                  go-live actions, DLaaS finance scope, or money movement.
                </p>
              </div>
              <StatusBadge label="No billing or money" tone="success" />
            </div>
            <div className="route-card">
              <div>
                <strong>Commercial finance boundary</strong>
                <p>{commercial.commercialFinanceBoundary.nextAction}</p>
                <p className="table-subtext">
                  H1 only reads plan posture and launch entitlement fields. Deferred finance capability:{" "}
                  {commercial.commercialFinanceBoundary.h1DeferredCapabilities.map(formatDisplay).join(", ")}.
                </p>
              </div>
              <StatusBadge label={formatDisplay(commercial.commercialFinanceBoundary.scope)} tone="warning" />
            </div>
            <section className="route-card">
              <div>
                <strong>Production activation decision</strong>
                <p>
                  This is the backend launch decision. The UI cannot override it; campaign activation stays blocked
                  until every required gate passes with current evidence.
                </p>
              </div>
              {isProductionActivationLoading ? (
                <LoadingState label="Checking production activation gates" />
              ) : null}
              {productionActivationError ? <ErrorPanel error={productionActivationError} /> : null}
              {activation ? (
                <>
                  <div className="wizard-status-card">
                    <div>
                      <strong>{activation.launchAllowed ? "Ready for production launch" : "Production launch is blocked"}</strong>
                      <p>{activation.plainLanguageSummary}</p>
                    </div>
                    <StatusBadge
                      label={formatDisplay(activation.decisionStatus)}
                      tone={activation.launchAllowed ? "success" : "warning"}
                    />
                  </div>
                  <DataTable
                    rows={activationGateRows}
                    emptyText="No production activation gates returned."
                    columns={[
                      {
                        key: "gate",
                        header: "Gate",
                        render: (row) => <strong>{formatDisplay(getValue(row, ["label"], "Gate"))}</strong>,
                      },
                      {
                        key: "status",
                        header: "Status",
                        render: (row) => (
                          <StatusBadge
                            label={formatDisplay(getValue(row, ["status"], ""))}
                            tone={statusTone(getValue(row, ["status"], ""))}
                          />
                        ),
                      },
                      {
                        key: "reason",
                        header: "What it means",
                        render: (row) => getValue(row, ["reason"], ""),
                      },
                      {
                        key: "next",
                        header: "Next action",
                        render: (row) => {
                          const routeHint = getValue(row, ["routeHint"], "");
                          const nextAction = getValue(row, ["nextAction"], "Open page");
                          if (!routeHint || routeHint === "commercial") {
                            return <span className="table-subtext">{nextAction}</span>;
                          }
                          return (
                            <Link
                              className="button secondary compact"
                              to={buildCustomerModuleRoute(selectedCustomerPath, routeHint, "")}
                            >
                              {nextAction}
                            </Link>
                          );
                        },
                      },
                    ]}
                  />
                </>
              ) : null}
            </section>
            <DataTable
              rows={featureRows}
              emptyText="No entitlement features returned."
              columns={[
                {
                  key: "feature",
                  header: "Feature",
                  render: (row) => <strong>{formatDisplay(getValue(row, ["label"], "Feature"))}</strong>,
                },
                {
                  key: "status",
                  header: "Status",
                  render: (row) => (
                    <StatusBadge
                      label={formatDisplay(getValue(row, ["status"], ""))}
                      tone={statusTone(getValue(row, ["status"], ""))}
                    />
                  ),
                },
                {
                  key: "reason",
                  header: "What it means",
                  render: (row) => getValue(row, ["reason"], ""),
                },
                {
                  key: "route",
                  header: "Next page",
                  render: (row) => {
                    const routeHint = getValue(row, ["routeHint"], "");
                    if (!routeHint || routeHint === "commercial") {
                      return <span className="table-subtext">Stay here</span>;
                    }
                    return (
                      <Link className="button secondary compact" to={buildCustomerModuleRoute(selectedCustomerPath, routeHint, "")}>
                        Open {formatDisplay(routeHint)}
                      </Link>
                    );
                  },
                },
              ]}
            />
            <div className="grid-2">
              <section className="route-card">
                <div>
                  <strong>Next actions</strong>
                  <p>These actions show what an operator should resolve before production activation.</p>
                </div>
                <div className="route-list compact">
                  {nextActionRows.map((action) => (
                    <div className="route-card" key={action.actionRef}>
                      <div>
                        <strong>{action.label}</strong>
                        <p>{action.reason}</p>
                      </div>
                      <StatusBadge label={formatDisplay(action.status)} tone={statusTone(action.status)} />
                    </div>
                  ))}
                </div>
              </section>
              <section className="route-card">
                <div>
                  <strong>Plan limits</strong>
                  <p>These are reference limits for H1 setup posture. They are not invoice terms.</p>
                </div>
                <DataTable
                  rows={limitRows}
                  emptyText="No plan limits returned."
                  columns={[
                    {
                      key: "limit",
                      header: "Limit",
                      render: (row) => <strong>{formatDisplay(row.key)}</strong>,
                    },
                    {
                      key: "value",
                      header: "Current value",
                      render: (row) => row.value,
                    },
                  ]}
                />
              </section>
            </div>
          </>
        ) : null}
      </div>
    </section>
  );
}

function CustomerTechnicalSetupPage({
  account,
  customerName,
  error,
  externalTenantRef,
  isLoading,
  readiness,
  selectedCustomerPath,
}: {
  account?: AccountRegistryItem;
  customerName: string;
  error: unknown;
  externalTenantRef: string;
  isLoading: boolean;
  readiness?: ReferralSaasTechnicalSetupReadinessResponse;
  selectedCustomerPath: string;
}) {
  const accountScope = {
    refType: "external_tenant_ref" as const,
    externalRef: externalTenantRef,
    context: "setup" as const,
  };
  const [draft, setDraft] = useState<IntegrationConfigurationDraft>({
    environment: "LOCAL_DEVELOPMENT",
    intendedAuthMethod: "API_KEY",
    allowedUse: ["CAMPAIGN_READ", "REFERRAL_CODE_VALIDATE", "REPORT_READ"],
    callbackUrl: "http://localhost:8000/webhooks/referral-saas",
    eventCategories: ["CAMPAIGN", "REFERRAL", "PROGRESS"],
    inviteDeliveryChannel: "EMAIL",
    inviteProviderApprovalRef: "",
    referralMessageChannels: ["EMAIL"],
  });
  const configurationQuery = useQuery({
    queryKey: [
      "referral-saas",
      "integration-configuration",
      account?.accountId || "",
      externalTenantRef,
    ],
    queryFn: () =>
      getReferralSaasIntegrationConfiguration({
        accountRef: account?.accountId || "",
        refType: "external_tenant_ref",
        externalRef: externalTenantRef,
        context: "setup",
      }),
    enabled: Boolean(account?.accountId && externalTenantRef),
    retry: false,
  });
  const executionReadinessQuery = useQuery({
    queryKey: [
      "referral-saas",
      "integration-execution-readiness",
      account?.accountId || "",
      externalTenantRef,
    ],
    queryFn: () =>
      getReferralSaasIntegrationExecutionReadiness({
        accountRef: account?.accountId || "",
        refType: "external_tenant_ref",
        externalRef: externalTenantRef,
        context: "setup",
      }),
    enabled: Boolean(account?.accountId && externalTenantRef),
    retry: false,
  });
  const credentialRequestsQuery = useQuery({
    queryKey: [
      "referral-saas",
      "integration-credential-requests",
      account?.accountId || "",
      externalTenantRef,
    ],
    queryFn: () =>
      listReferralSaasIntegrationCredentialRequests({
        accountRef: account?.accountId || "",
        refType: "external_tenant_ref",
        externalRef: externalTenantRef,
        context: "setup",
        limit: 20,
      }),
    enabled: Boolean(account?.accountId && externalTenantRef),
    retry: false,
  });
  const providerVaultReadinessQuery = useQuery({
    queryKey: [
      "referral-saas",
      "provider-vault-readiness",
      account?.accountId || "",
      externalTenantRef,
    ],
    queryFn: () =>
      getReferralSaasProviderVaultReadiness({
        accountRef: account?.accountId || "",
        refType: "external_tenant_ref",
        externalRef: externalTenantRef,
        context: "setup",
      }),
    enabled: Boolean(account?.accountId && externalTenantRef),
    retry: false,
  });
  const [configurationMessage, setConfigurationMessage] = useState<string | null>(null);
  const [activeIntegrationTab, setActiveIntegrationTab] = useState<"plan" | "verify">("plan");
  const validationMutation = useMutation({
    mutationFn: () =>
      validateReferralSaasIntegrationConfiguration({
        accountRef: account?.accountId || "",
        ...buildIntegrationConfigurationPayload(draft, accountScope, account?.accountId || ""),
      }),
    onSuccess: (response) => {
      setConfigurationMessage(
        `${formatDisplay(response.validation.commandStatus)}. The connection plan is valid and was not saved yet.`,
      );
    },
  });
  const saveMutation = useMutation({
    mutationFn: () =>
      saveReferralSaasIntegrationConfiguration({
        accountRef: account?.accountId || "",
        ...buildIntegrationConfigurationPayload(draft, accountScope, account?.accountId || ""),
      }),
    onSuccess: async (response) => {
      await configurationQuery.refetch();
      await executionReadinessQuery.refetch();
      await providerVaultReadinessQuery.refetch();
      setActiveIntegrationTab("verify");
      setConfigurationMessage(
        `${formatDisplay(response.integrationConfigurationResult.commandStatus)}. Connection plan saved. Run verification checks next. No credentials, webhook dispatch, invite delivery, campaign activation, billing, or money movement occurred.`,
      );
    },
  });
  const apiAccessVerificationMutation = useMutation({
    mutationFn: () =>
      recordReferralSaasApiAccessVerification({
        accountRef: account?.accountId || "",
        ...buildIntegrationApiAccessVerificationPayload(
          draft,
          accountScope,
          account?.accountId || "",
          savedConfiguration?.configurationRef || executionReadiness?.configurationRef || "no-configuration",
        ),
    }),
    onSuccess: async (response) => {
      const verification = response.integrationApiAccessVerification;
      setConfigurationMessage(
        `${formatDisplay(verification.verificationStatus)}. ${verification.plainLanguageSummary}`,
      );
      await executionReadinessQuery.refetch();
      await providerVaultReadinessQuery.refetch();
    },
  });
  const webhookTestDispatchMutation = useMutation({
    mutationFn: () =>
      recordReferralSaasWebhookTestDispatch({
        accountRef: account?.accountId || "",
        ...buildIntegrationWebhookTestDispatchPayload(
          draft,
          accountScope,
          account?.accountId || "",
          savedConfiguration?.configurationRef || executionReadiness?.configurationRef || "no-configuration",
        ),
      }),
    onSuccess: async (response) => {
      const webhookTest = response.integrationWebhookTestDispatch;
      setConfigurationMessage(
        `${formatDisplay(webhookTest.dispatchStatus)}. ${webhookTest.plainLanguageSummary}`,
      );
      await executionReadinessQuery.refetch();
      await providerVaultReadinessQuery.refetch();
    },
  });
  const messageProviderTestMutation = useMutation({
    mutationFn: () =>
      recordReferralSaasMessageProviderTest({
        accountRef: account?.accountId || "",
        ...buildIntegrationMessageProviderTestPayload(
          draft,
          accountScope,
          account?.accountId || "",
          savedConfiguration?.configurationRef || executionReadiness?.configurationRef || "no-configuration",
        ),
      }),
    onSuccess: async (response) => {
      const providerTest = response.integrationMessageProviderTest;
      setConfigurationMessage(
        `${formatDisplay(providerTest.testStatus)}. ${providerTest.plainLanguageSummary}`,
      );
      await executionReadinessQuery.refetch();
      await providerVaultReadinessQuery.refetch();
    },
  });
  const credentialRequestMutation = useMutation({
    mutationFn: () =>
      recordReferralSaasIntegrationCredentialRequest({
        accountRef: account?.accountId || "",
        ...buildIntegrationCredentialRequestPayload(
          draft,
          accountScope,
          account?.accountId || "",
          savedConfiguration?.configurationRef || executionReadiness?.configurationRef || "no-configuration",
          customerName,
        ),
      }),
    onSuccess: async (response) => {
      const requestResult = response.integrationCredentialRequestResult;
      setConfigurationMessage(
        `${formatDisplay(requestResult.commandStatus)}. ${requestResult.plainLanguageSummary}`,
      );
      await credentialRequestsQuery.refetch();
      await executionReadinessQuery.refetch();
      await providerVaultReadinessQuery.refetch();
    },
  });
  const credentialReviewMutation = useMutation({
    mutationFn: ({
      credentialRequestRef,
      decision,
    }: {
      credentialRequestRef: string;
      decision: "APPROVED" | "BLOCKED";
    }) =>
      recordReferralSaasIntegrationCredentialReviewDecision(
        buildIntegrationCredentialReviewDecisionPayload(
          accountScope,
          account?.accountId || "",
          credentialRequestRef,
          decision,
        ),
      ),
    onSuccess: async (response) => {
      const reviewResult = response.integrationCredentialReviewDecisionResult;
      setConfigurationMessage(
        `${formatDisplay(reviewResult.commandStatus)}. ${reviewResult.plainLanguageSummary}`,
      );
      await credentialRequestsQuery.refetch();
      await executionReadinessQuery.refetch();
      await providerVaultReadinessQuery.refetch();
    },
  });
  const credentialExecutionCheckMutation = useMutation({
    mutationFn: (credentialRequestRef: string) =>
      recordReferralSaasIntegrationCredentialExecutionCheck(
        buildIntegrationCredentialExecutionCheckPayload(
          accountScope,
          account?.accountId || "",
          credentialRequestRef,
        ),
      ),
    onSuccess: async (response) => {
      const executionResult = response.integrationCredentialExecutionCheckResult;
      setConfigurationMessage(
        `${formatDisplay(executionResult.commandStatus)}. ${executionResult.plainLanguageSummary}`,
      );
      await credentialRequestsQuery.refetch();
      await executionReadinessQuery.refetch();
      await providerVaultReadinessQuery.refetch();
    },
  });
  const technicalReadiness = readiness?.technicalSetupReadiness;
  const savedConfiguration = configurationQuery.data?.integrationConfiguration || null;
  const executionReadiness = executionReadinessQuery.data?.integrationExecutionReadiness || null;
  const providerVaultReadiness = providerVaultReadinessQuery.data?.providerVaultReadiness || null;
  const credentialRequests = credentialRequestsQuery.data?.credentialRequests || [];
  const capabilities = technicalReadiness?.capabilities || [];
  const missingCapabilities = capabilities.filter((capability) => capability.status !== "READY");
  const executionActions = executionReadiness?.executionActions || [];
  const readyExecutionActions = executionReadiness?.readyActions || [];
  const executionBlockers = executionReadiness?.blockers || [];
  const apiAccessAction = executionActions.find((action) => action.actionRef === "API_ACCESS_VERIFICATION");
  const webhookTestAction = executionActions.find((action) => action.actionRef === "WEBHOOK_TEST_DISPATCH");
  const messageProviderTestAction = executionActions.find((action) => action.actionRef === "MESSAGE_PROVIDER_TEST");
  const credentialRequestAction = executionActions.find((action) => action.actionRef === "CREDENTIAL_REQUEST");
  const canRecordApiAccessVerification = Boolean(
    account?.accountId &&
      externalTenantRef &&
      apiAccessAction?.status === "READY" &&
      !apiAccessVerificationMutation.isPending,
  );
  const canRecordWebhookTestDispatch = Boolean(
    account?.accountId &&
      externalTenantRef &&
      webhookTestAction?.status === "READY" &&
      !webhookTestDispatchMutation.isPending,
  );
  const canRecordMessageProviderTest = Boolean(
    account?.accountId &&
      externalTenantRef &&
      messageProviderTestAction?.status === "READY" &&
      !messageProviderTestMutation.isPending,
  );
  const canRecordCredentialRequest = Boolean(
    account?.accountId &&
      externalTenantRef &&
      credentialRequestAction?.status === "READY" &&
      !credentialRequestMutation.isPending,
  );
  const canSubmitConfiguration = Boolean(account?.accountId && externalTenantRef);
  const hasSavedConnectionPlan = Boolean(savedConfiguration?.configurationRef || executionReadiness?.configurationRef);
  const stageLabel = hasSavedConnectionPlan
    ? readyExecutionActions.length
      ? "Ready to verify"
      : "Saved plan"
    : "Draft plan";
  const stageTone = hasSavedConnectionPlan ? "success" : "warning";
  const stageSentence = hasSavedConnectionPlan
    ? readyExecutionActions.length
      ? "Connection plan saved. Run the available verification checks next."
      : "Connection plan saved. Resolve the listed setup gaps before live verification."
    : "Save the connection plan before verification can start.";

  return (
    <section className="panel customer-module-page" id="integrations">
      <div className="panel-header">
        <div>
          <div className="page-kicker">Referral SaaS &gt; {customerName} &gt; Integrations</div>
          <h2 className="panel-title">Integrations</h2>
          <div className="panel-subtitle">
            Plan the customer's API, webhook, and message connection. Save the plan, then record safe verification evidence.
          </div>
        </div>
        <StatusBadge label={stageLabel} tone={stageTone} />
      </div>
      <div className="panel-body route-list">
        {isLoading ||
        configurationQuery.isLoading ||
        executionReadinessQuery.isLoading ||
        providerVaultReadinessQuery.isLoading ? (
          <LoadingState label="Checking integration readiness" />
        ) : null}
        {error ? <ErrorPanel error={error} /> : null}
        {configurationQuery.error ? <ErrorPanel error={configurationQuery.error} /> : null}
        {executionReadinessQuery.error ? <ErrorPanel error={executionReadinessQuery.error} /> : null}
        {providerVaultReadinessQuery.error ? <ErrorPanel error={providerVaultReadinessQuery.error} /> : null}
        {credentialRequestsQuery.error ? <ErrorPanel error={credentialRequestsQuery.error} /> : null}
        {validationMutation.error ? <ErrorPanel error={validationMutation.error} /> : null}
        {saveMutation.error ? <ErrorPanel error={saveMutation.error} /> : null}
        {apiAccessVerificationMutation.error ? <ErrorPanel error={apiAccessVerificationMutation.error} /> : null}
        {webhookTestDispatchMutation.error ? <ErrorPanel error={webhookTestDispatchMutation.error} /> : null}
        {messageProviderTestMutation.error ? <ErrorPanel error={messageProviderTestMutation.error} /> : null}
        {credentialRequestMutation.error ? <ErrorPanel error={credentialRequestMutation.error} /> : null}
        {credentialReviewMutation.error ? <ErrorPanel error={credentialReviewMutation.error} /> : null}
        {credentialExecutionCheckMutation.error ? <ErrorPanel error={credentialExecutionCheckMutation.error} /> : null}
        {technicalReadiness ? (
          <>
            <div className={`integrations-stage-card ${hasSavedConnectionPlan ? "success" : "warning"}`}>
              <div>
                <strong>{stageLabel}</strong>
                <p>{stageSentence}</p>
                {savedConfiguration ? (
                  <span className="table-subtext">
                    Saved by {savedConfiguration.createdByRef || "an operator"} as{" "}
                    {formatDisplay(savedConfiguration.configurationStatus)}.
                  </span>
                ) : null}
              </div>
              <div className="action-row">
                <button
                  className="button secondary"
                  disabled={!canSubmitConfiguration || validationMutation.isPending}
                  onClick={() => validationMutation.mutate()}
                  type="button"
                >
                  {validationMutation.isPending ? "Validating" : "Validate plan"}
                </button>
                <button
                  className="button primary"
                  disabled={!canSubmitConfiguration || saveMutation.isPending}
                  onClick={() => saveMutation.mutate()}
                  type="button"
                >
                  {saveMutation.isPending ? "Saving" : "Save connection plan"}
                </button>
              </div>
            </div>

            <div className="customer-tabs integrations-tabs" role="tablist" aria-label="Integrations setup stages">
              <button
                aria-selected={activeIntegrationTab === "plan"}
                className={activeIntegrationTab === "plan" ? "active" : ""}
                onClick={() => setActiveIntegrationTab("plan")}
                role="tab"
                type="button"
              >
                Plan
              </button>
              <button
                aria-selected={activeIntegrationTab === "verify"}
                className={activeIntegrationTab === "verify" ? "active" : ""}
                onClick={() => {
                  if (!hasSavedConnectionPlan) {
                    setConfigurationMessage("Save the connection plan first, then verification checks unlock.");
                    return;
                  }
                  setActiveIntegrationTab("verify");
                }}
                role="tab"
                type="button"
              >
                Verify
              </button>
            </div>

            {configurationMessage ? (
              <div className="success-banner">
                <strong>Integrations setup updated.</strong> {configurationMessage}
              </div>
            ) : null}

            {activeIntegrationTab === "plan" ? (
              <div className="integrations-plan-grid">
                <div className="panel-lite integrations-step-card">
                  <h3 className="section-heading">1. API connection</h3>
                  <p>Where this customer's systems will call Amplifi, and what they may use.</p>
                  <div className="grid-2">
                    <label>
                      Environment
                      <select
                        onChange={(event) => setDraft({ ...draft, environment: event.target.value })}
                        value={draft.environment}
                      >
                        <option value="LOCAL_DEVELOPMENT">Local development</option>
                        <option value="SANDBOX">Sandbox</option>
                        <option value="PRODUCTION_INTENT">Production intent</option>
                      </select>
                    </label>
                    <label>
                      Planned auth method
                      <select
                        onChange={(event) => setDraft({ ...draft, intendedAuthMethod: event.target.value })}
                        value={draft.intendedAuthMethod}
                      >
                        <option value="API_KEY">API key</option>
                        <option value="OAUTH_CLIENT_CREDENTIALS">OAuth client credentials</option>
                        <option value="SIGNED_WEBHOOK">Signed webhook</option>
                      </select>
                    </label>
                  </div>
                  <fieldset className="option-grid">
                    <legend>Allowed use</legend>
                    {integrationUseCaseOptions.map((option) => (
                      <label className="checkbox-row" key={option.value}>
                        <input
                          checked={draft.allowedUse.includes(option.value)}
                          onChange={() =>
                            setDraft({
                              ...draft,
                              allowedUse: toggleListValue(draft.allowedUse, option.value),
                            })
                          }
                          type="checkbox"
                        />
                        <span>{option.label}</span>
                      </label>
                    ))}
                  </fieldset>
                </div>

                <div className="panel-lite integrations-step-card">
                  <h3 className="section-heading">2. Webhook</h3>
                  <p>Where Amplifi should notify their systems. This is setup intent until verification is recorded.</p>
                  <label>
                    Callback URL
                    <input
                      onChange={(event) => setDraft({ ...draft, callbackUrl: event.target.value })}
                      placeholder="https://customer.example/webhooks/referral-saas"
                      value={draft.callbackUrl}
                    />
                  </label>
                  <fieldset className="option-grid">
                    <legend>Events to prepare</legend>
                    {integrationEventOptions.map((option) => (
                      <label className="checkbox-row" key={option.value}>
                        <input
                          checked={draft.eventCategories.includes(option.value)}
                          onChange={() =>
                            setDraft({
                              ...draft,
                              eventCategories: toggleListValue(draft.eventCategories, option.value),
                            })
                          }
                          type="checkbox"
                        />
                        <span>{option.label}</span>
                      </label>
                    ))}
                  </fieldset>
                </div>

                <div className="panel-lite integrations-step-card">
                  <h3 className="section-heading">3. Messages</h3>
                  <p>Invite and referral journey channels this customer intends to use.</p>
                  <div className="grid-2">
                    <label>
                      Invite delivery channel
                      <select
                        onChange={(event) => setDraft({ ...draft, inviteDeliveryChannel: event.target.value })}
                        value={draft.inviteDeliveryChannel}
                      >
                        {integrationChannelOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Provider reference
                      <input
                        onChange={(event) => setDraft({ ...draft, inviteProviderApprovalRef: event.target.value })}
                        placeholder="Optional approved provider reference"
                        value={draft.inviteProviderApprovalRef}
                      />
                    </label>
                  </div>
                  <fieldset className="option-grid">
                    <legend>Referral message channels</legend>
                    {integrationChannelOptions.map((option) => (
                      <label className="checkbox-row" key={option.value}>
                        <input
                          checked={draft.referralMessageChannels.includes(option.value)}
                          onChange={() =>
                            setDraft({
                              ...draft,
                              referralMessageChannels: toggleListValue(
                                draft.referralMessageChannels,
                                option.value,
                              ),
                            })
                          }
                          type="checkbox"
                        />
                        <span>{option.label}</span>
                      </label>
                    ))}
                  </fieldset>
                  <details className="wizard-details integrations-details">
                    <summary>Platform channel readiness ({missingCapabilities.length} gaps)</summary>
                    <div className="route-list">
                      {capabilities.map((capability) => (
                        <div className="wizard-status-card" key={capability.code}>
                          <div>
                            <strong>{capability.label}</strong>
                            <p>{capability.nextAction}</p>
                            <span className="table-subtext">
                              Needs {formatList(capability.requiredChannels)}. Ready:{" "}
                              {formatList(capability.readyChannels)}. Missing:{" "}
                              {formatList(capability.missingChannels)}.
                            </span>
                          </div>
                          <StatusBadge label={formatDisplay(capability.status)} tone={statusTone(capability.status)} />
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              </div>
            ) : null}

            {activeIntegrationTab === "verify" && executionReadiness ? (
              <div className="panel-lite integrations-verify-panel">
                <div className="settings-summary-header">
                  <div>
                    <h3 className="section-heading">Verification checks</h3>
                    <p>
                      Available after the connection plan is saved. These checks record evidence; they do not create
                      secrets, dispatch webhooks, send invites, or activate campaigns.
                    </p>
                  </div>
                  <StatusBadge
                    label={formatDisplay(executionReadiness.executionStatus)}
                    tone={statusTone(executionReadiness.executionStatus)}
                  />
                </div>
                <div className={`wizard-summary-strip ${executionBlockers.length ? "warning" : "success"}`}>
                  <div>
                    <strong>In plain English:</strong> {executionReadiness.plainLanguageSummary}
                  </div>
                  <StatusBadge
                    label={`${readyExecutionActions.length} ready`}
                    tone={readyExecutionActions.length ? "success" : "warning"}
                  />
                </div>
                {executionBlockers.length ? (
                  <div className="route-list">
                    {executionBlockers.map((blocker) => (
                      <div className="wizard-status-card" key={blocker.code}>
                        <div>
                          <strong>{formatDisplay(blocker.code)}</strong>
                          <p>{blocker.message}</p>
                        </div>
                        <StatusBadge label="Fix first" tone="warning" />
                      </div>
                    ))}
                  </div>
                ) : null}
                <div className="route-list">
                  {executionActions.map((action) => (
                    <div className="integrations-check-row" key={action.actionRef}>
                      <div>
                        <strong>{integrationExecutionActionLabel(action.actionRef, action.label)}</strong>
                        <p>{integrationExecutionActionNextStep(action.actionRef, action.nextStep)}</p>
                        <span className="table-subtext">{action.reason}</span>
                      </div>
                      <StatusBadge label={formatDisplay(action.status)} tone={statusTone(action.status)} />
                      {action.actionRef === "API_ACCESS_VERIFICATION" ? (
                        <button
                          className="button secondary"
                          disabled={!canRecordApiAccessVerification}
                          onClick={() => apiAccessVerificationMutation.mutate()}
                          type="button"
                        >
                          {apiAccessVerificationMutation.isPending
                            ? "Recording API check"
                            : "Record API check"}
                        </button>
                      ) : null}
                      {action.actionRef === "WEBHOOK_TEST_DISPATCH" ? (
                        <button
                          className="button secondary"
                          disabled={!canRecordWebhookTestDispatch}
                          onClick={() => webhookTestDispatchMutation.mutate()}
                          type="button"
                        >
                          {webhookTestDispatchMutation.isPending
                            ? "Recording webhook evidence"
                            : "Record webhook test"}
                        </button>
                      ) : null}
                      {action.actionRef === "MESSAGE_PROVIDER_TEST" ? (
                        <button
                          className="button secondary"
                          disabled={!canRecordMessageProviderTest}
                          onClick={() => messageProviderTestMutation.mutate()}
                          type="button"
                        >
                          {messageProviderTestMutation.isPending
                            ? "Recording provider check"
                            : "Record provider check"}
                        </button>
                      ) : null}
                      {action.actionRef === "CREDENTIAL_REQUEST" ? (
                        <button
                          className="button secondary"
                          disabled={!canRecordCredentialRequest}
                          onClick={() => credentialRequestMutation.mutate()}
                          type="button"
                        >
                          {credentialRequestMutation.isPending
                            ? "Requesting credential setup"
                            : "Request credential setup"}
                        </button>
                      ) : null}
                    </div>
                  ))}
                </div>
                <div className="panel-lite integrations-step-card">
                  <div className="settings-summary-header">
                    <div>
                      <h3 className="section-heading">Credential setup requests</h3>
                      <p>
                        Record that this customer needs credential setup. This is a review request only; no key is
                        created, shown, stored in a vault, sent to a provider, or downloaded from the browser.
                      </p>
                    </div>
                    <StatusBadge
                      label={credentialRequests.length ? `${credentialRequests.length} request${credentialRequests.length === 1 ? "" : "s"}` : "None yet"}
                      tone={credentialRequests.length ? "info" : "neutral"}
                    />
                  </div>
                  {credentialRequests.length ? (
                    <div className="route-list">
                      {credentialRequests.map((credentialRequest) => (
                        <div className="wizard-status-card" key={credentialRequest.credentialRequestRef}>
                          <div>
                            <strong>
                              {credentialRequestLabel(credentialRequest.requestType)} for{" "}
                              {formatDisplay(credentialRequest.environment)}
                            </strong>
                            <p>
                              {formatDisplay(credentialRequest.capability)} -{" "}
                              {formatList(credentialRequest.intendedUse)}
                            </p>
                            <span className="table-subtext">
                              {credentialRequest.credentialRequestRef}
                              {credentialRequest.createdAt ? ` - ${credentialRequest.createdAt}` : ""}
                            </span>
                          </div>
                          <StatusBadge
                            label={formatDisplay(credentialRequest.reviewStatus)}
                            tone={statusTone(credentialRequest.reviewStatus)}
                          />
                          {credentialRequest.reviewStatus === "READY_FOR_REVIEW" ? (
                            <div className="action-row">
                              <button
                                className="button secondary"
                                disabled={credentialReviewMutation.isPending}
                                onClick={() =>
                                  credentialReviewMutation.mutate({
                                    credentialRequestRef: credentialRequest.credentialRequestRef,
                                    decision: "BLOCKED",
                                  })
                                }
                                type="button"
                              >
                                Block request
                              </button>
                              <button
                                className="button primary"
                                disabled={credentialReviewMutation.isPending}
                                onClick={() =>
                                  credentialReviewMutation.mutate({
                                    credentialRequestRef: credentialRequest.credentialRequestRef,
                                    decision: "APPROVED",
                                  })
                                }
                                type="button"
                              >
                                Approve request
                              </button>
                            </div>
                          ) : null}
                          {credentialRequest.reviewStatus === "REVIEW_APPROVED" ? (
                            <div className="action-row">
                              <button
                                className="button secondary"
                                disabled={credentialExecutionCheckMutation.isPending}
                                onClick={() =>
                                  credentialExecutionCheckMutation.mutate(
                                    credentialRequest.credentialRequestRef,
                                  )
                                }
                                type="button"
                              >
                                {credentialExecutionCheckMutation.isPending
                                  ? "Checking approved setup"
                                  : "Check approved setup"}
                              </button>
                            </div>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-panel">
                      No credential setup request has been recorded for this customer yet.
                    </div>
                  )}
                </div>
                {providerVaultReadiness ? (
                  <div className="panel-lite integrations-step-card">
                    <div className="settings-summary-header">
                      <div>
                        <h3 className="section-heading">Secure provider handoff</h3>
                        <p>
                          Shows whether approved credential requests are ready for a future governed provider/vault
                          executor. This page does not run that executor.
                        </p>
                      </div>
                      <StatusBadge
                        label={formatDisplay(providerVaultReadiness.readinessStatus)}
                        tone={statusTone(providerVaultReadiness.readinessStatus)}
                      />
                    </div>
                    <div
                      className={`wizard-summary-strip ${
                        providerVaultReadiness.readyActions.length ? "success" : "warning"
                      }`}
                    >
                      <div>
                        <strong>In plain English:</strong> {providerVaultReadiness.plainLanguageSummary}
                      </div>
                      <StatusBadge
                        label={`${providerVaultReadiness.readyActions.length} ready for handoff`}
                        tone={providerVaultReadiness.readyActions.length ? "success" : "warning"}
                      />
                    </div>
                    {providerVaultReadiness.blockers.length ? (
                      <div className="route-list">
                        {providerVaultReadiness.blockers.map((blocker) => (
                          <div className="wizard-status-card" key={`${blocker.code}-${blocker.message}`}>
                            <div>
                              <strong>{formatDisplay(blocker.code)}</strong>
                              <p>{blocker.message}</p>
                            </div>
                            <StatusBadge label="Fix first" tone="warning" />
                          </div>
                        ))}
                      </div>
                    ) : null}
                    {providerVaultReadiness.credentialRequests.length ? (
                      <div className="route-list">
                        {providerVaultReadiness.credentialRequests.map((credentialRequest) => (
                          <div className="integrations-check-row" key={credentialRequest.credentialRequestRef}>
                            <div>
                              <strong>
                                {credentialRequestLabel(credentialRequest.requestType)} -{" "}
                                {formatDisplay(credentialRequest.environment)}
                              </strong>
                              <p>{credentialRequest.plainLanguageSummary}</p>
                              <span className="table-subtext">
                                {credentialRequest.credentialRequestRef}
                                {credentialRequest.configurationRef
                                  ? ` - plan ${credentialRequest.configurationRef}`
                                  : ""}
                              </span>
                            </div>
                            <StatusBadge
                              label={credentialRequest.readyForExecution ? "Ready for handoff" : "Blocked"}
                              tone={credentialRequest.readyForExecution ? "success" : "warning"}
                            />
                            <span className="table-subtext">
                              {credentialRequest.nextActions[0]?.nextStep || "Resolve blockers before handoff."}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="empty-panel">
                        No credential request is approved for secure provider handoff yet.
                      </div>
                    )}
                    <div className="integrations-footnote">
                      <div>
                        <strong>Provider/vault boundary</strong>
                        <p>
                          No secret is shown, no credential is created or downloaded, no vault entry is written, no
                          provider is called, no webhook or message is dispatched, no auth changes, no campaign
                          activation, no billing, and no money movement happens here.
                        </p>
                      </div>
                      <StatusBadge label="Read-only readiness" tone="success" />
                    </div>
                  </div>
                ) : null}
                <div className="action-row integrations-handoff-row">
                  <Link className="button secondary" to={`${selectedCustomerPath}/people`}>
                    Open People & access
                  </Link>
                  <Link className="button primary" to={`${selectedCustomerPath}/campaigns`}>
                    Continue to Campaigns
                  </Link>
                </div>
              </div>
            ) : null}

            <div className="integrations-footnote">
              <div>
                <strong>What this page will not do</strong>
                <p>
                  Saves a non-secret connection plan and records safe verification checks. It does not create
                  credentials, dispatch business webhooks, send invites, activate login, assign seats, launch
                  campaigns, bill, or move money.
                </p>
              </div>
              <StatusBadge label="Safe setup check" tone="success" />
            </div>
          </>
        ) : null}
      </div>
    </section>
  );
}

type JourneyConfigurationDraft = {
  customerJourneyDraftId: string;
  templateCode: string;
  templateVersion: string;
  draftName: string;
  milestoneCodes: string;
  transitionRules: string;
  evidenceCodes: string;
  rewardPolicyCode: string;
  attributionWindowDays: string;
};

const defaultJourneyDraft: JourneyConfigurationDraft = {
  customerJourneyDraftId: "",
  templateCode: "",
  templateVersion: "",
  draftName: "Standard referral journey",
  milestoneCodes: "REFERRED, QUALIFIED, CONVERTED",
  transitionRules: "REFERRED > QUALIFIED\nQUALIFIED > CONVERTED",
  evidenceCodes: "CUSTOMER_REFERENCE, ACCEPTED_TERMS, OUTCOME_EVENT",
  rewardPolicyCode: "",
  attributionWindowDays: "30",
};

function CustomerJourneysPage({
  customerName,
  externalTenantRef,
  selectedAccount,
  selectedCustomerPath,
}: {
  customerName: string;
  externalTenantRef: string;
  selectedAccount?: AccountRegistryItem;
  selectedCustomerPath: string;
}) {
  const [draft, setDraft] = useState<JourneyConfigurationDraft>(defaultJourneyDraft);
  const [selectedTemplateCode, setSelectedTemplateCode] = useState("");
  const [latestValidation, setLatestValidation] =
    useState<ReferralSaasCustomerJourneyDraftValidationResponse | null>(null);
  const [latestPublish, setLatestPublish] = useState<ReferralSaasCustomerJourneyPublishResponse | null>(null);
  const [journeyMessage, setJourneyMessage] = useState<string | null>(null);
  const accountScope = {
    refType: "external_tenant_ref" as const,
    externalRef: externalTenantRef,
    context: "setup" as const,
  };
  const templatesQuery = useQuery({
    queryKey: ["referral-saas", "journey-templates", "approved"],
    queryFn: () => listReferralSaasJourneyTemplates({ statuses: ["APPROVED"], limit: 50 }),
    retry: false,
  });
  const draftsQuery = useQuery({
    queryKey: ["referral-saas", "journey-drafts", selectedAccount?.accountId || "", externalTenantRef],
    queryFn: () =>
      listReferralSaasAccountJourneyDrafts({
        accountRef: selectedAccount?.accountId || "",
        refType: "external_tenant_ref",
        externalRef: externalTenantRef,
        context: "setup",
        limit: 50,
      }),
    enabled: Boolean(selectedAccount?.accountId && externalTenantRef),
    retry: false,
  });
  const templates = templatesQuery.data?.templates || [];
  const selectedTemplate =
    templates.find((template) => template.templateCode === (selectedTemplateCode || draft.templateCode)) ||
    templates[0];
  const selectedVersion =
    selectedTemplate?.versions.find((version) => version.templateVersion === draft.templateVersion) ||
    selectedTemplate?.versions[0];
  const savedDraftRef = draft.customerJourneyDraftId;
  const canValidate = Boolean(selectedAccount?.accountId && savedDraftRef);
  const validationStatus = latestValidation?.validation.validationStatus || "";
  const canPublish =
    canValidate &&
    Boolean(validationStatus) &&
    !["FAILED", "BLOCKED", "INVALID"].some((blocked) => validationStatus.toUpperCase().includes(blocked));

  useEffect(() => {
    if (!selectedTemplate || draft.templateCode) {
      return;
    }
    setDraft((current) => ({
      ...current,
      templateCode: selectedTemplate.templateCode,
      templateVersion: selectedTemplate.versions[0]?.templateVersion || "",
      draftName: `${selectedTemplate.templateName} for ${customerName}`,
    }));
    setSelectedTemplateCode(selectedTemplate.templateCode);
  }, [customerName, draft.templateCode, selectedTemplate]);

  function selectTemplate(template: ReferralSaasJourneyTemplateCatalogueItem) {
    setSelectedTemplateCode(template.templateCode);
    setLatestValidation(null);
    setLatestPublish(null);
    setDraft((current) => ({
      ...current,
      customerJourneyDraftId: "",
      templateCode: template.templateCode,
      templateVersion: template.versions[0]?.templateVersion || "",
      draftName: `${template.templateName} for ${customerName}`,
    }));
  }

  function loadDraft(savedDraft: ReferralSaasCustomerJourneyDraft) {
    const payload = savedDraft.configurationPayload || {};
    setLatestValidation(null);
    setLatestPublish(null);
    setSelectedTemplateCode(savedDraft.templateCode);
    setDraft({
      customerJourneyDraftId: savedDraft.customerJourneyDraftId,
      templateCode: savedDraft.templateCode,
      templateVersion: savedDraft.templateVersion,
      draftName: savedDraft.draftName,
      milestoneCodes: extractPayloadCodes(payload, "milestones"),
      transitionRules: extractPayloadTransitions(payload),
      evidenceCodes: extractPayloadCodes(payload, "evidence"),
      rewardPolicyCode: textValue(getNestedValue(payload, ["rewards", "policyCode"])),
      attributionWindowDays: textValue(getNestedValue(payload, ["attribution", "attributionWindowDays"]), "30"),
    });
    setJourneyMessage("Draft loaded. Review the configuration, then validate it before publishing.");
  }

  const saveMutation = useMutation({
    mutationFn: () =>
      saveReferralSaasAccountJourneyDraft({
        accountRef: selectedAccount?.accountId || "",
        accountScope,
        templateCode: draft.templateCode || selectedTemplate?.templateCode || "",
        templateVersion: draft.templateVersion || selectedVersion?.templateVersion || null,
        draftName: draft.draftName,
        configurationPayload: buildJourneyConfigurationPayload(draft, selectedVersion),
        customerJourneyDraftId: draft.customerJourneyDraftId || null,
        correlationId: safeIdempotencyKey("journey-draft", selectedAccount?.accountId || "", draft.draftName),
        idempotencyKey: safeIdempotencyKey(
          "save-journey-draft",
          selectedAccount?.accountId || "",
          draft.templateCode || selectedTemplate?.templateCode || "",
          draft.draftName,
        ),
      }),
    onSuccess: async (response) => {
      setDraft((current) => ({
        ...current,
        customerJourneyDraftId: response.draft.customerJourneyDraftId,
        templateCode: response.draft.templateCode,
        templateVersion: response.draft.templateVersion,
        draftName: response.draft.draftName,
      }));
      setLatestValidation(null);
      setLatestPublish(null);
      setJourneyMessage(
        `${formatDisplay(response.commandStatus)}. Customer journey draft saved. Validate it before publishing.`,
      );
      await draftsQuery.refetch();
    },
  });
  const validateMutation = useMutation({
    mutationFn: () =>
      validateReferralSaasAccountJourneyDraft({
        accountRef: selectedAccount?.accountId || "",
        draftRef: savedDraftRef,
        accountScope,
        correlationId: safeIdempotencyKey("journey-validation", selectedAccount?.accountId || "", savedDraftRef),
        idempotencyKey: safeIdempotencyKey("validate-journey-draft", selectedAccount?.accountId || "", savedDraftRef),
      }),
    onSuccess: async (response) => {
      setLatestValidation(response);
      setJourneyMessage(`${formatDisplay(response.validation.validationStatus)}. Validation evidence recorded.`);
      await draftsQuery.refetch();
    },
  });
  const publishMutation = useMutation({
    mutationFn: () =>
      publishReferralSaasAccountJourneyDraft({
        accountRef: selectedAccount?.accountId || "",
        draftRef: savedDraftRef,
        accountScope,
        correlationId: safeIdempotencyKey("journey-publish", selectedAccount?.accountId || "", savedDraftRef),
        idempotencyKey: safeIdempotencyKey("publish-journey-draft", selectedAccount?.accountId || "", savedDraftRef),
      }),
    onSuccess: async (response) => {
      setLatestPublish(response);
      setJourneyMessage(
        `${formatDisplay(response.commandStatus)}. Published an immutable customer journey version for later campaign binding.`,
      );
      await draftsQuery.refetch();
    },
  });

  return (
    <section className="panel customer-module-page" id="journeys">
      <div className="panel-header">
        <div>
          <div className="page-kicker">Referral SaaS &gt; {customerName} &gt; Journeys</div>
          <h2 className="panel-title">Journey configuration</h2>
          <div className="panel-subtitle">
            Select an approved template, save this customer's draft, validate it, then publish a version for later
            campaign binding.
          </div>
        </div>
        <StatusBadge label="Customer scoped" tone="success" />
      </div>
      <div className="panel-body route-list">
        {templatesQuery.isLoading || draftsQuery.isLoading ? <LoadingState label="Loading journey configuration" /> : null}
        {templatesQuery.error ? <ErrorPanel error={templatesQuery.error} /> : null}
        {draftsQuery.error ? <ErrorPanel error={draftsQuery.error} /> : null}
        {saveMutation.error ? <ErrorPanel error={saveMutation.error} /> : null}
        {validateMutation.error ? <ErrorPanel error={validateMutation.error} /> : null}
        {publishMutation.error ? <ErrorPanel error={publishMutation.error} /> : null}
        {journeyMessage ? (
          <div className="success-banner">
            <strong>Journey configuration updated.</strong> {journeyMessage}
          </div>
        ) : null}
        <div className="integrations-stage-card success">
          <div>
            <strong>What this page does</strong>
            <p>
              It prepares a customer-specific journey version from approved templates. The version is safe for later
              campaign binding, but it does not switch runtime behaviour by itself.
            </p>
          </div>
          <StatusBadge label="No live switch" tone="warning" />
        </div>

        <div className="integrations-plan-grid">
          <div className="panel-lite integrations-step-card">
            <h3 className="section-heading">1. Choose approved template</h3>
            <p>Only governed templates are shown. Customer-specific data is configured in the draft below.</p>
            <div className="route-list">
              {templates.map((template) => (
                <button
                  className={`wizard-status-card ${template.templateCode === selectedTemplate?.templateCode ? "active" : ""}`}
                  key={template.journeyTemplateId}
                  onClick={() => selectTemplate(template)}
                  type="button"
                >
                  <div>
                    <strong>{template.templateName}</strong>
                    <p>{textValue(getNestedValue(template.safeSummary, ["description"], "Approved journey template."))}</p>
                    <span className="table-subtext">
                      {template.templateCode} - {formatDisplay(template.templateFamily)} -{" "}
                      {template.versions[0]?.milestoneCount || 0} milestones
                    </span>
                  </div>
                  <StatusBadge label={formatDisplay(template.status)} tone={statusTone(template.status)} />
                </button>
              ))}
              {!templates.length && !templatesQuery.isLoading ? (
                <div className="empty-panel">No approved journey templates are available.</div>
              ) : null}
            </div>
          </div>

          <form
            className="panel-lite integrations-step-card"
            onSubmit={(event: FormEvent) => {
              event.preventDefault();
              saveMutation.mutate();
            }}
          >
            <h3 className="section-heading">2. Configure customer draft</h3>
            <p>Use plain configuration values. Sections unsupported by the selected template are not sent.</p>
            <div className="grid-2">
              <label>
                Template version
                <select
                  onChange={(event) => setDraft({ ...draft, templateVersion: event.target.value })}
                  value={draft.templateVersion}
                >
                  {(selectedTemplate?.versions || []).map((version) => (
                    <option key={version.journeyTemplateVersionId} value={version.templateVersion}>
                      {version.templateVersion} - {formatDisplay(version.status)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Draft name
                <input
                  onChange={(event) => setDraft({ ...draft, draftName: event.target.value })}
                  value={draft.draftName}
                />
              </label>
            </div>
            <label>
              Milestone codes
              <textarea
                onChange={(event) => setDraft({ ...draft, milestoneCodes: event.target.value })}
                value={draft.milestoneCodes}
              />
            </label>
            <label>
              Transition rules
              <textarea
                onChange={(event) => setDraft({ ...draft, transitionRules: event.target.value })}
                value={draft.transitionRules}
              />
            </label>
            <label>
              Evidence codes
              <textarea
                onChange={(event) => setDraft({ ...draft, evidenceCodes: event.target.value })}
                value={draft.evidenceCodes}
              />
            </label>
            <div className="grid-2">
              <label>
                Reward policy reference
                <input
                  onChange={(event) => setDraft({ ...draft, rewardPolicyCode: event.target.value })}
                  placeholder="Optional approved reward policy code"
                  value={draft.rewardPolicyCode}
                />
              </label>
              <label>
                Attribution window
                <input
                  onChange={(event) => setDraft({ ...draft, attributionWindowDays: event.target.value })}
                  type="number"
                  value={draft.attributionWindowDays}
                />
              </label>
            </div>
            <div className="action-row">
              <button className="button primary" disabled={!selectedAccount?.accountId || saveMutation.isPending} type="submit">
                {saveMutation.isPending ? "Saving" : "Save journey draft"}
              </button>
              <button
                className="button secondary"
                disabled={!canValidate || validateMutation.isPending}
                onClick={() => validateMutation.mutate()}
                type="button"
              >
                {validateMutation.isPending ? "Validating" : "Validate draft"}
              </button>
              <button
                className="button secondary"
                disabled={!canPublish || publishMutation.isPending}
                onClick={() => publishMutation.mutate()}
                type="button"
              >
                {publishMutation.isPending ? "Publishing" : "Publish journey version"}
              </button>
            </div>
          </form>
        </div>

        {latestValidation ? (
          <JourneyValidationPanel validationResponse={latestValidation} />
        ) : null}
        {latestPublish ? (
          <div className="success-banner">
            <strong>Published journey version.</strong>{" "}
            {latestPublish.version.customerJourneyCode} v{latestPublish.version.versionNumber} is ready for TASK-390
            campaign binding.
          </div>
        ) : null}

        <div className="panel-lite integrations-step-card">
          <div className="settings-summary-header">
            <div>
              <h3 className="section-heading">Saved drafts</h3>
              <p>Continue an existing customer draft or publish a newly validated one.</p>
            </div>
            <StatusBadge label={`${draftsQuery.data?.count || 0} drafts`} tone="info" />
          </div>
          <div className="route-list">
            {(draftsQuery.data?.drafts || []).map((savedDraft) => (
              <div className="wizard-status-card" key={savedDraft.customerJourneyDraftId}>
                <div>
                  <strong>{savedDraft.draftName}</strong>
                  <p>
                    {savedDraft.templateCode} {savedDraft.templateVersion} -{" "}
                    {formatDisplay(savedDraft.lastValidationStatus)}
                  </p>
                  <span className="table-subtext">
                    Version {savedDraft.draftVersion}
                    {savedDraft.updatedAt ? ` - updated ${savedDraft.updatedAt}` : ""}
                  </span>
                </div>
                <StatusBadge label={formatDisplay(savedDraft.draftStatus)} tone={statusTone(savedDraft.draftStatus)} />
                <button className="button secondary" onClick={() => loadDraft(savedDraft)} type="button">
                  Use draft
                </button>
              </div>
            ))}
            {!draftsQuery.data?.drafts?.length && !draftsQuery.isLoading ? (
              <div className="empty-panel">No customer journey drafts exist yet.</div>
            ) : null}
          </div>
        </div>

        <div className="integrations-footnote">
          <div>
            <strong>Journey configuration boundary</strong>
            <p>
              This page does not mutate runtime journey execution, bind campaigns, activate campaigns, dispatch
              providers, create credentials, change auth, bill, settle, pay out, or move money.
            </p>
          </div>
          <StatusBadge label="Governed draft only" tone="success" />
        </div>

        <div className="action-row integrations-handoff-row">
          <Link className="button secondary" to={selectedCustomerPath}>
            Customer home
          </Link>
          <Link className="button primary" to={`${selectedCustomerPath}/campaigns`}>
            Continue to Campaigns
          </Link>
        </div>
      </div>
    </section>
  );
}

function JourneyValidationPanel({
  validationResponse,
}: {
  validationResponse: ReferralSaasCustomerJourneyDraftValidationResponse;
}) {
  const validation = validationResponse.validation;
  const summary = validation.safeSummary || {};
  const simulatedPath = textArray(getNestedValue(summary, ["simulation", "simulatedMilestonePath"]));
  return (
    <div className="panel-lite integrations-step-card">
      <div className="settings-summary-header">
        <div>
          <h3 className="section-heading">Validation feedback</h3>
          <p>Use this before publishing. Blockers must be fixed; warnings can be reviewed deliberately.</p>
        </div>
        <StatusBadge label={formatDisplay(validation.validationStatus)} tone={statusTone(validation.validationStatus)} />
      </div>
      <div className="grid-2">
        <div className={`wizard-summary-strip ${validation.blockers.length ? "warning" : "success"}`}>
          <div>
            <strong>{validation.blockers.length} blockers</strong>
            <p>{validation.blockers.length ? "Fix these before publish." : "No publish blockers returned."}</p>
          </div>
        </div>
        <div className={`wizard-summary-strip ${validation.warnings.length ? "warning" : "success"}`}>
          <div>
            <strong>{validation.warnings.length} warnings</strong>
            <p>{validation.warnings.length ? "Review these before campaign binding." : "No warnings returned."}</p>
          </div>
        </div>
      </div>
      {validation.blockers.length || validation.warnings.length ? (
        <div className="route-list">
          {[...validation.blockers, ...validation.warnings].map((item, index) => (
            <div
              className="wizard-status-card"
              key={`${textValue(getNestedValue(item, ["code"], "item"))}-${index}`}
            >
              <div>
                <strong>{formatDisplay(textValue(getNestedValue(item, ["code"], "Validation item")))}</strong>
                <p>{textValue(getNestedValue(item, ["message"], "Review this validation item."))}</p>
              </div>
              <StatusBadge label={index < validation.blockers.length ? "Blocker" : "Warning"} tone="warning" />
            </div>
          ))}
        </div>
      ) : null}
      {simulatedPath.length ? (
        <div className="integrations-footnote">
          <div>
            <strong>Simulated path</strong>
            <p>{simulatedPath.join(" -> ")}</p>
          </div>
          <StatusBadge label="Read-only simulation" tone="info" />
        </div>
      ) : null}
    </div>
  );
}

type ProgrammeConfigurationDraft = {
  programmeDraftId: string;
  programmeName: string;
  programmeDescription: string;
  customerJourneyVersionId: string;
  customerProductLineId: string;
  customerProductOfferingId: string;
  subProductCode: string;
  campaignPurpose: string;
  defaultAttributionWindowDays: string;
  incentiveRef: string;
  engagementRef: string;
  effectiveFrom: string;
  effectiveTo: string;
  reviewReason: string;
  publishReason: string;
};

const defaultProgrammeDraft: ProgrammeConfigurationDraft = {
  programmeDraftId: "",
  programmeName: "",
  programmeDescription: "Referral management and campaign attribution programme.",
  customerJourneyVersionId: "",
  customerProductLineId: "",
  customerProductOfferingId: "",
  subProductCode: "RMCA_BUNDLE",
  campaignPurpose: "Customer referral acquisition",
  defaultAttributionWindowDays: "30",
  incentiveRef: "",
  engagementRef: "",
  effectiveFrom: "",
  effectiveTo: "",
  reviewReason: "Programme package reviewed for customer-safe campaign setup.",
  publishReason: "Approved for customer-scoped campaign setup.",
};

function isActiveCustomerProductStatus(status?: string | null) {
  return ["ACTIVE", "PUBLISHED"].includes(String(status || "").toUpperCase());
}

function productLineLabel(line: ReferralSaasCustomerProductLineSummary) {
  const category = line.productLineCategory ? ` - ${formatDisplay(line.productLineCategory)}` : "";
  return `${line.productLineName}${category}`;
}

function productOfferingLabel(offering: ReferralSaasCustomerProductOfferingSummary) {
  const family = offering.offeringFamily ? ` - ${formatDisplay(offering.offeringFamily)}` : "";
  return `${offering.offeringName}${family}`;
}

function programmeProductBindingLabel(binding?: ReferralSaasCustomerProductBindingSummary | null) {
  if (!binding) {
    return "Customer product not shown";
  }
  const productLine = binding.productLineName || binding.externalProductLineRef;
  const offering = binding.offeringName || binding.externalOfferingRef;
  if (productLine && offering) {
    return `${productLine} - ${offering}`;
  }
  return productLine || offering || "Customer product not shown";
}

function CustomerProgrammesPage({
  customerName,
  externalTenantRef,
  selectedAccount,
  selectedCustomerPath,
}: {
  customerName: string;
  externalTenantRef: string;
  selectedAccount?: AccountRegistryItem;
  selectedCustomerPath: string;
}) {
  const [draft, setDraft] = useState<ProgrammeConfigurationDraft>({
    ...defaultProgrammeDraft,
    programmeName: `${customerName} referral programme`,
  });
  const [latestValidation, setLatestValidation] = useState<ReferralSaasProgrammeValidationResponse | null>(null);
  const [latestLifecycle, setLatestLifecycle] = useState<ReferralSaasProgrammeLifecycleResponse | null>(null);
  const [programmeMessage, setProgrammeMessage] = useState<string | null>(null);
  const accountScope = {
    refType: "external_tenant_ref" as const,
    externalRef: externalTenantRef,
    context: "setup" as const,
  };
  const accountRef = selectedAccount?.accountId || "";
  const catalogueQuery = useQuery({
    queryKey: ["referral-saas", "programme-catalogue", accountRef, externalTenantRef],
    queryFn: () =>
      getReferralSaasAccountProgrammeCatalogue({
        accountRef,
        refType: "external_tenant_ref",
        externalRef: externalTenantRef,
        context: "setup",
        limit: 50,
      }),
    enabled: Boolean(accountRef && externalTenantRef),
    retry: false,
  });
  const programmesQuery = useQuery({
    queryKey: ["referral-saas", "programmes", accountRef, externalTenantRef],
    queryFn: () =>
      listReferralSaasAccountProgrammes({
        accountRef,
        refType: "external_tenant_ref",
        externalRef: externalTenantRef,
        context: "setup",
        includeRetired: true,
        limit: 50,
      }),
    enabled: Boolean(accountRef && externalTenantRef),
    retry: false,
  });
  const analyticsQuery = useQuery({
    queryKey: ["referral-saas", "programme-analytics", accountRef, externalTenantRef],
    queryFn: () =>
      getReferralSaasAccountProgrammeAnalytics({
        accountRef,
        refType: "external_tenant_ref",
        externalRef: externalTenantRef,
        context: "setup",
        limit: 50,
      }),
    enabled: Boolean(accountRef && externalTenantRef),
    retry: false,
  });
  const journeyVersions = catalogueQuery.data?.customerJourneyVersions || [];
  const customerProductLines = (catalogueQuery.data?.customerProductLines || []).filter((line) =>
    isActiveCustomerProductStatus(line.lifecycleStatus),
  );
  const subProductCodes = catalogueQuery.data?.subProductCodes || ["RMCA_BUNDLE"];
  const publishedProgrammes = programmesQuery.data?.programmes || [];
  const activeProgrammes = publishedProgrammes.filter((programme) =>
    ["ACTIVE", "PUBLISHED"].includes(programme.versionStatus),
  );
  const analyticsVersions = analyticsQuery.data?.programmeAnalytics.versions || [];
  const reportingDimensions = analyticsQuery.data?.programmeAnalytics.reportingDimensions;
  const selectedJourney =
    journeyVersions.find((version) => version.customerJourneyVersionId === draft.customerJourneyVersionId) ||
    journeyVersions[0];
  const selectedProductLine = customerProductLines.find(
    (line) => line.customerProductLineId === draft.customerProductLineId,
  );
  const availableProductOfferings = (selectedProductLine?.offerings || []).filter((offering) =>
    isActiveCustomerProductStatus(offering.lifecycleStatus),
  );
  const selectedProductOffering = availableProductOfferings.find(
    (offering) => offering.customerProductOfferingId === draft.customerProductOfferingId,
  );
  const hasProductCatalogue = customerProductLines.length > 0;
  const productSelectionReady = Boolean(selectedProductLine && selectedProductOffering);
  const canSave = Boolean(
    accountRef && (draft.customerJourneyVersionId || selectedJourney?.customerJourneyVersionId) && productSelectionReady,
  );
  const canValidate = Boolean(accountRef && draft.programmeDraftId);
  const publishAllowed = Boolean(latestValidation?.validation.publishAllowed);
  const canPublish = canValidate && publishAllowed;
  const programmeNextAction = !productSelectionReady
    ? {
        title: "Choose the customer product first",
        copy: "Pick the product line and offering this referral programme is for. This keeps customer products separate from Amplifi package codes.",
        label: "Product required",
        tone: "warning" as StatusTone,
      }
    : !draft.programmeDraftId
      ? {
          title: "Save the programme draft",
          copy: "Create the safe draft before validation, review, or publishing. Nothing goes live from a draft save.",
          label: "Save next",
          tone: "warning" as StatusTone,
        }
      : !latestValidation
        ? {
            title: "Validate the programme",
            copy: "Run the readiness check so blockers are clear before review and publish.",
            label: "Validate next",
            tone: "info" as StatusTone,
          }
        : !publishAllowed
          ? {
              title: "Fix validation blockers",
              copy: "The programme is saved, but it is not ready to publish. Resolve blockers before campaign teams use it.",
              label: "Needs work",
              tone: "warning" as StatusTone,
            }
          : {
              title: "Publish the programme version",
              copy: "Publishing creates the immutable package campaigns can bind to. Campaigns still activate separately.",
              label: "Publish next",
              tone: "success" as StatusTone,
            };

  function journeyVersionLabel(customerJourneyVersionId: string) {
    const version = journeyVersions.find((journeyVersion) => journeyVersion.customerJourneyVersionId === customerJourneyVersionId);
    if (!version) {
      return "Published journey";
    }
    const journeyName = programmeJourneyDisplayName(version.templateCode);
    return `${journeyName} v${version.versionNumber}`;
  }

  function programmeJourneyDisplayName(templateCode: string) {
    const parts = templateCode
      .split("_")
      .map((part) => part.toLowerCase())
      .filter(Boolean);
    if (parts.length > 1 && parts[parts.length - 1] === "standard") {
      return `Standard ${parts.slice(0, -1).join(" ")}`;
    }
    return formatDisplay(templateCode);
  }

  useEffect(() => {
    if (draft.customerJourneyVersionId || !selectedJourney) {
      return;
    }
    setDraft((current) => ({
      ...current,
      customerJourneyVersionId: selectedJourney.customerJourneyVersionId,
    }));
  }, [draft.customerJourneyVersionId, selectedJourney]);

  function loadProgrammeDraft(savedDraft: ReferralSaasProgrammeDraft) {
    const campaignDefaults = asRecord(savedDraft.campaignDefaults);
    setDraft({
      programmeDraftId: savedDraft.programmeDraftId,
      programmeName: savedDraft.programmeName,
      programmeDescription: savedDraft.programmeDescription || "",
      customerJourneyVersionId: savedDraft.customerJourneyVersionId,
      customerProductLineId: savedDraft.customerProductLineId || "",
      customerProductOfferingId: savedDraft.customerProductOfferingId || "",
      subProductCode: savedDraft.subProductCode,
      campaignPurpose: textValue(getNestedValue(campaignDefaults, ["campaignPurpose"]), "Customer referral acquisition"),
      defaultAttributionWindowDays: textValue(
        getNestedValue(campaignDefaults, ["attributionWindowDays"]),
        "30",
      ),
      incentiveRef: textValue(savedDraft.incentiveRefs[0]),
      engagementRef: textValue(savedDraft.engagementRefs[0]),
      effectiveFrom: savedDraft.effectiveFrom || "",
      effectiveTo: savedDraft.effectiveTo || "",
      reviewReason: "Programme package reviewed for customer-safe campaign setup.",
      publishReason: "Approved for customer-scoped campaign setup.",
    });
    setLatestValidation(null);
    setLatestLifecycle(null);
    setProgrammeMessage("Programme draft loaded. Validate it before review or publish.");
  }

  function programmePayload() {
    const attributionWindowDays = Number(draft.defaultAttributionWindowDays);
    return {
      accountScope,
      programmeName: draft.programmeName.trim() || `${customerName} referral programme`,
      programmeDescription: draft.programmeDescription.trim() || null,
      operatingJurisdictionCode: selectedAccount?.operatingJurisdictionCode || defaultOperatingMarket,
      productCode: catalogueQuery.data?.productCode || "REFERRAL_SAAS",
      subProductCode: draft.subProductCode || subProductCodes[0] || "RMCA_BUNDLE",
      customerProductLineId: draft.customerProductLineId,
      customerProductOfferingId: draft.customerProductOfferingId,
      customerJourneyVersionId: draft.customerJourneyVersionId || selectedJourney?.customerJourneyVersionId || "",
      campaignDefaults: {
        campaignPurpose: draft.campaignPurpose.trim() || "Customer referral acquisition",
        attributionWindowDays: Number.isFinite(attributionWindowDays) && attributionWindowDays > 0 ? attributionWindowDays : 30,
        setupMode: "customer_scoped_programme",
      },
      incentiveRefs: draft.incentiveRef.trim() ? [draft.incentiveRef.trim()] : [],
      engagementRefs: draft.engagementRef.trim() ? [draft.engagementRef.trim()] : [],
      integrationReadinessSnapshot: {
        providerDispatch: "not_performed",
        credentials: "not_created",
      },
      commercialEntitlementSnapshot: {
        billing: "not_performed",
        moneyMovement: "not_performed",
      },
      effectiveFrom: draft.effectiveFrom || null,
      effectiveTo: draft.effectiveTo || null,
      correlationId: safeIdempotencyKey("programme-draft", accountRef, draft.programmeName),
      idempotencyKey: safeIdempotencyKey(
        "save-programme-draft",
        accountRef,
        draft.programmeDraftId || "new",
        draft.programmeName,
        draft.customerJourneyVersionId || selectedJourney?.customerJourneyVersionId || "",
        draft.customerProductLineId,
        draft.customerProductOfferingId,
        draft.subProductCode,
      ),
    };
  }

  const saveMutation = useMutation({
    mutationFn: () =>
      draft.programmeDraftId
        ? updateReferralSaasProgrammeDraft({
            accountRef,
            draftRef: draft.programmeDraftId,
            body: programmePayload(),
          })
        : createReferralSaasProgrammeDraft({
            accountRef,
            body: programmePayload(),
          }),
    onSuccess: async (response) => {
      setDraft((current) => ({
        ...current,
        programmeDraftId: response.draft.programmeDraftId,
        programmeName: response.draft.programmeName,
        customerJourneyVersionId: response.draft.customerJourneyVersionId,
        customerProductLineId: response.draft.customerProductLineId || current.customerProductLineId,
        customerProductOfferingId: response.draft.customerProductOfferingId || current.customerProductOfferingId,
        subProductCode: response.draft.subProductCode,
      }));
      setLatestValidation(null);
      setLatestLifecycle(null);
      setProgrammeMessage(`${formatDisplay(response.commandStatus)}. Programme draft saved. Validate it next.`);
      await programmesQuery.refetch();
    },
  });
  const validateMutation = useMutation({
    mutationFn: () =>
      validateReferralSaasProgrammeDraft({
        accountRef,
        draftRef: draft.programmeDraftId,
        accountScope,
        correlationId: safeIdempotencyKey("programme-validation", accountRef, draft.programmeDraftId),
        idempotencyKey: safeIdempotencyKey(
          "validate-programme-draft",
          accountRef,
          draft.programmeDraftId,
          draft.programmeName,
        ),
      }),
    onSuccess: (response) => {
      setLatestValidation(response);
      setLatestLifecycle(null);
      setProgrammeMessage(response.validation.plainLanguageSummary || "Programme validation recorded.");
    },
  });
  const submitReviewMutation = useMutation({
    mutationFn: () =>
      submitReferralSaasProgrammeDraftReview({
        accountRef,
        draftRef: draft.programmeDraftId,
        accountScope,
        reviewReason: draft.reviewReason,
        correlationId: safeIdempotencyKey("programme-review-submit", accountRef, draft.programmeDraftId),
        idempotencyKey: safeIdempotencyKey("submit-programme-review", accountRef, draft.programmeDraftId),
      }),
    onSuccess: (response) => {
      setLatestLifecycle(response);
      setProgrammeMessage(response.plainLanguageSummary || "Programme draft submitted for review.");
    },
  });
  const approveMutation = useMutation({
    mutationFn: () =>
      decideReferralSaasProgrammeDraftReview({
        accountRef,
        draftRef: draft.programmeDraftId,
        accountScope,
        decision: "APPROVED",
        reviewReason: draft.reviewReason,
        correlationId: safeIdempotencyKey("programme-review-approval", accountRef, draft.programmeDraftId),
        idempotencyKey: safeIdempotencyKey("approve-programme-review", accountRef, draft.programmeDraftId),
      }),
    onSuccess: (response) => {
      setLatestLifecycle(response);
      setProgrammeMessage(response.plainLanguageSummary || "Programme draft approved for publish.");
    },
  });
  const publishMutation = useMutation({
    mutationFn: () =>
      publishReferralSaasProgrammeDraft({
        accountRef,
        draftRef: draft.programmeDraftId,
        accountScope,
        publishReason: draft.publishReason,
        correlationId: safeIdempotencyKey("programme-publish", accountRef, draft.programmeDraftId),
        idempotencyKey: safeIdempotencyKey("publish-programme", accountRef, draft.programmeDraftId),
      }),
    onSuccess: async (response) => {
      setLatestLifecycle(response);
      setProgrammeMessage(response.plainLanguageSummary || "Programme version published for campaign setup.");
      await Promise.all([programmesQuery.refetch(), analyticsQuery.refetch()]);
    },
  });

  return (
    <section className="panel customer-module-page" id="programmes">
      <div className="panel-header">
        <div>
          <div className="page-kicker">Referral SaaS &gt; {customerName} &gt; Programmes</div>
          <h2 className="panel-title">Programme workspace</h2>
          <div className="panel-subtitle">
            A programme is the governed package a campaign uses: journey version, product scope, defaults, and safe
            incentive references.
          </div>
        </div>
        <StatusBadge label="Customer scoped" tone="success" />
      </div>
      <div className="panel-body route-list">
        {catalogueQuery.isLoading || programmesQuery.isLoading || analyticsQuery.isLoading ? (
          <LoadingState label="Loading programme workspace" />
        ) : null}
        {catalogueQuery.error ? <ErrorPanel error={catalogueQuery.error} /> : null}
        {programmesQuery.error ? <ErrorPanel error={programmesQuery.error} /> : null}
        {analyticsQuery.error ? <ErrorPanel error={analyticsQuery.error} /> : null}
        {saveMutation.error ? <ErrorPanel error={saveMutation.error} /> : null}
        {validateMutation.error ? <ErrorPanel error={validateMutation.error} /> : null}
        {submitReviewMutation.error ? <ErrorPanel error={submitReviewMutation.error} /> : null}
        {approveMutation.error ? <ErrorPanel error={approveMutation.error} /> : null}
        {publishMutation.error ? <ErrorPanel error={publishMutation.error} /> : null}
        {programmeMessage ? (
          <div className="success-banner">
            <strong>Programme updated.</strong> {programmeMessage}
          </div>
        ) : null}

        <div className="kpi-grid">
          <KpiCard
            label="Published programmes"
            value={publishedProgrammes.length}
            footnote="Versioned packages for campaigns"
            icon={FileJson}
          />
          <KpiCard
            label="Active packages"
            value={activeProgrammes.length}
            footnote="Usable or published programme versions"
            icon={CheckCircle2}
          />
          <KpiCard
            label="Comparable versions"
            value={analyticsVersions.length}
            footnote="Analytics-ready programme versions"
            icon={BarChart3}
          />
        </div>

        <div className={`integrations-stage-card ${programmeNextAction.tone === "success" ? "success" : "warning"}`}>
          <div>
            <strong>Do this next: {programmeNextAction.title}</strong>
            <p>{programmeNextAction.copy}</p>
          </div>
          <StatusBadge label={programmeNextAction.label} tone={programmeNextAction.tone} />
        </div>

        <div className="panel-lite integrations-step-card">
          <div className="settings-summary-header">
            <div>
              <h3 className="section-heading">How this stays simple</h3>
              <p>
                Build the reusable referral rules here. Campaigns only choose when, where, and how to run those rules;
                approved campaign changes stay visible and bounded.
              </p>
            </div>
            <StatusBadge label="No raw config" tone="success" />
          </div>
          <div className="configuration-proof-grid">
            {configurationProofSteps.map((step, index) => (
              <Link
                className="configuration-proof-card"
                key={step.title}
                to={buildCustomerModuleRoute(selectedCustomerPath, step.route, "")}
              >
                <span className="configuration-proof-index">{index + 1}</span>
                <div>
                  <strong>{step.title}</strong>
                  <p>{step.copy}</p>
                  <span>{step.action}</span>
                </div>
              </Link>
            ))}
          </div>
        </div>

        <form
          className="panel-lite integrations-step-card"
          onSubmit={(event: FormEvent) => {
            event.preventDefault();
            saveMutation.mutate();
          }}
        >
          <div className="settings-summary-header">
            <div>
              <h3 className="section-heading">1. Build the programme package</h3>
              <p>
                First choose the customer's real product and offering, then choose the published journey and defaults
                campaigns should inherit.
              </p>
            </div>
            <StatusBadge label="No live action" tone="warning" />
          </div>
          <div className="panel-lite">
            <div className="settings-summary-header">
              <div>
                <h4 className="section-heading">Customer product and offering</h4>
                <p>
                  This is the customer's market-facing product. Amplifi package codes stay behind the scenes and are not
                  the product being sold or referred.
                </p>
              </div>
              <StatusBadge label={productSelectionReady ? "Product selected" : "Required"} tone={productSelectionReady ? "success" : "warning"} />
            </div>
            {hasProductCatalogue ? (
              <div className="grid-2">
                <label htmlFor="programme-product-line-select">
                  Customer product line
                  <select
                    aria-describedby="programme-product-line-help"
                    id="programme-product-line-select"
                    onChange={(event) =>
                      setDraft({
                        ...draft,
                        customerProductLineId: event.target.value,
                        customerProductOfferingId: "",
                      })
                    }
                    value={draft.customerProductLineId}
                  >
                    <option value="">Choose the customer product line</option>
                    {customerProductLines.map((line) => (
                      <option key={line.customerProductLineId} value={line.customerProductLineId}>
                        {productLineLabel(line)}
                      </option>
                    ))}
                  </select>
                </label>
                <label htmlFor="programme-product-offering-select">
                  Customer product offering
                  <select
                    aria-describedby="programme-product-offering-help"
                    disabled={!selectedProductLine || availableProductOfferings.length === 0}
                    id="programme-product-offering-select"
                    onChange={(event) => setDraft({ ...draft, customerProductOfferingId: event.target.value })}
                    value={draft.customerProductOfferingId}
                  >
                    <option value="">
                      {selectedProductLine ? "Choose the customer offering" : "Choose product line first"}
                    </option>
                    {availableProductOfferings.map((offering) => (
                      <option key={offering.customerProductOfferingId} value={offering.customerProductOfferingId}>
                        {productOfferingLabel(offering)}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            ) : (
              <div className="empty-panel">
                No customer product catalogue is ready for this account yet. Add a product line and offering in Customer
                settings before saving a programme.
              </div>
            )}
            <div className="configuration-proof-grid compact">
              <div className="configuration-proof-card static" id="programme-product-line-help">
                <span className="configuration-proof-index">1</span>
                <div>
                  <strong>Product line</strong>
                  <p>Examples: Transactional banking, Insurance, Telco, or Automotive services.</p>
                </div>
              </div>
              <div className="configuration-proof-card static" id="programme-product-offering-help">
                <span className="configuration-proof-index">2</span>
                <div>
                  <strong>Offering</strong>
                  <p>Examples: Easy Account, Funeral Plan, Fibre Upgrade, or Vehicle Service Plan.</p>
                </div>
              </div>
            </div>
            {selectedProductLine && !availableProductOfferings.length ? (
              <div className="warning-banner">
                Add an active offering under {selectedProductLine.productLineName} before this programme can be saved.
              </div>
            ) : null}
          </div>
          <div className="grid-2">
            <label>
              Published journey version
              <select
                onChange={(event) => setDraft({ ...draft, customerJourneyVersionId: event.target.value })}
                value={draft.customerJourneyVersionId}
              >
                {journeyVersions.map((version) => (
                  <option key={version.customerJourneyVersionId} value={version.customerJourneyVersionId}>
                    {version.customerJourneyCode} v{version.versionNumber} - {formatDisplay(version.templateCode)}
                  </option>
                ))}
              </select>
            </label>
            <div className="readonly-card">
              <strong>Amplifi package</strong>
              <p>{formatDisplay(draft.subProductCode || subProductCodes[0] || "RMCA_BUNDLE")}</p>
              <span className="table-subtext">Internal service packaging, not the customer's product.</span>
            </div>
          </div>
          <label>
            Programme name
            <input onChange={(event) => setDraft({ ...draft, programmeName: event.target.value })} value={draft.programmeName} />
          </label>
          <label>
            What is this programme for?
            <textarea
              onChange={(event) => setDraft({ ...draft, programmeDescription: event.target.value })}
              value={draft.programmeDescription}
            />
          </label>
          <div className="grid-2">
            <label>
              Campaign purpose
              <input onChange={(event) => setDraft({ ...draft, campaignPurpose: event.target.value })} value={draft.campaignPurpose} />
            </label>
            <label>
              Attribution window
              <input
                onChange={(event) => setDraft({ ...draft, defaultAttributionWindowDays: event.target.value })}
                type="number"
                value={draft.defaultAttributionWindowDays}
              />
            </label>
          </div>
          <div className="grid-2">
            <label>
              Incentive reference
              <input
                onChange={(event) => setDraft({ ...draft, incentiveRef: event.target.value })}
                placeholder="Optional approved reward or incentive code"
                value={draft.incentiveRef}
              />
            </label>
            <label>
              Engagement reference
              <input
                onChange={(event) => setDraft({ ...draft, engagementRef: event.target.value })}
                placeholder="Optional mission, badge, or leaderboard code"
                value={draft.engagementRef}
              />
            </label>
          </div>
          <div className="action-row">
            <button className="button primary" disabled={!canSave || saveMutation.isPending} type="submit">
              {saveMutation.isPending ? "Saving" : "Save programme draft"}
            </button>
            <button
              className="button secondary"
              disabled={!canValidate || validateMutation.isPending}
              onClick={() => validateMutation.mutate()}
              type="button"
            >
              {validateMutation.isPending ? "Validating" : "Validate programme"}
            </button>
          </div>
          {!productSelectionReady ? (
            <div className="warning-banner">
              Choose a customer product line and offering before saving this programme.
            </div>
          ) : null}
        </form>

        <div className="panel-lite integrations-step-card">
          <div className="settings-summary-header">
            <div>
              <h3 className="section-heading">2. Review and publish</h3>
              <p>Publishing creates an immutable programme version. It still does not activate a campaign.</p>
            </div>
            <StatusBadge label={publishAllowed ? "Publish allowed" : "Validate first"} tone={publishAllowed ? "success" : "warning"} />
          </div>
          {latestValidation ? <ProgrammeValidationSummary validationResponse={latestValidation} /> : null}
          <label>
            Review note
            <textarea onChange={(event) => setDraft({ ...draft, reviewReason: event.target.value })} value={draft.reviewReason} />
          </label>
          <label>
            Publish note
            <textarea onChange={(event) => setDraft({ ...draft, publishReason: event.target.value })} value={draft.publishReason} />
          </label>
          <div className="action-row">
            <button
              className="button secondary"
              disabled={!canValidate || submitReviewMutation.isPending}
              onClick={() => submitReviewMutation.mutate()}
              type="button"
            >
              {submitReviewMutation.isPending ? "Submitting" : "Submit for review"}
            </button>
            <button
              className="button secondary"
              disabled={!canValidate || approveMutation.isPending}
              onClick={() => approveMutation.mutate()}
              type="button"
            >
              {approveMutation.isPending ? "Approving" : "Approve programme"}
            </button>
            <button
              className="button primary"
              disabled={!canPublish || publishMutation.isPending}
              onClick={() => publishMutation.mutate()}
              type="button"
            >
              {publishMutation.isPending ? "Publishing" : "Publish programme version"}
            </button>
          </div>
          {latestLifecycle ? (
            <div className="success-banner">
              <strong>{formatDisplay(latestLifecycle.commandStatus)}.</strong>{" "}
              {latestLifecycle.plainLanguageSummary || "Programme lifecycle command recorded."}
            </div>
          ) : null}
        </div>

        <div className="grid-2">
          <div className="panel-lite integrations-step-card">
            <div className="settings-summary-header">
              <div>
                <h3 className="section-heading">Published programme versions</h3>
                <p>Campaigns bind to one of these packages.</p>
              </div>
              <StatusBadge label={`${publishedProgrammes.length} versions`} tone="info" />
            </div>
            <div className="route-list">
              {publishedProgrammes.map((programme) => (
                <div className="wizard-status-card" key={programme.programmeVersionId}>
                  <div>
                    <strong>{programme.programmeName}</strong>
                    <p>
                      {programmeProductBindingLabel(programme.customerProductBinding)} - version {programme.versionNumber}
                    </p>
                    <span className="table-subtext">
                      Journey: {journeyVersionLabel(programme.customerJourneyVersionId)}
                      {programme.publishedAt ? ` - published ${programme.publishedAt}` : ""}
                    </span>
                  </div>
                  <StatusBadge label={formatDisplay(programme.versionStatus)} tone={statusTone(programme.versionStatus)} />
                </div>
              ))}
              {!publishedProgrammes.length && !programmesQuery.isLoading ? (
                <div className="empty-panel">No published programme versions yet.</div>
              ) : null}
            </div>
          </div>

          <div className="panel-lite integrations-step-card">
            <div className="settings-summary-header">
              <div>
                <h3 className="section-heading">Programme performance</h3>
                <p>Read-only reporting separates product, programme, campaign, and approved campaign changes.</p>
              </div>
              <StatusBadge label="Read-only analytics" tone="success" />
            </div>
            {reportingDimensions ? (
              <div className="configuration-proof-grid compact">
                <div className="configuration-proof-card static">
                  <span className="configuration-proof-index">P</span>
                  <div>
                    <strong>Products measured</strong>
                    <p>
                      {reportingDimensions.productLineCount ?? 0} product lines and{" "}
                      {reportingDimensions.productOfferingCount ?? 0} offerings.
                    </p>
                  </div>
                </div>
                <div className="configuration-proof-card static">
                  <span className="configuration-proof-index">C</span>
                  <div>
                    <strong>Campaigns measured</strong>
                    <p>{reportingDimensions.runtimeCampaignCount ?? 0} campaigns with runtime referral evidence.</p>
                  </div>
                </div>
                <div className="configuration-proof-card static">
                  <span className="configuration-proof-index">O</span>
                  <div>
                    <strong>Campaign changes measured</strong>
                    <p>
                      {reportingDimensions.approvedCampaignOverrideReferralCount ?? 0} referrals used approved campaign-specific changes.
                    </p>
                  </div>
                </div>
              </div>
            ) : null}
            <div className="route-list">
              {analyticsVersions.slice(0, 5).map((version) => (
                <div className="wizard-status-card" key={version.programmeVersionId}>
                  <div>
                    <strong>{version.programmeName}</strong>
                    <p>
                      {version.referralCount} referrals - {Math.round(version.attributionRate * 100)}% attributed -{" "}
                      {Math.round(version.completionRate * 100)}% completed
                    </p>
                  </div>
                  <StatusBadge label={formatDisplay(version.performanceSignal)} tone={statusTone(version.performanceSignal)} />
                </div>
              ))}
              {!analyticsVersions.length && !analyticsQuery.isLoading ? (
                <div className="empty-panel">No programme analytics yet. Publish a programme and bind campaigns first.</div>
              ) : null}
            </div>
          </div>
        </div>

        <details className="panel-lite integrations-step-card">
          <summary>Show programme diagnostics</summary>
          <div className="route-list">
            <div className="empty-panel">
              Safe workspace: no campaign activation, provider dispatch, credential creation, auth mutation, billing,
              payout, settlement, or money movement happens on this page.
            </div>
            {(programmesQuery.data?.guardrails || []).map((guardrail) => (
              <span className="tag-pill" key={guardrail}>
                {guardrail}
              </span>
            ))}
          </div>
        </details>

        <div className="action-row integrations-handoff-row">
          <Link className="button secondary" to={selectedCustomerPath}>
            Customer home
          </Link>
          <Link className="button primary" to={`${selectedCustomerPath}/campaigns`}>
            Continue to Campaigns
          </Link>
        </div>
      </div>
    </section>
  );
}

function ProgrammeValidationSummary({
  validationResponse,
}: {
  validationResponse: ReferralSaasProgrammeValidationResponse;
}) {
  const validation = validationResponse.validation;
  return (
    <div className="integrations-stage-card success">
      <div>
        <strong>{formatDisplay(validation.validationStatus)}</strong>
        <p>{validation.plainLanguageSummary || "Programme validation completed."}</p>
        <span className="table-subtext">
          {validation.blockers.length} blockers, {validation.warnings.length} warnings.
        </span>
      </div>
      <StatusBadge label={validation.publishAllowed ? "Ready to publish" : "Needs work"} tone={validation.publishAllowed ? "success" : "warning"} />
    </div>
  );
}

function CustomerReportsPage({
  customerName,
  externalTenantRef,
  selectedAccount,
  selectedCustomerPath,
}: {
  customerName: string;
  externalTenantRef: string;
  selectedAccount?: AccountRegistryItem;
  selectedCustomerPath: string;
}) {
  const { refreshKey } = useRefreshContext();
  const [reportType, setReportType] = useState<ReferralSaasReportType>("campaign_performance");
  const [campaignCode, setCampaignCode] = useState("");
  const [scheduleCadence, setScheduleCadence] = useState<ReferralSaasReportDeliveryCadence>("weekly");
  const [scheduleTimezone, setScheduleTimezone] = useState("Africa/Johannesburg");
  const [scheduleFormat, setScheduleFormat] = useState<ReferralSaasExportFormat>("csv");
  const [scheduleRetentionDays, setScheduleRetentionDays] = useState(7);
  const [scheduleRecipientRef, setScheduleRecipientRef] = useState("");
  const accountScope = {
    refType: "external_tenant_ref" as const,
    externalRef: externalTenantRef,
    context: "setup" as const,
  };
  const {
    data: campaignListResponse,
    error: campaignListError,
    isLoading: isCampaignListLoading,
  } = useReferralSaasAccountCampaignList(
    selectedAccount?.accountId || "",
    externalTenantRef,
    Boolean(selectedAccount && externalTenantRef),
    refreshKey,
  );
  const campaigns = campaignListResponse?.campaigns || [];
  const selectedCampaign = campaigns.find((campaign) => campaign.campaignCode === campaignCode);
  const filters = campaignCode ? { campaign_code: campaignCode } : undefined;
  const reportQuery = useQuery({
    queryKey: [
      "referral-saas",
      "customer-report",
      selectedAccount?.accountId || "",
      externalTenantRef,
      reportType,
      campaignCode,
      refreshKey,
    ],
    queryFn: () =>
      getReferralSaasAccountReport({
        accountRef: selectedAccount?.accountId || "",
        accountScope,
        reportType,
        filters,
      }),
    enabled: Boolean(selectedAccount?.accountId && externalTenantRef),
    retry: false,
  });
  const scheduleListQuery = useQuery({
    queryKey: [
      "referral-saas",
      "customer-report-delivery-schedules",
      selectedAccount?.accountId || "",
      externalTenantRef,
      reportType,
      refreshKey,
    ],
    queryFn: () =>
      listReferralSaasAccountReportDeliverySchedules({
        accountRef: selectedAccount?.accountId || "",
        accountScope,
        reportType,
      }),
    enabled: Boolean(selectedAccount?.accountId && externalTenantRef),
    retry: false,
  });
  const previewMutation = useMutation({
    mutationFn: (format: ReferralSaasExportFormat) =>
      previewReferralSaasAccountReportExport({
        accountRef: selectedAccount?.accountId || "",
        accountScope,
        reportType,
        format,
        redactionProfile: "tenant_safe",
        filters,
        rowLimit: 100,
      }),
  });
  const prepareDownloadMutation = useMutation({
    mutationFn: async (format: ReferralSaasExportFormat) => {
      const requestResponse = await createReferralSaasAccountReportExportRequest({
        accountRef: selectedAccount?.accountId || "",
        accountScope,
        reportType,
        format,
        redactionProfile: "tenant_safe",
        filters,
        rowLimit: 100,
        correlationId: safeIdempotencyKey(
          "customer-report-export-request",
          selectedAccount?.accountId || "",
          reportType,
          campaignCode || "all-campaigns",
          format,
        ),
        idempotencyKey: safeIdempotencyKey(
          "customer-report-export-request",
          selectedAccount?.accountId || "",
          reportType,
          campaignCode || "all-campaigns",
          format,
        ),
      });
      const exportPayload = asRecord(requestResponse.reportExport);
      const requestRecord = asRecord(getNestedValue(exportPayload, ["exportRequest"], {}));
      const exportRequestId = textValue(getNestedValue(requestRecord, ["exportRequestId"], ""));
      if (!exportRequestId) {
        throw new Error("The export request was accepted, but no export request ID was returned.");
      }
      return createReferralSaasAccountReportExportFile({
        accountRef: selectedAccount?.accountId || "",
        accountScope,
        reportType,
        exportRequestId,
        correlationId: safeIdempotencyKey(
          "customer-report-export-file",
          selectedAccount?.accountId || "",
          reportType,
          exportRequestId,
        ),
        idempotencyKey: safeIdempotencyKey(
          "customer-report-export-file",
          selectedAccount?.accountId || "",
          reportType,
          exportRequestId,
        ),
      });
    },
  });
  const report = asRecord(reportQuery.data?.report);
  const metrics = asArray(getNestedValue(report, ["metrics"], []));
  const rows = asArray(getNestedValue(report, ["rows"], metrics));
  const warnings = asArray(getNestedValue(report, ["warnings"], []));
  const preview = asRecord(previewMutation.data?.export_preview);
  const previewRows = asArray(getNestedValue(preview, ["sample_rows"], getNestedValue(preview, ["rows"], [])));
  const preparedExportPayload = asRecord(prepareDownloadMutation.data?.reportExport);
  const preparedExportRequest = asRecord(getNestedValue(preparedExportPayload, ["exportRequest"], {}));
  const preparedExportFile = asRecord(getNestedValue(preparedExportPayload, ["file"], {}));
  const preparedExportRequestId = textValue(getNestedValue(preparedExportRequest, ["exportRequestId"], ""));
  const downloadMutation = useMutation({
    mutationFn: async () => {
      if (!preparedExportRequestId) {
        throw new Error("Prepare the export file before downloading it.");
      }
      const response = await downloadReferralSaasAccountReportExportFile({
        accountRef: selectedAccount?.accountId || "",
        accountScope,
        exportRequestId: preparedExportRequestId,
        correlationId: safeIdempotencyKey(
          "customer-report-export-download",
          selectedAccount?.accountId || "",
          preparedExportRequestId,
        ),
      });
      const exportPayload = asRecord(response.reportExport);
      const file = asRecord(getNestedValue(exportPayload, ["file"], {}));
      downloadCustomerReportFile({
        content: textValue(getNestedValue(file, ["content"], "")),
        contentType: textValue(getNestedValue(file, ["contentType"], "text/plain"), "text/plain"),
        fileName: textValue(
          getNestedValue(file, ["fileName"], `${customerName}-${reportType}.${textValue(getNestedValue(preparedExportRequest, ["format"], "csv"), "csv")}`),
          `${customerName}-${reportType}.csv`,
        ),
      });
      return response;
    },
  });
  const deleteExportMutation = useMutation({
    mutationFn: async () => {
      if (!preparedExportRequestId) {
        throw new Error("Prepare the export file before deleting it.");
      }
      return deleteReferralSaasAccountReportExportFile({
        accountRef: selectedAccount?.accountId || "",
        accountScope,
        exportRequestId: preparedExportRequestId,
        correlationId: safeIdempotencyKey(
          "customer-report-export-delete",
          selectedAccount?.accountId || "",
          preparedExportRequestId,
        ),
        idempotencyKey: safeIdempotencyKey(
          "customer-report-export-delete",
          selectedAccount?.accountId || "",
          preparedExportRequestId,
        ),
        reasonCode: "CUSTOMER_PROFILE_REPORT_EXPORT_DELETE",
      });
    },
    onSuccess: () => {
      prepareDownloadMutation.reset();
      downloadMutation.reset();
    },
  });
  const scheduleMutation = useMutation({
    mutationFn: () => {
      const recipientRef = scheduleRecipientRef.trim();
      const key = safeIdempotencyKey(
        "customer-report-delivery-schedule",
        selectedAccount?.accountId || "",
        reportType,
        campaignCode || "all-campaigns",
        scheduleCadence,
        scheduleTimezone,
        scheduleFormat,
        String(scheduleRetentionDays),
        recipientRef || "no-recipient",
      );
      return createReferralSaasAccountReportDeliverySchedule({
        accountRef: selectedAccount?.accountId || "",
        accountScope,
        reportType,
        cadence: scheduleCadence,
        timezone: scheduleTimezone,
        format: scheduleFormat,
        redactionProfile: "tenant_safe",
        recipientContactRefs: recipientRef ? [recipientRef] : [],
        retentionDays: scheduleRetentionDays,
        campaignRef: campaignCode || undefined,
        scheduleStatus: recipientRef ? "ready" : "blocked",
        reasonCode: "CUSTOMER_PROFILE_REPORT_DELIVERY_SCHEDULE_UI",
        correlationId: key,
        idempotencyKey: key,
      });
    },
    onSuccess: () => {
      void scheduleListQuery.refetch();
    },
  });
  const updateScheduleMutation = useMutation({
    mutationFn: ({
      scheduleId,
      scheduleStatus,
    }: {
      scheduleId: string;
      scheduleStatus: "ready" | "paused" | "cancelled";
    }) => {
      const key = safeIdempotencyKey(
        "customer-report-delivery-schedule-update",
        selectedAccount?.accountId || "",
        scheduleId,
        scheduleStatus,
      );
      return updateReferralSaasAccountReportDeliverySchedule({
        accountRef: selectedAccount?.accountId || "",
        accountScope,
        scheduleId,
        scheduleStatus,
        reasonCode: `CUSTOMER_PROFILE_REPORT_DELIVERY_SCHEDULE_${scheduleStatus.toUpperCase()}`,
        correlationId: key,
        idempotencyKey: key,
      });
    },
    onSuccess: () => {
      void scheduleListQuery.refetch();
    },
  });
  const readinessMutation = useMutation({
    mutationFn: (scheduleId: string) =>
      getReferralSaasAccountReportDeliveryScheduleReadiness({
        accountRef: selectedAccount?.accountId || "",
        accountScope,
        scheduleId,
      }),
  });
  const exportFileName = textValue(getNestedValue(preparedExportFile, ["fileName"], ""));
  const exportFileType = textValue(getNestedValue(preparedExportFile, ["contentType"], ""));
  const exportFileSize = textValue(getNestedValue(preparedExportFile, ["byteSize"], ""));
  const exportRowCount = textValue(getNestedValue(preparedExportRequest, ["rowCount"], ""));
  const exportDownloadStatus = textValue(getNestedValue(preparedExportRequest, ["downloadStatus"], ""));
  const deletedExportPayload = asRecord(deleteExportMutation.data?.reportExport);
  const deletedExportRequest = asRecord(getNestedValue(deletedExportPayload, ["exportRequest"], {}));
  const deletedExportRequestId = textValue(getNestedValue(deletedExportRequest, ["exportRequestId"], ""));
  const activeReport = customerReportOptions.find((option) => option.value === reportType) || customerReportOptions[0];
  const scheduleRows = asArray(scheduleListQuery.data?.deliverySchedules).map((entry) => {
    const record = asRecord(entry);
    const schedule = asRecord(getNestedValue(record, ["deliverySchedule"], record));
    const readiness = asRecord(getNestedValue(record, ["readiness"], {}));
    return {
      record,
      schedule,
      readiness,
      scheduleId: textValue(getNestedValue(schedule, ["scheduleId"], "")),
      status: textValue(getNestedValue(schedule, ["scheduleStatus"], "draft")),
      cadence: textValue(getNestedValue(schedule, ["cadence"], "weekly")),
      timezone: textValue(getNestedValue(schedule, ["timezone"], "")),
      format: textValue(getNestedValue(schedule, ["format"], "csv")),
      recipients: textArray(getNestedValue(schedule, ["recipientContactRefs"], [])),
      retentionDays: textValue(getNestedValue(schedule, ["retentionDays"], "7")),
      campaignRef: textValue(getNestedValue(schedule, ["campaignRef"], "")),
      readinessStatus: textValue(getNestedValue(readiness, ["status"], getNestedValue(schedule, ["scheduleStatus"], "draft"))),
      blockedReasons: textArray(getNestedValue(readiness, ["blockedReasons"], getNestedValue(schedule, ["blockedReasons"], []))),
      warnings: textArray(getNestedValue(readiness, ["warnings"], getNestedValue(schedule, ["warnings"], []))),
    };
  });
  const latestSchedule = asRecord(scheduleMutation.data?.reportDeliverySchedule);
  const latestScheduleRecord = asRecord(getNestedValue(latestSchedule, ["deliverySchedule"], {}));
  const updatedSchedule = asRecord(updateScheduleMutation.data?.reportDeliverySchedule);
  const updatedScheduleRecord = asRecord(getNestedValue(updatedSchedule, ["deliverySchedule"], {}));
  const readinessResult = asRecord(readinessMutation.data?.reportDeliveryScheduleReadiness);
  const readinessSchedule = asRecord(getNestedValue(readinessResult, ["deliverySchedule"], {}));
  const readinessDetails = asRecord(getNestedValue(readinessResult, ["readiness"], readinessResult));
  const readinessStatus = textValue(getNestedValue(readinessDetails, ["status"], ""));
  const resetExportState = () => {
    previewMutation.reset();
    prepareDownloadMutation.reset();
    downloadMutation.reset();
    deleteExportMutation.reset();
    scheduleMutation.reset();
    updateScheduleMutation.reset();
    readinessMutation.reset();
  };

  return (
    <section className="panel customer-module-page">
      <div className="panel-header">
        <div>
          <div className="page-kicker">Referral SaaS &gt; {customerName} &gt; Reports</div>
          <h2 className="panel-title">Reports</h2>
          <div className="panel-subtitle">
            View tenant-safe campaign and referral performance for this customer without entering tenant code.
          </div>
        </div>
        <StatusBadge label="Customer scoped" tone="success" />
      </div>
      <div className="panel-body route-list">
        <div className="wizard-status-card">
          <div>
            <strong>Selected customer</strong>
            <p>
              {selectedAccount?.accountCode || "No account code"} - {externalTenantRef || "No customer reference"}
            </p>
          </div>
          <StatusBadge label="No tenant code entry" tone="success" />
        </div>

        {campaignListError ? <ErrorPanel error={campaignListError} /> : null}
        {reportQuery.error ? <ErrorPanel error={reportQuery.error} /> : null}
        {previewMutation.error ? <ErrorPanel error={previewMutation.error} /> : null}
        {prepareDownloadMutation.error ? <ErrorPanel error={prepareDownloadMutation.error} /> : null}
        {downloadMutation.error ? <ErrorPanel error={downloadMutation.error} /> : null}
        {deleteExportMutation.error ? <ErrorPanel error={deleteExportMutation.error} /> : null}
        {scheduleListQuery.error ? <ErrorPanel error={scheduleListQuery.error} /> : null}
        {scheduleMutation.error ? <ErrorPanel error={scheduleMutation.error} /> : null}
        {updateScheduleMutation.error ? <ErrorPanel error={updateScheduleMutation.error} /> : null}
        {readinessMutation.error ? <ErrorPanel error={readinessMutation.error} /> : null}

        <div className="grid-2">
          <div className="panel-lite">
            <h3 className="section-heading">1. Choose report</h3>
            <div className="route-list">
              {customerReportOptions.map((option) => (
                <button
                  className={`route-card ${option.value === reportType ? "selected" : ""}`}
                  key={option.value}
                  onClick={() => {
                    setReportType(option.value);
                    resetExportState();
                  }}
                  type="button"
                >
                  <span>
                    <strong>{option.label}</strong>
                    <span>{option.copy}</span>
                  </span>
                  {option.value === reportType ? <StatusBadge label="Selected" tone="success" /> : null}
                </button>
              ))}
            </div>
          </div>
          <div className="panel-lite">
            <h3 className="section-heading">2. Scope the view</h3>
            <p className="muted">
              Reports are already locked to {customerName}. Optionally narrow the view to one customer campaign.
            </p>
            {isCampaignListLoading ? <LoadingState label="Loading campaigns" /> : null}
            <label>
              Campaign filter
              <select
                onChange={(event) => {
                  setCampaignCode(event.target.value);
                  resetExportState();
                }}
                value={campaignCode}
              >
                <option value="">All campaigns for this customer</option>
                {campaigns.map((campaign) => (
                  <option key={campaign.campaignCode} value={campaign.campaignCode}>
                    {campaign.name || campaign.campaignCode}
                  </option>
                ))}
              </select>
            </label>
            <div className="wizard-status-card">
              <div>
                <strong>{activeReport.label}</strong>
                <p>{selectedCampaign ? selectedCampaign.name || selectedCampaign.campaignCode : "All customer campaigns"}</p>
              </div>
              <StatusBadge label="Read-only" tone="success" />
            </div>
          </div>
        </div>

        <div className="kpi-grid">
          <KpiCard
            footnote="Returned by the selected report"
            icon={BarChart3}
            label="Report rows"
            value={String(rows.length)}
          />
          <KpiCard
            footnote="Source or coverage caveats"
            icon={AlertCircle}
            label="Warnings"
            value={String(warnings.length)}
          />
          <KpiCard
            footnote={exportFileName ? "Tenant-safe file prepared for this customer" : "Preview first, then prepare a file"}
            icon={Download}
            label="Export mode"
            value={exportFileName ? "Download ready" : "Preview"}
          />
        </div>

        <section className="panel-lite">
          <div className="panel-header compact">
            <div>
              <h3 className="section-heading">3. Review results</h3>
              <div className="panel-subtitle">Tenant-safe rows from the selected customer report.</div>
            </div>
            <div className="button-row">
              <button
                className="button secondary"
                disabled={previewMutation.isPending || !selectedAccount}
                onClick={() => previewMutation.mutate("json")}
                type="button"
              >
                <FileJson size={16} /> Preview JSON
              </button>
              <button
                className="button secondary"
                disabled={previewMutation.isPending || !selectedAccount}
                onClick={() => previewMutation.mutate("csv")}
                type="button"
              >
                <Download size={16} /> Preview CSV
              </button>
            </div>
          </div>
          {reportQuery.isLoading ? <LoadingState label="Loading customer report" /> : null}
          <DataTable
            rows={rows}
            emptyText="No report rows returned for this customer yet."
            columns={[
              {
                key: "metric",
                header: "Metric",
                render: (row) =>
                  formatDisplay(getValue(row, ["metric_name", "metricName", "name", "label"], "Metric")),
              },
              {
                key: "campaign",
                header: "Campaign",
                render: (row) =>
                  formatDisplay(getValue(row, ["campaign_code", "campaignCode", "campaign_ref", "campaignRef"], "All")),
              },
              {
                key: "value",
                header: "Value",
                render: (row) => formatDisplay(getValue(row, ["value", "count", "metric_value", "metricValue"], "-")),
              },
              {
                key: "status",
                header: "Status",
                render: (row) => {
                  const label = formatDisplay(getValue(row, ["status", "safe_status", "safeStatus"], "Available"));
                  return <StatusBadge label={label} tone={statusTone(label)} />;
                },
              },
            ]}
          />
        </section>

        {previewMutation.data ? (
          <section className="panel-lite">
            <h3 className="section-heading">Export preview</h3>
            <p className="muted">Preview only. No export file, storage row, delivery job, or email was created.</p>
            <DataTable
              rows={previewRows}
              emptyText="The preview returned no sample rows."
              columns={[
                {
                  key: "preview",
                  header: "Sample row",
                  render: (row) => <code>{JSON.stringify(row)}</code>,
                },
              ]}
            />
          </section>
        ) : null}

        <section className="panel-lite">
          <div className="panel-header compact">
            <div>
              <h3 className="section-heading">4. Prepare download</h3>
              <div className="panel-subtitle">
                Create a tenant-safe export file for this selected customer only. No email, scheduled delivery,
                external download URL, billing, campaign activation, or money movement is triggered.
              </div>
            </div>
            <StatusBadge label={exportFileName ? "Download ready" : "No file yet"} tone={exportFileName ? "success" : "warning"} />
          </div>
          <div className="wizard-status-card">
            <div>
              <strong>{exportFileName || "Prepare a file when the report looks right"}</strong>
              <p>
                {exportFileName
                  ? `${formatDisplay(exportFileType)} - ${exportFileSize || "0"} bytes - ${exportRowCount || rows.length} rows - ${formatDisplay(exportDownloadStatus || "available")}`
                  : "Use this after reviewing the report rows or export preview. The backend records the export request and file metadata for audit."}
              </p>
            </div>
            <div className="button-row">
              <button
                className="button secondary"
                disabled={prepareDownloadMutation.isPending || !selectedAccount}
                onClick={() => prepareDownloadMutation.mutate("csv")}
                type="button"
              >
                <Download size={16} /> {prepareDownloadMutation.isPending ? "Preparing" : "Prepare CSV"}
              </button>
              <button
                className="button"
                disabled={downloadMutation.isPending || !preparedExportRequestId}
                onClick={() => downloadMutation.mutate()}
                type="button"
              >
                <Download size={16} /> {downloadMutation.isPending ? "Downloading" : "Download file"}
              </button>
              <button
                className="button secondary"
                disabled={deleteExportMutation.isPending || !preparedExportRequestId}
                onClick={() => deleteExportMutation.mutate()}
                type="button"
              >
                {deleteExportMutation.isPending ? "Deleting" : "Delete prepared file"}
              </button>
            </div>
          </div>
          {downloadMutation.data ? (
            <div className="success-panel">
              <strong>Download started.</strong> The file content came from the selected-customer export route.
              No signed URL, scheduled delivery, email, credential, billing, campaign activation, or money movement was created.
            </div>
          ) : null}
          {deleteExportMutation.data ? (
            <div className="success-panel">
              <strong>Prepared export deleted.</strong>{" "}
              {deletedExportRequestId || "The export"} keeps its audit row, but file content and signed download metadata were removed.
              Prepare a new file if this customer needs another download.
            </div>
          ) : null}
        </section>

        <section className="panel-lite">
          <div className="panel-header compact">
            <div>
              <h3 className="section-heading">5. Schedule delivery intent</h3>
              <div className="panel-subtitle">
                Record when this customer report should be delivered later. This does not send a report today.
              </div>
            </div>
            <StatusBadge label="Intent only" tone="info" />
          </div>
          <div className="grid-2">
            <div className="route-list">
              <label>
                Cadence
                <select
                  onChange={(event) => setScheduleCadence(event.target.value as ReferralSaasReportDeliveryCadence)}
                  value={scheduleCadence}
                >
                  <option value="weekly">Weekly</option>
                  <option value="daily">Daily</option>
                  <option value="monthly">Monthly</option>
                </select>
              </label>
              <label>
                Timezone
                <input
                  onChange={(event) => setScheduleTimezone(event.target.value)}
                  placeholder="Example: Africa/Johannesburg"
                  value={scheduleTimezone}
                />
              </label>
              <label>
                Format
                <select
                  onChange={(event) => setScheduleFormat(event.target.value as ReferralSaasExportFormat)}
                  value={scheduleFormat}
                >
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                </select>
              </label>
              <label>
                Retention days
                <input
                  max={7}
                  min={1}
                  onChange={(event) => setScheduleRetentionDays(Number(event.target.value) || 7)}
                  type="number"
                  value={scheduleRetentionDays}
                />
              </label>
              <label>
                Recipient contact reference
                <input
                  onChange={(event) => setScheduleRecipientRef(event.target.value)}
                  placeholder="Example: contact-owner"
                  value={scheduleRecipientRef}
                />
              </label>
              <button
                className="button primary"
                disabled={scheduleMutation.isPending || !selectedAccount?.accountId || !scheduleTimezone.trim()}
                onClick={() => scheduleMutation.mutate()}
                type="button"
              >
                <Download size={16} /> {scheduleMutation.isPending ? "Saving schedule" : "Save schedule intent"}
              </button>
            </div>
            <div className="wizard-status-card vertical">
              <div>
                <strong>Delivery boundary</strong>
                <p>
                  Schedule intent is customer-scoped and audit-friendly. It does not send email, call a provider,
                  dispatch webhooks, create credentials, activate a campaign, bill, or move money.
                </p>
              </div>
              <StatusBadge label={campaignCode ? `Campaign: ${campaignCode}` : "All campaigns"} tone="info" />
            </div>
          </div>

          {scheduleMutation.data ? (
            <div className="success-panel">
              <strong>Schedule intent saved.</strong>{" "}
              {textValue(getNestedValue(latestScheduleRecord, ["scheduleId"], "The schedule"))} is{" "}
              {formatDisplay(getNestedValue(latestScheduleRecord, ["scheduleStatus"], "recorded"))}. No live delivery
              was executed.
            </div>
          ) : null}
          {updateScheduleMutation.data ? (
            <div className="success-panel">
              <strong>Schedule updated.</strong>{" "}
              {textValue(getNestedValue(updatedScheduleRecord, ["scheduleId"], "The schedule"))} is now{" "}
              {formatDisplay(getNestedValue(updatedScheduleRecord, ["scheduleStatus"], "updated"))}. No live delivery
              was executed.
            </div>
          ) : null}
          {readinessMutation.data ? (
            <div className="wizard-status-card">
              <div>
                <strong>Readiness checked.</strong>
                <p>
                  {textValue(getNestedValue(readinessSchedule, ["scheduleId"], "Selected schedule"))} is{" "}
                  {formatDisplay(readinessStatus || "not ready")}.{" "}
                  {formatList(textArray(getNestedValue(readinessDetails, ["blockedReasons"], [])))}{" "}
                  blockers.
                </p>
              </div>
              <StatusBadge label={formatDisplay(readinessStatus || "Checked")} tone={statusTone(readinessStatus)} />
            </div>
          ) : null}

          {scheduleListQuery.isLoading ? <LoadingState label="Loading delivery schedules" /> : null}
          <DataTable
            rows={scheduleRows}
            emptyText="No scheduled delivery intent has been recorded for this customer report yet."
            columns={[
              {
                key: "schedule",
                header: "Schedule",
                render: (row) => (
                  <div>
                    <strong>{formatDisplay(getValue(row, ["cadence"], "Weekly"))}</strong>
                    <div className="muted">
                      {formatDisplay(getValue(row, ["format"], "CSV"))} - {getValue(row, ["timezone"], "No timezone")}
                    </div>
                  </div>
                ),
              },
              {
                key: "scope",
                header: "Scope",
                render: (row) => (
                  <div>
                    <strong>{getValue(row, ["campaignRef"], "") || "All campaigns"}</strong>
                    <div className="muted">
                      {textArray(row.recipients).join(", ") || "No recipient contact reference"}
                    </div>
                  </div>
                ),
              },
              {
                key: "status",
                header: "Status",
                render: (row) => {
                  const status = formatDisplay(getValue(row, ["status"], "Draft"));
                  const warningCount = textArray(getNestedValue(row, ["warnings"], [])).length;
                  const blockedCount = textArray(getNestedValue(row, ["blockedReasons"], [])).length;
                  return (
                    <div>
                      <StatusBadge label={status} tone={statusTone(status)} />
                      <div className="muted">
                        {blockedCount} blockers, {warningCount} warnings
                      </div>
                    </div>
                  );
                },
              },
              {
                key: "actions",
                header: "Actions",
                render: (row) => {
                  const scheduleId = textValue(getValue(row, ["scheduleId"], ""));
                  const status = textValue(getValue(row, ["status"], ""));
                  const isPaused = status.toUpperCase() === "PAUSED";
                  const isCancelled = status.toUpperCase() === "CANCELLED";
                  return (
                    <div className="button-row">
                      <button
                        className="button secondary"
                        disabled={!scheduleId || readinessMutation.isPending}
                        onClick={() => readinessMutation.mutate(scheduleId)}
                        type="button"
                      >
                        Check readiness
                      </button>
                      <button
                        className="button secondary"
                        disabled={!scheduleId || updateScheduleMutation.isPending || isCancelled}
                        onClick={() =>
                          updateScheduleMutation.mutate({
                            scheduleId,
                            scheduleStatus: isPaused ? "ready" : "paused",
                          })
                        }
                        type="button"
                      >
                        {isPaused ? "Resume" : "Pause"}
                      </button>
                      <button
                        className="button secondary"
                        disabled={!scheduleId || updateScheduleMutation.isPending || isCancelled}
                        onClick={() =>
                          updateScheduleMutation.mutate({
                            scheduleId,
                            scheduleStatus: "cancelled",
                          })
                        }
                        type="button"
                      >
                        Cancel
                      </button>
                    </div>
                  );
                },
              },
            ]}
          />
        </section>

        <div className="button-row">
          <Link className="button secondary" to={selectedCustomerPath}>
            Back to customer home
          </Link>
          <Link className="button secondary" to={`${selectedCustomerPath}/campaigns`}>
            Open campaigns
          </Link>
        </div>
      </div>
    </section>
  );
}

function CustomerSupportCasesPage({
  cases,
  customerName,
  customerQuery,
  draft,
  error,
  assignmentDraft,
  assignmentResult,
  isLoading,
  isAssignmentSaving,
  isLifecycleSaving,
  isReadinessLoading,
  isSaving,
  lifecycleDraft,
  lifecycleResult,
  onChange,
  onAssignmentChange,
  onAssignmentSubmit,
  onLifecycleChange,
  onReadinessCaseChange,
  onLifecycleSubmit,
  onSubmit,
  readiness,
  readinessCaseRef,
  readinessError,
  result,
  selectedCustomerPath,
}: {
  cases: ReferralSaasSupportCase[];
  customerName: string;
  customerQuery: string;
  draft: SupportCaseDraft;
  error: unknown;
  assignmentDraft: SupportCaseAssignmentDraft | null;
  assignmentResult: ReferralSaasSupportCaseAssignmentResponse | null;
  isLoading: boolean;
  isAssignmentSaving: boolean;
  isLifecycleSaving: boolean;
  isReadinessLoading: boolean;
  isSaving: boolean;
  lifecycleDraft: SupportCaseLifecycleDraft | null;
  lifecycleResult: ReferralSaasSupportCaseLifecycleResponse | null;
  onChange: (values: Partial<SupportCaseDraft>) => void;
  onAssignmentChange: (values: SupportCaseAssignmentDraft | null) => void;
  onAssignmentSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onLifecycleChange: (values: SupportCaseLifecycleDraft | null) => void;
  onReadinessCaseChange: (caseRef: string) => void;
  onLifecycleSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  readiness: ReferralSaasSupportCaseRepairReplayReadinessResponse | null;
  readinessCaseRef: string;
  readinessError: unknown;
  result: ReferralSaasSupportCaseCreateResponse | null;
  selectedCustomerPath: string;
}) {
  const selectedCategory = supportCaseCategoryOptions.find((option) => option.value === draft.category);
  const selectedPriority = supportCasePriorityOptions.find((option) => option.value === draft.priority);
  const selectedLifecycleCase = cases.find((supportCase) => supportCase.caseRef === lifecycleDraft?.caseRef);
  const selectedAssignmentCase = cases.find((supportCase) => supportCase.caseRef === assignmentDraft?.caseRef);
  return (
    <section className="panel customer-module-page">
      <div className="panel-header">
        <div>
          <div className="page-kicker">Referral SaaS &gt; {customerName} &gt; Support</div>
          <h2 className="panel-title">Support cases</h2>
          <div className="panel-subtitle">
            Record safe support cases for this customer and review what is already open.
          </div>
        </div>
        <StatusBadge label="Customer scoped" tone="success" />
      </div>
      <div className="panel-body route-list">
        <div className="wizard-status-card">
          <div>
            <strong>What this page does</strong>
            <p>
              Create and list customer support cases linked to safe evidence, assign an owner,
              record notes, change status, and review safe recovery posture. Repair, replay,
              retry, and operational fixes stay in later governed workflows.
            </p>
          </div>
          <StatusBadge label="Owner + audit" tone="success" />
        </div>
        <form className="account-setup-scope-form" onSubmit={onSubmit}>
          <label className="field">
            <span>What needs help?</span>
            <select
              aria-label="What needs help?"
              className="input"
              onChange={(event) => onChange({ category: event.target.value })}
              value={draft.category}
            >
              {supportCaseCategoryOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {selectedCategory ? <span className="field-help">{selectedCategory.copy}</span> : null}
          </label>
          <label className="field">
            <span>Priority</span>
            <select
              aria-label="Priority"
              className="input"
              onChange={(event) => onChange({ priority: event.target.value })}
              value={draft.priority}
            >
              {supportCasePriorityOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {selectedPriority ? <span className="field-help">{selectedPriority.copy}</span> : null}
          </label>
          <label className="field">
            <span>Case title</span>
            <input
              aria-label="Case title"
              className="input"
              onChange={(event) => onChange({ title: event.target.value })}
              placeholder="Example: Referral code validation failed for branch pilot"
              value={draft.title}
            />
          </label>
          <label className="field">
            <span>What happened?</span>
            <textarea
              aria-label="What happened?"
              className="input textarea"
              onChange={(event) => onChange({ summary: event.target.value })}
              placeholder="Explain the issue in plain language. Do not paste raw customer identifiers, secrets, provider payloads, or banking data."
              value={draft.summary}
            />
          </label>
          <label className="field">
            <span>Safe evidence type</span>
            <select
              aria-label="Safe evidence type"
              className="input"
              onChange={(event) => onChange({ evidenceType: event.target.value, evidenceRef: "" })}
              value={draft.evidenceType}
            >
              {supportCaseEvidenceOptions.map((option) => (
                <option key={option.value || "none"} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Safe evidence reference</span>
            <input
              aria-label="Safe evidence reference"
              className="input"
              disabled={!draft.evidenceType}
              onChange={(event) => onChange({ evidenceRef: event.target.value })}
              placeholder={draft.evidenceType ? "Example: LINK_CHECK_123" : "Choose an evidence type first"}
              value={draft.evidenceRef}
            />
          </label>
          <button
            className="button"
            disabled={isSaving || !draft.title.trim() || !draft.summary.trim()}
            type="submit"
          >
            {isSaving ? "Recording case" : "Record support case"}
          </button>
        </form>
        {error ? <ErrorPanel error={error} /> : null}
        {result ? (
          <div className="success-panel">
            <strong>Support case recorded.</strong>{" "}
            {result.supportCase.supportCase.title} is {formatDisplay(result.supportCase.supportCase.status)}.
            No repair, replay, retry, referral mutation, campaign mutation, invite delivery,
            credential change, billing, or money action was performed.
          </div>
        ) : null}
        {lifecycleResult ? (
          <div className="success-panel">
            <strong>Support case updated.</strong>{" "}
            {lifecycleResult.supportCaseLifecycle.note
              ? `Note added to ${lifecycleResult.supportCaseLifecycle.supportCase.title}.`
              : `${lifecycleResult.supportCaseLifecycle.supportCase.title} moved to ${formatDisplay(
                  lifecycleResult.supportCaseLifecycle.supportCase.status,
                )}.`}{" "}
            No repair, replay, retry, referral mutation, campaign mutation, invite delivery,
            credential change, billing, or money action was performed.
          </div>
        ) : null}
        {assignmentResult ? (
          <div className="success-panel">
            <strong>Case owner assigned.</strong>{" "}
            {assignmentResult.supportCaseAssignment.supportCase.title} is owned by{" "}
            {assignmentResult.supportCaseAssignment.assignment.assigneeRef}. No repair, replay,
            retry, referral mutation, campaign mutation, invite delivery, credential change,
            billing, or money action was performed.
          </div>
        ) : null}
        <div className="wizard-status-card">
          <div>
            <strong>Customer cases</strong>
            <p>Only cases for {customerName} are shown here.</p>
          </div>
          <StatusBadge label={`${cases.length} cases`} tone={cases.length ? "info" : "success"} />
        </div>
        {isLoading ? (
          <LoadingState label="Loading support cases" />
        ) : (
          <DataTable
            rows={cases}
            emptyText="No support cases have been recorded for this customer yet."
            columns={[
              {
                key: "case",
                header: "Case",
                render: (row) => (
                  <div>
                    <strong>{getValue(row, ["title"], "Support case")}</strong>
                    <div className="table-subtext">{getValue(row, ["summary"], "No summary returned.")}</div>
                    <div className="table-subtext">{getValue(row, ["caseRef"], "No case reference returned.")}</div>
                    <div className="table-subtext">
                      Owner: {getValue(row, ["assigneeRef"], "") || "Unassigned"}
                    </div>
                  </div>
                ),
              },
              {
                key: "type",
                header: "Type",
                render: (row) => formatDisplay(getValue(row, ["category"], "Manual review")),
              },
              {
                key: "priority",
                header: "Priority",
                render: (row) => (
                  <StatusBadge
                    label={formatDisplay(getValue(row, ["priority"], "Medium"))}
                    tone={statusTone(getValue(row, ["priority"], "Medium"))}
                  />
                ),
              },
              {
                key: "status",
                header: "Status",
                render: (row) => (
                  <StatusBadge
                    label={formatDisplay(getValue(row, ["status"], "Open"))}
                    tone={statusTone(getValue(row, ["status"], "Open"))}
                  />
                ),
              },
              {
                key: "evidence",
                header: "Evidence",
                render: (row) => {
                  const links = asArray(getValue(row, ["evidenceLinks"], "") || []);
                  return links.length
                    ? `${links.length} safe evidence link${links.length === 1 ? "" : "s"}`
                    : "No evidence link";
                },
              },
              {
                key: "updated",
                header: "Updated",
                render: (row) => formatDisplay(getValue(row, ["updatedAt"], "Not returned")),
              },
              {
                key: "actions",
                header: "Work case",
                render: (row) => {
                  const caseRef = getValue(row, ["caseRef"], "");
                  const currentStatus = getValue(row, ["status"], "OPEN");
                  return (
                    <div className="button-row">
                      <button
                        className="button secondary"
                        onClick={() => onReadinessCaseChange(caseRef)}
                        type="button"
                      >
                        Review readiness
                      </button>
                      <button
                        className="button secondary"
                        onClick={() =>
                          onAssignmentChange({
                            caseRef,
                            assigneeRef: getValue(row, ["assigneeRef"], "") || "amplifi-support",
                            assignmentReason: "Assigned for customer support ownership.",
                          })
                        }
                        type="button"
                      >
                        Assign owner
                      </button>
                      <button
                        className="button secondary"
                        onClick={() =>
                          onLifecycleChange({
                            caseRef,
                            action: "note",
                            noteType: "OPERATOR_NOTE",
                            noteText: "",
                            status: currentStatus,
                            transitionReason: "",
                          })
                        }
                        type="button"
                      >
                        Add note
                      </button>
                      <button
                        className="button secondary"
                        onClick={() =>
                          onLifecycleChange({
                            caseRef,
                            action: "status",
                            noteType: "OPERATOR_NOTE",
                            noteText: "",
                            status: currentStatus === "OPEN" ? "INVESTIGATING" : currentStatus,
                            transitionReason: "",
                          })
                        }
                        type="button"
                      >
                        Change status
                      </button>
                    </div>
                  );
                },
              },
            ]}
          />
        )}
        <SupportCaseRepairReplayReadinessPanel
          cases={cases}
          customerName={customerName}
          customerQuery={customerQuery}
          error={readinessError}
          isLoading={isReadinessLoading}
          onSelectCase={onReadinessCaseChange}
          readiness={readiness?.repairReplayReadiness || null}
          readinessCaseRef={readinessCaseRef}
          selectedCustomerPath={selectedCustomerPath}
        />
        {assignmentDraft ? (
          <form className="wizard-status-card support-lifecycle-card" onSubmit={onAssignmentSubmit}>
            <div>
              <strong>Assign case owner</strong>
              <p>
                {selectedAssignmentCase?.title || "Selected support case"} gets an operator owner.
                This is internal ownership only, so no customer record or referral evidence is changed.
              </p>
            </div>
            <StatusBadge label="Assignment only" tone="success" />
            <label className="field">
              <span>Owner reference</span>
              <input
                aria-label="Support case owner reference"
                className="input"
                onChange={(event) =>
                  onAssignmentChange({ ...assignmentDraft, assigneeRef: event.target.value })
                }
                placeholder="Example: amplifi-support"
                value={assignmentDraft.assigneeRef}
              />
              <span className="field-help">Use the safe operator or queue reference for this case.</span>
            </label>
            <label className="field">
              <span>Why this owner?</span>
              <textarea
                aria-label="Support case assignment reason"
                className="input textarea"
                onChange={(event) =>
                  onAssignmentChange({ ...assignmentDraft, assignmentReason: event.target.value })
                }
                placeholder="Example: Assigned to support owner for customer recovery follow-up."
                value={assignmentDraft.assignmentReason}
              />
            </label>
            <div className="button-row">
              <button
                className="button"
                disabled={
                  isAssignmentSaving ||
                  !assignmentDraft.assigneeRef.trim() ||
                  !assignmentDraft.assignmentReason.trim()
                }
                type="submit"
              >
                {isAssignmentSaving ? "Saving owner" : "Save owner"}
              </button>
              <button
                className="button secondary"
                onClick={() => onAssignmentChange(null)}
                type="button"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : null}
        {lifecycleDraft ? (
          <form className="wizard-status-card support-lifecycle-card" onSubmit={onLifecycleSubmit}>
            <div>
              <strong>
                {lifecycleDraft.action === "note" ? "Add a case note" : "Change case status"}
              </strong>
              <p>
                {selectedLifecycleCase?.title || "Selected support case"} stays customer-scoped. This records
                evidence only.
              </p>
            </div>
            {lifecycleDraft.action === "note" ? (
              <>
                <label className="field">
                  <span>Note type</span>
                  <select
                    aria-label="Support case note type"
                    className="input"
                    onChange={(event) =>
                      onLifecycleChange({ ...lifecycleDraft, noteType: event.target.value })
                    }
                    value={lifecycleDraft.noteType}
                  >
                    {supportCaseNoteTypeOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span>Safe note</span>
                  <textarea
                    aria-label="Support case note"
                    className="input textarea"
                    onChange={(event) =>
                      onLifecycleChange({ ...lifecycleDraft, noteText: event.target.value })
                    }
                    placeholder="Write a plain-language update. Do not paste raw customer identifiers, secrets, provider payloads, or bank data."
                    value={lifecycleDraft.noteText}
                  />
                </label>
              </>
            ) : (
              <>
                <label className="field">
                  <span>New status</span>
                  <select
                    aria-label="Support case status"
                    className="input"
                    onChange={(event) =>
                      onLifecycleChange({ ...lifecycleDraft, status: event.target.value })
                    }
                    value={lifecycleDraft.status}
                  >
                    {supportCaseStatusOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span>Why is the status changing?</span>
                  <textarea
                    aria-label="Support case status reason"
                    className="input textarea"
                    onChange={(event) =>
                      onLifecycleChange({
                        ...lifecycleDraft,
                        transitionReason: event.target.value,
                      })
                    }
                    placeholder="Example: Evidence reviewed and customer is waiting for integration setup confirmation."
                    value={lifecycleDraft.transitionReason}
                  />
                </label>
              </>
            )}
            <div className="button-row">
              <button
                className="button"
                disabled={
                  isLifecycleSaving ||
                  (lifecycleDraft.action === "note"
                    ? !lifecycleDraft.noteText.trim()
                    : !lifecycleDraft.transitionReason.trim())
                }
                type="submit"
              >
                {isLifecycleSaving
                  ? "Saving update"
                  : lifecycleDraft.action === "note"
                    ? "Save note"
                    : "Save status"}
              </button>
              <button
                className="button secondary"
                onClick={() => onLifecycleChange(null)}
                type="button"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : null}
        <div className="customer-context-note">
          This page records support demand, owner assignment, and the safe case trail. Repair actions,
          replay, retry, provider execution, export creation, credential changes, billing, and money
          movement remain separate governed workflows.
        </div>
      </div>
    </section>
  );
}

function SupportCaseRepairReplayReadinessPanel({
  cases,
  customerName,
  customerQuery,
  error,
  isLoading,
  onSelectCase,
  readiness,
  readinessCaseRef,
  selectedCustomerPath,
}: {
  cases: ReferralSaasSupportCase[];
  customerName: string;
  customerQuery: string;
  error: unknown;
  isLoading: boolean;
  onSelectCase: (caseRef: string) => void;
  readiness: ReferralSaasSupportCaseRepairReplayReadiness | null;
  readinessCaseRef: string;
  selectedCustomerPath: string;
}) {
  if (!cases.length) {
    return (
      <div className="wizard-status-card">
        <div>
          <strong>Repair/replay readiness</strong>
          <p>Record a support case first. Readiness is shown only against a selected case.</p>
        </div>
        <StatusBadge label="Waiting for case" tone="info" />
      </div>
    );
  }

  const evidenceRoute = supportCaseEvidenceRoute(
    selectedCustomerPath,
    readiness?.owningWorkflow || "support_hub",
    customerQuery,
  );
  const evidenceLinks = readiness?.supportCase.evidenceLinks || [];
  const safeActionCount =
    readiness?.allowedActions.filter((action) => action.status === "AVAILABLE").length || 0;
  const blockedActionCount =
    readiness?.allowedActions.filter((action) => action.status === "BLOCKED").length || 0;

  return (
    <div className="wizard-status-card support-lifecycle-card">
      <div>
        <strong>Repair/replay readiness</strong>
        <p>
          Read-only posture for one support case. This shows what evidence can be reviewed and
          why a future governed fix is blocked here.
        </p>
      </div>
      <StatusBadge
        label={readiness ? formatDisplay(readiness.overallStatus) : "Select case"}
        tone={readiness ? statusTone(readiness.overallStatus) : "info"}
      />
      <label className="field">
        <span>Case to review</span>
        <select
          aria-label="Support case readiness case"
          className="input"
          onChange={(event) => onSelectCase(event.target.value)}
          value={readinessCaseRef}
        >
          {cases.map((supportCase) => (
            <option key={supportCase.caseRef} value={supportCase.caseRef}>
              {supportCase.title} - {supportCase.caseRef}
            </option>
          ))}
        </select>
      </label>
      {isLoading ? <LoadingState label="Checking support-case readiness" /> : null}
      {error ? <ErrorPanel error={error} /> : null}
      {readiness ? (
        <>
          <div className="grid-3">
            <KpiCard
              label="Safe diagnostics"
              icon={Search}
              value={safeActionCount}
              footnote="Evidence review only"
            />
            <KpiCard
              label="Blocked future actions"
              icon={AlertCircle}
              value={blockedActionCount}
              footnote="No repair/replay command here"
            />
            <KpiCard
              label="Required evidence"
              icon={ListChecks}
              value={readiness.requiredEvidence.length}
              footnote="Needed before a governed command exists"
            />
          </div>
          <div className="customer-context-note">
            <strong>In plain English:</strong>{" "}
            {supportCaseReadinessPlainEnglish(readiness, customerName)}
          </div>
          <div className="route-list">
            {readiness.allowedActions.map((action) => (
              <div className="wizard-status-card" key={`${action.action}-${action.status}`}>
                <div>
                  <strong>{action.label || formatDisplay(action.action)}</strong>
                  <p>{supportCaseActionCopy(action)}</p>
                </div>
                <StatusBadge label={formatDisplay(action.status)} tone={statusTone(action.status)} />
              </div>
            ))}
          </div>
          <div className="wizard-status-card">
            <div>
              <strong>Evidence to inspect</strong>
              <p>
                Owning workflow: {formatDisplay(readiness.owningWorkflow)}. Open the evidence
                area if the operator needs to continue investigation.
              </p>
            </div>
            <Link className="button secondary" to={evidenceRoute}>
              Open evidence area
            </Link>
          </div>
          <DataTable
            rows={evidenceLinks}
            emptyText="No evidence is linked to this support case yet."
            columns={[
              {
                key: "type",
                header: "Evidence type",
                render: (row) => formatDisplay(row.evidenceType),
              },
              {
                key: "ref",
                header: "Safe reference",
                render: (row) => row.evidenceRef,
              },
              {
                key: "status",
                header: "Safe status",
                render: (row) => (
                  <StatusBadge
                    label={formatDisplay(row.safeStatus || "Not returned")}
                    tone={statusTone(row.safeStatus || "INFO")}
                  />
                ),
              },
            ]}
          />
          <div className="customer-context-note">
            No executable repair, replay, retry, provider dispatch, credential/auth change,
            campaign activation, billing, or money movement is available from this page.
          </div>
        </>
      ) : null}
    </div>
  );
}

function supportCaseReadinessPlainEnglish(
  readiness: ReferralSaasSupportCaseRepairReplayReadiness,
  customerName: string,
) {
  if (readiness.overallStatus === "CASE_CLOSED") {
    return `${readiness.supportCase.title} is closed for ${customerName}. Reopen or create a new case before reviewing any future governed action.`;
  }
  if (readiness.overallStatus === "ACTION_NOT_SUPPORTED") {
    return `${readiness.supportCase.title} is a support investigation only. Use the evidence area; no repair or replay path applies to this case.`;
  }
  return `${readiness.supportCase.title} has evidence to inspect. A future governed repair or replay may be considered later, but this page only shows readiness and blockers.`;
}

function supportCaseActionCopy(action: ReferralSaasSupportCaseRepairReplayAction) {
  if (action.action === "READ_ONLY_DIAGNOSTIC") {
    return action.status === "AVAILABLE"
      ? "You can review safe evidence for this case."
      : "The case is closed, so diagnostic review is read-only history.";
  }
  if (action.action === "HARD_EXCLUDED") {
    return "This case type does not support repair or replay.";
  }
  return "Blocked until a future governed command exists with audit, idempotency, evidence, and approval gates.";
}

function supportCaseEvidenceRoute(
  selectedCustomerPath: string,
  owningWorkflow: string,
  customerQuery: string,
) {
  const moduleRoute =
    {
      account_health: "health",
      attribution_trace: "attribution",
      integrations: "integrations",
      links_and_codes: "links",
      people_and_access: "people",
      progress_status: "progress",
      reports: "reports",
      support_hub: "support",
    }[owningWorkflow] || "support";
  return `${selectedCustomerPath}/${moduleRoute}${customerQuery}`;
}

function CustomerModulePage({
  customerName,
  customerQuery,
  module,
}: {
  customerName: string;
  customerQuery: string;
  module: CustomerModule;
}) {
  const details = getModulePageDetails(module);
  return (
    <section className="panel customer-module-page">
      <div className="panel-header">
        <div>
          <div className="page-kicker">Referral SaaS &gt; {customerName} &gt; {details.kicker}</div>
          <h2 className="panel-title">{details.title}</h2>
          <div className="panel-subtitle">{details.copy}</div>
        </div>
      </div>
      <div className="panel-body route-list">
        <div className="wizard-status-card">
          <div>
            <strong>{details.actionTitle}</strong>
            <p>{details.actionCopy}</p>
          </div>
          <StatusBadge label="Customer scoped" tone={details.tone} />
        </div>
        {details.externalRoute ? (
          <Link className="button" to={`${details.externalRoute}${customerQuery}`}>
            Open current {details.title.toLowerCase()} workspace
          </Link>
        ) : null}
        <div className="customer-context-note">
          This is a separate customer page. It keeps {customerName} in context instead of expanding the customer home.
        </div>
      </div>
    </section>
  );
}

function getModulePageDetails(module: CustomerModule) {
  switch (module) {
    case "campaigns":
      return {
        kicker: "Campaigns",
        title: "Campaigns",
        copy: "Campaign work for this customer only.",
        actionTitle: "Campaigns for this customer",
        actionCopy: "Set up or review referral campaigns while keeping the selected customer context.",
        externalRoute: "/admin/referral-saas/campaigns",
        tone: "success" as StatusTone,
      };
    case "links":
      return {
        kicker: "Links and codes",
        title: "Links and codes",
        copy: "Referral links and codes for this customer only.",
        actionTitle: "Links and codes for this customer",
        actionCopy: "Issue, inspect, and validate referral codes without leaving customer context.",
        externalRoute: "/admin/referral-saas/link-codes",
        tone: "success" as StatusTone,
      };
    case "reports":
      return {
        kicker: "Reports",
        title: "Reports",
        copy: "Tenant-safe referral and campaign reporting for this customer.",
        actionTitle: "Reporting setup",
        actionCopy: "Open the report workspace with this customer already scoped.",
        externalRoute: "/admin/referral-saas/reports",
        tone: "warning" as StatusTone,
      };
    case "support":
      return {
        kicker: "Support",
        title: "Support",
        copy: "Support evidence for this customer.",
        actionTitle: "Support hub",
        actionCopy: "Investigate validation, link/code, progress, and attribution issues in customer context.",
        externalRoute: "/admin/referral-saas/support",
        tone: "success" as StatusTone,
      };
    case "attribution":
      return {
        kicker: "Attribution",
        title: "Attribution",
        copy: "Explainable attribution evidence for this customer.",
        actionTitle: "Attribution trace",
        actionCopy: "Open the attribution trace workspace with customer identifiers carried forward.",
        externalRoute: "/admin/referral-saas/attribution-trace",
        tone: "success" as StatusTone,
      };
    case "progress":
      return {
        kicker: "Progress status",
        title: "Progress status",
        copy: "Referral journey progress for this customer.",
        actionTitle: "Progress diagnostics",
        actionCopy: "Review safe progress status and missing evidence without leaking internal identifiers.",
        externalRoute: "/admin/referral-saas/progress-status",
        tone: "success" as StatusTone,
      };
    default:
      return {
        kicker: "Customer page",
        title: "Customer page",
        copy: "Customer-scoped work area.",
        actionTitle: "Customer-scoped action",
        actionCopy: "This page keeps customer work separate from the profile home.",
        externalRoute: "",
        tone: "info" as StatusTone,
      };
  }
}

function getCustomerNextActions({
  blockedCount,
  missingEvidenceCount,
  hasAcceptedRequiredAccess,
  commercialBlocked,
  hasSeatProvisioningWork,
}: {
  blockedCount: number;
  missingEvidenceCount: number;
  hasAcceptedRequiredAccess: boolean;
  commercialBlocked: boolean;
  hasSeatProvisioningWork: boolean;
}) {
  if (!hasAcceptedRequiredAccess) {
    return [
      {
        title: "Add who can manage this account",
        copy: "Complete owner and campaign manager setup for day-to-day referral work.",
        priority: "First",
        route: "people",
        tone: "warning" as StatusTone,
      },
      {
        title: "Check integrations",
        copy: "See whether API, webhook, invite delivery, and referral message providers are ready.",
        priority: "Next",
        route: "integrations",
        tone: "info" as StatusTone,
      },
      {
        title: "Open Campaigns",
        copy: "Account setup is far enough to set up or review a campaign.",
        priority: "Later",
        route: "campaigns",
        tone: "neutral" as StatusTone,
      },
    ];
  }
  if (blockedCount > 0 || missingEvidenceCount > 0 || hasSeatProvisioningWork) {
    return [
      {
        title: "Check integrations",
        copy: "See whether API, webhook, invite delivery, and referral message providers are ready.",
        priority: "First",
        route: "integrations",
        tone: "warning" as StatusTone,
      },
      {
        title: "Review account health",
        copy: "Confirm remaining customer setup warnings without reopening People and Access.",
        priority: "Next",
        route: "health",
        tone: "info" as StatusTone,
      },
      {
        title: "Open Campaigns",
        copy: "Account setup is far enough to set up or review a campaign.",
        priority: "Later",
        route: "campaigns",
        tone: "neutral" as StatusTone,
      },
    ];
  }
  if (commercialBlocked) {
    return [
      {
        title: "Review plan and entitlement",
        copy: "Production launch needs an explicit commercial entitlement source.",
        priority: "First",
        route: "commercial",
        tone: "warning" as StatusTone,
      },
      {
        title: "Open Campaigns",
        copy: "Safe setup and campaign drafting can continue before production launch.",
        priority: "Next",
        route: "campaigns",
        tone: "info" as StatusTone,
      },
      {
        title: "Check integrations",
        copy: "Confirm API, webhook, invite delivery, and referral message readiness.",
        priority: "Later",
        route: "integrations",
        tone: "neutral" as StatusTone,
      },
    ];
  }
  return [
    {
      title: "Open Campaigns",
      copy: "The customer is ready for campaign setup or review.",
      priority: "First",
      route: "campaigns",
      tone: "success" as StatusTone,
    },
    {
      title: "Run link and code tests",
      copy: "Issue and validate referral codes inside this customer context.",
      priority: "Next",
      route: "links",
      tone: "info" as StatusTone,
    },
    {
      title: "Check reporting",
      copy: "Review tenant-safe performance and export posture.",
      priority: "Later",
      route: "reports",
      tone: "neutral" as StatusTone,
    },
  ];
}

function accessReadinessSummary(overallStatus: string, missingRoleCount: number) {
  if (overallStatus === "ACCESS_READY") {
    return "The required customer access responsibilities are confirmed.";
  }
  if (missingRoleCount > 0) {
    const label = missingRoleCount === 1 ? "responsibility" : "responsibilities";
    const verb = missingRoleCount === 1 ? "needs" : "need";
    return `${formatDisplay(missingRoleCount)} ${label} still ${verb} to be named for this customer.`;
  }
  return "People are named, but customer acceptance is not confirmed yet.";
}

function accessLifecycleLabel(status: string) {
  if (status === "ACTIVE") {
    return "Confirmed";
  }
  if (status === "INVITED") {
    return "Added";
  }
  if (status === "MISSING") {
    return "Still needed";
  }
  return formatDisplay(status);
}

function accessLifecycleTone(status: string): StatusTone {
  if (status === "ACTIVE") {
    return "success";
  }
  if (status === "INVITED") {
    return "info";
  }
  if (status === "MISSING") {
    return "warning";
  }
  return statusTone(status);
}

function accessAcceptanceLabel(status: string) {
  if (status === "ACTIVE") {
    return "Accepted";
  }
  if (status === "READY_TO_ACTIVATE") {
    return "Ready to accept";
  }
  if (status === "BLOCKED") {
    return "Blocked";
  }
  if (status === "INVITED") {
    return "Added";
  }
  if (status === "MISSING") {
    return "Still needed";
  }
  return formatDisplay(status);
}

function accessProvisioningLabel(status: string) {
  if (status === "PROVISIONING_BLOCKED" || status === "SEPARATE_WORKFLOW") {
    return "Login separate";
  }
  if (status === "READY_TO_PROVISION_SEAT") {
    return "Ready for seat";
  }
  if (status === "SEAT_ASSIGNED") {
    return "Seat assigned";
  }
  if (status === "WAITING_FOR_MEMBERSHIP_ACTIVATION") {
    return "Waiting for confirmation";
  }
  return formatDisplay(status);
}

function accessProvisioningTone(status: string): StatusTone {
  if (status === "SEAT_ASSIGNED") {
    return "success";
  }
  if (status === "READY_TO_PROVISION_SEAT") {
    return "warning";
  }
  return statusTone(status);
}

function timelineEvidenceTone(posture: string): StatusTone {
  if (posture === "READY_FOR_SUPPORT_AND_ATTRIBUTION") {
    return "success";
  }
  if (posture === "DEDUPE_REPLAY_RECORDED") {
    return "info";
  }
  if (posture === "SOURCE_EVENT_FAILED_OR_DELAYED") {
    return "danger";
  }
  if (posture === "CHECK_SOURCE_PROVENANCE" || posture === "CHECK_IDEMPOTENCY_EVIDENCE") {
    return "warning";
  }
  return statusTone(posture);
}

function timelineEvidencePlainLanguage(posture: string) {
  if (posture === "READY_FOR_SUPPORT_AND_ATTRIBUTION") {
    return "The referral timeline has enough safe source and idempotency evidence to explain.";
  }
  if (posture === "DEDUPE_REPLAY_RECORDED") {
    return "A replay or duplicate event was safely detected and recorded.";
  }
  if (posture === "SOURCE_EVENT_FAILED_OR_DELAYED") {
    return "At least one source event is failed, ignored, or delayed.";
  }
  if (posture === "CHECK_SOURCE_PROVENANCE") {
    return "Some events need source-system or inbox proof before they can be fully trusted.";
  }
  if (posture === "CHECK_IDEMPOTENCY_EVIDENCE") {
    return "Some events need idempotency proof before replay safety is clear.";
  }
  if (posture === "NO_TIMELINE_EVIDENCE") {
    return "No progress timeline evidence has been returned yet.";
  }
  return "Review the event-level evidence posture before support, attribution, or reporting decisions.";
}

function initials(name: string) {
  const letters = name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
  return letters || "?";
}

function peopleAccessStage(row: Record<string, unknown>, readiness?: Record<string, unknown>) {
  if (Boolean(row.isMissingRole)) {
    return { label: "Still needed", tone: "warning" as StatusTone };
  }
  const membershipStatus = getValue(row, ["status"], getValue(row, ["membershipStatus"], ""));
  const activationStatus = getValue(readiness || {}, ["activationReadiness"], membershipStatus);
  const provisioningReadiness = getValue(readiness || {}, ["provisioningReadiness"], "");
  const seatStatus = getValue(readiness || {}, ["seatAssignmentStatus"], "");
  if (seatStatus === "SEAT_ASSIGNED" || provisioningReadiness === "SEAT_ASSIGNED") {
    return { label: "Seat assigned", tone: "success" as StatusTone };
  }
  if (membershipStatus === "ACTIVE") {
    return { label: "Confirmed", tone: "success" as StatusTone };
  }
  if (activationStatus === "READY_TO_ACTIVATE") {
    return { label: "Ready to confirm", tone: "info" as StatusTone };
  }
  if (membershipStatus === "INVITED") {
    return { label: "Added", tone: "info" as StatusTone };
  }
  return { label: accessLifecycleLabel(membershipStatus), tone: accessLifecycleTone(membershipStatus) };
}

function peopleAccessNextAction(row: Record<string, unknown>, readiness?: Record<string, unknown>) {
  if (Boolean(row.isMissingRole)) {
    return "Add the person who owns this responsibility.";
  }
  const membershipStatus = getValue(row, ["status"], getValue(row, ["membershipStatus"], ""));
  const activationStatus = getValue(readiness || {}, ["activationReadiness"], "");
  const provisioningReadiness = getValue(readiness || {}, ["provisioningReadiness"], "");
  const seatStatus = getValue(readiness || {}, ["seatAssignmentStatus"], "");
  const deliveryReadiness = getValue(readiness || {}, ["deliveryReadiness"], "");
  const contactStatus = getValue(row, ["recipientContactStatus"], getValue(readiness || {}, ["recipientContactStatus"], ""));

  if (seatStatus === "SEAT_ASSIGNED" || provisioningReadiness === "SEAT_ASSIGNED") {
    return "Seat is assigned. Record login completion only if this person must sign in.";
  }
  if (membershipStatus === "ACTIVE" && provisioningReadiness === "READY_TO_PROVISION_SEAT") {
    return "Confirmed for customer work. Assign a platform seat only if this person must sign in.";
  }
  if (membershipStatus === "ACTIVE") {
    return "Confirmed for customer work. Platform login remains a separate optional setup step.";
  }
  if (activationStatus === "READY_TO_ACTIVATE") {
    return "Confirm this person after the customer approves the responsibility.";
  }
  if (deliveryReadiness === "READY_TO_DELIVER_INVITE") {
    return "Invite delivery can be checked when you need provider evidence.";
  }
  if (contactStatus !== "CONTACT_REFERENCE_PRESENT") {
    return "Add a safe work email before invite delivery or acceptance checks.";
  }
  return "Review this person before invite delivery or accepted access.";
}

function seatTypeForRoleFamily(roleFamily: string):
  | "ADMIN"
  | "OPERATOR"
  | "PARTNER"
  | "PRODUCER"
  | "DISTRIBUTOR"
  | "CONSUMER"
  | "SUPPORT" {
  if (roleFamily === "DISTRIBUTION_ADMIN") {
    return "ADMIN";
  }
  if (roleFamily === "CAMPAIGN_MANAGER") {
    return "OPERATOR";
  }
  if (roleFamily === "SUPPORT") {
    return "SUPPORT";
  }
  return "OPERATOR";
}

function permissionProfileForRoleFamily(roleFamily: string) {
  if (roleFamily === "DISTRIBUTION_ADMIN") {
    return "REFERRAL_SAAS_ACCOUNT_ADMIN";
  }
  if (roleFamily === "CAMPAIGN_MANAGER") {
    return "REFERRAL_SAAS_CAMPAIGN_MANAGER";
  }
  if (roleFamily === "SUPPORT") {
    return "REFERRAL_SAAS_SUPPORT";
  }
  return "REFERRAL_SAAS_OPERATOR";
}

function inviteDeliveryProviderRef(readiness?: ReferralSaasTechnicalSetupReadinessResponse) {
  const inviteCapability = readiness?.technicalSetupReadiness.capabilities.find(
    (capability) => capability.code === "MEMBERSHIP_INVITE_DELIVERY",
  );
  return inviteCapability?.approvedProviderRefs[0] || "";
}

function approvedAuthProviderRef(readiness?: ReferralSaasTechnicalSetupReadinessResponse) {
  const preferredCapability = readiness?.technicalSetupReadiness.capabilities.find(
    (capability) =>
      ["PLATFORM_LOGIN", "AUTH_PROVIDER", "MEMBERSHIP_INVITE_DELIVERY"].includes(capability.code) &&
      capability.approvedProviderRefs.length,
  );
  return preferredCapability?.approvedProviderRefs[0] || "";
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function buildIntegrationConfigurationPayload(
  draft: IntegrationConfigurationDraft,
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context: "setup";
  },
  accountId: string,
) {
  const providerRefs = draft.inviteProviderApprovalRef.trim()
    ? [draft.inviteProviderApprovalRef.trim()]
    : [];
  return {
    accountScope,
    apiEnvironment: {
      environment: draft.environment,
      authMethod: draft.intendedAuthMethod,
      useCases: draft.allowedUse,
    },
    webhookIntent: {
      callbackUrl: draft.callbackUrl,
      eventCategories: draft.eventCategories,
      deliveryMode: "DRAFT_ONLY",
    },
    messageProviders: {
      channels: Array.from(new Set([draft.inviteDeliveryChannel, ...draft.referralMessageChannels])),
      providerRefs,
      approvalIntent: providerRefs.length ? "PROVIDER_APPROVAL_REFERENCE_RECORDED" : "DRAFT_ONLY",
    },
    reasonCode: "CUSTOMER_INTEGRATION_CONFIGURATION",
    correlationId: `customer-profile-integrations-${accountId}`,
    idempotencyKey: safeIdempotencyKey(
      "customer-profile-integrations",
      accountId,
      draft.environment,
      draft.intendedAuthMethod,
      ...draft.allowedUse,
      draft.callbackUrl,
      ...draft.eventCategories,
      draft.inviteDeliveryChannel,
      draft.inviteProviderApprovalRef,
      ...draft.referralMessageChannels,
    ),
  };
}

function buildIntegrationApiAccessVerificationPayload(
  draft: IntegrationConfigurationDraft,
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context: "setup";
  },
  accountId: string,
  configurationRef: string,
) {
  return {
    accountScope,
    verification: {
      verificationType: "API_ACCESS_VERIFICATION",
      configurationRef,
      environment: draft.environment,
      authMethod: draft.intendedAuthMethod,
      intendedUseCases: draft.allowedUse,
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
    correlationId: `customer-profile-integrations-api-verification-${accountId}`,
    idempotencyKey: safeIdempotencyKey(
      "customer-profile-integrations-api-verification",
      accountId,
      configurationRef,
      draft.environment,
      draft.intendedAuthMethod,
      ...draft.allowedUse,
    ),
  };
}

function buildIntegrationWebhookTestDispatchPayload(
  draft: IntegrationConfigurationDraft,
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context: "setup";
  },
  accountId: string,
  configurationRef: string,
) {
  return {
    accountScope,
    webhookTest: {
      testType: "WEBHOOK_TEST_DISPATCH",
      configurationRef,
      callbackUrlPresent: Boolean(draft.callbackUrl.trim()),
      eventCategories: draft.eventCategories,
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
    correlationId: `customer-profile-integrations-webhook-test-${accountId}`,
    idempotencyKey: safeIdempotencyKey(
      "customer-profile-integrations-webhook-test",
      accountId,
      configurationRef,
      draft.callbackUrl,
      ...draft.eventCategories,
    ),
  };
}

function buildIntegrationMessageProviderTestPayload(
  draft: IntegrationConfigurationDraft,
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context: "setup";
  },
  accountId: string,
  configurationRef: string,
) {
  const providerRefs = draft.inviteProviderApprovalRef.trim()
    ? [draft.inviteProviderApprovalRef.trim()]
    : [];
  const channels = Array.from(new Set([draft.inviteDeliveryChannel, ...draft.referralMessageChannels]));
  return {
    accountScope,
    messageProviderTest: {
      testType: "MESSAGE_PROVIDER_TEST",
      configurationRef,
      channels,
      providerRefs,
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
    correlationId: `customer-profile-integrations-message-provider-test-${accountId}`,
    idempotencyKey: safeIdempotencyKey(
      "customer-profile-integrations-message-provider-test",
      accountId,
      configurationRef,
      ...channels,
      ...providerRefs,
    ),
  };
}

function buildIntegrationCredentialRequestPayload(
  draft: IntegrationConfigurationDraft,
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context: "setup";
  },
  accountId: string,
  configurationRef: string,
  customerName: string,
) {
  const requestType =
    draft.intendedAuthMethod === "SIGNED_WEBHOOK"
      ? "WEBHOOK_SIGNING_KEY_CREATE"
      : "API_KEY_CREATE";
  const capability =
    requestType === "WEBHOOK_SIGNING_KEY_CREATE"
      ? "REFERRAL_SAAS_WEBHOOK_SIGNING"
      : "REFERRAL_SAAS_API_ACCESS";
  return {
    accountScope,
    credentialRequest: {
      requestType,
      capability,
      environment: draft.environment,
      intendedUse: draft.allowedUse,
      requestedFor: {
        customerName,
        configurationRef,
        requestedBy: "AMPLIFI_ADMIN",
        requestReason: "Customer integration credential setup",
      },
    },
    reasonCode: "CUSTOMER_CREDENTIAL_REQUEST",
    correlationId: `customer-profile-integrations-credential-request-${accountId}`,
    idempotencyKey: safeIdempotencyKey(
      "customer-profile-integrations-credential-request",
      accountId,
      configurationRef,
      requestType,
      capability,
      draft.environment,
      ...draft.allowedUse,
    ),
  };
}

function buildIntegrationCredentialReviewDecisionPayload(
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context: "setup";
  },
  accountId: string,
  credentialRequestRef: string,
  decision: "APPROVED" | "BLOCKED",
) {
  const decisionSlug = decision.toLowerCase();
  const reason =
    decision === "APPROVED"
      ? "Amplifi Admin reviewed this credential setup request and approved it for later governed execution."
      : "Amplifi Admin reviewed this credential setup request and blocked later governed execution.";
  return {
    accountRef: accountId,
    credentialRequestRef,
    accountScope,
    reviewDecision: {
      decision,
      reason,
    },
    reasonCode:
      decision === "APPROVED"
        ? "CUSTOMER_CREDENTIAL_REQUEST_APPROVED"
        : "CUSTOMER_CREDENTIAL_REQUEST_BLOCKED",
    correlationId: `customer-profile-integrations-credential-review-${accountId}-${credentialRequestRef}-${decisionSlug}`,
    idempotencyKey: safeIdempotencyKey(
      "customer-profile-integrations-credential-review",
      accountId,
      credentialRequestRef,
      decisionSlug,
    ),
  };
}

function buildIntegrationCredentialExecutionCheckPayload(
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context: "setup";
  },
  accountId: string,
  credentialRequestRef: string,
) {
  return {
    accountRef: accountId,
    credentialRequestRef,
    accountScope,
    executionCheck: {
      reason:
        "Amplifi Admin checked that this approved credential setup request is ready for later governed execution.",
      reasonCode: "CUSTOMER_CREDENTIAL_EXECUTION_READY_CHECK",
    },
    reasonCode: "CUSTOMER_CREDENTIAL_EXECUTION_READY_CHECK",
    correlationId: `customer-profile-integrations-credential-execution-check-${accountId}-${credentialRequestRef}`,
    idempotencyKey: safeIdempotencyKey(
      "customer-profile-integrations-credential-execution-check",
      accountId,
      credentialRequestRef,
    ),
  };
}

function integrationExecutionActionLabel(actionRef: string, fallback: string) {
  if (actionRef === "CREDENTIAL_REQUEST") {
    return "Credential setup request";
  }
  if (actionRef === "MESSAGE_PROVIDER_TEST") {
    return "Message provider check";
  }
  if (actionRef === "WEBHOOK_TEST_DISPATCH") {
    return "Webhook test";
  }
  if (actionRef === "API_ACCESS_VERIFICATION") {
    return "API access check";
  }
  return fallback;
}

function integrationExecutionActionNextStep(actionRef: string, fallback: string) {
  if (actionRef === "CREDENTIAL_REQUEST") {
    return "Record a governed setup request without creating, showing, storing, or sending credentials.";
  }
  if (actionRef === "MESSAGE_PROVIDER_TEST") {
    return "Record that planned invite/referral message providers are ready without sending a message.";
  }
  if (actionRef === "WEBHOOK_TEST_DISPATCH") {
    return "Record signed callback test evidence without dispatching a business webhook.";
  }
  if (actionRef === "API_ACCESS_VERIFICATION") {
    return "Record that the planned API posture has been checked without creating credentials.";
  }
  return fallback;
}

function credentialRequestLabel(requestType: string) {
  if (requestType === "WEBHOOK_SIGNING_KEY_CREATE") {
    return "Webhook signing setup";
  }
  if (requestType === "API_KEY_ROTATE") {
    return "API key rotation";
  }
  if (requestType === "API_KEY_REVOKE") {
    return "API key revoke";
  }
  if (requestType === "PROVIDER_CREDENTIAL_REFERENCE_CREATE") {
    return "Provider credential reference";
  }
  return "API credential setup";
}

function toggleListValue(values: string[], value: string) {
  return values.includes(value)
    ? values.filter((currentValue) => currentValue !== value)
    : [...values, value];
}

function campaignEvidenceTone(value: string): StatusTone {
  const normalised = value.toLowerCase();
  if (normalised.includes("blocker")) {
    return "danger";
  }
  if (normalised.includes("warning") || normalised.includes("unknown")) {
    return "warning";
  }
  return "info";
}

function attributionConfidenceTone(value: string): StatusTone {
  const normalised = value.trim().toUpperCase();
  if (normalised === "HIGH") {
    return "success";
  }
  if (normalised === "CONFLICT") {
    return "danger";
  }
  if (normalised === "MISSING" || normalised === "LOW") {
    return "warning";
  }
  return "info";
}

function attributionStatusTone(value: string): StatusTone {
  const normalised = value.trim().toUpperCase();
  if (normalised === "READY" || normalised === "CREDITED") {
    return "success";
  }
  if (normalised === "REVIEW_REQUIRED") {
    return "danger";
  }
  if (
    normalised === "PARTIAL_EVIDENCE" ||
    normalised === "NO_ATTRIBUTION_EVIDENCE" ||
    normalised === "CREDITABLE" ||
    normalised === "NEEDS_EVIDENCE" ||
    normalised === "NO_REFERRALS"
  ) {
    return "warning";
  }
  return "info";
}

function formatCampaignLabel(value: unknown): string {
  return formatDisplay(value)
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b[a-z]/g, (letter) => letter.toUpperCase());
}

function campaignLifecycleActionsFor(status: string): ReferralSaasCampaignLifecycleAction[] {
  const lifecycle = status.trim().toUpperCase();
  if (lifecycle === "ACTIVE" || lifecycle === "SCHEDULED") {
    return ["PAUSE", "END"];
  }
  if (lifecycle === "PAUSED") {
    return ["RESUME", "END", "ARCHIVE"];
  }
  if (lifecycle === "ENDED") {
    return ["ARCHIVE"];
  }
  return [];
}

function campaignLifecycleActionLabel(action: ReferralSaasCampaignLifecycleAction): string {
  if (action === "PAUSE") {
    return "Pause";
  }
  if (action === "RESUME") {
    return "Resume";
  }
  if (action === "END") {
    return "End";
  }
  return "Archive";
}

function buildCustomerModuleRoute(selectedCustomerPath: string, route: string, customerQuery: string) {
  if (isCustomerModule(route)) {
    return `${selectedCustomerPath}/${route}`;
  }
  return `${route}${customerQuery}`;
}

function normalizeCustomerModule(value: string | undefined): CustomerModule {
  if (value === "technical") {
    return "integrations";
  }
  return isCustomerModule(value) ? value : "home";
}

function isCustomerModule(value: string | undefined): value is CustomerModule {
  return [
    "home",
    "health",
    "settings",
    "people",
    "commercial",
    "integrations",
    "technical",
    "journeys",
    "programmes",
    "campaigns",
    "referrals",
    "referrers",
    "links",
    "reports",
    "support",
    "attribution",
    "progress",
  ].includes(value || "");
}

function isValidEmail(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

function safeIdempotencyKey(...parts: string[]) {
  return parts
    .map((part) => part.trim().toLowerCase().replace(/[^a-z0-9-]+/g, "-").replace(/^-+|-+$/g, ""))
    .filter(Boolean)
    .join("-");
}

function textValue(value: unknown, fallback = "") {
  if (typeof value === "string") {
    return value.trim() || fallback;
  }
  if (value === null || value === undefined) {
    return fallback;
  }
  return String(value).trim() || fallback;
}

function textArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((entry) => textValue(entry)).filter(Boolean);
}

function splitConfiguredList(value: string): string[] {
  return value
    .split(/[\n,]+/)
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function parseTransitionRules(value: string): { from: string; to: string }[] {
  return value
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const separator = line.includes(">") ? ">" : ":";
      const [from, to] = line.split(separator);
      return { from: (from || "").trim(), to: (to || "").trim() };
    })
    .filter((transition) => transition.from && transition.to);
}

function allowedJourneySections(version?: ReferralSaasJourneyTemplateVersionSummary) {
  return new Set((version?.allowedConfigurationSections || []).map((section) => section.toLowerCase()));
}

function journeySectionAllowed(sections: Set<string>, ...names: string[]) {
  return names.some((name) => sections.has(name.toLowerCase()));
}

function buildJourneyConfigurationPayload(
  draft: JourneyConfigurationDraft,
  selectedVersion?: ReferralSaasJourneyTemplateVersionSummary,
): Record<string, unknown> {
  const sections = allowedJourneySections(selectedVersion);
  const payload: Record<string, unknown> = {};
  const milestones = splitConfiguredList(draft.milestoneCodes);
  const transitions = parseTransitionRules(draft.transitionRules);
  const evidence = splitConfiguredList(draft.evidenceCodes);
  const rewardPolicyCode = draft.rewardPolicyCode.trim();
  const attributionWindowDays = Number(draft.attributionWindowDays);

  if (milestones.length && journeySectionAllowed(sections, "milestones", "enabledMilestones")) {
    payload.milestones = milestones.map((code) => ({ code }));
  }
  if (transitions.length && journeySectionAllowed(sections, "transitions", "transitionRules")) {
    payload.transitions = transitions;
  }
  if (evidence.length && journeySectionAllowed(sections, "evidence", "evidenceRequirements", "requiredEvidence")) {
    payload.evidence = evidence.map((code) => ({ code }));
  }
  if (rewardPolicyCode && journeySectionAllowed(sections, "rewards", "rewardPolicy")) {
    payload.rewards = { policyCode: rewardPolicyCode, mode: "configured_reference_only" };
  }
  if (
    Number.isFinite(attributionWindowDays) &&
    attributionWindowDays > 0 &&
    journeySectionAllowed(sections, "attribution")
  ) {
    payload.attribution = { attributionWindowDays };
  }
  return payload;
}

function extractPayloadCodes(payload: Record<string, unknown>, key: "milestones" | "evidence") {
  return asArray(payload[key])
    .map((entry) => textValue(getNestedValue(entry, ["code"])))
    .filter(Boolean)
    .join(", ");
}

function extractPayloadTransitions(payload: Record<string, unknown>) {
  return asArray(payload.transitions)
    .map((entry) => {
      const from = textValue(getNestedValue(entry, ["from"]));
      const to = textValue(getNestedValue(entry, ["to"]));
      return from && to ? `${from} > ${to}` : "";
    })
    .filter(Boolean)
    .join("\n");
}

function downloadCustomerReportFile({
  content,
  contentType,
  fileName,
}: {
  content: string;
  contentType: string;
  fileName: string;
}) {
  const blob = new Blob([content], { type: contentType || "text/plain" });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

function newAccessCreateAttemptKey() {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function newSupportCaseLifecycleRequestKey() {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function newSupportCaseAssignmentRequestKey() {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

async function sha256Hex(value: string) {
  if (!window.crypto?.subtle) {
    let hash = 5381;
    for (const character of value.toLowerCase()) {
      hash = (hash * 33) ^ character.charCodeAt(0);
    }
    return `local-${(hash >>> 0).toString(16)}`;
  }
  const data = new TextEncoder().encode(value);
  const hashBuffer = await window.crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hashBuffer))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

function formatList(values: string[]) {
  return values.length ? values.map(formatDisplay).join(", ") : "None";
}

function resolveReadinessArea(
  area: (typeof readinessCategoryMap)[number],
  categories: Record<string, unknown>[],
) {
  const matchingCategory = categories.find((category) => categoryMatches(category, area.code));
  const status = formatDisplay(
    getNestedValue(matchingCategory, ["safe_display_status", "label"], getNestedValue(matchingCategory, ["status"], "Not ready")),
  );
  return {
    label: area.label,
    status,
    evidence: formatDisplay(getNestedValue(matchingCategory, ["evidence_summary"], "No customer evidence has been returned for this area yet.")),
  };
}

function categoryMatches(category: Record<string, unknown>, code: string) {
  const categoryCode = getValue(category, ["category"], "").toUpperCase();
  return categoryCode === code;
}

function toCount(value: unknown) {
  const count = Number(value);
  return Number.isFinite(count) ? count : 0;
}

function formatAreaCount(count: number, singularLabel: string) {
  return `${formatDisplay(count)} ${count === 1 ? singularLabel : `${singularLabel}s`}`;
}

function findAccountExternalRef(
  references: { refType: string; externalRef: string }[] = [],
  refType: string,
) {
  return references.find((reference) => reference.refType === refType)?.externalRef || "";
}

const knownOperatingMarkets = [
  { name: "South Africa", description: "South African referral accounts" },
  { name: "Botswana", description: "Botswana operating market" },
  { name: "Namibia", description: "Namibia operating market" },
  { name: "Zambia", description: "Zambia operating market" },
];

function getOperatingMarkets(accounts: AccountRegistryItem[]) {
  const counts = accounts.reduce<Record<string, number>>((marketCounts, account) => {
    const market = operatingMarketFromAccount(account).name;
    marketCounts[market] = (marketCounts[market] || 0) + 1;
    return marketCounts;
  }, {});

  const knownMarkets = knownOperatingMarkets.map((market) => ({
    ...market,
    count: counts[market.name] || 0,
  }));
  const unknownCount = counts["Other markets"] || 0;
  return unknownCount
    ? [
        ...knownMarkets,
        {
          name: "Other markets",
          description: "Accounts without a mapped operating market",
          count: unknownCount,
        },
      ]
    : knownMarkets;
}

function operatingMarketFromAccount(account: AccountRegistryItem) {
  return operatingMarketFromCode(account.operatingJurisdictionCode);
}

function operatingMarketFromCode(code: string | undefined) {
  switch ((code || "OTHER").toUpperCase()) {
    case "ZA":
      return { name: "South Africa", description: "South African referral accounts" };
    case "BW":
      return { name: "Botswana", description: "Botswana operating market" };
    case "NA":
      return { name: "Namibia", description: "Namibia operating market" };
    case "ZM":
      return { name: "Zambia", description: "Zambia operating market" };
    default:
      return { name: "Other markets", description: "Accounts without a mapped operating market" };
  }
}

function findSelectedAccount(
  accounts: AccountRegistryItem[] = [],
  externalTenantRef: string,
  organisationRef: string,
) {
  return accounts.find((account) => isSelectedAccount(account, externalTenantRef, organisationRef));
}

function isSelectedAccount(
  account: AccountRegistryItem,
  externalTenantRef: string,
  organisationRef: string,
) {
  const accountExternalTenantRef =
    account.primaryExternalTenantRef ||
    findAccountExternalRef(account.externalReferences, "external_tenant_ref");
  const accountOrganisationRef = findAccountExternalRef(account.externalReferences, "organisation_ref");
  return accountExternalTenantRef === externalTenantRef && accountOrganisationRef === organisationRef;
}
