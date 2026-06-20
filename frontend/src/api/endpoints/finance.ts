import { apiRequest } from "../client";

export type FinanceRecord = Record<string, unknown>;

export function getOutcomeMoneyMap(tenantCode: string, limit = 25): Promise<FinanceRecord> {
  return apiRequest<FinanceRecord>("admin/finance/outcome-money-map", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function resolveOutcomeSettlementExceptions(
  referralTrackId: string,
  resolvedBy: string,
  tenantCode?: string,
): Promise<FinanceRecord> {
  return apiRequest<FinanceRecord>(
    `admin/finance/outcome-money-map/${referralTrackId}/settlement-exceptions/resolve`,
    {
      method: "POST",
      body: {
        resolved_by: resolvedBy,
        tenant_code: tenantCode,
      },
    },
  );
}

export function createOutcomeRewardEvidence(
  referralTrackId: string,
  createdBy: string,
  tenantCode?: string,
): Promise<FinanceRecord> {
  return apiRequest<FinanceRecord>(`admin/finance/outcome-money-map/${referralTrackId}/reward-evidence`, {
    method: "POST",
    body: {
      created_by: createdBy,
      tenant_code: tenantCode,
    },
  });
}

export function createOutcomeCommissionEvidence(
  referralTrackId: string,
  createdBy: string,
  tenantCode?: string,
): Promise<FinanceRecord> {
  return apiRequest<FinanceRecord>(`admin/finance/outcome-money-map/${referralTrackId}/commission-evidence`, {
    method: "POST",
    body: {
      created_by: createdBy,
      tenant_code: tenantCode,
    },
  });
}

export function createOutcomeWalletEvidence(
  referralTrackId: string,
  createdBy: string,
  tenantCode?: string,
): Promise<FinanceRecord> {
  return apiRequest<FinanceRecord>(`admin/finance/outcome-money-map/${referralTrackId}/wallet-evidence`, {
    method: "POST",
    body: {
      created_by: createdBy,
      tenant_code: tenantCode,
    },
  });
}

export function createOutcomeInvoiceEvidence(
  referralTrackId: string,
  createdBy: string,
  tenantCode?: string,
): Promise<FinanceRecord> {
  return apiRequest<FinanceRecord>(`admin/finance/outcome-money-map/${referralTrackId}/invoice-evidence`, {
    method: "POST",
    body: {
      created_by: createdBy,
      tenant_code: tenantCode,
    },
  });
}

export function createOutcomeSettlementEvidence(
  referralTrackId: string,
  createdBy: string,
  tenantCode?: string,
): Promise<FinanceRecord> {
  return apiRequest<FinanceRecord>(`admin/finance/outcome-money-map/${referralTrackId}/settlement-evidence`, {
    method: "POST",
    body: {
      created_by: createdBy,
      tenant_code: tenantCode,
    },
  });
}
