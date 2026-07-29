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
  useReferralSaasAccountCampaignReadiness,
  useReferralSaasAccountDraftSelector,
  useReferralSaasAccountMaintenanceState,
  useReferralSaasAccountMembershipPosture,
  useReferralSaasMembershipActivationReadiness,
  useReferralSaasAccountRegistry,
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
  getReferralSaasAccountReport,
  previewReferralSaasAccountReportExport,
  type ReferralSaasExportFormat,
  type ReferralSaasReportType,
} from "../../api/endpoints/referralSaasReports";
import {
  cancelReferralSaasMembershipInvitationIntent,
  createReferralSaasAccountCampaignSetup,
  recordReferralSaasAccountCampaignReviewDecision,
  recordReferralSaasApiAccessVerification,
  recordReferralSaasWebhookTestDispatch,
  recordReferralSaasMembershipInvitationIntent,
  requestReferralSaasAccountCampaignActivation,
  requestReferralSaasAccountFoundationActivation,
  requestReferralSaasAccessProvisioning,
  requestReferralSaasMembershipActivation,
  requestReferralSaasMembershipInvitationDelivery,
  saveReferralSaasIntegrationConfiguration,
  submitReferralSaasAccountCampaignReview,
  updateReferralSaasMembershipInvitationIntent,
  updateReferralSaasAccountCampaignPolicySettings,
  validateReferralSaasIntegrationConfiguration,
  type ReferralSaasAccountCampaignActivationResponse,
  type ReferralSaasAccountCampaignReviewResponse,
  type ReferralSaasAccountCampaignPolicySettingsResponse,
  updateReferralSaasAccountProfile,
  getReferralSaasIntegrationConfiguration,
  getReferralSaasIntegrationExecutionReadiness,
  type ReferralSaasAccountCampaignSetupCreateResponse,
  type ReferralSaasTechnicalSetupReadinessResponse,
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
  | "integrations"
  | "technical"
  | "campaigns"
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
    title: "Campaigns",
    copy: "Set up or review referral campaigns for this customer.",
    letsYou: "Create campaign tests once blockers are clear.",
    route: "campaigns",
    icon: Target,
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
  const [accountActivationResult, setAccountActivationResult] =
    useState<ScopedAccountActivationResult | null>(null);
  const [profileDraft, setProfileDraft] = useState<ProfileDraft | null>(null);
  const [profileResult, setProfileResult] = useState<string | null>(null);
  const [campaignSetupDraft, setCampaignSetupDraft] = useState<CampaignSetupDraft>({
    name: "",
    segment: "Referral acquisition",
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
  const scopeChanged =
    draftExternalTenantRef.trim() !== appliedExternalTenantRef ||
    draftOrganisationRef.trim() !== appliedOrganisationRef;
  const canCheckScope = Boolean(draftExternalTenantRef.trim() && draftOrganisationRef.trim() && scopeChanged);

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
    data: technicalSetupReadiness,
    error: technicalSetupError,
    isLoading: isTechnicalSetupLoading,
  } = useReferralSaasTechnicalSetupReadiness(
    selectedAccount?.accountId || "",
    selectedExternalTenantRef,
    Boolean(accountId && selectedAccount && selectedExternalTenantRef),
    refreshKey,
  );
  const refreshPeopleAccessReadModels = async () => {
    await Promise.all([refetchMembershipPosture(), refetchActivationReadiness()]);
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
      setDeliveryResult(
        `${formatDisplay(response.deliveryRequest.membership.roleFamily)} delivery check returned ${formatDisplay(
          response.deliveryRequest.delivery.status,
        )}. ${response.deliveryRequest.delivery.nextAction} No email was sent, no login was activated, no seat was assigned, and no permissions changed.`,
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
        seatStatus === "SEAT_ASSIGNED" ? "Login seat assigned." : "Login setup not completed yet.";
      setProvisioningResult(
        `${formatDisplay(response.accessProvisioning.membership.roleFamily)}: ${seatOutcome} ${response.accessProvisioning.provisioning.nextAction} No invitation email was sent, no credential was created, no login permission changed, no campaign was activated, and no money moved.`,
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
  const waitingCount = Math.max(0, missingEvidenceCount - blockedCount);
  const overallStatus = formatDisplay(readiness?.overall_status || "go_live_disabled");
  const customerName = selectedAccount?.accountName || formatDisplay(appliedOrganisationRef);
  const selectedCustomerPath = selectedAccount
    ? `/admin/referral-saas/account-maintenance/${encodeURIComponent(selectedAccount.accountId)}`
    : "/admin/referral-saas/account-maintenance";
  const selectedModule = normalizeCustomerModule(customerModule);
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

  function submitCampaignSetup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedName = campaignSetupDraft.name.trim();
    const cleanedSegment = campaignSetupDraft.segment.trim();
    if (!selectedAccount || !selectedExternalTenantRef || !cleanedName || !cleanedSegment) {
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
                        <h2 className="panel-title">Health at a glance</h2>
                        <div className="panel-subtitle">Based on the services we check for this customer.</div>
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
                            ? `Most of ${customerName} is ready. ${formatAreaCount(effectiveBlockedCount || effectiveMissingEvidenceCount, "thing")} needs attention before safe referral testing.`
                            : `${customerName} has no visible setup blocker count. Continue with campaign, link/code, attribution, or reporting tests.`}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="panel">
                    <div className="panel-header">
                      <div>
                        <h2 className="panel-title">Do this next</h2>
                        <div className="panel-subtitle">Highest-value actions for this customer right now.</div>
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
                        Everything opens against {customerName} until you switch customer.
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
                          <div className="customer-function-open">Open page</div>
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
                      <strong>Invite delivery checked.</strong> {deliveryResult}
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
                        <strong>Platform login setup</strong>
                        <p>
                          {missingAccessRoleCount
                            ? "Finish confirming the required customer responsibilities first. "
                            : "Referral work can continue because the required people are confirmed. "}
                          Use platform login setup only when a confirmed person needs to sign in to Amplifi. This is
                          separate from naming who manages the customer.
                        </p>
                        <ul className="people-access-login-purpose" aria-label="Platform login setup purpose">
                          <li>Use it for Amplifi sign-in access.</li>
                          <li>Skip it when the person only owns the relationship outside the platform.</li>
                          <li>Permissions and auth claims remain governed separately.</li>
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
                        {provisioningResult.includes("Seat not assigned")
                          ? "Login setup could not be completed."
                          : "Login setup recorded."}
                      </strong>{" "}
                      {provisioningResult}
                    </div>
                  ) : null}
                  {loginSetupRows.length ? (
                    <div className="people-access-login-setup" aria-label="Optional platform login setup">
                      <div>
                        <strong>Optional login setup</strong>
                        <p>
                          These people are confirmed for customer work. Set up platform login only for people who need
                          to use Amplifi directly.
                        </p>
                      </div>
                      <div className="people-access-login-list">
                        {loginSetupRows.map((item) => {
                          const membershipRef = getValue(item, ["membershipRef"], "");
                          const roleFamily = getValue(item, ["roleFamily"], "");
                          const seatAssigned = item.provisioningReadiness === "SEAT_ASSIGNED";
                          return (
                            <div className="people-access-login-row" key={`${membershipRef}-${roleFamily}`}>
                              <div>
                                <strong>{formatDisplay(getValue(item, ["displayName"], "Named person"))}</strong>
                                <span>
                                  {roleOptionForFamily(roleFamily).label} -{" "}
                                  {seatAssigned ? "Platform login set up" : "Platform login not set up"}
                                </span>
                              </div>
                              <button
                                className="button secondary compact"
                                disabled={seatAssigned || provisioningMutation.isPending}
                                onClick={() => requestAccessProvisioning(membershipRef, roleFamily)}
                                type="button"
                              >
                                {provisioningMutation.isPending
                                  ? "Setting up"
                                  : seatAssigned
                                    ? "Platform login set up"
                                    : "Set up platform login"}
                              </button>
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
                          header: "Delivery check",
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
                                  {deliveryMutation.isPending ? "Checking" : "Check invite delivery"}
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
                    isSaving={campaignSetupMutation.isPending}
                    onChange={updateCampaignSetupDraft}
                    onSubmit={submitCampaignSetup}
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

              {["support", "attribution", "progress"].includes(selectedModule) ? (
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
  const [campaignCode, setCampaignCode] = useState("");
  const [operation, setOperation] = useState<CampaignReadinessOperation>("CONTROL_PLANE_VIEW");
  const [opportunityId, setOpportunityId] = useState("");
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
                  </div>
                );
              },
            },
          ]}
        />

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

function CustomerCampaignSetupCreatePage({
  customerName,
  draft,
  error,
  isSaving,
  onChange,
  onSubmit,
  result,
  selectedAccount,
  selectedCustomerPath,
}: {
  customerName: string;
  draft: CampaignSetupDraft;
  error: unknown;
  isSaving: boolean;
  onChange: (values: Partial<CampaignSetupDraft>) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  result: ReferralSaasAccountCampaignSetupCreateResponse | null;
  selectedAccount?: AccountRegistryItem;
  selectedCustomerPath: string;
}) {
  const savedCampaign = result?.campaignSetup.campaign;
  const canSave = Boolean(selectedAccount && draft.name.trim() && draft.segment.trim());

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

        <form className="form-grid" onSubmit={onSubmit}>
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
            {isSaving ? "Saving campaign setup" : "Save campaign setup"}
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
                A customer-scoped inactive campaign draft. It gives the customer a campaign record to continue with later, without activating or launching anything.
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

function CustomerTechnicalSetupPage({
  account,
  customerName,
  error,
  externalTenantRef,
  isLoading,
  readiness,
}: {
  account?: AccountRegistryItem;
  customerName: string;
  error: unknown;
  externalTenantRef: string;
  isLoading: boolean;
  readiness?: ReferralSaasTechnicalSetupReadinessResponse;
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
  const [configurationMessage, setConfigurationMessage] = useState<string | null>(null);
  const validationMutation = useMutation({
    mutationFn: () =>
      validateReferralSaasIntegrationConfiguration({
        accountRef: account?.accountId || "",
        ...buildIntegrationConfigurationPayload(draft, accountScope, account?.accountId || ""),
      }),
    onSuccess: (response) => {
      setConfigurationMessage(
        `${formatDisplay(response.validation.commandStatus)}. Setup evidence is valid and was not saved.`,
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
      setConfigurationMessage(
        `${formatDisplay(response.integrationConfigurationResult.commandStatus)}. Safe setup evidence saved; no credentials, webhook dispatch, invite delivery, campaign activation, billing, or money movement occurred.`,
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
    },
  });
  const technicalReadiness = readiness?.technicalSetupReadiness;
  const savedConfiguration = configurationQuery.data?.integrationConfiguration || null;
  const executionReadiness = executionReadinessQuery.data?.integrationExecutionReadiness || null;
  const channelSummary = technicalReadiness?.channelSummary;
  const capabilities = technicalReadiness?.capabilities || [];
  const missingCapabilities = capabilities.filter((capability) => capability.status !== "READY");
  const supportedChannels = channelSummary?.supportedChannels || [];
  const executionActions = executionReadiness?.executionActions || [];
  const readyExecutionActions = executionReadiness?.readyActions || [];
  const executionBlockers = executionReadiness?.blockers || [];
  const apiAccessAction = executionActions.find((action) => action.actionRef === "API_ACCESS_VERIFICATION");
  const webhookTestAction = executionActions.find((action) => action.actionRef === "WEBHOOK_TEST_DISPATCH");
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
  const currentStatus = savedConfiguration?.configurationStatus || "NOT_SAVED";
  const canSubmitConfiguration = Boolean(account?.accountId && externalTenantRef);

  return (
    <section className="panel customer-module-page" id="integrations">
      <div className="panel-header">
        <div>
          <div className="page-kicker">Referral SaaS &gt; {customerName} &gt; Integrations</div>
          <h2 className="panel-title">Integrations</h2>
          <div className="panel-subtitle">
            Save safe setup evidence for API, webhook, invite delivery, and referral-message connections. This page does not create credentials or send anything.
          </div>
        </div>
        <StatusBadge label={formatDisplay(currentStatus)} tone={statusTone(currentStatus)} />
      </div>
      <div className="panel-body route-list">
        {isLoading || configurationQuery.isLoading || executionReadinessQuery.isLoading ? (
          <LoadingState label="Checking integration readiness" />
        ) : null}
        {error ? <ErrorPanel error={error} /> : null}
        {configurationQuery.error ? <ErrorPanel error={configurationQuery.error} /> : null}
        {executionReadinessQuery.error ? <ErrorPanel error={executionReadinessQuery.error} /> : null}
        {validationMutation.error ? <ErrorPanel error={validationMutation.error} /> : null}
        {saveMutation.error ? <ErrorPanel error={saveMutation.error} /> : null}
        {apiAccessVerificationMutation.error ? <ErrorPanel error={apiAccessVerificationMutation.error} /> : null}
        {webhookTestDispatchMutation.error ? <ErrorPanel error={webhookTestDispatchMutation.error} /> : null}
        {technicalReadiness ? (
          <>
            <div className="grid-3">
              <KpiCard
                label="Ready providers"
                value={String(channelSummary?.readyCount ?? 0)}
                footnote="Channels currently configured for safe use"
                icon={CheckCircle2}
              />
              <KpiCard
                label="Need setup"
                value={String(channelSummary?.attentionCount ?? 0)}
                footnote="Provider gaps to resolve before live delivery"
                icon={AlertCircle}
              />
              <KpiCard
                label="Supported channels"
                value={String(channelSummary?.count ?? supportedChannels.length)}
                footnote={`${channelSummary?.approvedInviteProviderCount ?? 0} approved for invite delivery`}
                icon={PlugZap}
              />
            </div>

            <div className={`wizard-summary-strip ${missingCapabilities.length ? "warning" : "success"}`}>
              <div>
                <strong>In plain English:</strong>{" "}
                {missingCapabilities.length
                  ? `${customerName} still needs ${formatAreaCount(
                      missingCapabilities.length,
                      "integration setup item",
                    )} before live invite delivery or referral message testing.`
                  : `${customerName} has the provider readiness needed for the checked integration capabilities.`}
              </div>
              <StatusBadge
                label={formatDisplay(technicalReadiness.overallStatus)}
                tone={statusTone(technicalReadiness.overallStatus)}
              />
            </div>

            <div className="wizard-status-card">
              <div>
                <strong>Saved setup evidence</strong>
                <p>
                  {savedConfiguration
                    ? `Last saved ${formatDisplay(savedConfiguration.configurationStatus)} setup by ${savedConfiguration.createdByRef || "an operator"}.`
                    : "No Integrations setup evidence has been saved for this customer yet."}
                </p>
                {savedConfiguration ? (
                  <span className="table-subtext">
                    API: {formatDisplay(String(savedConfiguration.apiEnvironment.environment || "Not set"))}. Webhook:{" "}
                    {String(savedConfiguration.webhookIntent.callbackUrl || "Not set")}. Invite channel:{" "}
                    {formatDisplay(String(asArray(savedConfiguration.messageProviders.channels)[0] || "Not set"))}.
                  </span>
                ) : null}
              </div>
              <StatusBadge label="No secrets stored" tone="success" />
            </div>

            <div className="panel-lite">
              <h3 className="section-heading">1. API access intent</h3>
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

            <div className="panel-lite">
              <h3 className="section-heading">2. Webhook intent</h3>
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

            <div className="panel-lite">
              <h3 className="section-heading">3. Message provider intent</h3>
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
                          referralMessageChannels: toggleListValue(draft.referralMessageChannels, option.value),
                        })
                      }
                      type="checkbox"
                    />
                    <span>{option.label}</span>
                  </label>
                ))}
              </fieldset>
            </div>

            <div className="action-row">
              <button
                className="button secondary"
                disabled={!canSubmitConfiguration || validationMutation.isPending}
                onClick={() => validationMutation.mutate()}
                type="button"
              >
                {validationMutation.isPending ? "Validating" : "Validate setup"}
              </button>
              <button
                className="button primary"
                disabled={!canSubmitConfiguration || saveMutation.isPending}
                onClick={() => saveMutation.mutate()}
                type="button"
              >
                {saveMutation.isPending ? "Saving" : "Save setup evidence"}
              </button>
            </div>
            {configurationMessage ? (
              <div className="success-banner">
                <strong>Integrations setup updated.</strong> {configurationMessage}
              </div>
            ) : null}

            {executionReadiness ? (
              <div className="panel-lite">
                <div className="settings-summary-header">
                  <div>
                    <h3 className="section-heading">4. Live readiness check</h3>
                    <p>
                      Shows whether this customer can move from saved setup evidence into governed API, webhook,
                      provider, or credential checks. It does not run those checks.
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
                    <div className="wizard-status-card" key={action.actionRef}>
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
                            : "Record API access check"}
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
                            : "Record webhook test evidence"}
                        </button>
                      ) : null}
                    </div>
                  ))}
                </div>
                <div className="wizard-status-card">
                  <div>
                    <strong>Still separate</strong>
                    <p>
                      Credential creation, live webhook dispatch, invite delivery, referral-message delivery, auth
                      changes, campaign activation, billing, and money movement stay in later governed workflows.
                    </p>
                  </div>
                  <StatusBadge label="Read only" tone="info" />
                </div>
              </div>
            ) : null}

            <div className="route-list">
              {capabilities.map((capability) => (
                <div className="wizard-status-card" key={capability.code}>
                  <div>
                    <strong>{capability.label}</strong>
                    <p>{capability.nextAction}</p>
                    <span className="table-subtext">
                      Needs {formatList(capability.requiredChannels)}. Ready:{" "}
                      {formatList(capability.readyChannels)}. Missing: {formatList(capability.missingChannels)}.
                      {capability.missingApprovalChannels.length
                        ? ` Approval needed: ${formatList(capability.missingApprovalChannels)}.`
                        : ""}
                      {capability.approvedProviderRefs.length
                        ? ` Approved provider: ${formatList(capability.approvedProviderRefs)}.`
                        : ""}
                    </span>
                  </div>
                  <StatusBadge label={formatDisplay(capability.status)} tone={statusTone(capability.status)} />
                </div>
              ))}
            </div>

            <div className="wizard-status-card">
              <div>
                <strong>What this page will not do</strong>
                <p>
                  No credentials are created, no webhook is dispatched, no invite is sent, no login is activated, no seat is assigned, no campaign is launched, and no money moves.
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
  const report = asRecord(reportQuery.data?.report);
  const metrics = asArray(getNestedValue(report, ["metrics"], []));
  const rows = asArray(getNestedValue(report, ["rows"], metrics));
  const warnings = asArray(getNestedValue(report, ["warnings"], []));
  const preview = asRecord(previewMutation.data?.export_preview);
  const previewRows = asArray(getNestedValue(preview, ["sample_rows"], getNestedValue(preview, ["rows"], [])));
  const activeReport = customerReportOptions.find((option) => option.value === reportType) || customerReportOptions[0];

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

        <div className="grid-2">
          <div className="panel-lite">
            <h3 className="section-heading">1. Choose report</h3>
            <div className="route-list">
              {customerReportOptions.map((option) => (
                <button
                  className={`route-card ${option.value === reportType ? "selected" : ""}`}
                  key={option.value}
                  onClick={() => setReportType(option.value)}
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
              <select onChange={(event) => setCampaignCode(event.target.value)} value={campaignCode}>
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
            footnote="No file, storage, or delivery is created"
            icon={Download}
            label="Export mode"
            value="Preview"
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
  hasSeatProvisioningWork,
}: {
  blockedCount: number;
  missingEvidenceCount: number;
  hasAcceptedRequiredAccess: boolean;
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
    return "Login setup separate";
  }
  if (status === "READY_TO_PROVISION_SEAT") {
    return "Ready for login setup";
  }
  if (status === "SEAT_ASSIGNED") {
    return "Login seat assigned";
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
    return { label: "Login seat assigned", tone: "success" as StatusTone };
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
    return "Login seat is assigned. Login permissions remain in the governed auth workflow.";
  }
  if (membershipStatus === "ACTIVE" && provisioningReadiness === "READY_TO_PROVISION_SEAT") {
    return "Confirmed for customer work. Set up platform login later only if this person must sign in.";
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

function inviteDeliveryProviderRef(readiness?: ReferralSaasTechnicalSetupReadinessResponse) {
  const inviteCapability = readiness?.technicalSetupReadiness.capabilities.find(
    (capability) => capability.code === "MEMBERSHIP_INVITE_DELIVERY",
  );
  return inviteCapability?.approvedProviderRefs[0] || "";
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

function integrationExecutionActionLabel(actionRef: string, fallback: string) {
  if (actionRef === "WEBHOOK_TEST_DISPATCH") {
    return "Record webhook test evidence";
  }
  return fallback;
}

function integrationExecutionActionNextStep(actionRef: string, fallback: string) {
  if (actionRef === "WEBHOOK_TEST_DISPATCH") {
    return "Record governed webhook callback test evidence for this customer.";
  }
  return fallback;
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

function formatCampaignLabel(value: unknown): string {
  return formatDisplay(value)
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b[a-z]/g, (letter) => letter.toUpperCase());
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
      "integrations",
      "technical",
      "campaigns",
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

function newAccessCreateAttemptKey() {
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
