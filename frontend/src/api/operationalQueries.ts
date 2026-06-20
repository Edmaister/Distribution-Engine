import { useQuery } from "@tanstack/react-query";

import {
  getAdminAuditEntries,
  getAdminAuditSummary,
} from "./endpoints/adminAudit";
import {
  getAdminChannelAudit,
  getAdminChannelDeliveries,
  getAdminChannelReadiness,
} from "./endpoints/adminChannels";
import { getHealth, getReadiness } from "./endpoints/health";
import { queryKeys } from "./queryKeys";

export function useAdminAudit(
  summaryHours = 24,
  entryLimit = 25,
  refreshKey = 0,
) {
  return useQuery({
    queryKey: queryKeys.adminAudit(summaryHours, entryLimit, refreshKey),
    queryFn: async () => {
      const [summary, entries] = await Promise.all([
        getAdminAuditSummary(summaryHours),
        getAdminAuditEntries(entryLimit),
      ]);
      return {
        summary,
        rows: Array.isArray(entries) ? entries : [],
      };
    },
  });
}

export function useHealthReadiness(refreshKey = 0) {
  return useQuery({
    queryKey: queryKeys.healthReadiness(refreshKey),
    queryFn: async () => {
      const [health, readiness] = await Promise.all([
        getHealth(),
        getReadiness(),
      ]);
      return { health, readiness };
    },
  });
}

export function useHealthConnection(refreshKey = 0) {
  return useQuery({
    queryKey: queryKeys.healthConnection(refreshKey),
    queryFn: getHealth,
    retry: 1,
  });
}

export function useAdminChannelOperations(
  statusFilter = "ALL",
  refreshKey = 0,
) {
  const normalizedStatus = statusFilter === "ALL" ? undefined : statusFilter;

  return useQuery({
    queryKey: queryKeys.adminChannelOperations(statusFilter, refreshKey),
    queryFn: async () => {
      const [readiness, deliveries, audit] = await Promise.all([
        getAdminChannelReadiness(),
        getAdminChannelDeliveries(normalizedStatus, 50),
        getAdminChannelAudit(50),
      ]);
      return { readiness, deliveries, audit };
    },
  });
}
