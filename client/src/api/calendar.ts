import { api } from './client';

export interface CalendarEventItem {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  event_type: 'busy_slot' | 'activity_joined' | 'activity_hosted';
  activity_id?: string | null;
  category?: string | null;
  meeting_location?: string | null;
  location_name?: string | null;
  is_recurring: boolean;
  color_tag: 'busy' | 'joined' | 'hosted';
}

export interface BusySlotCreate {
  title: string;
  recurrence: 'none' | 'weekly';
  start_datetime?: string | null;
  end_datetime?: string | null;
  day_of_week?: number | null;
  start_time_of_day?: string | null;
  end_time_of_day?: string | null;
  valid_from?: string | null;
  valid_until?: string | null;
}

export interface BusySlotResponse {
  id: string;
  user_id: string;
  title: string;
  recurrence: string;
  start_datetime?: string | null;
  end_datetime?: string | null;
  day_of_week?: number | null;
  start_time_of_day?: string | null;
  end_time_of_day?: string | null;
  valid_from?: string | null;
  valid_until?: string | null;
  exception_dates?: string[];
}

export interface ConflictDetail {
  type: 'busy_slot' | 'approved_activity' | 'hosted_activity' | 'pending_request';
  title: string;
  time_range: string;
  target_id?: string | null;
}

export interface ConflictInfo {
  has_conflict: boolean;
  level: 'none' | 'soft_conflict' | 'hard_conflict';
  can_join: boolean;
  warning_message?: string | null;
  conflicting_with?: ConflictDetail | null;
  swap_candidate?: {
    join_request_id: string;
    activity_id: string;
    title: string;
  } | null;
}

export interface ConflictCheckRequest {
  start_time: string;
  end_time: string;
  exclude_activity_id?: string | null;
}

export interface ReschedulePreviewRequest {
  new_start_time: string;
  new_end_time: string;
}

export interface ConflictedMemberInfo {
  user_id: string;
  full_name: string;
  conflict_type: 'busy_slot' | 'other_activity';
  reason: string;
}

export interface ReschedulePreviewResponse {
  total_participants: number;
  conflicted_count: number;
  safe_to_reschedule: boolean;
  free_percentage: number;
  conflicted_members: ConflictedMemberInfo[];
}

export const calendarApi = {
  getEvents: (startDate?: string, endDate?: string) => {
    const query = new URLSearchParams();
    if (startDate) query.set('start_date', startDate);
    if (endDate) query.set('end_date', endDate);
    return api.get<CalendarEventItem[]>(`/calendar/events?${query}`);
  },

  listBusySlots: () => api.get<BusySlotResponse[]>('/calendar/busy-slots'),

  createBusySlot: (data: BusySlotCreate) =>
    api.post<BusySlotResponse>('/calendar/busy-slots', data),

  deleteBusySlot: (slotId: string) =>
    api.delete<void>(`/calendar/busy-slots/${slotId}`),

  checkConflict: (data: ConflictCheckRequest) =>
    api.post<ConflictInfo>('/calendar/check-conflict', data),

  previewReschedule: (activityId: string, data: ReschedulePreviewRequest) =>
    api.post<ReschedulePreviewResponse>(`/activities/${activityId}/preview-reschedule`, data),
};
