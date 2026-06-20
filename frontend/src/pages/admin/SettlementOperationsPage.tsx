import { AlertTriangle, CheckCircle2, Landmark, PackageCheck, ReceiptText, Send, XCircle } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import {
  addAdminSettlementToBatch,
  approveAdminSettlementApproval,
  approveAdminSettlementBatch,
  createAdminSettlementBatch,
  executeAdminSettlementBatch,
  getAdminSettlementBatches,
  getAdminSettlementBatchApprovals,
  getAdminSettlementCertifications,
  getAdminSettlementExposure,
  getAdminSettlementPeriods,
  getAdminSettlementReversals,
  getAdminSettlements,
  rejectAdminSettlementApproval,
  requestAdminSettlementBatchApproval,
  submitAdminSettlementBatch,
} from "../../api/endpoints/settlement";
import { DataTable } from "../../components/DataTable";
import { ErrorPanel } from "../../components/ErrorPanel";
import { FieldLabel } from "../../components/FieldLabel";
import { ActionGuardrail, GuardrailItem, GuardrailTone } from "../../components/ActionGuardrail";
import { JourneyStep, JourneyTracker } from "../../components/JourneyTracker";
import { KpiCard } from "../../components/KpiCard";
import { LoadingState } from "../../components/LoadingState";
import { PanelTitle } from "../../components/PanelTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";
import { asArray, formatCurrency, formatDisplay, getValue, moneyValue, statusTone, useRefreshContext } from "../pageUtils";

const ADMIN_SETTLEMENT_TENANT_KEY = "amplifi.adminSettlement.tenant";

