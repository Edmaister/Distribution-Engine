import { Building2, Plus, Sparkles, Target } from "lucide-react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";

import { DataTable } from "../../../components/DataTable";
import { EmptyState } from "../../../components/EmptyState";
import { ErrorPanel } from "../../../components/ErrorPanel";
import { LoadingState } from "../../../components/LoadingState";
import { StatusBadge } from "../../../components/StatusBadge";
import { SummaryItem } from "../../../components/SummaryItem";
import { formatDisplay, getNestedValue, getValue, statusTone } from "../../pageUtils";

type SponsorWorkspaceViewProps = {
  activeCampaigns: unknown;
  acquiredCustomers: unknown;
  campaignRows: Record<string, unknown>[];
  channelCount: number;
  channelReadyCount: number;
  channelStatus: string;
  contracts: Record<string, unknown>[];
  error: unknown;
  forecast: unknown;
  loading: boolean;
  opportunityPerformance: Record<string, unknown>[];
  producerName: unknown;
  producerSessionLocked: boolean;
  receipts: Record<string, unknown>[];
  rewardLiability: unknown;
  sponsorCode: string;
  sponsorOptions: Record<string, unknown>[];
  sponsorOptionsLoading: boolean;
  submitted: { tenantCode: string; sponsorCode: string };
  tenantCode: string;
  walletBalance: unknown;
  onSponsorCodeChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onTenantCodeChange: (value: string) => void;
};

export function SponsorWorkspaceView({
  activeCampaigns,
  acquiredCustomers,
  campaignRows,
  channelCount,
  channelReadyCount,
  channelStatus,
  contracts,
  error,
  forecast,
  loading,
  opportunityPerformance,
  producerName,
  producerSessionLocked,
  receipts,
  rewardLiability,
  sponsorCode,
  sponsorOptions,
  sponsorOptionsLoading,
  submitted,
  tenantCode,
  walletBalance,
  onSponsorCodeChange,
  onSubmit,
  onTenantCodeChange,
}: SponsorWorkspaceViewProps) {
  return (
    <>
      <section className="producer-command-header">
        <div className="producer-brand-breadcrumb">
          <span className="producer-brand-dot">
            <Sparkles size={14} />
          </span>
          <span>Amplifi</span>
          <span>Workspace</span>
          <strong>Company view</strong>
        </div>
        <div className="earnings-search">
          <Target size={16} />
          <input aria-label="Search producer workspace" placeholder="Search campaigns, distributors, settlements..." />
        </div>
        <div className="earnings-header-actions">
          <span className="producer-company-pill">
            <Building2 size={14} />
            {formatDisplay(producerName || submitted.sponsorCode || "Producer")}
          </span>
        </div>
      </section>

      <section className="producer-workspace-hero">
        <div>
          <div className="producer-identity-kicker">Amplifi Distribution OS</div>
          <h1>Organisation Workspace</h1>
          <p>
            Where {formatDisplay(producerName || submitted.sponsorCode || "a producer")} runs distribution strategy:
            campaigns, partners, funding, and fulfilment in one tenant.
          </p>
        </div>
        <Link className="button producer-primary-action" to="/sponsor/operations#producer-supply-launch">
          <Plus size={16} />
          New campaign
        </Link>
      </section>

      <section className="producer-scope-strip">
        <form className="producer-scope-form" onSubmit={onSubmit}>
          <input
            aria-label="Tenant code"
            disabled={producerSessionLocked}
            value={tenantCode}
            onChange={(event) => onTenantCodeChange(event.target.value)}
          />
          <select
            aria-label="Producer"
            disabled={producerSessionLocked || sponsorOptionsLoading || !sponsorOptions.length}
            value={sponsorCode}
            onChange={(event) => onSponsorCodeChange(event.target.value)}
          >
            <option value="">
              {sponsorOptionsLoading ? "Loading producers..." : sponsorOptions.length ? "Select producer" : "Producer code"}
            </option>
            {sponsorOptions.map((option) => {
              const code = getValue(option, ["sponsor_code"]);
              const name = getValue(option, ["sponsor_name"]);
              return (
                <option key={code} value={code}>
                  {name} - {code}
                </option>
              );
            })}
          </select>
          <button className="button secondary" disabled={producerSessionLocked} type="submit">
            {producerSessionLocked ? "Session loaded" : "Load"}
          </button>
        </form>
      </section>

      {!submitted.tenantCode || !submitted.sponsorCode ? (
        <EmptyState label="Load a producer to see campaigns, funding exposure, and partner readiness." />
      ) : loading ? (
        <LoadingState label="Loading producer workspace" />
      ) : error ? (
        <ErrorPanel error={error} />
      ) : (
        <>
          <section className="producer-stat-grid">
            <ProducerStat label="Active campaigns" value={activeCampaigns} note="Launching this week" tone="positive" />
            <ProducerStat label="Customers acquired" value={acquiredCustomers} note="Against live producer routes" tone="positive" />
            <ProducerStat label="Sponsor wallet balance" value={walletBalance} note="Funds at current pace" tone="warning" />
            <ProducerStat label="Reward liability" value={rewardLiability} note="Pending fulfilment" />
          </section>

          <section className="producer-overview-grid">
            <div className="producer-workspace-panel producer-campaign-panel">
              <div className="producer-panel-head">
                <h2>Campaigns</h2>
                <span>distribution / products / offers</span>
              </div>
              <DataTable
                emptyText="No producer campaigns returned yet."
                rows={campaignRows}
                columns={[
                  {
                    key: "campaign",
                    header: "Campaign",
                    render: (row) => (
                      <div>
                        <strong>{getValue(row, ["title", "opportunity_title", "opportunity_code"], "Producer campaign")}</strong>
                        <div className="table-subtext">
                          {getValue(row, ["product_name", "campaign_code", "description"], "Producer supply")}
                        </div>
                      </div>
                    ),
                  },
                  {
                    key: "status",
                    header: "Status",
                    render: (row) => {
                      const status = getValue(row, ["opportunity_status", "status"], "Draft");
                      return <StatusBadge label={status} tone={statusTone(status)} />;
                    },
                  },
                  {
                    key: "acquired",
                    header: "Acquired",
                    render: (row) => {
                      const performance = findOpportunityPerformance(opportunityPerformance, row);
                      return formatDisplay(getValue(performance || {}, ["completed_conversion_count", "conversion_count"], "-"));
                    },
                  },
                  {
                    key: "budget",
                    header: "Budget used",
                    render: (row) => {
                      const remaining = numberValue(getValue(row, ["remaining_allocations"], "0"));
                      const max = numberValue(getValue(row, ["max_allocations"], "0"));
                      if (!max) {
                        return "-";
                      }
                      return `${Math.max(0, Math.round(((max - remaining) / max) * 100))}%`;
                    },
                  },
                  {
                    key: "roi",
                    header: "ROI",
                    render: (row) => {
                      const performance = findOpportunityPerformance(opportunityPerformance, row);
                      return formatDisplay(getValue(performance || {}, ["roi", "conversion_completion_rate"], "-"));
                    },
                  },
                ]}
              />
            </div>

            <div className="producer-side-stack">
              <div className="producer-workspace-panel">
                <div className="producer-panel-head">
                  <h2>Funding & exposure</h2>
                  <span>live rails</span>
                </div>
                <div className="status-list spacious">
                  <ExposureRow label="Committed contracts" value={contracts.length ? `${contracts.length} contracts` : "-"} />
                  <ExposureRow label="Funds available" value={walletBalance} tone="success" />
                  <ExposureRow label="Pending settlement" value={rewardLiability} />
                  <ExposureRow
                    label="Forecast runway"
                    value={getNestedValue(forecast, ["forecast", "wallet", "days_remaining"], "-")}
                    tone="success"
                  />
                </div>
              </div>

              <div className="producer-workspace-panel">
                <div className="producer-panel-head">
                  <h2>Partners</h2>
                  <span>backend readiness</span>
                </div>
                <div className="producer-partner-grid">
                  <SummaryItem label="Contracts" value={contracts.length} />
                  <SummaryItem label="Receipts" value={receipts.length} />
                  <SummaryItem label="Channel ready" value={channelCount ? `${channelReadyCount}/${channelCount}` : "-"} />
                  <SummaryItem label="Fulfilment SLA" value={channelStatus || "Unknown"} />
                </div>
              </div>
            </div>
          </section>
        </>
      )}
    </>
  );
}

