import { useQuery } from "@tanstack/react-query";

import { getAdminOnboardingDrafts, getAdminOnboardingState } from "./endpoints/adminOnboarding";
import {
  getReferralSaasAccountReferral,
  getReferralSaasAccountReferralAttribution,
  getReferralSaasAccountReferrer,
  getReferralSaasAccountCampaignAttribution,
  listReferralSaasAccountCampaigns,
  listReferralSaasAccountReferrals,
  listReferralSaasAccountReferrers,
  getReferralSaasAccountCampaignReadiness,
  listReferralSaasAccountJourneyVersions,
  getReferralSaasCommercialEntitlement,
  getReferralSaasIdentityLoginReconciliation,
  getReferralSaasProductionActivation,
  getReferralSaasLoginCompletionReadiness,
  getReferralSaasMembershipActivationReadiness,
  getReferralSaasAccountMembershipPosture,
  getReferralSaasOperationsOverview,
  getReferralSaasTechnicalSetupReadiness,
  listReferralSaasAccounts,
  listReferralSaasOperatorSupportQueue,
  resolveReferralSaasAccount,
} from "./endpoints/referralSaasAccounts";
import type { CampaignReadinessOperation } from "./endpoints/adminCampaignReadiness";
import { queryKeys } from "./queryKeys";

export function useReferralSaasAccountSetupState(
  externalTenantRef: string,
  organisationRef: string,
  refreshKey = 0,
) {
  const cleanedExternalTenantRef = externalTenantRef.trim();
  const cleanedOrganisationRef = organisationRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasAccountSetup(
      cleanedExternalTenantRef,
      cleanedOrganisationRef,
      refreshKey,
    ),
    queryFn: () =>
      getAdminOnboardingState({
        external_tenant_ref: cleanedExternalTenantRef,
        organisation_ref: cleanedOrganisationRef,
      }),
    enabled: Boolean(cleanedExternalTenantRef && cleanedOrganisationRef),
  });
}

export function useReferralSaasAccountMaintenanceState(
  externalTenantRef: string,
  organisationRef: string,
  refreshKey = 0,
) {
  const cleanedExternalTenantRef = externalTenantRef.trim();
  const cleanedOrganisationRef = organisationRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasAccountMaintenance(
      cleanedExternalTenantRef,
      cleanedOrganisationRef,
      refreshKey,
    ),
    queryFn: () =>
      getAdminOnboardingState({
        external_tenant_ref: cleanedExternalTenantRef,
        organisation_ref: cleanedOrganisationRef,
      }),
    enabled: Boolean(cleanedExternalTenantRef && cleanedOrganisationRef),
  });
}

export function useReferralSaasAccountDraftSelector(
  externalTenantRef: string,
  organisationRef: string,
  refreshKey = 0,
) {
  const cleanedExternalTenantRef = externalTenantRef.trim();
  const cleanedOrganisationRef = organisationRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasAccountDraftSelector(
      cleanedExternalTenantRef,
      cleanedOrganisationRef,
      refreshKey,
    ),
    queryFn: () =>
      getAdminOnboardingDrafts({
        external_tenant_ref: cleanedExternalTenantRef,
        organisation_ref: cleanedOrganisationRef,
        limit: 10,
      }),
    enabled: Boolean(cleanedExternalTenantRef && cleanedOrganisationRef),
  });
}

export function useReferralSaasAccountRegistry(limit = 50, refreshKey = 0) {
  return useQuery({
    queryKey: queryKeys.referralSaasAccountRegistry(limit, refreshKey),
    queryFn: () => listReferralSaasAccounts(limit),
  });
}

export function useReferralSaasOperationsOverview(limit = 8, refreshKey = 0) {
  return useQuery({
    queryKey: queryKeys.referralSaasOperationsOverview(limit, refreshKey),
    queryFn: () => getReferralSaasOperationsOverview({ limit }),
    retry: false,
  });
}

export type ReferralSaasOperationsQueueFilters = {
  priority?: string;
  jurisdiction?: string;
  customer?: string;
  category?: string;
  status?: string;
  owner?: string;
  workType?: string;
  serviceTarget?: string;
  sort?: string;
  limit: number;
  cursor?: string;
};

