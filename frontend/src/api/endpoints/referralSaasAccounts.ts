import { apiRequest } from "../client";
import type { CampaignReadinessOperation } from "./adminCampaignReadiness";

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

export type ReferralSaasAccountRegistryItem = {
  accountId: string;
  accountCode: string;
  accountName: string;
  accountType: string;
  accountStatus: string;
  onboardingStatus: string;
  operatingJurisdictionCode: string;
  primaryExternalTenantRef?: string | null;
  externalReferences: {
    refType: string;
    externalRef: string;
    referenceStatus: string;
  }[];
  createdAt: string;
  updatedAt: string;
};

export type ReferralSaasAccountRegistryResponse = {
  status: string;
  count: number;
  accounts: ReferralSaasAccountRegistryItem[];
  guardrail: string;
  redactions: string[];
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

export type ReferralSaasMembershipPersonSummary = {
  membershipRef: string;
  actorType: string;
  subject?: string | null;
  displayName?: string | null;
  roleFamily: string;
  permissionSet: string;
  status: string;
  deliveryStatus: string;
  recipientContactStatus: string;
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
  memberships: ReferralSaasMembershipPersonSummary[];
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

export type ReferralSaasMembershipActivationReadinessItem = {
  membershipRef: string;
  subject?: string | null;
  displayName?: string | null;
  roleFamily: string;
  membershipStatus: string;
  deliveryStatus: string;
  recipientContactStatus: string;
  deliveryReadiness: string;
  activationReadiness: string;
  provisioningReadiness: string;
  seatAssignmentStatus: string;
  authClaimStatus: string;
  blockers: string[];
  nextAction: string;
};

export type ReferralSaasMembershipActivationReadiness = {
  accountId: string;
  overallStatus: string;
  activeCount: number;
  invitedCount: number;
  deliveryReadyCount: number;
  activationReadyCount: number;
  missingRoleFamilies: string[];
  items: ReferralSaasMembershipActivationReadinessItem[];
  guardrails: string[];
  redactions: string[];
  noInviteDeliveryConfirmed: boolean;
  noMembershipActivationConfirmed: boolean;
  noSeatAssignmentConfirmed: boolean;
  noAuthClaimChangeConfirmed: boolean;
};

export type ReferralSaasMembershipActivationReadinessRequest = ReferralSaasAccountResolutionRequest & {
  accountRef: string;
};

export type ReferralSaasMembershipActivationReadinessResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  activationReadiness: ReferralSaasMembershipActivationReadiness;
  guardrail: string;
  no_invite_delivery_confirmed: boolean;
  no_membership_activation_confirmed: boolean;
  no_auth_claim_change_confirmed: boolean;
  no_seat_assignment_confirmed: boolean;
  no_money_movement_confirmed: boolean;
};

export type ReferralSaasTechnicalSetupCapability = {
  code: string;
  label: string;
  status: string;
  requiredChannels: string[];
  readyChannels: string[];
  missingChannels: string[];
  approvedProviderRefs: string[];
  missingApprovalChannels: string[];
  nextAction: string;
};

export type ReferralSaasTechnicalSetupReadiness = {
  accountId: string;
  overallStatus: string;
  providerStatus: string;
  channelSummary: {
    count: number;
    readyCount: number;
    attentionCount: number;
    supportedChannels: string[];
    approvedInviteProviderCount: number;
    postureBlockers: string[];
  };
  capabilities: ReferralSaasTechnicalSetupCapability[];
  guardrails: string[];
  redactions: string[];
  noCredentialCreationConfirmed: boolean;
  noWebhookDispatchConfirmed: boolean;
  noInviteDeliveryConfirmed: boolean;
  noMembershipActivationConfirmed: boolean;
  noAuthClaimChangeConfirmed: boolean;
  noSeatAssignmentConfirmed: boolean;
  noCampaignActivationConfirmed: boolean;
  noMoneyMovementConfirmed: boolean;
};

export type ReferralSaasTechnicalSetupReadinessRequest = ReferralSaasAccountResolutionRequest & {
  accountRef: string;
};

export type ReferralSaasTechnicalSetupReadinessResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  technicalSetupReadiness: ReferralSaasTechnicalSetupReadiness;
  guardrail: string;
  no_credential_creation_confirmed: boolean;
  no_webhook_dispatch_confirmed: boolean;
  no_invite_delivery_confirmed: boolean;
  no_membership_activation_confirmed: boolean;
  no_auth_claim_change_confirmed: boolean;
  no_seat_assignment_confirmed: boolean;
  no_campaign_activation_confirmed: boolean;
  no_money_movement_confirmed: boolean;
};

export type ReferralSaasAccountCampaignReadinessRequest = ReferralSaasAccountResolutionRequest & {
  accountRef: string;
  campaignCode: string;
  operation?: CampaignReadinessOperation;
  opportunityId?: string;
  includeEvidence?: boolean;
};

