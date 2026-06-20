import { AlertTriangle, CheckCircle2, GitBranch, Inbox, RotateCw } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import {
  getEnterpriseEventDashboard,
  getEnterpriseEvents,
  getEnterpriseEventSummary,
  replayEnterpriseEvent,
} from "../../api/endpoints/enterpriseEvents";
import { ActionGuardrail, GuardrailItem, GuardrailTone } from "../../components/ActionGuardrail";
import { DataTable } from "../../components/DataTable";
import { ErrorPanel } from "../../components/ErrorPanel";
import { FieldLabel } from "../../components/FieldLabel";
import { InfoTooltip } from "../../components/InfoTooltip";
import { JourneyStep, JourneyTracker } from "../../components/JourneyTracker";
import { KpiCard } from "../../components/KpiCard";
import { LoadingState } from "../../components/LoadingState";
import { PanelTitle } from "../../components/PanelTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryGrid } from "../../components/SummaryGrid";
import { SummaryItem } from "../../components/SummaryItem";
import {
  asArray,
  formatDisplay,
  getNestedValue,
  getValue,
  statusTone,
  useRefreshContext,
} from "../pageUtils";

export function EnterpriseEventsPage() {
  const { refreshKey } = useRefreshContext();
  const [summary, setSummary] = useState<unknown>(null);
  const [dashboard, setDashboard] = useState<unknown>(null);
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [tenantCode, setTenantCode] = useState("");
  const [processingStatus, setProcessingStatus] = useState("");
  const [sourceSystem, setSourceSystem] = useState("");
  const [submittedFilters, setSubmittedFilters] = useState({
    tenantCode: "",
    processingStatus: "",
    sourceSystem: "",
  });
  const [selectedEventId, setSelectedEventId] = useState("");
  const [replayDryRun, setReplayDryRun] = useState(true);
  const [replayLoading, setReplayLoading] = useState(false);
  const [replayError, setReplayError] = useState<unknown>(null);
  const [replayResult, setReplayResult] = useState<Record<string, unknown> | null>(null);
  const [localRefreshKey, setLocalRefreshKey] = useState(0);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    Promise.all([
      getEnterpriseEventSummary(),
      getEnterpriseEventDashboard(7, submittedFilters.tenantCode || undefined),
      getEnterpriseEvents(
        25,
        submittedFilters.processingStatus || undefined,
        submittedFilters.sourceSystem || undefined,
      ),
    ])
      .then(([summaryPayload, dashboardPayload, eventPayload]) => {
        if (alive) {
          setSummary(summaryPayload);
          setDashboard(dashboardPayload);
          setRows(asArray(eventPayload));
        }
      })
      .catch((requestError) => alive && setError(requestError))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [refreshKey, localRefreshKey, submittedFilters]);

  useEffect(() => {
    if (!rows.length) {
      setSelectedEventId("");
      return;
    }

    const current = rows.find((row) => getValue(row, ["inboxEventId", "inbox_event_id"]) === selectedEventId);
    setSelectedEventId(getValue(current || rows[0], ["inboxEventId", "inbox_event_id"], ""));
  }, [rows, selectedEventId]);

  const selectedEvent = rows.find((row) => getValue(row, ["inboxEventId", "inbox_event_id"]) === selectedEventId);
  const eventGuidance = getEnterpriseEventGuidance({ rows, dashboard, replayResult });
  const replayGuard = getReplayGuardrail({ selectedEvent, replayDryRun, replayLoading });
  const totalEvents = Number(getNestedValue(summary, ["total"], 0));
  const queuedCount = statusCount(dashboard, "QUEUED");
  const failedCount = statusCount(dashboard, "FAILED");
  const ignoredCount = statusCount(dashboard, "IGNORED");
  const problemEvents = asArrayFromKey(dashboard, "recentProblemEvents");
  const sourceCount = asArrayFromKey(dashboard, "bySourceSystem").length;
  const eventTypeCount = asArrayFromKey(dashboard, "byEventType").length;
  const hasExceptions = failedCount > 0 || problemEvents.length > 0;

  function submitFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setReplayError(null);
    setReplayResult(null);
    setSubmittedFilters({
      tenantCode: tenantCode.trim().toUpperCase(),
      processingStatus: processingStatus.trim().toUpperCase(),
      sourceSystem: sourceSystem.trim().toUpperCase(),
    });
  }

  function submitReplay(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedEventId) {
      return;
    }
    if (
      !replayDryRun &&
      !window.confirm(
        `Queue this ${getValue(selectedEvent || {}, ["eventType", "event_type"], "enterprise")} event for replay? This creates replay work for the backend processor.`,
      )
    ) {
      return;
    }
    setReplayLoading(true);
    setReplayError(null);
    setReplayResult(null);
    replayEnterpriseEvent(selectedEventId, replayDryRun)
      .then((payload) => {
        setReplayResult(payload);
        if (!replayDryRun) {
          setLocalRefreshKey((value) => value + 1);
        }
      })
      .catch((requestError) => setReplayError(requestError))
      .finally(() => setReplayLoading(false));
  }

  if (loading) {
    return <LoadingState label="Loading event inbox" />;
  }

  if (error) {
    return <ErrorPanel error={error} />;
  }

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Amplifi Admin - Event Fabric</div>
          <h1 className="page-title">Event Fabric</h1>
          <p className="page-copy">
            Operate the Hogan and enterprise event path that supports account activation, salary switching,
            debit order switching, replay, and auditability.
          </p>
        </div>
        <StatusBadge label={hasExceptions ? "Review needed" : "Replay-backed"} tone={hasExceptions ? "warning" : "success"} />
      </section>

      <section className="event-fabric-grid">
        <div className="event-fabric-card primary">
          <div className="event-fabric-card-top">
            <div>
              <div className="event-fabric-kicker">Fabric posture</div>
              <h2>{hasExceptions ? "Exceptions need operator review" : "Event intake is observable"}</h2>
            </div>
            {hasExceptions ? <AlertTriangle size={24} /> : <CheckCircle2 size={24} />}
          </div>
          <p>
            Source events land in the inbox, move through processing states, and can be replay checked before any
            replay is queued. This keeps activation and switching signals auditable.
          </p>
          <div className="event-fabric-metrics">
            <SummaryItem label="Total" value={totalEvents} />
            <SummaryItem label="Queued" value={queuedCount} />
            <SummaryItem label="Ignored" value={ignoredCount} />
            <SummaryItem label="Failed" value={failedCount} />
          </div>
        </div>

        <div className="panel event-action-map">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Shows where the operator should look first based on the live event dashboard."
                title="Operator action map"
              />
              <div className="panel-subtitle">Where to inspect, decide, and monitor.</div>
            </div>
          </div>
          <div className="panel-body admin-attention-list">
            <ActionMapRow
              label="Inspect intake"
              copy={`${rows.length} latest inbox records returned for review.`}
              targetId="events-inbox-records"
              value={`${rows.length} rows`}
              tone={rows.length ? "info" : "neutral"}
            />
            <ActionMapRow
              label="Review exceptions"
              copy="Problem, failed, or ignored events should be checked before replay."
              targetId="events-problem-events"
              value={hasExceptions ? "Review" : "Clear"}
              tone={hasExceptions ? "warning" : "success"}
            />
            <ActionMapRow
              label="Replay safely"
              copy="Use the replay control in dry-run mode before queueing a backend replay."
              targetId="events-replay-control"
              value={replayDryRun ? "Dry run" : "Will queue"}
              tone={replayDryRun ? "info" : "warning"}
            />
            <ActionMapRow
              label="Monitor mix"
              copy={`${sourceCount} source groups and ${eventTypeCount} event type groups are visible.`}
              targetId="events-processing-status"
              value="Monitor"
              tone="info"
            />
          </div>
        </div>
      </section>

      <section className="grid-3">
        <KpiCard label="Returned events" value={rows.length} footnote="Latest inbox records" icon={Inbox} />
        <KpiCard
          label="Summary total"
          value={formatDisplay(totalEvents)}
          footnote="Processing status summary"
          icon={GitBranch}
        />
        <KpiCard label="Replay service" value="Ready" footnote="Dry-run and queued replay API exists" icon={RotateCw} />
      </section>

      <JourneyTracker
        badge={eventGuidance.badge}
        currentCopy={eventGuidance.copy}
        currentTitle={eventGuidance.title}
        steps={eventGuidance.steps}
        subtitle="Step-by-step path from upstream intake through processing, replay, and operational monitoring."
        title="Enterprise event journey"
        tone={eventGuidance.tone}
      />

      <section className="grid-2">
        <div className="panel" id="events-inbox-filters">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Use these filters to narrow the event inbox before choosing an event to inspect or replay."
                title="Inbox filters"
              />
              <div className="panel-subtitle">Narrow the event list before choosing a replay candidate.</div>
            </div>
          </div>
          <div className="panel-body">
            <form className="event-filter-form" onSubmit={submitFilters}>
              <div className="field">
                <FieldLabel
                  help="Limits the inbox to one tenant, for example FNB. Leave it empty to see all tenants."
                  htmlFor="event-tenant"
                  label="Tenant code"
                />
                <input
                  className="input"
                  id="event-tenant"
                  placeholder="All tenants"
                  value={tenantCode}
                  onChange={(event) => setTenantCode(event.target.value)}
                />
              </div>
              <div className="field">
                <FieldLabel
                  help="Filters by where the event is in processing, such as QUEUED, IGNORED, PROCESSED, or FAILED."
                  htmlFor="event-status"
                  label="Processing status"
                />
                <input
                  className="input"
                  id="event-status"
                  placeholder="Any status"
                  value={processingStatus}
                  onChange={(event) => setProcessingStatus(event.target.value)}
                />
              </div>
              <div className="field">
                <FieldLabel
                  help="Filters by the upstream system that sent the event. Hogan is the core-banking source in this flow."
                  htmlFor="event-source"
                  label="Source system"
                />
                <input
                  className="input"
                  id="event-source"
                  placeholder="Any source"
                  value={sourceSystem}
                  onChange={(event) => setSourceSystem(event.target.value)}
                />
              </div>
              <button className="button" type="submit">
                Apply filters
              </button>
            </form>
          </div>
        </div>

        <div className="panel" id="events-replay-control">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Replay lets an operator re-run one inbox event through the backend processing path."
                title="Replay control"
              />
              <div className="panel-subtitle">Dry run first, then queue a replay only when intended.</div>
            </div>
            <StatusBadge label={replayDryRun ? "Dry run" : "Will queue"} tone={replayDryRun ? "info" : "warning"} />
          </div>
          <div className="panel-body">
            <form className="event-replay-form" onSubmit={submitReplay}>
              <div className="field">
                <FieldLabel
                  help="Choose the specific inbox event to check or replay. The value includes event type, status, and source event reference."
                  htmlFor="event-replay-id"
                  label="Event"
                />
                <select
                  className="input"
                  id="event-replay-id"
                  value={selectedEventId}
                  onChange={(event) => setSelectedEventId(event.target.value)}
                >
                  {rows.length ? null : <option value="">No events returned</option>}
                  {rows.map((row) => {
                    const eventId = getValue(row, ["inboxEventId", "inbox_event_id"], "");
                    return (
                      <option key={eventId} value={eventId}>
                        {eventLabel(row)}
                      </option>
                    );
                  })}
                </select>
              </div>
              <label className="check-field">
                <input
                  checked={replayDryRun}
                  type="checkbox"
                  onChange={(event) => setReplayDryRun(event.target.checked)}
                />
                Dry run only
                <InfoTooltip text="When this is on, the backend checks whether the event can replay but does not queue or process it." />
              </label>
              <button className="button" disabled={!replayGuard.canRun} type="submit">
                <RotateCw size={16} />
                {replayLoading ? "Running" : replayDryRun ? "Run replay check" : "Queue replay"}
              </button>
            </form>
            <ActionGuardrail
              badge={replayGuard.badge}
              tone={replayGuard.tone}
              title={replayGuard.title}
              copy={replayGuard.copy}
              items={replayGuard.items}
            />
            <SelectedEventSummary event={selectedEvent} />
            {replayError ? <div className="action-result"><ErrorPanel error={replayError} /></div> : null}
            {replayResult ? <ReplayResult payload={replayResult} /> : null}
          </div>
        </div>
      </section>

      <section className="grid-2">
        <div className="panel" id="events-processing-status">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Shows how many inbox events are queued, ignored, processed, failed, or in another processing state."
                title="Processing status"
              />
              <div className="panel-subtitle">Inbox state by processing outcome.</div>
            </div>
          </div>
          <div className="panel-body">
            <StatusRows rows={asArrayFromKey(dashboard, "byStatus")} labelKeys={["processingStatus", "processing_status", "status"]} />
          </div>
        </div>
        <div className="panel" id="events-source-systems">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Shows which upstream systems are sending events into the inbox."
                title="Source systems"
              />
              <div className="panel-subtitle">Events received by upstream system.</div>
            </div>
          </div>
          <div className="panel-body">
            <StatusRows rows={asArrayFromKey(dashboard, "bySourceSystem")} labelKeys={["sourceSystem", "source_system", "source"]} />
          </div>
        </div>
      </section>

      <section className="grid-2">
        <div className="panel" id="events-event-types">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Shows the business type of event, such as account activation or customer profile update."
                title="Event types"
              />
              <div className="panel-subtitle">Intake volume by enterprise event type.</div>
            </div>
          </div>
          <div className="panel-body">
            <StatusRows rows={asArrayFromKey(dashboard, "byEventType")} labelKeys={["eventType", "event_type"]} />
          </div>
        </div>
        <div className="panel" id="events-problem-events">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Shows recent events that need attention because they were not processed normally."
                title="Recent problem events"
              />
              <div className="panel-subtitle">Events needing review or replay attention.</div>
            </div>
          </div>
          <DataTable
            emptyText="No problem events returned."
            rows={asArrayFromKey(dashboard, "recentProblemEvents")}
            columns={[
              { key: "source", header: "Source", render: (row) => getValue(row, ["sourceSystem", "source_system", "source"]) },
              { key: "event", header: "Event type", render: (row) => getValue(row, ["eventType", "event_type"]) },
              {
                key: "status",
                header: "Status",
                render: (row) => {
                  const status = getValue(row, ["processingStatus", "processing_status", "status"]);
                  return <StatusBadge label={status} tone={statusTone(status)} />;
                },
              },
              { key: "received", header: "Received", render: (row) => <span className="mono">{getValue(row, ["receivedAt", "received_at", "created_at"])}</span> },
            ]}
          />
        </div>
      </section>

      <section className="panel" id="events-inbox-records">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="The latest raw inbox records, shown as operational fields instead of JSON."
              title="Inbox records"
            />
            <div className="panel-subtitle">Last 25 enterprise events returned by the API.</div>
          </div>
        </div>
        <DataTable
          rows={rows}
          columns={[
            { key: "source", header: "Source", render: (row) => getValue(row, ["sourceSystem", "source_system", "source"]) },
            { key: "event", header: "Event type", render: (row) => getValue(row, ["eventType", "event_type"]) },
            {
              key: "status",
              header: "Status",
              render: (row) => {
                const status = getValue(row, ["processingStatus", "processing_status", "status"]);
                return <StatusBadge label={status} tone={statusTone(status)} />;
              },
            },
            { key: "correlation", header: "Correlation", render: (row) => <span className="mono">{getValue(row, ["correlationId", "correlation_id", "sourceEventId", "source_event_id"])}</span> },
            { key: "received", header: "Received", render: (row) => <span className="mono">{getValue(row, ["receivedAt", "received_at", "created_at"])}</span> },
          ]}
        />
      </section>
    </>
  );
}

