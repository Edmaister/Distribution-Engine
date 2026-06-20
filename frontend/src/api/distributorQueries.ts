import { useQuery } from "@tanstack/react-query";

import {
  getAdminDistributors,
  getDistributorPortalPerformance,
  getDistributorPortalProfile,
  getDistributorPortalWalletLedger,
  getDistributorPortalWallets,
  type DistributionRecord,
} from "./endpoints/distribution";
import { queryKeys } from "./queryKeys";

export function useDistributorOptions(tenantCode: string, refreshKey = 0) {
  const cleanedTenant = tenantCode.trim().toUpperCase();

  return useQuery({
    queryKey: queryKeys.distributorOptions(cleanedTenant, refreshKey),
    queryFn: () =>
      getAdminDistributors(cleanedTenant, 100)
        .then(asRecords)
        .catch(() => []),
    enabled: Boolean(cleanedTenant),
  });
}

export function useDistributorWalletWorkspace(
  tenantCode: string,
  distributorCode: string,
  refreshKey = 0,
) {
  return useQuery({
    queryKey: queryKeys.distributorWalletWorkspace(
      tenantCode,
      distributorCode,
      refreshKey,
    ),
    queryFn: async () => {
      const [profile, performance, wallets] = await Promise.all([
        getDistributorPortalProfile(tenantCode, distributorCode).catch(
          () => null,
        ),
        getDistributorPortalPerformance(tenantCode, distributorCode).catch(
          () => null,
        ),
        getDistributorPortalWallets(tenantCode, distributorCode),
      ]);

      return {
        profile,
        performance,
        wallets: asRecords(wallets),
      };
    },
    enabled: Boolean(tenantCode && distributorCode),
  });
}

export function useDistributorWalletLedger(
  tenantCode: string,
  distributorCode: string,
  walletId: string,
  refreshKey = 0,
) {
  return useQuery({
    queryKey: queryKeys.distributorWalletLedger(
      tenantCode,
      distributorCode,
      walletId,
      refreshKey,
    ),
    queryFn: () =>
      getDistributorPortalWalletLedger(tenantCode, distributorCode, walletId)
        .then(asRecords)
        .catch(() => []),
    enabled: Boolean(tenantCode && distributorCode && walletId),
  });
}

function asRecords(value: unknown): DistributionRecord[] {
  return Array.isArray(value)
    ? value.filter((item): item is DistributionRecord =>
        Boolean(item && typeof item === "object"),
      )
    : [];
}
