import { getApiBaseUrl, getApiKey, getAuthToken, setApiBaseUrl, setApiKey, setAuthToken } from "../api/client";

export const ROLE_PRESETS = [
  {
    label: "Amplifi Admin",
    value: "admin",
    apiKey: "test-admin-key",
  },
  {
    label: "Finance Admin",
    value: "finance_admin",
    apiKey: "test-finance-admin-key",
  },
  {
    label: "Distribution Admin",
    value: "distribution_admin",
    apiKey: "test-distribution-admin-key",
  },
  {
    label: "System Admin",
    value: "system_admin",
    apiKey: "test-system-admin-key",
  },
  {
    label: "Producer - Supply",
    value: "producer",
    apiKey: "test-fnb-producer-insureco-key",
  },
  {
    label: "Distributor - Demand",
    value: "distributor",
    apiKey: "test-fnb-distributor-insurance-advocate-key",
  },
  {
    label: "Consumer Journey",
    value: "consumer",
    apiKey: "test-fnb-consumer-key",
  },
  {
    label: "FNB Partner",
    value: "partner",
    apiKey: "test-fnb-key",
  },
];

export type ApiSession = {
  apiBaseUrl: string;
  apiKey: string;
  authToken: string;
};

export function readApiSession(): ApiSession {
  return {
    apiBaseUrl: getApiBaseUrl(),
    apiKey: getApiKey(),
    authToken: getAuthToken(),
  };
}

export function writeApiSession(session: ApiSession): void {
  setApiBaseUrl(session.apiBaseUrl);
  setApiKey(session.apiKey);
  setAuthToken(session.authToken);
}

export function roleForApiKey(apiKey: string) {
  return ROLE_PRESETS.find((preset) => preset.apiKey === apiKey)?.value ?? "custom";
}

export function roleLabelForApiKey(apiKey: string) {
  return ROLE_PRESETS.find((preset) => preset.apiKey === apiKey)?.label ?? "Custom key";
}
