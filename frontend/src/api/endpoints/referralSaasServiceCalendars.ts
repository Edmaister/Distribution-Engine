import { apiRequest } from "../client";

export type CalendarInterval = {
  local_day_of_week: number;
  local_start_time: string;
  local_end_time: string;
};

export type CalendarException = {
  local_date: string;
  exception_type: "CLOSED" | "WORKING_INTERVAL";
  local_start_time: string | null;
  local_end_time: string | null;
  reason_code: string;
};

export type ServiceCalendar = {
  calendar_version_id: string;
  calendar_code: string;
  version_number: number;
  scope_type: "GLOBAL" | "ACCOUNT";
  account_id: string | null;
  calendar_name: string;
  business_timezone: string;
  lifecycle_status: "DRAFT" | "IN_REVIEW" | "APPROVED" | "RETIRED";
  effective_from: string;
  effective_to: string | null;
  weekly_intervals: CalendarInterval[];
  date_exceptions: CalendarException[];
};

type CalendarResponse = { status: string; calendar: ServiceCalendar };
export type CalendarListResponse = { status: string; calendars: ServiceCalendar[]; count: number };
export type CalendarPreviewResponse = {
  status: string;
  preview: {
    calendarRef: string;
    calendarCode: string;
    versionNumber: number;
    lifecycleStatus: string;
    businessTimezone: string;
    startedAt: string;
    warningAt: string;
    dueAt: string;
    warningThresholdMinutes: number;
    targetDurationMinutes: number;
    calculationMode: string;
    clockCreated: boolean;
  };
};

export type CreateCalendarInput = {
  calendarCode: string;
  scopeType: "GLOBAL" | "ACCOUNT";
  accountId?: string;
  calendarName: string;
  businessTimezone: string;
  effectiveFrom: string;
  effectiveTo?: string;
  weeklyIntervals: Array<{ localDayOfWeek: number; localStartTime: string; localEndTime: string }>;
  dateExceptions: Array<{
    localDate: string;
    exceptionType: "CLOSED" | "WORKING_INTERVAL";
    localStartTime?: string;
    localEndTime?: string;
    reasonCode: string;
  }>;
  metadata: Record<string, unknown>;
};

export function listServiceCalendars() {
  return apiRequest<CalendarListResponse>("/v1/referral-saas/service-target-calendars");
}

export function createServiceCalendar(input: CreateCalendarInput) {
  return apiRequest<CalendarResponse>("/v1/referral-saas/service-target-calendars", {
    method: "POST",
    body: { ...input, idempotencyKey: crypto.randomUUID() },
  });
}

export function transitionServiceCalendar(
  calendarRef: string,
  action: "submit-review" | "approve" | "return-to-draft" | "retire",
  reason: string,
) {
  return apiRequest<CalendarResponse>(`/v1/referral-saas/service-target-calendars/${calendarRef}/${action}`, {
    method: "POST",
    body: { reason, idempotencyKey: crypto.randomUUID() },
  });
}

export function previewServiceCalendar(
  calendarRef: string,
  input: { startedAt: string; warningThresholdMinutes: number; targetDurationMinutes: number },
) {
  return apiRequest<CalendarPreviewResponse>(
    `/v1/referral-saas/service-target-calendars/${calendarRef}/calculation-preview`,
    { method: "POST", body: input },
  );
}