export function SettlementOperationsPage() {
  const { refreshKey } = useRefreshContext();
  const [tenantCode, setTenantCode] = useState(localStorage.getItem(ADMIN_SETTLEMENT_TENANT_KEY) || "FNB");
  const [submittedTenant, setSubmittedTenant] = useState(
    localStorage.getItem(ADMIN_SETTLEMENT_TENANT_KEY) || "FNB",
  );
  const [settlements, setSettlements] = useState<Record<string, unknown>[]>([]);
  const [exposure, setExposure] = useState<Record<string, unknown>[]>([]);
  const [batches, setBatches] = useState<Record<string, unknown>[]>([]);
  const [periods, setPeriods] = useState<Record<string, unknown>[]>([]);
  const [certifications, setCertifications] = useState<Record<string, unknown>[]>([]);
  const [reversals, setReversals] = useState<Record<string, unknown>[]>([]);
  const [approvals, setApprovals] = useState<Record<string, unknown>[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState("");
  const [selectedApprovalId, setSelectedApprovalId] = useState("");
  const [selectedSettlementId, setSelectedSettlementId] = useState("");
  const [batchReference, setBatchReference] = useState(`BATCH-${new Date().toISOString().slice(0, 10)}`);
  const [batchType, setBatchType] = useState("REWARD_SETTLEMENT");
  const [settlementAmount, setSettlementAmount] = useState("1.00");
  const [approvalType, setApprovalType] = useState("SETTLEMENT_BATCH_APPROVAL");
  const [approvalComments, setApprovalComments] = useState("");
  const [actor, setActor] = useState("ops");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionError, setActionError] = useState<unknown>(null);
  const [actionResult, setActionResult] = useState<Record<string, unknown> | null>(null);
  const [localRefreshKey, setLocalRefreshKey] = useState(0);

  useEffect(() => {
    if (!submittedTenant) {
      return;
    }

    let alive = true;
    setLoading(true);
    setError(null);
    Promise.all([
      getAdminSettlements(submittedTenant),
      getAdminSettlementExposure(submittedTenant),
      getAdminSettlementBatches(submittedTenant),
      getAdminSettlementPeriods(submittedTenant),
      getAdminSettlementCertifications(submittedTenant),
      getAdminSettlementReversals(submittedTenant),
    ])
      .then(([settlementPayload, exposurePayload, batchPayload, periodPayload, certificationPayload, reversalPayload]) => {
        if (alive) {
          setSettlements(asArray(settlementPayload));
          setExposure(asArray(exposurePayload));
          setBatches(asArray(batchPayload));
          setPeriods(asArray(periodPayload));
          setCertifications(asArray(certificationPayload));
          setReversals(asArray(reversalPayload));
        }
      })
      .catch((requestError) => alive && setError(requestError))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [submittedTenant, refreshKey, localRefreshKey]);

  useEffect(() => {
    if (!batches.length) {
      setSelectedBatchId("");
      return;
    }

    const current = batches.find((batch) => getValue(batch, ["batch_id", "settlement_batch_id", "id"]) === selectedBatchId);
    setSelectedBatchId(getValue(current || batches[0], ["batch_id", "settlement_batch_id", "id"], ""));
  }, [batches, selectedBatchId]);

  useEffect(() => {
    if (!settlements.length) {
      setSelectedSettlementId("");
      return;
    }

    const current = settlements.find((settlement) => getValue(settlement, ["settlement_id", "id"]) === selectedSettlementId);
    setSelectedSettlementId(getValue(current || settlements[0], ["settlement_id", "id"], ""));
  }, [settlements, selectedSettlementId]);

  useEffect(() => {
    if (!selectedBatchId) {
      setApprovals([]);
      return;
    }

    let alive = true;
    getAdminSettlementBatchApprovals(selectedBatchId)
      .then((payload) => alive && setApprovals(asArray(payload)))
      .catch(() => alive && setApprovals([]));
    return () => {
      alive = false;
    };
  }, [selectedBatchId, refreshKey, localRefreshKey]);

  useEffect(() => {
    if (!approvals.length) {
      setSelectedApprovalId("");
      return;
    }

    const current = approvals.find((approval) => getValue(approval, ["approval_id", "id"]) === selectedApprovalId);
    const pending = approvals.find((approval) => getValue(approval, ["approval_status", "status"]) === "PENDING");
    setSelectedApprovalId(getValue(current || pending || approvals[0], ["approval_id", "id"], ""));
  }, [approvals, selectedApprovalId]);

  const selectedBatch = batches.find((batch) => getValue(batch, ["batch_id", "settlement_batch_id", "id"]) === selectedBatchId);
  const selectedBatchStatus = selectedBatch ? getValue(selectedBatch, ["status", "batch_status"]) : "-";
  const selectedBatchItemCount = Number(selectedBatch ? getValue(selectedBatch, ["total_count", "item_count"], "0") : "0") || 0;
  const pendingApprovals = approvals.filter((approval) => getValue(approval, ["approval_status", "status"]) === "PENDING");
  const approvedApprovals = approvals.filter((approval) => getValue(approval, ["approval_status", "status"]) === "APPROVED");
  const draftBatches = batches.filter((batch) => getValue(batch, ["status", "batch_status"]) === "DRAFT");
  const readyBatches = batches.filter((batch) => getValue(batch, ["status", "batch_status"]) === "READY_FOR_APPROVAL");
  const approvedBatches = batches.filter((batch) => getValue(batch, ["status", "batch_status"]) === "APPROVED");
  const settlementExposureAmount = sumRows(exposure, ["amount", "total_amount", "exposure_amount"]);
  const settlementAmountTotal = sumRows(settlements, ["amount", "settlement_amount", "total_amount"]);
  const settlementNeedsAction = readyBatches.length > 0 || approvedBatches.length > 0 || pendingApprovals.length > 0;
  const canAddSettlement = selectedBatchStatus === "DRAFT" && Boolean(selectedBatchId && selectedSettlementId);
  const canSubmitBatch = selectedBatchStatus === "DRAFT" && selectedBatchItemCount > 0;
  const canRequestApproval = selectedBatchStatus === "READY_FOR_APPROVAL" && pendingApprovals.length === 0;
  const canDecideApproval = selectedBatchStatus === "READY_FOR_APPROVAL" && pendingApprovals.length > 0 && Boolean(selectedApprovalId);
  const canExecuteBatch = selectedBatchStatus === "APPROVED";
  const batchGuard = getSettlementBatchGuardrail({
    selectedBatch,
    selectedBatchStatus,
    selectedBatchItemCount,
    canAddSettlement,
    canSubmitBatch,
    canExecuteBatch,
    actionLoading,
  });
  const approvalGuard = getSettlementApprovalGuardrail({
    selectedBatchStatus,
    selectedBatchItemCount,
    pendingApprovalCount: pendingApprovals.length,
    canRequestApproval,
    canDecideApproval,
    actionLoading,
  });
  const batchGuidance = getBatchGuidance({
    batch: selectedBatch,
    settlements,
    pendingApprovalCount: pendingApprovals.length,
    approvedApprovalCount: approvedApprovals.length,
  });

  function submitTenant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedTenant = tenantCode.trim().toUpperCase();
    localStorage.setItem(ADMIN_SETTLEMENT_TENANT_KEY, cleanedTenant);
    setTenantCode(cleanedTenant);
    setSubmittedTenant(cleanedTenant);
    setActionError(null);
    setActionResult(null);
  }

  function runAction(label: string, action: () => Promise<Record<string, unknown>>) {
    setActionLoading(label);
    setActionError(null);
    setActionResult(null);
    action()
      .then((payload) => {
        setActionResult({ action: label, result: payload });
        setLocalRefreshKey((value) => value + 1);
      })
      .catch((requestError) => setActionError(requestError))
      .finally(() => setActionLoading(null));
  }

  function submitCreateBatch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!window.confirm("Create this settlement batch?")) {
      return;
    }
    runAction("Create settlement batch", () =>
      createAdminSettlementBatch({
        tenant_code: submittedTenant,
        batch_reference: batchReference.trim(),
        batch_type: batchType.trim() || "REWARD_SETTLEMENT",
        created_by: actor.trim() || undefined,
      }),
    );
  }

  function submitAddSettlement(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedBatchId || !selectedSettlementId) {
      return;
    }
    if (!window.confirm("Add this settlement to the selected batch?")) {
      return;
    }
    runAction("Add settlement to batch", () =>
      addAdminSettlementToBatch(selectedBatchId, {
        settlement_id: selectedSettlementId,
        amount: settlementAmount,
      }),
    );
  }

  function submitBatch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedBatchId && window.confirm("Submit this settlement batch for approval?")) {
      runAction("Submit settlement batch", () => submitAdminSettlementBatch(selectedBatchId));
    }
  }

  function approveBatch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedBatchId && window.confirm("Approve this settlement batch?")) {
      runAction("Approve settlement batch", () => approveAdminSettlementBatch(selectedBatchId, actor.trim() || "ops"));
    }
  }

  function executeBatch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedBatchId && window.confirm("Execute this settlement batch?")) {
      runAction("Execute settlement batch", () => executeAdminSettlementBatch(selectedBatchId));
    }
  }

  function requestApproval(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedBatchId && window.confirm("Request approval for this settlement batch?")) {
      runAction("Request settlement approval", () =>
        requestAdminSettlementBatchApproval(selectedBatchId, {
          approval_type: approvalType.trim() || "SETTLEMENT_BATCH_APPROVAL",
          requested_by: actor.trim() || "ops",
          comments: approvalComments.trim() || undefined,
        }),
      );
    }
  }

  function approveApproval(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedApprovalId && window.confirm("Approve this settlement approval request?")) {
      runAction("Approve settlement request", () =>
        approveAdminSettlementApproval(selectedApprovalId, {
          approved_by: actor.trim() || "ops",
          comments: approvalComments.trim() || undefined,
        }),
      );
    }
  }

  function rejectApproval(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedApprovalId && window.confirm("Reject this settlement approval request?")) {
      runAction("Reject settlement request", () =>
        rejectAdminSettlementApproval(selectedApprovalId, {
          rejected_by: actor.trim() || "ops",
          comments: approvalComments.trim() || undefined,
        }),
      );
    }
  }

  if (loading) {
    return <LoadingState label="Loading settlement operations" />;
  }

  if (error) {
    return <ErrorPanel error={error} />;
  }

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Amplifi Admin - Settlement Rail</div>
          <h1 className="page-title">Settlement Rail</h1>
          <p className="page-copy">
            Control the finance workflow that groups earned rewards into batches, checks exposure,
            records approval, and executes settlement only when the batch is ready.
          </p>
        </div>
        <StatusBadge label={settlementNeedsAction ? "Action needed" : "Finance control"} tone={settlementNeedsAction ? "warning" : "info"} />
      </section>

      <section className="settlement-rail-grid">
        <div className="settlement-rail-card primary">
          <div className="settlement-rail-card-top">
            <div>
              <div className="settlement-rail-kicker">Settlement posture</div>
              <h2>{settlementNeedsAction ? "Settlement work is waiting" : "Settlement rail is observable"}</h2>
            </div>
            {settlementNeedsAction ? <AlertTriangle size={24} /> : <CheckCircle2 size={24} />}
          </div>
          <p>
            Settlement turns earned rewards into controlled payouts. The operator prepares a batch, adds settlement
            items, requests approval, and executes only after finance control is satisfied.
          </p>
          <div className="settlement-rail-metrics">
            <SummaryItem label="Exposure" value={settlementExposureAmount ? formatCurrency(settlementExposureAmount) : exposure.length} />
            <SummaryItem label="Settlement value" value={settlementAmountTotal ? formatCurrency(settlementAmountTotal) : settlements.length} />
            <SummaryItem label="Draft batches" value={draftBatches.length} />
            <SummaryItem label="Pending approvals" value={pendingApprovals.length} />
          </div>
        </div>

        <div className="panel settlement-action-map">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Shows the safest next settlement actions and where the operator performs each one."
                title="Operator action map"
              />
              <div className="panel-subtitle">Where to prepare, approve, execute, and monitor.</div>
            </div>
          </div>
          <div className="panel-body admin-attention-list">
            <SettlementActionMapRow
              label="Create batch"
              copy="Start a controlled settlement batch for reward or commission payout."
              targetId="settlement-create-batch"
              value={batches.length ? `${batches.length} batches` : "Start"}
              tone={batches.length ? "info" : "warning"}
            />
            <SettlementActionMapRow
              label="Add settlement items"
              copy="Attach eligible settlement records before submitting the batch."
              targetId="settlement-batch-lifecycle"
              value={canAddSettlement ? "Ready" : `${settlements.length} records`}
              tone={canAddSettlement ? "success" : settlements.length ? "info" : "neutral"}
            />
            <SettlementActionMapRow
              label="Submit and approve"
              copy="Use the approval workflow to record four-eyes control before execution."
              targetId="settlement-approval-workflow"
              value={pendingApprovals.length ? `${pendingApprovals.length} pending` : readyBatches.length ? "Request" : "Waiting"}
              tone={pendingApprovals.length || readyBatches.length ? "warning" : "neutral"}
            />
            <SettlementActionMapRow
              label="Execute settlement"
              copy="Execute only when the selected batch is approved."
              targetId="settlement-batch-lifecycle"
              value={canExecuteBatch ? "Ready" : approvedBatches.length ? `${approvedBatches.length} ready` : "Blocked"}
              tone={canExecuteBatch || approvedBatches.length ? "success" : "neutral"}
            />
            <SettlementActionMapRow
              label="Monitor exposure"
              copy="Review provider exposure, settlement periods, certifications, and reversals."
              targetId="settlement-provider-exposure"
              value={`${exposure.length} providers`}
              tone={exposure.length ? "info" : "neutral"}
            />
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Sets the tenant context for settlement exposure, batches, periods, and controls."
              title="Settlement scope"
            />
            <div className="panel-subtitle">Required by settlement admin APIs.</div>
          </div>
        </div>
        <div className="panel-body">
          <form className="form-row treasury-scope-row" onSubmit={submitTenant}>
            <div className="field">
              <FieldLabel
                help="The tenant whose settlement operations should be loaded."
                htmlFor="settlement-tenant"
                label="Tenant code"
              />
              <input
                className="input"
                id="settlement-tenant"
                value={tenantCode}
                onChange={(event) => setTenantCode(event.target.value)}
              />
            </div>
            <button className="button" type="submit">
              Load settlements
            </button>
          </form>
        </div>
      </section>

      <section className="grid-3">
        <KpiCard label="Settlements" value={settlements.length} footnote="Settlement records" icon={ReceiptText} />
        <KpiCard label="Exposure" value={exposure.length} footnote="Provider exposure rows" icon={Landmark} />
        <KpiCard label="Batches" value={batches.length} footnote="Settlement batch records" icon={PackageCheck} />
      </section>

      <JourneyTracker
        badge={batchGuidance.badge}
        currentCopy={batchGuidance.copy}
        currentTitle={batchGuidance.title}
        steps={batchGuidance.steps}
        subtitle="Step-by-step path from batch preparation through approval and execution."
        title="Settlement journey"
        tone={batchGuidance.tone}
      />

      <section className="grid-2">
        <div className="panel" id="settlement-create-batch">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Creates a settlement batch that can collect settlement items before approval and execution."
                title="Create batch"
              />
              <div className="panel-subtitle">Prepare settlement batches for approval and execution.</div>
            </div>
          </div>
          <div className="panel-body">
            <form className="settlement-batch-form" onSubmit={submitCreateBatch}>
              <div className="field">
                <FieldLabel help="Unique reference used to identify this batch." htmlFor="settlement-batch-reference" label="Reference" />
                <input
                  className="input"
                  id="settlement-batch-reference"
                  value={batchReference}
                  onChange={(event) => setBatchReference(event.target.value)}
                />
              </div>
              <div className="field">
                <FieldLabel help="Batch category, normally reward settlement." htmlFor="settlement-batch-type" label="Type" />
                <input
                  className="input"
                  id="settlement-batch-type"
                  value={batchType}
                  onChange={(event) => setBatchType(event.target.value)}
                />
              </div>
              <div className="field">
                <FieldLabel help="Operator creating or approving the batch." htmlFor="settlement-actor" label="Actor" />
                <input className="input" id="settlement-actor" value={actor} onChange={(event) => setActor(event.target.value)} />
              </div>
              <button className="button" disabled={actionLoading !== null} type="submit">
                Create batch
              </button>
            </form>
          </div>
        </div>

        <div className="panel" id="settlement-batch-lifecycle">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Adds a settlement to a batch, then moves the batch through submit, approve, and execute states."
                title="Batch lifecycle"
              />
              <div className="panel-subtitle">Controlled settlement batch workflow.</div>
            </div>
            <StatusBadge label={selectedBatchStatus} tone={statusTone(selectedBatchStatus)} />
          </div>
          <div className="panel-body">
            <form className="settlement-item-form" onSubmit={submitAddSettlement}>
              <div className="field">
                <FieldLabel help="The batch receiving the settlement item." htmlFor="settlement-batch-select" label="Batch" />
                <select
                  className="input"
                  id="settlement-batch-select"
                  value={selectedBatchId}
                  onChange={(event) => setSelectedBatchId(event.target.value)}
                >
                  {batches.length ? null : <option value="">No batches returned</option>}
                  {batches.map((batch) => {
                    const batchId = getValue(batch, ["batch_id", "settlement_batch_id", "id"], "");
                    return (
                      <option key={batchId} value={batchId}>
                        {batchLabel(batch)}
                      </option>
                    );
                  })}
                </select>
              </div>
              <div className="field">
                <FieldLabel help="The settlement record to add into the selected batch." htmlFor="settlement-record-select" label="Settlement" />
                <select
                  className="input"
                  id="settlement-record-select"
                  value={selectedSettlementId}
                  onChange={(event) => setSelectedSettlementId(event.target.value)}
                >
                  {settlements.length ? null : <option value="">No settlements returned</option>}
                  {settlements.map((settlement) => {
                    const settlementId = getValue(settlement, ["settlement_id", "id"], "");
                    return (
                      <option key={settlementId} value={settlementId}>
                        {settlementLabel(settlement)}
                      </option>
                    );
                  })}
                </select>
              </div>
              <div className="field">
                <FieldLabel help="Amount to add for this settlement item." htmlFor="settlement-item-amount" label="Amount" />
                <input
                  className="input"
                  id="settlement-item-amount"
                  value={settlementAmount}
                  onChange={(event) => setSettlementAmount(event.target.value)}
                />
              </div>
              <button className="button" disabled={!canAddSettlement || actionLoading !== null} type="submit">
                Add item
              </button>
            </form>
            <div className="action-button-row">
              <form onSubmit={submitBatch}>
                <button className="button secondary" disabled={!canSubmitBatch || actionLoading !== null} type="submit">
                  <Send size={16} />
                  Submit
                </button>
              </form>
              <form onSubmit={approveBatch}>
                <button
                  className="button secondary"
                  disabled={selectedBatchStatus !== "READY_FOR_APPROVAL" || actionLoading !== null}
                  type="submit"
                >
                  <CheckCircle2 size={16} />
                  Approve
                </button>
              </form>
              <form onSubmit={executeBatch}>
                <button className="button secondary" disabled={!canExecuteBatch || actionLoading !== null} type="submit">
                  <CheckCircle2 size={16} />
                  Execute
                </button>
              </form>
            </div>
            <ActionGuardrail
              badge={batchGuard.badge}
              tone={batchGuard.tone}
              title={batchGuard.title}
              copy={batchGuard.copy}
              items={batchGuard.items}
            />
          </div>
        </div>
      </section>

      <section className="panel" id="settlement-approval-workflow">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Requests and records approval decisions for the selected settlement batch."
              title="Approval workflow"
            />
            <div className="panel-subtitle">Four-eyes control before settlement execution.</div>
          </div>
          <StatusBadge label={`${pendingApprovals.length} pending`} tone={pendingApprovals.length ? "warning" : "success"} />
        </div>
        <div className="panel-body">
          <form className="settlement-approval-form" onSubmit={requestApproval}>
            <div className="field">
              <FieldLabel help="The batch that will be sent for formal approval." htmlFor="approval-batch" label="Batch" />
              <select
                className="input"
                id="approval-batch"
                value={selectedBatchId}
                onChange={(event) => setSelectedBatchId(event.target.value)}
              >
                {batches.length ? null : <option value="">No batches returned</option>}
                {batches.map((batch) => {
                  const batchId = getValue(batch, ["batch_id", "settlement_batch_id", "id"], "");
                  return (
                    <option key={batchId} value={batchId}>
                      {batchLabel(batch)}
                    </option>
                  );
                })}
              </select>
            </div>
            <div className="field">
              <FieldLabel help="The kind of approval being requested." htmlFor="approval-type" label="Approval type" />
              <input
                className="input"
                id="approval-type"
                value={approvalType}
                onChange={(event) => setApprovalType(event.target.value)}
              />
            </div>
            <div className="field">
              <FieldLabel help="Optional reason or context for the approval request." htmlFor="approval-comments" label="Comments" />
              <input
                className="input"
                id="approval-comments"
                value={approvalComments}
                onChange={(event) => setApprovalComments(event.target.value)}
              />
            </div>
            <button className="button" disabled={!canRequestApproval || actionLoading !== null} type="submit">
              Request approval
            </button>
          </form>
          {canRequestApproval ? null : (
            <div className="field-hint approval-hint">{approvalActionHint(selectedBatchStatus, selectedBatchItemCount, pendingApprovals.length)}</div>
          )}
          <div className="action-button-row">
            <div className="field approval-select-field">
              <FieldLabel help="Pending or historical approval request for the selected batch." htmlFor="approval-select" label="Approval request" />
              <select
                className="input"
                id="approval-select"
                value={selectedApprovalId}
                onChange={(event) => setSelectedApprovalId(event.target.value)}
              >
                {approvals.length ? null : <option value="">No approvals returned</option>}
                {approvals.map((approval) => {
                  const approvalId = getValue(approval, ["approval_id", "id"], "");
                  return (
                    <option key={approvalId} value={approvalId}>
                      {approvalLabel(approval)}
                    </option>
                  );
                })}
              </select>
            </div>
            <form onSubmit={approveApproval}>
              <button className="button secondary" disabled={!canDecideApproval || actionLoading !== null} type="submit">
                <CheckCircle2 size={16} />
                Approve request
              </button>
            </form>
            <form onSubmit={rejectApproval}>
              <button className="button secondary" disabled={!canDecideApproval || actionLoading !== null} type="submit">
                <XCircle size={16} />
                Reject request
              </button>
            </form>
          </div>
          <ActionGuardrail
            badge={approvalGuard.badge}
            tone={approvalGuard.tone}
            title={approvalGuard.title}
            copy={approvalGuard.copy}
            items={approvalGuard.items}
          />
        </div>
      </section>

      {actionError ? <ErrorPanel error={actionError} /> : null}
      {actionResult ? <SettlementActionResult payload={actionResult} /> : null}

      <section className="grid-2">
        <SettlementTable
          id="settlement-provider-exposure"
          title="Provider exposure"
          help="Provider-level exposure shows how much settlement value is sitting with each provider."
          emptyText="No settlement exposure returned."
          rows={exposure}
          columns={[
            { key: "provider", header: "Provider", render: (row) => getValue(row, ["provider_key", "provider"]) },
            { key: "currency", header: "Currency", render: (row) => getValue(row, ["currency"]) },
            { key: "amount", header: "Amount", render: (row) => moneyValue(row, ["amount", "total_amount", "exposure_amount"], "0.00") },
            { key: "count", header: "Count", render: (row) => getValue(row, ["count", "settlement_count"], "0") },
          ]}
        />
        <SettlementTable
          title="Settlement periods"
          help="Settlement periods define open and closed windows for settlement activity."
          emptyText="No settlement periods returned."
          rows={periods}
          columns={[
            { key: "period", header: "Period", render: (row) => getValue(row, ["period_code", "period_id"]) },
            { key: "start", header: "Start", render: (row) => getValue(row, ["period_start"]) },
            { key: "end", header: "End", render: (row) => getValue(row, ["period_end"]) },
            {
              key: "status",
              header: "Status",
              render: (row) => {
                const status = getValue(row, ["status", "period_status"]);
                return <StatusBadge label={status} tone={statusTone(status)} />;
              },
            },
          ]}
        />
      </section>

      <SettlementTable
        id="settlement-records"
        title="Settlements"
        help="Individual settlement records moving through fulfilment."
        emptyText="No settlement records returned."
        rows={settlements}
        columns={[
          { key: "settlement", header: "Settlement", render: (row) => <span className="mono">{getValue(row, ["settlement_id", "id"])}</span> },
          { key: "provider", header: "Provider", render: (row) => getValue(row, ["provider_key", "provider"]) },
          { key: "amount", header: "Amount", render: (row) => moneyValue(row, ["amount", "settlement_amount", "total_amount"], "0.00") },
          { key: "currency", header: "Currency", render: (row) => getValue(row, ["currency"]) },
          {
            key: "status",
            header: "Status",
            render: (row) => {
              const status = getValue(row, ["status", "settlement_status"]);
              return <StatusBadge label={status} tone={statusTone(status)} />;
            },
          },
        ]}
      />

      <SettlementTable
        id="settlement-batches"
        title="Settlement batches"
        help="Batches group settlement records for approval and execution."
        emptyText="No settlement batches returned."
        rows={batches}
        columns={[
          { key: "batch", header: "Batch", render: (row) => <span className="mono">{getValue(row, ["batch_id", "settlement_batch_id", "id"])}</span> },
          { key: "reference", header: "Reference", render: (row) => getValue(row, ["batch_reference", "reference"]) },
          { key: "type", header: "Type", render: (row) => getValue(row, ["batch_type"]) },
          { key: "amount", header: "Amount", render: (row) => moneyValue(row, ["total_amount", "amount"], "0.00") },
          {
            key: "status",
            header: "Status",
            render: (row) => {
              const status = getValue(row, ["status", "batch_status"]);
              return <StatusBadge label={status} tone={statusTone(status)} />;
            },
          },
        ]}
      />

      <SettlementTable
        title="Batch approvals"
        help="Approval records show requested, approved, and rejected control decisions for the selected batch."
        emptyText="No batch approvals returned."
        rows={approvals}
        columns={[
          { key: "approval", header: "Approval", render: (row) => <span className="mono">{getValue(row, ["approval_id", "id"])}</span> },
          { key: "type", header: "Type", render: (row) => getValue(row, ["approval_type"]) },
          { key: "requester", header: "Requester", render: (row) => getValue(row, ["requested_by"], "-") },
          { key: "approver", header: "Approver", render: (row) => getValue(row, ["approved_by", "rejected_by"], "-") },
          {
            key: "status",
            header: "Status",
            render: (row) => {
              const status = getValue(row, ["approval_status", "status"]);
              return <StatusBadge label={status} tone={statusTone(status)} />;
            },
          },
        ]}
      />

      <section className="grid-2">
        <SettlementTable
          title="Certifications"
          help="Certification records compare expected and actual settlement values."
          emptyText="No settlement certifications returned."
          rows={certifications}
          columns={[
            { key: "certification", header: "Certification", render: (row) => <span className="mono">{getValue(row, ["certification_id", "id"])}</span> },
            { key: "expected", header: "Expected", render: (row) => moneyValue(row, ["expected_amount"], "0.00") },
            { key: "actual", header: "Actual", render: (row) => moneyValue(row, ["actual_amount"], "0.00") },
            {
              key: "status",
              header: "Status",
              render: (row) => {
                const status = getValue(row, ["status", "certification_status"]);
                return <StatusBadge label={status} tone={statusTone(status)} />;
              },
            },
          ]}
        />
        <SettlementTable
          title="Reversals"
          help="Reversal records show requested, approved, or executed settlement reversals."
          emptyText="No settlement reversals returned."
          rows={reversals}
          columns={[
            { key: "reversal", header: "Reversal", render: (row) => <span className="mono">{getValue(row, ["reversal_id", "id"])}</span> },
            { key: "settlement", header: "Settlement", render: (row) => <span className="mono">{getValue(row, ["settlement_id"], "-")}</span> },
            { key: "amount", header: "Amount", render: (row) => moneyValue(row, ["amount"], "0.00") },
            {
              key: "status",
              header: "Status",
              render: (row) => {
                const status = getValue(row, ["status", "reversal_status"]);
                return <StatusBadge label={status} tone={statusTone(status)} />;
              },
            },
          ]}
        />
      </section>
    </>
  );
}

