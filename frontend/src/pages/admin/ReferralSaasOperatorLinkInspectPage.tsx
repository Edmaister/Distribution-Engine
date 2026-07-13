import {
  AlertTriangle,
  Eye,
  FileWarning,
  Link as LinkIcon,
  Search,
  ShieldCheck,
} from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import {
  inspectReferralSaasOperatorLink,
  type ReferralSaasOperatorLinkSourceType,
} from "../../api/endpoints/referralSaasLinks";
import { ErrorPanel } from "../../components/ErrorPanel";
import { KpiCard } from "../../components/KpiCard";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";
import { asArray, asRecord, formatDisplay, getNestedValue, getValue, statusTone } from "../pageUtils";

const defaultTenantCode = "FNB";
const defaultCodeOrRef = "REF123";

const sourceOptions: Array<{
  label: string;
  value: ReferralSaasOperatorLinkSourceType;
  lookupMode: "code" | "link";
}> = [
  { label: "Referral code", value: "REFERRAL_CODE", lookupMode: "code" },
  { label: "Campaign code", value: "CAMPAIGN_CODE", lookupMode: "code" },
  { label: "Campaign/referral bridge", value: "CAMPAIGN_REFERRAL_LINK", lookupMode: "link" },
  { label: "Route/referral link", value: "ROUTE_REFERRAL_LINK", lookupMode: "link" },
  { label: "Composite compatibility code", value: "COMPOSITE_CODE", lookupMode: "code" },
];

