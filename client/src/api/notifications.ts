import { api } from './client';

export interface UserInfo {
  id: string;
  username: string;
  full_name: string | null;
  avatar_url?: string | null;
}

export interface NotificationResponse {
  id: string;
  user_id: string;
  actor_id: string | null;
  activity_id?: string | null;
  type: string;
  target_type?: string;
  target_id?: string;
  message: string;
  is_read: boolean;
  created_at: string;
  actor: UserInfo & { avatar_url?: string } | null;
}

export interface NotificationListResponse {
  items: NotificationResponse[];
  total: number;
  unread_count: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export const notificationsApi = {
  listNotifications: (params?: { limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    const qs = query.toString();
    return api.get<NotificationListResponse>(`/notifications${qs ? `?${qs}` : ''}`);
  },

  markAsRead: (id: string) =>
    api.patch<NotificationResponse>(`/notifications/${id}/read`),

  markAllAsRead: () =>
    api.patch<{ status: string; updated_count: number }>('/notifications/read-all'),
};
