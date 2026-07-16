import { api } from './client';

// ── Types ──

export interface AdminStats {
  total_users: number;
  total_activities: number;
  total_documents: number;
  total_reports: number;
  pending_reports: number;
  new_users_this_week: number;
}

export interface AdminUserItem {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  university: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface AdminUserList {
  items: AdminUserItem[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface ReportReporterInfo {
  id: string;
  username: string;
  full_name: string | null;
  email: string;
}

export interface AdminReportItem {
  id: string;
  reporter_id: string;
  target_type: string;
  target_id: string;
  reason: string;
  description: string | null;
  status: string;
  admin_note: string | null;
  resolved_by: string | null;
  created_at: string;
  updated_at: string;
  reporter: ReportReporterInfo | null;
}

export interface AdminReportList {
  items: AdminReportItem[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface AdminActivityItem {
  id: string;
  host_id: string;
  title: string;
  description: string | null;
  category: string | null;
  location_name: string | null;
  start_time: string;
  end_time: string;
  max_participants: number;
  current_participants: number;
  privacy: string;
  created_at: string;
  host_username: string | null;
}

export interface AdminActivityList {
  items: AdminActivityItem[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface AdminDocumentItem {
  id: string;
  author_id: string;
  title: string;
  description: string | null;
  file_name: string;
  file_size: number;
  file_type: string;
  is_deleted: boolean;
  created_at: string;
  author_username: string | null;
}

export interface AdminDocumentList {
  items: AdminDocumentItem[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

// ── API Functions ──

const buildQuery = (params: Record<string, unknown>): string => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, String(value));
    }
  });
  const qs = query.toString();
  return qs ? `?${qs}` : '';
};

export const adminApi = {
  // Dashboard
  getStats: () =>
    api.get<AdminStats>('/admin/stats'),

  // Users
  listUsers: (params?: { search?: string; role?: string; is_active?: boolean; limit?: number; offset?: number }) =>
    api.get<AdminUserList>(`/admin/users${buildQuery(params || {})}`),

  updateUserRole: (userId: string, role: string) =>
    api.patch<AdminUserItem>(`/admin/users/${userId}/role`, { role }),

  updateUserStatus: (userId: string, is_active: boolean) =>
    api.patch<AdminUserItem>(`/admin/users/${userId}/status`, { is_active }),

  // Reports
  listReports: (params?: { status?: string; target_type?: string; limit?: number; offset?: number }) =>
    api.get<AdminReportList>(`/admin/reports${buildQuery(params || {})}`),

  updateReport: (reportId: string, data: { status: string; admin_note?: string }) =>
    api.patch<AdminReportItem>(`/admin/reports/${reportId}`, data),

  // Activities
  listActivities: (params?: { search?: string; limit?: number; offset?: number }) =>
    api.get<AdminActivityList>(`/admin/activities${buildQuery(params || {})}`),

  deleteActivity: (activityId: string) =>
    api.delete(`/admin/activities/${activityId}`),

  // Documents
  listDocuments: (params?: { search?: string; limit?: number; offset?: number }) =>
    api.get<AdminDocumentList>(`/admin/documents${buildQuery(params || {})}`),

  deleteDocument: (documentId: string) =>
    api.delete(`/admin/documents/${documentId}`),
};