function SettlementTable({
  id,
  title,
  help,
  emptyText,
  rows,
  columns,
}: {
  id?: string;
  title: string;
  help: string;
  emptyText: string;
  rows: Record<string, unknown>[];
  columns: Array<{
    key: string;
    header: string;
    render: (row: Record<string, unknown>) => React.ReactNode;
  }>;
}) {
  return (
    <section className="panel" id={id}>
      <div className="panel-header">
        <div>
          <PanelTitle help={help} title={title} />
          <div className="panel-subtitle">Latest records returned by the settlement APIs.</div>
        </div>
      </div>
      <DataTable emptyText={emptyText} rows={rows} columns={columns} />
    </section>
  );
}

function SettlementActionResult({ payload }: { payload: Record<string, unknown> }) {
  const result = (payload.result && typeof payload.result === "object" ? payload.result : {}) as Record<string, unknown>;
  const item = (result.item && typeof result.item === "object" ? result.item : result) as Record<string, unknown>;
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">Action result</h2>
          <div className="panel-subtitle">{getValue(payload, ["action"], "Settlement action")} completed.</div>
        </div>
        <StatusBadge label="Updated" tone="success" />
      </div>
      <div className="panel-body">
        <div className="summary-grid">
          <SummaryItem label="Batch" value={getValue(item, ["batch_id", "settlement_batch_id"], "-")} />
          <SummaryItem label="Settlement" value={getValue(item, ["settlement_id"], "-")} />
          <SummaryItem label="Status" value={getValue(item, ["status", "batch_status", "approval_status"], "-")} />
        </div>
      </div>
    </section>
  );
}

