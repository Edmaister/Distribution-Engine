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
  seatAssignmentStatus?: string;
  authClaimStatus?: string;
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

export type ReferralSaasIntegrationConfiguration = {
  configurationRef: string;
  accountRef: string;
  configurationStatus: string;
  apiEnvironment: Record<string, unknown>;
  webhookIntent: Record<string, unknown>;
  messageProviders: Record<string, unknown>;
  safeSetupPosture: Record<string, unknown>;
  reasonCode?: string | null;
  correlationId?: string | null;
  createdByRef?: string | null;
  createdByRole?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
  redactions: string[];
};

export type ReferralSaasIntegrationConfigurationPayload = {
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  apiEnvironment: {
    environment: string;
    authMethod: string;
    useCases: string[];
  };
  webhookIntent: {
    callbackUrl?: string;
    eventCategories: string[];
    deliveryMode: string;
  };
  messageProviders: {
    channels: string[];
    providerRefs: string[];
    approvalIntent: string;
  };
  reasonCode?: string;
  correlationId?: string;
  idempotencyKey?: string;
};

export type ReferralSaasIntegrationConfigurationReadRequest = ReferralSaasAccountResolutionRequest & {
  accountRef: string;
};

export type ReferralSaasIntegrationConfigurationReadResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  integrationConfiguration: ReferralSaasIntegrationConfiguration | null;
  technicalSetupReadiness: ReferralSaasTechnicalSetupReadiness;
  guardrail: string;
  guardrails: string[];
  redactions: string[];
  no_secret_or_credential_storage_confirmed: boolean;
  no_credential_creation_confirmed: boolean;
  no_webhook_dispatch_confirmed: boolean;
  no_invite_delivery_confirmed: boolean;
  no_membership_activation_confirmed: boolean;
  no_seat_assignment_confirmed: boolean;
  no_auth_claim_change_confirmed: boolean;
  no_campaign_activation_confirmed: boolean;
  no_go_live_action_confirmed: boolean;
  no_billing_or_money_movement_confirmed: boolean;
};

export type ReferralSaasIntegrationExecutionAction = {
  actionRef: string;
  label: string;
  status: string;
  nextStep: string;
  reason: string;
};

export type ReferralSaasIntegrationExecutionBlocker = {
  code: string;
  message: string;
};

export type ReferralSaasIntegrationExecutionReadiness = {
  executionStatus: string;
  plainLanguageSummary: string;
  blockers: ReferralSaasIntegrationExecutionBlocker[];
  readyActions: ReferralSaasIntegrationExecutionAction[];
  executionActions: ReferralSaasIntegrationExecutionAction[];
  configurationRef?: string | null;
  configurationStatus?: string | null;
  guardrails: string[];
  redactions: string[];
  noSecretOrCredentialStorageConfirmed: boolean;
  noCredentialCreationConfirmed: boolean;
  noCredentialLifecycleConfirmed: boolean;
  noWebhookDispatchConfirmed: boolean;
  noInviteDeliveryConfirmed: boolean;
  noMessageProviderDeliveryConfirmed: boolean;
  noMembershipActivationConfirmed: boolean;
  noSeatAssignmentConfirmed: boolean;
  noAuthClaimChangeConfirmed: boolean;
  noCampaignActivationConfirmed: boolean;
  noGoLiveActionConfirmed: boolean;
  noBillingOrMoneyMovementConfirmed: boolean;
};

export type ReferralSaasIntegrationExecutionReadinessResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  integrationExecutionReadiness: ReferralSaasIntegrationExecutionReadiness;
  integrationConfiguration: ReferralSaasIntegrationConfiguration | null;
  guardrail: string;
  guardrails: string[];
  redactions: string[];
  no_secret_or_credential_storage_confirmed: boolean;
  no_credential_creation_confirmed: boolean;
  no_credential_lifecycle_confirmed: boolean;
  no_webhook_dispatch_confirmed: boolean;
  no_invite_delivery_confirmed: boolean;
  no_message_provider_delivery_confirmed: boolean;
  no_membership_activation_confirmed: boolean;
  no_seat_assignment_confirmed: boolean;
  no_auth_claim_change_confirmed: boolean;
  no_campaign_activation_confirmed: boolean;
  no_go_live_action_confirmed: boolean;
  no_billing_or_money_movement_confirmed: boolean;
};

export type ReferralSaasApiAccessVerificationPayload = {
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  verification: Record<string, unknown>;
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasApiAccessVerificationResult = {
  verificationStatus: string;
  configurationRef: string;
  accountRef: string;
  apiEnvironment: string;
  verifiedUseCases: string[];
  idempotency: {
    status: string;
  };
  audit: {
    accountAuditEventId?: string | null;
  };
  plainLanguageSummary: string;
  guardrails: string[];
  redactions: string[];
  noSecretOrCredentialStorageConfirmed: boolean;
  noCredentialCreationConfirmed: boolean;
  noCredentialLifecycleConfirmed: boolean;
  noWebhookDispatchConfirmed: boolean;
  noInviteDeliveryConfirmed: boolean;
  noMessageProviderDeliveryConfirmed: boolean;
  noMembershipActivationConfirmed: boolean;
  noSeatAssignmentConfirmed: boolean;
  noAuthClaimChangeConfirmed: boolean;
  noCampaignActivationConfirmed: boolean;
  noGoLiveActionConfirmed: boolean;
  noBillingOrMoneyMovementConfirmed: boolean;
};

export type ReferralSaasApiAccessVerificationResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  integrationApiAccessVerification: ReferralSaasApiAccessVerificationResult;
  account_scope?: Record<string, unknown>;
  guardrail: string;
  guardrails: string[];
  redactions: string[];
  no_secret_or_credential_storage_confirmed: boolean;
  no_credential_creation_confirmed: boolean;
  no_credential_lifecycle_confirmed: boolean;
  no_webhook_dispatch_confirmed: boolean;
  no_invite_delivery_confirmed: boolean;
  no_message_provider_delivery_confirmed: boolean;
  no_membership_activation_confirmed: boolean;
  no_seat_assignment_confirmed: boolean;
  no_auth_claim_change_confirmed: boolean;
  no_campaign_activation_confirmed: boolean;
  no_go_live_action_confirmed: boolean;
  no_billing_or_money_movement_confirmed: boolean;
};

