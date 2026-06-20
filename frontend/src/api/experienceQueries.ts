import { useQuery } from "@tanstack/react-query";

import { getAdminCommandCentreExperience } from "./endpoints/adminExperience";
import { getConsumerExperience, type ConsumerExperienceRequest } from "./endpoints/consumerPortal";
import { getDistributorExperience } from "./endpoints/distribution";
import { getSponsorExperience } from "./endpoints/sponsorBilling";
import { queryKeys } from "./queryKeys";

export function useAdminExperience(tenantCode: string, outcomeLimit = 25) {
  return useQuery({
    queryKey: queryKeys.adminExperience(tenantCode, outcomeLimit),
    queryFn: () => getAdminCommandCentreExperience(tenantCode, outcomeLimit),
    enabled: Boolean(tenantCode),
  });
}

export function useConsumerExperience(request: ConsumerExperienceRequest) {
  return useQuery({
    queryKey: queryKeys.consumerExperience(
      request.tenantCode,
      request.referrerUcn,
      request.referralTrackId,
      request.leaderboardCode || "GLOBAL_OVERALL",
      request.includeInsuranceProof || false,
    ),
    queryFn: () => getConsumerExperience(request),
    enabled: Boolean(request.referrerUcn),
  });
}

export function useDistributorExperience(
  tenantCode: string,
  distributorCode: string,
  limit = 25,
  refreshKey = 0,
) {
  return useQuery({
    queryKey: [...queryKeys.distributorExperience(tenantCode, distributorCode, limit), refreshKey],
    queryFn: () => getDistributorExperience(tenantCode, distributorCode, limit),
    enabled: Boolean(tenantCode && distributorCode),
  });
}

export function useSponsorExperience(
  tenantCode: string,
  sponsorCode: string,
  currency = "ZAR",
  limit = 25,
  refreshKey = 0,
) {
  return useQuery({
    queryKey: [...queryKeys.sponsorExperience(tenantCode, sponsorCode, currency, limit), refreshKey],
    queryFn: () => getSponsorExperience(tenantCode, sponsorCode, currency, limit),
    enabled: Boolean(tenantCode && sponsorCode),
  });
}
