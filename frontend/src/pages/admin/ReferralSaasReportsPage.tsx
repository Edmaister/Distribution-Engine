import { Download, FileJson, ShieldCheck, TableProperties } from "lucide-react";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import {
  previewReferralSaasReportExport,
  type ReferralSaasExportFormat,
  type ReferralSaasReportType,
} from "../../api/endpoints/referralSaasReports";
import { useReferralSaasReport } from "../../api/referralSaasQueries";
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

type ReportOption = {
  label: string;
  value: ReferralSaasReportType;
};

const reportOptions: ReportOption[] = [
  { label: "Campaigns", value: "campaign_performance" },
  { label: "Funnel", value: "referral_funnel" },
  { label: "Links", value: "link_code_performance" },
  { label: "Events", value: "progress_event_health" },
  { label: "Attribution", value: "attribution_quality" },
  { label: "Status", value: "safe_status_distribution" },
  { label: "Rewards", value: "reward_visibility_summary" },
];

const defaultTenantCode = "FNB";

export function ReferralSaasReportsPage() {
  const { refreshKey } = useRefreshContext();
  const [reportType, setReportType] = useState<ReferralSaasReportType>("campaign_performance");
  const [tenantCode, setTenantCode] = useState(defaultTenantCode);
  const [previewRowLimit, setPreviewRowLimit] = useState(10);
  const { data, error, isLoading } = useReferralSaasReport(reportType, tenantCode, refreshKey);
  const exportPreviewMutation = useMutation({
    mutationFn: (format: ReferralSaasExportFormat) =>
      previewReferralSaasReportExport({
        reportType,
        tenantCode,
        format,
        redactionProfile: "tenant_safe",
        rowLimit: previewRowLimit,
      }),
  });

  const report = asRecord(data?.report);
  const metrics = asArray(getNestedValue(report, ["metrics"], []));
  const freshness = asRecord(getNestedValue(report, ["freshness"], {}));
  const warnings = asArray(getNestedValue(report, ["source_warnings"], []));
  const redactions = asArray(
    (getNestedValue(report, ["redactions"], []) as unknown[]).map((redaction) => ({
      name: redaction,
    })),
  );
  const accountScope = asRecord(data?.account_scope);
  const exportPreview = asRecord(exportPreviewMutation.data?.export_preview);
  const preview = asRecord(getNestedValue(exportPreview, ["preview"], {}));
  const previewMetadata = asRecord(getNestedValue(preview, ["metadata"], {}));
  const previewPayloadValue = getNestedValue(preview, ["payload"], "");
  const previewPayload =
    typeof previewPayloadValue === "string"
      ? previewPayloadValue
      : JSON.stringify(previewPayloadValue, null, 2);
  const metricTotal = metrics.reduce((total, metric) => {
    const value = Number(getValue(metric, ["value"], "0"));
    return Number.isFinite(value) ? total + value : total;
  }, 0);
  const handleReportTypeChange = (value: string) => {
    exportPreviewMutation.reset();
    setReportType(value as ReferralSaasReportType);
  };
  const handleTenantCodeChange = (value: string) => {
    exportPreviewMutation.reset();
    setTenantCode(value.toUpperCase());
  };
  const handlePreviewRowLimitChange = (value: string) => {
    const nextLimit = Number(value);
    exportPreviewMutation.reset();
    setPreviewRowLimit(Number.isFinite(nextLimit) ? Math.min(100, Math.max(1, nextLimit)) : 1);
  };

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Referral SaaS - Reports</div>
          <h1 className="page-title">Tenant-safe reporting</h1>
          <p className="page-copy">
            Review the current Referral SaaS report catalog with safe metrics,
            freshness, warnings, redactions, and inline-preview readiness.
          </p>
        </div>
        <StatusBadge
          label={formatDisplay(getNestedValue(report, ["catalog_status"], "pending"))}
          tone={statusTone(formatDisplay(getNestedValue(report, ["catalog_status"], "pending")))}
        />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Report scope</h2>
            <div className="panel-subtitle">
              Tenant code remains transitional until account setup and membership are productized.
            </div>
          </div>
        </div>
        <div className="panel-body referral-report-controls">
          <label className="field">
            <span>Tenant code</span>
            <input
              className="input"
              onChange={(event) => handleTenantCodeChange(event.target.value)}
              value={tenantCode}
            />
          </label>
          <SegmentedFilter
            ariaLabel="Select Referral SaaS report"
            onChange={handleReportTypeChange}
            options={reportOptions}
            value={reportType}
          />
        </div>
      </section>

      {isLoading ? <LoadingState label="Loading Referral SaaS report" /> : null}
      {error ? <ErrorPanel error={error} /> : null}
      {!isLoading && !error ? (
        <>
          <section className="grid-4">
            <KpiCard
              label="Metrics"
              value={metrics.length}
              footnote="Tenant-safe rows"
              icon={TableProperties}
            />
            <KpiCard
              label="Metric total"
              value={metricTotal.toLocaleString("en-ZA")}
              footnote="Numeric row values"
              icon={FileJson}
            />
            <KpiCard
              label="Warnings"
              value={warnings.length}
              footnote="Source caveats"
              icon={ShieldCheck}
            />
            <KpiCard
              label="Export"
              value={formatDisplay(getNestedValue(report, ["export_status"]))}
              footnote="Preview only, no stored file"
              icon={Download}
            />
          </section>

          <section className="grid-2">
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">Report posture</h2>
                  <div className="panel-subtitle">
                    Source, freshness, and account-scope evidence returned by the API.
                  </div>
                </div>
                <StatusBadge
                  label={formatDisplay(getNestedValue(freshness, ["status"]))}
                  tone={statusTone(formatDisplay(getNestedValue(freshness, ["status"])))}
                />
              </div>
              <div className="panel-body">
                <div className="summary-grid">
                  <SummaryItem label="Report" value={formatDisplay(getNestedValue(report, ["report_type"]))} />
                  <SummaryItem label="Source" value={formatDisplay(getNestedValue(report, ["source_report_type"]))} />
                  <SummaryItem label="Scope" value={formatDisplay(getNestedValue(accountScope, ["source"]))} />
                </div>
              </div>
            </div>

            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">Inline export preview</h2>
                  <div className="panel-subtitle">
                    Current report surface can preview payloads but does not create stored files.
                  </div>
                </div>
              </div>
              <div className="panel-body route-list">
                <div className="export-preview-actions">
                  <label className="field export-preview-row-limit">
                    <span>Preview rows</span>
                    <input
                      aria-label="Preview row limit"
                      className="input"
                      min={1}
                      max={100}
                      onChange={(event) => handlePreviewRowLimitChange(event.target.value)}
                      type="number"
                      value={previewRowLimit}
                    />
                  </label>
                  <button
                    className="button"
                    disabled={exportPreviewMutation.isPending}
                    onClick={() => exportPreviewMutation.mutate("json")}
                    type="button"
                  >
                    <FileJson size={16} />
                    Preview JSON
                  </button>
                  <button
                    className="button secondary"
                    disabled={exportPreviewMutation.isPending}
                    onClick={() => exportPreviewMutation.mutate("csv")}
                    type="button"
                  >
                    <Download size={16} />
                    Preview CSV
                  </button>
                </div>
                {exportPreviewMutation.error ? <ErrorPanel error={exportPreviewMutation.error} /> : null}
                <div className="route-item">
                  <div>
                    <div className="route-name">Inline preview only</div>
                    <div className="route-path">Export storage, download URLs, and audit rows remain future work.</div>
                  </div>
                  <StatusBadge label="Bounded" tone="info" />
                </div>
                <div className="route-item">
                  <div>
                    <div className="route-name">Tenant-safe evidence</div>
                    <div className="route-path">{formatDisplay(data?.guardrail)}</div>
                  </div>
                  <StatusBadge label="Read-only" tone="success" />
                </div>
                {exportPreviewMutation.data ? (
                  <div className="export-preview-result">
                    <div className="summary-grid">
                      <SummaryItem label="Preview status" value={formatDisplay(getNestedValue(preview, ["status"]))} />
                      <SummaryItem label="Format" value={formatDisplay(getNestedValue(preview, ["export_format"]))} />
                      <SummaryItem label="Content type" value={formatDisplay(getNestedValue(preview, ["content_type"]))} />
                      <SummaryItem label="Rows" value={formatDisplay(getNestedValue(previewMetadata, ["row_count"]))} />
                    </div>
                    <pre className="export-preview-payload" aria-label="Export preview payload">
                      {previewPayload}
                    </pre>
                  </div>
                ) : null}
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Metric rows</h2>
                <div className="panel-subtitle">
                  Productized metric names and dimensions from the selected report.
                </div>
              </div>
              <StatusBadge label={`${metrics.length} rows`} tone={metrics.length ? "info" : "neutral"} />
            </div>
            <DataTable
              rows={metrics}
              emptyText="No tenant-safe metrics returned."
              columns={[
                {
                  key: "metric",
                  header: "Metric",
                  render: (row) => <span className="mono">{getValue(row, ["name"])}</span>,
                },
                {
                  key: "value",
                  header: "Value",
                  render: (row) => formatDisplay(getNestedValue(row, ["value"])),
                },
                {
                  key: "class",
                  header: "Class",
                  render: (row) => getValue(row, ["metric_class"]),
                },
                {
                  key: "dimensions",
                  header: "Dimensions",
                  render: (row) => (
                    <span className="table-subtext">{formatDisplay(JSON.stringify(getNestedValue(row, ["dimensions"], {})))}</span>
                  ),
                },
              ]}
            />
          </section>

          <section className="grid-2">
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">Warnings</h2>
                  <div className="panel-subtitle">Safe source caveats exposed to operators.</div>
                </div>
              </div>
              <div className="panel-body route-list">
                {warnings.length ? (
                  warnings.map((warning) => (
                    <div className="route-item" key={getValue(warning, ["code", "message"])}>
                      <div>
                        <div className="route-name">{getValue(warning, ["code"])}</div>
                        <div className="route-path">{getValue(warning, ["message"])}</div>
                      </div>
                      <StatusBadge label={getValue(warning, ["severity"], "WARNING")} tone="warning" />
                    </div>
                  ))
                ) : (
                  <div className="empty-state">No report warnings returned.</div>
                )}
              </div>
            </div>

            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2 className="panel-title">Redactions</h2>
                  <div className="panel-subtitle">Sensitive fields excluded from this tenant-safe view.</div>
                </div>
              </div>
              <DataTable
                rows={redactions}
                emptyText="No redactions returned."
                columns={[
                  {
                    key: "redaction",
                    header: "Redaction",
                    render: (row) => <span className="mono">{getValue(row, ["name"])}</span>,
                  },
                ]}
              />
            </div>
          </section>
        </>
      ) : null}
    </>
  );
}
