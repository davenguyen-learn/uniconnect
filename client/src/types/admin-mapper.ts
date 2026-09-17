import type {
  AdminMetricsDTO,
  KPICardDTO,
  StudentAuditItemDTO,
  VerificationItemDTO,
  AdminReportItem,
} from '../api/admin';

// ── View Models ──

export interface KPICardViewModel {
  label: string;
  formattedValue: string;
  deltaPercent: number | null;
  deltaText: string | null;
  isPositiveDelta: boolean;
  trend: number[];
  svgPoints: string;
  unit: string | null;
}

export interface AdminMetricsViewModel {
  totalCtxh: KPICardViewModel;
  attendanceRate: KPICardViewModel;
  activeUsers: KPICardViewModel;
  monthlyGrowth: KPICardViewModel;
  dau: number;
  mau: number;
  totalUsers: number;
  totalActivities: number;
  lastUpdatedFormatted: string;
}

export interface StudentAuditItemViewModel {
  id: string;
  username: string;
  fullName: string;
  email: string;
  university: string;
  statusBadge: { label: string; className: string };
  verifiedBadge: { label: string; className: string };
  roleBadge: { label: string; className: string };
  confirmedCtxhDays: string;
  attendanceCount: number;
  joinedDate: string;
}

export interface VerificationItemViewModel {
  id: string;
  userId: string;
  organizationName: string;
  faculty: string;
  documentUrl: string | null;
  description: string;
  status: 'pending' | 'approved' | 'rejected';
  statusBadge: { label: string; className: string };
  adminNote: string | null;
  createdAtFormatted: string;
  applicantName: string;
  applicantEmail: string;
}

export interface AdminReportViewModel {
  id: string;
  reporterId: string;
  targetType: string;
  targetId: string;
  reason: string;
  description: string;
  status: string;
  statusBadge: { label: string; className: string };
  adminNote: string | null;
  createdAtFormatted: string;
  reporterName: string;
}

// ── Pure Presentation Coordinate Mapping for Sparkline ──

