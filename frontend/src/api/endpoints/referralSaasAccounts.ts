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

export type ReferralSaasAccountCreateFromDraftRequest = {
  draftRef: string;
  internalTenantCode: string;
  idempotencyKey: string;
  correlationId?: string;
};

export type ReferralSaasAccountCreateFromDraftResponse = {
  status: string;
  account: ReferralSaasAccountSummary;
  guardrails: string[];
  redactions: string[];
  noAdjacentLiveActionConfirmed: boolean;
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

export function createReferralSaasAccountFromDraft({
  draftRef,
  internalTenantCode,
  idempotencyKey,
  correlationId = "referral-saas-account-setup-create",
}: ReferralSaasAccountCreateFromDraftRequest): Promise<ReferralSaasAccountCreateFromDraftResponse> {
  return apiRequest<{
    status: string;
    account: ReferralSaasAccountSummary;
    guardrails: string[];
    redactions: string[];
    no_adjacent_live_action_confirmed: boolean;
  }>("v1/referral-saas/accounts/from-draft", {
    method: "POST",
    body: {
      draft_ref: draftRef.trim(),
      internal_tenant_code: internalTenantCode.trim(),
      idempotency_key: idempotencyKey,
      correlation_id: correlationId,
    },
  }).then((response) => ({
    status: response.status,
    account: response.account,
    guardrails: response.guardrails,
    redactions: response.redactions,
    noAdjacentLiveActionConfirmed: response.no_adjacent_live_action_confirmed,
  }));
}
