import { apiRequest } from "../client";

export type SponsorBillingRecord = Record<string, unknown>;

export type CreateProducerSupplyLaunchRequest = {
  campaign_name: string;
  segment: string;
  opportunity_title: string;
  campaign_code?: string;
  opportunity_code?: string;
  description?: string;
  funding_contract_id?: string;
  product_code?: string;
  product_name?: string;
  target_segments?: string[];
  target_regions?: string[];
  target_channels?: string[];
  distributor_types?: string[];
  estimated_reward_amount?: string;
  estimated_commission_amount?: string;
  total_budget?: string;
  max_allocations?: number;
  starts_at?: string;
  ends_at?: string;
  publish_now?: boolean;
  metadata?: Record<string, unknown>;
};

export type UpdateProducerSupplyOpportunityRequest = {
  title?: string;
  description?: string;
  product_code?: string;
  product_name?: string;
  target_segments?: string[];
  target_regions?: string[];
  target_channels?: string[];
  distributor_types?: string[];
  estimated_reward_amount?: string;
  estimated_commission_amount?: string;
  total_budget?: string;
  max_allocations?: number;
  starts_at?: string;
  ends_at?: string;
  metadata?: Record<string, unknown>;
};

export type ScheduledBillingGenerationRequest = {
  tenant_code: string;
  invoice_period_start: string;
  invoice_period_end: string;
  due_date?: string;
  sponsor_code?: string;
  currency: string;
  vat_rate: string;
  issue: boolean;
  dry_run: boolean;
  limit: number;
  metadata?: Record<string, unknown>;
};

export type RecordSponsorInvoicePaymentRequest = {
  amount: string;
  payment_reference?: string;
  metadata?: Record<string, unknown>;
};

export function getAdminSponsorBillingDashboard(tenantCode: string): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>("admin/funding/sponsor-billing/dashboard", {
    query: { tenant_code: tenantCode },
  });
}

export function getAdminSponsorInvoices(tenantCode: string, limit = 25): Promise<SponsorBillingRecord[]> {
  return apiRequest<SponsorBillingRecord[]>("admin/funding/sponsor-billing/invoices", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function getAdminSponsorWallets(tenantCode: string, limit = 25): Promise<SponsorBillingRecord[]> {
  return apiRequest<SponsorBillingRecord[]>("admin/marketplace-funding/sponsor-wallets", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function getAdminNetworkWalletOverview(tenantCode: string): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>("admin/finance/wallets/overview", {
    query: { tenant_code: tenantCode },
  });
}

export function getAdminChannelReadiness(): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>("admin/channels/readiness");
}

export function getAdminChannelRecommendations(input: {
  event_type: string;
  audience: string;
  target_channels?: string[];
  distributor_channels?: string[];
}): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>("admin/channels/recommendations", {
    method: "POST",
    body: input,
  });
}

export function getProducerSupplyChannelRecommendations(
  tenantCode: string,
  producerCode: string,
  input: {
    event_type?: string;
    audience?: string;
    target_channels?: string[];
  },
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(`${producerSupplyBase(tenantCode, producerCode)}/channel-recommendations`, {
    query: {
      event_type: input.event_type,
      audience: input.audience,
      target_channels: input.target_channels,
    },
  });
}

export function getProducerSupplyChannelReadiness(
  tenantCode: string,
  producerCode: string,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(`${producerSupplyBase(tenantCode, producerCode)}/channel-readiness`);
}

export function getAdminSponsorStatement(
  tenantCode: string,
  sponsorCode: string,
  periodStart: string,
  periodEnd: string,
  currency?: string,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>("admin/funding/sponsor-billing/statements", {
    query: {
      tenant_code: tenantCode,
      sponsor_code: sponsorCode,
      period_start: periodStart,
      period_end: periodEnd,
      currency,
    },
  });
}

export function getAdminSponsorVatReport(
  tenantCode: string,
  periodStart: string,
  periodEnd: string,
  sponsorCode?: string,
  currency?: string,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>("admin/funding/sponsor-billing/vat-report", {
    query: {
      tenant_code: tenantCode,
      period_start: periodStart,
      period_end: periodEnd,
      sponsor_code: sponsorCode,
      currency,
    },
  });
}

export function runScheduledSponsorBillingGeneration(
  request: ScheduledBillingGenerationRequest,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>("admin/funding/sponsor-billing/scheduled-generation", {
    method: "POST",
    body: request,
  });
}

export function issueSponsorInvoice(invoiceId: string): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(
    `admin/funding/sponsor-billing/invoices/${encodeURIComponent(invoiceId)}/issue`,
    { method: "POST" },
  );
}

