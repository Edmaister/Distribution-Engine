import { CalendarClock, CheckCircle2, Flag, Link as LinkIcon, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";
import { useState } from "react";

import {
  type CampaignReadinessOperation,
} from "../../api/endpoints/adminCampaignReadiness";
import { useReferralSaasCampaignReadiness } from "../../api/referralSaasCampaignQueries";
import { DataTable } from "../../components/DataTable";
import { ErrorPanel } from "../../components/ErrorPanel";
import { KpiCard } from "../../components/KpiCard";
import { LoadingState } from "../../components/LoadingState";
import { SegmentedFilter } from "../../components/SegmentedFilter";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";
import {
  asArray,
  asRecord,
  formatDisplay,
  getNestedValue,
  getValue,
  statusTone,
  useRefreshContext,
} from "../pageUtils";

const defaultCampaignCode = "CAMP001";
const defaultTenantCode = "FNB";

const operationOptions: Array<{ label: string; value: CampaignReadinessOperation }> = [
  { label: "View", value: "CONTROL_PLANE_VIEW" },
  { label: "Validate", value: "CREATE_TRACK" },
  { label: "Links", value: "GENERATE_LINKS" },
  { label: "Activate", value: "ACTIVATE_CAMPAIGN" },
];

const setupChecklist = [
  {
    code: "CAMPAIGN_DEFINITION",
    label: "Campaign definition",
    evidencePath: ["evidence", "campaign"],
    next: "Confirm campaign code, name, segment, active flag, date window, and capacity.",
  },
  {
    code: "POLICY_BASELINE",
    label: "Policy baseline",
    evidencePath: ["evidence", "policy"],
    next: "Confirm an active policy before activation is promised.",
  },
  {
    code: "LINK_CODE_PATH",
    label: "Link/code path",
    evidencePath: ["evidence", "links"],
    next: "Use readiness as a gate before link/code generation.",
  },
  {
    code: "ATTRIBUTION_REPORTING",
    label: "Attribution and reporting",
    evidencePath: ["campaign_code"],
    next: "Review attribution-quality and campaign-performance reports after setup.",
  },
];

export function ReferralSaasCampaignReadinessPage() {
  const { refreshKey } = useRefreshContext();
  const [campaignCode, setCampaignCode] = useState(defaultCampaignCode);
  const [tenantCode, setTenantCode] = useState(defaultTenantCode);
  const [operation, setOperation] = useState<CampaignReadinessOperation>("CONTROL_PLANE_VIEW");
  const [opportunityId, setOpportunityId] = useState("");
  const { data, error, isLoading } = useReferralSaasCampaignReadiness(
    campaignCode,
    tenantCode,
    operation,
    opportunityId,
    refreshKey,
  );

  const readiness = asRecord(data?.readiness);
  const blockers = asArray(getNestedValue(readiness, ["blockers"], []));
  const warnings = asArray(getNestedValue(readiness, ["warnings"], []));
  const unknowns = asArray(getNestedValue(readiness, ["unknowns"], []));
  const evidence = asRecord(getNestedValue(readiness, ["evidence"], {}));
  const campaignEvidence = asRecord(getNestedValue(evidence, ["campaign"], {}));
  const policyEvidence = asRecord(getNestedValue(evidence, ["policy"], {}));
  const readinessStatus = formatDisplay(getNestedValue(readiness, ["readiness"], "pending"));
  const lifecycleStatus = formatDisplay(getNestedValue(readiness, ["canonical_lifecycle"], "unknown"));
  const canProceed = Boolean(getNestedValue(readiness, ["can_proceed"], false));
  const checklistRows = setupChecklist.map((item) => {
    const sourceEvidence = getNestedValue(readiness, item.evidencePath, undefined);
    const hasEvidence =
      sourceEvidence !== undefined &&
      sourceEvidence !== null &&
      !(typeof sourceEvidence === "object" && Object.keys(sourceEvidence as Record<string, unknown>).length === 0);

    return {
      ...item,
      status: hasEvidence ? "Evidence present" : "Needs evidence",
      detail: hasEvidence ? "Current source evidence is available." : item.next,
    };
  });

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Referral SaaS - Campaigns</div>
          <h1 className="page-title">Campaign readiness</h1>
          <p className="page-copy">
            Review campaign setup, policy, lifecycle, link/code, and activation
            readiness over the existing read-only campaign readiness primitive.
          </p>
        </div>
        <StatusBadge label={readinessStatus} tone={statusTone(readinessStatus)} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Campaign scope</h2>
            <div className="panel-subtitle">
              This surface uses the current internal tenant bridge until account/membership resolution exists.
            </div>
          </div>
        </div>
        <div className="panel-body referral-campaign-controls">
          <label className="field">
            <span>Campaign code</span>
            <input
              className="input"
              onChange={(event) => setCampaignCode(event.target.value.toUpperCase())}
              value={campaignCode}
            />
          </label>
          <label className="field">
            <span>Tenant code bridge</span>
            <input
              className="input"
              onChange={(event) => setTenantCode(event.target.value.toUpperCase())}
              value={tenantCode}
            />
          </label>
          <label className="field">
            <span>Opportunity ID</span>
            <input
              className="input"
              onChange={(event) => setOpportunityId(event.target.value)}
              placeholder="Optional for broader marketplace readiness"
              value={opportunityId}
            />
          </label>
          <SegmentedFilter
            ariaLabel="Select campaign readiness operation"
            onChange={(value) => setOperation(value as CampaignReadinessOperation)}
            options={operationOptions}
            value={operation}
          />
        </div>
      </section>

      {isLoading ? <LoadingState label="Loading Referral SaaS campaign readiness" /> : null}
      {error ? <ErrorPanel error={error} /> : null}
      {!isLoading && !error ? (
        <>
          <section className="grid-4">
            <KpiCard
              label="Readiness"
              value={readinessStatus}
              footnote="Current operation"
              icon={CheckCircle2}
            />
            <KpiCard
              label="Lifecycle"
              value={lifecycleStatus}
              footnote="Setup state, not track state"
              icon={CalendarClock}
            />
            <KpiCard
              label="Blockers"
              value={blockers.length}
              footnote="Must clear before launch"
              icon={ShieldCheck}
            />
            <KpiCard
              label="Warnings"
              value={warnings.length + unknowns.length}
              footnote="Warnings and unknowns"
              icon={Flag}
            />
          </section>

          <section className="grid-2">
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">Readiness decision</h2>
                  <div className="panel-subtitle">
                    The existing readiness service decides if this operation can proceed.
                  </div>
                </div>
                <StatusBadge label={canProceed ? "Can proceed" : "Blocked"} tone={canProceed ? "success" : "warning"} />
              </div>
              <div className="panel-body">
                <div className="summary-grid">
                  <SummaryItem label="Operation" value={formatDisplay(getNestedValue(readiness, ["operation"]))} />
                  <SummaryItem label="Campaign" value={formatDisplay(getNestedValue(readiness, ["campaign_code"]))} />
                  <SummaryItem label="Evaluated" value={formatDisplay(getNestedValue(readiness, ["evaluated_at"]))} />
                </div>
              </div>
            </div>

            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">Launch guardrails</h2>
                  <div className="panel-subtitle">
                    Readiness is visible, but launch commands remain future work.
                  </div>
                </div>
                <StatusBadge label="Read-only" tone="info" />
              </div>
              <div className="panel-body route-list">
                <div className="route-item">
                  <div>
                    <div className="route-name">No campaign mutation</div>
                    <div className="route-path">
                      No create, policy write, submit, activate, pause, archive, link generation, or validation command is wired here.
                    </div>
                  </div>
                  <StatusBadge label="Bounded" tone="info" />
                </div>
                <div className="route-item">
                  <div>
                    <div className="route-name">No marketplace or money expansion</div>
                    <div className="route-path">
                      Opportunity routing, rewards, funding, fulfilment, settlement, billing, and wallet flows stay outside this page.
                    </div>
                  </div>
                  <StatusBadge label="Deferred" tone="warning" />
                </div>
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Setup checklist</h2>
                <div className="panel-subtitle">
                  Product setup gates mapped onto current campaign readiness evidence.
                </div>
              </div>
            </div>
            <DataTable
              rows={checklistRows}
              emptyText="No campaign setup checklist rows returned."
              columns={[
                {
                  key: "gate",
                  header: "Gate",
                  render: (row) => (
                    <>
                      <span className="mono">{row.code}</span>
                      <div className="table-subtext">{row.label}</div>
                    </>
                  ),
                },
                {
                  key: "status",
                  header: "Status",
                  render: (row) => <StatusBadge label={row.status} tone={statusTone(row.status)} />,
                },
                {
                  key: "detail",
                  header: "Detail",
                  render: (row) => <span className="table-subtext">{row.detail}</span>,
                },
              ]}
            />
          </section>

          <section className="grid-2">
            <EvidencePanel title="Campaign evidence" evidence={campaignEvidence} />
            <EvidencePanel title="Policy evidence" evidence={policyEvidence} />
          </section>

          <section className="grid-2">
            <SignalPanel title="Blockers" rows={blockers} emptyText="No blockers returned." tone="warning" />
            <SignalPanel title="Warnings and unknowns" rows={[...warnings, ...unknowns]} emptyText="No warnings or unknowns returned." tone="info" />
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Workflow links</h2>
                <div className="panel-subtitle">
                  Continue through existing safe Referral SaaS setup and reporting surfaces.
                </div>
              </div>
              <LinkIcon size={18} />
            </div>
            <div className="panel-body route-list">
              <SetupLink to="/admin/referral-saas/account-setup" title="Account setup readiness" copy="Confirm account, membership, tenant-link, and report-baseline gates." />
              <SetupLink to="/admin/onboarding/campaign-opportunity" title="Broader campaign shell" copy="Use only when broader opportunity setup intent is needed." />
              <SetupLink to="/admin/referral-saas/reports" title="Referral SaaS reports" copy="Review campaign, funnel, attribution, link/code, and reward visibility reports." />
            </div>
          </section>
        </>
      ) : null}
    </>
  );
}

