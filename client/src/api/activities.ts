import { api } from './client';
import type { ConflictInfo } from './calendar';

export interface FormField {
  id?: string;
  label: string;
  field_type: 'text' | 'number' | 'checkbox' | 'boolean' | string;
  is_required: boolean;
  order: number;
}

export interface CustomForm {
  id?: string;
  title: string | null;
  description: string | null;
  fields: FormField[];
}

export interface TrophyResponse {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  points: number;
}

export interface ActivityResponse {
  id: string;
  host_id: string;
  group_id?: string | null;
  title: string;
  description: string | null;
  private_description?: string | null;
  category: string | null;
  latitude: number;
  longitude: number;
  meeting_location?: string | null;
  location_name?: string | null;
  start_time: string;
  end_time: string;
  max_participants: number;
  current_participants: number;
  privacy: string;
  require_approval: boolean;
  created_at: string;
  host?: {
    username: string;
    full_name: string | null;
    avatar_url?: string | null;
  };
  group?: {
    id: string;
    name: string;
    avatar_url?: string | null;
  } | null;
  co_hosts?: Array<{
    id: string;
    name: string;
    avatar_url?: string | null;
  }>;
  distance_meters?: number;
  custom_form?: CustomForm | null;
  trophy?: TrophyResponse | null;
  social_work_days?: number | null;
  conflict_info?: ConflictInfo | null;
  attendance_mode?: 'manual' | 'auto' | 'qr_code';
  check_in_radius?: number;
  attendance_confirmed?: boolean;
  joined_at?: string | null;
}

export interface ActivityCreate {
  title: string;
  description?: string;
  private_description?: string;
  category?: string;
  latitude: number;
  longitude: number;
  meeting_location?: string;
  location_name?: string;
  start_time: string;
  end_time: string;
  max_participants: number;
  privacy?: string;
  require_approval?: boolean;
  social_work_days?: number | null;
  custom_form?: CustomForm;
  trophy_id?: string | null;
  attendance_mode?: 'manual' | 'auto' | 'qr_code';
  check_in_radius?: number;
}

export interface ActivityUpdate {
  title?: string;
  description?: string;
  private_description?: string;
  category?: string;
  latitude?: number;
  longitude?: number;
  meeting_location?: string;
  location_name?: string;
  start_time?: string;
  end_time?: string;
  max_participants?: number;
  privacy?: string;
  require_approval?: boolean;
  social_work_days?: number | null;
  trophy_id?: string | null;
  attendance_mode?: 'manual' | 'auto' | 'qr_code';
  check_in_radius?: number;
  custom_form?: CustomForm | null;
}

export interface NearbyQuery {
  lat: number;
  lng: number;
  radius?: number;
  category?: string;
  search?: string;
  free_to_join?: boolean;
  days_ahead?: number;
  is_ctxh?: boolean;
  has_trophy?: boolean;
  sort_by?: 'distance' | 'time' | 'created_at';
  exclude_my_activities?: boolean;
  limit?: number;
  offset?: number;
  include_conflicts?: boolean;
}

export interface PaginatedActivities {
  items: ActivityResponse[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export const activitiesApi = {
  create: (data: ActivityCreate) =>
    api.post<ActivityResponse>('/activities', data),

  getById: (id: string) =>
    api.get<ActivityResponse>(`/activities/${id}`),

  update: (id: string, data: ActivityUpdate) =>
    api.patch<ActivityResponse>(`/activities/${id}`, data),

  delete: (id: string) =>
    api.delete<void>(`/activities/${id}`),

  list: (params?: { limit?: number; offset?: number; category?: string; search?: string; include_conflicts?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    if (params?.category) query.set('category', params.category);
    if (params?.search) query.set('search', params.search);
    if (params?.include_conflicts) query.set('include_conflicts', 'true');
    return api.get<PaginatedActivities>(`/activities?${query}`);
  },

  nearby: (params: NearbyQuery) => {
    const query = new URLSearchParams({
      lat: String(params.lat),
      lng: String(params.lng),
    });
    if (params.radius) query.set('radius', String(params.radius));
    if (params.category) query.set('category', params.category);
    if (params.search) query.set('search', params.search);
    if (params.free_to_join) query.set('free_to_join', 'true');
    if (params.days_ahead) query.set('days_ahead', String(params.days_ahead));
    if (params.is_ctxh) query.set('is_ctxh', 'true');
    if (params.has_trophy) query.set('has_trophy', 'true');
    if (params.sort_by) query.set('sort_by', params.sort_by);
    if (params.exclude_my_activities !== undefined) {
      query.set('exclude_my_activities', String(params.exclude_my_activities));
    }
    if (params.limit) query.set('limit', String(params.limit));
    if (params.offset !== undefined) query.set('offset', String(params.offset));
    if (params.include_conflicts) query.set('include_conflicts', 'true');
    return api.get<PaginatedActivities>(`/activities/nearby?${query}`);
  },

  getJoinedActivities: (params?: { status?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    return api.get<PaginatedActivities>(`/activities/joined?${query}`);
  },

  getMyActivities: (params?: { status?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    return api.get<PaginatedActivities>(`/activities/mine?${query}`);
  },

  getCheckInCode: (activityId: string) =>
    api.get<{
      check_in_code: string;
      rotating_token: string;
      expires_in_seconds: number;
      check_in_radius: number;
    }>(`/activities/${activityId}/check-in-code`),

  checkIn: (activityId: string, data: { code: string; latitude?: number; longitude?: number; accuracy?: number }) =>
    api.post<{
      message: string;
      attendance_confirmed: boolean;
      trophy_awarded: boolean;
      already_confirmed?: boolean;
    }>(`/activities/${activityId}/check-in`, data),

  updateAttendance: (activityId: string, userId: string, attended: boolean) =>
    api.patch<{
      message: string;
      attendance_confirmed: boolean;
      trophy_awarded: boolean;
    }>(`/activities/${activityId}/participants/${userId}/attendance`, { attended }),

  exportParticipantsCsv: (activityId: string) =>
    api.getBlob(`/activities/${activityId}/participants/export`),
};
