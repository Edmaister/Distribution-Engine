import {
  Activity,
  AlertTriangle,
  FileWarning,
  Link as LinkIcon,
  Milestone,
  Search,
  ShieldCheck,
} from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import {
  inspectReferralSaasOperatorProgressStatus,
  type ReferralSaasProgressStatusViewerRole,
} from "../../api/endpoints/referralSaasLinks";
import { ErrorPanel } from "../../components/ErrorPanel";
import { KpiCard } from "../../components/KpiCard";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";
import { asArray, asRecord, formatDisplay, getNestedValue, getValue, statusTone } from "../pageUtils";

const defaultTenantCode = "FNB";
const defaultReferralTrackId = "11111111-1111-4111-8111-111111111111";

const viewerRoleOptions: Array<{ label: string; value: ReferralSaasProgressStatusViewerRole }> = [
  { label: "Referrer view", value: "referrer" },
  { label: "Customer view", value: "customer" },
  { label: "Operator view", value: "operator" },
];

export function ReferralSaasProgressStatusPage() {
  const [tenantCode, setTenantCode] = useState(defaultTenantCode);
  const [referralTrackId, setReferralTrackId] = useState(defaultReferralTrackId);
  const [viewerRole, setViewerRole] = useState<ReferralSaasProgressStatusViewerRole>("referrer");
  const canInspect = tenantCode.trim() !== "" && referralTrackId.trim() !== "";

  const progressMutation = useMutation({
    mutationFn: () =>
      inspectReferralSaasOperatorProgressStatus({
        tenantCode,
        referralTrackId,
        viewerRole,
      }),
  });

  const result = progressMutation.data;
  const progressStatus = asRecord(getNestedValue(result, ["progressStatus"], {}));
  const lookup = asRecord(getNestedValue(progressStatus, ["lookup"], {}));
  const progress = asRecord(getNestedValue(progressStatus, ["progress"], {}));
  const safeStatus = asRecord(getNestedValue(progressStatus, ["safeStatus"], {}));
  const missingEvidence = asArray(getNestedValue(progressStatus, ["missingEvidence"], []));
  const redactions = asArray(getNestedValue(progressStatus, ["redactions"], []));
  const nextDiagnostics = asArray(getNestedValue(progressStatus, ["nextDiagnostics"], []));
  const productStatus = getValue(safeStatus, ["product_status", "status"], "Waiting");
  const progressPercent = getValue(progress, ["progressPercent"], "0");
  const nextMilestone = getValue(progress, ["nextMilestone"]);

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Referral SaaS - Progress Support</div>
          <h1 className="page-title">Operator progress/status</h1>
          <p className="page-copy">
            Inspect safe progress and product status for one referral through
            the read-only progress/status diagnostics wrapper.
          </p>
        </div>
        <StatusBadge label={formatDisplay(productStatus)} tone={statusTone(productStatus)} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Progress lookup</h2>
            <div className="panel-subtitle">
              Operator-only route using the current tenant bridge until account support scope exists.
            </div>
          </div>
          <StatusBadge label="Read-only" tone="info" />
        </div>
        <div className="panel-body referral-link-code-controls">
          <label className="field">
            <span>Tenant code bridge</span>
            <input
              className="input"
              onChange={(event) => setTenantCode(event.target.value.toUpperCase())}
              value={tenantCode}
            />
          </label>
          <label className="field">
            <span>Referral track ID</span>
            <input
              className="input"
              onChange={(event) => setReferralTrackId(event.target.value)}
              value={referralTrackId}
            />
          </label>
          <label className="field">
            <span>Viewer projection</span>
            <select
              className="input"
              onChange={(event) =>
                setViewerRole(event.target.value as ReferralSaasProgressStatusViewerRole)
              }
              value={viewerRole}
            >
              {viewerRoleOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <button
            className="button"
            disabled={!canInspect || progressMutation.isPending}
            onClick={() => progressMutation.mutate()}
            type="button"
          >
            <Search size={16} />
            {progressMutation.isPending ? "Inspecting" : "Inspect progress"}
          </button>
        </div>
      </section>

      {progressMutation.error ? <ErrorPanel error={progressMutation.error} /> : null}

      <section className="grid-4">
        <KpiCard label="Product status" value={formatDisplay(productStatus)} footnote="Safe projection" icon={ShieldCheck} />
        <KpiCard label="Progress" value={`${progressPercent}%`} footnote="Current milestone progress" icon={Activity} />
        <KpiCard label="Missing evidence" value={missingEvidence.length} footnote="Support triage signals" icon={FileWarning} />
        <KpiCard label="Next diagnostics" value={nextDiagnostics.length} footnote="Read-only follow-up" icon={Milestone} />
      </section>

      <section className="grid-2">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Progress summary</h2>
              <div className="panel-subtitle">Safe progress evidence from the product wrapper.</div>
            </div>
            <StatusBadge label={formatDisplay(getValue(progress, ["progressBand"], "Waiting"))} tone="info" />
          </div>
          <div className="panel-body">
            <div className="summary-grid">
              <SummaryItem label="Lookup type" value={getValue(lookup, ["type"])} />
              <SummaryItem label="Lookup value" value={getValue(lookup, ["value"])} />
              <SummaryItem label="Tenant" value={getValue(progressStatus, ["tenantCode"], tenantCode)} />
              <SummaryItem label="Viewer role" value={getValue(progressStatus, ["viewerRole"], viewerRole)} />
              <SummaryItem label="Referral track" value={getValue(progress, ["referralTrackId"], referralTrackId)} />
              <SummaryItem label="Progress status" value={getValue(progress, ["status"])} />
              <SummaryItem label="Complete" value={getValue(progress, ["isComplete"])} />
              <SummaryItem label="Display status" value={getValue(progress, ["displayStatus"])} />
              <SummaryItem label="Next milestone" value={nextMilestone} />
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Safe status</h2>
              <div className="panel-subtitle">Product copy and action posture.</div>
            </div>
            <StatusBadge label={formatDisplay(productStatus)} tone={statusTone(productStatus)} />
          </div>
          <div className="panel-body">
            <div className="summary-grid">
              <SummaryItem label="Label" value={getValue(safeStatus, ["product_label", "label"])} />
              <SummaryItem label="Summary" value={getValue(safeStatus, ["summary"])} />
              <SummaryItem label="What happened" value={getValue(safeStatus, ["what_happened"])} />
              <SummaryItem label="What happens next" value={getValue(safeStatus, ["what_happens_next"])} />
              <SummaryItem label="Action required" value={getValue(safeStatus, ["action_required"])} />
              <SummaryItem label="Action category" value={getValue(safeStatus, ["action_category"])} />
              <SummaryItem label="Terminal" value={getValue(safeStatus, ["terminal"])} />
              <SummaryItem label="Confidence" value={getValue(safeStatus, ["source_confidence"])} />
            </div>
          </div>
        </div>
      </section>

      <section className="grid-4">
        <DiagnosticList
          emptyLabel="No missing evidence returned."
          items={missingEvidence}
          title="Missing evidence"
          typeKey="code"
        />
        <DiagnosticList
          emptyLabel="No next diagnostics available yet."
          items={nextDiagnostics}
          title="Next diagnostics"
          typeKey="type"
        />
        <DiagnosticList
          emptyLabel="No redactions returned."
          items={redactions}
          title="Redactions"
          typeKey="field"
        />
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Guardrails</h2>
              <div className="panel-subtitle">This progress surface is diagnostic only.</div>
            </div>
            <AlertTriangle size={18} />
          </div>
          <div className="panel-body route-list">
            <Guardrail title="No progress mutation" copy="This page does not ingest, correct, replay, repair, or requeue progress events." />
            <Guardrail title="No support-case writes" copy="Support triage remains read-only until a later audited workflow exists." />
            <Guardrail title="No sensitive identifiers" copy="Raw UCN values, provider payloads, wallet data, and money evidence are not rendered." />
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Adjacent support workflow</h2>
            <div className="panel-subtitle">Continue through read-only product surfaces.</div>
          </div>
        </div>
        <div className="panel-body route-list">
          <SetupLink to="/admin/referral-saas/support" title="Support workflow hub" copy="Choose the right read-only diagnostic path by support case type." />
          <SetupLink to="/admin/referral-saas/attribution-trace" title="Attribution trace" copy="Inspect outcome attribution evidence after progress completes." />
          <SetupLink to="/admin/referral-saas/operator-links" title="Link/code inspection" copy="Start from a code, route link, campaign link, or composite code." />
          <SetupLink to="/admin/referral-saas/campaigns" title="Campaign readiness" copy="Check setup and readiness blockers." />
          <SetupLink to="/admin/referral-saas/reports" title="Referral SaaS reports" copy="Review progress, attribution, and link/code reporting." />
        </div>
      </section>
    </>
  );
}

