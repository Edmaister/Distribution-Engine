import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createServiceCalendar,
  listServiceCalendars,
  previewServiceCalendar,
  transitionServiceCalendar,
  type CreateCalendarInput,
} from "./endpoints/referralSaasServiceCalendars";

const calendarKey = ["referral-saas", "service-calendars"] as const;

export function useServiceCalendars(refreshKey = 0) {
  return useQuery({ queryKey: [...calendarKey, refreshKey], queryFn: listServiceCalendars, retry: false });
}

export function useCreateServiceCalendar() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateCalendarInput) => createServiceCalendar(input),
    onSuccess: () => client.invalidateQueries({ queryKey: calendarKey }),
  });
}

export function useTransitionServiceCalendar() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { calendarRef: string; action: "submit-review" | "approve" | "return-to-draft" | "retire"; reason: string }) =>
      transitionServiceCalendar(input.calendarRef, input.action, input.reason),
    onSuccess: () => client.invalidateQueries({ queryKey: calendarKey }),
  });
}

export function usePreviewServiceCalendar() {
  return useMutation({
    mutationFn: (input: { calendarRef: string; startedAt: string; warningThresholdMinutes: number; targetDurationMinutes: number }) =>
      previewServiceCalendar(input.calendarRef, input),
  });
}
