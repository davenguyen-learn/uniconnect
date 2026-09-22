import type { CalendarEventItem, BusySlotResponse } from '../api/calendar';

export const DAYS_OF_WEEK_VI = [
  'Thứ Hai',
  'Thứ Ba',
  'Thứ Tư',
  'Thứ Năm',
  'Thứ Sáu',
  'Thứ Bảy',
  'Chủ Nhật',
];

export const DAYS_OF_WEEK_SHORT_VI = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

export interface CalendarEventViewModel {
  id: string;
  title: string;
  startTime: string;
  endTime: string;
  timeRange: string;
  dateKey: string; // YYYY-MM-DD
  dateDisplay: string; // e.g. "Thứ Ba, 20/09"
  eventType: 'busy_slot' | 'activity_joined' | 'activity_hosted';
  typeLabel: string;
  colorTag: 'busy' | 'joined' | 'hosted';
  isRecurring: boolean;
  activityId?: string | null;
  category?: string | null;
  locationName?: string | null;
  rawEvent: CalendarEventItem;
}

export interface AgendaDayGroup {
  dateKey: string; // YYYY-MM-DD
  dateTitle: string; // "Hôm nay (Thứ Ba, 20/09)" or "Thứ Tư, 21/09"
  isToday: boolean;
  events: CalendarEventViewModel[];
}

export interface BusySlotRuleViewModel {
  id: string;
  title: string;
  recurrence: 'none' | 'weekly';
  recurrenceLabel: string;
  timeRange: string;
  validityRange: string;
  rawSlot: BusySlotResponse;
}

export function formatTimeRange(startIso: string, endIso: string): string {
  try {
    const s = new Date(startIso);
    const e = new Date(endIso);
    const startStr = s.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    const endStr = e.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    return `${startStr} - ${endStr}`;
  } catch {
    return '';
  }
}

export function formatDateKey(date: Date): string {
  return date.toISOString().split('T')[0];
}

export function formatDateDisplay(dateIso: string): string {
  try {
    const d = new Date(dateIso);
    const dayOfWeek = d.getDay(); // 0 is Sunday
    const viDay = dayOfWeek === 0 ? 'Chủ Nhật' : `Thứ ${dayOfWeek + 1}`;
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    return `${viDay}, ${day}/${month}`;
  } catch {
    return dateIso;
  }
}

export function mapCalendarEventToViewModel(event: CalendarEventItem): CalendarEventViewModel {
  const d = new Date(event.start_time);
  const dateKey = !isNaN(d.getTime()) ? d.toISOString().split('T')[0] : '';
  
  let typeLabel = 'Lịch bận cá nhân';
  if (event.event_type === 'activity_joined') {
    typeLabel = 'Hoạt động đã đăng ký';
  } else if (event.event_type === 'activity_hosted') {
    typeLabel = 'Hoạt động Host chủ trì';
  }

  return {
    id: event.id,
    title: event.title,
    startTime: event.start_time,
    endTime: event.end_time,
    timeRange: formatTimeRange(event.start_time, event.end_time),
    dateKey,
    dateDisplay: formatDateDisplay(event.start_time),
    eventType: event.event_type,
    typeLabel,
    colorTag: event.color_tag,
    isRecurring: event.is_recurring,
    activityId: event.activity_id,
    category: event.category,
    locationName: event.meeting_location || event.location_name,
    rawEvent: event,
  };
}

export function groupEventsByDate(events: CalendarEventViewModel[]): AgendaDayGroup[] {
  const map = new Map<string, CalendarEventViewModel[]>();
  const todayKey = formatDateKey(new Date());

  for (const ev of events) {
    if (!ev.dateKey) continue;
    const list = map.get(ev.dateKey) || [];
    list.push(ev);
    map.set(ev.dateKey, list);
  }

  const sortedDateKeys = Array.from(map.keys()).sort();

  return sortedDateKeys.map((k) => {
    const isToday = k === todayKey;
    const sampleDate = new Date(`${k}T00:00:00`);
    const dateTitle = isToday
      ? `Hôm nay (${formatDateDisplay(sampleDate.toISOString())})`
      : formatDateDisplay(sampleDate.toISOString());

    // Sort events inside the day by start time
    const dayEvents = (map.get(k) || []).sort(
      (a, b) => new Date(a.startTime).getTime() - new Date(b.startTime).getTime()
    );

    return {
      dateKey: k,
      dateTitle,
      isToday,
      events: dayEvents,
    };
  });
}

export function mapBusySlotToRuleViewModel(slot: BusySlotResponse): BusySlotRuleViewModel {
  const isWeekly = slot.recurrence === 'weekly';
  let recurrenceLabel = 'Bận 1 lần duy nhất';
  let timeRange = '';

  if (isWeekly && slot.day_of_week !== null && slot.day_of_week !== undefined) {
    const dayName = DAYS_OF_WEEK_VI[slot.day_of_week] || `Thứ ${slot.day_of_week + 1}`;
    recurrenceLabel = `Lặp hàng tuần (${dayName})`;
    timeRange = `${slot.start_time_of_day || ''} - ${slot.end_time_of_day || ''}`;
  } else if (slot.start_datetime && slot.end_datetime) {
    timeRange = `${formatDateDisplay(slot.start_datetime)} (${formatTimeRange(slot.start_datetime, slot.end_datetime)})`;
  }

  let validityRange = 'Không thời hạn';
  if (slot.valid_from && slot.valid_until) {
    validityRange = `${slot.valid_from} → ${slot.valid_until}`;
  } else if (slot.valid_from) {
    validityRange = `Từ ${slot.valid_from}`;
  } else if (slot.valid_until) {
    validityRange = `Đến ${slot.valid_until}`;
  }

  return {
    id: slot.id,
    title: slot.title,
    recurrence: isWeekly ? 'weekly' : 'none',
    recurrenceLabel,
    timeRange,
    validityRange,
    rawSlot: slot,
  };
}