export function useReferralSaasOperationsQueue(
  filters: ReferralSaasOperationsQueueFilters,
  refreshKey = 0,
) {
  return useQuery({
    queryKey: queryKeys.referralSaasOperationsQueue(filters, refreshKey),
    queryFn: () => getReferralSaasOperationsOverview(filters),
    retry: false,
  });
}

export function useReferralSaasOperatorSupportQueue(
  filters: {
    status?: string;
    priority?: string;
    category?: string;
    accountRef?: string;
    sourceSurface?: string;
    assigneeRef?: string;
    limit?: number;
  },
  refreshKey = 0,
) {
  const status = filters.status?.trim() || "";
  const priority = filters.priority?.trim() || "";
  const category = filters.category?.trim() || "";
  const accountRef = filters.accountRef?.trim() || "";
  const sourceSurface = filters.sourceSurface?.trim() || "";
  const assigneeRef = filters.assigneeRef?.trim() || "";
  const limit = filters.limit || 50;

  return useQuery({
    queryKey: queryKeys.referralSaasOperatorSupportQueue(
      status,
      priority,
      category,
      accountRef,
      sourceSurface,
      assigneeRef,
      limit,
      refreshKey,
    ),
    queryFn: () =>
      listReferralSaasOperatorSupportQueue({
        status,
        priority,
        category,
        accountRef,
        sourceSurface,
        assigneeRef,
        limit,
      }),
    retry: false,
  });
}

export function useReferralSaasAccountResolver(
  externalTenantRef: string,
  refreshKey = 0,
) {
  const cleanedExternalTenantRef = externalTenantRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasAccountResolver(
      "external_tenant_ref",
      cleanedExternalTenantRef,
      "setup",
      refreshKey,
    ),
    queryFn: () =>
      resolveReferralSaasAccount({
        refType: "external_tenant_ref",
        externalRef: cleanedExternalTenantRef,
        context: "setup",
      }),
    enabled: Boolean(cleanedExternalTenantRef),
    retry: false,
  });
}

export function useReferralSaasAccountMembershipPosture(
  externalTenantRef: string,
  enabled: boolean,
  refreshKey = 0,
) {
  const cleanedExternalTenantRef = externalTenantRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasAccountMembershipPosture(
      "external_tenant_ref",
      cleanedExternalTenantRef,
      "setup",
      refreshKey,
    ),
    queryFn: () =>
      getReferralSaasAccountMembershipPosture({
        refType: "external_tenant_ref",
        externalRef: cleanedExternalTenantRef,
        context: "setup",
      }),
    enabled: Boolean(enabled && cleanedExternalTenantRef),
    retry: false,
  });
}

export function useReferralSaasMembershipActivationReadiness(
  accountRef: string,
  externalTenantRef: string,
  enabled: boolean,
  refreshKey = 0,
) {
  const cleanedAccountRef = accountRef.trim();
  const cleanedExternalTenantRef = externalTenantRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasMembershipActivationReadiness(
      cleanedAccountRef,
      "external_tenant_ref",
      cleanedExternalTenantRef,
      "setup",
      refreshKey,
    ),
    queryFn: () =>
      getReferralSaasMembershipActivationReadiness({
        accountRef: cleanedAccountRef,
        refType: "external_tenant_ref",
        externalRef: cleanedExternalTenantRef,
        context: "setup",
      }),
    enabled: Boolean(enabled && cleanedAccountRef && cleanedExternalTenantRef),
    retry: false,
  });
}

export function useReferralSaasLoginCompletionReadiness(
  accountRef: string,
  membershipRefs: string[],
  externalTenantRef: string,
  enabled: boolean,
  refreshKey = 0,
) {
  const cleanedAccountRef = accountRef.trim();
  const cleanedExternalTenantRef = externalTenantRef.trim();
  const cleanedMembershipRefs = membershipRefs.map((membershipRef) => membershipRef.trim()).filter(Boolean);

  return useQuery({
    queryKey: queryKeys.referralSaasLoginCompletionReadiness(
      cleanedAccountRef,
      cleanedMembershipRefs.join("|"),
      "external_tenant_ref",
      cleanedExternalTenantRef,
      "setup",
      refreshKey,
    ),
    queryFn: () =>
      Promise.all(
        cleanedMembershipRefs.map((membershipRef) =>
          getReferralSaasLoginCompletionReadiness({
            accountRef: cleanedAccountRef,
            membershipRef,
            refType: "external_tenant_ref",
            externalRef: cleanedExternalTenantRef,
            context: "setup",
          }),
        ),
      ),
    enabled: Boolean(enabled && cleanedAccountRef && cleanedExternalTenantRef && cleanedMembershipRefs.length),
    retry: false,
  });
}