function SettlementActionMapRow({
  label,
  copy,
  targetId,
  value,
  tone,
}: {
  label: string;
  copy: string;
  targetId: string;
  value: string;
  tone: BadgeTone;
}) {
  return (
    <a className="admin-attention-row" href={`#${targetId}`}>
      <div>
        <div className="admin-attention-label">{label}</div>
        <div className="table-subtext">{copy}</div>
      </div>
      <StatusBadge label={value} tone={tone} />
    </a>
  );
}

function batchLabel(batch: Record<string, unknown>): string {
  return `${getValue(batch, ["batch_reference", "reference", "batch_id"])} | ${getValue(
    batch,
    ["status", "batch_status"],
  )}`;
}

function settlementLabel(settlement: Record<string, unknown>): string {
  return `${getValue(settlement, ["settlement_id", "id"])} | ${getValue(
    settlement,
    ["amount", "settlement_amount", "total_amount"],
    "0.00",
  )}`;
}

function sumRows(rows: Record<string, unknown>[], keys: string[]): number {
  return rows.reduce((total, row) => {
    const raw = getValue(row, keys, "0");
    const value = Number(String(raw).replace(/[^0-9.-]/g, ""));
    return Number.isFinite(value) ? total + value : total;
  }, 0);
}

function approvalLabel(approval: Record<string, unknown>): string {
  return `${getValue(approval, ["approval_type"], "Approval")} | ${getValue(
    approval,
    ["approval_status", "status"],
  )}`;
}