export type ReferralSaasAccountCampaignSummary = {
  campaignCode: string;
  name: string;
  segment: string;
  status: string;
  lifecycle: string;
  startsAt?: string | null;
  endsAt?: string | null;
  maxUses?: number | null;
  usesCount: number;
  policyStatus: string;
  createdAt?: string | null;
  updatedAt?: string | null;
};

export type ReferralSaasAccountCampaignListRequest = ReferralSaasAccountResolutionRequest & {
  accountRef: string;
  limit?: number;
};

export type ReferralSaasAccountCampaignListResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  count: number;
  campaigns: ReferralSaasAccountCampaignSummary[];
  guardrail: string;
  redactions: string[];
  no_campaign_mutation_confirmed: boolean;
  no_policy_write_confirmed: boolean;
  no_link_generation_confirmed: boolean;
  no_campaign_activation_confirmed: boolean;
  no_money_movement_confirmed: boolean;
};

export type ReferralSaasAccountCampaignReadRequest = ReferralSaasAccountResolutionRequest & {
  accountRef: string;
  campaignCode: string;
};

export type ReferralSaasAccountCampaignReadResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  campaign: ReferralSaasAccountCampaignSummary;
  guardrail: string;
  redactions: string[];
  no_campaign_mutation_confirmed: boolean;
  no_policy_write_confirmed: boolean;
  no_link_generation_confirmed: boolean;
  no_campaign_activation_confirmed: boolean;
  no_money_movement_confirmed: boolean;
};

export type ReferralSaasAccountCampaignReadinessResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  readiness: Record<string, unknown>;
  guardrail: string;
  redactions: string[];
  no_campaign_mutation_confirmed: boolean;
  no_policy_write_confirmed: boolean;
  no_link_generation_confirmed: boolean;
  no_campaign_activation_confirmed: boolean;
  no_money_movement_confirmed: boolean;
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

