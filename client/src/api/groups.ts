import { api } from './client';
import type { ActivityResponse } from './activities';
import type { DocumentResponse } from './documents';

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
  allow_member_activities?: boolean;
  allow_member_documents?: boolean;
}

export interface GroupCreate extends GroupBase {
  name: string; // making it required here
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
}

export const groupsApi = {
  createGroup: (data: GroupCreate) => 
    api.post<GroupResponse>('/groups', data),

  updateGroup: (id: string, data: GroupUpdate) =>
    api.patch<GroupResponse>(`/groups/${id}`, data),

  getMyGroups: () => 
    api.get<GroupResponse[]>('/groups/my'),

  discoverGroups: () => 
    api.get<GroupResponse[]>('/groups/discover'),

  getGroup: (id: string) => 
    api.get<GroupDetailResponse>(`/groups/${id}`),

  joinGroup: (id: string) => 
    api.post(`/groups/${id}/join`),

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

  getGroupDocuments: (id: string, params?: { limit?: number; offset?: number }) => {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    const queryStr = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return api.get<{items: DocumentResponse[], total: number, has_more: boolean}>(`/groups/${id}/documents${queryStr}`);
  },
};
