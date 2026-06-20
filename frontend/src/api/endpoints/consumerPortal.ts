import { apiRequest } from "../client";

export type ConsumerPortalRecord = Record<string, unknown>;

export type ConsumerExperienceRequest = {
  tenantCode?: string;
  referrerUcn: string;
  referralTrackId?: string;
  leaderboardCode?: string;
  includeInsuranceProof?: boolean;
};

export function getConsumerExperience({
  tenantCode,
  referrerUcn,
  referralTrackId,
  leaderboardCode = "GLOBAL_OVERALL",
  includeInsuranceProof = false,
}: ConsumerExperienceRequest): Promise<ConsumerPortalRecord> {
  return apiRequest<ConsumerPortalRecord>("v1/experience/consumer", {
    query: {
      tenant_code: tenantCode,
      referrer_ucn: referrerUcn,
      referral_track_id: referralTrackId,
      leaderboard_code: leaderboardCode,
      include_insurance_proof: includeInsuranceProof,
    },
  });
}

export function getConsumerReferrerDashboard(referrerUcn: string): Promise<ConsumerPortalRecord> {
  return apiRequest<ConsumerPortalRecord>(`v1/referrers/${encodeURIComponent(referrerUcn)}/dashboard`);
}

export function getConsumerRewardSummary(referrerUcn: string): Promise<ConsumerPortalRecord> {
  return apiRequest<ConsumerPortalRecord>(`v1/rewards/summary/referrers/${encodeURIComponent(referrerUcn)}`);
}

export function getConsumerReferralDashboard(referralTrackId: string): Promise<ConsumerPortalRecord> {
  return apiRequest<ConsumerPortalRecord>(`v1/referrals/${encodeURIComponent(referralTrackId)}/dashboard`);
}

export function getConsumerMissions(referrerUcn: string): Promise<ConsumerPortalRecord> {
  return apiRequest<ConsumerPortalRecord>(`v1/missions/referrer/${encodeURIComponent(referrerUcn)}`, {
    query: { audit: false },
  });
}

export function getConsumerLeaderboardPosition(
  tenantCode: string,
  leaderboardCode: string,
  referrerUcn: string,
): Promise<ConsumerPortalRecord> {
  return apiRequest<ConsumerPortalRecord>(
    `v1/tenants/${encodeURIComponent(tenantCode)}/leaderboards/${encodeURIComponent(leaderboardCode)}/me`,
    { query: { referrer_ucn: referrerUcn } },
  );
}

export function getConsumerInsuranceProof(
  tenantCode: string,
  referralTrackId?: string,
): Promise<ConsumerPortalRecord> {
  return apiRequest<ConsumerPortalRecord>(
    `v1/tenants/${encodeURIComponent(tenantCode)}/consumer/proof/insurance`,
    { query: { referral_track_id: referralTrackId || undefined } },
  );
}

export function bootstrapConsumerReferrer(referrerUcn: string, tenantCode: string): Promise<ConsumerPortalRecord> {
  return apiRequest<ConsumerPortalRecord>("referrals/bootstrap", {
    method: "POST",
    body: {
      referrerUcn,
      tenantCode,
    },
  });
}

export function acceptConsumerTerms(referrerUcn: string, tenantCode: string): Promise<ConsumerPortalRecord> {
  return apiRequest<ConsumerPortalRecord>("referrals/accept-terms", {
    method: "POST",
    body: {
      referrerUcn,
      tenantCode,
    },
  });
}

export function issueConsumerReferralCode({
  referrerUcn,
  tenantCode,
  sticker,
  segment,
  preferredHandle,
  acceptedTerms,
}: {
  referrerUcn: string;
  tenantCode: string;
  sticker: string;
  segment: string;
  preferredHandle?: string;
  acceptedTerms: boolean;
}): Promise<ConsumerPortalRecord> {
  return apiRequest<ConsumerPortalRecord>("referrals/codes", {
    method: "POST",
    body: {
      referrer_ucn: referrerUcn,
      tenant: tenantCode,
      sticker,
      segment,
      preferred_handle: preferredHandle || undefined,
      acceptedTerms,
    },
  });
}

export function validateConsumerReferralCode({
  tenantCode,
  referralCode,
  acceptedTerms,
  alias,
}: {
  tenantCode: string;
  referralCode: string;
  acceptedTerms: boolean;
  alias?: string;
}): Promise<ConsumerPortalRecord> {
  return apiRequest<ConsumerPortalRecord>("public/referrals/validate", {
    method: "POST",
    body: {
      tenantCode,
      referralCode,
      acceptedTerms,
      alias: alias || undefined,
    },
  });
}

export function captureConsumerRefereeUcn(referralTrackId: string, refereeUcn: string): Promise<ConsumerPortalRecord> {
  return apiRequest<ConsumerPortalRecord>("referrals/referees/ucn", {
    method: "POST",
    body: {
      referral_track_id: referralTrackId,
      referee_ucn: refereeUcn,
    },
  });
}
