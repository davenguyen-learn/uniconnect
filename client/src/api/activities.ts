import { api } from './client';

export interface ActivityResponse {
  id: string;
  host_id: string;
  title: string;
  description: string | null;
  category: string | null;
  latitude: number;
  longitude: number;
  location_name: string | null;
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
  };
  distance_meters?: number;
}

export interface ActivityCreate {
  title: string;
  description?: string;
  category?: string;
  latitude: number;
  longitude: number;
  location_name?: string;
  start_time: string;
  end_time: string;
  max_participants: number;
  privacy?: string;
  require_approval?: boolean;
}

export interface ActivityUpdate {
  title?: string;
  description?: string;
  category?: string;
  latitude?: number;
  longitude?: number;
  location_name?: string;
  start_time?: string;
  end_time?: string;
  max_participants?: number;
  privacy?: string;
  require_approval?: boolean;
}

export interface NearbyQuery {
  lat: number;
  lng: number;
  radius?: number;
  category?: string;
  search?: string;
  free_to_join?: boolean;
  limit?: number;
  offset?: number;
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

  list: (params?: { limit?: number; offset?: number; category?: string }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    if (params?.category) query.set('category', params.category);
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
    if (params.limit) query.set('limit', String(params.limit));
    if (params.offset) query.set('offset', String(params.offset));
    return api.get<PaginatedActivities>(`/activities/nearby?${query}`);
  },

  getJoinedActivities: (params?: { limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    return api.get<PaginatedActivities>(`/activities/joined?${query}`);
  },

  getMyActivities: (params?: { limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    return api.get<PaginatedActivities>(`/activities/mine?${query}`);
  },
};
