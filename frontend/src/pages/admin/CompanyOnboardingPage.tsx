import {
  Building2,
  CheckCircle2,
  CircleDashed,
  KeyRound,
  Link as LinkIcon,
  ShieldCheck,
  Users,
} from "lucide-react";
import { useEffect, useId, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  getAdminOnboardingState,
  saveAdminOnboardingDraft,
  type AdminOnboardingDraftSaveResponse,
  type AdminOnboardingStateResponse,
} from "../../api/endpoints/adminOnboarding";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";

type FormState = {
  organisationName: string;
  externalTenantRef: string;
  organisationRef: string;
  country: string;
  organisationType: string;
  industry: string;
  adminContact: string;
  intendedRole: string;
};

type ReadinessStep = {
  label: string;
  copy: string;
  ready: boolean;
};

const initialState: FormState = {
  organisationName: "",
  externalTenantRef: "",
  organisationRef: "",
  country: "",
  organisationType: "Producer / sponsor",
  industry: "",
  adminContact: "",
  intendedRole: "Company admin",
};

const futureJourneyLinks = [
  {
    label: "Producer / sponsor onboarding",
    path: "/admin/onboarding/producer-sponsor",
    copy: "Continue with sponsor profile, funding-readiness placeholders, and campaign ownership context.",
  },
  {
    label: "Distributor onboarding",
    path: "/admin/onboarding/distributor",
    copy: "Invite distributors or partner admins into the demand side once the company shell is complete.",
  },
  {
    label: "User & role setup",
    path: "/admin/onboarding/members-roles",
    copy: "Draft invite, membership, and role-family intent without creating users or roles.",
  },
  {
    label: "Campaign / opportunity setup",
    path: "/admin/onboarding/campaign-opportunity",
    copy: "Draft campaign, opportunity, readiness, and go-live intent without launching anything.",
  },
  {
    label: "Webhook & API setup",
    path: "/admin/onboarding/webhook-api",
    copy: "Draft credential, callback, event catalog, and payload preview intent without creating secrets.",
  },
  {
    label: "Operator monitoring",
    path: "/admin",
    copy: "Return to read-only platform diagnostics while account lifecycle APIs remain future work.",
  },
];

const readOnlyScope = {
  external_tenant_ref: "demo-platform-operator",
  organisation_ref: "demo-organisation",
};

type LoadState = "loading" | "success" | "fallback";
type DraftSaveState = "idle" | "saving" | "saved" | "error";

