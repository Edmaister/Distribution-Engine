import {
  CheckCircle2,
  CircleDashed,
  KeyRound,
  Link as LinkIcon,
  RadioTower,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useId, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  getAdminOnboardingState,
  type AdminOnboardingStateResponse,
} from "../../api/endpoints/adminOnboarding";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";

type FormState = {
  organisationRef: string;
  externalTenantRef: string;
  integrationOwner: string;
  apiEnvironmentIntent: string;
  callbackUrl: string;
  authMethodIntent: string;
  ipAllowlistNotes: string;
  payloadFormatVersion: string;
  goLiveReadinessStatus: string;
};

type EventCategory = {
  id: string;
  label: string;
  copy: string;
  examples: string[];
};

type ReadinessStep = {
  label: string;
  copy: string;
  ready: boolean;
};

const initialState: FormState = {
  organisationRef: "",
  externalTenantRef: "",
  integrationOwner: "",
  apiEnvironmentIntent: "Sandbox only",
  callbackUrl: "",
  authMethodIntent: "OAuth client credentials later",
  ipAllowlistNotes: "",
  payloadFormatVersion: "DLaaS envelope v1 preview",
  goLiveReadinessStatus: "Draft setup",
};

const eventCategories: EventCategory[] = [
  {
    id: "campaign",
    label: "Campaign events",
    copy: "Campaign and opportunity lifecycle events such as published or closed.",
    examples: ["CAMPAIGN_PUBLISHED", "CAMPAIGN_CLOSED"],
  },
  {
    id: "outcome",
    label: "Outcome events",
    copy: "Outcome completion or blocker events using safe external evidence.",
    examples: ["OUTCOME_COMPLETED", "OUTCOME_BLOCKED"],
  },
  {
    id: "reward",
    label: "Reward events",
    copy: "Reward obligation state changes without raw fulfilment/provider details.",
    examples: ["REWARD_APPLIED", "REWARD_FULFILLED", "REWARD_FAILED"],
  },
  {
    id: "funding",
    label: "Funding events",
    copy: "Funding reservation and settlement evidence without money movement.",
    examples: ["FUNDING_RESERVED", "FUNDING_SETTLED", "FUNDING_REVERSED"],
  },
  {
    id: "fulfilment",
    label: "Fulfilment events",
    copy: "Safe fulfilment status events for pending, processing, success, failure, or duplicate-skip evidence.",
    examples: [
      "FULFILMENT_PENDING",
      "FULFILMENT_SUCCEEDED",
      "FULFILMENT_FAILED",
    ],
  },
  {
    id: "settlement",
    label: "Settlement events",
    copy: "Safe settlement state events without ledger internals or exception details.",
    examples: [
      "SETTLEMENT_PENDING",
      "SETTLEMENT_SETTLED",
      "SETTLEMENT_DISPUTED",
    ],
  },
  {
    id: "integration",
    label: "Integration events",
    copy: "Webhook delivery and subscription health events without signing material.",
    examples: [
      "INTEGRATION_WEBHOOK_DELIVERY_FAILED",
      "INTEGRATION_WEBHOOK_SUBSCRIPTION_CHANGED",
    ],
  },
];

const journeyLinks = [
  {
    label: "Company onboarding",
    path: "/admin/onboarding/company",
    copy: "Confirm organisation and external tenant references.",
  },
  {
    label: "Producer / sponsor onboarding",
    path: "/admin/onboarding/producer-sponsor",
    copy: "Confirm producer or sponsor ownership before integration setup.",
  },
  {
    label: "Distributor onboarding",
    path: "/admin/onboarding/distributor",
    copy: "Confirm partner or distributor context before webhook readiness.",
  },
  {
    label: "User & role setup",
    path: "/admin/onboarding/members-roles",
    copy: "Draft integration owner and admin role intent.",
  },
  {
    label: "Campaign / opportunity setup",
    path: "/admin/onboarding/campaign-opportunity",
    copy: "Connect campaign setup intent to event categories and payload preview.",
  },
];

const readOnlyScope = {
  external_tenant_ref: "demo-platform-operator",
  organisation_ref: "demo-organisation",
};

