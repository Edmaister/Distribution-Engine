import {
  BadgeDollarSign,
  CheckCircle2,
  CircleDashed,
  Flag,
  GitPullRequestArrow,
  Link as LinkIcon,
  Rocket,
  ShieldCheck,
  Target,
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
  producerSponsorRef: string;
  campaignCode: string;
  opportunityRef: string;
  campaignName: string;
  marketCountry: string;
  distributionModel: string;
  eligibleDistributorType: string;
  intendedOutcomeEvent: string;
  rewardCommissionIntent: string;
  fundingModelIntent: string;
  goLiveTargetStatus: string;
  linkCodeIntent: string;
};

type WizardStep = {
  id: string;
  label: string;
  copy: string;
};

type ReadinessStep = {
  label: string;
  copy: string;
  ready: boolean;
};

const wizardSteps: WizardStep[] = [
  {
    id: "basics",
    label: "Basics",
    copy: "External refs, campaign code, opportunity reference, name, and market.",
  },
  {
    id: "participants",
    label: "Participants",
    copy: "Producer/sponsor ownership and eligible distributor type.",
  },
  {
    id: "distribution",
    label: "Distribution model",
    copy: "Channel model and link/code intent before any route generation.",
  },
  {
    id: "outcome",
    label: "Outcome and reward intention",
    copy: "Outcome event and reward/commission policy direction only.",
  },
  {
    id: "funding",
    label: "Funding intention",
    copy: "Funding model intent without reservation, wallet, or invoice writes.",
  },
  {
    id: "review",
    label: "Readiness review",
    copy: "Go-live status preview and unavailable backend integration blockers.",
  },
];

const initialState: FormState = {
  organisationRef: "",
  producerSponsorRef: "",
  campaignCode: "",
  opportunityRef: "",
  campaignName: "",
  marketCountry: "",
  distributionModel: "Lead/referral distribution",
  eligibleDistributorType: "Distributor / partner admin",
  intendedOutcomeEvent: "QUALIFIED_OUTCOME",
  rewardCommissionIntent: "Reward and commission policy to be selected later",
  fundingModelIntent: "Funding model undecided",
  goLiveTargetStatus: "Draft setup",
  linkCodeIntent: "Inspect readiness before link/code issuance",
};

const journeyLinks = [
  {
    label: "Company onboarding",
    path: "/admin/onboarding/company",
    copy: "Return to organisation and external tenant setup.",
  },
  {
    label: "Producer / sponsor onboarding",
    path: "/admin/onboarding/producer-sponsor",
    copy: "Confirm producer/sponsor identity before campaign setup.",
  },
  {
    label: "Distributor onboarding",
    path: "/admin/onboarding/distributor",
    copy: "Confirm eligible demand-side participants before routing.",
  },
  {
    label: "User & role setup",
    path: "/admin/onboarding/members-roles",
    copy: "Draft role-family access before operational readiness.",
  },
  {
    label: "Webhook & API setup",
    path: "/admin/onboarding/webhook-api",
    copy: "Draft callback, credential, event catalog, and payload preview intent after campaign setup.",
  },
  {
    label: "Demand marketplace",
    path: "/admin/distribution",
    copy: "Move to the existing read-only marketplace surface after setup review.",
  },
];

const readOnlyScope = {
  external_tenant_ref: "demo-platform-operator",
  organisation_ref: "demo-organisation",
  producer_ref: "demo-producer",
  sponsor_ref: "demo-sponsor",
  campaign_code: "DEMO-CAMPAIGN",
  opportunity_ref: "demo-opportunity",
};

type LoadState = "loading" | "success" | "fallback";

