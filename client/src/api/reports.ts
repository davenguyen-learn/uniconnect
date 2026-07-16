import { api } from './client';

export interface ReportCreate {
  target_type: 'activity' | 'document' | 'user';
  target_id: string;
  reason: string;
  description?: string;
}

export interface ReportResponse {
  id: string;
  reporter_id: string;
  target_type: string;
  target_id: string;
  reason: string;
  description?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export const reportsApi = {
  createReport: (data: ReportCreate) => 
    api.post<ReportResponse>('/reports', data),

  listReports: (params?: { status?: string; target_type?: string; limit?: number; offset?: number }) => {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.target_type) queryParams.append('target_type', params.target_type);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    
    const queryStr = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return api.get<ReportResponse[]>(`/reports${queryStr}`);
  }
};
