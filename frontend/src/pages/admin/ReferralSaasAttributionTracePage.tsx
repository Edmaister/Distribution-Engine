import {
  AlertTriangle,
  FileWarning,
  GitBranch,
  Link as LinkIcon,
  Search,
  ShieldCheck,
  Split,
} from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import {
  inspectReferralSaasOperatorAttributionTrace,
  type ReferralSaasAttributionTraceSection,
} from "../../api/endpoints/referralSaasLinks";
import { ErrorPanel } from "../../components/ErrorPanel";
import { KpiCard } from "../../components/KpiCard";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";
import { asArray, asRecord, formatDisplay, getNestedValue, getValue, statusTone } from "../pageUtils";

const defaultTenantCode = "FNB";
const defaultReferralTrackId = "11111111-1111-4111-8111-111111111111";

const sectionOptions: Array<{ label: string; value: ReferralSaasAttributionTraceSection }> = [
  { label: "Attribution", value: "attribution" },
  { label: "Participants", value: "participants" },
  { label: "Events", value: "events" },
  { label: "Audit", value: "audit" },
];

const allowedSectionOrder: ReferralSaasAttributionTraceSection[] = [
  "outcome",
  "attribution",
  "participants",
  "events",
  "audit",
];

export function ReferralSaasAttributionTracePage() {
  const [tenantCode, setTenantCode] = useState(defaultTenantCode);
  const [referralTrackId, setReferralTrackId] = useState(defaultReferralTrackId);
  const [includeSections, setIncludeSections] = useState<ReferralSaasAttributionTraceSection[]>(
    ["attribution", "participants", "events", "audit"],
  );
  const canInspect = tenantCode.trim() !== "" && referralTrackId.trim() !== "";

  const traceMutation = useMutation({
    mutationFn: () =>
      inspectReferralSaasOperatorAttributionTrace({
        tenantCode,
        referralTrackId,
        includeSections,
      }),
  });

  const traceResult = traceMutation.data;
  const trace = asRecord(getNestedValue(traceResult, ["attributionTrace"], {}));
  const lookup = asRecord(getNestedValue(trace, ["lookup"], {}));
  const sections = asRecord(getNestedValue(trace, ["sections"], {}));
  const outcome = asRecord(getNestedValue(sections, ["outcome"], {}));
  const attribution = asRecord(getNestedValue(sections, ["attribution"], {}));
  const participants = asArray(getNestedValue(sections, ["participants", "items"], []));
  const events = asArray(getNestedValue(sections, ["events", "items"], []));
  const audit = asArray(getNestedValue(sections, ["audit", "items"], []));
  const campaignLinks = asArray(getNestedValue(attribution, ["campaign_links"], []));
  const routeLinks = asArray(getNestedValue(attribution, ["route_links"], []));
  const missingEvidence = asArray(getNestedValue(trace, ["missingEvidence"], []));
  const sourceWarnings = asArray(getNestedValue(trace, ["sourceWarnings"], []));
  const nextDiagnostics = asArray(getNestedValue(trace, ["nextDiagnostics"], []));
  const redactions = asArray(getNestedValue(trace, ["redactions"], []));
  const traceStatus = getValue(trace, ["traceStatus"], "Waiting");
  const displayedSections = allowedSectionOrder.filter((section) => sections[section]);

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Referral SaaS - Attribution Support</div>
          <h1 className="page-title">Operator attribution trace</h1>
          <p className="page-copy">
            Explain how referral, campaign, link, event, participant, and audit
            evidence supports one attributed outcome through the read-only
            product trace wrapper.
          </p>
        </div>
        <StatusBadge label={formatDisplay(traceStatus)} tone={statusTone(traceStatus)} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Trace lookup</h2>
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
          <div className="field">
            <span>Trace sections</span>
            <div className="report-chip-list">
              {sectionOptions.map((section) => (
                <label className="checkbox-row" key={section.value}>
                  <input
                    checked={includeSections.includes(section.value)}
                    onChange={(event) => {
                      setIncludeSections((current) =>
                        event.target.checked
                          ? [...current, section.value]
                          : current.filter((item) => item !== section.value),
                      );
                    }}
                    type="checkbox"
                  />
                  <span>{section.label}</span>
                </label>
              ))}
            </div>
          </div>
          <button
            className="button"
            disabled={!canInspect || traceMutation.isPending}
            onClick={() => traceMutation.mutate()}
            type="button"
          >
            <Search size={16} />
            {traceMutation.isPending ? "Tracing" : "Inspect trace"}
          </button>
        </div>
      </section>

      {traceMutation.error ? <ErrorPanel error={traceMutation.error} /> : null}

      <section className="grid-4">
        <KpiCard label="Trace status" value={formatDisplay(traceStatus)} footnote="Evidence completeness" icon={GitBranch} />
        <KpiCard label="Sections" value={displayedSections.length} footnote="First-launch trace sections" icon={Split} />
        <KpiCard label="Missing evidence" value={missingEvidence.length} footnote="Support triage signals" icon={FileWarning} />
        <KpiCard label="Warnings" value={sourceWarnings.length} footnote="Source inspection warnings" icon={AlertTriangle} />
      </section>

      <section className="grid-2">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Trace summary</h2>
              <div className="panel-subtitle">Product-safe outcome and lookup evidence.</div>
            </div>
            <StatusBadge label={formatDisplay(getValue(trace, ["tenantCode"], tenantCode))} tone="info" />
          </div>
          <div className="panel-body">
            <div className="summary-grid">
              <SummaryItem label="Trace ID" value={getValue(trace, ["traceId"])} />
              <SummaryItem label="Lookup type" value={getValue(lookup, ["type"])} />
              <SummaryItem label="Lookup value" value={getValue(lookup, ["value"])} />
              <SummaryItem label="Generated" value={getValue(trace, ["generatedAt"])} />
              <SummaryItem label="Outcome status" value={getValue(outcome, ["status", "outcome_status"])} />
              <SummaryItem label="Referral track" value={getValue(outcome, ["referral_track_id"], referralTrackId)} />
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Attribution links</h2>
              <div className="panel-subtitle">Campaign and route links connected to the outcome.</div>
            </div>
            <StatusBadge label={`${campaignLinks.length + routeLinks.length}`} tone="info" />
          </div>
          <div className="panel-body route-list">
            <EvidenceList emptyLabel="No campaign links returned." items={campaignLinks} title="Campaign link" />
            <EvidenceList emptyLabel="No route links returned." items={routeLinks} title="Route link" />
          </div>
        </div>
      </section>

      <section className="grid-4">
        <TraceList emptyLabel="No participants returned." items={participants} title="Participants" typeKey="participant_type" />
        <TraceList emptyLabel="No events returned." items={events} title="Events" typeKey="event_type" />
        <TraceList emptyLabel="No audit evidence returned." items={audit} title="Audit" typeKey="action_type" />
        <TraceList emptyLabel="No redactions returned." items={redactions} title="Redactions" typeKey="field" />
      </section>

      <section className="grid-4">
        <TraceList emptyLabel="No missing evidence returned." items={missingEvidence} title="Missing evidence" typeKey="code" />
        <TraceList emptyLabel="No source warnings returned." items={sourceWarnings} title="Source warnings" typeKey="code" />
        <TraceList emptyLabel="No next diagnostics available yet." items={nextDiagnostics} title="Next diagnostics" typeKey="type" />
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Guardrails</h2>
              <div className="panel-subtitle">This trace surface is diagnostic only.</div>
            </div>
            <ShieldCheck size={18} />
          </div>
          <div className="panel-body route-list">
            <Guardrail title="First-launch sections only" copy="Outcome, attribution, participants, events, and audit are the only rendered trace sections." />
            <Guardrail title="No mutation controls" copy="Repair, retry, replay, override, attribution edits, and support-case writes are not available here." />
            <Guardrail title="No money evidence" copy="Reward, commission, funding, fulfilment, settlement, wallet, invoice, payout, and webhook evidence is not rendered." />
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
          <SetupLink to="/admin/referral-saas/operator-links" title="Link/code inspection" copy="Start from a code, route link, campaign link, or composite code." />
          <SetupLink to="/admin/referral-saas/campaigns" title="Campaign readiness" copy="Check campaign setup and launch blockers." />
          <SetupLink to="/admin/referral-saas/reports" title="Referral SaaS reports" copy="Review link/code, progress, and attribution reporting." />
        </div>
      </section>
    </>
  );
}

