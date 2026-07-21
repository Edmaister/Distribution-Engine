import {
  AlertCircle,
  BarChart3,
  Building2,
  CheckCircle2,
  Link as LinkIcon,
  ListChecks,
  Search,
  ShieldCheck,
  Target,
  Users,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";

import {
  useReferralSaasAccountDraftSelector,
  useReferralSaasAccountMaintenanceState,
  useReferralSaasAccountMembershipPosture,
  useReferralSaasMembershipActivationReadiness,
  useReferralSaasAccountRegistry,
} from "../../api/referralSaasAccountQueries";
import {
  recordReferralSaasMembershipInvitationIntent,
  updateReferralSaasAccountProfile,
} from "../../api/endpoints/referralSaasAccounts";
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
  const { accountId, customerModule } = useParams<{ accountId?: string; customerModule?: string }>();
  const { refreshKey } = useRefreshContext();
  const [draftExternalTenantRef, setDraftExternalTenantRef] = useState(defaultExternalTenantRef);
  const [draftOrganisationRef, setDraftOrganisationRef] = useState(defaultOrganisationRef);
  const [appliedExternalTenantRef, setAppliedExternalTenantRef] = useState(defaultExternalTenantRef);
  const [appliedOrganisationRef, setAppliedOrganisationRef] = useState(defaultOrganisationRef);
  const [selectedOperatingMarket, setSelectedOperatingMarket] = useState(defaultOperatingMarket);
  const [pendingAccountId, setPendingAccountId] = useState<string | null>(null);
  const [accessDisplayName, setAccessDisplayName] = useState("");
  const [accessEmail, setAccessEmail] = useState("");
  const [accessRoleLabel, setAccessRoleLabel] = useState(accessRoleOptions[0].label);
  const [accessResult, setAccessResult] = useState<string | null>(null);
  const [profileDraft, setProfileDraft] = useState<ProfileDraft | null>(null);
  const [profileResult, setProfileResult] = useState<string | null>(null);
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
  const accessMutation = useMutation({
    mutationFn: recordReferralSaasMembershipInvitationIntent,
    onSuccess: (response) => {
      const savedRole =
        accessRoleOptions.find(
          (option) => option.roleFamily === response.invitation.membership.roleFamily,
        )?.label || formatDisplay(response.invitation.membership.roleFamily);
      setAccessResult(
        `${savedRole} access recorded as ${formatDisplay(
          response.invitation.membership.status,
        )}. No invitation email, login activation, seat assignment, or auth claim change was performed.`,
      );
      void refetchMembershipPosture();
      void refetchActivationReadiness();
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
  const doNext = getCustomerNextActions(blockedCount, missingEvidenceCount);
  const selectedCustomerPath = selectedAccount
    ? `/admin/referral-saas/account-maintenance/${encodeURIComponent(selectedAccount.accountId)}`
    : "/admin/referral-saas/account-maintenance";
  const selectedModule = normalizeCustomerModule(customerModule);
  const customerQuery = `?external_tenant_ref=${encodeURIComponent(
    selectedExternalTenantRef,
  )}&organisation_ref=${encodeURIComponent(selectedOrganisationRef)}`;
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

  function submitAccessIntent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedEmail = accessEmail.trim().toLowerCase();
    if (!selectedAccount || !selectedExternalTenantRef || !isValidEmail(cleanedEmail)) {
      return;
    }
    const selectedRole = accessRoleOptions.find((option) => option.label === accessRoleLabel) || accessRoleOptions[0];
    accessMutation.mutate({
      accountRef: selectedAccount.accountId,
      accountScope: {
        refType: "external_tenant_ref",
        externalRef: selectedExternalTenantRef,
        context: "setup",
      },
      actor: {
        actorType: "USER",
        subject: cleanedEmail,
        displayName: accessDisplayName.trim() || cleanedEmail,
      },
      membership: {
        roleFamily: selectedRole.roleFamily,
        permissionSet: selectedRole.permissionSet,
        tenantScope: "PRIMARY_ACCOUNT_TENANT",
      },
      reasonCode: "CUSTOMER_PROFILE_ACCESS_MAINTENANCE",
      correlationId: `customer-profile-access-${selectedAccount.accountId}`,
      idempotencyKey: `customer-profile-access-${selectedAccount.accountId}-${cleanedEmail}-${selectedRole.roleFamily}`
        .toLowerCase()
        .replace(/[^a-z0-9-]+/g, "-"),
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
              <span>{operatingMarketFromAccount(selectedAccount).name}</span>
              <StatusBadge label={formatDisplay(selectedAccount.accountStatus)} tone="success" />
              <span>{selectedAccount.accountCode}</span>
              <span>
                {selectedExternalTenantRef} / {selectedOrganisationRef}
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
                    <div className="panel-subtitle">Only accounts in {selectedOperatingMarket}.</div>
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
                        return (
                          <button
                            className={`customer-selector-card ${pending || opened ? "selected" : ""}`}
                            disabled={!canSelectAccount}
                            key={account.accountId}
                            onClick={() => stageAccount(account)}
                            type="button"
                          >
                            <span className="customer-selector-title">{account.accountName}</span>
                            <span className="customer-selector-meta">
                              {externalTenantRef || "Missing customer ref"} / {organisationRef || "Missing organisation ref"}
                            </span>
                            <span className="customer-selector-count">{account.accountCode}</span>
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
                        <div className="customer-health-card good">
                          <strong>{readyCount}</strong>
                          <span>Looking fine</span>
                        </div>
                        <div className="customer-health-card bad">
                          <strong>{blockedCount}</strong>
                          <span>Stopping you</span>
                        </div>
                        <div className="customer-health-card wait">
                          <strong>{waitingCount}</strong>
                          <span>Can wait</span>
                        </div>
                      </div>
                      <div className={`wizard-summary-strip ${blockedCount || missingEvidenceCount ? "warning" : "success"}`}>
                        <div>
                          <strong>In plain English:</strong>{" "}
                          {blockedCount || missingEvidenceCount
                            ? `Most of ${customerName} is ready. ${formatAreaCount(blockedCount || missingEvidenceCount, "thing")} needs attention before safe referral testing.`
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
                      const Icon = item.icon;
                      const href = buildCustomerModuleRoute(selectedCustomerPath, item.route, customerQuery);
                      return (
                        <Link
                          className="customer-function-card"
                          key={item.title}
                          to={href}
                        >
                          <div className="customer-function-card-header">
                            <span className="customer-function-title">
                              <Icon size={16} />
                              {item.title}
                            </span>
                            <StatusBadge label={item.status} tone={item.tone} />
                          </div>
                          <p>{item.copy}</p>
                          <div className="customer-function-help">
                            <strong>This lets you:</strong> {item.letsYou}
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
                    <KpiCard label="Roles still missing" value={blockedCount ? "1" : "0"} footnote="Owner or campaign manager still needs attention" icon={AlertCircle} />
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
                      Add who should manage this customer from inside the selected customer profile.
                    </div>
                  </div>
                  <StatusBadge label="Intent only" tone="info" />
                </div>
                <div className="panel-body route-list">
                  <div className="grid-3">
                    <KpiCard label="Active users" value={String(membershipPosture?.membershipPosture.activeCount ?? 0)} footnote="Activation remains a future bounded workflow" icon={Users} />
                    <KpiCard label="Named or invited" value={String(membershipPosture?.membershipPosture.invitedCount ?? 0)} footnote="Invitation intent is stored without email delivery" icon={CheckCircle2} />
                    <KpiCard label="Roles still missing" value={blockedCount ? "1" : "0"} footnote="Add owner and campaign manager intent here" icon={AlertCircle} />
                  </div>
                  <form className="account-setup-scope-form" onSubmit={submitAccessIntent}>
                    <div className="wizard-status-card">
                      <div>
                        <strong>Add access intent</strong>
                        <p>
                          This records who should manage {customerName}. It does not send an email, activate login, assign a seat, or change auth permissions.
                        </p>
                      </div>
                      <StatusBadge label="No live invite" tone="warning" />
                    </div>
                    <label className="field">
                      <span>Person name</span>
                      <input
                        className="input"
                        onChange={(event) => setAccessDisplayName(event.target.value)}
                        placeholder="Example: Referral operations owner"
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
                      <span>Access responsibility</span>
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
                    <button className="button" disabled={!isValidEmail(accessEmail.trim()) || accessMutation.isPending} type="submit">
                      {accessMutation.isPending ? "Recording access intent" : "Record access intent"}
                    </button>
                  </form>
                  {accessMutation.error ? <ErrorPanel error={accessMutation.error} /> : null}
                  {accessResult ? (
                    <div className="wizard-summary-strip success">
                      <strong>Access intent saved.</strong> {accessResult}
                    </div>
                  ) : null}
                  {activationReadiness ? (
                    <div className="wizard-status-card">
                      <div>
                        <strong>Access activation readiness</strong>
                        <p>
                          {accessReadinessSummary(
                            activationReadiness.activationReadiness.overallStatus,
                            activationReadiness.activationReadiness.missingRoleFamilies.length,
                          )}
                        </p>
                        <span className="table-subtext">
                          This is a read-only check. It does not send invites, activate login, assign seats, or change permissions.
                        </span>
                      </div>
                      <StatusBadge
                        label={formatDisplay(activationReadiness.activationReadiness.overallStatus)}
                        tone={statusTone(activationReadiness.activationReadiness.overallStatus)}
                      />
                    </div>
                  ) : null}
                  {activationReadiness ? (
                    <div className="grid-3">
                      <KpiCard
                        label="Ready to invite"
                        value={String(activationReadiness.activationReadiness.deliveryReadyCount)}
                        footnote="People that can move to invite delivery later"
                        icon={CheckCircle2}
                      />
                      <KpiCard
                        label="Ready to activate"
                        value={String(activationReadiness.activationReadiness.activationReadyCount)}
                        footnote="People with no activation blocker"
                        icon={ShieldCheck}
                      />
                      <KpiCard
                        label="Responsibilities missing"
                        value={String(activationReadiness.activationReadiness.missingRoleFamilies.length)}
                        footnote="Owner and campaign manager are required"
                        icon={AlertCircle}
                      />
                    </div>
                  ) : null}
                  {activationReadiness?.activationReadiness.missingRoleFamilies.length ? (
                    <div className="wizard-summary-strip warning">
                      <strong>Still needed:</strong>{" "}
                      {activationReadiness.activationReadiness.missingRoleFamilies
                        .map((roleFamily) => formatDisplay(roleFamily))
                        .join(", ")}
                      .
                    </div>
                  ) : null}
                  {activationReadiness?.activationReadiness.items.length ? (
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
                      ]}
                    />
                  ) : null}
                  {(membershipPosture?.membershipPosture.memberships || []).length ? (
                    <DataTable
                      rows={membershipPosture?.membershipPosture.memberships || []}
                      emptyText="No people or access intent has been recorded for this customer yet."
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
                          key: "roleFamily",
                          header: "Access responsibility",
                          render: (row) => formatDisplay(getValue(row, ["roleFamily"], "Role")),
                        },
                        {
                          key: "status",
                          header: "Status",
                          render: (row) => (
                            <StatusBadge
                              label={formatDisplay(getValue(row, ["status"], "Status"))}
                              tone={statusTone(getValue(row, ["status"], "Status"))}
                            />
                          ),
                        },
                        {
                          key: "deliveryStatus",
                          header: "Invite delivery",
                          render: (row) => formatDisplay(getValue(row, ["deliveryStatus"], "Delivery not configured")),
                        },
                      ]}
                    />
                  ) : null}
                </div>
              </section>
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

              {["campaigns", "links", "reports", "support", "attribution", "progress"].includes(selectedModule) ? (
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

function getCustomerNextActions(blockedCount: number, missingEvidenceCount: number) {
  if (blockedCount > 0 || missingEvidenceCount > 0) {
    return [
      {
        title: "Add who can manage this account",
        copy: "Complete owner and campaign manager setup for day-to-day referral work.",
        priority: "First",
        route: "people",
        tone: "warning" as StatusTone,
      },
      {
        title: "Open Campaigns",
        copy: "Account setup is far enough to set up or review a campaign.",
        priority: "Next",
        route: "campaigns",
        tone: "info" as StatusTone,
      },
      {
        title: "Finish reporting setup",
        copy: "Useful for performance views, not a hard stop for first testing.",
        priority: "Later",
        route: "reports",
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
    return "The required customer access responsibilities are active.";
  }
  if (missingRoleCount > 0) {
    return `${formatAreaCount(missingRoleCount, "responsibility")} still needs to be named for this customer.`;
  }
  return "People are named, but invite delivery or login activation is not ready yet.";
}

function buildCustomerModuleRoute(selectedCustomerPath: string, route: string, customerQuery: string) {
  if (isCustomerModule(route)) {
    return `${selectedCustomerPath}/${route}`;
  }
  return `${route}${customerQuery}`;
}

function normalizeCustomerModule(value: string | undefined): CustomerModule {
  return isCustomerModule(value) ? value : "home";
}

function isCustomerModule(value: string | undefined): value is CustomerModule {
  return [
    "home",
    "health",
    "settings",
    "people",
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
