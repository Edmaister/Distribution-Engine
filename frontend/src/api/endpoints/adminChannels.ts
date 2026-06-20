import { apiRequest } from "../client";

export type AdminChannelRecord = Record<string, unknown>;

export function getAdminChannelReadiness(): Promise<AdminChannelRecord> {
  return apiRequest<AdminChannelRecord>("admin/channels/readiness");
}

export function getAdminChannelDeliveries(
  status?: string,
  limit = 50,
): Promise<AdminChannelRecord> {
  return apiRequest<AdminChannelRecord>("admin/channels/deliveries", {
    query: { status, limit },
  });
}

export function getAdminChannelAudit(limit = 50): Promise<AdminChannelRecord> {
  return apiRequest<AdminChannelRecord>("admin/channels/audit", {
    query: { limit },
  });
}

export function retryAdminChannelDelivery(
  deliveryId: string,
): Promise<AdminChannelRecord> {
  return apiRequest<AdminChannelRecord>(
    `admin/channels/deliveries/${encodeURIComponent(deliveryId)}/retry`,
    { method: "POST" },
  );
}
