import { api } from './client';

export interface TrophyCreate {
  name: string;
  description?: string;
  points?: number;
  icon?: string;
}

export interface TrophyResponse {
  id: string;
  name: string;
  description?: string | null;
  points: number;
  icon?: string | null;
  creator_id: string;
  created_at: string;
}

export interface UserTrophyResponse {
  id: string;
  user_id: string;
  trophy: TrophyResponse;
  activity_id?: string | null;
  activity?: {
    id: string | null;
    title: string;
    privacy?: string;
    is_accessible?: boolean;
  } | null;
  created_at: string;
}

export const trophiesApi = {
  list: () => api.get<TrophyResponse[]>('/trophies'),

  create: (data: TrophyCreate) => api.post<TrophyResponse>('/trophies', data),

  getUserTrophies: (userId: string) => api.get<UserTrophyResponse[]>(`/trophies/user/${userId}`),

  award: (trophyId: string, data: { user_id: string; activity_id?: string }) =>
    api.post<UserTrophyResponse>(`/trophies/${trophyId}/award`, data),
};