export type ReferralSaasWebhookTestDispatchPayload = {
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  webhookTest: Record<string, unknown>;
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasWebhookTestDispatchResult = {
  dispatchStatus: string;
  configurationRef: string;
  accountRef: string;
  callbackUrlPresent: boolean;
  eventCategories: string[];
  idempotency: {
    status: string;
  };
  audit: {
    accountAuditEventId?: string | null;
  };
  plainLanguageSummary: string;
  guardrails: string[];
  redactions: string[];
  noSecretOrCredentialStorageConfirmed: boolean;
  noCredentialCreationConfirmed: boolean;
  noCredentialLifecycleConfirmed: boolean;
  noWebhookDispatchConfirmed: boolean;
  noInviteDeliveryConfirmed: boolean;
  noMessageProviderDeliveryConfirmed: boolean;
  noMembershipActivationConfirmed: boolean;
  noSeatAssignmentConfirmed: boolean;
  noAuthClaimChangeConfirmed: boolean;
  noCampaignActivationConfirmed: boolean;
  noGoLiveActionConfirmed: boolean;
  noBillingOrMoneyMovementConfirmed: boolean;
};

export type ReferralSaasWebhookTestDispatchResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  integrationWebhookTestDispatch: ReferralSaasWebhookTestDispatchResult;
  account_scope?: Record<string, unknown>;
  guardrail: string;
  guardrails: string[];
  redactions: string[];
  no_secret_or_credential_storage_confirmed: boolean;
  no_credential_creation_confirmed: boolean;
  no_credential_lifecycle_confirmed: boolean;
  no_webhook_dispatch_confirmed: boolean;
  no_invite_delivery_confirmed: boolean;
  no_message_provider_delivery_confirmed: boolean;
  no_membership_activation_confirmed: boolean;
  no_seat_assignment_confirmed: boolean;
  no_auth_claim_change_confirmed: boolean;
  no_campaign_activation_confirmed: boolean;
  no_go_live_action_confirmed: boolean;
  no_billing_or_money_movement_confirmed: boolean;
};

export type ReferralSaasMessageProviderTestPayload = {
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  messageProviderTest: Record<string, unknown>;
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasMessageProviderTestResult = {
  testStatus: string;
  configurationRef: string;
  accountRef: string;
  channels: string[];
  providerRefs: string[];
  idempotency: {
    status: string;
  };
  audit: {
    accountAuditEventId?: string | null;
  };
  plainLanguageSummary: string;
  guardrails: string[];
  redactions: string[];
  noSecretOrCredentialStorageConfirmed: boolean;
  noCredentialCreationConfirmed: boolean;
  noCredentialLifecycleConfirmed: boolean;
  noWebhookDispatchConfirmed: boolean;
  noInviteDeliveryConfirmed: boolean;
  noMessageProviderDeliveryConfirmed: boolean;
  noMembershipActivationConfirmed: boolean;
  noSeatAssignmentConfirmed: boolean;
  noAuthClaimChangeConfirmed: boolean;
  noCampaignActivationConfirmed: boolean;
  noGoLiveActionConfirmed: boolean;
  noBillingOrMoneyMovementConfirmed: boolean;
};

export type ReferralSaasMessageProviderTestResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  integrationMessageProviderTest: ReferralSaasMessageProviderTestResult;
  account_scope?: Record<string, unknown>;
  guardrail: string;
  guardrails: string[];
  redactions: string[];
  no_secret_or_credential_storage_confirmed: boolean;
  no_credential_creation_confirmed: boolean;
  no_credential_lifecycle_confirmed: boolean;
  no_webhook_dispatch_confirmed: boolean;
  no_invite_delivery_confirmed: boolean;
  no_message_provider_delivery_confirmed: boolean;
  no_membership_activation_confirmed: boolean;
  no_seat_assignment_confirmed: boolean;
  no_auth_claim_change_confirmed: boolean;
  no_campaign_activation_confirmed: boolean;
  no_go_live_action_confirmed: boolean;
  no_billing_or_money_movement_confirmed: boolean;
};

export type ReferralSaasIntegrationCredentialRequest = {
  credentialRequestRef: string;
  accountRef: string;
  configurationRef?: string | null;
  credentialRequestStatus: string;
  reviewStatus: string;
  requestType: string;
  capability: string;
  environment: string;
  intendedUse: string[];
  requestedFor: Record<string, unknown>;
  safeRequestPosture: Record<string, unknown>;
  reasonCode?: string | null;
  correlationId?: string | null;
  createdByRef?: string | null;
  createdByRole?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
  redactions: string[];
  noSecretOrCredentialStorageConfirmed: boolean;
  noCredentialCreationConfirmed: boolean;
  noCredentialLifecycleExecutionConfirmed: boolean;
  noCredentialRevealOrDownloadConfirmed: boolean;
  noVaultWriteConfirmed: boolean;
  noProviderCallConfirmed: boolean;
  noWebhookDispatchConfirmed: boolean;
  noInviteDeliveryConfirmed: boolean;
  noMessageProviderDeliveryConfirmed: boolean;
  noMembershipActivationConfirmed: boolean;
  noSeatAssignmentConfirmed: boolean;
  noAuthClaimChangeConfirmed: boolean;
  noCampaignActivationConfirmed: boolean;
  noGoLiveActionConfirmed: boolean;
  noBillingOrMoneyMovementConfirmed: boolean;
};

export type ReferralSaasIntegrationCredentialRequestPayload = {
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  credentialRequest: {
    requestType: string;
    capability: string;
    environment?: string;
    intendedUse?: string[];
    requestedFor?: Record<string, unknown>;
  };
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasIntegrationCredentialRequestCreateResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  integrationCredentialRequestResult: {
    commandStatus: string;
    credentialRequest: ReferralSaasIntegrationCredentialRequest;
    idempotency: {
      status: string;
    };
    audit: {
      accountAuditEventId?: string | null;
    };
    plainLanguageSummary: string;
    guardrails: string[];
    redactions: string[];
  };
  account_scope?: Record<string, unknown>;
  guardrail: string;
  guardrails: string[];
  redactions: string[];
  no_secret_or_credential_storage_confirmed: boolean;
  no_credential_creation_confirmed: boolean;
  no_credential_lifecycle_execution_confirmed: boolean;
  no_credential_reveal_or_download_confirmed: boolean;
  no_vault_write_confirmed: boolean;
  no_provider_call_confirmed: boolean;
  no_webhook_dispatch_confirmed: boolean;
  no_invite_delivery_confirmed: boolean;
  no_message_provider_delivery_confirmed: boolean;
  no_membership_activation_confirmed: boolean;
  no_seat_assignment_confirmed: boolean;
  no_auth_claim_change_confirmed: boolean;
  no_campaign_activation_confirmed: boolean;
  no_go_live_action_confirmed: boolean;
  no_billing_or_money_movement_confirmed: boolean;
};

