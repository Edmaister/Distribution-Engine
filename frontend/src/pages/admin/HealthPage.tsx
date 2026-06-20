import {
  AlertTriangle,
  CheckCircle2,
  Activity,
  Database,
  ShieldCheck,
} from "lucide-react";
import { useHealthReadiness } from "../../api/operationalQueries";
import { EmptyState } from "../../components/EmptyState";
import { ErrorPanel } from "../../components/ErrorPanel";
import { KpiCard } from "../../components/KpiCard";
import { LoadingState } from "../../components/LoadingState";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";
import {
  formatDisplay,
  getNestedValue,
  objectEntries,
  statusTone,
  useRefreshContext,
} from "../pageUtils";

export function HealthPage() {
  const { refreshKey } = useRefreshContext();
  const { data, error, isLoading } = useHealthReadiness(refreshKey);

  if (isLoading) {
    return <LoadingState label="Loading health checks" />;
  }

  if (error) {
    return <ErrorPanel error={error} />;
  }

  const runtimeComponents = objectEntries(
    getNestedValue(data?.health, ["components"], {}),
  ).filter(([name]) => name !== "schema");
  const schemaGroups = objectEntries(
    getNestedValue(data?.readiness, ["components", "schema", "groups"], {}),
  );
  const unhealthyComponents = runtimeComponents.filter(([, component]) => {
    if (!("ok" in component)) {
      return false;
    }
    return formatDisplay(component.ok) !== "Yes";
  });
  const missingSchemaGroups = schemaGroups.filter(
    ([, group]) => formatDisplay(group.ok) !== "Yes",
  );
  const runtimeReady =
    unhealthyComponents.length === 0 && missingSchemaGroups.length === 0;

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Amplifi Admin - Runtime Health</div>
          <h1 className="page-title">Runtime Health</h1>
          <p className="page-copy">
            Confirm that core dependencies, schema groups, and platform
            readiness signals are healthy before operators rely on event replay,
            settlement, funding, or distribution workflows.
          </p>
        </div>
        <StatusBadge
          label={runtimeReady ? "Ready" : "Review needed"}
          tone={runtimeReady ? "success" : "warning"}
        />
      </section>

      <section className="runtime-health-grid">
        <div className="runtime-health-card primary">
          <div className="runtime-health-card-top">
            <div>
              <div className="runtime-health-kicker">Runtime posture</div>
              <h2>
                {runtimeReady
                  ? "Platform dependencies are ready"
                  : "Runtime review is needed"}
              </h2>
            </div>
            {runtimeReady ? (
              <CheckCircle2 size={24} />
            ) : (
              <AlertTriangle size={24} />
            )}
          </div>
          <p>
            Runtime Health tells the operator whether the backend can support
            the admin rails. It checks live dependencies and the database groups
            required by the target-state platform.
          </p>
          <div className="runtime-health-metrics">
            <SummaryItem label="Components" value={runtimeComponents.length} />
            <SummaryItem label="Issues" value={unhealthyComponents.length} />
            <SummaryItem label="Schema groups" value={schemaGroups.length} />
            <SummaryItem
              label="Schema gaps"
              value={missingSchemaGroups.length}
            />
          </div>
        </div>

        <div className="panel runtime-action-map">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Operator action map</h2>
              <div className="panel-subtitle">
                Where to inspect readiness before operating the rails.
              </div>
            </div>
          </div>
          <div className="panel-body admin-attention-list">
            <RuntimeActionMapRow
              label="Check dependencies"
              copy="Review database, messaging, and service dependency status."
              targetId="runtime-components"
              value={
                unhealthyComponents.length
                  ? `${unhealthyComponents.length} issues`
                  : "Healthy"
              }
              tone={unhealthyComponents.length ? "warning" : "success"}
            />
            <RuntimeActionMapRow
              label="Check schema readiness"
              copy="Confirm the database groups needed by the platform rails are present."
              targetId="schema-readiness"
              value={
                missingSchemaGroups.length
                  ? `${missingSchemaGroups.length} gaps`
                  : "Ready"
              }
              tone={missingSchemaGroups.length ? "warning" : "success"}
            />
            <RuntimeActionMapRow
              label="Confirm operating posture"
              copy="Use the top posture before trusting write-heavy workflows."
              targetId="runtime-components"
              value={runtimeReady ? "Operate" : "Review"}
              tone={runtimeReady ? "success" : "warning"}
            />
          </div>
        </div>
      </section>

      <section className="grid-3">
        <KpiCard
          label="Health endpoint"
          value="OK"
          footnote="/health responded"
          icon={Activity}
        />
        <KpiCard
          label="Readiness endpoint"
          value="OK"
          footnote="/readyz responded"
          icon={ShieldCheck}
        />
        <KpiCard
          label="Schema spine"
          value={missingSchemaGroups.length ? "Review" : "Ready"}
          footnote="Backend readiness payload"
          icon={Database}
        />
      </section>

      <section className="grid-2">
        <div className="panel" id="runtime-components">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Runtime components</h2>
              <div className="panel-subtitle">
                Current dependency status from `/health`.
              </div>
            </div>
          </div>
          <div className="panel-body">
            <div className="status-list">
              {runtimeComponents.length === 0 ? (
                <EmptyState label="No runtime components returned." />
              ) : (
                runtimeComponents.map(([name, component]) => {
                  const hasHealthFlag = "ok" in component;
                  const ok = formatDisplay(component.ok);
                  const msg = hasHealthFlag
                    ? formatDisplay(component.msg)
                    : formatDisplay(component.value);
                  return (
                    <div className="status-row" key={name}>
                      <div>
                        <div className="status-name">
                          {formatGroupName(name)}
                        </div>
                        <div className="table-subtext">{msg}</div>
                      </div>
                      <StatusBadge
                        label={
                          hasHealthFlag
                            ? ok === "Yes"
                              ? "OK"
                              : "Issue"
                            : "Info"
                        }
                        tone={hasHealthFlag ? statusTone(ok) : "neutral"}
                      />
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
        <div className="panel" id="schema-readiness">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Schema readiness</h2>
              <div className="panel-subtitle">
                Required database groups for the platform spine.
              </div>
            </div>
          </div>
          <div className="panel-body">
            <div className="status-list">
              {schemaGroups.length === 0 ? (
                <EmptyState label="No schema readiness groups returned." />
              ) : (
                schemaGroups.map(([name, group]) => {
                  const ok = formatDisplay(group.ok);
                  const missing = Array.isArray(group.missing_tables)
                    ? group.missing_tables.length
                    : 0;
                  return (
                    <div className="status-row" key={name}>
                      <div>
                        <div className="status-name">
                          {formatGroupName(name)}
                        </div>
                        <div className="table-subtext">
                          {missing === 0
                            ? "No missing tables"
                            : `${missing} missing tables`}
                        </div>
                      </div>
                      <StatusBadge
                        label={ok === "Yes" ? "Ready" : "Missing"}
                        tone={statusTone(ok)}
                      />
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

function RuntimeActionMapRow({
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
  tone: "success" | "warning" | "danger" | "info" | "neutral";
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

function formatGroupName(value: string): string {
  return value.replace(/_/g, " ");
}
