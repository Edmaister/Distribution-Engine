import { apiRequest } from "../client";

export type ReferralSaasLinkRecord = Record<string, unknown>;

export type ReferralSaasOperatorLinkSourceType =
  | "REFERRAL_CODE"
  | "CAMPAIGN_CODE"
  | "CAMPAIGN_REFERRAL_LINK"
  | "ROUTE_REFERRAL_LINK"
  | "COMPOSITE_CODE";

export type ReferralSaasAttributionTraceSection =
  | "outcome"
  | "attribution"
  | "participants"
  | "events"
  | "audit";

export function issueReferralSaasCode({
  referrerUcn,
  sticker,
  segment,
  preferredHandle,
  acceptedTerms,
}: {
  referrerUcn: string;
  sticker: string;
  segment: string;
  preferredHandle?: string;
  acceptedTerms: boolean;
}): Promise<ReferralSaasLinkRecord> {
  return apiRequest<ReferralSaasLinkRecord>("v1/referral-saas/referral-codes", {
    method: "POST",
    body: {
      referrerUcn,
      sticker,
      segment,
      preferredHandle: preferredHandle || undefined,
      acceptedTerms,
    },
  });
}

export function validateReferralSaasCode({
  tenantCode,
  referralCode,
  acceptedTerms,
  alias,
}: {
  tenantCode: string;
  referralCode: string;
  acceptedTerms: boolean;
  alias?: string;
}): Promise<ReferralSaasLinkRecord> {
  return apiRequest<ReferralSaasLinkRecord>("v1/referral-saas/public/referrals/validate", {
    method: "POST",
    body: {
      tenantCode,
      referralCode,
      acceptedTerms,
      alias: alias || undefined,
    },
  });
}

export function captureReferralSaasRefereeUcn(
  referralTrackId: string,
  refereeUcn: string,
): Promise<ReferralSaasLinkRecord> {
  return apiRequest<ReferralSaasLinkRecord>(
    `v1/referral-saas/referrals/${encodeURIComponent(referralTrackId)}/referee-ucn`,
    {
      method: "POST",
      body: {
        refereeUcn,
      },
    },
  );
}

export function inspectReferralSaasOperatorLink({
  tenantCode,
  sourceType,
  linkCodeId,
  codeOrRef,
  includeEvidence = true,
}: {
  tenantCode: string;
  sourceType: ReferralSaasOperatorLinkSourceType;
  linkCodeId?: string;
  codeOrRef?: string;
  includeEvidence?: boolean;
}): Promise<ReferralSaasLinkRecord> {
  return apiRequest<ReferralSaasLinkRecord>("v1/referral-saas/operator/links/inspect", {
    query: {
      tenant_code: tenantCode,
      source_type: sourceType,
      link_code_id: linkCodeId || undefined,
      code_or_ref: codeOrRef || undefined,
      include_evidence: includeEvidence,
    },
  });
}

export function inspectReferralSaasOperatorAttributionTrace({
  tenantCode,
  referralTrackId,
  includeSections,
}: {
  tenantCode: string;
  referralTrackId: string;
  includeSections?: ReferralSaasAttributionTraceSection[];
}): Promise<ReferralSaasLinkRecord> {
  return apiRequest<ReferralSaasLinkRecord>(
    `v1/referral-saas/operator/outcomes/${encodeURIComponent(referralTrackId)}/trace`,
    {
      query: {
        tenant_code: tenantCode,
        include_sections: includeSections?.length ? includeSections : undefined,
      },
    },
  );
}