export function recordSponsorInvoicePayment(
  invoiceId: string,
  request: RecordSponsorInvoicePaymentRequest,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(
    `admin/funding/sponsor-billing/invoices/${encodeURIComponent(invoiceId)}/payments`,
    {
      method: "POST",
      body: request,
    },
  );
}

function sponsorBillingBase(tenantCode: string, sponsorCode: string): string {
  return `v1/tenants/${encodeURIComponent(tenantCode)}/sponsors/${encodeURIComponent(sponsorCode)}/billing`;
}

export function getSponsorPortalDashboard(
  tenantCode: string,
  sponsorCode: string,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(`${sponsorBillingBase(tenantCode, sponsorCode)}/dashboard`);
}

export function getSponsorExperience(
  tenantCode: string,
  sponsorCode: string,
  currency = "ZAR",
  limit = 25,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>("v1/experience/sponsor", {
    query: { tenant_code: tenantCode, sponsor_code: sponsorCode, currency, limit },
  });
}

export function getSponsorPortalInvoices(
  tenantCode: string,
  sponsorCode: string,
  limit = 25,
): Promise<SponsorBillingRecord[]> {
  return apiRequest<SponsorBillingRecord[]>(`${sponsorBillingBase(tenantCode, sponsorCode)}/invoices`, {
    query: { limit },
  });
}

export function getSponsorPortalStatement(
  tenantCode: string,
  sponsorCode: string,
  periodStart: string,
  periodEnd: string,
  currency?: string,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(`${sponsorBillingBase(tenantCode, sponsorCode)}/statements`, {
    query: { period_start: periodStart, period_end: periodEnd, currency },
  });
}

export function getSponsorPortalPaymentReceipts(
  tenantCode: string,
  sponsorCode: string,
  limit = 25,
): Promise<SponsorBillingRecord[]> {
  return apiRequest<SponsorBillingRecord[]>(`${sponsorBillingBase(tenantCode, sponsorCode)}/payment-receipts`, {
    query: { limit },
  });
}

export function getSponsorPortalWallet(
  tenantCode: string,
  sponsorCode: string,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(`${sponsorBillingBase(tenantCode, sponsorCode)}/wallet`);
}

export function getSponsorPortalWalletLedger(
  tenantCode: string,
  sponsorCode: string,
  limit = 25,
): Promise<SponsorBillingRecord[]> {
  return apiRequest<SponsorBillingRecord[]>(`${sponsorBillingBase(tenantCode, sponsorCode)}/wallet/ledger`, {
    query: { limit },
  });
}

export function getSponsorPortalContracts(
  tenantCode: string,
  sponsorCode: string,
  limit = 25,
): Promise<SponsorBillingRecord[]> {
  return apiRequest<SponsorBillingRecord[]>(`${sponsorBillingBase(tenantCode, sponsorCode)}/contracts`, {
    query: { limit },
  });
}

export function getSponsorPortalContractLedger(
  tenantCode: string,
  sponsorCode: string,
  contractId: string,
  limit = 25,
): Promise<SponsorBillingRecord[]> {
  return apiRequest<SponsorBillingRecord[]>(
    `${sponsorBillingBase(tenantCode, sponsorCode)}/contracts/${encodeURIComponent(contractId)}/ledger`,
    { query: { limit } },
  );
}

