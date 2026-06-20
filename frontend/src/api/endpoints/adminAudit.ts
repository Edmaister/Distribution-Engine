import { apiRequest } from "../client";

export type AdminAuditSummary = Record<string, unknown>;
export type AdminAuditEntry = Record<string, unknown>;

export function getAdminAuditSummary(hours = 24): Promise<AdminAuditSummary> {
  return apiRequest<AdminAuditSummary>("admin/audit/summary", {
    query: { hours },
  });
}

export function getAdminAuditEntries(limit = 25): Promise<AdminAuditEntry[]> {
  return apiRequest<AdminAuditEntry[]>("admin/audit", {
    query: { limit },
  });
}
