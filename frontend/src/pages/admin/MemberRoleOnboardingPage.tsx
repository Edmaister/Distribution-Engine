import {
  CheckCircle2,
  CircleDashed,
  KeyRound,
  Link as LinkIcon,
  LockKeyhole,
  ShieldCheck,
  UserPlus,
  Users,
} from "lucide-react";
import { useId, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";

type FormState = {
  organisationRef: string;
  externalTenantRef: string;
  userEmail: string;
  displayName: string;
  roleFamily: string;
  participantType: string;
  accessScope: string;
  inviteStatus: string;
};

type ReadinessStep = {
  label: string;
  copy: string;
  ready: boolean;
};

const initialState: FormState = {
  organisationRef: "",
  externalTenantRef: "",
  userEmail: "",
  displayName: "",
  roleFamily: "Company admin",
  participantType: "Producer / sponsor",
  accessScope: "Organisation setup only",
  inviteStatus: "Draft invite",
};

const nextJourneyLinks = [
  {
    label: "Company onboarding",
    path: "/admin/onboarding/company",
    copy: "Return to the organisation shell and shared external tenant boundary.",
  },
  {
    label: "Producer / sponsor onboarding",
    path: "/admin/onboarding/producer-sponsor",
    copy: "Review producer/sponsor setup before role-family assignment.",
  },
  {
    label: "Distributor onboarding",
    path: "/admin/onboarding/distributor",
    copy: "Review distributor setup before distributor/partner admin invite intent.",
  },
  {
    label: "Campaign / opportunity setup",
    path: "/admin/onboarding/campaign-opportunity",
    copy: "Draft campaign, opportunity, readiness, and go-live intent after access setup.",
  },
  {
    label: "Operator monitoring",
    path: "/admin",
    copy: "Return to read-only platform diagnostics while membership APIs remain future work.",
  },
];

export function MemberRoleOnboardingPage() {
  const [form, setForm] = useState<FormState>(initialState);
  const requiredComplete = Boolean(
    form.organisationRef.trim() &&
      form.externalTenantRef.trim() &&
      form.userEmail.trim() &&
      form.displayName.trim() &&
      form.roleFamily.trim() &&
      form.participantType.trim() &&
      form.accessScope.trim() &&
      form.inviteStatus.trim(),
  );

  const readinessSteps = useMemo<ReadinessStep[]>(
    () => [
      {
        label: "External account scope",
        copy: "`external_tenant_ref` and `organisation_ref` identify the future account boundary without exposing tenant_code.",
        ready: Boolean(form.externalTenantRef.trim() && form.organisationRef.trim()),
      },
      {
        label: "Invite identity",
        copy: "Email and display name are captured locally for future invite delivery and user identity flows.",
        ready: Boolean(form.userEmail.trim() && form.displayName.trim()),
      },
      {
        label: "Role-family intent",
        copy: "Role family and participant type are selected before future membership permission checks exist.",
        ready: Boolean(form.roleFamily.trim() && form.participantType.trim()),
      },
      {
        label: "Access scope",
        copy: "Access scope and invite status are drafted, but no membership, seat, or auth claim changes are made.",
        ready: Boolean(form.accessScope.trim() && form.inviteStatus.trim()),
      },
      {
        label: "Backend membership lifecycle",
        copy: "Blocked until additive user, membership, invitation, seat, and role-assignment APIs are implemented.",
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
          <div className="page-kicker">DLaaS onboarding - Access setup</div>
          <h1 className="page-title">User, member & role setup</h1>
          <p className="page-copy">
            Capture invite intent, membership scope, and role-family assignment
            across operator, producer/sponsor, company admin, distributor, and
            partner contexts. This is a frontend shell only; no users,
            memberships, invites, seats, roles, or auth claims are created.
          </p>
        </div>
        <StatusBadge label="Shell only" tone="warning" />
      </section>

      <section className="grid-3">
        <SummaryItem label="Readiness" value={`${readyCount}/5`} />
        <SummaryItem label="Invite actions" value="Disabled" />
        <SummaryItem label="Internal tenant_code" value="Hidden" />
      </section>

      <section className="banner warning" role="note">
        <ShieldCheck size={18} />
        <div>
          <strong>No user, invite, membership, or role records are created from this page.</strong>
          <div className="table-subtext">
            This shell uses local form state only. It does not call identity,
            invitation, membership, seat, role-assignment, auth, billing,
            funding, fulfilment, settlement, retry, or money movement APIs.
          </div>
        </div>
      </section>

      <section className="grid-2">
        <form className="panel" aria-label="User member role setup shell">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Invite and role intent</h2>
              <div className="panel-subtitle">
                Safe setup fields before membership lifecycle APIs exist.
              </div>
            </div>
            <UserPlus size={18} />
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
                label="User email"
                value={form.userEmail}
                onChange={(value) => updateField("userEmail", value)}
                placeholder="admin@example.test"
                required
              />
              <TextField
                label="Display name"
                value={form.displayName}
                onChange={(value) => updateField("displayName", value)}
                placeholder="Alex Admin"
                required
              />
              <SelectField
                label="Role family"
                value={form.roleFamily}
                onChange={(value) => updateField("roleFamily", value)}
                options={[
                  "Platform operator",
                  "Company admin",
                  "Producer / sponsor admin",
                  "Distributor / partner admin",
                  "Finance admin",
                  "System admin",
                  "Support viewer",
                ]}
              />
              <SelectField
                label="Participant type"
                value={form.participantType}
                onChange={(value) => updateField("participantType", value)}
                options={[
                  "Platform operator",
                  "Producer / sponsor",
                  "Distributor",
                  "Partner integration",
                  "Consumer support",
                ]}
              />
              <SelectField
                label="Access scope"
                value={form.accessScope}
                onChange={(value) => updateField("accessScope", value)}
                options={[
                  "Organisation setup only",
                  "Producer workspace later",
                  "Distributor workspace later",
                  "Read-only operator support",
                  "Finance operations later",
                  "System operations later",
                ]}
              />
              <SelectField
                label="Invite status"
                value={form.inviteStatus}
                onChange={(value) => updateField("inviteStatus", value)}
                options={[
                  "Draft invite",
                  "Ready for future invitation API",
                  "Hold for access review",
                  "Blocked by account setup",
                ]}
              />
            </div>
            <div className="action-button-row">
              <button className="button" disabled type="button">
                Send invite later
              </button>
              <button className="button secondary" disabled type="button">
                Assign role later
              </button>
              <button className="button secondary" disabled type="button">
                Activate membership later
              </button>
              <span className={requiredComplete ? "muted" : "danger-text"}>
                {requiredComplete
                  ? "Required shell fields are captured locally."
                  : "Complete required shell fields before a future invite flow."}
              </span>
            </div>
          </div>
        </form>

        <section className="panel" aria-labelledby="member-readiness-heading">
          <div className="panel-header">
            <div>
              <h2 className="panel-title" id="member-readiness-heading">
                Setup readiness
              </h2>
              <div className="panel-subtitle">
                Role setup guardrails before identity and permission work.
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
            <h2 className="panel-title">Persona and permission guidance</h2>
            <div className="panel-subtitle">
              TASK-073 visualizes membership intent without changing auth.
            </div>
          </div>
          <Users size={18} />
        </div>
        <div className="panel-body capability-grid">
          <BoundaryCard
            icon={ShieldCheck}
            title="Platform operator"
            copy="Platform, system, finance, distribution, and support roles remain admin-scoped and audited by future membership checks."
          />
          <BoundaryCard
            icon={KeyRound}
            title="Producer or company admin"
            copy="Producer/sponsor and company admins draft campaign, reporting, and setup access without funding or billing changes."
          />
          <BoundaryCard
            icon={Users}
            title="Distributor or partner admin"
            copy="Distributor and partner admins draft portal and integration access without routes, wallets, or offer mutations."
          />
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Access boundary</h2>
            <div className="panel-subtitle">
              Keep external references visible and internal identifiers hidden.
            </div>
          </div>
          <LockKeyhole size={18} />
        </div>
        <div className="panel-body capability-grid">
          <BoundaryCard
            icon={LinkIcon}
            title="External references only"
            copy="Use external_tenant_ref and organisation_ref for onboarding; tenant_code remains an internal partition key."
          />
          <BoundaryCard
            icon={UserPlus}
            title="Invites are not delivered"
            copy="Email delivery, identity-provider registration, seat assignment, and membership activation are disabled placeholders."
          />
          <BoundaryCard
            icon={ShieldCheck}
            title="Auth stays unchanged"
            copy="This shell does not grant access, create roles, change sessions, or bypass the API permission matrix."
          />
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Onboarding journey links</h2>
            <div className="panel-subtitle">
              Continue the product journey without production writes.
            </div>
          </div>
          <CircleDashed size={18} />
        </div>
        <div className="panel-body route-list">
          {nextJourneyLinks.map((item) => (
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
