import { ShieldCheck } from "lucide-react";

import { StatusBadge } from "./StatusBadge";

type ProofPanelRole = "producer" | "distributor" | "consumer";
type BadgeTone = "success" | "warning" | "danger" | "info" | "neutral";

type Props = {
  proof: unknown;
  role: ProofPanelRole;
};

const roleCopy = {
  producer: {
    surface: "Producer - Supply",
    title: "Insurance supply proof",
    subtitle: "Shows that the producer offer can be traced through billing and the shared money journey.",
    valueLabel: "Producer value",
  },
  distributor: {
    surface: "Distributor - Demand",
    title: "Insurance demand proof",
    subtitle: "Shows that accepted demand can be traced through attribution, earnings, and wallet movement.",
    valueLabel: "Distributor value",
  },
  consumer: {
    surface: "Consumer Journey",
    title: "Insurance customer proof",
    subtitle: "Shows that the customer outcome can be traced through policy progress, reward visibility, and value.",
    valueLabel: "Customer value",
  },
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function asArray(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? value.filter((item) => item && typeof item === "object") as Record<string, unknown>[] : [];
}

function text(value: unknown, fallback = "-") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  return String(value);
}

function money(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return text(value);
  }
  return numeric.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function toneFor(status: unknown, ready: unknown): BadgeTone {
  if (ready === true || status === "READY") {
    return "success";
  }
  if (status === "MISSING") {
    return "warning";
  }
  if (status === "FAILED") {
    return "danger";
  }
  return "info";
}

function roleValue(role: ProofPanelRole, proof: Record<string, unknown>) {
  if (role === "producer") {
    return money(proof.invoiced_amount);
  }
  if (role === "distributor") {
    return money(proof.commission_amount ?? proof.wallet_movement_amount);
  }
  return money(proof.reward_amount);
}

export function InsuranceJourneyProofPanel({ proof, role }: Props) {
  const payload = asRecord(proof);
  const copy = roleCopy[role];
  const steps = asArray(payload.steps);
  const roleStep = steps.find((step) => step.surface === copy.surface);
  const stepTone = toneFor(roleStep?.status, roleStep?.ready);
  const overallTone = toneFor(payload.status, payload.ready);

  if (!Object.keys(payload).length) {
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{copy.title}</h2>
            <div className="panel-subtitle">{copy.subtitle}</div>
          </div>
          <StatusBadge label="Not loaded" tone="neutral" />
        </div>
        <div className="panel-body">
          <div className="state-panel">Insurance proof is not available yet.</div>
        </div>
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>{copy.title}</h2>
          <div className="panel-subtitle">{copy.subtitle}</div>
        </div>
        <StatusBadge label={text(roleStep?.status ?? payload.status, "Unknown")} tone={stepTone} />
      </div>
      <div className="panel-body">
        <div className="summary-grid">
          <div className="summary-item">
            <span>Campaign</span>
            <strong>{text(payload.campaign_code)}</strong>
          </div>
          <div className="summary-item">
            <span>Journey</span>
            <strong>{text(payload.journey_code)}</strong>
          </div>
          <div className="summary-item">
            <span>{copy.valueLabel}</span>
            <strong>{roleValue(role, payload)}</strong>
          </div>
          <div className="summary-item">
            <span>Money status</span>
            <strong>
              <StatusBadge label={text(payload.money_status ?? payload.status)} tone={overallTone} />
            </strong>
          </div>
        </div>
        <div className="state-panel">
          <div className="icon-title-row">
            <ShieldCheck size={18} />
            <strong>{text(roleStep?.label, copy.surface)}</strong>
          </div>
          <p>{text(roleStep?.evidence, text(payload.proof_summary))}</p>
          <p>{text(roleStep?.action, "Review the Insurance journey proof before continuing.")}</p>
        </div>
      </div>
    </section>
  );
}
