import { apiRequest } from "../client";

export type SettlementRecord = Record<string, unknown>;

export type CreateSettlementBatchRequest = {
  tenant_code: string;
  batch_reference: string;
  batch_type: string;
  created_by?: string;
};

export type AddSettlementBatchItemRequest = {
  settlement_id: string;
  amount: string;
};

export type RequestSettlementApprovalRequest = {
  approval_type: string;
  requested_by: string;
  comments?: string;
};

export type ApproveSettlementApprovalRequest = {
  approved_by: string;
  comments?: string;
};

export type RejectSettlementApprovalRequest = {
  rejected_by: string;
  comments?: string;
};

export function getAdminSettlements(tenantCode: string, limit = 25): Promise<SettlementRecord> {
  return apiRequest<SettlementRecord>("admin/settlements", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function getAdminSettlementExposure(tenantCode: string): Promise<SettlementRecord> {
  return apiRequest<SettlementRecord>("admin/settlements/exposure", {
    query: { tenant_code: tenantCode },
  });
}

export function getAdminSettlementBatches(tenantCode: string, limit = 25): Promise<SettlementRecord> {
  return apiRequest<SettlementRecord>("admin/settlement/batches", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function createAdminSettlementBatch(request: CreateSettlementBatchRequest): Promise<SettlementRecord> {
  return apiRequest<SettlementRecord>("admin/settlement/batches", {
    method: "POST",
    body: request,
  });
}

export function addAdminSettlementToBatch(
  batchId: string,
  request: AddSettlementBatchItemRequest,
): Promise<SettlementRecord> {
  return apiRequest<SettlementRecord>(`admin/settlement/batches/${encodeURIComponent(batchId)}/items`, {
    method: "POST",
    body: request,
  });
}

export function submitAdminSettlementBatch(batchId: string): Promise<SettlementRecord> {
  return apiRequest<SettlementRecord>(`admin/settlement/batches/${encodeURIComponent(batchId)}/submit`, {
    method: "POST",
  });
}

export function approveAdminSettlementBatch(batchId: string, approvedBy: string): Promise<SettlementRecord> {
  return apiRequest<SettlementRecord>(`admin/settlement/batches/${encodeURIComponent(batchId)}/approve`, {
    method: "POST",
    body: { approved_by: approvedBy },
  });
}

export function executeAdminSettlementBatch(batchId: string): Promise<SettlementRecord> {
  return apiRequest<SettlementRecord>(`admin/settlement/batches/${encodeURIComponent(batchId)}/execute`, {
    method: "POST",
  });
}

export function requestAdminSettlementBatchApproval(
  batchId: string,
  request: RequestSettlementApprovalRequest,
): Promise<SettlementRecord> {
  return apiRequest<SettlementRecord>(
    `admin/settlement/batches/${encodeURIComponent(batchId)}/approval/request`,
    {
      method: "POST",
      body: request,
    },
  );
}

export function getAdminSettlementBatchApprovals(batchId: string): Promise<SettlementRecord> {
  return apiRequest<SettlementRecord>(`admin/settlement/batches/${encodeURIComponent(batchId)}/approvals`);
}

export function approveAdminSettlementApproval(
  approvalId: string,
  request: ApproveSettlementApprovalRequest,
): Promise<SettlementRecord> {
  return apiRequest<SettlementRecord>(`admin/settlement/approvals/${encodeURIComponent(approvalId)}/approve`, {
    method: "POST",
    body: request,
  });
}

export function rejectAdminSettlementApproval(
  approvalId: string,
  request: RejectSettlementApprovalRequest,
): Promise<SettlementRecord> {
  return apiRequest<SettlementRecord>(`admin/settlement/approvals/${encodeURIComponent(approvalId)}/reject`, {
    method: "POST",
    body: request,
  });
}

export function getAdminSettlementPeriods(tenantCode: string, limit = 25): Promise<SettlementRecord> {
  return apiRequest<SettlementRecord>("admin/settlement/periods", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function getAdminSettlementCertifications(tenantCode: string, limit = 25): Promise<SettlementRecord> {
  return apiRequest<SettlementRecord>("admin/settlement/certifications", {
    query: { tenant_code: tenantCode, limit },
  });
}

export function getAdminSettlementReversals(tenantCode: string, limit = 25): Promise<SettlementRecord> {
  return apiRequest<SettlementRecord>("admin/settlement/reversals", {
    query: { tenant_code: tenantCode, limit },
  });
}