function EvidenceList({
  emptyLabel,
  items,
  title,
}: {
  emptyLabel: string;
  items: Record<string, unknown>[];
  title: string;
}) {
  if (!items.length) {
    return (
      <div className="route-item">
        <div>
          <div className="route-name">{emptyLabel}</div>
          <div className="route-path">No action is implied by this empty evidence list.</div>
        </div>
        <StatusBadge label="Clear" tone="success" />
      </div>
    );
  }

  return (
    <>
      {items.map((item, index) => (
        <div className="route-item" key={`${title}-${index}`}>
          <div>
            <div className="route-name">
              {formatDisplay(getValue(item, ["campaign_code", "route_id", "source"], title))}
            </div>
            <div className="route-path">
              {formatDisplay(getValue(item, ["campaign_track_id", "referral_track_id", "route_referral_link_id"]))}
            </div>
          </div>
          <StatusBadge label={title} tone="info" />
        </div>
      ))}
    </>
  );
}

function TraceList({
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
          <div className="panel-subtitle">Safe trace diagnostics only.</div>
        </div>
        <StatusBadge label={String(items.length)} tone={items.length ? "warning" : "success"} />
      </div>
      <div className="panel-body route-list">
        {items.length ? (
          items.map((item, index) => (
            <div className="route-item" key={`${title}-${index}`}>
              <div>
                <div className="route-name">
                  {formatDisplay(getNestedValue(item, [typeKey], getValue(item, ["label"], "Trace item")))}
                </div>
                <div className="route-path">
                  {formatDisplay(
                    getNestedValue(
                      item,
                      ["message"],
                      getNestedValue(item, ["source_event_id"], getNestedValue(item, ["targetRef"], "-")),
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
