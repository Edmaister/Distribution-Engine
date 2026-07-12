import { useQuery } from "@tanstack/react-query";

import { getReferralSaasReport, type ReferralSaasReportType } from "./endpoints/referralSaasReports";
import { queryKeys } from "./queryKeys";

export function useReferralSaasReport(
  reportType: ReferralSaasReportType,
  tenantCode: string,
  refreshKey = 0,
) {
  return useQuery({
    queryKey: queryKeys.referralSaasReport(reportType, tenantCode, refreshKey),
    queryFn: () =>
      getReferralSaasReport({
        reportType,
        tenantCode,
      }),
    enabled: Boolean(tenantCode.trim()),
  });
}
