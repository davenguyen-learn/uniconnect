import { api } from './client';
import type { ActivityResponse } from './activities';

export interface GroupMemberResponse {
  user_id: string;
  role: 'owner' | 'admin' | 'member';
  joined_at: string;
  username?: string;
  full_name?: string;
}

export interface GroupBase {
  name: string;
  description?: string;
  public_description?: string;
  private_description?: string;
  allow_member_activities?: boolean;
  require_approval?: boolean;
  privacy?: 'public' | 'private';
}

export interface GroupCreate extends GroupBase {
  name: string;
  custom_form?: any;
}

export interface GroupUpdate extends GroupBase {}

export interface GroupResponse extends GroupBase {
  id: string;
  owner_id: string;
  created_at: string;
  member_count: number;
}

export interface GroupDetailResponse extends GroupResponse {
  members: GroupMemberResponse[];
  custom_form?: any;
}

export interface GroupStatsResponse {
  group_id: string;
  member_count: number;
  total_activities_count: number;
  total_ctxh_contributed: number;
}

export interface GroupJoinRequestResponse {
  id: string;
  group_id: string;
  user_id: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  username?: string;
  full_name?: string;
  form_responses?: Record<string, any>;
}

export interface CoHostInvitationResponse {
  id: string;
  activity_id: string;
  activity_title?: string;
  host_group_id: string;
  host_group_name?: string;
  invited_group_id: string;
  invited_group_name?: string;
  status: 'pending' | 'accepted' | 'declined';
  message?: string;
  created_at: string;
}

export const groupsApi = {
  createGroup: (data: GroupCreate) => 
    api.post<GroupResponse>('/groups', data),

  updateGroup: (id: string, data: GroupUpdate) =>
    api.patch<GroupResponse>(`/groups/${id}`, data),

  getMyGroups: () => 
    api.get<GroupResponse[]>('/groups/my'),

  discoverGroups: (params?: { search?: string; sort_by?: string; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.search) query.set('search', params.search);
    if (params?.sort_by) query.set('sort_by', params.sort_by);
    if (params?.limit) query.set('limit', String(params.limit));
    const qs = query.toString();
    return api.get<GroupResponse[]>(`/groups/discover${qs ? `?${qs}` : ''}`);
  },

  getGroup: (id: string) => 
    api.get<GroupDetailResponse>(`/groups/${id}`),

  getGroupStats: (id: string) =>
    api.get<GroupStatsResponse>(`/groups/${id}/stats`),

  getGroupMembers: (id: string, params?: { limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    const qs = query.toString();
    return api.get<GroupMemberResponse[]>(`/groups/${id}/members${qs ? `?${qs}` : ''}`);
  },

  getJoinRequests: (id: string, params?: { status?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    const qs = query.toString();
    return api.get<GroupJoinRequestResponse[]>(`/groups/${id}/join-requests${qs ? `?${qs}` : ''}`);
  },

  actionJoinRequest: (id: string, requestId: string, action: 'approved' | 'rejected') =>
    api.post<GroupJoinRequestResponse>(`/groups/${id}/join-requests/${requestId}/action`, { action }),

  getCoHostInvitations: (id: string, params?: { status?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    const qs = query.toString();
    return api.get<CoHostInvitationResponse[]>(`/groups/${id}/co-host-invitations${qs ? `?${qs}` : ''}`);
  },

  respondCoHostInvitation: (invitationId: string, action: 'accepted' | 'declined') =>
    api.post<CoHostInvitationResponse>(`/groups/co-host-invitations/${invitationId}/respond`, { action }),

  inviteCoHost: (activityId: string, data: { invited_group_id: string; message?: string }) =>
    api.post<CoHostInvitationResponse>(`/activities/${activityId}/invite-cohost`, data),

  joinGroup: (id: string, payload?: { form_responses?: Record<string, any> }) => 
    api.post(`/groups/${id}/join`, payload),

  leaveGroup: (id: string) => 
    api.post(`/groups/${id}/leave`),

  getGroupActivities: (id: string, params?: { category?: string; limit?: number; offset?: number }) => {
    const queryParams = new URLSearchParams();
    if (params?.category) queryParams.append('category', params.category);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    const queryStr = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return api.get<{items: ActivityResponse[], total: number, has_more: boolean}>(`/groups/${id}/activities${queryStr}`);
  },
};

