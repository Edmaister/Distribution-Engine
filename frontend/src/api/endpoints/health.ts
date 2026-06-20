import { apiRequest } from "../client";

export type HealthResponse = Record<string, unknown>;
export type ReadinessResponse = Record<string, unknown>;

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("health");
}

export function getReadiness(): Promise<ReadinessResponse> {
  return apiRequest<ReadinessResponse>("readyz");
}