export function useReferralSaasIdentityLoginReconciliation(
  accountRef: string,
  externalTenantRef: string,
  enabled: boolean,
  refreshKey = 0,
) {
  const cleanedAccountRef = accountRef.trim();
  const cleanedExternalTenantRef = externalTenantRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasIdentityLoginReconciliation(
      cleanedAccountRef,
      "external_tenant_ref",
      cleanedExternalTenantRef,
      "setup",
      refreshKey,
    ),
    queryFn: () =>
      getReferralSaasIdentityLoginReconciliation({
        accountRef: cleanedAccountRef,
        refType: "external_tenant_ref",
        externalRef: cleanedExternalTenantRef,
        context: "setup",
      }),
    enabled: Boolean(enabled && cleanedAccountRef && cleanedExternalTenantRef),
    retry: false,
  });
}

export function useReferralSaasTechnicalSetupReadiness(
  accountRef: string,
  externalTenantRef: string,
  enabled: boolean,
  refreshKey = 0,
) {
  const cleanedAccountRef = accountRef.trim();
  const cleanedExternalTenantRef = externalTenantRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasTechnicalSetupReadiness(
      cleanedAccountRef,
      "external_tenant_ref",
      cleanedExternalTenantRef,
      "setup",
      refreshKey,
    ),
    queryFn: () =>
      getReferralSaasTechnicalSetupReadiness({
        accountRef: cleanedAccountRef,
        refType: "external_tenant_ref",
        externalRef: cleanedExternalTenantRef,
        context: "setup",
      }),
    enabled: Boolean(enabled && cleanedAccountRef && cleanedExternalTenantRef),
    retry: false,
  });
}

export function useReferralSaasCommercialEntitlement(
  accountRef: string,
  externalTenantRef: string,
  enabled: boolean,
  refreshKey = 0,
) {
  const cleanedAccountRef = accountRef.trim();
  const cleanedExternalTenantRef = externalTenantRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasCommercialEntitlement(
      cleanedAccountRef,
      "external_tenant_ref",
      cleanedExternalTenantRef,
      "setup",
      refreshKey,
    ),
    queryFn: () =>
      getReferralSaasCommercialEntitlement({
        accountRef: cleanedAccountRef,
        refType: "external_tenant_ref",
        externalRef: cleanedExternalTenantRef,
        context: "setup",
      }),
    enabled: Boolean(enabled && cleanedAccountRef && cleanedExternalTenantRef),
    retry: false,
  });
}

export function useReferralSaasProductionActivation(
  accountRef: string,
  externalTenantRef: string,
  enabled: boolean,
  refreshKey = 0,
) {
  const cleanedAccountRef = accountRef.trim();
  const cleanedExternalTenantRef = externalTenantRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasProductionActivation(
      cleanedAccountRef,
      "external_tenant_ref",
      cleanedExternalTenantRef,
      "setup",
      refreshKey,
    ),
    queryFn: () =>
      getReferralSaasProductionActivation({
        accountRef: cleanedAccountRef,
        refType: "external_tenant_ref",
        externalRef: cleanedExternalTenantRef,
        context: "setup",
      }),
    enabled: Boolean(enabled && cleanedAccountRef && cleanedExternalTenantRef),
    retry: false,
  });
}

