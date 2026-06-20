import { apiRequest } from "../client";

export type VerticalReadinessRecord = Record<string, unknown>;

export function getVerticalReadiness(): Promise<VerticalReadinessRecord> {
  return apiRequest<VerticalReadinessRecord>("admin/verticals/readiness");
}

export function getInsuranceJourneyProof(): Promise<VerticalReadinessRecord> {
  return apiRequest<VerticalReadinessRecord>("admin/verticals/proof/insurance").then((payload) => {
    const proof = payload.proof;
    return proof && typeof proof === "object" ? (proof as VerticalReadinessRecord) : {};
  });
}
