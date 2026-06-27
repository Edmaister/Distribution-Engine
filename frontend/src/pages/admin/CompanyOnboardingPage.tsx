import {
  Building2,
  CheckCircle2,
  CircleDashed,
  KeyRound,
  Link as LinkIcon,
  ShieldCheck,
  Users,
} from "lucide-react";
import { useId, useMemo, useState } from "react";
import { Link } from "react-router-dom";
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
    label: "Operator monitoring",
    path: "/admin",
    copy: "Return to read-only platform diagnostics while account lifecycle APIs remain future work.",
  },
];

export function CompanyOnboardingPage() {
  const [form, setForm] = useState<FormState>(initialState);
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

  function updateField(field: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

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
        <SummaryItem label="Create API" value="Not wired" />
        <SummaryItem label="Internal tenant_code" value="Hidden" />
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
              <button className="button" disabled type="button">
                Create account later
              </button>
              <span className={requiredComplete ? "muted" : "danger-text"}>
                {requiredComplete
                  ? "Required shell fields are captured locally."
                  : "Complete required shell fields before a future create flow."}
              </span>
            </div>
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
            title="tenant_code stays internal"
            copy="Do not expose tenant_code as the primary product identifier in this company setup journey."
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