function SelectedEventSummary({ event }: { event?: Record<string, unknown> }) {
  if (!event) {
    return <div className="state-panel">No event selected.</div>;
  }

  return (
    <SummaryGrid
      actionResult
      items={[
        ["Source", getValue(event, ["sourceSystem", "source_system"])],
        ["Type", getValue(event, ["eventType", "event_type"])],
        ["Status", getValue(event, ["processingStatus", "processing_status"])],
      ]}
    />
  );
}

function ActionMapRow({
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

function ReplayResult({ payload }: { payload: Record<string, unknown> }) {
  return (
    <SummaryGrid
      actionResult
      items={[
        ["Status", getValue(payload, ["status"])],
        ["Queued", getValue(payload, ["queued"], "false")],
        ["Mode", getValue(payload, ["dry_run", "dryRun"], "-")],
      ]}
    />
  );
}

function StatusRows({
  rows,
  labelKeys,
}: {
  rows: Record<string, unknown>[];
  labelKeys: string[];
}) {
  if (!rows.length) {
    return <div className="state-panel">No records returned.</div>;
  }

  return (
    <div className="status-list">
      {rows.map((row, index) => {
        const label = getValue(row, labelKeys);
        const count = getValue(row, ["eventCount", "event_count", "count"], "0");
        return (
          <div className="status-row" key={`${label}-${index}`}>
            <StatusBadge label={label} tone={statusTone(label)} />
            <span className="status-count">{count}</span>
          </div>
        );
      })}
    </div>
  );
}

function asArrayFromKey(value: unknown, key: string): Record<string, unknown>[] {
  if (!value || typeof value !== "object") {
    return [];
  }

  const found = (value as Record<string, unknown>)[key];
  return Array.isArray(found) ? (found as Record<string, unknown>[]) : [];
}

function eventLabel(row: Record<string, unknown>): string {
  return `${getValue(row, ["eventType", "event_type"])} | ${getValue(
    row,
    ["processingStatus", "processing_status"],
  )} | ${getValue(row, ["sourceEventId", "source_event_id", "inboxEventId", "inbox_event_id"])}`;
}

type BadgeTone = GuardrailTone;

function getReplayGuardrail({
  selectedEvent,
  replayDryRun,
  replayLoading,
}: {
  selectedEvent?: Record<string, unknown>;
  replayDryRun: boolean;
  replayLoading: boolean;
}): {
  badge: string;
  tone: BadgeTone;
  title: string;
  copy: string;
  canRun: boolean;
  items: GuardrailItem[];
} {
  const eventType = selectedEvent ? getValue(selectedEvent, ["eventType", "event_type"], "Selected event") : "-";
  const eventStatus = selectedEvent ? getValue(selectedEvent, ["processingStatus", "processing_status"], "-") : "-";
  const source = selectedEvent ? getValue(selectedEvent, ["sourceSystem", "source_system"], "-") : "-";

  if (!selectedEvent) {
    return {
      badge: "Blocked",
      tone: "neutral",
      title: "Select an event first",
      copy: "Replay controls are disabled until an inbox event is selected from the replay dropdown.",
      canRun: false,
      items: [
        { label: "Selected event", value: "Missing", tone: "warning" },
        { label: "Mode", value: replayDryRun ? "Dry run" : "Queue", tone: replayDryRun ? "info" : "warning" },
        { label: "System change", value: "None", tone: "neutral" },
      ],
    };
  }

  if (replayLoading) {
    return {
      badge: "Running",
      tone: "info",
      title: "Replay request is running",
      copy: "Wait for the backend response before changing the selected event or running another replay action.",
      canRun: false,
      items: [
        { label: "Selected event", value: eventType, tone: "info" },
        { label: "Current status", value: eventStatus, tone: statusTone(eventStatus) as BadgeTone },
        { label: "System change", value: replayDryRun ? "None" : "Queue pending", tone: replayDryRun ? "neutral" : "warning" },
      ],
    };
  }

  if (replayDryRun) {
    return {
      badge: "Safe check",
      tone: "info",
      title: "Dry-run replay check",
      copy: "This checks whether the selected event can be replayed. It does not queue the event or change processing state.",
      canRun: true,
      items: [
        { label: "Selected event", value: eventType, tone: "info" },
        { label: "Source", value: source, tone: "neutral" },
        { label: "System change", value: "None", tone: "success" },
      ],
    };
  }

  return {
    badge: "Will queue",
    tone: "warning",
    title: "Queue replay",
    copy: "This queues the selected event for backend replay. Use this only after a dry-run check or operator review confirms replay is intended.",
    canRun: true,
    items: [
      { label: "Selected event", value: eventType, tone: "info" },
      { label: "Current status", value: eventStatus, tone: statusTone(eventStatus) as BadgeTone },
      { label: "System change", value: "Replay queued", tone: "warning" },
    ],
  };
}

function getEnterpriseEventGuidance({
  rows,
  dashboard,
  replayResult,
}: {
  rows: Record<string, unknown>[];
  dashboard: unknown;
  replayResult: Record<string, unknown> | null;
}): {
  badge: string;
  tone: BadgeTone;
  title: string;
  copy: string;
  steps: JourneyStep[];
} {
  const problemEvents = asArrayFromKey(dashboard, "recentProblemEvents");
  const queuedCount = statusCount(dashboard, "QUEUED");
  const failedCount = statusCount(dashboard, "FAILED");
  const ignoredCount = statusCount(dashboard, "IGNORED");
  const hasReplay = Boolean(replayResult);

  if (!rows.length) {
    return {
      badge: "No events",
      tone: "neutral",
      title: "Wait for enterprise intake",
      copy: "No inbox events were returned for the current filter. Confirm the source system and tenant filter before replaying anything.",
      steps: eventSteps("current", "waiting", "waiting", "waiting", "waiting"),
    };
  }

  if (failedCount > 0 || problemEvents.length > 0) {
    return {
      badge: "Review",
      tone: "warning",
      title: "Review problem events",
      copy: "Some events need operator attention. Inspect the problem list, choose an event, and run a replay check before queueing replay.",
      steps: eventSteps("done", "review", "current", hasReplay ? "done" : "waiting", "waiting"),
    };
  }

  if (queuedCount > 0) {
    return {
      badge: "Queued",
      tone: "info",
      title: "Monitor queued processing",
      copy: "Events are queued for processing. Watch status movement before taking replay action.",
      steps: eventSteps("done", "current", "waiting", "waiting", "waiting"),
    };
  }

  if (!hasReplay && ignoredCount > 0) {
    return {
      badge: "Replay",
      tone: "info",
      title: "Run a replay check",
      copy: "Ignored events are present. Use dry-run replay to confirm whether a selected event can safely move through processing again.",
      steps: eventSteps("done", "done", "current", "current", "waiting"),
    };
  }

  return {
    badge: "Stable",
    tone: "success",
    title: "Event intake is observable",
    copy: "Enterprise intake, processing status, event types, source systems, and replay controls are visible for operations.",
    steps: eventSteps("done", "done", "done", hasReplay ? "done" : "waiting", "current"),
  };
}

function eventSteps(
  ingest: JourneyStep["state"],
  process: JourneyStep["state"],
  review: JourneyStep["state"],
  replay: JourneyStep["state"],
  monitor: JourneyStep["state"],
): JourneyStep[] {
  return [
    {
      label: "Ingest events",
      description: "Receive source events into the enterprise inbox.",
      workArea: "Inbox records and KPI cards",
      targetId: "events-inbox-records",
      state: ingest,
    },
    {
      label: "Process outcomes",
      description: "Track queued, processed, ignored, or failed outcomes.",
      workArea: "Processing status, source systems, and event types",
      targetId: "events-processing-status",
      state: process,
    },
    {
      label: "Review exceptions",
      description: "Inspect problem events before replay or escalation.",
      workArea: "Recent problem events and selected event summary",
      targetId: "events-problem-events",
      state: review,
    },
    {
      label: "Replay safely",
      description: "Run dry-run checks before queueing replay.",
      workArea: "Replay control",
      targetId: "events-replay-control",
      state: replay,
    },
    {
      label: "Monitor intake",
      description: "Watch event mix, source systems, and recent status movement.",
      workArea: "Dashboard status panels",
      targetId: "events-processing-status",
      state: monitor,
    },
  ];
}

function statusCount(dashboard: unknown, status: string): number {
  return asArrayFromKey(dashboard, "byStatus").reduce((total, row) => {
    const rowStatus = String(getValue(row, ["processingStatus", "processing_status", "status"], "")).toUpperCase();
    if (rowStatus !== status) {
      return total;
    }
    return total + Number(getValue(row, ["eventCount", "event_count", "count"], "0"));
  }, 0);
}
