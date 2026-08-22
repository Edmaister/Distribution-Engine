import { CalendarClock, Check, Clock3, Plus, RotateCcw, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";

import type { ApiError } from "../../api/client";
import type { CreateCalendarInput, ServiceCalendar } from "../../api/endpoints/referralSaasServiceCalendars";
import {
  useCreateServiceCalendar,
  usePreviewServiceCalendar,
  useServiceCalendars,
  useTransitionServiceCalendar,
} from "../../api/referralSaasCalendarQueries";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";
import { StatusBadge } from "../../components/StatusBadge";

const weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const zones = ["Africa/Johannesburg", "Africa/Gaborone", "Africa/Windhoek", "Africa/Lusaka", "Europe/London", "America/New_York", "UTC"];

export function ReferralSaasServiceCalendarsPage() {
  const outlet = useOutletContext<{ refreshKey?: number } | undefined>();
  const calendars = useServiceCalendars(outlet?.refreshKey ?? 0);
  const create = useCreateServiceCalendar();
  const transition = useTransitionServiceCalendar();
  const preview = usePreviewServiceCalendar();
  const [selectedRef, setSelectedRef] = useState("");
  const [creating, setCreating] = useState(false);
  const [reason, setReason] = useState("");
  const [startedAt, setStartedAt] = useState(toLocalInput(new Date()));
  const [warningMinutes, setWarningMinutes] = useState(120);
  const [targetMinutes, setTargetMinutes] = useState(480);
  const [form, setForm] = useState(defaultForm);
  const selected = useMemo(() => {
    const items = calendars.data?.calendars || [];
    return items.find((item) => item.calendar_version_id === selectedRef) || items[0];
  }, [calendars.data, selectedRef]);

  function submitCreate(event: React.FormEvent) {
    event.preventDefault();
    create.mutate(
      {
        ...form,
        accountId: form.scopeType === "ACCOUNT" ? form.accountId : undefined,
        effectiveFrom: new Date(form.effectiveFrom).toISOString(),
        effectiveTo: form.effectiveTo ? new Date(form.effectiveTo).toISOString() : undefined,
        metadata: {},
      },
      { onSuccess: (response) => { setSelectedRef(response.calendar.calendar_version_id); setCreating(false); } },
    );
  }

  function runAction(action: "submit-review" | "approve" | "return-to-draft" | "retire") {
    if (!selected || !reason.trim()) return;
    transition.mutate({ calendarRef: selected.calendar_version_id, action, reason: reason.trim() }, { onSuccess: () => setReason("") });
  }

  function runPreview() {
    if (!selected) return;
    preview.mutate({
      calendarRef: selected.calendar_version_id,
      startedAt: new Date(startedAt).toISOString(),
      warningThresholdMinutes: warningMinutes,
      targetDurationMinutes: targetMinutes,
    });
  }

  return <div className="operations-workspace service-calendar-page">
    <section className="page-header operations-hero">
      <div><div className="page-kicker">Amplifi Internal · Service Governance</div><h1 className="page-title">Service calendars</h1><p className="page-copy">Set the working hours used to calculate support and operational service targets. Only approved, effective versions can run live clocks.</p></div>
      <button className="button" onClick={() => setCreating((value) => !value)} type="button"><Plus size={16} /> New calendar</button>
    </section>

    {creating ? <CalendarCreateForm form={form} setForm={setForm} pending={create.isPending} error={create.error} onSubmit={submitCreate} /> : null}
    {calendars.isLoading ? <LoadingState label="Loading service calendars" /> : null}
    {calendars.error ? <ErrorMessage error={calendars.error} /> : null}
    {calendars.data ? <div className="service-calendar-layout">
      <section className="panel service-calendar-directory">
        <div className="panel-header"><div><h2 className="panel-title"><CalendarClock size={16} /> Calendar versions</h2><div className="panel-subtitle">Global standards and customer-specific exceptions.</div></div><StatusBadge label={`${calendars.data.count} versions`} tone="info" /></div>
        {calendars.data.calendars.length ? <div className="service-calendar-list" role="list">{calendars.data.calendars.map((calendar) => <button className={calendar.calendar_version_id === selected?.calendar_version_id ? "selected" : ""} key={calendar.calendar_version_id} onClick={() => setSelectedRef(calendar.calendar_version_id)} role="listitem" type="button"><span><strong>{calendar.calendar_name}</strong><small>{calendar.scope_type === "GLOBAL" ? "Global standard" : "Customer-specific"} · {calendar.business_timezone}</small></span><StatusBadge label={plain(calendar.lifecycle_status)} tone={statusTone(calendar.lifecycle_status)} /></button>)}</div> : <EmptyState label="No service calendars have been created." />}
      </section>
      {selected ? <section className="panel service-calendar-detail"><CalendarDetail calendar={selected} reason={reason} setReason={setReason} pending={transition.isPending} runAction={runAction} /><PreviewPanel startedAt={startedAt} setStartedAt={setStartedAt} warningMinutes={warningMinutes} setWarningMinutes={setWarningMinutes} targetMinutes={targetMinutes} setTargetMinutes={setTargetMinutes} runPreview={runPreview} pending={preview.isPending} result={preview.data?.preview} error={preview.error} /></section> : null}
    </div> : null}
  </div>;
}

function CalendarDetail({ calendar, reason, setReason, pending, runAction }: { calendar: ServiceCalendar; reason: string; setReason: (value: string) => void; pending: boolean; runAction: (action: "submit-review" | "approve" | "return-to-draft" | "retire") => void }) {
  return <div className="service-calendar-overview">
    <div className="panel-header"><div><h2 className="panel-title">{calendar.calendar_name}</h2><div className="panel-subtitle">{calendar.calendar_code} · version {calendar.version_number}</div></div><StatusBadge label={plain(calendar.lifecycle_status)} tone={statusTone(calendar.lifecycle_status)} /></div>
    <dl className="service-calendar-facts"><div><dt>Applies to</dt><dd>{calendar.scope_type === "GLOBAL" ? "All customers without a specific override" : `Customer ${calendar.account_id}`}</dd></div><div><dt>Timezone</dt><dd>{calendar.business_timezone}</dd></div><div><dt>Effective from</dt><dd>{formatDate(calendar.effective_from)}</dd></div><div><dt>Effective until</dt><dd>{calendar.effective_to ? formatDate(calendar.effective_to) : "No end date"}</dd></div></dl>
    <div className="service-calendar-schedule"><h3>Weekly working hours</h3>{weekdays.map((day, index) => { const intervals = calendar.weekly_intervals.filter((item) => item.local_day_of_week === index + 1); return <div key={day}><span>{day}</span><strong>{intervals.length ? intervals.map((item) => `${shortTime(item.local_start_time)}-${shortTime(item.local_end_time)}`).join(", ") : "Closed"}</strong></div>; })}</div>
    <div className="service-calendar-exceptions"><h3>Closures and exceptions</h3>{calendar.date_exceptions.length ? calendar.date_exceptions.map((item) => <div key={`${item.local_date}-${item.reason_code}`}><span>{item.local_date}</span><strong>{item.exception_type === "CLOSED" ? "Closed" : `${shortTime(item.local_start_time || "")}-${shortTime(item.local_end_time || "")}`} · {plain(item.reason_code)}</strong></div>) : <p>No date exceptions recorded.</p>}</div>
    {calendar.lifecycle_status !== "RETIRED" ? <div className="service-calendar-actions"><label><span>Governance reason</span><input onChange={(event) => setReason(event.target.value)} placeholder="Explain why this change is being made" value={reason} /></label><div>{calendar.lifecycle_status === "DRAFT" ? <button className="button" disabled={pending || !reason.trim()} onClick={() => runAction("submit-review")} type="button"><Check size={15} /> Submit for review</button> : null}{calendar.lifecycle_status === "IN_REVIEW" ? <><button className="button" disabled={pending || !reason.trim()} onClick={() => runAction("approve")} type="button"><ShieldCheck size={15} /> Approve</button><button className="button secondary" disabled={pending || !reason.trim()} onClick={() => runAction("return-to-draft")} type="button"><RotateCcw size={15} /> Return to draft</button></> : null}{calendar.lifecycle_status === "APPROVED" ? <button className="button secondary" disabled={pending || !reason.trim()} onClick={() => runAction("retire")} type="button">Retire version</button> : null}</div></div> : null}
  </div>;
}

function PreviewPanel({ startedAt, setStartedAt, warningMinutes, setWarningMinutes, targetMinutes, setTargetMinutes, runPreview, pending, result, error }: { startedAt: string; setStartedAt: (value: string) => void; warningMinutes: number; setWarningMinutes: (value: number) => void; targetMinutes: number; setTargetMinutes: (value: number) => void; runPreview: () => void; pending: boolean; result?: { startedAt: string; warningAt: string; dueAt: string; businessTimezone: string; clockCreated: boolean }; error: unknown }) {
  return <div className="service-calendar-preview"><div><h3><Clock3 size={16} /> Deadline preview</h3><p>Test how this saved calendar treats an example start time. The server calculates the dates; no service clock is created.</p></div><div className="service-calendar-preview-inputs"><label><span>Example start</span><input type="datetime-local" value={startedAt} onChange={(event) => setStartedAt(event.target.value)} /></label><label><span>Warning after (working minutes)</span><input min="0" type="number" value={warningMinutes} onChange={(event) => setWarningMinutes(Number(event.target.value))} /></label><label><span>Due after (working minutes)</span><input min="1" type="number" value={targetMinutes} onChange={(event) => setTargetMinutes(Number(event.target.value))} /></label><button className="button" disabled={pending} onClick={runPreview} type="button">Preview deadlines</button></div>{error ? <ErrorMessage error={error} /> : null}{result ? <div className="service-calendar-preview-result"><span><small>Example start</small><strong>{formatDate(result.startedAt)}</strong></span><span><small>Warning</small><strong>{formatDate(result.warningAt)}</strong></span><span><small>Due</small><strong>{formatDate(result.dueAt)}</strong></span><p>{result.businessTimezone} calendar · Preview only · No clock created</p></div> : null}</div>;
}

function CalendarCreateForm({ form, setForm, pending, error, onSubmit }: { form: CreateCalendarInput & { effectiveTo: string }; setForm: React.Dispatch<React.SetStateAction<typeof defaultForm>>; pending: boolean; error: unknown; onSubmit: (event: React.FormEvent) => void }) {
  return <form className="panel service-calendar-create" onSubmit={onSubmit}><div className="panel-header"><div><h2 className="panel-title">Create a calendar draft</h2><div className="panel-subtitle">Record working hours and exceptions, then send the saved draft through independent review.</div></div><StatusBadge label="Draft only" tone="warning" /></div><div className="service-calendar-form-grid"><label><span>Name</span><input required value={form.calendarName} onChange={(event) => setForm((value) => ({ ...value, calendarName: event.target.value }))} /></label><label><span>Code</span><input required value={form.calendarCode} onChange={(event) => setForm((value) => ({ ...value, calendarCode: event.target.value }))} /></label><label><span>Scope</span><select value={form.scopeType} onChange={(event) => setForm((value) => ({ ...value, scopeType: event.target.value as "GLOBAL" | "ACCOUNT" }))}><option value="GLOBAL">Global standard</option><option value="ACCOUNT">Customer-specific</option></select></label>{form.scopeType === "ACCOUNT" ? <label><span>Customer account ID</span><input required value={form.accountId || ""} onChange={(event) => setForm((value) => ({ ...value, accountId: event.target.value }))} /></label> : null}<label><span>Business timezone</span><select value={form.businessTimezone} onChange={(event) => setForm((value) => ({ ...value, businessTimezone: event.target.value }))}>{zones.map((zone) => <option key={zone}>{zone}</option>)}</select></label><label><span>Effective from</span><input required type="datetime-local" value={form.effectiveFrom} onChange={(event) => setForm((value) => ({ ...value, effectiveFrom: event.target.value }))} /></label></div><div className="service-calendar-week-editor"><h3>Working week</h3>{weekdays.map((day, index) => { const active = form.weeklyIntervals.some((item) => item.localDayOfWeek === index + 1); const interval = form.weeklyIntervals.find((item) => item.localDayOfWeek === index + 1); return <div key={day}><label><input checked={active} type="checkbox" onChange={(event) => setForm((value) => ({ ...value, weeklyIntervals: event.target.checked ? [...value.weeklyIntervals, { localDayOfWeek: index + 1, localStartTime: "08:00", localEndTime: "17:00" }] : value.weeklyIntervals.filter((item) => item.localDayOfWeek !== index + 1) }))} /> {day}</label>{active ? <><input aria-label={`${day} start`} type="time" value={interval?.localStartTime} onChange={(event) => setForm((value) => ({ ...value, weeklyIntervals: value.weeklyIntervals.map((item) => item.localDayOfWeek === index + 1 ? { ...item, localStartTime: event.target.value } : item) }))} /><input aria-label={`${day} end`} type="time" value={interval?.localEndTime} onChange={(event) => setForm((value) => ({ ...value, weeklyIntervals: value.weeklyIntervals.map((item) => item.localDayOfWeek === index + 1 ? { ...item, localEndTime: event.target.value } : item) }))} /></> : <span>Closed</span>}</div>; })}</div>{error ? <ErrorMessage error={error} /> : null}<button className="button" disabled={pending} type="submit">Save calendar draft</button></form>;
}

const now = new Date(); now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
const defaultForm: CreateCalendarInput & { effectiveTo: string } = { calendarCode: "", scopeType: "GLOBAL", accountId: "", calendarName: "", businessTimezone: "Africa/Johannesburg", effectiveFrom: toLocalInput(now), effectiveTo: "", weeklyIntervals: [1, 2, 3, 4, 5].map((day) => ({ localDayOfWeek: day, localStartTime: "08:00", localEndTime: "17:00" })), dateExceptions: [], metadata: {} };
function toLocalInput(value: Date) { const local = new Date(value.getTime() - value.getTimezoneOffset() * 60000); return local.toISOString().slice(0, 16); }
function formatDate(value: string) { return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)); }
function shortTime(value: string) { return value.slice(0, 5); }
function plain(value: string) { return value.replace(/_/g, " ").toLowerCase(); }
function statusTone(value: string): "success" | "warning" | "info" | "neutral" { return value === "APPROVED" ? "success" : value === "IN_REVIEW" ? "info" : value === "DRAFT" ? "warning" : "neutral"; }
function ErrorMessage({ error }: { error: unknown }) { const message = (error as ApiError | undefined)?.message || "The request could not be completed."; return <div className="operations-error" role="alert">{message}</div>; }
