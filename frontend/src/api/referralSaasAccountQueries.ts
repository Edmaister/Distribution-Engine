import { useQuery } from "@tanstack/react-query";

import { getAdminOnboardingDrafts, getAdminOnboardingState } from "./endpoints/adminOnboarding";
import {
  getReferralSaasMembershipActivationReadiness,
  getReferralSaasAccountMembershipPosture,
  getReferralSaasTechnicalSetupReadiness,
  listReferralSaasAccounts,
  resolveReferralSaasAccount,
} from "./endpoints/referralSaasAccounts";
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
