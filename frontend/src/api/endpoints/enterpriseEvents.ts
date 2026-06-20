import { apiRequest } from "../client";

export type EnterpriseEventSummary = Record<string, unknown>;
export type EnterpriseEventDashboard = Record<string, unknown>;
export type EnterpriseEventEntry = Record<string, unknown>;

export function getEnterpriseEventSummary(): Promise<EnterpriseEventSummary> {
  return apiRequest<EnterpriseEventSummary>("admin/enterprise-events/summary");
}

export function getEnterpriseEventDashboard(days = 7, tenantCode?: string): Promise<EnterpriseEventDashboard> {
  return apiRequest<EnterpriseEventDashboard>("admin/enterprise-events/dashboard", {
    query: { days, tenantCode, problemLimit: 10 },
  });
}

export function getEnterpriseEvents(
  limit = 25,
  processingStatus?: string,
  sourceSystem?: string,
): Promise<EnterpriseEventEntry[]> {
  return apiRequest<EnterpriseEventEntry[]>("admin/enterprise-events", {
    query: { limit, processingStatus, sourceSystem },
  });
}

export function replayEnterpriseEvent(
  inboxEventId: string,
  dryRun = true,
): Promise<EnterpriseEventEntry> {
  return apiRequest<EnterpriseEventEntry>(
    `admin/enterprise-events/${encodeURIComponent(inboxEventId)}/replay`,
    {
      method: "POST",
      query: { dryRun },
    },
  );
}