export function useReferralSaasAccountCampaignList(
  accountRef: string,
  externalTenantRef: string,
  enabled: boolean,
  refreshKey = 0,
  limit = 50,
) {
  const cleanedAccountRef = accountRef.trim();
  const cleanedExternalTenantRef = externalTenantRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasAccountCampaignList(
      cleanedAccountRef,
      "external_tenant_ref",
      cleanedExternalTenantRef,
      "setup",
      limit,
      refreshKey,
    ),
    queryFn: () =>
      listReferralSaasAccountCampaigns({
        accountRef: cleanedAccountRef,
        refType: "external_tenant_ref",
        externalRef: cleanedExternalTenantRef,
        context: "setup",
        limit,
      }),
    enabled: Boolean(enabled && cleanedAccountRef && cleanedExternalTenantRef),
    retry: false,
  });
}

export function useReferralSaasAccountCampaignAttribution(
  accountRef: string,
  externalTenantRef: string,
  enabled: boolean,
  refreshKey = 0,
  limit = 50,
) {
  const cleanedAccountRef = accountRef.trim();
  const cleanedExternalTenantRef = externalTenantRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasAccountCampaignAttribution(
      cleanedAccountRef,
      "external_tenant_ref",
      cleanedExternalTenantRef,
      "setup",
      limit,
      refreshKey,
    ),
    queryFn: () =>
      getReferralSaasAccountCampaignAttribution({
        accountRef: cleanedAccountRef,
        refType: "external_tenant_ref",
        externalRef: cleanedExternalTenantRef,
        context: "setup",
        limit,
      }),
    enabled: Boolean(enabled && cleanedAccountRef && cleanedExternalTenantRef),
    retry: false,
  });
}

export function useReferralSaasAccountReferralAttribution(
  accountRef: string,
  externalTenantRef: string,
  enabled: boolean,
  refreshKey = 0,
  limit = 50,
) {
  const cleanedAccountRef = accountRef.trim();
  const cleanedExternalTenantRef = externalTenantRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasAccountReferralAttribution(
      cleanedAccountRef,
      "external_tenant_ref",
      cleanedExternalTenantRef,
      "setup",
      limit,
      refreshKey,
    ),
    queryFn: () =>
      getReferralSaasAccountReferralAttribution({
        accountRef: cleanedAccountRef,
        refType: "external_tenant_ref",
        externalRef: cleanedExternalTenantRef,
        context: "setup",
        limit,
      }),
    enabled: Boolean(enabled && cleanedAccountRef && cleanedExternalTenantRef),
    retry: false,
  });
}

export function useReferralSaasAccountReferralList(
  accountRef: string,
  externalTenantRef: string,
  enabled: boolean,
  refreshKey = 0,
  limit = 50,
) {
  const cleanedAccountRef = accountRef.trim();
  const cleanedExternalTenantRef = externalTenantRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasAccountReferralList(
      cleanedAccountRef,
      "external_tenant_ref",
      cleanedExternalTenantRef,
      "setup",
      limit,
      refreshKey,
    ),
    queryFn: () =>
      listReferralSaasAccountReferrals({
        accountRef: cleanedAccountRef,
        refType: "external_tenant_ref",
        externalRef: cleanedExternalTenantRef,
        context: "setup",
        limit,
      }),
    enabled: Boolean(enabled && cleanedAccountRef && cleanedExternalTenantRef),
    retry: false,
  });
}

export function useReferralSaasAccountReferralDetail(
  accountRef: string,
  referralTrackId: string,
  externalTenantRef: string,
  enabled: boolean,
  refreshKey = 0,
) {
  const cleanedAccountRef = accountRef.trim();
  const cleanedReferralTrackId = referralTrackId.trim();
  const cleanedExternalTenantRef = externalTenantRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasAccountReferralDetail(
      cleanedAccountRef,
      cleanedReferralTrackId,
      "external_tenant_ref",
      cleanedExternalTenantRef,
      "setup",
      refreshKey,
    ),
    queryFn: () =>
      getReferralSaasAccountReferral({
        accountRef: cleanedAccountRef,
        referralTrackId: cleanedReferralTrackId,
        refType: "external_tenant_ref",
        externalRef: cleanedExternalTenantRef,
        context: "setup",
      }),
    enabled: Boolean(
      enabled && cleanedAccountRef && cleanedReferralTrackId && cleanedExternalTenantRef,
    ),
    retry: false,
  });
}