export function ReferralSaasOperatorLinkInspectPage() {
  const [tenantCode, setTenantCode] = useState(defaultTenantCode);
  const [sourceType, setSourceType] = useState<ReferralSaasOperatorLinkSourceType>("REFERRAL_CODE");
  const [codeOrRef, setCodeOrRef] = useState(defaultCodeOrRef);
  const [linkCodeId, setLinkCodeId] = useState("");
  const [includeEvidence, setIncludeEvidence] = useState(false);
  const selectedSource = sourceOptions.find((option) => option.value === sourceType) || sourceOptions[0];
  const lookupValue = selectedSource.lookupMode === "link" ? linkCodeId : codeOrRef;
  const canInspect = tenantCode.trim() !== "" && lookupValue.trim() !== "";

  const inspectMutation = useMutation({
    mutationFn: () =>
      inspectReferralSaasOperatorLink({
        tenantCode,
        sourceType,
        linkCodeId: selectedSource.lookupMode === "link" ? linkCodeId : undefined,
        codeOrRef: selectedSource.lookupMode === "code" ? codeOrRef : undefined,
        includeEvidence,
      }),
  });

  const inspectionResult = inspectMutation.data;
  const inspection = asRecord(getNestedValue(inspectionResult, ["inspection"], {}));
  const linkCode = asRecord(getNestedValue(inspection, ["linkCode"], {}));
  const campaign = asRecord(getNestedValue(linkCode, ["campaign"], {}));
  const participant = asRecord(getNestedValue(linkCode, ["participant"], {}));
  const attribution = asRecord(getNestedValue(linkCode, ["attribution"], {}));
  const nextDiagnostics = asArray(getNestedValue(inspection, ["nextDiagnostics"], []));
  const missingEvidence = asArray(getNestedValue(linkCode, ["missing_evidence"], []));
  const sourceWarnings = asArray(getNestedValue(linkCode, ["source_warnings"], []));
  const redactions = asArray(getNestedValue(linkCode, ["redactions"], []));
  const inspectionStatus = getValue(inspection, ["inspectionStatus"], getValue(linkCode, ["status"], "Waiting"));

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Referral SaaS - Operator Support</div>
          <h1 className="page-title">Operator link/code inspection</h1>
          <p className="page-copy">
            Inspect existing referral, campaign, route, or composite link/code
            evidence through the read-only product wrapper.
          </p>
        </div>
        <StatusBadge label={formatDisplay(inspectionStatus)} tone={statusTone(inspectionStatus)} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Inspection lookup</h2>
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
            <span>Source type</span>
            <select
              className="input"
              onChange={(event) => {
                const nextSource = event.target.value as ReferralSaasOperatorLinkSourceType;
                setSourceType(nextSource);
              }}
              value={sourceType}
            >
              {sourceOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Code or reference</span>
            <input
              className="input"
              disabled={selectedSource.lookupMode !== "code"}
              onChange={(event) => setCodeOrRef(event.target.value.toUpperCase())}
              placeholder="Code, campaign code, or composite code"
              value={codeOrRef}
            />
          </label>
          <label className="field">
            <span>Link/code ID</span>
            <input
              className="input"
              disabled={selectedSource.lookupMode !== "link"}
              onChange={(event) => setLinkCodeId(event.target.value)}
              placeholder="Campaign/referral or route/referral link ID"
              value={linkCodeId}
            />
          </label>
          <label className="checkbox-row referral-link-code-terms">
            <input
              checked={includeEvidence}
              onChange={(event) => setIncludeEvidence(event.target.checked)}
              type="checkbox"
            />
            <span>Request source evidence from the API; this page still renders only safe operator fields.</span>
          </label>
          <button
            className="button"
            disabled={!canInspect || inspectMutation.isPending}
            onClick={() => inspectMutation.mutate()}
            type="button"
          >
            <Search size={16} />
            {inspectMutation.isPending ? "Inspecting" : "Inspect link/code"}
          </button>
        </div>
      </section>

      {inspectMutation.error ? <ErrorPanel error={inspectMutation.error} /> : null}

      <section className="grid-4">
        <KpiCard label="Inspection" value={formatDisplay(inspectionStatus)} footnote="Source-derived status" icon={Eye} />
        <KpiCard label="Missing evidence" value={missingEvidence.length} footnote="Support triage signals" icon={FileWarning} />
        <KpiCard label="Warnings" value={sourceWarnings.length} footnote="Source inspection warnings" icon={AlertTriangle} />
        <KpiCard label="Redactions" value={redactions.length} footnote="Sensitive fields withheld" icon={ShieldCheck} />
      </section>

      <section className="grid-2">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Source summary</h2>
              <div className="panel-subtitle">
                Product-safe operator evidence. Raw source evidence is not displayed.
              </div>
            </div>
            <StatusBadge label={formatDisplay(getValue(linkCode, ["source_type"], sourceType))} tone="info" />
          </div>
          <div className="panel-body">
            <div className="summary-grid">
              <SummaryItem label="Status" value={getValue(linkCode, ["status"])} />
              <SummaryItem label="Source" value={getValue(linkCode, ["source"])} />
              <SummaryItem label="Tenant" value={getValue(linkCode, ["tenant_code"])} />
              <SummaryItem label="Code" value={getValue(linkCode, ["code"])} />
              <SummaryItem label="Link/code ID" value={getValue(linkCode, ["link_code_id"])} />
              <SummaryItem label="Inspected" value={getValue(linkCode, ["inspected_at"])} />
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Connected evidence</h2>
              <div className="panel-subtitle">
                Campaign, participant, and attribution identifiers for safe follow-up.
              </div>
            </div>
            <StatusBadge label="Diagnostics" tone="info" />
          </div>
          <div className="panel-body">
            <div className="summary-grid">
              <SummaryItem label="Campaign code" value={getValue(campaign, ["campaign_code"])} />
              <SummaryItem label="Campaign track" value={getValue(campaign, ["campaign_track_id"])} />
              <SummaryItem label="Participant type" value={getValue(participant, ["participant_type"])} />
              <SummaryItem label="Participant ref" value={getValue(participant, ["participant_ref"])} />
              <SummaryItem label="Referral track" value={getValue(attribution, ["referral_track_id"])} />
              <SummaryItem label="Route ID" value={getValue(attribution, ["route_id"])} />
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
          emptyLabel="No source warnings returned."
          items={sourceWarnings}
          title="Source warnings"
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
      </section>

      <section className="grid-2">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Operator guardrails</h2>
              <div className="panel-subtitle">This support surface is diagnostic only.</div>
            </div>
          </div>
          <div className="panel-body route-list">
            <Guardrail title="No mutation controls" copy="Reissue, revoke, expire, repair, retry, replay, and support-case writes are not available here." />
            <Guardrail title="No money evidence" copy="Reward, funding, fulfilment, settlement, wallet, invoice, and payout evidence is not rendered." />
            <Guardrail title="No raw evidence rendering" copy="The page shows whitelisted inspection fields, missing evidence, warnings, redactions, and next diagnostics only." />
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Adjacent support workflow</h2>
              <div className="panel-subtitle">Continue through read-only product surfaces.</div>
            </div>
          </div>
          <div className="panel-body route-list">
            <SetupLink to="/admin/referral-saas/campaigns" title="Campaign readiness" copy="Check campaign setup and launch blockers." />
            <SetupLink to="/admin/referral-saas/attribution-trace" title="Attribution trace" copy="Inspect outcome evidence through the product trace wrapper." />
            <SetupLink to="/admin/referral-saas/link-codes" title="Link/code workflow" copy="Run issue, validation, and identity-capture checks." />
            <SetupLink to="/admin/referral-saas/reports" title="Referral SaaS reports" copy="Review link/code, progress, and attribution reporting." />
          </div>
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
                <div className="route-name">{formatDisplay(getNestedValue(item, [typeKey], getValue(item, ["label"], "Diagnostic")))}</div>
                <div className="route-path">
                  {formatDisplay(getNestedValue(item, ["label"], getNestedValue(item, ["message"], getNestedValue(item, ["targetRef"], "-"))))}
                </div>
              </div>
              <StatusBadge label={formatDisplay(getNestedValue(item, ["targetRef"], getNestedValue(item, ["severity"], "Review")))} tone="info" />
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