function ProducerStat({
  label,
  value,
  note,
  tone,
}: {
  label: string;
  value: unknown;
  note: string;
  tone?: "positive" | "warning";
}) {
  return (
    <div className="producer-stat-card">
      <span>{label}</span>
      <strong>{formatDisplay(value)}</strong>
      <small className={tone}>{note}</small>
    </div>
  );
}

function ExposureRow({
  label,
  value,
  tone,
}: {
  label: string;
  value: unknown;
  tone?: "success" | "warning" | "danger" | "info" | "neutral";
}) {
  return (
    <div className="status-row">
      <span className="status-name">{label}</span>
      <span className={tone === "success" ? "status-count up" : "status-count"}>{formatDisplay(value)}</span>
    </div>
  );
}

function findOpportunityPerformance(
  performanceRows: Record<string, unknown>[],
  opportunity: Record<string, unknown>,
): Record<string, unknown> | undefined {
  const opportunityId = getValue(opportunity, ["opportunity_id", "id"], "");
  const opportunityCode = getValue(opportunity, ["opportunity_code", "campaign_code"], "");
  return performanceRows.find((row) => {
    return (
      getValue(row, ["opportunity_id", "id"], "") === opportunityId ||
      getValue(row, ["opportunity_code", "campaign_code"], "") === opportunityCode
    );
  });
}

function numberValue(value: unknown): number {
  const parsed = Number(String(value ?? "0").replace(/[^0-9.-]/g, ""));
  return Number.isFinite(parsed) ? parsed : 0;
}