function EvidencePanel({ title, evidence }: { title: string; evidence: Record<string, unknown> }) {
  const rows = Object.entries(evidence)
    .filter(([key]) => key !== "tenant_code")
    .map(([key, value]) => ({ key, value: formatDisplay(value) }));

  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">{title}</h2>
          <div className="panel-subtitle">Safe source evidence returned by the readiness service.</div>
        </div>
      </div>
      <DataTable
        rows={rows}
        emptyText="No safe evidence returned."
        columns={[
          { key: "field", header: "Field", render: (row) => <span className="mono">{row.key}</span> },
          { key: "value", header: "Value", render: (row) => row.value },
        ]}
      />
    </div>
  );
}

function SignalPanel({
  title,
  rows,
  emptyText,
  tone,
}: {
  title: string;
  rows: Record<string, unknown>[];
  emptyText: string;
  tone: "info" | "warning";
}) {
  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">{title}</h2>
          <div className="panel-subtitle">Safe readiness evidence for the selected operation.</div>
        </div>
        <StatusBadge label={`${rows.length} items`} tone={rows.length ? tone : "neutral"} />
      </div>
      <div className="panel-body route-list">
        {rows.length ? (
          rows.map((row) => (
            <div className="route-item" key={getValue(row, ["code", "message"])}>
              <div>
                <div className="route-name">{getValue(row, ["code"])}</div>
                <div className="route-path">{getValue(row, ["message"])}</div>
                <div className="table-subtext">{getValue(row, ["source"])}</div>
              </div>
              <StatusBadge label={getValue(row, ["severity"], "INFO")} tone={tone} />
            </div>
          ))
        ) : (
          <div className="empty-state">{emptyText}</div>
        )}
      </div>
    </div>
  );
}

function SetupLink({ to, title, copy }: { to: string; title: string; copy: string }) {
  return (
    <Link className="route-item" to={to}>
      <div>
        <div className="route-name">{title}</div>
        <div className="route-path">{copy}</div>
      </div>
      <LinkIcon size={18} />
    </Link>
  );
}
