import {
  CheckCircle2,
  CircleDashed,
  GitPullRequestArrow,
  Link as LinkIcon,
  Route,
  ShieldCheck,
  Store,
  Wallet,
} from "lucide-react";
import { useId, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";

type FormState = {
  distributorName: string;
  externalTenantRef: string;
  distributorRef: string;
  organisationRef: string;
  channelType: string;
  marketCountry: string;
  adminContact: string;
  distributionModel: string;
  participationIntent: string;
};

type ReadinessStep = {
  label: string;
  copy: string;
  ready: boolean;
};

const initialState: FormState = {
  distributorName: "",
  externalTenantRef: "",
  distributorRef: "",
  organisationRef: "",
  channelType: "Partner distributor",
  marketCountry: "",
  adminContact: "",
  distributionModel: "Lead/referral distribution",
  participationIntent: "Campaign participant",
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
    copy: "Review sponsor setup intent before connecting demand-side partners.",
  },
  {
    label: "User & role setup",
    path: "/admin/onboarding/members-roles",
    copy: "Draft distributor or partner admin invite intent before portal access is live.",
  },
  {
    label: "Distributor portal",
    path: "/distributor",
    copy: "View the existing distributor-safe portal after onboarding data is mocked locally.",
  },
];

export function DistributorOnboardingPage() {
  const [form, setForm] = useState<FormState>(initialState);
  const requiredComplete = Boolean(
    form.distributorName.trim() &&
      form.externalTenantRef.trim() &&
      form.distributorRef.trim() &&
      form.organisationRef.trim() &&
      form.marketCountry.trim() &&
      form.adminContact.trim(),
  );

  const readinessSteps = useMemo<ReadinessStep[]>(
    () => [
      {
        label: "Distributor profile",
        copy: "Display name, channel type, market, and distribution model are captured locally.",
        ready: Boolean(
          form.distributorName.trim() &&
            form.channelType.trim() &&
            form.marketCountry.trim() &&
            form.distributionModel.trim(),
        ),
      },
      {
        label: "External references",
        copy: "`external_tenant_ref`, `distributor_ref`, and `organisation_ref` stay outside internal tenant partitioning.",
        ready: Boolean(
          form.externalTenantRef.trim() &&
            form.distributorRef.trim() &&
            form.organisationRef.trim(),
        ),
      },
      {
        label: "Portal access contact",
        copy: "Distributor admin contact is ready for a future membership and role invite flow.",
        ready: Boolean(form.adminContact.trim()),
      },
      {
        label: "Campaign participation intent",
        copy: "Offer, route, and campaign participation are captured as intent only.",
        ready: Boolean(form.participationIntent.trim()),
      },
      {
        label: "Backend distributor onboarding",
        copy: "Blocked until additive distributor onboarding and lifecycle APIs are implemented.",
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
          <div className="page-kicker">DLaaS onboarding - Distributor setup</div>
          <h1 className="page-title">Distributor onboarding</h1>
          <p className="page-copy">
            Capture distributor setup intent, market context, and portal access
            readiness using external references. This shell does not create
            distributors, routes, wallets, offers, commissions, or lifecycle
            records.
          </p>
        </div>
        <StatusBadge label="Shell only" tone="warning" />
      </section>

      <section className="grid-3">
        <SummaryItem label="Readiness" value={`${readyCount}/5`} />
        <SummaryItem label="Lifecycle actions" value="Disabled" />
        <SummaryItem label="Internal tenant_code" value="Hidden" />
      </section>

      <section className="banner warning" role="note">
        <ShieldCheck size={18} />
        <div>
          <strong>No distributor or marketplace records are created from this page.</strong>
          <div className="table-subtext">
            This shell uses local form state only. It does not call distributor
            creation, activation, route, offer, wallet, funding, fulfilment,
            settlement, retry, or money movement APIs.
          </div>
        </div>
      </section>

      <section className="grid-2">
        <form className="panel" aria-label="Distributor onboarding shell">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Distributor profile</h2>
              <div className="panel-subtitle">
                Safe demand-side setup fields before marketplace lifecycle work.
              </div>
            </div>
            <Store size={18} />
          </div>
          <div className="panel-body">
            <div className="grid-2">
              <TextField
                label="Distributor name"
                value={form.distributorName}
                onChange={(value) => updateField("distributorName", value)}
                placeholder="Acme Advisor Network"
                required
              />
              <TextField
                label="external_tenant_ref"
                value={form.externalTenantRef}
                onChange={(value) => updateField("externalTenantRef", value)}
                placeholder="acme-advisors"
                required
              />
              <TextField
                label="distributor_ref"
                value={form.distributorRef}
                onChange={(value) => updateField("distributorRef", value)}
                placeholder="dist-acme-advisors"
                required
              />
              <TextField
                label="organisation_ref"
                value={form.organisationRef}
                onChange={(value) => updateField("organisationRef", value)}
                placeholder="org-acme-advisors"
                required
              />
              <SelectField
                label="Channel type"
                value={form.channelType}
                onChange={(value) => updateField("channelType", value)}
                options={[
                  "Partner distributor",
                  "Advisor network",
                  "Affiliate channel",
                  "Broker channel",
                  "Embedded marketplace",
                ]}
              />
              <TextField
                label="Market / country"
                value={form.marketCountry}
                onChange={(value) => updateField("marketCountry", value)}
                placeholder="South Africa"
                required
              />
              <TextField
                label="Distributor admin contact"
                value={form.adminContact}
                onChange={(value) => updateField("adminContact", value)}
                placeholder="distributor-admin@example.test"
                required
              />
              <SelectField
                label="Distribution model"
                value={form.distributionModel}
                onChange={(value) => updateField("distributionModel", value)}
                options={[
                  "Lead/referral distribution",
                  "Offer route distribution",
                  "QR/link distribution",
                  "Partner API distribution",
                ]}
              />
              <SelectField
                label="Campaign / opportunity participation"
                value={form.participationIntent}
                onChange={(value) => updateField("participationIntent", value)}
                options={[
                  "Campaign participant",
                  "Opportunity candidate",
                  "Route owner later",
                  "Portal viewer first",
                ]}
              />
            </div>
            <div className="action-button-row">
              <button className="button" disabled type="button">
                Create distributor later
              </button>
              <button className="button secondary" disabled type="button">
                Activate route later
              </button>
              <button className="button secondary" disabled type="button">
                Create wallet later
              </button>
              <span className={requiredComplete ? "muted" : "danger-text"}>
                {requiredComplete
                  ? "Required shell fields are captured locally."
                  : "Complete required shell fields before a future distributor create flow."}
              </span>
            </div>
          </div>
        </form>

        <section className="panel" aria-labelledby="distributor-readiness-heading">
          <div className="panel-header">
            <div>
              <h2 className="panel-title" id="distributor-readiness-heading">
                Setup readiness
              </h2>
              <div className="panel-subtitle">
                Distributor guardrails before routes, offers, wallets, and portal access.
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
            <h2 className="panel-title">Safe distributor boundary</h2>
            <div className="panel-subtitle">
              TASK-072 stops at setup intent and disabled placeholders.
            </div>
          </div>
          <Route size={18} />
        </div>
        <div className="panel-body capability-grid">
          <BoundaryCard
            icon={LinkIcon}
            title="External distributor identity"
            copy="Use distributor_ref and organisation_ref for SaaS-facing setup; tenant_code remains internal."
          />
          <BoundaryCard
            icon={GitPullRequestArrow}
            title="Routes are not active"
            copy="No offer routes, referral links, acceptance, activation, or opportunity mutations are triggered."
          />
          <BoundaryCard
            icon={Wallet}
            title="Wallets are not created"
            copy="No distributor wallet, commission, payout, fulfilment, settlement, or funding state is changed."
          />
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Next onboarding steps</h2>
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
  icon: typeof Store;
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