export function CompanyOnboardingPage() {
  const [form, setForm] = useState<FormState>(initialState);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [readOnlyState, setReadOnlyState] =
    useState<AdminOnboardingStateResponse | null>(null);
  const [draftSaveState, setDraftSaveState] =
    useState<DraftSaveState>("idle");
  const [draftSaveResponse, setDraftSaveResponse] =
    useState<AdminOnboardingDraftSaveResponse | null>(null);
  const [draftSaveError, setDraftSaveError] = useState<string | null>(null);
  const requiredComplete = Boolean(
    form.organisationName.trim() &&
    form.externalTenantRef.trim() &&
    form.organisationRef.trim() &&
    form.country.trim() &&
    form.adminContact.trim(),
  );

  const readinessSteps = useMemo<ReadinessStep[]>(
    () => [
      {
        label: "Company profile",
        copy: "Organisation name, country, type, and industry are captured locally for the onboarding shell.",
        ready: Boolean(
          form.organisationName.trim() &&
          form.country.trim() &&
          form.industry.trim(),
        ),
      },
      {
        label: "External identifiers",
        copy: "`external_tenant_ref` and `organisation_ref` stay outside the internal tenant partition.",
        ready: Boolean(
          form.externalTenantRef.trim() && form.organisationRef.trim(),
        ),
      },
      {
        label: "Admin contact",
        copy: "Primary admin contact and intended role are ready for a future membership invite flow.",
        ready: Boolean(form.adminContact.trim() && form.intendedRole.trim()),
      },
      {
        label: "Backend account lifecycle",
        copy: "Blocked until additive account, membership, and external-reference APIs are implemented.",
        ready: false,
      },
    ],
    [form],
  );

  const readyCount = readinessSteps.filter((step) => step.ready).length;
  const organisationCategory = readOnlyState?.readiness.categories.find(
    (category) => category.category.toUpperCase().includes("ORGANISATION"),
  );
  const draftSaveReady = Boolean(
    form.externalTenantRef.trim() && form.organisationRef.trim(),
  );
  const draftIdempotencyKey = useMemo(
    () =>
      [
        "company-onboarding-draft",
        form.externalTenantRef.trim() || "missing-external-ref",
        form.organisationRef.trim() || "missing-organisation-ref",
        form.organisationName.trim() || "unnamed-organisation",
        form.adminContact.trim() || "missing-admin-contact",
      ].join(":"),
    [form],
  );

  function updateField(field: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSaveDraft() {
    if (!draftSaveReady || draftSaveState === "saving") {
      return;
    }

    setDraftSaveState("saving");
    setDraftSaveError(null);
    setDraftSaveResponse(null);

    try {
      const response = await saveAdminOnboardingDraft({
        external_tenant_ref: form.externalTenantRef,
        organisation_ref: form.organisationRef,
        idempotency_key: draftIdempotencyKey,
        correlation_id: "company-onboarding-shell",
        sections: {
          company: {
            organisation_name: form.organisationName,
            external_tenant_ref: form.externalTenantRef,
            organisation_ref: form.organisationRef,
            country: form.country,
            organisation_type: form.organisationType,
            industry: form.industry,
            admin_contact: form.adminContact,
            intended_role: form.intendedRole,
          },
        },
      });
      setDraftSaveResponse(response);
      setDraftSaveState("saved");
    } catch (error) {
      const status =
        typeof error === "object" && error && "status" in error
          ? Number((error as { status?: number }).status)
          : null;
      setDraftSaveError(
        status === 409
          ? "A matching draft already exists or the idempotency key needs review. No live action was taken."
          : "Draft save is unavailable, so the page is keeping local shell state only. No live action was taken.",
      );
      setDraftSaveState("error");
    }
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
          <div className="page-kicker">DLaaS onboarding - Company setup</div>
          <h1 className="page-title">Company & organisation onboarding</h1>
          <p className="page-copy">
            Capture the first company setup pass using external SaaS-facing
            identifiers while account creation, memberships, and tenant-link
            APIs remain future implementation work.
          </p>
        </div>
        <StatusBadge label="Shell only" tone="warning" />
      </section>

      <section className="grid-3">
        <SummaryItem label="Readiness" value={`${readyCount}/4`} />
        <SummaryItem
          label="Read-only state"
          value={loadState === "success" ? "Available" : "Fallback"}
        />
        <SummaryItem label="Internal tenant identifier" value="Hidden" />
      </section>

      <section className="panel" aria-labelledby="read-only-state-heading">
        <div className="panel-header">
          <div>
            <h2 className="panel-title" id="read-only-state-heading">
              Read-only platform state
            </h2>
            <div className="panel-subtitle">
              Uses external references to hydrate safe onboarding context when
              available.
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
                <strong>Loading read-only company readiness.</strong>
                <div className="table-subtext">
                  The shell is checking external references without creating
                  account records.
                </div>
              </div>
            </div>
          ) : loadState === "fallback" ? (
            <div className="banner warning" role="status">
              <ShieldCheck size={18} />
              <div>
                <strong>Using local company setup fallback.</strong>
                <div className="table-subtext">
                  The read-only onboarding state endpoint is unavailable, so
                  this page keeps local shell state only.
                </div>
              </div>
            </div>
          ) : (
            <>
              <div className="grid-3">
                <SummaryItem
                  label="Overall readiness"
                  value={
                    readOnlyState?.readiness.overall_status ?? "Unavailable"
                  }
                />
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
                      {organisationCategory?.display_label ??
                        "Organisation profile"}
                    </div>
                    <div className="route-path">
                      {organisationCategory?.evidence_summary ??
                        "Read-only organisation evidence is not available yet."}
                    </div>
                    {organisationCategory?.blockers[0] ? (
                      <div className="table-subtext">
                        {organisationCategory.blockers[0]}
                      </div>
                    ) : null}
                    {organisationCategory?.next_actions[0] ? (
                      <div className="table-subtext">
                        {organisationCategory.next_actions[0]}
                      </div>
                    ) : null}
                  </div>
                  <StatusBadge
                    label={
                      organisationCategory?.safe_display_status?.label ??
                      organisationCategory?.status ??
                      "Missing evidence"
                    }
                    tone={
                      organisationCategory?.status === "READY"
                        ? "success"
                        : "info"
                    }
                  />
                </div>
              </div>
            </>
          )}
        </div>
      </section>

      <section className="banner warning" role="note">
        <ShieldCheck size={18} />
        <div>
          <strong>No records are created from this page.</strong>
          <div className="table-subtext">
            This shell uses local form state only. It does not call account,
            tenant, membership, billing, or external-reference APIs.
          </div>
        </div>
      </section>

      <section className="grid-2">
        <form className="panel" aria-label="Company onboarding shell">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Company profile</h2>
              <div className="panel-subtitle">
                External identifiers are captured before any internal tenant
                mapping.
              </div>
            </div>
            <Building2 size={18} />
          </div>
          <div className="panel-body">
            <div className="grid-2">
              <TextField
                label="Organisation name"
                value={form.organisationName}
                onChange={(value) => updateField("organisationName", value)}
                placeholder="Acme Distribution Ltd"
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
                label="organisation_ref"
                value={form.organisationRef}
                onChange={(value) => updateField("organisationRef", value)}
                placeholder="org-acme"
                required
              />
              <TextField
                label="Country"
                value={form.country}
                onChange={(value) => updateField("country", value)}
                placeholder="South Africa"
                required
              />
              <SelectField
                label="Organisation type"
                value={form.organisationType}
                onChange={(value) => updateField("organisationType", value)}
                options={[
                  "Producer / sponsor",
                  "Distributor",
                  "Partner",
                  "Mixed account",
                  "Platform operator",
                ]}
              />
              <TextField
                label="Industry"
                value={form.industry}
                onChange={(value) => updateField("industry", value)}
                placeholder="Banking, insurance, retail"
              />
              <TextField
                label="Admin contact"
                value={form.adminContact}
                onChange={(value) => updateField("adminContact", value)}
                placeholder="ops@example.test"
                required
              />
              <SelectField
                label="Intended role"
                value={form.intendedRole}
                onChange={(value) => updateField("intendedRole", value)}
                options={[
                  "Company admin",
                  "Producer admin",
                  "Distributor admin",
                  "Partner admin",
                  "Platform operator",
                ]}
              />
            </div>
            <div className="action-button-row">
              <button
                className="button secondary"
                disabled={!draftSaveReady || draftSaveState === "saving"}
                onClick={handleSaveDraft}
                type="button"
              >
                {draftSaveState === "saving" ? "Saving draft" : "Save draft"}
              </button>
              <button className="button" disabled type="button">
                Create account later
              </button>
              <span className={requiredComplete ? "muted" : "danger-text"}>
                {requiredComplete
                  ? "Required shell fields are captured locally."
                  : "Complete required shell fields before a future create flow."}
              </span>
            </div>
            <div className="table-subtext">
              Draft save stores onboarding intent only. It does not create
              accounts, invite users, create credentials, publish campaigns,
              deliver webhooks, activate go-live, or move money.
            </div>
            {draftSaveState === "saved" && draftSaveResponse ? (
              <div className="banner success" role="status">
                <CheckCircle2 size={18} />
                <div>
                  <strong>Draft saved for review.</strong>
                  <div className="table-subtext">
                    {draftSaveResponse.draft_ref} -{" "}
                    {draftSaveResponse.draft_status} -{" "}
                    {draftSaveResponse.idempotency_status}
                  </div>
                  {draftSaveResponse.validation_summary ? (
                    <div className="table-subtext">
                      Validation:{" "}
                      {draftSaveResponse.validation_summary.status}; blockers:{" "}
                      {draftSaveResponse.validation_summary.blocker_count};
                      missing evidence:{" "}
                      {
                        draftSaveResponse.validation_summary
                          .missing_evidence_count
                      }
                    </div>
                  ) : null}
                  {draftSaveResponse.next_actions?.[0] ? (
                    <div className="table-subtext">
                      {draftSaveResponse.next_actions[0]}
                    </div>
                  ) : null}
                </div>
              </div>
            ) : null}
            {draftSaveState === "error" && draftSaveError ? (
              <div className="banner warning" role="status">
                <ShieldCheck size={18} />
                <div>
                  <strong>Draft save fallback.</strong>
                  <div className="table-subtext">{draftSaveError}</div>
                </div>
              </div>
            ) : null}
          </div>
        </form>

        <section className="panel" aria-labelledby="readiness-heading">
          <div className="panel-header">
            <div>
              <h2 className="panel-title" id="readiness-heading">
                Setup readiness
              </h2>
              <div className="panel-subtitle">
                Visible guardrails before producer, distributor, and role setup.
              </div>
            </div>
            <StatusBadge
              label={requiredComplete ? "Profile drafted" : "Draft"}
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

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Identifier boundary</h2>
            <div className="panel-subtitle">
              This shell follows the TASK-048 tenant identifier decision.
            </div>
          </div>
          <KeyRound size={18} />
        </div>
        <div className="panel-body capability-grid">
          <BoundaryCard
            icon={LinkIcon}
            title="External first"
            copy="Use external_tenant_ref and organisation_ref in onboarding and future public/SaaS-facing flows."
          />
          <BoundaryCard
            icon={ShieldCheck}
            title="Internal tenant identifier stays hidden"
            copy="Use external references as the visible product identifiers in this company setup journey."
          />
          <BoundaryCard
            icon={Users}
            title="Membership comes later"
            copy="User invites, seats, role assignment, and tenant-link enforcement are TASK-073 and backend follow-up work."
          />
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Next onboarding steps</h2>
            <div className="panel-subtitle">
              Links point to existing workspaces until the next shells are
              built.
            </div>
          </div>
          <CircleDashed size={18} />
        </div>
        <div className="panel-body route-list">
          {futureJourneyLinks.map((item) => (
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
  icon: typeof Building2;
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
