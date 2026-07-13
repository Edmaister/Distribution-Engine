import { useQuery } from "@tanstack/react-query";

import {
  getAdminCampaignReadiness,
  type CampaignReadinessOperation,
} from "./endpoints/adminCampaignReadiness";
import { queryKeys } from "./queryKeys";

export function useReferralSaasCampaignReadiness(
  campaignCode: string,
  tenantCode: string,
  operation: CampaignReadinessOperation,
  opportunityId: string,
  refreshKey = 0,
) {
  return useQuery({
    queryKey: queryKeys.referralSaasCampaignReadiness(
      campaignCode,
      tenantCode,
      operation,
      opportunityId,
      refreshKey,
    ),
    queryFn: () =>
      getAdminCampaignReadiness({
        campaignCode,
        tenantCode,
        operation,
        opportunityId,
        includeEvidence: true,
      }),
    enabled: Boolean(campaignCode.trim() && tenantCode.trim()),
  });
}