export function CampaignOpportunitySetupPage() {
  const [form, setForm] = useState<FormState>(initialState);
  const [activeStepId, setActiveStepId] = useState(wizardSteps[0].id);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [readOnlyState, setReadOnlyState] =
    useState<AdminOnboardingStateResponse | null>(null);
  const requiredComplete = Boolean(
    form.organisationRef.trim() &&
    form.producerSponsorRef.trim() &&
    form.campaignCode.trim() &&
    form.opportunityRef.trim() &&
    form.campaignName.trim() &&
    form.marketCountry.trim() &&
    form.distributionModel.trim() &&
    form.eligibleDistributorType.trim() &&
    form.intendedOutcomeEvent.trim() &&
    form.rewardCommissionIntent.trim() &&
    form.fundingModelIntent.trim() &&
    form.goLiveTargetStatus.trim() &&
    form.linkCodeIntent.trim(),
  );

  const readinessSteps = useMemo<ReadinessStep[]>(
    () => [
      {
        label: "Campaign basics",
        copy: "Organisation reference, campaign code, opportunity reference, name, and market are captured locally.",
        ready: Boolean(
          form.organisationRef.trim() &&
          form.campaignCode.trim() &&
          form.opportunityRef.trim() &&
          form.campaignName.trim() &&
          form.marketCountry.trim(),
        ),
      },
      {
        label: "Participant scope",
        copy: "Producer/sponsor reference and eligible distributor type are selected without changing permissions.",
        ready: Boolean(
          form.producerSponsorRef.trim() && form.eligibleDistributorType.trim(),
        ),
      },
      {
        label: "Distribution intent",
        copy: "Distribution model and link/code intent are drafted, but no routes, links, or codes are generated.",
        ready: Boolean(
          form.distributionModel.trim() && form.linkCodeIntent.trim(),
        ),
      },
      {
        label: "Outcome and policy intent",
        copy: "Outcome event and reward/commission policy direction are captured without policy or money writes.",
        ready: Boolean(
          form.intendedOutcomeEvent.trim() &&
          form.rewardCommissionIntent.trim(),
        ),
      },
      {
        label: "Funding intention",
        copy: "Funding model intent is visible without budget reservation, wallet, invoice, fulfilment, or settlement changes.",
        ready: Boolean(form.fundingModelIntent.trim()),
      },
      {
        label: "Backend launch lifecycle",
        copy: "Blocked until safe campaign creation, opportunity publication, readiness, link/code, funding, and lifecycle APIs are explicitly wired.",
        ready: false,
      },
    ],
    [form],
  );

  const readyCount = readinessSteps.filter((step) => step.ready).length;
  const activeStep =
    wizardSteps.find((step) => step.id === activeStepId) || wizardSteps[0];
  const campaignCategory = readOnlyState?.readiness.categories.find(
    (category) =>
      category.category.toUpperCase().includes("CAMPAIGN") ||
      category.category.toUpperCase().includes("OPPORTUNITY"),
  );

  function updateField(field: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
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
          <div className="page-kicker">DLaaS onboarding - Campaign setup</div>
          <h1 className="page-title">Campaign & opportunity setup wizard</h1>
          <p className="page-copy">
            Walk through campaign and distribution opportunity setup intent
            before any lifecycle, routing, link/code, reward, funding,
            fulfilment, or settlement command is available.
          </p>
        </div>
        <StatusBadge label="Shell only" tone="warning" />
      </section>

      <section className="grid-3">
        <SummaryItem label="Readiness" value={`${readyCount}/6`} />
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
              Uses external campaign and opportunity references to hydrate safe
              readiness context when available.
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
                <strong>Loading read-only campaign readiness.</strong>
                <div className="table-subtext">
                  The wizard is checking external references without creating
                  campaigns, publishing opportunities, issuing links, activating
                  routes, writing policies, funding, fulfilling, settling,
                  retrying, going live, or moving money.
                </div>
              </div>
            </div>
          ) : loadState === "fallback" ? (
            <div className="banner warning" role="status">
              <ShieldCheck size={18} />
              <div>
                <strong>Using local campaign setup fallback.</strong>
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
                  label="Campaign code"
                  value={readOnlyScope.campaign_code}
                />
                <SummaryItem
                  label="Opportunity ref"
                  value={readOnlyScope.opportunity_ref}
                />
              </div>
              <div className="grid-3">
                <SummaryItem
                  label="Producer ref"
                  value={readOnlyScope.producer_ref}
                />
                <SummaryItem
                  label="Sponsor ref"
                  value={readOnlyScope.sponsor_ref}
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
                      {campaignCategory?.display_label ??
                        "Campaign / opportunity setup"}
                    </div>
                    <div className="route-path">
                      {campaignCategory?.evidence_summary ??
                        "Read-only campaign/opportunity evidence is not available yet."}
                    </div>
                    {campaignCategory?.blockers[0] ? (
                      <div className="table-subtext">
                        {campaignCategory.blockers[0]}
                      </div>
                    ) : null}
                    {campaignCategory?.next_actions[0] ? (
                      <div className="table-subtext">
                        {campaignCategory.next_actions[0]}
                      </div>
                    ) : null}
                  </div>
                  <StatusBadge
                    label={
                      campaignCategory?.safe_display_status?.label ??
                      campaignCategory?.status ??
                      "Missing evidence"
                    }
                    tone={
                      campaignCategory?.status === "READY" ? "success" : "info"
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
          <strong>
            No campaign, opportunity, route, link, code, reward, or funding
            records are created from this page.
          </strong>
          <div className="table-subtext">
            This wizard uses local form state only. It does not call campaign
            creation, opportunity publication, route generation, link/code
            issuance, policy, funding, fulfilment, settlement, retry, or money
            movement APIs.
          </div>
        </div>
      </section>

      <section className="grid-2">
        <section
          className="panel"
          aria-label="Campaign opportunity setup wizard"
        >
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Wizard steps</h2>
              <div className="panel-subtitle">
                Step through a setup draft without publishing anything.
              </div>
            </div>
            <Rocket size={18} />
          </div>
          <div className="panel-body route-list">
            {wizardSteps.map((step, index) => (
              <button
                className="route-item"
                key={step.id}
                onClick={() => setActiveStepId(step.id)}
                type="button"
              >
                <div>
                  <div className="route-name">
                    {index + 1}. {step.label}
                  </div>
                  <div className="route-path">{step.copy}</div>
                </div>
                <StatusBadge
                  label={step.id === activeStep.id ? "Open" : "Draft"}
                  tone={step.id === activeStep.id ? "info" : "neutral"}
                />
              </button>
            ))}
          </div>
        </section>

        <form className="panel" aria-label="Campaign opportunity setup form">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">{activeStep.label}</h2>
              <div className="panel-subtitle">{activeStep.copy}</div>
            </div>
            <Target size={18} />
          </div>
          <div className="panel-body">
            {activeStep.id === "basics" ? (
              <div className="grid-2">
                <TextField
                  label="organisation_ref"
                  value={form.organisationRef}
                  onChange={(value) => updateField("organisationRef", value)}
                  placeholder="org-acme"
                  required
                />
                <TextField
                  label="campaign_code"
                  value={form.campaignCode}
                  onChange={(value) => updateField("campaignCode", value)}
                  placeholder="ACME-INSURANCE-2026"
                  required
                />
                <TextField
                  label="opportunity_ref"
                  value={form.opportunityRef}
                  onChange={(value) => updateField("opportunityRef", value)}
                  placeholder="opp-acme-insurance-2026"
                  required
                />
                <TextField
                  label="Campaign name"
                  value={form.campaignName}
                  onChange={(value) => updateField("campaignName", value)}
                  placeholder="Acme insurance launch"
                  required
                />
                <TextField
                  label="Market / country"
                  value={form.marketCountry}
                  onChange={(value) => updateField("marketCountry", value)}
                  placeholder="South Africa"
                  required
                />
              </div>
            ) : null}

            {activeStep.id === "participants" ? (
              <div className="grid-2">
                <TextField
                  label="producer_ref / sponsor_ref"
                  value={form.producerSponsorRef}
                  onChange={(value) => updateField("producerSponsorRef", value)}
                  placeholder="prod-acme-insurance"
                  required
                />
                <SelectField
                  label="Eligible distributor type"
                  value={form.eligibleDistributorType}
                  onChange={(value) =>
                    updateField("eligibleDistributorType", value)
                  }
                  options={[
                    "Distributor / partner admin",
                    "Advisor network",
                    "Affiliate channel",
                    "Broker channel",
                    "Embedded marketplace",
                  ]}
                />
              </div>
            ) : null}

            {activeStep.id === "distribution" ? (
              <div className="grid-2">
                <SelectField
                  label="Channel / distribution model"
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
                  label="Link/code intent"
                  value={form.linkCodeIntent}
                  onChange={(value) => updateField("linkCodeIntent", value)}
                  options={[
                    "Inspect readiness before link/code issuance",
                    "Future campaign code",
                    "Future distributor route link",
                    "Future QR distribution link",
                  ]}
                />
              </div>
            ) : null}

            {activeStep.id === "outcome" ? (
              <div className="grid-2">
                <SelectField
                  label="Intended outcome event"
                  value={form.intendedOutcomeEvent}
                  onChange={(value) =>
                    updateField("intendedOutcomeEvent", value)
                  }
                  options={[
                    "QUALIFIED_OUTCOME",
                    "ACCOUNT_OPENED",
                    "POLICY_ACTIVATED",
                    "PURCHASE_COMPLETED",
                    "LEAD_ACCEPTED",
                  ]}
                />
                <SelectField
                  label="Reward / commission policy intention"
                  value={form.rewardCommissionIntent}
                  onChange={(value) =>
                    updateField("rewardCommissionIntent", value)
                  }
                  options={[
                    "Reward and commission policy to be selected later",
                    "Customer/referrer reward only",
                    "Distributor commission only",
                    "Reward plus distributor commission",
                    "No money policy in this demo",
                  ]}
                />
              </div>
            ) : null}

            {activeStep.id === "funding" ? (
              <div className="grid-2">
                <SelectField
                  label="Funding model intention"
                  value={form.fundingModelIntent}
                  onChange={(value) => updateField("fundingModelIntent", value)}
                  options={[
                    "Funding model undecided",
                    "Prefunded campaign later",
                    "Invoice-backed sponsor later",
                    "Budget reservation later",
                    "No money movement in demo",
                  ]}
                />
              </div>
            ) : null}

            {activeStep.id === "review" ? (
              <div className="grid-2">
                <SelectField
                  label="Go-live target / status"
                  value={form.goLiveTargetStatus}
                  onChange={(value) => updateField("goLiveTargetStatus", value)}
                  options={[
                    "Draft setup",
                    "Ready for future readiness API",
                    "Hold for policy review",
                    "Blocked by funding setup",
                    "Blocked by distributor readiness",
                  ]}
                />
              </div>
            ) : null}

            <div className="action-button-row">
              <button className="button" disabled type="button">
                Save campaign later
              </button>
              <button className="button secondary" disabled type="button">
                Publish opportunity later
              </button>
              <button className="button secondary" disabled type="button">
                Generate links later
              </button>
              <button className="button secondary" disabled type="button">
                Activate route later
              </button>
              <button className="button secondary" disabled type="button">
                Write reward policy later
              </button>
              <button className="button secondary" disabled type="button">
                Configure funding later
              </button>
              <button className="button secondary" disabled type="button">
                Trigger fulfilment later
              </button>
              <button className="button secondary" disabled type="button">
                Run settlement later
              </button>
              <button className="button secondary" disabled type="button">
                Retry lifecycle later
              </button>
              <button className="button secondary" disabled type="button">
                Activate go-live later
              </button>
              <button className="button secondary" disabled type="button">
                Move money later
              </button>
              <span className={requiredComplete ? "muted" : "danger-text"}>
                {requiredComplete
                  ? "Required wizard fields are captured locally."
                  : "Complete wizard fields before a future campaign create flow."}
              </span>
            </div>
          </div>
        </form>
      </section>

      <section className="grid-2">
        <section className="panel" aria-labelledby="campaign-readiness-heading">
          <div className="panel-header">
            <div>
              <h2 className="panel-title" id="campaign-readiness-heading">
                Readiness review
              </h2>
              <div className="panel-subtitle">
                Derived setup preview before any backend lifecycle command.
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

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Safe launch boundary</h2>
              <div className="panel-subtitle">
                TASK-074 stops at local setup intent and disabled actions.
              </div>
            </div>
            <Flag size={18} />
          </div>
          <div className="panel-body capability-grid">
            <BoundaryCard
              icon={LinkIcon}
              title="External setup identifiers"
              copy="Use organisation_ref, producer_ref or sponsor_ref, campaign_code, and opportunity_ref; the internal tenant identifier remains hidden."
            />
            <BoundaryCard
              icon={GitPullRequestArrow}
              title="Lifecycle commands are unavailable"
              copy="No create, publish, route, link/code issuance, activate, pause, close, or go-live command is wired."
            />
            <BoundaryCard
              icon={BadgeDollarSign}
              title="Money setup is intent only"
              copy="Reward, commission, funding, fulfilment, settlement, wallet, and billing work remain untouched."
            />
          </div>
        </section>
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