export const generateSparklinePoints = (
  trend: number[],
  width = 120,
  height = 36
): string => {
  if (!trend || trend.length === 0) return '';
  if (trend.length === 1) return `0,${height / 2} ${width},${height / 2}`;

  const min = Math.min(...trend);
  const max = Math.max(...trend);
  const range = max - min === 0 ? 1 : max - min;

  return trend
    .map((val, idx) => {
      const x = (idx / (trend.length - 1)) * width;
      const y = height - ((val - min) / range) * (height - 8) - 4;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
};

// ── Mappers ──

export const mapKPICardToViewModel = (
  dto: KPICardDTO,
  width = 120,
  height = 36
): KPICardViewModel => {
  let deltaText: string | null = null;
  let isPositive = true;

  if (dto.delta_percent !== null && dto.delta_percent !== undefined) {
    isPositive = dto.delta_percent >= 0;
    const sign = isPositive ? '+' : '';
    deltaText = `${sign}${dto.delta_percent.toFixed(1)}%`;
  }

  return {
    label: dto.label,
    formattedValue: dto.formatted_value,
    deltaPercent: dto.delta_percent,
    deltaText,
    isPositiveDelta: isPositive,
    trend: dto.trend,
    svgPoints: generateSparklinePoints(dto.trend, width, height),
    unit: dto.unit,
  };
};

export const mapAdminMetricsToViewModel = (
  dto: AdminMetricsDTO
): AdminMetricsViewModel => {
  const d = new Date(dto.last_updated);
  const formattedTime = isNaN(d.getTime())
    ? 'Vừa xong'
    : d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) +
      ' ' +
      d.toLocaleDateString('vi-VN');

  return {
    totalCtxh: mapKPICardToViewModel(dto.total_ctxh),
    attendanceRate: mapKPICardToViewModel(dto.attendance_rate),
    activeUsers: mapKPICardToViewModel(dto.active_users),
    monthlyGrowth: mapKPICardToViewModel(dto.monthly_growth),
    dau: dto.dau,
    mau: dto.mau,
    totalUsers: dto.total_users,
    totalActivities: dto.total_activities,
    lastUpdatedFormatted: formattedTime,
  };
};

export const mapStudentAuditToViewModel = (
  dto: StudentAuditItemDTO
): StudentAuditItemViewModel => {
  const createdDate = new Date(dto.created_at);
  const joinedDate = isNaN(createdDate.getTime())
    ? '—'
    : createdDate.toLocaleDateString('vi-VN');

  const roleMap: Record<string, { label: string; className: string }> = {
    admin: { label: 'Quản trị viên', className: 'badge-role-admin' },
    edu_org: { label: 'Tổ chức uy tín', className: 'badge-role-org' },
    moderator: { label: 'Điều hành', className: 'badge-role-mod' },
    student: { label: 'Sinh viên', className: 'badge-role-student' },
  };

  return {
    id: dto.id,
    username: dto.username,
    fullName: dto.full_name || dto.username,
    email: dto.email,
    university: dto.university || '—',
    statusBadge: dto.is_active
      ? { label: 'Hoạt động', className: 'badge-status-active' }
      : { label: 'Đã khóa', className: 'badge-status-inactive' },
    verifiedBadge: dto.is_verified
      ? { label: 'Đã xác minh', className: 'badge-verified' }
      : { label: 'Chưa', className: 'badge-unverified' },
    roleBadge: roleMap[dto.role] || { label: dto.role, className: 'badge-role-default' },
    confirmedCtxhDays: dto.confirmed_ctxh_days.toFixed(1),
    attendanceCount: dto.attendance_count,
    joinedDate,
  };
};

export const mapVerificationToViewModel = (
  dto: VerificationItemDTO
): VerificationItemViewModel => {
  const cDate = dto.created_at ? new Date(dto.created_at) : null;
  const createdAtFormatted = cDate && !isNaN(cDate.getTime())
    ? cDate.toLocaleDateString('vi-VN')
    : '—';

  const statusMap: Record<string, { label: string; className: string }> = {
    pending: { label: 'Chờ duyệt', className: 'badge-verif-pending' },
    approved: { label: 'Đã duyệt', className: 'badge-verif-approved' },
    rejected: { label: 'Từ chối', className: 'badge-verif-rejected' },
  };

  return {
    id: dto.id,
    userId: dto.user_id,
    organizationName: dto.organization_name,
    faculty: dto.faculty || '—',
    documentUrl: dto.document_url,
    description: dto.description || 'Không có mô tả thêm',
    status: dto.status,
    statusBadge: statusMap[dto.status] || { label: dto.status, className: 'badge-verif-default' },
    adminNote: dto.admin_note,
    createdAtFormatted,
    applicantName: dto.applicant_name || 'Đại diện CLB',
    applicantEmail: dto.applicant_email || '—',
  };
};

export const mapReportToViewModel = (
  dto: AdminReportItem
): AdminReportViewModel => {
  const cDate = new Date(dto.created_at);
  const createdAtFormatted = !isNaN(cDate.getTime())
    ? cDate.toLocaleDateString('vi-VN') + ' ' + cDate.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
    : '—';

  const statusMap: Record<string, { label: string; className: string }> = {
    pending: { label: 'Chờ xử lý', className: 'badge-report-pending' },
    resolved: { label: 'Đã xử lý', className: 'badge-report-resolved' },
    dismissed: { label: 'Đã bỏ qua', className: 'badge-report-dismissed' },
  };

  return {
    id: dto.id,
    reporterId: dto.reporter_id,
    targetType: dto.target_type,
    targetId: dto.target_id,
    reason: dto.reason,
    description: dto.description || 'Không có mô tả chi tiết',
    status: dto.status,
    statusBadge: statusMap[dto.status] || { label: dto.status, className: 'badge-report-default' },
    adminNote: dto.admin_note,
    createdAtFormatted,
    reporterName: dto.reporter_name || dto.reporter?.full_name || dto.reporter?.username || 'Ẩn danh',
  };
};
