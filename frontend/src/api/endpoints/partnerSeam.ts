import { apiRequest } from "../client";

export type PartnerSeamClientsResponse = {
  status?: string;
  count?: number;
  items?: Array<Record<string, unknown>>;
  available?: boolean;
  message?: string;
};

export type PartnerWebhookDeliveriesResponse = {
  status?: string;
  count?: number;
  items?: Array<Record<string, unknown>>;
  available?: boolean;
  message?: string;
};

export type PartnerWebhookProcessResponse = {
  status?: string;
  processed_count?: number;
  sent_count?: number;
  pending_count?: number;
  failed_count?: number;
  notified_count?: number;
  items?: Array<Record<string, unknown>>;
};

export type PartnerWebhookSummaryResponse = {
  status?: string;
  summary?: Record<string, unknown>;
  available?: boolean;
  message?: string;
};

export type PartnerIntegrationResponse = {
  status?: string;
  integration?: Record<string, unknown>;
};

export type PartnerReadinessResponse = {
  status?: string;
  readiness?: Record<string, unknown>;
  available?: boolean;
  message?: string;
};

export type PartnerWebhookActionResponse = {
  status?: string;
  client?: Record<string, unknown>;
  webhook?: Record<string, unknown>;
  rotated_count?: number;
  items?: Array<Record<string, unknown>>;
  guardrail?: string;
};

export type PartnerDeadLetterExportResponse = {
  status?: string;
  export?: {
    filename?: string;
    content_type?: string;
    count?: number;
    csv?: string;
    guardrail?: string;
  };
};

export function getPartnerClients(): Promise<PartnerSeamClientsResponse> {
  return apiRequest<PartnerSeamClientsResponse>("admin/partners/clients", {
    query: { limit: 25 },
  }).catch((error: unknown) => ({
    available: false,
    message: error && typeof error === "object" && "message" in error ? String(error.message) : "Unavailable",
    items: [],
    count: 0,
  }));
}

export function getPartnerWebhookDeliveries(): Promise<PartnerWebhookDeliveriesResponse> {
  return apiRequest<PartnerWebhookDeliveriesResponse>("admin/partners/webhook-deliveries", {
    query: { limit: 25 },
  }).catch((error: unknown) => ({
    available: false,
    message: error && typeof error === "object" && "message" in error ? String(error.message) : "Unavailable",
    items: [],
    count: 0,
  }));
}

export function getPartnerWebhookSummary(): Promise<PartnerWebhookSummaryResponse> {
  return apiRequest<PartnerWebhookSummaryResponse>("admin/partners/webhook-deliveries/summary", {
    query: { hours: 24 },
  }).catch((error: unknown) => ({
    available: false,
    message: error && typeof error === "object" && "message" in error ? String(error.message) : "Unavailable",
    summary: {},
  }));
}

export function processPartnerWebhookDeliveries(limit = 25): Promise<PartnerWebhookProcessResponse> {
  return apiRequest<PartnerWebhookProcessResponse>("admin/partners/webhook-deliveries/process", {
    method: "POST",
    query: { limit },
  });
}

export function getAdminPartnerWebhookAlerts(limit = 25): Promise<PartnerWebhookDeliveriesResponse> {
  return apiRequest<PartnerWebhookDeliveriesResponse>("admin/partners/webhook-deliveries/alerts", {
    query: { limit },
  }).catch((error: unknown) => ({
    available: false,
    message: error && typeof error === "object" && "message" in error ? String(error.message) : "Unavailable",
    items: [],
    count: 0,
  }));
}

export function notifyPartnerWebhookAlerts(limit = 25): Promise<PartnerWebhookProcessResponse> {
  return apiRequest<PartnerWebhookProcessResponse>("admin/partners/webhook-deliveries/alerts/notify", {
    method: "POST",
    query: { limit, channel: "IN_APP" },
  });
}

export function getPartnerIntegration(): Promise<PartnerIntegrationResponse> {
  return apiRequest<PartnerIntegrationResponse>("partner/integration");
}

export function getAdminPartnerReadiness(): Promise<PartnerReadinessResponse> {
  return apiRequest<PartnerReadinessResponse>("admin/partners/readiness").catch((error: unknown) => ({
    available: false,
    message: error && typeof error === "object" && "message" in error ? String(error.message) : "Unavailable",
    readiness: {},
  }));
}

export function createPartnerClient(input: {
  clientName: string;
  scopes: string[];
}): Promise<PartnerWebhookActionResponse> {
  return apiRequest<PartnerWebhookActionResponse>("partner/clients", {
    method: "POST",
    body: {
      tenant_code: "SELF",
      client_name: input.clientName,
      scopes: input.scopes,
    },
  });
}

export function createPartnerWebhook(input: {
  eventType: string;
  targetUrl: string;
}): Promise<PartnerWebhookActionResponse> {
  return apiRequest<PartnerWebhookActionResponse>("partner/webhooks", {
    method: "POST",
    body: {
      event_type: input.eventType,
      target_url: input.targetUrl,
    },
  });
}

export function rotatePartnerWebhookSecret(webhookId: string): Promise<PartnerWebhookActionResponse> {
  return apiRequest<PartnerWebhookActionResponse>(`partner/webhooks/${encodeURIComponent(webhookId)}/rotate-secret`, {
    method: "POST",
  });
}

export function rotatePartnerLegacyWebhookSecrets(limit = 25): Promise<PartnerWebhookActionResponse> {
  return apiRequest<PartnerWebhookActionResponse>("partner/webhooks/rotate-legacy-secrets", {
    method: "POST",
    query: { limit },
  });
}

export function retryPartnerWebhookDelivery(deliveryId: string): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>(`partner/webhook-deliveries/${encodeURIComponent(deliveryId)}/retry`, {
    method: "POST",
  });
}

export function exportPartnerWebhookDeadLetters(limit = 500): Promise<PartnerDeadLetterExportResponse> {
  return apiRequest<PartnerDeadLetterExportResponse>("partner/webhook-deliveries/dead-letter-export", {
    query: { limit },
  });
}

export function getPartnerWebhookAlerts(limit = 100): Promise<PartnerWebhookDeliveriesResponse> {
  return apiRequest<PartnerWebhookDeliveriesResponse>("partner/webhook-deliveries/alerts", {
    query: { limit },
  });
}
