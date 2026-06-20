import { apiRequest } from "../client";

export type MultiCurrencyRecord = Record<string, unknown>;

export type ConversionQuoteRequest = {
  tenant_code: string;
  source_currency: string;
  target_currency: string;
  source_amount: string;
  persist_quote: boolean;
};

export function getAdminFxRates(tenantCode: string, limit = 25): Promise<MultiCurrencyRecord[]> {
  return apiRequest<MultiCurrencyRecord[]>("admin/multi-currency/fx-rates", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function getAdminCrossBorderSettlements(
  tenantCode: string,
  limit = 25,
): Promise<MultiCurrencyRecord[]> {
  return apiRequest<MultiCurrencyRecord[]>("admin/multi-currency/cross-border-settlements", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function previewConversionQuote(request: ConversionQuoteRequest): Promise<MultiCurrencyRecord> {
  return apiRequest<MultiCurrencyRecord>("admin/multi-currency/quotes", {
    method: "POST",
    body: request,
  });
}