export type ReferralSaasMembershipInvitationDeliveryRequest = {
  accountRef: string;
  membershipRef: string;
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  delivery: {
    providerRef: string;
    channel: "EMAIL";
    templateRef: string;
  };
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasMembershipActivationRequest = {
  accountRef: string;
  membershipRef: string;
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  activation: {
    acceptedSubject: string;
    acceptanceEvidenceRef: string;
  };
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasAccountProfileUpdateRequest = {
  accountRef: string;
  profile: {
    accountName: string;
    accountType: string;
    operatingJurisdictionCode: string;
    customerType?: string;
    industry?: string;
  };
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasAccountProfileUpdateResponse = {
  status: string;
  profile: {
    accountId: string;
    accountCode: string;
    accountName: string;
    accountType: string;
    accountStatus: string;
    onboardingStatus: string;
    operatingJurisdictionCode: string;
    customerType?: string | null;
    industry?: string | null;
    auditEventId?: string | null;
    guardrails: string[];
    redactions: string[];
  };
  guardrails: string[];
  redactions: string[];
  no_external_reference_rotation_confirmed: boolean;
  no_account_activation_confirmed: boolean;
  no_membership_write_confirmed: boolean;
  no_invite_delivery_confirmed: boolean;
  no_money_movement_confirmed: boolean;
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

export type ReferralSaasMembershipInvitationDeliveryResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  deliveryRequest: {
    commandStatus: string;
    membership: {
      membershipRef: string;
      status: string;
      roleFamily: string;
      permissionSet: string;
    };
    delivery: {
      status: string;
      nextAction: string;
      recipientContactStatus: string;
      providerRef: string;
      channel: string;
      templateRef: string;
    };
    idempotency: {
      status: string;
    };
    auditEventId?: string | null;
    guardrails: string[];
    redactions: string[];
    noInviteDeliveryConfirmed: boolean;
    noMembershipActivationConfirmed: boolean;
    noAuthClaimChangeConfirmed: boolean;
    noSeatAssignmentConfirmed: boolean;
    noMoneyMovementConfirmed: boolean;
  };
  guardrails: string[];
  redactions: string[];
  no_invite_delivery_confirmed: boolean;
  no_membership_activation_confirmed: boolean;
  no_auth_claim_change_confirmed: boolean;
  no_seat_assignment_confirmed: boolean;
  no_money_movement_confirmed: boolean;
};

export type ReferralSaasMembershipActivationResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  activationRequest: {
    commandStatus: string;
    membership: {
      membershipRef: string;
      previousStatus: string;
      status: string;
      roleFamily: string;
      permissionSet: string;
    };
    activation: {
      status: string;
      acceptedSubjectStatus: string;
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

export function listReferralSaasAccounts(limit = 50): Promise<ReferralSaasAccountRegistryResponse> {
  return apiRequest<ReferralSaasAccountRegistryResponse>("v1/referral-saas/accounts", {
    query: {
      limit,
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

export function getReferralSaasMembershipActivationReadiness({
  accountRef,
  refType,
  externalRef,
  context = "setup",
}: ReferralSaasMembershipActivationReadinessRequest): Promise<ReferralSaasMembershipActivationReadinessResponse> {
  return apiRequest<ReferralSaasMembershipActivationReadinessResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/membership-activation-readiness`,
    {
      query: {
        ref_type: refType,
        external_ref: externalRef.trim(),
        context,
      },
    },
  );
}

export function getReferralSaasTechnicalSetupReadiness({
  accountRef,
  refType,
  externalRef,
  context = "setup",
}: ReferralSaasTechnicalSetupReadinessRequest): Promise<ReferralSaasTechnicalSetupReadinessResponse> {
  return apiRequest<ReferralSaasTechnicalSetupReadinessResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/technical-setup-readiness`,
    {
      query: {
        ref_type: refType,
        external_ref: externalRef.trim(),
        context,
      },
    },
  );
}

export function listReferralSaasAccountCampaigns({
  accountRef,
  refType,
  externalRef,
  context = "setup",
  limit = 50,
}: ReferralSaasAccountCampaignListRequest): Promise<ReferralSaasAccountCampaignListResponse> {
  return apiRequest<ReferralSaasAccountCampaignListResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/campaigns`,
    {
      query: {
        ref_type: refType,
        external_ref: externalRef.trim(),
        context,
        limit,
      },
    },
  );
}

export function getReferralSaasAccountCampaign({
  accountRef,
  campaignCode,
  refType,
  externalRef,
  context = "setup",
}: ReferralSaasAccountCampaignReadRequest): Promise<ReferralSaasAccountCampaignReadResponse> {
  return apiRequest<ReferralSaasAccountCampaignReadResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/campaigns/${encodeURIComponent(
      campaignCode.trim(),
    )}`,
    {
      query: {
        ref_type: refType,
        external_ref: externalRef.trim(),
        context,
      },
    },
  );
}

export function getReferralSaasAccountCampaignReadiness({
  accountRef,
  campaignCode,
  refType,
  externalRef,
  operation = "CONTROL_PLANE_VIEW",
  context = "setup",
  opportunityId,
  includeEvidence = true,
}: ReferralSaasAccountCampaignReadinessRequest): Promise<ReferralSaasAccountCampaignReadinessResponse> {
  return apiRequest<ReferralSaasAccountCampaignReadinessResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/campaigns/${encodeURIComponent(
      campaignCode.trim(),
    )}/readiness`,
    {
      query: {
        ref_type: refType,
        external_ref: externalRef.trim(),
        operation,
        context,
        opportunity_id: opportunityId?.trim() || undefined,
        include_evidence: includeEvidence,
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

export function requestReferralSaasMembershipInvitationDelivery({
  accountRef,
  membershipRef,
  accountScope,
  delivery,
  reasonCode = "CUSTOMER_PROFILE_INVITE_DELIVERY_REQUEST",
  correlationId,
  idempotencyKey,
}: ReferralSaasMembershipInvitationDeliveryRequest): Promise<ReferralSaasMembershipInvitationDeliveryResponse> {
  return apiRequest<ReferralSaasMembershipInvitationDeliveryResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/membership-invitations/${encodeURIComponent(
      membershipRef.trim(),
    )}/delivery`,
    {
      method: "POST",
      body: {
        accountScope: {
          refType: accountScope.refType,
          externalRef: accountScope.externalRef.trim(),
          context: accountScope.context || "setup",
        },
        delivery: {
          providerRef: delivery.providerRef.trim(),
          channel: delivery.channel,
          templateRef: delivery.templateRef.trim(),
        },
        reasonCode,
        correlationId,
        idempotencyKey,
      },
    },
  );
}

export function requestReferralSaasMembershipActivation({
  accountRef,
  membershipRef,
  accountScope,
  activation,
  reasonCode = "CUSTOMER_PROFILE_MEMBERSHIP_ACTIVATION_REQUEST",
  correlationId,
  idempotencyKey,
}: ReferralSaasMembershipActivationRequest): Promise<ReferralSaasMembershipActivationResponse> {
  return apiRequest<ReferralSaasMembershipActivationResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/memberships/${encodeURIComponent(
      membershipRef.trim(),
    )}/activation`,
    {
      method: "POST",
      body: {
        accountScope: {
          refType: accountScope.refType,
          externalRef: accountScope.externalRef.trim(),
          context: accountScope.context || "setup",
        },
        activation: {
          acceptedSubject: activation.acceptedSubject.trim(),
          acceptanceEvidenceRef: activation.acceptanceEvidenceRef.trim(),
        },
        reasonCode,
        correlationId,
        idempotencyKey,
      },
    },
  );
}

export function updateReferralSaasAccountProfile({
  accountRef,
  profile,
  correlationId,
  idempotencyKey,
}: ReferralSaasAccountProfileUpdateRequest): Promise<ReferralSaasAccountProfileUpdateResponse> {
  return apiRequest<ReferralSaasAccountProfileUpdateResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/profile`,
    {
      method: "PATCH",
      body: {
        profile: {
          accountName: profile.accountName.trim(),
          accountType: profile.accountType.trim(),
          operatingJurisdictionCode: profile.operatingJurisdictionCode.trim(),
          customerType: profile.customerType?.trim() || undefined,
          industry: profile.industry?.trim() || undefined,
        },
        correlationId,
        idempotencyKey,
      },
    },
  );
}
