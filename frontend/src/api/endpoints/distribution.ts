import { apiRequest } from "../client";

export type DistributionRecord = Record<string, unknown>;

export type DistributorWalletMovementRequest = {
  amount: string;
  correlation_id?: string;
  metadata?: Record<string, unknown>;
};

export type CreateComplianceReviewRequest = {
  distributor_id: string;
  review_type: string;
  reviewer?: string;
  notes?: string;
  metadata?: Record<string, unknown>;
};

export type CompleteComplianceReviewRequest = {
  review_result: string;
  reviewer?: string;
  notes?: string;
  metadata?: Record<string, unknown>;
};

export type CreateDisputeRequest = {
  route_id: string;
  raised_by: string;
  reason_code: string;
  description?: string;
  metadata?: Record<string, unknown>;
};

export type ResolveDisputeRequest = {
  dispute_status: string;
  resolved_by?: string;
  resolution_notes?: string;
  metadata?: Record<string, unknown>;
};

export type DistributorGovernanceActionRequest = {
  action_type: string;
  reason_code?: string;
  actor?: string;
  notes?: string;
  operating_limits?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
};

export function getAdminDistributors(tenantCode: string, limit = 25): Promise<DistributionRecord[]> {
  return apiRequest<DistributionRecord[]>("admin/distribution/distributors", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function getAdminOpportunities(tenantCode: string, limit = 25): Promise<DistributionRecord[]> {
  return apiRequest<DistributionRecord[]>("admin/distribution/opportunities", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function getAdminRoutes(tenantCode: string, limit = 25): Promise<DistributionRecord[]> {
  return apiRequest<DistributionRecord[]>("admin/distribution/routing/routes", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function getAdminDistributorWallets(tenantCode: string, limit = 25): Promise<DistributionRecord[]> {
  return apiRequest<DistributionRecord[]>("admin/distribution/distributor-wallets", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function getAdminDistributionOverview(tenantCode: string): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>("admin/distribution/reporting/overview", {
    query: { tenant_code: tenantCode },
  });
}

export function getAdminDistributionOpportunityReport(tenantCode: string): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>("admin/distribution/reporting/opportunities", {
    query: { tenant_code: tenantCode },
  });
}

export function getAdminDistributionDistributorReport(tenantCode: string): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>("admin/distribution/reporting/distributors", {
    query: { tenant_code: tenantCode },
  });
}

export function getAdminDistributionGovernanceReport(tenantCode: string): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>("admin/distribution/reporting/governance", {
    query: { tenant_code: tenantCode },
  });
}

export function getAdminDistributionAttributionExceptions(
  tenantCode: string,
  limit = 25,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>("admin/distribution/reporting/attribution-exceptions", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function publishAdminOpportunity(opportunityId: string): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `admin/distribution/opportunities/${encodeURIComponent(opportunityId)}/publish`,
    { method: "POST" },
  );
}

export function closeAdminOpportunity(opportunityId: string): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `admin/distribution/opportunities/${encodeURIComponent(opportunityId)}/close`,
    { method: "POST" },
  );
}

export function reopenAdminOpportunity(opportunityId: string): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `admin/distribution/opportunities/${encodeURIComponent(opportunityId)}/reopen`,
    { method: "POST" },
  );
}

export function acceptAdminRoute(routeId: string): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `admin/distribution/routing/routes/${encodeURIComponent(routeId)}/accept`,
    { method: "POST" },
  );
}

export function declineAdminRoute(routeId: string): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `admin/distribution/routing/routes/${encodeURIComponent(routeId)}/decline`,
    { method: "POST" },
  );
}

export function activateAdminDistributor(distributorId: string): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `admin/distribution/distributors/${encodeURIComponent(distributorId)}/activate`,
    { method: "POST" },
  );
}

export function suspendAdminDistributor(distributorId: string): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `admin/distribution/distributors/${encodeURIComponent(distributorId)}/suspend`,
    { method: "POST" },
  );
}

export function terminateAdminDistributor(distributorId: string): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `admin/distribution/distributors/${encodeURIComponent(distributorId)}/terminate`,
    { method: "POST" },
  );
}