type LoadState = "loading" | "success" | "fallback";

export function WebhookApiSetupPage() {
  const [form, setForm] = useState<FormState>(initialState);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([
    "campaign",
    "outcome",
  ]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [readOnlyState, setReadOnlyState] =
    useState<AdminOnboardingStateResponse | null>(null);

  const requiredComplete = Boolean(
    form.organisationRef.trim() &&
    form.externalTenantRef.trim() &&
    form.integrationOwner.trim() &&
    form.apiEnvironmentIntent.trim() &&
    form.callbackUrl.trim() &&
    selectedCategories.length > 0 &&
    form.authMethodIntent.trim() &&
    form.ipAllowlistNotes.trim() &&
    form.payloadFormatVersion.trim() &&
    form.goLiveReadinessStatus.trim(),
  );

  const readinessSteps = useMemo<ReadinessStep[]>(
    () => [
      {
        label: "External tenant scope",
        copy: "organisation_ref and external_tenant_ref are captured without exposing the internal tenant identifier.",
        ready: Boolean(
          form.organisationRef.trim() && form.externalTenantRef.trim(),
        ),
      },
      {
        label: "Integration owner",
        copy: "Owner/contact and API environment intent are drafted locally.",
        ready: Boolean(
          form.integrationOwner.trim() && form.apiEnvironmentIntent.trim(),
        ),
      },
      {
        label: "Callback placeholder",
        copy: "Callback URL and IP allowlist notes are recorded as intent only; no validation or registration occurs.",
        ready: Boolean(form.callbackUrl.trim() && form.ipAllowlistNotes.trim()),
      },
      {
        label: "Webhook catalog selection",
        copy: "Selected event categories and payload format are ready for a future subscription flow.",
        ready: Boolean(
          selectedCategories.length > 0 && form.payloadFormatVersion.trim(),
        ),
      },
      {
        label: "Security method intent",
        copy: "Authentication method and go-live readiness status are documented without creating credentials.",
        ready: Boolean(
          form.authMethodIntent.trim() && form.goLiveReadinessStatus.trim(),
        ),
      },
      {
        label: "Backend credential lifecycle",
        copy: "Blocked until safe credential, secret, subscription, signing, delivery, and audit APIs are explicitly wired.",
        ready: false,
      },
    ],
    [form, selectedCategories.length],
  );

  const readyCount = readinessSteps.filter((step) => step.ready).length;
  const selectedCategoryLabels = eventCategories
    .filter((category) => selectedCategories.includes(category.id))
    .map((category) => category.label);
  const webhookCategory = readOnlyState?.readiness.categories.find(
    (category) => {
      const categoryKey = category.category.toUpperCase();
      return categoryKey.includes("WEBHOOK") || categoryKey.includes("API");
    },
  );

  function updateField(field: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function toggleCategory(categoryId: string) {
    setSelectedCategories((current) =>
      current.includes(categoryId)
        ? current.filter((value) => value !== categoryId)
        : [...current, categoryId],
    );
  }

  useEffect(() => {
    let cancelled = false;

    getAdminOnboardingState(readOnlyScope)
      .then((response) => {
        if (cancelled) {
          return;
        }
        setReadOnlyState(response);
        setLoadState("success");
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        setReadOnlyState(null);
        setLoadState("fallback");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">DLaaS onboarding - Integrations</div>
          <h1 className="page-title">Webhook & API credential setup</h1>
          <p className="page-copy">
            Draft integration setup intent for external tenant references, API
            environment, callback URL, webhook event categories, payload
            preview, and security guardrails without creating credentials.
          </p>
        </div>
        <StatusBadge label="Shell only" tone="warning" />
      </section>

      <section className="grid-3">
        <SummaryItem label="Readiness" value={`${readyCount}/6`} />
        <SummaryItem label="Credential actions" value="Disabled" />
        <SummaryItem label="Secrets displayed" value="Never" />
        <SummaryItem
          label="Read-only state"
          value={loadState === "success" ? "Available" : "Fallback"}
        />
      </section>

      <section className="banner warning" role="note">
        <ShieldCheck size={18} />
        <div>
          <strong>
            No API keys, webhook subscriptions, signing material, callback
            registrations, or deliveries are created from this page.
          </strong>
          <div className="table-subtext">
            This shell uses local form state only. It does not create, rotate,
            reveal, store, validate, subscribe, sign, queue, retry, deliver, or
            persist credentials or webhook records.
          </div>
        </div>
      </section>

      <section className="panel" aria-labelledby="read-only-state-heading">
        <div className="panel-header">
          <div>
            <h2 className="panel-title" id="read-only-state-heading">
              Read-only platform state
            </h2>
            <div className="panel-subtitle">
              Uses external integration references to hydrate safe webhook/API
              readiness when available.
            </div>
          </div>
          <StatusBadge
            label={
              loadState === "loading"
                ? "Loading"
                : loadState === "success"
                  ? "Read-only"
                  : "Demo fallback"
            }
            tone={loadState === "success" ? "success" : "info"}
          />
        </div>
        <div className="panel-body">
          {loadState === "loading" ? (
            <div className="banner info" role="status">
              <CircleDashed size={18} />
              <div>
                <strong>Loading read-only webhook and API readiness.</strong>
                <div className="table-subtext">
                  This checks the admin onboarding state endpoint without
                  creating credentials, subscriptions, deliveries, retries, or
                  go-live actions.
                </div>
              </div>
            </div>
          ) : loadState === "fallback" ? (
            <div className="banner warning" role="status">
              <ShieldCheck size={18} />
              <div>
                <strong>Using local webhook/API setup fallback.</strong>
                <div className="table-subtext">
                  The read-only onboarding state endpoint is unavailable, so
                  this page keeps local shell state only and all credential and
                  webhook actions remain disabled.
                </div>
              </div>
            </div>
          ) : (
            <div className="grid-2">
              <div className="summary-grid">
                <SummaryItem
                  label="External tenant ref"
                  value={readOnlyScope.external_tenant_ref}
                />
                <SummaryItem
                  label="Organisation ref"
                  value={readOnlyScope.organisation_ref}
                />
              </div>
              <div className="route-list">
                <div className="route-item">
                  <div>
                    <div className="route-name">
                      {webhookCategory?.display_label ?? "Webhook / API setup"}
                    </div>
                    <div className="route-path">
                      {webhookCategory?.evidence_summary ??
                        "Read-only webhook/API evidence is not available yet."}
                    </div>
                    {webhookCategory?.blockers[0] ? (
                      <div className="table-subtext">
                        {webhookCategory.blockers[0]}
                      </div>
                    ) : null}
                    {webhookCategory?.next_actions[0] ? (
                      <div className="table-subtext">
                        {webhookCategory.next_actions[0]}
                      </div>
                    ) : null}
                  </div>
                  <StatusBadge
                    label={
                      webhookCategory?.safe_display_status?.label ??
                      webhookCategory?.status ??
                      "Missing evidence"
                    }
                    tone={
                      webhookCategory?.status === "READY" ? "success" : "info"
                    }
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      <section className="grid-2">
        <form className="panel" aria-label="Webhook and API setup form">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Integration setup intent</h2>
              <div className="panel-subtitle">
                Capture safe placeholders before credential lifecycle APIs
                exist.
              </div>
            </div>
            <KeyRound size={18} />
          </div>
          <div className="panel-body">
            <div className="grid-2">
              <TextField
                label="organisation_ref"
                value={form.organisationRef}
                onChange={(value) => updateField("organisationRef", value)}
                placeholder="org-acme"
                required
              />
              <TextField
                label="external_tenant_ref"
                value={form.externalTenantRef}
                onChange={(value) => updateField("externalTenantRef", value)}
                placeholder="acme-distribution"
                required
              />
              <TextField
                label="Integration owner / contact"
                value={form.integrationOwner}
                onChange={(value) => updateField("integrationOwner", value)}
                placeholder="integration-owner@example.test"
                required
              />
              <SelectField
                label="API environment intention"
                value={form.apiEnvironmentIntent}
                onChange={(value) => updateField("apiEnvironmentIntent", value)}
                options={[
                  "Sandbox only",
                  "Sandbox then live review",
                  "Live readiness later",
                ]}
              />
              <TextField
                label="Callback URL placeholder"
                value={form.callbackUrl}
                onChange={(value) => updateField("callbackUrl", value)}
                placeholder="https://hooks.example.test/dlaas/events"
                required
              />
              <SelectField
                label="Intended authentication method"
                value={form.authMethodIntent}
                onChange={(value) => updateField("authMethodIntent", value)}
                options={[
                  "OAuth client credentials later",
                  "Signed webhook secret later",
                  "Partner API key later",
                  "Mutual TLS later",
                  "Not selected",
                ]}
              />
              <TextField
                label="IP allowlist notes"
                value={form.ipAllowlistNotes}
                onChange={(value) => updateField("ipAllowlistNotes", value)}
                placeholder="Partner network ranges to confirm later"
                required
              />
              <SelectField
                label="Payload format / version"
                value={form.payloadFormatVersion}
                onChange={(value) => updateField("payloadFormatVersion", value)}
                options={[
                  "DLaaS envelope v1 preview",
                  "Compact event preview",
                  "Safe diagnostics preview",
                ]}
              />
              <SelectField
                label="Go-live readiness status"
                value={form.goLiveReadinessStatus}
                onChange={(value) =>
                  updateField("goLiveReadinessStatus", value)
                }
                options={[
                  "Draft setup",
                  "Ready for future credential API",
                  "Blocked by security review",
                  "Blocked by callback validation",
                  "Hold for partner testing",
                ]}
              />
            </div>

            <fieldset
              className="panel-body"
              aria-label="Webhook event categories"
            >
              <legend className="panel-title">Webhook event categories</legend>
              <div className="route-list">
                {eventCategories.map((category) => (
                  <label className="route-item" key={category.id}>
                    <div>
                      <div className="route-name">{category.label}</div>
                      <div className="route-path">
                        {category.copy} Examples: {category.examples.join(", ")}
                        .
                      </div>
                    </div>
                    <input
                      checked={selectedCategories.includes(category.id)}
                      onChange={() => toggleCategory(category.id)}
                      type="checkbox"
                    />
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="action-button-row">
              <button className="button" disabled type="button">
                Create API key later
              </button>
              <button className="button secondary" disabled type="button">
                Rotate key later
              </button>
              <button className="button secondary" disabled type="button">
                Create secret later
              </button>
              <button className="button secondary" disabled type="button">
                Send test webhook later
              </button>
              <button className="button secondary" disabled type="button">
                Subscribe later
              </button>
              <button className="button secondary" disabled type="button">
                Register callback later
              </button>
              <button className="button secondary" disabled type="button">
                Sign payload later
              </button>
              <button className="button secondary" disabled type="button">
                Queue delivery later
              </button>
              <button className="button secondary" disabled type="button">
                Retry delivery later
              </button>
              <button className="button secondary" disabled type="button">
                Activate live credentials later
              </button>
              <button className="button secondary" disabled type="button">
                Move money later
              </button>
              <span className={requiredComplete ? "muted" : "danger-text"}>
                {requiredComplete
                  ? "Required integration setup fields are captured locally."
                  : "Complete integration setup fields before future credential APIs are considered."}
              </span>
            </div>
          </div>
        </form>

        <section className="panel" aria-labelledby="webhook-readiness-heading">
          <div className="panel-header">
            <div>
              <h2 className="panel-title" id="webhook-readiness-heading">
                Readiness review
              </h2>
              <div className="panel-subtitle">
                Local readiness only; backend credential lifecycle remains
                unavailable.
              </div>
            </div>
            <StatusBadge
              label={requiredComplete ? "Draft complete" : "Draft"}
              tone={requiredComplete ? "info" : "neutral"}
            />
          </div>
          <div className="panel-body route-list">
            {readinessSteps.map((step) => (
              <div className="route-item" key={step.label}>
                <div>
                  <div className="route-name">{step.label}</div>
                  <div className="route-path">{step.copy}</div>
                </div>
                <StatusBadge
                  label={step.ready ? "Ready" : "Pending"}
                  tone={step.ready ? "success" : "warning"}
                />
              </div>
            ))}
          </div>
        </section>
      </section>

      <section className="grid-2">
        <section className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Non-delivering payload preview</h2>
              <div className="panel-subtitle">
                Safe envelope shape only; no signing, queueing, or delivery.
              </div>
            </div>
            <RadioTower size={18} />
          </div>
          <div className="panel-body route-list">
            <div className="route-item">
              <div>
                <div className="route-name">Tenant reference</div>
                <div className="route-path">
                  {form.externalTenantRef.trim() ||
                    "external_tenant_ref placeholder"}
                </div>
              </div>
              <StatusBadge label="External" tone="info" />
            </div>
            <div className="route-item">
              <div>
                <div className="route-name">Selected categories</div>
                <div className="route-path">
                  {selectedCategoryLabels.length
                    ? selectedCategoryLabels.join(", ")
                    : "No event category selected"}
                </div>
              </div>
              <StatusBadge label="Catalog" tone="info" />
            </div>
            <div className="route-item">
              <div>
                <div className="route-name">Payload format</div>
                <div className="route-path">{form.payloadFormatVersion}</div>
              </div>
              <StatusBadge label="Preview" tone="neutral" />
            </div>
            <div className="route-item">
              <div>
                <div className="route-name">Credential material</div>
                <div className="route-path">
                  Never generated, stored, displayed, signed, or delivered in
                  this shell.
                </div>
              </div>
              <StatusBadge label="Redacted" tone="warning" />
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Safe integration boundary</h2>
              <div className="panel-subtitle">
                TASK-075 stops at visible setup intent and disabled actions.
              </div>
            </div>
            <ShieldCheck size={18} />
          </div>
          <div className="panel-body capability-grid">
            <BoundaryCard
              icon={LinkIcon}
              title="External references only"
              copy="Use external_tenant_ref and organisation_ref for setup; the internal tenant identifier stays hidden."
            />
            <BoundaryCard
              icon={KeyRound}
              title="Secrets stay unavailable"
              copy="No API key, token, signing material, client secret, certificate, or credential value is created or displayed."
            />
            <BoundaryCard
              icon={RadioTower}
              title="No webhook side effects"
              copy="No callback registration, URL validation, subscription write, signing, queueing, delivery, retry, or replay is wired."
            />
          </div>
        </section>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Onboarding journey links</h2>
            <div className="panel-subtitle">
              Continue the product journey without live credential changes.
            </div>
          </div>
          <CircleDashed size={18} />
        </div>
        <div className="panel-body route-list">
          {journeyLinks.map((item) => (
            <Link className="route-item" key={item.label} to={item.path}>
              <div>
                <div className="route-name">{item.label}</div>
                <div className="route-path">{item.copy}</div>
              </div>
              <CheckCircle2 size={18} />
            </Link>
          ))}
        </div>
      </section>
    </>
  );
}

function TextField({
  label,
  value,
  onChange,
  placeholder,
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  required?: boolean;
}) {
  const id = useId();

  return (
    <div className="field">
      <label htmlFor={id}>
        {label}
        {required ? " *" : ""}
      </label>
      <input
        className="input"
        id={id}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        required={required}
        type="text"
        value={value}
      />
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  const id = useId();

  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select
        className="input"
        id={id}
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        {options.map((option) => (
          <option key={option}>{option}</option>
        ))}
      </select>
    </div>
  );
}

function BoundaryCard({
  icon: Icon,
  title,
  copy,
}: {
  icon: typeof ShieldCheck;
  title: string;
  copy: string;
}) {
  return (
    <article className="capability-card">
      <div className="capability-icon">
        <Icon size={18} />
      </div>
      <div>
        <div className="capability-title">{title}</div>
        <div className="capability-copy">{copy}</div>
      </div>
      <StatusBadge label="Guardrail" tone="info" />
    </article>
  );
}
