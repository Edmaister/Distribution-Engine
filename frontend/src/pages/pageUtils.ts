import { useOutletContext } from "react-router-dom";

export type RefreshContext = {
  refreshKey: number;
};

export function useRefreshContext(): RefreshContext {
  return useOutletContext<RefreshContext>();
}

export function asArray(value: unknown): Record<string, unknown>[] {
  if (Array.isArray(value)) {
    return value as Record<string, unknown>[];
  }

  if (!value || typeof value !== "object") {
    return [];
  }

  const payload = value as Record<string, unknown>;
  for (const key of ["items", "results", "records", "invoices", "wallets", "contracts", "offers", "routes"]) {
    if (Array.isArray(payload[key])) {
      return payload[key] as Record<string, unknown>[];
    }
  }

  return [];
}

export function getValue(row: Record<string, unknown>, keys: string[], fallback = "-"): string {
  for (const key of keys) {
    const value = row[key];
    if (value !== undefined && value !== null && value !== "") {
      return String(value);
    }
  }
  return fallback;
}

export function countFrom(value: unknown, keys: string[]): number {
  if (!value || typeof value !== "object") {
    return 0;
  }

  for (const key of keys) {
    const found = (value as Record<string, unknown>)[key];
    if (typeof found === "number") {
      return found;
    }
    if (Array.isArray(found)) {
      return found.length;
    }
  }

  return 0;
}

export function formatJson(value: unknown): string {
  if (value === undefined || value === null) {
    return "-";
  }

  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  return JSON.stringify(value);
}

export function getNestedValue(value: unknown, path: string[], fallback: unknown = "-"): unknown {
  let current = value;
  for (const key of path) {
    if (!current || typeof current !== "object") {
      return fallback;
    }
    current = (current as Record<string, unknown>)[key];
  }
  return current ?? fallback;
}

export function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

export function objectEntries(value: unknown): Array<[string, Record<string, unknown>]> {
  if (!value || typeof value !== "object") {
    return [];
  }

  return Object.entries(value as Record<string, unknown>).map(([key, entry]) => [
    key,
    entry && typeof entry === "object" ? asRecord(entry) : { value: entry },
  ]);
}

export function formatDisplay(value: unknown): string {
  if (value === undefined || value === null || value === "") {
    return "-";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  return String(value);
}

export function currencyFrom(value: unknown, fallback = "ZAR"): string {
  if (!value || typeof value !== "object") {
    return fallback;
  }

  const record = value as Record<string, unknown>;
  for (const key of ["currency", "settlement_currency", "invoice_currency", "wallet_currency"]) {
    const found = record[key];
    if (typeof found === "string" && found.trim()) {
      return found.trim().toUpperCase();
    }
  }

  return fallback;
}

export function formatCurrency(value: unknown, currency = "ZAR", locale = "en-ZA"): string {
  if (value === undefined || value === null || value === "") {
    return "-";
  }

  const amount = typeof value === "number" ? value : Number(String(value).replace(/,/g, ""));
  if (!Number.isFinite(amount)) {
    return formatDisplay(value);
  }

  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${currency} ${amount.toFixed(2)}`;
  }
}

export function moneyValue(row: Record<string, unknown>, keys: string[], fallback = "0.00"): string {
  const value = getValue(row, keys, fallback);
  return formatCurrency(value, currencyFrom(row));
}

export function formatPercent(value: unknown, decimals = 1): string {
  if (value === undefined || value === null || value === "") {
    return "-";
  }

  const numeric = typeof value === "number" ? value : Number(String(value).replace("%", ""));
  if (!Number.isFinite(numeric)) {
    return formatDisplay(value);
  }

  const percent = Math.abs(numeric) <= 1 ? numeric * 100 : numeric;
  return `${percent.toFixed(decimals)}%`;
}

export function statusTone(status: string): "success" | "warning" | "danger" | "info" | "neutral" {
  const normalised = status.toLowerCase();
  if (["active", "ready", "paid", "completed", "success", "processed", "issued", "ok", "true", "yes"].includes(normalised)) {
    return "success";
  }
  if (["pending", "draft", "held", "queued", "open"].includes(normalised)) {
    return "warning";
  }
  if (["failed", "error", "reversed", "cancelled", "suspended", "terminated"].includes(normalised)) {
    return "danger";
  }
  if (normalised === "-") {
    return "neutral";
  }
  return "info";
}