export function creditAdminDistributorWallet(
  walletId: string,
  request: DistributorWalletMovementRequest,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `admin/distribution/distributor-wallets/${encodeURIComponent(walletId)}/credit`,
    { method: "POST", body: request },
  );
}

export function holdAdminDistributorWallet(
  walletId: string,
  request: DistributorWalletMovementRequest,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `admin/distribution/distributor-wallets/${encodeURIComponent(walletId)}/hold`,
    { method: "POST", body: request },
  );
}

export function releaseHoldAdminDistributorWallet(
  walletId: string,
  request: DistributorWalletMovementRequest,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `admin/distribution/distributor-wallets/${encodeURIComponent(walletId)}/release-hold`,
    { method: "POST", body: request },
  );
}

export function payoutAdminDistributorWallet(
  walletId: string,
  request: DistributorWalletMovementRequest,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `admin/distribution/distributor-wallets/${encodeURIComponent(walletId)}/payout`,
    { method: "POST", body: request },
  );
}

export function reverseAdminDistributorWallet(
  walletId: string,
  request: DistributorWalletMovementRequest,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `admin/distribution/distributor-wallets/${encodeURIComponent(walletId)}/reverse`,
    { method: "POST", body: request },
  );
}

export function getAdminDistributorWalletLedger(walletId: string, limit = 25): Promise<DistributionRecord[]> {
  return apiRequest<DistributionRecord[]>(
    `admin/distribution/distributor-wallets/${encodeURIComponent(walletId)}/ledger`,
    { query: { limit } },
  );
}

export function getAdminComplianceReviews(tenantCode: string, limit = 25): Promise<DistributionRecord[]> {
  return apiRequest<DistributionRecord[]>("admin/distribution/governance/compliance-reviews", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function createAdminComplianceReview(request: CreateComplianceReviewRequest): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>("admin/distribution/governance/compliance-reviews", {
    method: "POST",
    body: request,
  });
}

export function completeAdminComplianceReview(
  reviewId: string,
  request: CompleteComplianceReviewRequest,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `admin/distribution/governance/compliance-reviews/${encodeURIComponent(reviewId)}/complete`,
    { method: "POST", body: request },
  );
}

export function getAdminDisputes(tenantCode: string, limit = 25): Promise<DistributionRecord[]> {
  return apiRequest<DistributionRecord[]>("admin/distribution/governance/disputes", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function createAdminDispute(request: CreateDisputeRequest): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>("admin/distribution/governance/disputes", {
    method: "POST",
    body: request,
  });
}

export function resolveAdminDispute(disputeId: string, request: ResolveDisputeRequest): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `admin/distribution/governance/disputes/${encodeURIComponent(disputeId)}/resolve`,
    { method: "POST", body: request },
  );
}

export function applyAdminDistributorGovernanceAction(
  distributorId: string,
  request: DistributorGovernanceActionRequest,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `admin/distribution/governance/distributors/${encodeURIComponent(distributorId)}/actions`,
    { method: "POST", body: request },
  );
}

