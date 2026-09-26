import { api } from './client';

export interface JoinRequestResponse {
  id: string;
  activity_id: string;
  user_id: string;
  status: 'pending' | 'approved' | 'declined' | 'cancelled';
  message: string | null;
  responded_at: string | null;
  created_at: string;
  form_responses?: Record<string, any>;
  attendance_confirmed?: boolean;
  user?: {
    username: string;
    full_name: string | null;
  };
}

export interface JoinRequestCreate {
  message?: string;
  form_responses?: Record<string, any>;
}

export interface CertificateCustomField {
  label: string;
  value: string;
}

export interface CertificateResponse {
  certificate_code: string;
  activity_id: string;
  user_id: string;
  participant_name: string;
  participant_username: string;
  participant_email?: string | null;
  participant_university?: string | null;
  activity_title: string;
  activity_date: string;
  meeting_location?: string | null;
  location_name?: string | null;
  host_id?: string | null;
  host_name: string;
  host_university?: string | null;
  group_id?: string | null;
  group_name?: string | null;
  group_is_private?: boolean;
  social_work_days?: number | null;
  trophy_name?: string | null;
  trophy_icon?: string | null;
  trophy_points?: number | null;
  custom_fields?: CertificateCustomField[];
  issued_at: string;
  verification_url: string;
  is_host?: boolean;
}

export const participationApi = {
  requestToJoin: (activityId: string, data?: JoinRequestCreate, confirmSwap?: boolean) =>
    api.post<JoinRequestResponse>(
      `/activities/${activityId}/join${confirmSwap ? '?confirm_swap=true' : ''}`,
      data
    ),

  listByActivity: (activityId: string) =>
    api.get<JoinRequestResponse[]>(`/activities/${activityId}/requests`),
    
  listParticipants: (activityId: string) =>
    api.get<JoinRequestResponse[]>(`/activities/${activityId}/participants`),

  approve: (requestId: string) =>
    api.patch<JoinRequestResponse>(`/join-requests/${requestId}/approve`),

  decline: (requestId: string) =>
    api.patch<JoinRequestResponse>(`/join-requests/${requestId}/decline`),

  cancel: (requestId: string) =>
    api.patch<JoinRequestResponse>(`/join-requests/${requestId}/cancel`),

  leaveActivity: (activityId: string) =>
    api.post<void>(`/activities/${activityId}/leave`),

  removeParticipant: (activityId: string, userId: string) =>
    api.delete<{ message: string }>(`/activities/${activityId}/participants/${userId}`),

  getCertificate: (activityId: string, userId?: string) =>
    api.get<CertificateResponse>(
      `/activities/${activityId}/certificate${userId ? `?user_id=${userId}` : ''}`
    ),

  verifyCertificate: (code: string) =>
    api.get<CertificateResponse>(`/certificates/verify/${code}`),
};
