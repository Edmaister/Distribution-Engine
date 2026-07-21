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