function DiagnosticList({
  emptyLabel,
  items,
  title,
  typeKey,
}: {
  emptyLabel: string;
  items: Record<string, unknown>[];
  title: string;
  typeKey: string;
}) {
  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">{title}</h2>
          <div className="panel-subtitle">Safe support diagnostics only.</div>
        </div>
        <StatusBadge label={String(items.length)} tone={items.length ? "warning" : "success"} />
      </div>
      <div className="panel-body route-list">
        {items.length ? (
          items.map((item, index) => (
            <div className="route-item" key={`${title}-${index}`}>
              <div>
                <div className="route-name">
                  {formatDisplay(getNestedValue(item, [typeKey], getValue(item, ["label"], "Diagnostic")))}
                </div>
                <div className="route-path">
                  {formatDisplay(
                    getNestedValue(
                      item,
                      ["label"],
                      getNestedValue(item, ["message"], getNestedValue(item, ["targetRef"], "-")),
                    ),
                  )}
                </div>
              </div>
              <StatusBadge
                label={formatDisplay(getNestedValue(item, ["targetRef"], getNestedValue(item, ["severity"], "Review")))}
                tone="info"
              />
            </div>
          ))
        ) : (
          <div className="route-item">
            <div>
              <div className="route-name">{emptyLabel}</div>
              <div className="route-path">No action is implied by this empty diagnostic list.</div>
            </div>
            <StatusBadge label="Clear" tone="success" />
          </div>
        )}
      </div>
    </div>
  );
}

function Guardrail({ title, copy }: { title: string; copy: string }) {
  return (
    <div className="route-item">
      <div>
        <div className="route-name">{title}</div>
        <div className="route-path">{copy}</div>
      </div>
      <StatusBadge label="Deferred" tone="warning" />
    </div>
  );
}

function SetupLink({ to, title, copy }: { to: string; title: string; copy: string }) {
  return (
    <Link className="route-item route-link" to={to}>
      <div>
        <div className="route-name">{title}</div>
        <div className="route-path">{copy}</div>
      </div>
      <LinkIcon size={16} />
    </Link>
  );
}