function approvalActionHint(batchStatus: string, itemCount: number, pendingApprovalCount: number): string {
  if (batchStatus === "DRAFT" && itemCount === 0) {
    return "Add settlement items before submitting the batch for approval.";
  }
  if (batchStatus === "DRAFT") {
    return "Submit the batch first. Approval can be requested once the batch is ready for approval.";
  }
  if (pendingApprovalCount > 0) {
    return "A pending approval already exists for this batch.";
  }
  if (batchStatus === "APPROVED") {
    return "This batch is already approved and can be executed.";
  }
  if (batchStatus === "SETTLED") {
    return "This batch has already settled.";
  }
  return "Approval requests are only available once the batch is ready for approval.";
}

type BadgeTone = GuardrailTone;

type Guardrail = {
  badge: string;
  tone: BadgeTone;
  title: string;
  copy: string;
  items: GuardrailItem[];
};

function getSettlementBatchGuardrail({
  selectedBatch,
  selectedBatchStatus,
  selectedBatchItemCount,
  canAddSettlement,
  canSubmitBatch,
  canExecuteBatch,
  actionLoading,
}: {
  selectedBatch: Record<string, unknown> | undefined;
  selectedBatchStatus: string;
  selectedBatchItemCount: number;
  canAddSettlement: boolean;
  canSubmitBatch: boolean;
  canExecuteBatch: boolean;
  actionLoading: string | null;
}): Guardrail {
  if (!selectedBatch) {
    return {
      badge: "Blocked",
      tone: "neutral",
      title: "Create or select a batch first",
      copy: "Batch actions are disabled until a settlement batch is available.",
      items: [
        { label: "Selected batch", value: "Missing", tone: "warning" },
        { label: "Add item", value: "Blocked", tone: "neutral" },
        { label: "System change", value: "None", tone: "success" },
      ],
    };
  }

  if (actionLoading) {
    return {
      badge: "Running",
      tone: "info",
      title: "Settlement action in progress",
      copy: "Wait for the backend response before taking another batch action.",
      items: [
        { label: "Current action", value: actionLoading, tone: "info" },
        { label: "Batch status", value: selectedBatchStatus, tone: statusTone(selectedBatchStatus) as BadgeTone },
        { label: "System change", value: "Settlement batch", tone: "warning" },
      ],
    };
  }

  return {
    badge: canAddSettlement || canSubmitBatch || canExecuteBatch ? "Ready" : "Blocked",
    tone: canAddSettlement || canSubmitBatch || canExecuteBatch ? "success" : "neutral",
    title: canExecuteBatch
      ? "Approved batch can be executed"
      : canSubmitBatch
        ? "Batch can be submitted"
        : canAddSettlement
          ? "Settlement item can be added"
          : "Next batch action is not available",
    copy:
      selectedBatchStatus === "DRAFT" && selectedBatchItemCount === 0
        ? "Add at least one settlement item before submitting this batch."
        : selectedBatchStatus === "READY_FOR_APPROVAL"
          ? "Approval controls now decide whether this batch can move forward."
          : selectedBatchStatus === "APPROVED"
            ? "Execution will move approved settlement items into the final settlement state."
            : "The selected batch status controls which settlement action is available.",
    items: [
      { label: "Batch status", value: selectedBatchStatus, tone: statusTone(selectedBatchStatus) as BadgeTone },
      { label: "Items", value: String(selectedBatchItemCount), tone: selectedBatchItemCount > 0 ? "success" : "warning" },
      { label: "System change", value: canExecuteBatch ? "Settlement execution" : "Batch status/items", tone: "warning" },
    ],
  };
}