export type ReferralSaasIntegrationCredentialReviewDecisionRequest = {
  accountRef: string;
  credentialRequestRef: string;
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  reviewDecision: {
    decision: "APPROVED" | "BLOCKED";
    reason: string;
  };
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasIntegrationCredentialReviewDecisionResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  integrationCredentialReviewDecisionResult: {
    commandStatus: string;
    credentialRequest: ReferralSaasIntegrationCredentialRequest;
    reviewStatus: string;
    idempotency: {
      status: string;
    };
    audit: {
      accountAuditEventId?: string | null;
    };
    plainLanguageSummary: string;
    guardrails: string[];
    redactions: string[];
    noSecretOrCredentialStorageConfirmed: boolean;
    noCredentialCreationConfirmed: boolean;
    noCredentialLifecycleExecutionConfirmed: boolean;
    noCredentialRevealOrDownloadConfirmed: boolean;
    noVaultWriteConfirmed: boolean;
    noProviderCallConfirmed: boolean;
    noWebhookDispatchConfirmed: boolean;
    noInviteDeliveryConfirmed: boolean;
    noMessageProviderDeliveryConfirmed: boolean;
    noMembershipActivationConfirmed: boolean;
    noSeatAssignmentConfirmed: boolean;
    noAuthClaimChangeConfirmed: boolean;
    noCampaignActivationConfirmed: boolean;
    noGoLiveActionConfirmed: boolean;
    noBillingOrMoneyMovementConfirmed: boolean;
  };
  account_scope?: Record<string, unknown>;
  guardrail: string;
  guardrails: string[];
  redactions: string[];
  no_secret_or_credential_storage_confirmed: boolean;
  no_credential_creation_confirmed: boolean;
  no_credential_lifecycle_execution_confirmed: boolean;
  no_credential_reveal_or_download_confirmed: boolean;
  no_vault_write_confirmed: boolean;
  no_provider_call_confirmed: boolean;
  no_webhook_dispatch_confirmed: boolean;
  no_invite_delivery_confirmed: boolean;
  no_message_provider_delivery_confirmed: boolean;
  no_membership_activation_confirmed: boolean;
  no_seat_assignment_confirmed: boolean;
  no_auth_claim_change_confirmed: boolean;
  no_campaign_activation_confirmed: boolean;
  no_go_live_action_confirmed: boolean;
  no_billing_or_money_movement_confirmed: boolean;
};

export type ReferralSaasIntegrationCredentialExecutionCheckRequest = {
  accountRef: string;
  credentialRequestRef: string;
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  executionCheck: {
    reason: string;
    reasonCode?: string;
  };
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasIntegrationCredentialExecutionCheckResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  integrationCredentialExecutionCheckResult: {
    commandStatus: string;
    credentialRequest: ReferralSaasIntegrationCredentialRequest;
    executionCheckStatus: string;
    idempotency: {
      status: string;
    };
    audit: {
      accountAuditEventId?: string | null;
    };
    plainLanguageSummary: string;
    guardrails: string[];
    redactions: string[];
    noSecretOrCredentialStorageConfirmed: boolean;
    noCredentialCreationConfirmed: boolean;
    noCredentialLifecycleExecutionConfirmed: boolean;
    noCredentialRevealOrDownloadConfirmed: boolean;
    noVaultWriteConfirmed: boolean;
    noProviderCallConfirmed: boolean;
    noWebhookDispatchConfirmed: boolean;
    noInviteDeliveryConfirmed: boolean;
    noMessageProviderDeliveryConfirmed: boolean;
    noMembershipActivationConfirmed: boolean;
    noSeatAssignmentConfirmed: boolean;
    noAuthClaimChangeConfirmed: boolean;
    noCampaignActivationConfirmed: boolean;
    noGoLiveActionConfirmed: boolean;
    noBillingOrMoneyMovementConfirmed: boolean;
  };
  account_scope?: Record<string, unknown>;
  guardrail: string;
  guardrails: string[];
  redactions: string[];
  no_secret_or_credential_storage_confirmed: boolean;
  no_credential_creation_confirmed: boolean;
  no_credential_lifecycle_execution_confirmed: boolean;
  no_credential_reveal_or_download_confirmed: boolean;
  no_vault_write_confirmed: boolean;
  no_provider_call_confirmed: boolean;
  no_webhook_dispatch_confirmed: boolean;
  no_invite_delivery_confirmed: boolean;
  no_message_provider_delivery_confirmed: boolean;
  no_membership_activation_confirmed: boolean;
  no_seat_assignment_confirmed: boolean;
  no_auth_claim_change_confirmed: boolean;
  no_campaign_activation_confirmed: boolean;
  no_go_live_action_confirmed: boolean;
  no_billing_or_money_movement_confirmed: boolean;
};

export type ReferralSaasIntegrationCredentialRequestListRequest =
  ReferralSaasAccountResolutionRequest & {
    accountRef: string;
    limit?: number;
  };

export type ReferralSaasIntegrationCredentialRequestListResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  credentialRequests: ReferralSaasIntegrationCredentialRequest[];
  account_scope?: Record<string, unknown>;
  guardrail: string;
  guardrails: string[];
  redactions: string[];
  no_secret_or_credential_storage_confirmed: boolean;
  no_credential_creation_confirmed: boolean;
  no_credential_lifecycle_execution_confirmed: boolean;
  no_credential_reveal_or_download_confirmed: boolean;
  no_vault_write_confirmed: boolean;
  no_provider_call_confirmed: boolean;
  no_webhook_dispatch_confirmed: boolean;
  no_invite_delivery_confirmed: boolean;
  no_message_provider_delivery_confirmed: boolean;
  no_membership_activation_confirmed: boolean;
  no_seat_assignment_confirmed: boolean;
  no_auth_claim_change_confirmed: boolean;
  no_campaign_activation_confirmed: boolean;
  no_go_live_action_confirmed: boolean;
  no_billing_or_money_movement_confirmed: boolean;
};

export type ReferralSaasIntegrationConfigurationValidation = {
  commandStatus: string;
  safeSetupPosture: Record<string, unknown>;
  guardrails: string[];
  redactions: string[];
  noSecretOrCredentialStorageConfirmed: boolean;
  noCredentialCreationConfirmed: boolean;
  noWebhookDispatchConfirmed: boolean;
  noInviteDeliveryConfirmed: boolean;
  noMembershipActivationConfirmed: boolean;
  noSeatAssignmentConfirmed: boolean;
  noAuthClaimChangeConfirmed: boolean;
  noCampaignActivationConfirmed: boolean;
  noGoLiveActionConfirmed: boolean;
  noBillingOrMoneyMovementConfirmed: boolean;
};

export type ReferralSaasIntegrationConfigurationValidateResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  validation: ReferralSaasIntegrationConfigurationValidation;
  guardrails: string[];
  redactions: string[];
  no_configuration_saved_confirmed: boolean;
  no_secret_or_credential_storage_confirmed: boolean;
  no_credential_creation_confirmed: boolean;
  no_webhook_dispatch_confirmed: boolean;
  no_invite_delivery_confirmed: boolean;
  no_billing_or_money_movement_confirmed: boolean;
};

