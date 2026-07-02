import { api } from './client';

export interface JoinRequestResponse {
  id: string;
  activity_id: string;
  user_id: string;
  status: 'pending' | 'approved' | 'declined' | 'cancelled';
  message: string | null;
  responded_at: string | null;
  created_at: string;
  user?: {
    username: string;
    full_name: string | null;
  };
}

export interface JoinRequestCreate {
  message?: string;
}

export const participationApi = {
  requestToJoin: (activityId: string, data?: JoinRequestCreate) =>
    api.post<JoinRequestResponse>(`/activities/${activityId}/join`, data),

  listByActivity: (activityId: string) =>
    api.get<JoinRequestResponse[]>(`/activities/${activityId}/requests`),

  approve: (requestId: string) =>
    api.patch<JoinRequestResponse>(`/join-requests/${requestId}/approve`),

  decline: (requestId: string) =>
    api.patch<JoinRequestResponse>(`/join-requests/${requestId}/decline`),

  cancel: (requestId: string) =>
    api.patch<JoinRequestResponse>(`/join-requests/${requestId}/cancel`),

  leaveActivity: (activityId: string) =>
    api.post<void>(`/activities/${activityId}/leave`),
};
