export const queryKeys = {
  adminAudit: (summaryHours: number, entryLimit: number, refreshKey = 0) =>
    ["admin", "audit", summaryHours, entryLimit, refreshKey] as const,
  backendSession: (refreshKey = 0) =>
    ["auth", "backend-session", refreshKey] as const,
  adminExperience: (tenantCode: string, outcomeLimit: number) =>
    ["experience", "admin", tenantCode, outcomeLimit] as const,
  healthReadiness: (refreshKey = 0) =>
    ["admin", "health-readiness", refreshKey] as const,
  healthConnection: (refreshKey = 0) =>
    ["layout", "health-connection", refreshKey] as const,
  adminChannelOperations: (status: string, refreshKey = 0) =>
    ["admin", "channel-operations", status, refreshKey] as const,
  referralSaasAccountSetup: (
    externalTenantRef: string,
    organisationRef: string,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "account-setup",
      externalTenantRef,
      organisationRef,
      refreshKey,
    ] as const,
  referralSaasAccountMaintenance: (
    externalTenantRef: string,
    organisationRef: string,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "account-maintenance",
      externalTenantRef,
      organisationRef,
      refreshKey,
    ] as const,
  referralSaasAccountDraftSelector: (
    externalTenantRef: string,
    organisationRef: string,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "account-draft-selector",
      externalTenantRef,
      organisationRef,
      refreshKey,
    ] as const,
  referralSaasAccountRegistry: (limit: number, refreshKey = 0) =>
    ["referral-saas", "account-registry", limit, refreshKey] as const,
  referralSaasOperatorSupportQueue: (
    status: string,
    priority: string,
    category: string,
    accountRef: string,
    sourceSurface: string,
    assigneeRef: string,
    limit: number,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "operator-support-queue",
      status,
      priority,
      category,
      accountRef,
      sourceSurface,
      assigneeRef,
      limit,
      refreshKey,
    ] as const,
  referralSaasAccountResolver: (
    refType: string,
    externalRef: string,
    context: string,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "account-resolver",
      refType,
      externalRef,
      context,
      refreshKey,
    ] as const,
  referralSaasAccountMembershipPosture: (
    refType: string,
    externalRef: string,
    context: string,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "account-membership-posture",
      refType,
      externalRef,
      context,
      refreshKey,
    ] as const,
  referralSaasMembershipActivationReadiness: (
    accountRef: string,
    refType: string,
    externalRef: string,
    context: string,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "membership-activation-readiness",
      accountRef,
      refType,
      externalRef,
      context,
      refreshKey,
    ] as const,
  referralSaasLoginCompletionReadiness: (
    accountRef: string,
    membershipRefs: string,
    refType: string,
    externalRef: string,
    context: string,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "login-completion-readiness",
      accountRef,
      membershipRefs,
      refType,
      externalRef,
      context,
      refreshKey,
    ] as const,
  referralSaasIdentityLoginReconciliation: (
    accountRef: string,
    refType: string,
    externalRef: string,
    context: string,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "identity-login-reconciliation",
      accountRef,
      refType,
      externalRef,
      context,
      refreshKey,
    ] as const,
  referralSaasTechnicalSetupReadiness: (
    accountRef: string,
    refType: string,
    externalRef: string,
    context: string,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "technical-setup-readiness",
      accountRef,
      refType,
      externalRef,
      context,
      refreshKey,
    ] as const,
  referralSaasCommercialEntitlement: (
    accountRef: string,
    refType: string,
    externalRef: string,
    context: string,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "commercial-entitlement",
      accountRef,
      refType,
      externalRef,
      context,
      refreshKey,
    ] as const,
  referralSaasProductionActivation: (
    accountRef: string,
    refType: string,
    externalRef: string,
    context: string,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "production-activation",
      accountRef,
      refType,
      externalRef,
      context,
      refreshKey,
    ] as const,
  referralSaasAccountCampaignList: (
    accountRef: string,
    refType: string,
    externalRef: string,
    context: string,
    limit: number,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "account-campaign-list",
      accountRef,
      refType,
      externalRef,
      context,
      limit,
      refreshKey,
    ] as const,
  referralSaasAccountReferralList: (
    accountRef: string,
    refType: string,
    externalRef: string,
    context: string,
    limit: number,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "account-referral-list",
      accountRef,
      refType,
      externalRef,
      context,
      limit,
      refreshKey,
    ] as const,
  referralSaasAccountReferralDetail: (
    accountRef: string,
    referralTrackId: string,
    refType: string,
    externalRef: string,
    context: string,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "account-referral-detail",
      accountRef,
      referralTrackId,
      refType,
      externalRef,
      context,
      refreshKey,
    ] as const,
  referralSaasAccountReferrerList: (
    accountRef: string,
    refType: string,
    externalRef: string,
    context: string,
    limit: number,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "account-referrer-list",
      accountRef,
      refType,
      externalRef,
      context,
      limit,
      refreshKey,
    ] as const,
  referralSaasAccountReferrerDetail: (
    accountRef: string,
    safeReferrerKey: string,
    refType: string,
    externalRef: string,
    context: string,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "account-referrer-detail",
      accountRef,
      safeReferrerKey,
      refType,
      externalRef,
      context,
      refreshKey,
    ] as const,
  referralSaasReport: (reportType: string, tenantCode: string, refreshKey = 0) =>
    ["referral-saas", "report", reportType, tenantCode, refreshKey] as const,
  referralSaasCampaignReadiness: (
    campaignCode: string,
    tenantCode: string,
    operation: string,
    opportunityId: string,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "campaign-readiness",
      campaignCode,
      tenantCode,
      operation,
      opportunityId,
      refreshKey,
    ] as const,
  referralSaasAccountCampaignReadiness: (
    accountRef: string,
    campaignCode: string,
    refType: string,
    externalRef: string,
    operation: string,
    context: string,
    opportunityId: string,
    refreshKey = 0,
  ) =>
    [
      "referral-saas",
      "account-campaign-readiness",
      accountRef,
      campaignCode,
      refType,
      externalRef,
      operation,
      context,
      opportunityId,
      refreshKey,
    ] as const,
  partnerIntegrationWorkspace: (refreshKey = 0) =>
    ["partner", "integration-workspace", refreshKey] as const,
  consumerExperience: (
    tenantCode: string | undefined,
    referrerUcn: string,
    referralTrackId: string | undefined,
    leaderboardCode: string,
    includeInsuranceProof: boolean,
  ) =>
    [
      "experience",
      "consumer",
      tenantCode || "",
      referrerUcn,
      referralTrackId || "",
      leaderboardCode,
      includeInsuranceProof,
    ] as const,
  distributorExperience: (
    tenantCode: string,
    distributorCode: string,
    limit: number,
  ) =>
    ["experience", "distributor", tenantCode, distributorCode, limit] as const,
  distributorOptions: (tenantCode: string, refreshKey = 0) =>
    ["distribution", "distributor-options", tenantCode, refreshKey] as const,
  distributorWalletLedger: (
    tenantCode: string,
    distributorCode: string,
    walletId: string,
    refreshKey = 0,
  ) =>
    [
      "distribution",
      "wallet-ledger",
      tenantCode,
      distributorCode,
      walletId,
      refreshKey,
    ] as const,
  distributorWalletWorkspace: (
    tenantCode: string,
    distributorCode: string,
    refreshKey = 0,
  ) =>
    [
      "distribution",
      "wallet-workspace",
      tenantCode,
      distributorCode,
      refreshKey,
    ] as const,
  sponsorExperience: (
    tenantCode: string,
    sponsorCode: string,
    currency: string,
    limit: number,
  ) =>
    [
      "experience",
      "sponsor",
      tenantCode,
      sponsorCode,
      currency,
      limit,
    ] as const,
};
