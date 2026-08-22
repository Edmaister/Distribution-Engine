import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  useCreateServiceCalendar,
  usePreviewServiceCalendar,
  useServiceCalendars,
  useTransitionServiceCalendar,
} from "../../api/referralSaasCalendarQueries";
import { ReferralSaasServiceCalendarsPage } from "./ReferralSaasServiceCalendarsPage";

vi.mock("../../api/referralSaasCalendarQueries", () => ({
  useServiceCalendars: vi.fn(),
  useCreateServiceCalendar: vi.fn(),
  useTransitionServiceCalendar: vi.fn(),
  usePreviewServiceCalendar: vi.fn(),
}));

const calendar = {
  calendar_version_id: "calendar-1", calendar_code: "SUPPORT_ZA", version_number: 2,
  scope_type: "GLOBAL" as const, account_id: null, calendar_name: "South Africa support hours",
  business_timezone: "Africa/Johannesburg", lifecycle_status: "DRAFT" as const,
  effective_from: "2026-08-22T00:00:00Z", effective_to: null,
  weekly_intervals: [{ local_day_of_week: 1, local_start_time: "08:00:00", local_end_time: "17:00:00" }],
  date_exceptions: [{ local_date: "2026-12-25", exception_type: "CLOSED" as const, local_start_time: null, local_end_time: null, reason_code: "PUBLIC_HOLIDAY" }],
};

describe("ReferralSaasServiceCalendarsPage", () => {
  afterEach(cleanup);
  it("shows governed calendar context and delegates preview calculation to the API", () => {
    const preview = vi.fn();
    vi.mocked(useServiceCalendars).mockReturnValue({ data: { status: "ok", calendars: [calendar], count: 1 }, isLoading: false, error: null } as ReturnType<typeof useServiceCalendars>);
    vi.mocked(useCreateServiceCalendar).mockReturnValue({ mutate: vi.fn(), isPending: false, error: null } as unknown as ReturnType<typeof useCreateServiceCalendar>);
    vi.mocked(useTransitionServiceCalendar).mockReturnValue({ mutate: vi.fn(), isPending: false } as unknown as ReturnType<typeof useTransitionServiceCalendar>);
    vi.mocked(usePreviewServiceCalendar).mockReturnValue({ mutate: preview, isPending: false, data: undefined, error: null } as unknown as ReturnType<typeof usePreviewServiceCalendar>);
    render(<MemoryRouter><ReferralSaasServiceCalendarsPage /></MemoryRouter>);
    expect(screen.getByText("Global standard · Africa/Johannesburg")).toBeInTheDocument();
    expect(screen.getByText("All customers without a specific override")).toBeInTheDocument();
    expect(screen.getByText(/no service clock is created/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Preview deadlines" }));
    expect(preview).toHaveBeenCalledWith(expect.objectContaining({ calendarRef: "calendar-1", targetDurationMinutes: 480 }));
  });
});