export function getAdminGovernanceAudit(tenantCode: string, limit = 25): Promise<DistributionRecord[]> {
  return apiRequest<DistributionRecord[]>("admin/distribution/governance/audit", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function getDistributorPortalProfile(
  tenantCode: string,
  distributorCode: string,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>("distribution/portal/profile", {
    query: { tenant_code: tenantCode, distributor_code: distributorCode },
  });
}

export function getDistributorExperience(
  tenantCode: string,
  distributorCode: string,
  limit = 25,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>("v1/experience/distributor", {
    query: { tenant_code: tenantCode, distributor_code: distributorCode, limit },
  });
}

export function getDistributorPortalOffers(
  tenantCode: string,
  distributorCode: string,
  limit = 25,
): Promise<DistributionRecord[]> {
  return apiRequest<DistributionRecord[]>("distribution/portal/offers", {
    query: { tenant_code: tenantCode, distributor_code: distributorCode, limit },
  });
}

export function acceptDistributorPortalOffer(
  tenantCode: string,
  distributorCode: string,
  routeId: string,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(`distribution/portal/offers/${encodeURIComponent(routeId)}/accept`, {
    method: "POST",
    query: { tenant_code: tenantCode, distributor_code: distributorCode },
  });
}

export function declineDistributorPortalOffer(
  tenantCode: string,
  distributorCode: string,
  routeId: string,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(`distribution/portal/offers/${encodeURIComponent(routeId)}/decline`, {
    method: "POST",
    query: { tenant_code: tenantCode, distributor_code: distributorCode },
  });
}

export function linkDistributorPortalOfferReferral(
  tenantCode: string,
  distributorCode: string,
  routeId: string,
  referralTrackId: string,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(`distribution/portal/offers/${encodeURIComponent(routeId)}/referrals`, {
    method: "POST",
    query: { tenant_code: tenantCode, distributor_code: distributorCode },
    body: {
      referral_track_id: referralTrackId,
      metadata: { source: "distributor_workspace" },
    },
  });
}

export function getDistributorPortalWallets(
  tenantCode: string,
  distributorCode: string,
  limit = 25,
): Promise<DistributionRecord[]> {
  return apiRequest<DistributionRecord[]>("distribution/portal/wallets", {
    query: { tenant_code: tenantCode, distributor_code: distributorCode, limit },
  });
}

export function getDistributorPortalWalletLedger(
  tenantCode: string,
  distributorCode: string,
  walletId: string,
  limit = 25,
): Promise<DistributionRecord[]> {
  return apiRequest<DistributionRecord[]>(`distribution/portal/wallets/${encodeURIComponent(walletId)}/ledger`, {
    query: { tenant_code: tenantCode, distributor_code: distributorCode, limit },
  });
}

export function getDistributorPortalConversions(
  tenantCode: string,
  distributorCode: string,
  limit = 25,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>("distribution/portal/conversions", {
    query: { tenant_code: tenantCode, distributor_code: distributorCode, limit },
  });
}

export function getDistributorPortalOutcomeMoneyReview(
  tenantCode: string,
  distributorCode: string,
  limit = 25,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>("distribution/portal/outcome-money-review", {
    query: { tenant_code: tenantCode, distributor_code: distributorCode, limit },
  });
}

export function getDistributorPortalPerformance(
  tenantCode: string,
  distributorCode: string,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>("distribution/portal/performance", {
    query: { tenant_code: tenantCode, distributor_code: distributorCode },
  });
}

export function getDistributorPortalInsuranceProof(
  tenantCode: string,
  distributorCode: string,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>("distribution/portal/proof/insurance", {
    query: { tenant_code: tenantCode, distributor_code: distributorCode },
  });
}

export function getAdminChannelRecommendations(input: {
  event_type: string;
  audience: string;
  target_channels?: string[];
  distributor_channels?: string[];
}): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>("admin/channels/recommendations", {
    method: "POST",
    body: input,
  });
}

export function getDistributorPortalChannelRecommendations(
  tenantCode: string,
  distributorCode: string,
  input: {
    event_type?: string;
    audience?: string;
    distributor_channels?: string[];
  },
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>("distribution/portal/channel-recommendations", {
    query: {
      tenant_code: tenantCode,
      distributor_code: distributorCode,
      event_type: input.event_type,
      audience: input.audience,
      distributor_channels: input.distributor_channels,
    },
  });
}

export function getDistributorPortalChannelReadiness(
  tenantCode: string,
  distributorCode: string,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>("distribution/portal/channel-readiness", {
    query: { tenant_code: tenantCode, distributor_code: distributorCode },
  });
}

export function getTenantLeaderboard(
  tenantCode: string,
  leaderboardCode = "GLOBAL_OVERALL",
  limit = 10,
  offset = 0,
): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(
    `v1/tenants/${encodeURIComponent(tenantCode)}/leaderboards/${encodeURIComponent(leaderboardCode)}`,
    { query: { limit, offset } },
  );
}

export function getRecognitionProgress(referrerUcn: string): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(`v1/referrers/${encodeURIComponent(referrerUcn)}`);
}

export function getRecognitionBadges(referrerUcn: string): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(`v1/users/${encodeURIComponent(referrerUcn)}/badges`);
}

export function getRecognitionMissions(referrerUcn: string): Promise<DistributionRecord> {
  return apiRequest<DistributionRecord>(`v1/missions/referrer/${encodeURIComponent(referrerUcn)}`, {
    query: { audit: false },
  });
}
