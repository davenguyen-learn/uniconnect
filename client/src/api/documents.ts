import { api } from './client';
export interface UserInfo {
  username: string;
  full_name: string | null;
}

export interface GroupInfo {
  id: string;
  name: string;
}

export interface DocumentResponse {
  id: string;
  author_id: string;
  group_id: string | null;
  title: string;
  description: string | null;
  file_name: string;
  file_size: number;
  file_type: string;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  author: UserInfo | null;
  group: GroupInfo | null;
}

export interface DocumentListResponse {
  items: DocumentResponse[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export const documentsApi = {
  uploadDocument: (formData: FormData) =>
    api.post<DocumentResponse>('/documents', formData),

  listDocuments: (params?: { group_id?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.group_id) query.set('group_id', params.group_id);
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    const qs = query.toString();
    return api.get<DocumentListResponse>(`/documents${qs ? `?${qs}` : ''}`);
  },

  listGroupDocuments: (groupId: string, params?: { limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    const qs = query.toString();
    return api.get<DocumentListResponse>(`/groups/${groupId}/documents${qs ? `?${qs}` : ''}`);
  },

  getDocument: (id: string) =>
    api.get<DocumentResponse>(`/documents/${id}`),

  updateDocument: (id: string, data: { title?: string; description?: string }) =>
    api.patch<DocumentResponse>(`/documents/${id}`, data),

  deleteDocument: (id: string) =>
    api.delete<void>(`/documents/${id}`),

  getDownloadUrl: (id: string) =>
    api.get<{ url: string }>(`/documents/${id}/download`),
};
