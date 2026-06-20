import { useMutation, useQueryClient } from "@tanstack/react-query";
import { RadioTower, RefreshCw, RotateCcw, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { retryAdminChannelDelivery } from "../../api/endpoints/adminChannels";
import { useAdminChannelOperations } from "../../api/operationalQueries";
import { queryKeys } from "../../api/queryKeys";
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

const statusOptions = [
  { label: "All", value: "ALL" },
  { label: "Queued", value: "QUEUED" },
  { label: "Failed", value: "FAILED" },
  { label: "Dead-lettered", value: "DEAD_LETTERED" },
  { label: "Delivered", value: "DELIVERED" },
];

export function ChannelOperationsPage() {
  const { refreshKey } = useRefreshContext();
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const { data, error, isLoading } = useAdminChannelOperations(
    statusFilter,
    refreshKey,
  );
  const retryMutation = useMutation({
    mutationFn: (deliveryId: string) => retryAdminChannelDelivery(deliveryId),
    onSuccess: async (result) => {
      const status = formatDisplay(getNestedValue(result, ["retry", "status"]));
      setActionMessage(`Retry completed with status ${status}.`);
      await queryClient.invalidateQueries({
        queryKey: queryKeys.adminChannelOperations(statusFilter, refreshKey),
      });
    },
    onError: (retryError: unknown) => {
      const message =
        retryError && typeof retryError === "object" && "message" in retryError
          ? String((retryError as { message: unknown }).message)
          : "Retry could not be completed.";
      setActionMessage(message);
    },
  });

  if (isLoading) {
    return <LoadingState label="Loading channel operations" />;
  }

  if (error) {
    return <ErrorPanel error={error} />;
  }

  const readiness = asRecord(getNestedValue(data?.readiness, ["readiness"], {}));
  const deliveries = asRecord(
    getNestedValue(data?.deliveries, ["deliveries"], {}),
  );
  const audit = asRecord(getNestedValue(data?.audit, ["audit"], {}));
  const summary = asRecord(getNestedValue(deliveries, ["summary"], {}));
  const deliveryRows = asArray(getNestedValue(deliveries, ["items"], []));
  const auditRows = asArray(getNestedValue(audit, ["items"], []));
  const readinessItems = asArray(getNestedValue(readiness, ["items"], []));
  const retryableRows = deliveryRows.filter((delivery) =>
    Boolean(getNestedValue(delivery, ["retryable"], false)),
  );
  const deadLetterRows = deliveryRows.filter(
    (delivery) => getValue(delivery, ["status"]) === "DEAD_LETTERED",
  );
  const readinessStatus = formatDisplay(getNestedValue(readiness, ["status"]));
  const readyCount = formatDisplay(
    getNestedValue(readiness, ["summary", "ready_count"], 0),
  );
  const channelCount = formatDisplay(
    getNestedValue(readiness, ["summary", "count"], 0),
  );

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Amplifi Admin - Channels</div>
          <h1 className="page-title">Channel Operations</h1>
          <p className="page-copy">
            Monitor WhatsApp, SMS, and USSD readiness, delivery outcomes,
            retryable failures, and channel audit evidence from one operational
            surface.
          </p>
        </div>
        <StatusBadge
          label={readinessStatus}
          tone={statusTone(readinessStatus)}
        />
      </section>

      <section className="grid-4">
        <KpiCard
          label="Provider readiness"
          value={`${readyCount}/${channelCount}`}
          footnote="Configured adapters"
          icon={RadioTower}
        />
        <KpiCard
          label="Queued"
          value={formatDisplay(getNestedValue(summary, ["queued"], 0))}
          footnote="Waiting for provider handoff"
          icon={RefreshCw}
        />
        <KpiCard
          label="Retryable"
          value={retryableRows.length}
          footnote="Safe to retry after correction"
          icon={RotateCcw}
        />
        <KpiCard
          label="Dead-lettered"
          value={formatDisplay(getNestedValue(summary, ["dead_lettered"], 0))}
          footnote="Needs operational review"
          icon={ShieldCheck}
        />
      </section>

      <section className="grid-2">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Channel readiness</h2>
              <div className="panel-subtitle">
                Provider configuration and supported channel posture.
              </div>
            </div>
            <StatusBadge
              label={readinessStatus}
              tone={statusTone(readinessStatus)}
            />
          </div>
          <div className="panel-body route-list">
            {readinessItems.length ? (
              readinessItems.map((item) => {
                const status = getValue(item, ["status"]);
                return (
                  <div className="route-item" key={getValue(item, ["channel_code"])}>
                    <div>
                      <div className="route-name">
                        {getValue(item, ["label", "channel_code"])}
                      </div>
                      <div className="route-path">
                        {getValue(item, ["recommended_action"])}
                      </div>
                    </div>
                    <StatusBadge label={status} tone={statusTone(status)} />
                  </div>
                );
              })
            ) : (
              <div className="empty-state">No channel readiness returned.</div>
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Delivery posture</h2>
              <div className="panel-subtitle">
                Queue health and customer-contact safety signals.
              </div>
            </div>
          </div>
          <div className="panel-body">
            <div className="summary-grid">
              <SummaryItem
                label="Sent"
                value={formatDisplay(getNestedValue(summary, ["sent"], 0))}
              />
              <SummaryItem
                label="Delivered"
                value={formatDisplay(getNestedValue(summary, ["delivered"], 0))}
              />
              <SummaryItem
                label="Failed"
                value={formatDisplay(getNestedValue(summary, ["failed"], 0))}
              />
              <SummaryItem
                label="Records"
                value={formatDisplay(getNestedValue(summary, ["count"], 0))}
              />
            </div>
            {actionMessage ? (
              <div className="state-panel compact">{actionMessage}</div>
            ) : null}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Delivery operations</h2>
            <div className="panel-subtitle">
              Filter by lifecycle status and retry recoverable failures after
              the provider issue is corrected.
            </div>
          </div>
          <SegmentedFilter
            ariaLabel="Filter channel deliveries"
            onChange={setStatusFilter}
            options={statusOptions}
            value={statusFilter}
          />
        </div>
        <DataTable
          rows={deliveryRows}
          emptyText="No channel delivery records returned."
          columns={[
            {
              key: "delivery",
              header: "Delivery",
              render: (row) => (
                <span className="mono">{getValue(row, ["delivery_id"])}</span>
              ),
            },
            {
              key: "channel",
              header: "Channel",
              render: (row) => getValue(row, ["channel_code"]),
            },
            {
              key: "status",
              header: "Status",
              render: (row) => {
                const status = getValue(row, ["status"]);
                return <StatusBadge label={status} tone={statusTone(status)} />;
              },
            },
            {
              key: "recipient",
              header: "Recipient ref",
              render: (row) => (
                <span className="mono">{getValue(row, ["recipient_ref"])}</span>
              ),
            },
            {
              key: "attempts",
              header: "Attempts",
              render: (row) =>
                `${getValue(row, ["attempt_count"], "0")}/${getValue(row, ["max_attempts"], "3")}`,
            },
            {
              key: "next",
              header: "Next step",
              render: (row) => nextStep(row),
            },
            {
              key: "action",
              header: "Action",
              render: (row) => {
                const deliveryId = getValue(row, ["delivery_id"]);
                const canRetry = Boolean(getNestedValue(row, ["retryable"], false));
                return (
                  <button
                    className="button secondary"
                    disabled={!canRetry || retryMutation.isPending}
                    onClick={() => retryMutation.mutate(deliveryId)}
                    type="button"
                  >
                    Retry
                  </button>
                );
              },
            },
          ]}
        />
      </section>

      <section className="grid-2">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Exception queue</h2>
              <div className="panel-subtitle">
                Recoverable failures and dead letters that need operator focus.
              </div>
            </div>
            <StatusBadge
              label={`${retryableRows.length + deadLetterRows.length} open`}
              tone={retryableRows.length || deadLetterRows.length ? "warning" : "success"}
            />
          </div>
          <div className="panel-body route-list">
            {[...retryableRows, ...deadLetterRows].slice(0, 8).map((row) => {
              const deliveryId = getValue(row, ["delivery_id"]);
              const status = getValue(row, ["status"]);
              return (
                <div className="route-item" key={deliveryId}>
                  <div>
                    <div className="route-name">{deliveryId}</div>
                    <div className="route-path">{nextStep(row)}</div>
                    <div className="route-path">
                      {getValue(row, ["dead_letter_reason"], "Provider review")}
                    </div>
                  </div>
                  <StatusBadge label={status} tone={statusTone(status)} />
                </div>
              );
            })}
            {!retryableRows.length && !deadLetterRows.length ? (
              <div className="empty-state">No channel exceptions returned.</div>
            ) : null}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Audit evidence</h2>
              <div className="panel-subtitle">
                Latest sanitized channel delivery lifecycle events.
              </div>
            </div>
            <StatusBadge
              label={`${auditRows.length} events`}
              tone={auditRows.length ? "info" : "neutral"}
            />
          </div>
          <DataTable
            rows={auditRows.slice(0, 8)}
            emptyText="No channel audit records returned."
            columns={[
              {
                key: "event",
                header: "Event",
                render: (row) => getValue(row, ["event_type"]),
              },
              {
                key: "delivery",
                header: "Delivery",
                render: (row) => (
                  <span className="mono">{getValue(row, ["delivery_id"])}</span>
                ),
              },
              {
                key: "channel",
                header: "Channel",
                render: (row) => getValue(row, ["channel_code"]),
              },
              {
                key: "recipient",
                header: "Recipient ref",
                render: (row) => (
                  <span className="mono">
                    {getValue(row, ["recipient_ref"])}
                  </span>
                ),
              },
            ]}
          />
        </div>
      </section>
    </>
  );
}

function nextStep(row: Record<string, unknown>): string {
  const status = getValue(row, ["status"]);
  if (status === "FAILED" && Boolean(getNestedValue(row, ["retryable"], false))) {
    return "Correct provider issue, then retry.";
  }
  if (status === "DEAD_LETTERED") {
    return "Review consent, recipient, and provider response before contact.";
  }
  if (status === "QUEUED") {
    return "Waiting for provider handoff.";
  }
  if (status === "DELIVERED") {
    return "Delivery confirmed by signed callback.";
  }
  return "Monitor audit and callback evidence.";
}