export function useReferralSaasAccountReferrerList(
  accountRef: string,
  externalTenantRef: string,
  enabled: boolean,
  refreshKey = 0,
  limit = 50,
) {
  const cleanedAccountRef = accountRef.trim();
  const cleanedExternalTenantRef = externalTenantRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasAccountReferrerList(
      cleanedAccountRef,
      "external_tenant_ref",
      cleanedExternalTenantRef,
      "setup",
      limit,
      refreshKey,
    ),
    queryFn: () =>
      listReferralSaasAccountReferrers({
        accountRef: cleanedAccountRef,
        refType: "external_tenant_ref",
        externalRef: cleanedExternalTenantRef,
        context: "setup",
        limit,
      }),
    enabled: Boolean(enabled && cleanedAccountRef && cleanedExternalTenantRef),
    retry: false,
  });
}

export function useReferralSaasAccountReferrerDetail(
  accountRef: string,
  safeReferrerKey: string,
  externalTenantRef: string,
  enabled: boolean,
  refreshKey = 0,
) {
  const cleanedAccountRef = accountRef.trim();
  const cleanedSafeReferrerKey = safeReferrerKey.trim();
  const cleanedExternalTenantRef = externalTenantRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasAccountReferrerDetail(
      cleanedAccountRef,
      cleanedSafeReferrerKey,
      "external_tenant_ref",
      cleanedExternalTenantRef,
      "setup",
      refreshKey,
    ),
    queryFn: () =>
      getReferralSaasAccountReferrer({
        accountRef: cleanedAccountRef,
        safeReferrerKey: cleanedSafeReferrerKey,
        refType: "external_tenant_ref",
        externalRef: cleanedExternalTenantRef,
        context: "setup",
      }),
    enabled: Boolean(
      enabled && cleanedAccountRef && cleanedSafeReferrerKey && cleanedExternalTenantRef,
    ),
    retry: false,
  });
}

export function useReferralSaasAccountCampaignReadiness(
  accountRef: string,
  campaignCode: string,
  externalTenantRef: string,
  operation: CampaignReadinessOperation,
  opportunityId: string,
  enabled: boolean,
  refreshKey = 0,
) {
  const cleanedAccountRef = accountRef.trim();
  const cleanedCampaignCode = campaignCode.trim();
  const cleanedExternalTenantRef = externalTenantRef.trim();
  const cleanedOpportunityId = opportunityId.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasAccountCampaignReadiness(
      cleanedAccountRef,
      cleanedCampaignCode,
      "external_tenant_ref",
      cleanedExternalTenantRef,
      operation,
      "setup",
      cleanedOpportunityId,
      refreshKey,
    ),
    queryFn: () =>
      getReferralSaasAccountCampaignReadiness({
        accountRef: cleanedAccountRef,
        campaignCode: cleanedCampaignCode,
        refType: "external_tenant_ref",
        externalRef: cleanedExternalTenantRef,
        operation,
        context: "setup",
        opportunityId: cleanedOpportunityId,
        includeEvidence: true,
      }),
    enabled: Boolean(enabled && cleanedAccountRef && cleanedCampaignCode && cleanedExternalTenantRef),
    retry: false,
  });
}

export function useReferralSaasAccountJourneyVersions(
  accountRef: string,
  externalTenantRef: string,
  enabled: boolean,
  refreshKey = 0,
  includeArchived = false,
  limit = 50,
) {
  const cleanedAccountRef = accountRef.trim();
  const cleanedExternalTenantRef = externalTenantRef.trim();

  return useQuery({
    queryKey: queryKeys.referralSaasAccountJourneyVersions(
      cleanedAccountRef,
      "external_tenant_ref",
      cleanedExternalTenantRef,
      "setup",
      includeArchived,
      limit,
      refreshKey,
    ),
    queryFn: () =>
      listReferralSaasAccountJourneyVersions({
        accountRef: cleanedAccountRef,
        refType: "external_tenant_ref",
        externalRef: cleanedExternalTenantRef,
        context: "setup",
        includeArchived,
        limit,
      }),
    enabled: Boolean(enabled && cleanedAccountRef && cleanedExternalTenantRef),
    retry: false,
  });
}