export type ReferralSaasIntegrationConfigurationSaveResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  integrationConfigurationResult: {
    commandStatus: string;
    configuration: ReferralSaasIntegrationConfiguration;
    validation: ReferralSaasIntegrationConfigurationValidation;
    idempotency: {
      status: string;
    };
    audit: {
      accountAuditEventId?: string | null;
    };
    guardrails: string[];
    redactions: string[];
  };
  guardrail: string;
  guardrails: string[];
  redactions: string[];
  no_secret_or_credential_storage_confirmed: boolean;
  no_credential_creation_confirmed: boolean;
  no_webhook_dispatch_confirmed: boolean;
  no_invite_delivery_confirmed: boolean;
  no_membership_activation_confirmed: boolean;
  no_seat_assignment_confirmed: boolean;
  no_auth_claim_change_confirmed: boolean;
  no_campaign_activation_confirmed: boolean;
  no_go_live_action_confirmed: boolean;
  no_billing_or_money_movement_confirmed: boolean;
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

export type ReferralSaasSupportCaseEvidenceLink = {
  evidenceLinkId?: string | null;
  evidenceType: string;
  evidenceRef: string;
  safeStatus?: string | null;
  warningCode?: string | null;
  missingEvidenceCode?: string | null;
  redactions: string[];
};

export type ReferralSaasSupportCase = {
  caseRef: string;
  accountRef: string;
  category: string;
  priority: string;
  status: string;
  title: string;
  summary: string;
  sourceSurface?: string | null;
  assigneeRef?: string | null;
  correlationId?: string | null;
  createdByRef: string;
  createdByRole?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
  evidenceLinks: ReferralSaasSupportCaseEvidenceLink[];
  redactions: string[];
};

export type ReferralSaasSupportCaseListRequest = ReferralSaasAccountResolutionRequest & {
  accountRef: string;
  status?: string;
  limit?: number;
};

export type ReferralSaasSupportCaseListResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  supportCases: ReferralSaasSupportCase[];
  account_scope?: Record<string, unknown>;
  guardrails: string[];
  redactions: string[];
  no_tenant_code_exposure_confirmed: boolean;
  no_product_state_mutation_confirmed: boolean;
  no_billing_or_money_movement_confirmed: boolean;
};