function getSettlementApprovalGuardrail({
  selectedBatchStatus,
  selectedBatchItemCount,
  pendingApprovalCount,
  canRequestApproval,
  canDecideApproval,
  actionLoading,
}: {
  selectedBatchStatus: string;
  selectedBatchItemCount: number;
  pendingApprovalCount: number;
  canRequestApproval: boolean;
  canDecideApproval: boolean;
  actionLoading: string | null;
}): Guardrail {
  if (actionLoading) {
    return {
      badge: "Running",
      tone: "info",
      title: "Approval action in progress",
      copy: "Wait for the approval response before requesting, approving, or rejecting again.",
      items: [
        { label: "Current action", value: actionLoading, tone: "info" },
        { label: "Pending approvals", value: String(pendingApprovalCount), tone: pendingApprovalCount ? "warning" : "success" },
        { label: "System change", value: "Approval record", tone: "warning" },
      ],
    };
  }

  return {
    badge: canRequestApproval || canDecideApproval ? "Ready" : "Blocked",
    tone: canRequestApproval || canDecideApproval ? "success" : "neutral",
    title: canDecideApproval
      ? "Pending approval can be decided"
      : canRequestApproval
        ? "Approval request can be created"
        : "Approval step is waiting",
    copy: approvalActionHint(selectedBatchStatus, selectedBatchItemCount, pendingApprovalCount),
    items: [
      { label: "Batch status", value: selectedBatchStatus, tone: statusTone(selectedBatchStatus) as BadgeTone },
      { label: "Pending approvals", value: String(pendingApprovalCount), tone: pendingApprovalCount ? "warning" : "success" },
      { label: "System change", value: canRequestApproval || canDecideApproval ? "Approval record" : "None", tone: canRequestApproval || canDecideApproval ? "warning" : "success" },
    ],
  };
}

