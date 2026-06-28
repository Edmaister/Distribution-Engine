import {
  BadgeDollarSign,
  Building2,
  CheckCircle2,
  CircleDashed,
  Link as LinkIcon,
  ShieldCheck,
  Target,
  Wallet,
} from "lucide-react";
import { useId, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";

type FormState = {
  sponsorName: string;
  externalTenantRef: string;
  producerRef: string;
  sponsorRef: string;
  organisationRef: string;
  industry: string;
  fundingModelIntent: string;
  adminContact: string;
  campaignRole: string;
};

type ReadinessStep = {
  label: string;
  copy: string;
  ready: boolean;
};

const initialState: FormState = {
  sponsorName: "",
  externalTenantRef: "",
  producerRef: "",
  sponsorRef: "",
  organisationRef: "",
  industry: "",
  fundingModelIntent: "Budget owner, not funded yet",
  adminContact: "",
  campaignRole: "Campaign owner",
};

const nextJourneyLinks = [
  {
    label: "Company onboarding",
    path: "/admin/onboarding/company",
    copy: "Return to the organisation shell and external tenant boundary.",
  },
  {
    label: "Distributor onboarding",
    path: "/admin/onboarding/distributor",
    copy: "Continue to distributor setup once the producer/sponsor shell is ready.",
  },
  {
    label: "User & role setup",
    path: "/admin/onboarding/members-roles",
    copy: "Draft producer admin invite and role-family intent without provisioning access.",
  },
  {
    label: "Campaign / opportunity setup",
    path: "/admin/onboarding/campaign-opportunity",
    copy: "Draft campaign ownership, outcome, reward, and funding intent without launching anything.",
  },
  {
    label: "Producer workspace",
    path: "/sponsor",
    copy: "View the existing producer workspace after onboarding data is mocked locally.",
  },
];

export function ProducerSponsorOnboardingPage() {
  const [form, setForm] = useState<FormState>(initialState);
  const requiredComplete = Boolean(
    form.sponsorName.trim() &&
      form.externalTenantRef.trim() &&
      form.producerRef.trim() &&
      form.sponsorRef.trim() &&
      form.organisationRef.trim() &&
      form.adminContact.trim(),
  );

  const readinessSteps = useMemo<ReadinessStep[]>(
    () => [
      {
        label: "Producer profile",
        copy: "Display name, industry, and campaign ownership intent are captured locally.",
        ready: Boolean(form.sponsorName.trim() && form.industry.trim()),
      },
      {
        label: "External references",
        copy: "`external_tenant_ref`, `producer_ref`, `sponsor_ref`, and `organisation_ref` stay outside internal tenant partitioning.",
        ready: Boolean(
          form.externalTenantRef.trim() &&
            form.producerRef.trim() &&
            form.sponsorRef.trim() &&
            form.organisationRef.trim(),
        ),
      },
      {
        label: "Admin contact",
        copy: "Primary producer admin contact is ready for a future membership invite flow.",
        ready: Boolean(form.adminContact.trim() && form.campaignRole.trim()),
      },
      {
        label: "Funding readiness",
        copy: "Funding model intent is noted, but no wallet, funding contract, invoice, or budget record is created.",
        ready: Boolean(form.fundingModelIntent.trim()),
      },
      {
        label: "Backend sponsor onboarding",
        copy: "Blocked until additive producer/sponsor onboarding APIs are implemented.",
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
          <div className="page-kicker">DLaaS onboarding - Producer setup</div>
          <h1 className="page-title">Producer & sponsor onboarding</h1>
          <p className="page-copy">
            Capture producer and sponsor setup intent with external references
            and funding-readiness placeholders. This is a frontend shell only;
            no sponsor, wallet, billing, funding, or campaign records are
            created.
          </p>
        </div>
        <StatusBadge label="Shell only" tone="warning" />
      </section>

      <section className="grid-3">
        <SummaryItem label="Readiness" value={`${readyCount}/5`} />
        <SummaryItem label="Funding actions" value="Disabled" />
        <SummaryItem label="Internal tenant_code" value="Hidden" />
      </section>

      <section className="banner warning" role="note">
        <ShieldCheck size={18} />
        <div>
          <strong>No money or sponsor records are created from this page.</strong>
          <div className="table-subtext">
            This shell uses local form state only. It does not call sponsor
            onboarding, funding, wallet, billing, fulfilment, settlement, or
            campaign launch APIs.
          </div>
        </div>
      </section>

      <section className="grid-2">
        <form className="panel" aria-label="Producer sponsor onboarding shell">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Producer profile</h2>
              <div className="panel-subtitle">
                Safe setup fields for campaign ownership and sponsor identity.
              </div>
            </div>
            <Building2 size={18} />
          </div>
          <div className="panel-body">
            <div className="grid-2">
              <TextField
                label="Producer / sponsor name"
                value={form.sponsorName}
                onChange={(value) => updateField("sponsorName", value)}
                placeholder="Acme Insurance Sponsors"
                required
              />
              <TextField
                label="external_tenant_ref"
                value={form.externalTenantRef}
                onChange={(value) => updateField("externalTenantRef", value)}
                placeholder="acme-insurance"
                required
              />
              <TextField
                label="producer_ref"
                value={form.producerRef}
                onChange={(value) => updateField("producerRef", value)}
                placeholder="prod-acme-insurance"
                required
              />
              <TextField
                label="sponsor_ref"
                value={form.sponsorRef}
                onChange={(value) => updateField("sponsorRef", value)}
                placeholder="spon-acme-insurance"
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
                label="Industry / vertical"
                value={form.industry}
                onChange={(value) => updateField("industry", value)}
                placeholder="Insurance, banking, retail"
              />
              <SelectField
                label="Funding model intention"
                value={form.fundingModelIntent}
                onChange={(value) => updateField("fundingModelIntent", value)}
                options={[
                  "Budget owner, not funded yet",
                  "Prefunded campaign later",
                  "Invoice-backed sponsor later",
                  "Funding model undecided",
                ]}
              />
              <TextField
                label="Producer admin contact"
                value={form.adminContact}
                onChange={(value) => updateField("adminContact", value)}
                placeholder="producer-admin@example.test"
                required
              />
              <SelectField
                label="Campaign / opportunity role"
                value={form.campaignRole}
                onChange={(value) => updateField("campaignRole", value)}
                options={[
                  "Campaign owner",
                  "Opportunity sponsor",
                  "Funding approver",
                  "Reporting viewer",
                ]}
              />
            </div>
            <div className="action-button-row">
              <button className="button" disabled type="button">
                Create sponsor later
              </button>
              <button className="button secondary" disabled type="button">
                Configure funding later
              </button>
              <span className={requiredComplete ? "muted" : "danger-text"}>
                {requiredComplete
                  ? "Required shell fields are captured locally."
                  : "Complete required shell fields before a future producer create flow."}
              </span>
            </div>
          </div>
        </form>

        <section className="panel" aria-labelledby="producer-readiness-heading">
          <div className="panel-header">
            <div>
              <h2 className="panel-title" id="producer-readiness-heading">
                Setup readiness
              </h2>
              <div className="panel-subtitle">
                Producer setup guardrails before campaign and funding work.
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
            <h2 className="panel-title">Safe funding boundary</h2>
            <div className="panel-subtitle">
              TASK-071 stops at setup intent and disabled placeholders.
            </div>
          </div>
          <Wallet size={18} />
        </div>
        <div className="panel-body capability-grid">
          <BoundaryCard
            icon={LinkIcon}
            title="External sponsor identity"
            copy="Use producer_ref and sponsor_ref for SaaS-facing setup; tenant_code remains internal."
          />
          <BoundaryCard
            icon={BadgeDollarSign}
            title="Funding is not active"
            copy="No wallet, invoice, funding contract, budget, or reserve/release behavior is triggered."
          />
          <BoundaryCard
            icon={Target}
            title="Campaign role only"
            copy="Campaign or opportunity ownership is captured as intent before future readiness and launch flows."
          />
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Next onboarding steps</h2>
            <div className="panel-subtitle">
              Continue the visible product journey without production writes.
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