export type ReferralSaasSupportCaseCreateRequest = {
  accountRef: string;
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  category: string;
  priority: string;
  title: string;
  summary: string;
  sourceSurface?: string;
  evidenceLinks?: Array<{
    evidenceType: string;
    evidenceRef: string;
    safeStatus?: string;
    warningCode?: string;
    missingEvidenceCode?: string;
    redactions?: string[];
  }>;
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasSupportCaseCreateResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  supportCase: {
    commandStatus: string;
    supportCase: ReferralSaasSupportCase;
    idempotency: {
      status: string;
    };
    audit: {
      accountAuditEventId?: string | null;
    };
    guardrails: string[];
    redactions: string[];
  };
  account_scope?: Record<string, unknown>;
  guardrail: string;
  guardrails: string[];
  redactions: string[];
  no_repair_replay_retry_confirmed: boolean;
  no_referral_or_campaign_mutation_confirmed: boolean;
  no_progress_or_attribution_mutation_confirmed: boolean;
  no_report_or_export_mutation_confirmed: boolean;
  no_invite_delivery_confirmed: boolean;
  no_credential_or_auth_claim_change_confirmed: boolean;
  no_tenant_code_exposure_confirmed: boolean;
  no_billing_or_money_movement_confirmed: boolean;
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

export type ReferralSaasAccountCampaignSetupCreateRequest = {
  accountRef: string;
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  campaign: {
    name: string;
    segment: string;
    startsAt?: string | null;
    endsAt?: string | null;
    maxUses?: number | null;
  };
  setupIntent?: {
    reason?: string;
  };
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasAccountCampaignSetupCreateResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  campaignSetup: {
    commandStatus: string;
    accountRef: string;
    campaign: {
      campaignRef: string;
      campaignCode: string;
      name: string;
      segment: string;
      setupStatus: string;
      isActive: boolean;
      startsAt?: string | null;
      endsAt?: string | null;
      maxUses?: number | null;
    };
    idempotency: {
      status: string;
    };
    audit: {
      accountAuditEventId?: string | null;
    };
    nextActions: string[];
    guardrails: string[];
    redactions: string[];
  };
  guardrails: string[];
  redactions: string[];
  no_campaign_activation_confirmed: boolean;
  no_link_generation_confirmed: boolean;
  no_validation_track_created_confirmed: boolean;
  no_policy_write_confirmed: boolean;
  no_webhook_delivery_confirmed: boolean;
  no_money_movement_confirmed: boolean;
};

export type ReferralSaasAccountCampaignPolicySettingsRequest = {
  accountRef: string;
  campaignCode: string;
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  policySettings: {
    version: number;
    attributionWindowDays?: number | null;
    eligibilityRules: Array<{
      rule: string;
      enabled: boolean;
    }>;
    productWindows: Record<string, { days: number }>;
    productRules: Record<string, { requiresAcceptedTerms: boolean }>;
    rewardVisibility: {
      mode: string;
      notes?: string;
    };
  };
  setupIntent?: {
    requestedStatus?: string;
    reason?: string;
  };
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasAccountCampaignPolicySettingsResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  policySettings: {
    commandStatus: string;
    accountRef: string;
    campaignRef: string;
    policySettings: {
      version: number;
      setupStatus: string;
      attributionWindowDays?: number | null;
      eligibilityRuleCount: number;
      productWindowCount: number;
      productRuleCount: number;
      rewardVisibilityStatus: string;
    };
    idempotency: {
      status: string;
    };
    audit: {
      accountAuditEventId?: string | null;
    };
    nextActions: string[];
    guardrails: string[];
    redactions: string[];
  };
  guardrails: string[];
  redactions: string[];
  no_campaign_activation_confirmed: boolean;
  no_link_generation_confirmed: boolean;
  no_validation_track_created_confirmed: boolean;
  no_webhook_delivery_confirmed: boolean;
  no_money_movement_confirmed: boolean;
};

export type ReferralSaasAccountCampaignReviewSubmissionRequest = {
  accountRef: string;
  campaignCode: string;
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  reviewSubmission: {
    setupSummary: string;
    requestedReviewStatus?: string;
    operatorNotes?: string;
  };
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasAccountCampaignReviewDecisionRequest = {
  accountRef: string;
  campaignCode: string;
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  reviewDecision: {
    decision: "APPROVED" | "BLOCKED";
    reason: string;
    reviewerRef: string;
  };
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasAccountCampaignReviewResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  campaignReview: {
    commandStatus: string;
    accountRef: string;
    campaignRef: string;
    previousReviewStatus: string;
    reviewStatus: string;
    setupStatus: string;
    readinessStatus: string;
    activationEligibility: string;
    activationStatus: string;
    reviewerAction: string;
    idempotency: {
      status: string;
    };
    audit: {
      accountAuditEventId?: string | null;
    };
    nextActions: string[];
    guardrails: string[];
    redactions: string[];
  };
  guardrails: string[];
  redactions: string[];
  no_campaign_activation_confirmed: boolean;
  no_link_generation_confirmed: boolean;
  no_validation_track_created_confirmed: boolean;
  no_webhook_delivery_confirmed: boolean;
  no_invite_or_seat_change_confirmed: boolean;
  no_money_movement_confirmed: boolean;
};

export type ReferralSaasAccountCampaignActivationRequest = {
  accountRef: string;
  campaignCode: string;
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  activationRequest: {
    requestedLifecycleStatus: "ACTIVE";
    reviewStatus: "REVIEW_APPROVED";
    goLiveReason: string;
    operatorNotes?: string;
    activationWindow?: {
      startsAt?: string | null;
      endsAt?: string | null;
    };
  };
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasAccountCampaignActivationResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  campaignActivation: {
    commandStatus: string;
    accountRef: string;
    campaignRef: string;
    campaignActivation: {
      previousLifecycle: string;
      lifecycle: string;
      reviewStatus: string;
      activationEligibility: string;
      activationStatus: string;
      readinessStatus: string;
    };
    idempotency: {
      status: string;
    };
    audit: {
      accountAuditEventId?: string | null;
    };
    nextActions: string[];
    guardrails: string[];
    redactions: string[];
  };
  guardrails: string[];
  redactions: string[];
  no_link_generation_confirmed: boolean;
  no_validation_track_created_confirmed: boolean;
  no_webhook_delivery_confirmed: boolean;
  no_invite_or_seat_change_confirmed: boolean;
  no_credential_creation_confirmed: boolean;
  no_billing_or_money_movement_confirmed: boolean;
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

export type ReferralSaasMembershipInvitationUpdateRequest = {
  accountRef: string;
  membershipRef: string;
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  actor: {
    emailHash?: string;
    displayName?: string;
  };
  membership: {
    roleFamily: string;
    permissionSet: string;
  };
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasMembershipInvitationCancelRequest = {
  accountRef: string;
  membershipRef: string;
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
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

export type ReferralSaasAccessProvisioningRequest = {
  accountRef: string;
  membershipRef: string;
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  provisioning: {
    seatType:
      | "ADMIN"
      | "OPERATOR"
      | "PARTNER"
      | "PRODUCER"
      | "DISTRIBUTOR"
      | "CONSUMER"
      | "SUPPORT";
    seatAssignmentEvidenceRef?: string;
    authProviderRef?: string;
    authClaimEvidenceRef?: string;
    operatorNotes?: string;
  };
  reasonCode?: string;
  correlationId: string;
  idempotencyKey: string;
};

export type ReferralSaasAccountFoundationActivationRequest = {
  accountRef: string;
  accountScope: {
    refType: "external_tenant_ref" | "organisation_ref";
    externalRef: string;
    context?: ReferralSaasAccountResolutionContext;
  };
  activation: {
    seatTypes: ("ADMIN" | "OPERATOR" | "SUPPORT")[];
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

export type ReferralSaasMembershipInvitationLifecycleResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  invitation: {
    commandStatus: string;
    membership: {
      membershipRef: string;
      previousStatus: string;
      status: string;
      previousRoleFamily?: string;
      roleFamily: string;
      previousPermissionSet?: string;
      permissionSet: string;
      canOperateSetup?: boolean;
    };
    lifecycle: {
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

export type ReferralSaasAccessProvisioningResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  accessProvisioning: {
    commandStatus: string;
    membership: {
      membershipRef: string;
      roleFamily: string;
      permissionSet: string;
    };
    seat: {
      seatType: string;
      seatAssignmentStatus: string;
      seatRef?: string | null;
    };
    authClaims: {
      authClaimStatus: string;
    };
    provisioning: {
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
    noCredentialCreationConfirmed: boolean;
    noCampaignActivationConfirmed: boolean;
    noGoLiveChangeConfirmed: boolean;
    noMoneyMovementConfirmed: boolean;
  };
  guardrails: string[];
  redactions: string[];
  no_invite_delivery_confirmed: boolean;
  no_auth_claim_change_confirmed: boolean;
  no_credential_creation_confirmed: boolean;
  no_campaign_activation_confirmed: boolean;
  no_go_live_change_confirmed: boolean;
  no_money_movement_confirmed: boolean;
};

export type ReferralSaasAccountFoundationActivationResponse = {
  status: string;
  context: ReferralSaasAccountResolutionContext;
  account: ReferralSaasAccountSummary;
  activation: {
    accountId: string;
    accountCode: string;
    accountName: string;
    previousAccountStatus: string;
    accountStatus: string;
    previousOnboardingStatus: string;
    onboardingStatus: string;
    previousTenantLinkStatus?: string | null;
    tenantLinkStatus?: string | null;
    seatCapacity: {
      seatTypes: string[];
      createdSeatCount: number;
    };
    commandStatus: string;
    auditEventId?: string | null;
    idempotency: {
      status: string;
    };
    guardrails: string[];
    redactions: string[];
    noMembershipWriteConfirmed: boolean;
    noSeatAssignmentConfirmed: boolean;
    noInviteDeliveryConfirmed: boolean;
    noAuthClaimChangeConfirmed: boolean;
    noCredentialCreationConfirmed: boolean;
    noCampaignActivationConfirmed: boolean;
    noGoLiveActionConfirmed: boolean;
    noBillingOrMoneyMovementConfirmed: boolean;
  };
  guardrails: string[];
  redactions: string[];
  no_membership_write_confirmed: boolean;
  no_seat_assignment_confirmed: boolean;
  no_invite_delivery_confirmed: boolean;
  no_auth_claim_change_confirmed: boolean;
  no_credential_creation_confirmed: boolean;
  no_campaign_activation_confirmed: boolean;
  no_go_live_action_confirmed: boolean;
  no_billing_or_money_movement_confirmed: boolean;
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

export function requestReferralSaasAccountFoundationActivation({
  accountRef,
  accountScope,
  activation,
  reasonCode,
  correlationId,
  idempotencyKey,
}: ReferralSaasAccountFoundationActivationRequest): Promise<ReferralSaasAccountFoundationActivationResponse> {
  return apiRequest<ReferralSaasAccountFoundationActivationResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/activation-requests`,
    {
      method: "POST",
      body: {
        accountScope: {
          refType: accountScope.refType,
          externalRef: accountScope.externalRef.trim(),
          context: accountScope.context || "setup",
        },
        activation: {
          seatTypes: activation.seatTypes,
        },
        reasonCode: reasonCode?.trim() || "CUSTOMER_ACCOUNT_FOUNDATION_ACTIVATION",
        correlationId,
        idempotencyKey,
      },
    },
  );
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

export function listReferralSaasAccountSupportCases({
  accountRef,
  refType,
  externalRef,
  context = "setup",
  status,
  limit = 50,
}: ReferralSaasSupportCaseListRequest): Promise<ReferralSaasSupportCaseListResponse> {
  return apiRequest<ReferralSaasSupportCaseListResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/support-cases`,
    {
      query: {
        ref_type: refType,
        external_ref: externalRef.trim(),
        context,
        status: status?.trim() || undefined,
        limit,
      },
    },
  );
}

export function createReferralSaasAccountSupportCase({
  accountRef,
  accountScope,
  category,
  priority,
  title,
  summary,
  sourceSurface,
  evidenceLinks = [],
  reasonCode,
  correlationId,
  idempotencyKey,
}: ReferralSaasSupportCaseCreateRequest): Promise<ReferralSaasSupportCaseCreateResponse> {
  return apiRequest<ReferralSaasSupportCaseCreateResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/support-cases`,
    {
      method: "POST",
      body: {
        accountScope: {
          refType: accountScope.refType,
          externalRef: accountScope.externalRef.trim(),
          context: accountScope.context || "setup",
        },
        category: category.trim(),
        priority: priority.trim(),
        title: title.trim(),
        summary: summary.trim(),
        sourceSurface: sourceSurface?.trim() || undefined,
        evidenceLinks: evidenceLinks.map((link) => ({
          evidenceType: link.evidenceType.trim(),
          evidenceRef: link.evidenceRef.trim(),
          safeStatus: link.safeStatus?.trim() || undefined,
          warningCode: link.warningCode?.trim() || undefined,
          missingEvidenceCode: link.missingEvidenceCode?.trim() || undefined,
          redactions: link.redactions || [],
        })),
        reasonCode: reasonCode?.trim() || "CUSTOMER_SUPPORT_CASE_CREATED",
        correlationId: correlationId.trim(),
        idempotencyKey: idempotencyKey.trim(),
      },
    },
  );
}

export function createReferralSaasAccountCampaignSetup({
  accountRef,
  accountScope,
  campaign,
  setupIntent,
  correlationId,
  idempotencyKey,
}: ReferralSaasAccountCampaignSetupCreateRequest): Promise<ReferralSaasAccountCampaignSetupCreateResponse> {
  return apiRequest<ReferralSaasAccountCampaignSetupCreateResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/campaigns`,
    {
      method: "POST",
      body: {
        accountScope: {
          refType: accountScope.refType,
          externalRef: accountScope.externalRef.trim(),
          context: accountScope.context || "setup",
        },
        campaign: {
          name: campaign.name.trim(),
          segment: campaign.segment.trim(),
          startsAt: campaign.startsAt || null,
          endsAt: campaign.endsAt || null,
          maxUses: campaign.maxUses ?? null,
        },
        setupIntent: {
          reason: setupIntent?.reason?.trim() || "CUSTOMER_PROFILE_CAMPAIGN_SETUP",
        },
        correlationId,
        idempotencyKey,
      },
    },
  );
}

export function updateReferralSaasAccountCampaignPolicySettings({
  accountRef,
  campaignCode,
  accountScope,
  policySettings,
  setupIntent,
  reasonCode,
  correlationId,
  idempotencyKey,
}: ReferralSaasAccountCampaignPolicySettingsRequest): Promise<ReferralSaasAccountCampaignPolicySettingsResponse> {
  return apiRequest<ReferralSaasAccountCampaignPolicySettingsResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/campaigns/${encodeURIComponent(
      campaignCode.trim(),
    )}/policy-settings`,
    {
      method: "PUT",
      body: {
        accountScope: {
          refType: accountScope.refType,
          externalRef: accountScope.externalRef.trim(),
          context: accountScope.context || "setup",
        },
        policySettings: {
          version: policySettings.version,
          attributionWindowDays: policySettings.attributionWindowDays ?? null,
          eligibilityRules: policySettings.eligibilityRules.map((rule) => ({
            rule: rule.rule.trim(),
            enabled: rule.enabled,
          })),
          productWindows: policySettings.productWindows,
          productRules: policySettings.productRules,
          rewardVisibility: {
            mode: policySettings.rewardVisibility.mode.trim(),
            notes: policySettings.rewardVisibility.notes?.trim() || undefined,
          },
        },
        setupIntent: {
          requestedStatus: setupIntent?.requestedStatus?.trim() || "POLICY_SETTINGS_RECORDED",
          reason: setupIntent?.reason?.trim() || "CUSTOMER_PROFILE_CAMPAIGN_POLICY_SETTINGS",
        },
        reasonCode: reasonCode?.trim() || "CUSTOMER_PROFILE_CAMPAIGN_POLICY_SETTINGS",
        correlationId,
        idempotencyKey,
      },
    },
  );
}

export function submitReferralSaasAccountCampaignReview({
  accountRef,
  campaignCode,
  accountScope,
  reviewSubmission,
  reasonCode,
  correlationId,
  idempotencyKey,
}: ReferralSaasAccountCampaignReviewSubmissionRequest): Promise<ReferralSaasAccountCampaignReviewResponse> {
  return apiRequest<ReferralSaasAccountCampaignReviewResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/campaigns/${encodeURIComponent(
      campaignCode.trim(),
    )}/review-submissions`,
    {
      method: "POST",
      body: {
        accountScope: {
          refType: accountScope.refType,
          externalRef: accountScope.externalRef.trim(),
          context: accountScope.context || "setup",
        },
        reviewSubmission: {
          setupSummary: reviewSubmission.setupSummary.trim(),
          requestedReviewStatus: reviewSubmission.requestedReviewStatus?.trim() || "READY_FOR_REVIEW",
          operatorNotes: reviewSubmission.operatorNotes?.trim() || undefined,
        },
        reasonCode: reasonCode?.trim() || "CUSTOMER_PROFILE_CAMPAIGN_REVIEW_SUBMISSION",
        correlationId,
        idempotencyKey,
      },
    },
  );
}

export function recordReferralSaasAccountCampaignReviewDecision({
  accountRef,
  campaignCode,
  accountScope,
  reviewDecision,
  reasonCode,
  correlationId,
  idempotencyKey,
}: ReferralSaasAccountCampaignReviewDecisionRequest): Promise<ReferralSaasAccountCampaignReviewResponse> {
  return apiRequest<ReferralSaasAccountCampaignReviewResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/campaigns/${encodeURIComponent(
      campaignCode.trim(),
    )}/review-decisions`,
    {
      method: "POST",
      body: {
        accountScope: {
          refType: accountScope.refType,
          externalRef: accountScope.externalRef.trim(),
          context: accountScope.context || "setup",
        },
        reviewDecision: {
          decision: reviewDecision.decision,
          reason: reviewDecision.reason.trim(),
          reviewerRef: reviewDecision.reviewerRef.trim(),
        },
        reasonCode: reasonCode?.trim() || "CUSTOMER_PROFILE_CAMPAIGN_REVIEW_DECISION",
        correlationId,
        idempotencyKey,
      },
    },
  );
}

export function requestReferralSaasAccountCampaignActivation({
  accountRef,
  campaignCode,
  accountScope,
  activationRequest,
  reasonCode,
  correlationId,
  idempotencyKey,
}: ReferralSaasAccountCampaignActivationRequest): Promise<ReferralSaasAccountCampaignActivationResponse> {
  return apiRequest<ReferralSaasAccountCampaignActivationResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/campaigns/${encodeURIComponent(
      campaignCode.trim(),
    )}/activation-requests`,
    {
      method: "POST",
      body: {
        accountScope: {
          refType: accountScope.refType,
          externalRef: accountScope.externalRef.trim(),
          context: accountScope.context || "setup",
        },
        activationRequest: {
          requestedLifecycleStatus: activationRequest.requestedLifecycleStatus,
          reviewStatus: activationRequest.reviewStatus,
          goLiveReason: activationRequest.goLiveReason.trim(),
          operatorNotes: activationRequest.operatorNotes?.trim() || undefined,
          activationWindow: activationRequest.activationWindow
            ? {
                startsAt: activationRequest.activationWindow.startsAt || null,
                endsAt: activationRequest.activationWindow.endsAt || null,
              }
            : undefined,
        },
        reasonCode: reasonCode?.trim() || "CUSTOMER_PROFILE_CAMPAIGN_ACTIVATION_REQUEST",
        correlationId,
        idempotencyKey,
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

export function updateReferralSaasMembershipInvitationIntent({
  accountRef,
  membershipRef,
  accountScope,
  actor,
  membership,
  reasonCode = "CUSTOMER_PROFILE_ACCESS_INTENT_UPDATE",
  correlationId,
  idempotencyKey,
}: ReferralSaasMembershipInvitationUpdateRequest): Promise<ReferralSaasMembershipInvitationLifecycleResponse> {
  return apiRequest<ReferralSaasMembershipInvitationLifecycleResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/membership-invitations/${encodeURIComponent(
      membershipRef.trim(),
    )}`,
    {
      method: "PATCH",
      body: {
        accountScope: {
          refType: accountScope.refType,
          externalRef: accountScope.externalRef.trim(),
          context: accountScope.context || "setup",
        },
        actor: {
          emailHash: actor.emailHash?.trim() || undefined,
          displayName: actor.displayName?.trim() || undefined,
        },
        membership: {
          roleFamily: membership.roleFamily.trim(),
          permissionSet: membership.permissionSet.trim(),
        },
        reasonCode,
        correlationId,
        idempotencyKey,
      },
    },
  );
}

export function cancelReferralSaasMembershipInvitationIntent({
  accountRef,
  membershipRef,
  accountScope,
  reasonCode = "CUSTOMER_PROFILE_ACCESS_INTENT_CANCEL",
  correlationId,
  idempotencyKey,
}: ReferralSaasMembershipInvitationCancelRequest): Promise<ReferralSaasMembershipInvitationLifecycleResponse> {
  return apiRequest<ReferralSaasMembershipInvitationLifecycleResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/membership-invitations/${encodeURIComponent(
      membershipRef.trim(),
    )}`,
    {
      method: "DELETE",
      body: {
        accountScope: {
          refType: accountScope.refType,
          externalRef: accountScope.externalRef.trim(),
          context: accountScope.context || "setup",
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

export function requestReferralSaasAccessProvisioning({
  accountRef,
  membershipRef,
  accountScope,
  provisioning,
  reasonCode = "CUSTOMER_PROFILE_ACCESS_PROVISIONING_REQUEST",
  correlationId,
  idempotencyKey,
}: ReferralSaasAccessProvisioningRequest): Promise<ReferralSaasAccessProvisioningResponse> {
  return apiRequest<ReferralSaasAccessProvisioningResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/memberships/${encodeURIComponent(
      membershipRef.trim(),
    )}/access-provisioning`,
    {
      method: "POST",
      body: {
        accountScope: {
          refType: accountScope.refType,
          externalRef: accountScope.externalRef.trim(),
          context: accountScope.context || "setup",
        },
        provisioning: {
          seatType: provisioning.seatType,
          seatAssignmentEvidenceRef: provisioning.seatAssignmentEvidenceRef?.trim() || undefined,
          authProviderRef: provisioning.authProviderRef?.trim() || undefined,
          authClaimEvidenceRef: provisioning.authClaimEvidenceRef?.trim() || undefined,
          operatorNotes: provisioning.operatorNotes?.trim() || undefined,
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

export function getReferralSaasIntegrationConfiguration({
  accountRef,
  refType,
  externalRef,
  context = "setup",
}: ReferralSaasIntegrationConfigurationReadRequest): Promise<ReferralSaasIntegrationConfigurationReadResponse> {
  return apiRequest<ReferralSaasIntegrationConfigurationReadResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/integrations/configuration`,
    {
      query: {
        ref_type: refType,
        external_ref: externalRef.trim(),
        context,
      },
    },
  );
}

export function getReferralSaasIntegrationExecutionReadiness({
  accountRef,
  refType,
  externalRef,
  context = "setup",
}: ReferralSaasIntegrationConfigurationReadRequest): Promise<ReferralSaasIntegrationExecutionReadinessResponse> {
  return apiRequest<ReferralSaasIntegrationExecutionReadinessResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/integrations/execution-readiness`,
    {
      query: {
        ref_type: refType,
        external_ref: externalRef.trim(),
        context,
      },
    },
  );
}

export function recordReferralSaasApiAccessVerification({
  accountRef,
  ...payload
}: ReferralSaasApiAccessVerificationPayload & {
  accountRef: string;
}): Promise<ReferralSaasApiAccessVerificationResponse> {
  return apiRequest<ReferralSaasApiAccessVerificationResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/integrations/api-access/verification`,
    {
      method: "POST",
      body: {
        accountScope: {
          refType: payload.accountScope.refType,
          externalRef: payload.accountScope.externalRef.trim(),
          context: payload.accountScope.context || "setup",
        },
        verification: payload.verification,
        reasonCode: payload.reasonCode?.trim() || undefined,
        correlationId: payload.correlationId.trim(),
        idempotencyKey: payload.idempotencyKey.trim(),
      },
    },
  );
}

export function recordReferralSaasWebhookTestDispatch({
  accountRef,
  ...payload
}: ReferralSaasWebhookTestDispatchPayload & {
  accountRef: string;
}): Promise<ReferralSaasWebhookTestDispatchResponse> {
  return apiRequest<ReferralSaasWebhookTestDispatchResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/integrations/webhooks/test-dispatch`,
    {
      method: "POST",
      body: {
        accountScope: {
          refType: payload.accountScope.refType,
          externalRef: payload.accountScope.externalRef.trim(),
          context: payload.accountScope.context || "setup",
        },
        webhookTest: payload.webhookTest,
        reasonCode: payload.reasonCode?.trim() || undefined,
        correlationId: payload.correlationId.trim(),
        idempotencyKey: payload.idempotencyKey.trim(),
      },
    },
  );
}

export function recordReferralSaasMessageProviderTest({
  accountRef,
  ...payload
}: ReferralSaasMessageProviderTestPayload & {
  accountRef: string;
}): Promise<ReferralSaasMessageProviderTestResponse> {
  return apiRequest<ReferralSaasMessageProviderTestResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/integrations/message-providers/test-check`,
    {
      method: "POST",
      body: {
        accountScope: {
          refType: payload.accountScope.refType,
          externalRef: payload.accountScope.externalRef.trim(),
          context: payload.accountScope.context || "setup",
        },
        messageProviderTest: payload.messageProviderTest,
        reasonCode: payload.reasonCode?.trim() || undefined,
        correlationId: payload.correlationId.trim(),
        idempotencyKey: payload.idempotencyKey.trim(),
      },
    },
  );
}

export function recordReferralSaasIntegrationCredentialRequest({
  accountRef,
  ...payload
}: ReferralSaasIntegrationCredentialRequestPayload & {
  accountRef: string;
}): Promise<ReferralSaasIntegrationCredentialRequestCreateResponse> {
  return apiRequest<ReferralSaasIntegrationCredentialRequestCreateResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/integrations/credential-requests`,
    {
      method: "POST",
      body: {
        accountScope: {
          refType: payload.accountScope.refType,
          externalRef: payload.accountScope.externalRef.trim(),
          context: payload.accountScope.context || "setup",
        },
        credentialRequest: {
          requestType: payload.credentialRequest.requestType.trim(),
          capability: payload.credentialRequest.capability.trim(),
          environment: payload.credentialRequest.environment?.trim() || undefined,
          intendedUse: payload.credentialRequest.intendedUse || [],
          requestedFor: payload.credentialRequest.requestedFor || {},
        },
        reasonCode: payload.reasonCode?.trim() || undefined,
        correlationId: payload.correlationId.trim(),
        idempotencyKey: payload.idempotencyKey.trim(),
      },
    },
  );
}

export function recordReferralSaasIntegrationCredentialReviewDecision({
  accountRef,
  credentialRequestRef,
  accountScope,
  reviewDecision,
  reasonCode,
  correlationId,
  idempotencyKey,
}: ReferralSaasIntegrationCredentialReviewDecisionRequest): Promise<ReferralSaasIntegrationCredentialReviewDecisionResponse> {
  return apiRequest<ReferralSaasIntegrationCredentialReviewDecisionResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(
      accountRef.trim(),
    )}/integrations/credential-requests/${encodeURIComponent(
      credentialRequestRef.trim(),
    )}/review-decisions`,
    {
      method: "POST",
      body: {
        accountScope: {
          refType: accountScope.refType,
          externalRef: accountScope.externalRef.trim(),
          context: accountScope.context || "setup",
        },
        reviewDecision: {
          decision: reviewDecision.decision,
          reason: reviewDecision.reason.trim(),
        },
        reasonCode: reasonCode?.trim() || "CUSTOMER_CREDENTIAL_REQUEST_REVIEW",
        correlationId: correlationId.trim(),
        idempotencyKey: idempotencyKey.trim(),
      },
    },
  );
}

export function recordReferralSaasIntegrationCredentialExecutionCheck({
  accountRef,
  credentialRequestRef,
  accountScope,
  executionCheck,
  reasonCode,
  correlationId,
  idempotencyKey,
}: ReferralSaasIntegrationCredentialExecutionCheckRequest): Promise<ReferralSaasIntegrationCredentialExecutionCheckResponse> {
  return apiRequest<ReferralSaasIntegrationCredentialExecutionCheckResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(
      accountRef.trim(),
    )}/integrations/credential-requests/${encodeURIComponent(
      credentialRequestRef.trim(),
    )}/execution-checks`,
    {
      method: "POST",
      body: {
        accountScope: {
          refType: accountScope.refType,
          externalRef: accountScope.externalRef.trim(),
          context: accountScope.context || "setup",
        },
        executionCheck: {
          reason: executionCheck.reason.trim(),
          reasonCode: executionCheck.reasonCode?.trim() || "CUSTOMER_CREDENTIAL_EXECUTION_READY_CHECK",
        },
        reasonCode: reasonCode?.trim() || "CUSTOMER_CREDENTIAL_EXECUTION_READY_CHECK",
        correlationId: correlationId.trim(),
        idempotencyKey: idempotencyKey.trim(),
      },
    },
  );
}

export function listReferralSaasIntegrationCredentialRequests({
  accountRef,
  refType,
  externalRef,
  context = "setup",
  limit = 50,
}: ReferralSaasIntegrationCredentialRequestListRequest): Promise<ReferralSaasIntegrationCredentialRequestListResponse> {
  return apiRequest<ReferralSaasIntegrationCredentialRequestListResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/integrations/credential-requests`,
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

export function validateReferralSaasIntegrationConfiguration({
  accountRef,
  ...payload
}: ReferralSaasIntegrationConfigurationPayload & {
  accountRef: string;
}): Promise<ReferralSaasIntegrationConfigurationValidateResponse> {
  return apiRequest<ReferralSaasIntegrationConfigurationValidateResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/integrations/configuration/validate`,
    {
      method: "POST",
      body: normaliseIntegrationConfigurationPayload(payload),
    },
  );
}

export function saveReferralSaasIntegrationConfiguration({
  accountRef,
  ...payload
}: ReferralSaasIntegrationConfigurationPayload & {
  accountRef: string;
}): Promise<ReferralSaasIntegrationConfigurationSaveResponse> {
  return apiRequest<ReferralSaasIntegrationConfigurationSaveResponse>(
    `v1/referral-saas/accounts/${encodeURIComponent(accountRef.trim())}/integrations/configuration`,
    {
      method: "PUT",
      body: normaliseIntegrationConfigurationPayload(payload),
    },
  );
}

function normaliseIntegrationConfigurationPayload(
  payload: ReferralSaasIntegrationConfigurationPayload,
) {
  return {
    accountScope: {
      refType: payload.accountScope.refType,
      externalRef: payload.accountScope.externalRef.trim(),
      context: payload.accountScope.context || "setup",
    },
    apiEnvironment: {
      environment: payload.apiEnvironment.environment,
      authMethod: payload.apiEnvironment.authMethod,
      useCases: payload.apiEnvironment.useCases,
    },
    webhookIntent: {
      callbackUrl: payload.webhookIntent.callbackUrl?.trim() || undefined,
      eventCategories: payload.webhookIntent.eventCategories,
      deliveryMode: payload.webhookIntent.deliveryMode,
    },
    messageProviders: {
      channels: payload.messageProviders.channels,
      providerRefs: payload.messageProviders.providerRefs
        .map((providerRef) => providerRef.trim())
        .filter(Boolean),
      approvalIntent: payload.messageProviders.approvalIntent,
    },
    reasonCode: payload.reasonCode?.trim() || undefined,
    correlationId: payload.correlationId?.trim() || undefined,
    idempotencyKey: payload.idempotencyKey?.trim() || undefined,
  };
}
