import { api } from './client';

// ── Types ──

export interface KPICardDTO {
  label: string;
  value: number;
  formatted_value: string;
  delta_percent: number | null;
  trend: number[];
  unit: string | null;
}

export interface AdminMetricsDTO {
  total_ctxh: KPICardDTO;
  attendance_rate: KPICardDTO;
  active_users: KPICardDTO;
  monthly_growth: KPICardDTO;
  dau: number;
  mau: number;
  total_users: number;
  total_activities: number;
  last_updated: string;
}

export interface AdminStats {
  total_users: number;
  total_activities: number;
  total_reports: number;
  pending_reports: number;
  new_users_this_week: number;
}

export interface StudentAuditItemDTO {
  id: string;
  username: string;
  full_name: string | null;
  email: string;
  university: string | null;
  is_active: boolean;
  is_verified: boolean;
  role: string;
  confirmed_ctxh_days: number;
  attendance_count: number;
  created_at: string;
}

export interface StudentAuditListDTO {
  items: StudentAuditItemDTO[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface VerificationItemDTO {
  id: string;
  user_id: string;
  organization_name: string;
  faculty: string | null;
  document_url: string | null;
  description: string | null;
  status: 'pending' | 'approved' | 'rejected';
  admin_note: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string | null;
  applicant_name: string | null;
  applicant_email: string | null;
}

export interface VerificationListDTO {
  items: VerificationItemDTO[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface VerificationRequestCreateDTO {
  organization_name: string;
  faculty?: string;
  document_url?: string;
  description?: string;
}

export interface VerificationReviewActionDTO {
  action: 'approve' | 'reject';
  admin_note?: string;
}

export interface ReportReviewActionDTO {
  action: 'resolve' | 'dismiss';
  admin_note?: string;
  hide_activity?: boolean;
  deactivate_user?: boolean;
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
  reporter?: ReportReporterInfo | null;
  reporter_name?: string | null;
}

export interface AdminReportList {
  items: AdminReportItem[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface AdminAuditLogItemDTO {
  id: string;
  actor_id: string | null;
  action: string;
  target_type: string;
  target_id: string;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
  actor_username: string | null;
}

export interface AdminAuditLogListDTO {
  items: AdminAuditLogItemDTO[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
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

// ── Helper ──

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

// ── API Functions ──

export const adminApi = {
  // Command Center Metrics
  getMetrics: () =>
    api.get<AdminMetricsDTO>('/admin/metrics'),

  getStats: () =>
    api.get<AdminStats>('/admin/stats'),

  // Master Student Audit
  listStudents: (params?: {
    search?: string;
    university?: string;
    is_active?: boolean;
    role?: string;
    limit?: number;
    offset?: number;
  }) =>
    api.get<StudentAuditListDTO>(`/admin/students${buildQuery(params || {})}`),

  getExportStudentsCsvUrl: (params?: {
    search?: string;
    university?: string;
    is_active?: boolean;
    role?: string;
  }): string => {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    return `${baseUrl}/admin/students/export${buildQuery(params || {})}`;
  },

  // Organization Verification
  listVerifications: (params?: { status?: string; limit?: number; offset?: number }) =>
    api.get<VerificationListDTO>(`/admin/verifications${buildQuery(params || {})}`),

  requestVerification: (data: VerificationRequestCreateDTO) =>
    api.post<VerificationItemDTO>('/admin/verifications/request', data),

  reviewVerification: (requestId: string, data: VerificationReviewActionDTO) =>
    api.post<VerificationItemDTO>(`/admin/verifications/${requestId}/review`, data),

  // Moderation Reports
  listReports: (params?: { status?: string; target_type?: string; limit?: number; offset?: number }) =>
    api.get<AdminReportList>(`/admin/reports${buildQuery(params || {})}`),

  reviewReport: (reportId: string, data: ReportReviewActionDTO) =>
    api.post<AdminReportItem>(`/admin/reports/${reportId}/review`, data),

  updateReport: (reportId: string, data: { status: string; admin_note?: string }) =>
    api.patch<AdminReportItem>(`/admin/reports/${reportId}`, data),

  // Audit Logs
  listAuditLogs: (params?: { action?: string; target_type?: string; limit?: number; offset?: number }) =>
    api.get<AdminAuditLogListDTO>(`/admin/audit-logs${buildQuery(params || {})}`),

  // Users
  listUsers: (params?: { search?: string; role?: string; is_active?: boolean; limit?: number; offset?: number }) =>
    api.get<AdminUserList>(`/admin/users${buildQuery(params || {})}`),

  updateUserRole: (userId: string, role: string) =>
    api.patch<AdminUserItem>(`/admin/users/${userId}/role`, { role }),

  updateUserStatus: (userId: string, is_active: boolean) =>
    api.patch<AdminUserItem>(`/admin/users/${userId}/status`, { is_active }),

  // Activities
  listActivities: (params?: { search?: string; limit?: number; offset?: number }) =>
    api.get<AdminActivityList>(`/admin/activities${buildQuery(params || {})}`),

  deleteActivity: (activityId: string) =>
    api.delete(`/admin/activities/${activityId}`),
};
