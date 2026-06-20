export type ApiError = {
  status: number;
  message: string;
  details?: unknown;
};

export type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  query?: Record<string, string | number | boolean | (string | number | boolean)[] | undefined | null>;
  body?: unknown;
};

const API_BASE_KEY = "amplifi.apiBaseUrl";
const API_KEY_KEY = "amplifi.apiKey";
const AUTH_TOKEN_KEY = "amplifi.authToken";

export function getApiBaseUrl(): string {
  return localStorage.getItem(API_BASE_KEY) || "http://127.0.0.1:8000";
}

export function setApiBaseUrl(value: string): void {
  localStorage.setItem(API_BASE_KEY, value.replace(/\/$/, ""));
}

export function getApiKey(): string {
  return localStorage.getItem(API_KEY_KEY) || "test-admin-key";
}

export function setApiKey(value: string): void {
  localStorage.setItem(API_KEY_KEY, value);
}

export function getAuthToken(): string {
  return localStorage.getItem(AUTH_TOKEN_KEY) || "";
}

export function setAuthToken(value: string): void {
  localStorage.setItem(AUTH_TOKEN_KEY, value.trim());
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const baseUrl = getApiBaseUrl();
  const url = new URL(path, `${resolveApiBaseUrl(baseUrl)}/`);

  Object.entries(query || {}).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== undefined && item !== null && item !== "") {
          url.searchParams.append(key, String(item));
        }
      });
    } else if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });

  return url.toString();
}

function resolveApiBaseUrl(baseUrl: string): string {
  if (
    typeof window !== "undefined" &&
    window.location.port === "5173" &&
    ["http://127.0.0.1:8000", "http://localhost:8000"].includes(baseUrl)
  ) {
    return `${window.location.origin}/api`;
  }

  return baseUrl;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  const apiKey = getApiKey();
  const authToken = getAuthToken();

  if (authToken) {
    headers.Authorization = authToken.toLowerCase().startsWith("bearer ")
      ? authToken
      : `Bearer ${authToken}`;
  } else if (apiKey) {
    headers["x-api-key"] = apiKey;
  }

  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(buildUrl(path, options.query), {
    method: options.method || "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message =
      typeof payload === "object" && payload && "detail" in payload
        ? formatErrorDetail((payload as { detail: unknown }).detail)
        : `Request failed with status ${response.status}`;
    throw { status: response.status, message, details: payload } satisfies ApiError;
  }

  return payload as T;
}

function formatErrorDetail(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (!item || typeof item !== "object") {
          return String(item);
        }

        const record = item as Record<string, unknown>;
        const location = Array.isArray(record.loc) ? record.loc.join(".") : undefined;
        const message = record.msg ? String(record.msg) : JSON.stringify(record);
        return location ? `${location}: ${message}` : message;
      })
      .join("; ");
  }

  if (detail && typeof detail === "object") {
    return JSON.stringify(detail);
  }

  return "The request could not be completed.";
}
