import { CheckCircle2, CircleAlert, CircleDashed, CircleDot, Info } from "lucide-react";
import { InfoTooltip } from "./InfoTooltip";
import { StatusBadge } from "./StatusBadge";

export type JourneyStepState = "done" | "current" | "waiting" | "blocked" | "review";

type Tone = "success" | "warning" | "danger" | "info" | "neutral";

export type JourneyStep = {
  label: string;
  description: string;
  state: JourneyStepState;
  workArea?: string;
  targetId?: string;
  help?: string;
};

type Props = {
  title: string;
  subtitle: string;
  badge: string;
  tone: Tone;
  currentTitle: string;
  currentCopy: string;
  steps: JourneyStep[];
};

const stateMeta: Record<JourneyStepState, { label: string; tone: Tone; icon: typeof CheckCircle2 }> = {
  done: { label: "Done", tone: "success", icon: CheckCircle2 },
  current: { label: "Current", tone: "info", icon: CircleDot },
  waiting: { label: "Waiting", tone: "neutral", icon: CircleDashed },
  blocked: { label: "Blocked", tone: "danger", icon: CircleAlert },
  review: { label: "Review", tone: "warning", icon: Info },
};

export function JourneyTracker({ title, subtitle, badge, tone, currentTitle, currentCopy, steps }: Props) {
  return (
    <section className="panel journey-panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">{title}</h2>
          <div className="panel-subtitle">{subtitle}</div>
        </div>
        <StatusBadge label={badge} tone={tone} />
      </div>
      <div className="panel-body">
        <div className="journey-summary">
          <div>
            <div className="guidance-kicker">Current focus</div>
            <div className="guidance-title">{currentTitle}</div>
            <p className="guidance-copy">{currentCopy}</p>
          </div>
        </div>
        <ol className="journey-steps" aria-label={title}>
          {steps.map((step, index) => {
            const meta = stateMeta[step.state];
            const Icon = meta.icon;
            return (
              <li className={`journey-step ${step.state}`} key={step.label}>
                <div className="journey-step-index">
                  <Icon size={16} />
                  <span>{index + 1}</span>
                </div>
                <div className="journey-step-body">
                  <div className="journey-step-title">
                    {step.label}
                    {step.help ? <InfoTooltip text={step.help} /> : null}
                  </div>
                  <div className="journey-step-copy">{step.description}</div>
                  {step.workArea ? (
                    <div className="journey-step-area">
                      <span>Do this in</span>
                      {step.targetId ? (
                        <a href={`#${step.targetId}`}>{step.workArea}</a>
                      ) : (
                        step.workArea
                      )}
                    </div>
                  ) : null}
                </div>
                <StatusBadge label={meta.label} tone={meta.tone} />
              </li>
            );
          })}
        </ol>
      </div>
    </section>
  );
}
