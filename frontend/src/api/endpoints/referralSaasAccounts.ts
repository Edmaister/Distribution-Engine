import { apiRequest } from "../client";

export type ReferralSaasAccountResolutionContext = "runtime" | "setup";

export type ReferralSaasAccountResolutionRequest = {
  refType: "external_tenant_ref" | "organisation_ref";
  externalRef: string;
  context?: ReferralSaasAccountResolutionContext;
};

export type ReferralSaasAccountSummary = {
  accountId?: string;
  accountCode?: string;
  accountName?: string;
  accountType?: string;
  accountStatus?: string;
  onboardingStatus?: string;
  externalRefId?: string;
  refType?: string;
  externalRef?: string;
  referenceStatus?: string;
  accountTenantId?: string | null;
  relationshipType?: string | null;
  tenantLinkStatus?: string | null;
  isPrimary?: boolean;
  source?: string;
};

export type ReferralSaasAccountResolutionResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  guardrail: string;
};

export function resolveReferralSaasAccount({
  refType,
  externalRef,
  context = "setup",
}: ReferralSaasAccountResolutionRequest): Promise<ReferralSaasAccountResolutionResponse> {
  return apiRequest<ReferralSaasAccountResolutionResponse>("v1/referral-saas/accounts/resolve", {
    query: {
      ref_type: refType,
      external_ref: externalRef.trim(),
      context,
    },
  });
}