function getBatchGuidance({
  batch,
  settlements,
  pendingApprovalCount,
  approvedApprovalCount,
}: {
  batch: Record<string, unknown> | undefined;
  settlements: Record<string, unknown>[];
  pendingApprovalCount: number;
  approvedApprovalCount: number;
}): {
  badge: string;
  tone: BadgeTone;
  title: string;
  copy: string;
  steps: JourneyStep[];
} {
  if (!batch) {
    return {
      badge: "No batch",
      tone: "neutral",
      title: "Create a settlement batch",
      copy: settlements.length
        ? "There are settlement records available. Create a batch, then add settlement items before submitting it for approval."
        : "No batch is selected yet. Load or create settlement records before building a settlement batch.",
      steps: [
        settlementStep("Create batch", "Prepare a batch that will collect settlement records.", "current"),
        settlementStep("Add settlement items", "Attach one or more settlement records to the batch.", "waiting"),
        settlementStep("Submit and approve", "Lock the batch and record the approval decision.", "waiting"),
        settlementStep("Execute settlement", "Mark approved batch items as settled.", "waiting"),
      ],
    };
  }

  const status = getValue(batch, ["status", "batch_status"], "DRAFT");
  const totalCount = Number(getValue(batch, ["total_count", "item_count"], "0")) || 0;

  if (status === "DRAFT") {
    return {
      badge: "Prepare",
      tone: "info",
      title: totalCount > 0 ? "Submit the batch for approval" : "Add settlement items",
      copy:
        totalCount > 0
          ? "This batch has items and is still editable. Submit it when the item list and amount look right."
          : "This batch is empty. Add at least one settlement item before submitting it for approval.",
      steps: [
        settlementStep("Create batch", "Prepare a batch that will collect settlement records.", "done"),
        settlementStep(
          "Add settlement items",
          "Attach one or more settlement records to the batch.",
          totalCount > 0 ? "done" : "current",
        ),
        settlementStep(
          "Submit and approve",
          "Lock the batch and record the approval decision.",
          totalCount > 0 ? "current" : "waiting",
        ),
        settlementStep("Execute settlement", "Mark approved batch items as settled.", "waiting"),
      ],
    };
  }

  if (status === "READY_FOR_APPROVAL") {
    const hasApprovalSignal = pendingApprovalCount > 0 || approvedApprovalCount > 0;
    return {
      badge: hasApprovalSignal ? "Approval" : "Request approval",
      tone: hasApprovalSignal ? "warning" : "info",
      title: hasApprovalSignal ? "Approve or reject the pending request" : "Request formal approval",
      copy: hasApprovalSignal
        ? "The batch is ready and approval records exist. Approve the request to move the batch forward, or reject it if finance control fails."
        : "The batch is ready for approval but no approval request is visible yet. Request approval so the decision is recorded.",
      steps: [
        settlementStep("Create batch", "Prepare a batch that will collect settlement records.", "done"),
        settlementStep("Add settlement items", "Attach one or more settlement records to the batch.", "done"),
        settlementStep("Submit and approve", "Lock the batch and record the approval decision.", "current"),
        settlementStep("Execute settlement", "Mark approved batch items as settled.", "waiting"),
      ],
    };
  }

  if (status === "APPROVED") {
    return {
      badge: "Ready",
      tone: "success",
      title: "Execute the settlement batch",
      copy: "The batch is approved. Execute it when you are ready to mark the batch items as settled.",
      steps: [
        settlementStep("Create batch", "Prepare a batch that will collect settlement records.", "done"),
        settlementStep("Add settlement items", "Attach one or more settlement records to the batch.", "done"),
        settlementStep("Submit and approve", "Lock the batch and record the approval decision.", "done"),
        settlementStep("Execute settlement", "Mark approved batch items as settled.", "current"),
      ],
    };
  }

  if (status === "SETTLED" || status === "PROCESSING") {
    return {
      badge: status,
      tone: "success",
      title: status === "SETTLED" ? "Settlement completed" : "Settlement is processing",
      copy:
        status === "SETTLED"
          ? "This batch has completed its settlement lifecycle. Review certifications or reversals if follow-up control is needed."
          : "The batch is being processed. Wait for it to settle before taking further control actions.",
      steps: [
        settlementStep("Create batch", "Prepare a batch that will collect settlement records.", "done"),
        settlementStep("Add settlement items", "Attach one or more settlement records to the batch.", "done"),
        settlementStep("Submit and approve", "Lock the batch and record the approval decision.", "done"),
        settlementStep("Execute settlement", "Mark approved batch items as settled.", status === "SETTLED" ? "done" : "current"),
      ],
    };
  }

  return {
    badge: status,
    tone: statusTone(status) as BadgeTone,
    title: "Review the selected batch",
    copy: "This batch is in a status that needs manual review before the next settlement action is taken.",
    steps: [
      settlementStep("Create batch", "Prepare a batch that will collect settlement records.", "review"),
      settlementStep("Add settlement items", "Attach one or more settlement records to the batch.", "review"),
      settlementStep("Submit and approve", "Lock the batch and record the approval decision.", "review"),
      settlementStep("Execute settlement", "Mark approved batch items as settled.", "review"),
    ],
  };
}

function settlementStep(label: string, description: string, state: JourneyStep["state"]): JourneyStep {
  const workAreas: Record<string, string> = {
    "Create batch": "Create batch",
    "Add settlement items": "Batch lifecycle",
    "Submit and approve": "Approval workflow",
    "Execute settlement": "Batch lifecycle",
  };
  const targets: Record<string, string> = {
    "Create batch": "settlement-create-batch",
    "Add settlement items": "settlement-batch-lifecycle",
    "Submit and approve": "settlement-approval-workflow",
    "Execute settlement": "settlement-batch-lifecycle",
  };

  return { label, description, state, workArea: workAreas[label], targetId: targets[label] };
}
