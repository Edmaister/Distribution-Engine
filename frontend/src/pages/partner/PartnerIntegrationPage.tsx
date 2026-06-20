import { KeyRound, Send, ShieldCheck } from "lucide-react";
import { type FormEvent, useState } from "react";
import {
  createPartnerClient,
  createPartnerWebhook,
  exportPartnerWebhookDeadLetters,
  retryPartnerWebhookDelivery,
  rotatePartnerLegacyWebhookSecrets,
  rotatePartnerWebhookSecret,
} from "../../api/endpoints/partnerSeam";
import { usePartnerIntegrationWorkspace } from "../../api/partnerQueries";
import { ErrorPanel } from "../../components/ErrorPanel";
import { KpiCard } from "../../components/KpiCard";
import { LoadingState } from "../../components/LoadingState";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryGrid } from "../../components/SummaryGrid";
import {
  asArray,
  countFrom,
  formatDisplay,
  getNestedValue,
  statusTone,
  useRefreshContext,
} from "../pageUtils";

export function PartnerIntegrationPage() {
  const { refreshKey } = useRefreshContext();
  const { data, error, isLoading, refetch } =
    usePartnerIntegrationWorkspace(refreshKey);
  const [eventType, setEventType] = useState("OUTCOME_COMPLETED");
  const [targetUrl, setTargetUrl] = useState("");
  const [clientName, setClientName] = useState("Partner Integration Client");
  const [clientScopes, setClientScopes] = useState(
    "events:write referrals:read",
  );
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionError, setActionError] = useState<unknown>(null);
  const [actionResult, setActionResult] = useState<Record<
    string,
    unknown
  > | null>(null);

  if (isLoading) {
    return <LoadingState label="Loading partner integration" />;
  }

  if (error) {
    return <ErrorPanel error={error} />;
  }

  const identity = getNestedValue(data, ["identity"], {});
  const clients = asArray(getNestedValue(data, ["clients"], []));
  const webhooks = asArray(getNestedValue(data, ["webhooks"], []));
  const deliveries = asArray(getNestedValue(data, ["deliveries"], []));
  const exceptions = asArray(getNestedValue(data, ["exceptions"], []));
  const alerts = asArray(getNestedValue(data, ["alerts"], []));
  const summary = getNestedValue(data, ["summary"], {});
  const secretReadiness = getNestedValue(data, ["secret_readiness"], {});
  const productionReadiness = getNestedValue(
    data,
    ["production_readiness"],
    {},
  );
  const guardrailValues = getNestedValue(data, ["guardrails"], []);
  const guardrails = Array.isArray(guardrailValues)
    ? guardrailValues.map((item) => ({ item }))
    : [];
  const deliveryStatus = formatDisplay(
    getNestedValue(summary, ["status"], "HEALTHY"),
  );
  const failedCount = countFrom(summary, ["failed_count"]);
  const pendingCount = countFrom(summary, ["pending_count"]);
  const sentCount = countFrom(summary, ["sent_count"]);
  const clientId = formatDisplay(getNestedValue(identity, ["client_id"], ""));
  const mode = formatDisplay(getNestedValue(data, ["mode"], "partner"));
  const isAdminReadOnly = mode === "admin";
  const canManageWebhooks =
    !isAdminReadOnly && Boolean(clientId && clientId !== "-");
  const canOnboardClient = !isAdminReadOnly && !canManageWebhooks;
  const legacySecretCount =
    Number(
      getNestedValue(secretReadiness, ["legacy_plaintext_subscriptions"], 0),
    ) || 0;

  function refreshIntegration() {
    return refetch();
  }

  function submitCreateWebhook(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !canManageWebhooks ||
      !eventType.trim() ||
      !targetUrl.trim() ||
      actionLoading
    ) {
      return;
    }

    setActionLoading("Creating webhook");
    setActionError(null);
    setActionResult(null);
    createPartnerWebhook({
      eventType: eventType.trim(),
      targetUrl: targetUrl.trim(),
    })
      .then((payload) => {
        setActionResult({ action: "Webhook created", ...payload });
        setTargetUrl("");
        return refreshIntegration();
      })
      .catch((requestError) => setActionError(requestError))
      .finally(() => setActionLoading(null));
  }

  function submitCreateClient(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canOnboardClient || !clientName.trim() || actionLoading) {
      return;
    }

    setActionLoading("Creating client");
    setActionError(null);
    setActionResult(null);
    createPartnerClient({
      clientName: clientName.trim(),
      scopes: csvList(clientScopes),
    })
      .then((payload) => {
        setActionResult({ action: "Client created", ...payload });
        return refreshIntegration();
      })
      .catch((requestError) => setActionError(requestError))
      .finally(() => setActionLoading(null));
  }

  function rotateSecret(webhook: Record<string, unknown>) {
    const webhookId = formatDisplay(
      getNestedValue(webhook, ["webhook_id"], ""),
    );
    if (
      !canManageWebhooks ||
      !webhookId ||
      webhookId === "-" ||
      actionLoading
    ) {
      return;
    }

    setActionLoading("Rotating secret");
    setActionError(null);
    setActionResult(null);
    rotatePartnerWebhookSecret(webhookId)
      .then((payload) => {
        setActionResult({ action: "Webhook secret rotated", ...payload });
        return refreshIntegration();
      })
      .catch((requestError) => setActionError(requestError))
      .finally(() => setActionLoading(null));
  }

  function rotateLegacySecrets() {
    if (!legacySecretCount || actionLoading) {
      return;
    }

    setActionLoading("Rotating legacy secrets");
    setActionError(null);
    setActionResult(null);
    rotatePartnerLegacyWebhookSecrets(25)
      .then((payload) => {
        setActionResult({ action: "Legacy secrets rotated", ...payload });
        return refreshIntegration();
      })
      .catch((requestError) => setActionError(requestError))
      .finally(() => setActionLoading(null));
  }

  function retryDelivery(delivery: Record<string, unknown>) {
    const deliveryId = formatDisplay(
      getNestedValue(delivery, ["delivery_id"], ""),
    );
    if (
      !canManageWebhooks ||
      !deliveryId ||
      deliveryId === "-" ||
      actionLoading
    ) {
      return;
    }

    setActionLoading("Retrying delivery");
    setActionError(null);
    setActionResult(null);
    retryPartnerWebhookDelivery(deliveryId)
      .then((payload) => {
        setActionResult({ action: "Delivery queued for retry", ...payload });
        return refreshIntegration();
      })
      .catch((requestError) => setActionError(requestError))
      .finally(() => setActionLoading(null));
  }

  function exportDeadLetters() {
    if (actionLoading) {
      return;
    }

    setActionLoading("Exporting dead letters");
    setActionError(null);
    setActionResult(null);
    exportPartnerWebhookDeadLetters(500)
      .then((payload) => {
        const exportPayload = payload.export ?? {};
        const csv = String(exportPayload.csv ?? "");
        const filename = String(
          exportPayload.filename ?? "partner-webhook-dead-letters.csv",
        );
        downloadCsv(filename, csv);
        setActionResult({
          action: "Dead-letter export prepared",
          status: payload.status ?? "ok",
          export: exportPayload,
          guardrail:
            exportPayload.guardrail ??
            "Export contains failed and cancelled webhook delivery evidence only.",
        });
      })
      .catch((requestError) => setActionError(requestError))
      .finally(() => setActionLoading(null));
  }

  return (
    <div className="page-stack">
      <section className="hero-panel">
        <div>
          <div className="eyebrow">Partner Integration</div>
          <h1>Integration Health</h1>
          <p>
            Tenant-scoped credentials, webhook subscriptions, and delivery
            health for the current partner session.
          </p>
        </div>
        <StatusBadge label={deliveryStatus} tone={statusTone(deliveryStatus)} />
      </section>

      <section className="kpi-grid">
        <KpiCard
          label="Tenant"
          value={formatDisplay(getNestedValue(identity, ["tenant_code"]))}
          footnote="Partner scope"
          icon={ShieldCheck}
        />
        <KpiCard
          label="Clients"
          value={String(clients.length)}
          footnote="Active credentials visible to this session"
          icon={KeyRound}
        />
        <KpiCard
          label="Webhooks"
          value={String(webhooks.length)}
          footnote="Subscribed event endpoints"
          icon={Send}
        />
        <KpiCard
          label="Deliveries"
          value={`${sentCount}/${sentCount + pendingCount + failedCount}`}
          footnote={`${pendingCount} pending / ${failedCount} failed`}
          icon={Send}
        />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Production readiness</h2>
            <div className="panel-subtitle">
              Backend-owned checklist for code capability and production
              configuration.
            </div>
          </div>
          <StatusBadge
            label={formatDisplay(
              getNestedValue(productionReadiness, ["code_status"], "READY"),
            )}
            tone={statusTone(
              formatDisplay(
                getNestedValue(productionReadiness, ["code_status"], "READY"),
              ),
            )}
          />
        </div>
        <div className="panel-body">
          <SummaryGrid
            items={[
              [
                "Code status",
                getNestedValue(productionReadiness, ["code_status"], "READY"),
              ],
              [
                "Deployment",
                getNestedValue(
                  productionReadiness,
                  ["deployment_status"],
                  "READY",
                ),
              ],
              [
                "Environment",
                getNestedValue(productionReadiness, ["app_env"], "-"),
              ],
              [
                "Attention items",
                getNestedValue(productionReadiness, ["attention_count"], 0),
              ],
            ]}
          />
          <div className="route-list">
            {asArray(getNestedValue(productionReadiness, ["checks"], [])).map(
              (check) => {
                const status = formatDisplay(
                  getNestedValue(check, ["status"], "READY"),
                );
                return (
                  <div
                    className="route-item"
                    key={formatDisplay(getNestedValue(check, ["code"], ""))}
                  >
                    <div>
                      <div className="route-name">
                        {formatDisplay(
                          getNestedValue(check, ["label"], "Readiness check"),
                        )}
                      </div>
                      <div className="route-path">
                        {formatDisplay(
                          getNestedValue(check, ["recommended_action"], ""),
                        )}
                      </div>
                    </div>
                    <StatusBadge label={status} tone={statusTone(status)} />
                  </div>
                );
              },
            )}
          </div>
        </div>
      </section>

      {actionLoading || actionError || actionResult ? (
        <section className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Action feedback</h2>
              <div className="panel-subtitle">
                One-time secrets and operational results from the last partner
                action.
              </div>
            </div>
            {actionLoading ? (
              <StatusBadge label={actionLoading} tone="info" />
            ) : null}
          </div>
          <div className="panel-body">
            {actionError ? <ErrorPanel error={actionError} /> : null}
            {actionResult ? (
              <PartnerActionResult payload={actionResult} />
            ) : null}
          </div>
        </section>
      ) : null}

      <section className="grid-2">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Client access</h2>
              <div className="panel-subtitle">
                Secrets are hidden after creation.
              </div>
            </div>
          </div>
          <div className="panel-body route-list">
            {clients.length ? (
              clients.map((client) => (
                <div
                  className="route-item"
                  key={formatDisplay(getNestedValue(client, ["client_id"]))}
                >
                  <div>
                    <div className="route-name">
                      {formatDisplay(getNestedValue(client, ["client_name"]))}
                    </div>
                    <div className="route-path">
                      {formatDisplay(getNestedValue(client, ["client_id"]))}
                    </div>
                    <div className="route-path">
                      {formatDisplay(
                        getNestedValue(
                          client,
                          ["scopes"],
                          "No scopes returned",
                        ),
                      )}
                    </div>
                  </div>
                  <StatusBadge
                    label={formatDisplay(getNestedValue(client, ["status"]))}
                    tone={statusTone(
                      formatDisplay(getNestedValue(client, ["status"])),
                    )}
                  />
                </div>
              ))
            ) : (
              <div className="empty-state">
                No active partner clients returned.
              </div>
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Webhook delivery</h2>
              <div className="panel-subtitle">
                Latest delivery health and partner endpoint posture.
              </div>
            </div>
          </div>
          <div className="panel-body route-list">
            {webhooks.length ? (
              webhooks.map((webhook) => (
                <div
                  className="route-item"
                  key={formatDisplay(getNestedValue(webhook, ["webhook_id"]))}
                >
                  <div>
                    <div className="route-name">
                      {formatDisplay(getNestedValue(webhook, ["event_type"]))}
                    </div>
                    <div className="route-path">
                      {formatDisplay(getNestedValue(webhook, ["target_url"]))}
                    </div>
                  </div>
                  <div className="action-button-row">
                    <StatusBadge
                      label={formatDisplay(getNestedValue(webhook, ["status"]))}
                      tone={statusTone(
                        formatDisplay(getNestedValue(webhook, ["status"])),
                      )}
                    />
                    <button
                      className="button secondary"
                      disabled={!canManageWebhooks || actionLoading !== null}
                      onClick={() => rotateSecret(webhook)}
                      type="button"
                    >
                      Rotate secret
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                No webhook subscriptions returned.
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Client onboarding</h2>
            <div className="panel-subtitle">
              {isAdminReadOnly
                ? "Amplifi Admin can inspect partner clients here. Create credentials from the admin command centre when needed."
                : canOnboardClient
                  ? "Create OAuth-style client credentials for this tenant."
                  : "This bearer-token session is scoped to one client and cannot create sibling credentials."}
            </div>
          </div>
          <StatusBadge
            label={
              isAdminReadOnly
                ? "Admin read only"
                : canOnboardClient
                  ? "Tenant scoped"
                  : "Client scoped"
            }
            tone={
              isAdminReadOnly
                ? "info"
                : canOnboardClient
                  ? "success"
                  : "warning"
            }
          />
        </div>
        <div className="panel-body">
          <form
            className="form-row sponsor-picker-row"
            onSubmit={submitCreateClient}
          >
            <label>
              Client name
              <input
                className="input"
                disabled={!canOnboardClient || actionLoading !== null}
                onChange={(event) => setClientName(event.target.value)}
                value={clientName}
              />
            </label>
            <label>
              Scopes
              <input
                className="input"
                disabled={!canOnboardClient || actionLoading !== null}
                onChange={(event) => setClientScopes(event.target.value)}
                value={clientScopes}
              />
            </label>
            <button
              className="button"
              disabled={
                !canOnboardClient ||
                !clientName.trim() ||
                actionLoading !== null
              }
              type="submit"
            >
              Create client
            </button>
          </form>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Secret readiness</h2>
            <div className="panel-subtitle">
              Signing-secret protection and legacy rotation posture for this
              partner scope.
            </div>
          </div>
          <StatusBadge
            label={formatDisplay(
              getNestedValue(secretReadiness, ["status"], "READY"),
            )}
            tone={statusTone(
              formatDisplay(
                getNestedValue(secretReadiness, ["status"], "READY"),
              ),
            )}
          />
        </div>
        <div className="panel-body">
          <SummaryGrid
            items={[
              ["Provider", getNestedValue(secretReadiness, ["provider"], "-")],
              [
                "Protection",
                getNestedValue(secretReadiness, ["protection_mode"], "-"),
              ],
              [
                "Configuration",
                getNestedValue(secretReadiness, ["config_status"], "-"),
              ],
              [
                "KMS key",
                getNestedValue(secretReadiness, ["kms_key_configured"], false),
              ],
              [
                "KMS backend",
                getNestedValue(secretReadiness, ["kms_backend"], "-"),
              ],
              [
                "Protected",
                getNestedValue(secretReadiness, ["protected_subscriptions"], 0),
              ],
              [
                "Legacy",
                getNestedValue(
                  secretReadiness,
                  ["legacy_plaintext_subscriptions"],
                  0,
                ),
              ],
            ]}
          />
          <div className="route-list">
            <div className="route-item">
              <div>
                <div className="route-name">
                  {formatDisplay(
                    getNestedValue(
                      secretReadiness,
                      ["rotation_status"],
                      "READY",
                    ),
                  )}
                </div>
                <div className="route-path">
                  {formatDisplay(
                    getNestedValue(
                      secretReadiness,
                      ["recommended_action"],
                      "Webhook secret storage is ready.",
                    ),
                  )}
                </div>
              </div>
              {legacySecretCount ? (
                <button
                  className="button secondary"
                  disabled={actionLoading !== null}
                  onClick={rotateLegacySecrets}
                  type="button"
                >
                  Rotate legacy
                </button>
              ) : (
                <ShieldCheck size={18} />
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Webhook setup</h2>
            <div className="panel-subtitle">
              {isAdminReadOnly
                ? "Amplifi Admin can inspect delivery posture here. Switch to a partner bearer session for partner-owned webhook setup."
                : canManageWebhooks
                  ? "Create partner-owned endpoints and rotate signing secrets for this client."
                  : "Switch to a bearer-token partner session to create or rotate webhook endpoints."}
            </div>
          </div>
          <StatusBadge
            label={canManageWebhooks ? "Client scoped" : "Read only"}
            tone={canManageWebhooks ? "success" : "warning"}
          />
        </div>
        <div className="panel-body">
          <form
            className="form-row sponsor-picker-row"
            onSubmit={submitCreateWebhook}
          >
            <label>
              Event
              <input
                className="input"
                disabled={!canManageWebhooks || actionLoading !== null}
                onChange={(event) => setEventType(event.target.value)}
                value={eventType}
              />
            </label>
            <label>
              Endpoint
              <input
                className="input"
                disabled={!canManageWebhooks || actionLoading !== null}
                onChange={(event) => setTargetUrl(event.target.value)}
                placeholder="https://partner.example/webhooks"
                value={targetUrl}
              />
            </label>
            <button
              className="button"
              disabled={
                !canManageWebhooks ||
                !eventType.trim() ||
                !targetUrl.trim() ||
                actionLoading !== null
              }
              type="submit"
            >
              Create webhook
            </button>
          </form>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Delivery alerts</h2>
            <div className="panel-subtitle">
              Repeated webhook delivery failures grouped by endpoint and event
              type.
            </div>
          </div>
          <StatusBadge
            label={`${alerts.length} active`}
            tone={alerts.length ? "danger" : "success"}
          />
        </div>
        <div className="panel-body route-list">
          {alerts.length ? (
            alerts.slice(0, 6).map((alert) => {
              const severity = formatDisplay(
                getNestedValue(alert, ["severity"], "NOTICE"),
              );
              return (
                <div
                  className="route-item"
                  key={`${formatDisplay(getNestedValue(alert, ["webhook_id"]))}-${formatDisplay(getNestedValue(alert, ["event_type"]))}`}
                >
                  <div>
                    <div className="route-name">
                      {formatDisplay(getNestedValue(alert, ["event_type"]))}
                    </div>
                    <div className="route-path">
                      {formatDisplay(
                        getNestedValue(
                          alert,
                          ["target_url"],
                          "Endpoint unavailable",
                        ),
                      )}
                    </div>
                    <div className="route-path">
                      {formatDisplay(
                        getNestedValue(alert, ["failed_count"], 0),
                      )}{" "}
                      failed / max attempt{" "}
                      {formatDisplay(
                        getNestedValue(alert, ["max_attempt_count"], 0),
                      )}
                    </div>
                    <div className="route-path">
                      {formatDisplay(
                        getNestedValue(alert, ["last_notified_at"], ""),
                      ) !== "-"
                        ? `Notified ${formatDisplay(getNestedValue(alert, ["last_notification_status"], "SENT"))} at ${formatDisplay(getNestedValue(alert, ["last_notified_at"], "-"))}`
                        : "No notification evidence recorded yet."}
                    </div>
                    <div className="route-path">
                      {formatDisplay(
                        getNestedValue(
                          alert,
                          ["recommended_action"],
                          "Review failed delivery evidence.",
                        ),
                      )}
                    </div>
                  </div>
                  <StatusBadge label={severity} tone={statusTone(severity)} />
                </div>
              );
            })
          ) : (
            <div className="empty-state">
              No repeated webhook failure alerts returned.
            </div>
          )}
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Delivery exceptions</h2>
            <div className="panel-subtitle">
              Failed or cancelled rows that need endpoint correction before the
              next delivery attempt.
            </div>
          </div>
          <div className="action-button-row">
            <StatusBadge
              label={`${exceptions.length} open`}
              tone={exceptions.length ? "warning" : "success"}
            />
            <button
              className="button secondary"
              disabled={!exceptions.length || actionLoading !== null}
              onClick={exportDeadLetters}
              type="button"
            >
              Export CSV
            </button>
          </div>
        </div>
        <div className="panel-body route-list">
          {exceptions.length ? (
            exceptions.slice(0, 8).map((delivery) => {
              const status = formatDisplay(
                getNestedValue(delivery, ["delivery_status"]),
              );
              return (
                <div
                  className="route-item"
                  key={formatDisplay(getNestedValue(delivery, ["delivery_id"]))}
                >
                  <div>
                    <div className="route-name">
                      {formatDisplay(getNestedValue(delivery, ["event_type"]))}
                    </div>
                    <div className="route-path">
                      Attempt{" "}
                      {formatDisplay(
                        getNestedValue(delivery, ["attempt_count"], 0),
                      )}
                    </div>
                    <div className="route-path">
                      {formatDisplay(
                        getNestedValue(
                          delivery,
                          ["last_error"],
                          "No error returned",
                        ),
                      )}
                    </div>
                  </div>
                  <div className="action-button-row">
                    <StatusBadge label={status} tone={statusTone(status)} />
                    <button
                      className="button secondary"
                      disabled={!canManageWebhooks || actionLoading !== null}
                      onClick={() => retryDelivery(delivery)}
                      type="button"
                    >
                      Retry
                    </button>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="empty-state">
              No failed or cancelled webhook deliveries returned.
            </div>
          )}
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Recent delivery evidence</h2>
            <div className="panel-subtitle">
              Failed rows need endpoint correction or platform retry support.
            </div>
          </div>
          <StatusBadge
            label={`${deliveries.length} records`}
            tone={deliveries.length ? "info" : "neutral"}
          />
        </div>
        <div className="panel-body route-list">
          {deliveries.length ? (
            deliveries.slice(0, 8).map((delivery) => {
              const status = formatDisplay(
                getNestedValue(delivery, ["delivery_status"]),
              );
              return (
                <div
                  className="route-item"
                  key={formatDisplay(getNestedValue(delivery, ["delivery_id"]))}
                >
                  <div>
                    <div className="route-name">
                      {formatDisplay(getNestedValue(delivery, ["event_type"]))}
                    </div>
                    <div className="route-path">
                      Attempt{" "}
                      {formatDisplay(
                        getNestedValue(delivery, ["attempt_count"], 0),
                      )}
                    </div>
                    <div className="route-path">
                      {formatDisplay(
                        getNestedValue(delivery, ["last_error"], "No error"),
                      )}
                    </div>
                  </div>
                  <StatusBadge label={status} tone={statusTone(status)} />
                </div>
              );
            })
          ) : (
            <div className="empty-state">
              No recent webhook delivery records returned.
            </div>
          )}
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Guardrails</h2>
            <div className="panel-subtitle">
              What this partner session can and cannot see.
            </div>
          </div>
        </div>
        <div className="panel-body route-list">
          {guardrails.map((guardrail) => (
            <div
              className="route-item"
              key={formatDisplay(getNestedValue(guardrail, ["item"]))}
            >
              <div>
                <div className="route-name">
                  {formatDisplay(getNestedValue(guardrail, ["item"]))}
                </div>
              </div>
              <ShieldCheck size={18} />
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function PartnerActionResult({
  payload,
}: {
  payload: Record<string, unknown>;
}) {
  const client = getNestedValue(payload, ["client"], {});
  const webhook = getNestedValue(payload, ["webhook"], {});
  const exportPayload = getNestedValue(payload, ["export"], {});
  const exportFilename = getNestedValue(exportPayload, ["filename"], "");
  const exportCount = getNestedValue(exportPayload, ["count"], "");
  const rotatedItems = asArray(getNestedValue(payload, ["items"], []));
  const summaryItems = [
    { label: "Action", value: getNestedValue(payload, ["action"], "-") },
    { label: "Status", value: getNestedValue(payload, ["status"], "-") },
    { label: "Client", value: getNestedValue(client, ["client_id"], "-") },
    {
      label: "Client secret",
      value: getNestedValue(client, ["client_secret"], "-"),
    },
    { label: "Webhook", value: getNestedValue(webhook, ["webhook_id"], "-") },
    {
      label: "Signing secret",
      value: getNestedValue(webhook, ["signing_secret"], "-"),
    },
    ...(getNestedValue(payload, ["rotated_count"], "") !== ""
      ? [
          {
            label: "Rotated",
            value: getNestedValue(payload, ["rotated_count"], 0),
          },
        ]
      : []),
    ...(exportFilename
      ? [{ label: "Export file", value: exportFilename }]
      : []),
    ...(exportCount !== ""
      ? [{ label: "Rows exported", value: exportCount }]
      : []),
    { label: "Guardrail", value: getNestedValue(payload, ["guardrail"], "-") },
  ];
  return (
    <div className="action-result">
      <SummaryGrid items={summaryItems} />
      {rotatedItems.length ? (
        <div className="route-list">
          {rotatedItems.slice(0, 8).map((item) => (
            <div
              className="route-item"
              key={formatDisplay(getNestedValue(item, ["webhook_id"]))}
            >
              <div>
                <div className="route-name">
                  {formatDisplay(
                    getNestedValue(item, ["event_type"], "Webhook"),
                  )}
                </div>
                <div className="route-path">
                  {formatDisplay(getNestedValue(item, ["webhook_id"], "-"))}
                </div>
                <div className="route-path mono">
                  {formatDisplay(getNestedValue(item, ["signing_secret"], "-"))}
                </div>
              </div>
              <StatusBadge label="One-time" tone="warning" />
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function csvList(value: string): string[] {
  return value
    .replace(/,/g, " ")
    .split(/\s+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function downloadCsv(filename: string, csv: string) {
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
