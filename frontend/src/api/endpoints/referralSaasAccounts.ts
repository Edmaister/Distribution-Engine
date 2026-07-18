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

export type ReferralSaasMembershipActorPosture = {
  status: string;
  roleFamily?: string | null;
  permissionSet?: string | null;
  canOperateSetup: boolean;
  evidence: string;
};

export type ReferralSaasMembershipRoleFamilySummary = {
  roleFamily: string;
  invitedCount: number;
  activeCount: number;
  suspendedCount: number;
  disabledCount: number;
  archivedCount: number;
};

export type ReferralSaasAccountMembershipPosture = {
  accountId: string;
  totalMemberships: number;
  invitedCount: number;
  activeCount: number;
  suspendedCount: number;
  disabledCount: number;
  archivedCount: number;
  roleFamilies: ReferralSaasMembershipRoleFamilySummary[];
  currentActor: ReferralSaasMembershipActorPosture;
  guardrails: string[];
  redactions: string[];
  noMembershipWriteConfirmed: boolean;
  noInviteDeliveryConfirmed: boolean;
};

export type ReferralSaasAccountMembershipPostureResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  membershipPosture: ReferralSaasAccountMembershipPosture;
  guardrail: string;
  no_membership_write_confirmed: boolean;
  no_invite_delivery_confirmed: boolean;
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

export type ReferralSaasMembershipInvitationRequest = {
  accountRef: string;
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  actor: {
    actorType: "USER" | "CLIENT";
    subject?: string;
    clientId?: string;
    emailHash?: string;
    displayName?: string;
  };
  membership: {
    roleFamily: string;
    permissionSet: string;
    tenantScope?: "PRIMARY_ACCOUNT_TENANT";
  };
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasMembershipInvitationResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  invitation: {
    commandStatus: string;
    membership: {
      membershipRef: string;
      status: string;
      roleFamily: string;
      permissionSet: string;
      canOperateSetup: boolean;
    };
    delivery: {
      status: string;
      nextAction: string;
    };
    idempotency: {
      status: string;
    };
    auditEventId?: string | null;
    guardrails: string[];
    redactions: string[];
    noInviteDeliveryConfirmed: boolean;
    noAuthClaimChangeConfirmed: boolean;
    noSeatAssignmentConfirmed: boolean;
    noMoneyMovementConfirmed: boolean;
  };
  guardrails: string[];
  redactions: string[];
  no_invite_delivery_confirmed: boolean;
  no_auth_claim_change_confirmed: boolean;
  no_seat_assignment_confirmed: boolean;
  no_money_movement_confirmed: boolean;
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

export function getReferralSaasAccountMembershipPosture({
  refType,
  externalRef,
  context = "setup",
}: ReferralSaasAccountResolutionRequest): Promise<ReferralSaasAccountMembershipPostureResponse> {
  return apiRequest<ReferralSaasAccountMembershipPostureResponse>(
    "v1/referral-saas/accounts/membership-posture",
    {
      query: {
        ref_type: refType,
        external_ref: externalRef.trim(),
        context,
      },
    },
  );
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

export function recordReferralSaasMembershipInvitationIntent({
  accountRef,
  accountScope,
  actor,
  membership,
  reasonCode = "ACCOUNT_SETUP_USER_ROLE",
  correlationId,
  idempotencyKey,
}: ReferralSaasMembershipInvitationRequest): Promise<ReferralSaasMembershipInvitationResponse> {
  return apiRequest<ReferralSaasMembershipInvitationResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/membership-invitations`,
    {
      method: "POST",
      body: {
        accountScope: {
          refType: accountScope.refType,
          externalRef: accountScope.externalRef.trim(),
          context: accountScope.context || "setup",
        },
        actor: {
          actorType: actor.actorType,
          subject: actor.subject?.trim() || undefined,
          clientId: actor.clientId?.trim() || undefined,
          emailHash: actor.emailHash?.trim() || undefined,
          displayName: actor.displayName?.trim() || undefined,
        },
        membership: {
          roleFamily: membership.roleFamily.trim(),
          permissionSet: membership.permissionSet.trim(),
          tenantScope: membership.tenantScope || "PRIMARY_ACCOUNT_TENANT",
        },
        reasonCode,
        correlationId,
        idempotencyKey,
      },
    },
  );
}