export function getSponsorPortalForecast(
  tenantCode: string,
  sponsorCode: string,
  currency = "ZAR",
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(`${sponsorBillingBase(tenantCode, sponsorCode)}/forecast`, {
    query: { currency },
  });
}

export function createProducerSupplyLaunch(
  tenantCode: string,
  producerCode: string,
  request: CreateProducerSupplyLaunchRequest,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(
    `v1/tenants/${encodeURIComponent(tenantCode)}/producers/${encodeURIComponent(producerCode)}/supply/launches`,
    {
      method: "POST",
      body: request,
    },
  );
}

function producerSupplyBase(tenantCode: string, producerCode: string): string {
  return `v1/tenants/${encodeURIComponent(tenantCode)}/producers/${encodeURIComponent(producerCode)}/supply`;
}

export function getProducerSupplyOpportunities(
  tenantCode: string,
  producerCode: string,
  limit = 100,
): Promise<SponsorBillingRecord[]> {
  return apiRequest<SponsorBillingRecord[]>(`${producerSupplyBase(tenantCode, producerCode)}/opportunities`, {
    query: { limit },
  });
}

export function getProducerSupplyPerformanceOverview(
  tenantCode: string,
  producerCode: string,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(`${producerSupplyBase(tenantCode, producerCode)}/performance/overview`);
}

export function getProducerSupplyOpportunityPerformance(
  tenantCode: string,
  producerCode: string,
  limit = 100,
): Promise<SponsorBillingRecord[]> {
  return apiRequest<SponsorBillingRecord[]>(`${producerSupplyBase(tenantCode, producerCode)}/performance/opportunities`, {
    query: { limit },
  });
}

export function getProducerSupplyConversions(
  tenantCode: string,
  producerCode: string,
  limit = 100,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(`${producerSupplyBase(tenantCode, producerCode)}/conversions`, {
    query: { limit },
  });
}

export function getProducerSupplyOutcomeMoneyReview(
  tenantCode: string,
  producerCode: string,
  limit = 25,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(`${producerSupplyBase(tenantCode, producerCode)}/outcome-money-review`, {
    query: { limit },
  });
}

export function getProducerSupplyInsuranceProof(
  tenantCode: string,
  producerCode: string,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(`${producerSupplyBase(tenantCode, producerCode)}/proof/insurance`);
}

export function updateProducerSupplyOpportunity(
  tenantCode: string,
  producerCode: string,
  opportunityId: string,
  request: UpdateProducerSupplyOpportunityRequest,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(
    `${producerSupplyBase(tenantCode, producerCode)}/opportunities/${encodeURIComponent(opportunityId)}`,
    {
      method: "PATCH",
      body: request,
    },
  );
}

export function publishProducerSupplyOpportunity(
  tenantCode: string,
  producerCode: string,
  opportunityId: string,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(
    `${producerSupplyBase(tenantCode, producerCode)}/opportunities/${encodeURIComponent(opportunityId)}/publish`,
    { method: "POST" },
  );
}

export function closeProducerSupplyOpportunity(
  tenantCode: string,
  producerCode: string,
  opportunityId: string,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(
    `${producerSupplyBase(tenantCode, producerCode)}/opportunities/${encodeURIComponent(opportunityId)}/close`,
    { method: "POST" },
  );
}

export function reopenProducerSupplyOpportunity(
  tenantCode: string,
  producerCode: string,
  opportunityId: string,
): Promise<SponsorBillingRecord> {
  return apiRequest<SponsorBillingRecord>(
    `${producerSupplyBase(tenantCode, producerCode)}/opportunities/${encodeURIComponent(opportunityId)}/reopen`,
    { method: "POST" },
  );
}
