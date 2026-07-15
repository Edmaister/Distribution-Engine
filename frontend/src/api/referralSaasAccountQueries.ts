import { useQuery } from "@tanstack/react-query";

import { getAdminOnboardingDrafts, getAdminOnboardingState } from "./endpoints/adminOnboarding";
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
