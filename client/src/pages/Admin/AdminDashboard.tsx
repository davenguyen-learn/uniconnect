import { useState, useEffect, useCallback } from 'react';
import {
  Award,
  TrendingUp,
  TrendingDown,
  Users,
  Shield,
  Search,
  Download,
  RefreshCw,
  CheckCircle2,
  XCircle,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  AlertCircle,
  Clock,
} from 'lucide-react';
import {
  adminApi,
  type StudentAuditListDTO,
  type VerificationListDTO,
  type AdminReportList,
  type TrophyGrantRequestItemDTO,
} from '../../api/admin';
import {
  mapAdminMetricsToViewModel,
  mapStudentAuditToViewModel,
  mapVerificationToViewModel,
  mapReportToViewModel,
  type AdminMetricsViewModel,
  type StudentAuditItemViewModel,
  type VerificationItemViewModel,
  type AdminReportViewModel,
} from '../../types/admin-mapper';
import './AdminDashboard.css';

export default function AdminDashboard() {
  // ── States ──
  const [metrics, setMetrics] = useState<AdminMetricsViewModel | null>(null);
  const [students, setStudents] = useState<StudentAuditItemViewModel[]>([]);
  const [studentsTotal, setStudentsTotal] = useState(0);
  const [studentsLimit] = useState(10);
  const [studentsOffset, setStudentsOffset] = useState(0);
  const [studentSearch, setStudentSearch] = useState('');

  const [verifications, setVerifications] = useState<VerificationItemViewModel[]>([]);
  const [verificationsTotal, setVerificationsTotal] = useState(0);

  const [reports, setReports] = useState<AdminReportViewModel[]>([]);
  const [reportsTotal, setReportsTotal] = useState(0);

  const [trophyRequests, setTrophyRequests] = useState<TrophyGrantRequestItemDTO[]>([]);
  const [trophyRequestsTotal, setTrophyRequestsTotal] = useState(0);
  const [activeTrophyReview, setActiveTrophyReview] = useState<{ id: string; title: string; action: 'approve' | 'reject' } | null>(null);
  const [trophyReviewNote, setTrophyReviewNote] = useState('');
  const [submittingTrophy, setSubmittingTrophy] = useState(false);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Review Modals
  const [activeVerification, setActiveVerification] = useState<{ id: string; name: string; action: 'approve' | 'reject' } | null>(null);
  const [verificationNote, setVerificationNote] = useState('');
  const [submittingVerif, setSubmittingVerif] = useState(false);

  const [activeReport, setActiveReport] = useState<{ id: string; action: 'resolve' | 'dismiss'; targetType: string } | null>(null);
  const [reportNote, setReportNote] = useState('');
  const [hideActivity, setHideActivity] = useState(false);
  const [deactivateUser, setDeactivateUser] = useState(false);
  const [submittingReport, setSubmittingReport] = useState(false);

  // ── Loaders ──

  const loadMetrics = async () => {
    try {
      const res = await adminApi.getMetrics();
      setMetrics(mapAdminMetricsToViewModel(res));
    } catch (err) {
      console.error('Failed to load metrics:', err);
    }
  };

  const loadStudents = useCallback(async (searchQuery = studentSearch, offset = studentsOffset) => {
    try {
      const res: StudentAuditListDTO = await adminApi.listStudents({
        search: searchQuery || undefined,
        limit: studentsLimit,
        offset: offset,
      });
      setStudents(res.items.map(mapStudentAuditToViewModel));
      setStudentsTotal(res.total);
    } catch (err) {
      console.error('Failed to load student audit:', err);
    }
  }, [studentSearch, studentsOffset, studentsLimit]);

  const loadVerifications = async () => {
    try {
      const res: VerificationListDTO = await adminApi.listVerifications({ status: 'pending', limit: 5 });
      setVerifications(res.items.map(mapVerificationToViewModel));
      setVerificationsTotal(res.total);
    } catch (err) {
      console.error('Failed to load verifications:', err);
    }
  };

  const loadReports = async () => {
    try {
      const res: AdminReportList = await adminApi.listReports({ status: 'pending', limit: 5 });
      setReports(res.items.map(mapReportToViewModel));
      setReportsTotal(res.total);
    } catch (err) {
      console.error('Failed to load reports:', err);
    }
  };

  const loadTrophyRequests = async () => {
    try {
      const res = await adminApi.listTrophyRequests({ limit: 10 });
      setTrophyRequests(res.items);
      setTrophyRequestsTotal(res.total);
    } catch (err) {
      console.error('Failed to load trophy requests:', err);
    }
  };

  const loadAll = async () => {
    setLoading(true);
    await Promise.allSettled([
      loadMetrics(),
      loadStudents(),
      loadVerifications(),
      loadReports(),
      loadTrophyRequests(),
    ]);
    setLoading(false);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.allSettled([
      loadMetrics(),
      loadStudents(),
      loadVerifications(),
      loadReports(),
      loadTrophyRequests(),
    ]);
    setRefreshing(false);
  };

  useEffect(() => {
    loadAll();
  }, []);

  // ── Search & Pagination Handlers ──

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setStudentsOffset(0);
    loadStudents(studentSearch, 0);
  };

  const handlePrevPage = () => {
    if (studentsOffset >= studentsLimit) {
      const nextOffset = studentsOffset - studentsLimit;
      setStudentsOffset(nextOffset);
      loadStudents(studentSearch, nextOffset);
    }
  };

  const handleNextPage = () => {
    if (studentsOffset + studentsLimit < studentsTotal) {
      const nextOffset = studentsOffset + studentsLimit;
      setStudentsOffset(nextOffset);
      loadStudents(studentSearch, nextOffset);
    }
  };

  // ── Verification Review ──

  const confirmVerificationReview = async () => {
    if (!activeVerification) return;
    try {
      setSubmittingVerif(true);
      await adminApi.reviewVerification(activeVerification.id, {
        action: activeVerification.action,
        admin_note: verificationNote.trim() || undefined,
      });
      setActiveVerification(null);
      setVerificationNote('');
      await loadVerifications();
      await loadMetrics();
    } catch (err) {
      console.error('Failed to review verification:', err);
      alert('Lỗi xử lý duyệt tổ chức. Vui lòng thử lại.');
    } finally {
      setSubmittingVerif(false);
    }
  };

  // ── Report Review ──

  const confirmReportReview = async () => {
    if (!activeReport) return;
    try {
      setSubmittingReport(true);
      await adminApi.reviewReport(activeReport.id, {
        action: activeReport.action,
        admin_note: reportNote.trim() || undefined,
        hide_activity: hideActivity,
        deactivate_user: deactivateUser,
      });
      setActiveReport(null);
      setReportNote('');
      setHideActivity(false);
      setDeactivateUser(false);
      await loadReports();
      await loadMetrics();
    } catch (err) {
      console.error('Failed to review report:', err);
      alert('Lỗi xử lý báo cáo. Vui lòng thử lại.');
    } finally {
      setSubmittingReport(false);
    }
  };

  // ── Trophy Grant Review ──

  const confirmTrophyReview = async () => {
    if (!activeTrophyReview) return;
    try {
      setSubmittingTrophy(true);
      await adminApi.reviewTrophyRequest(
        activeTrophyReview.id,
        activeTrophyReview.action,
        trophyReviewNote.trim() || undefined
      );
      setActiveTrophyReview(null);
      setTrophyReviewNote('');
      await loadTrophyRequests();
    } catch (err: any) {
      console.error('Failed to review trophy request:', err);
      alert(err?.response?.data?.detail || 'Lỗi xử lý phê duyệt danh hiệu. Vui lòng thử lại.');
    } finally {
      setSubmittingTrophy(false);
    }
  };

  // ── CSV Export Trigger ──

  const handleExportCsv = () => {
    const url = adminApi.getExportStudentsCsvUrl({
      search: studentSearch || undefined,
    });
    window.open(url, '_blank');
  };

  if (loading) {
    return (
      <div className="admin-command-center">
        <div className="admin-header-shimmer skeleton" style={{ height: 60, borderRadius: 12, marginBottom: 24 }} />
        <div className="admin-kpi-grid">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="admin-kpi-card skeleton-card">
              <div className="skeleton" style={{ width: '50%', height: 16 }} />
              <div className="skeleton" style={{ width: '70%', height: 32, marginTop: 12 }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="admin-command-center">
      {/* Header Bar */}
      <header className="command-header">
        <div className="command-title-group">
          <div className="command-badge">
            <Shield className="command-badge-icon" size={16} />
            <span>Campus Control Plane</span>
          </div>
          <h1 className="command-title">Admin Command Center</h1>
          <p className="command-subtitle">
            Hệ thống giám sát chỉ huy & kiểm toán hoạt động toàn trường
          </p>
        </div>
        <div className="command-actions">
          <span className="last-updated-pill">
            Cập nhật: {metrics?.lastUpdatedFormatted || 'Vừa xong'}
          </span>
          <button
            type="button"
            className="command-refresh-btn"
            onClick={handleRefresh}
            disabled={refreshing}
            title="Làm mới dữ liệu"
          >
            <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
            <span>Làm mới</span>
          </button>
        </div>
      </header>

      {/* Row 1: KPI Metrics Row with Sparklines */}
      {metrics && (
        <section className="command-kpi-section" aria-label="KPI Metrics">
          {/* Card 1: Total CTXH */}
          <div className="kpi-card kpi-card-gold">
            <div className="kpi-card-header">
              <span className="kpi-label">{metrics.totalCtxh.label}</span>
              <div className="kpi-icon-wrap icon-gold">
                <Award size={20} />
              </div>
            </div>
            <div className="kpi-value-row">
              <span className="kpi-value">{metrics.totalCtxh.formattedValue}</span>
              {metrics.totalCtxh.deltaText && (
                <span className={`kpi-delta ${metrics.totalCtxh.isPositiveDelta ? 'delta-up' : 'delta-down'}`}>
                  {metrics.totalCtxh.isPositiveDelta ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                  {metrics.totalCtxh.deltaText}
                </span>
              )}
            </div>
            <div className="kpi-sparkline-wrap">
              <svg className="sparkline-svg" viewBox="0 0 120 36" preserveAspectRatio="none">
                <polyline
                  fill="none"
                  stroke="var(--kpi-gold-stroke, #D97706)"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={metrics.totalCtxh.svgPoints}
                />
              </svg>
            </div>
          </div>

          {/* Card 2: Attendance Rate */}
          <div className="kpi-card kpi-card-emerald">
            <div className="kpi-card-header">
              <span className="kpi-label">{metrics.attendanceRate.label}</span>
              <div className="kpi-icon-wrap icon-emerald">
                <TrendingUp size={20} />
              </div>
            </div>
            <div className="kpi-value-row">
              <span className="kpi-value">{metrics.attendanceRate.formattedValue}</span>
              <span className="kpi-pill-sub">Điểm danh thực tế</span>
            </div>
            <div className="kpi-sparkline-wrap">
              <svg className="sparkline-svg" viewBox="0 0 120 36" preserveAspectRatio="none">
                <polyline
                  fill="none"
                  stroke="var(--kpi-emerald-stroke, #10B981)"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={metrics.attendanceRate.svgPoints}
                />
              </svg>
            </div>
          </div>

          {/* Card 3: DAU / MAU */}
          <div className="kpi-card kpi-card-navy">
            <div className="kpi-card-header">
              <span className="kpi-label">{metrics.activeUsers.label}</span>
              <div className="kpi-icon-wrap icon-navy">
                <Users size={20} />
              </div>
            </div>
            <div className="kpi-value-row">
              <span className="kpi-value">{metrics.activeUsers.formattedValue}</span>
              <span className="kpi-pill-sub">Hôm nay / 30 ngày</span>
            </div>
            <div className="kpi-sparkline-wrap">
              <svg className="sparkline-svg" viewBox="0 0 120 36" preserveAspectRatio="none">
                <polyline
                  fill="none"
                  stroke="var(--kpi-navy-stroke, #3B82F6)"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={metrics.activeUsers.svgPoints}
                />
              </svg>
            </div>
          </div>

          {/* Card 4: Monthly Growth */}
          <div className="kpi-card kpi-card-purple">
            <div className="kpi-card-header">
              <span className="kpi-label">{metrics.monthlyGrowth.label}</span>
              <div className="kpi-icon-wrap icon-purple">
                <Sparkles size={20} />
              </div>
            </div>
            <div className="kpi-value-row">
              <span className="kpi-value">{metrics.monthlyGrowth.formattedValue}</span>
              {metrics.monthlyGrowth.deltaText ? (
                <span className={`kpi-delta ${metrics.monthlyGrowth.isPositiveDelta ? 'delta-up' : 'delta-down'}`}>
                  {metrics.monthlyGrowth.isPositiveDelta ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                  {metrics.monthlyGrowth.deltaText}
                </span>
              ) : (
                <span className="kpi-pill-sub">Tháng đầu tiên</span>
              )}
            </div>
            <div className="kpi-sparkline-wrap">
              <svg className="sparkline-svg" viewBox="0 0 120 36" preserveAspectRatio="none">
                <polyline
                  fill="none"
                  stroke="var(--kpi-purple-stroke, #8B5CF6)"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={metrics.monthlyGrowth.svgPoints}
                />
              </svg>
            </div>
          </div>
        </section>
      )}

      {/* Row 2: Split Layout (Student Audit Table + Verification Queue) */}
      <section className="command-split-grid">
        {/* Left / Center: Master Student Audit Table */}
        <div className="command-panel student-audit-panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Bảng Kiểm toán Sinh viên</h2>
              <p className="panel-desc">Tổng cộng {studentsTotal} sinh viên toàn trường</p>
            </div>
            <div className="panel-controls">
              <form onSubmit={handleSearchSubmit} className="search-box-wrap">
                <Search size={16} className="search-icon" />
                <input
                  type="text"
                  placeholder="Tìm MSSV, tên, email..."
                  className="search-input"
                  value={studentSearch}
                  onChange={e => setStudentSearch(e.target.value)}
                />
              </form>
              <button
                type="button"
                className="btn-export-csv"
                onClick={handleExportCsv}
                title="Tải tệp CSV chuẩn UTF-8 BOM"
              >
                <Download size={16} />
                <span>Xuất CSV</span>
              </button>
            </div>
          </div>

          <div className="table-responsive">
            <table className="command-table">
              <thead>
                <tr>
                  <th>MSSV / Username</th>
                  <th>Họ và tên</th>
                  <th>Khoa / Viện</th>
                  <th>Vai trò</th>
                  <th>Trạng thái</th>
                  <th className="text-right">Ngày CTXH</th>
                  <th className="text-right">Đã tham gia</th>
                </tr>
              </thead>
              <tbody>
                {students.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="empty-cell">
                      Không tìm thấy sinh viên nào theo điều kiện tìm kiếm.
                    </td>
                  </tr>
                ) : (
                  students.map(s => (
                    <tr key={s.id}>
                      <td className="font-mono text-bold">{s.username}</td>
                      <td>{s.fullName}</td>
                      <td className="text-muted">{s.university}</td>
                      <td>
                        <span className={`role-badge ${s.roleBadge.className}`}>
                          {s.roleBadge.label}
                        </span>
                      </td>
                      <td>
                        <span className={`status-pill ${s.statusBadge.className}`}>
                          {s.statusBadge.label}
                        </span>
                      </td>
                      <td className="text-right">
                        <span className="ctxh-gold-badge">
                          {s.confirmedCtxhDays} ngày
                        </span>
                      </td>
                      <td className="text-right font-mono">{s.attendanceCount}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="pagination-bar">
            <span className="pagination-info">
              Hiển thị {students.length > 0 ? studentsOffset + 1 : 0}–
              {Math.min(studentsOffset + studentsLimit, studentsTotal)} / {studentsTotal}
            </span>
            <div className="pagination-btns">
              <button
                type="button"
                className="btn-page"
                onClick={handlePrevPage}
                disabled={studentsOffset === 0}
              >
                <ChevronLeft size={16} />
              </button>
              <button
                type="button"
                className="btn-page"
                onClick={handleNextPage}
                disabled={studentsOffset + studentsLimit >= studentsTotal}
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>

        {/* Right: Verified Org Approvals Queue */}
        <div className="command-panel verification-panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Duyệt Tổ chức Uy tín</h2>
              <p className="panel-desc">{verificationsTotal} đơn xin cấp tích xanh</p>
            </div>
          </div>

          {verifications.length === 0 ? (
            <div className="panel-empty-state">
              <CheckCircle2 size={36} className="text-emerald" />
              <p>Không có yêu cầu duyệt nào đang chờ!</p>
            </div>
          ) : (
            <div className="verification-cards-list">
              {verifications.map(v => (
                <div key={v.id} className="verification-item-card">
                  <div className="v-card-top">
                    <h3 className="v-org-name">{v.organizationName}</h3>
                    <span className="v-date">{v.createdAtFormatted}</span>
                  </div>
                  <p className="v-meta">
                    <strong>Khoa:</strong> {v.faculty} • <strong>Đại diện:</strong> {v.applicantName}
                  </p>
                  <p className="v-desc">{v.description}</p>
                  {v.documentUrl && (
                    <a
                      href={v.documentUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="v-doc-link"
                    >
                      <ExternalLink size={14} />
                      <span>Xem hồ sơ minh chứng</span>
                    </a>
                  )}
                  <div className="v-actions">
                    <button
                      type="button"
                      className="btn-approve"
                      onClick={() => setActiveVerification({ id: v.id, name: v.organizationName, action: 'approve' })}
                    >
                      <CheckCircle2 size={16} />
                      <span>Duyệt</span>
                    </button>
                    <button
                      type="button"
                      className="btn-reject"
                      onClick={() => setActiveVerification({ id: v.id, name: v.organizationName, action: 'reject' })}
                    >
                      <XCircle size={16} />
                      <span>Từ chối</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Row 3: Reports Moderation Queue */}
      <section className="command-panel moderation-panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Hàng đợi Kiểm duyệt Báo cáo</h2>
            <p className="panel-desc">{reportsTotal} báo cáo vi phạm cần giải quyết</p>
          </div>
        </div>

        {reports.length === 0 ? (
          <div className="panel-empty-state">
            <CheckCircle2 size={36} className="text-emerald" />
            <p>Hệ thống sạch sẽ, không có báo cáo vi phạm nào tồn đọng!</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="command-table">
              <thead>
                <tr>
                  <th>Đối tượng</th>
                  <th>Lý do</th>
                  <th>Mô tả chi tiết</th>
                  <th>Người báo cáo</th>
                  <th>Thời gian</th>
                  <th className="text-right">Thao tác xử lý</th>
                </tr>
              </thead>
              <tbody>
                {reports.map(r => (
                  <tr key={r.id}>
                    <td>
                      <span className="target-type-badge">{r.targetType}</span>
                    </td>
                    <td className="text-bold">{r.reason}</td>
                    <td className="text-muted">{r.description}</td>
                    <td>{r.reporterName}</td>
                    <td className="text-muted">{r.createdAtFormatted}</td>
                    <td className="text-right">
                      <div className="report-action-btns">
                        <button
                          type="button"
                          className="btn-resolve"
                          onClick={() => setActiveReport({ id: r.id, action: 'resolve', targetType: r.targetType })}
                        >
                          <CheckCircle2 size={14} />
                          <span>Giải quyết</span>
                        </button>
                        <button
                          type="button"
                          className="btn-dismiss"
                          onClick={() => setActiveReport({ id: r.id, action: 'dismiss', targetType: r.targetType })}
                        >
                          <XCircle size={14} />
                          <span>Bỏ qua</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Row 4: Trophy Approval Queue */}
      <section className="command-panel trophy-queue-panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Hàng đợi Phê duyệt Danh hiệu</h2>
            <p className="panel-desc">{trophyRequestsTotal} yêu cầu cấp danh hiệu từ các hoạt động đã chốt điểm danh</p>
          </div>
        </div>

        {trophyRequests.length === 0 ? (
          <div className="panel-empty-state">
            <Award size={36} className="text-muted" />
            <p>Hiện không có yêu cầu cấp danh hiệu nào trong hàng đợi!</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="command-table">
              <thead>
                <tr>
                  <th>Hoạt động</th>
                  <th>Danh hiệu đề xuất</th>
                  <th>Điểm danh thực tế</th>
                  <th>Trạng thái</th>
                  <th>Ghi chú / Duyệt bởi</th>
                  <th className="text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {trophyRequests.map(tr => (
                  <tr key={tr.id}>
                    <td className="text-bold">{tr.activity_title || 'Hoạt động'}</td>
                    <td>
                      <span className="trophy-name-tag">
                        <Award size={14} />
                        <span>{tr.trophy_name || 'Danh hiệu'}</span>
                      </span>
                    </td>
                    <td>
                      <span className={`attendance-quorum-badge ${tr.actual_attended_count >= tr.min_participants_required ? 'quorum-met' : 'quorum-unmet'}`}>
                        <Users size={13} />
                        <span>{tr.actual_attended_count} / {tr.min_participants_required}</span>
                      </span>
                    </td>
                    <td>
                      {tr.status === 'eligible_for_review' && (
                        <span className="trophy-status-badge badge-eligible">
                          <Clock size={12} />
                          <span>Chờ xét duyệt</span>
                        </span>
                      )}
                      {tr.status === 'insufficient_quorum' && (
                        <span className="trophy-status-badge badge-insufficient">
                          <AlertCircle size={12} />
                          <span>Không đủ người</span>
                        </span>
                      )}
                      {tr.status === 'approved' && (
                        <span className="trophy-status-badge badge-approved">
                          <CheckCircle2 size={12} />
                          <span>Đã duyệt cấp</span>
                        </span>
                      )}
                      {tr.status === 'rejected' && (
                        <span className="trophy-status-badge badge-rejected">
                          <XCircle size={12} />
                          <span>Từ chối</span>
                        </span>
                      )}
                    </td>
                    <td className="text-muted text-sm">
                      {tr.reviewed_by ? (
                        <span>{tr.reviewer_name ? `Duyệt: ${tr.reviewer_name}` : 'Đã duyệt'}{tr.admin_notes ? ` — ${tr.admin_notes}` : ''}</span>
                      ) : (
                        <span>{tr.status === 'insufficient_quorum' ? 'Tự động dừng do không đủ người' : 'Đang chờ Admin'}</span>
                      )}
                    </td>
                    <td className="text-right">
                      {tr.status === 'eligible_for_review' ? (
                        <div className="report-action-btns">
                          <button
                            type="button"
                            className="btn-resolve"
                            onClick={() => setActiveTrophyReview({ id: tr.id, title: tr.activity_title || 'Hoạt động', action: 'approve' })}
                          >
                            <CheckCircle2 size={14} />
                            <span>Duyệt cấp</span>
                          </button>
                          <button
                            type="button"
                            className="btn-dismiss"
                            onClick={() => setActiveTrophyReview({ id: tr.id, title: tr.activity_title || 'Hoạt động', action: 'reject' })}
                          >
                            <XCircle size={14} />
                            <span>Từ chối</span>
                          </button>
                        </div>
                      ) : (
                        <span className="text-muted text-xs">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Modal: Verification Action */}
      {activeVerification && (
        <div className="command-modal-overlay" onClick={() => setActiveVerification(null)}>
          <div className="command-modal-box" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">
                {activeVerification.action === 'approve' ? 'Xác nhận Duyệt Tổ chức' : 'Từ chối Yêu cầu Xác minh'}
              </h3>
              <button
                type="button"
                className="modal-close"
                onClick={() => setActiveVerification(null)}
              >
                ×
              </button>
            </div>
            <p className="modal-desc">
              Tổ chức: <strong>{activeVerification.name}</strong>
              {activeVerification.action === 'approve'
                ? ' — Duyệt sẽ cấp huy hiệu Tổ chức uy tín (is_verified = True) và nâng quyền tổ chức.'
                : ' — Yêu cầu sẽ bị đánh dấu từ chối.'}
            </p>
            <div className="form-group">
              <label htmlFor="verif-note">Ghi chú của Ban Quản trị:</label>
              <textarea
                id="verif-note"
                rows={3}
                placeholder="Nhập lý do hoặc phản hồi cho đại diện nhóm..."
                value={verificationNote}
                onChange={e => setVerificationNote(e.target.value)}
              />
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn-cancel"
                onClick={() => setActiveVerification(null)}
              >
                Hủy
              </button>
              <button
                type="button"
                className={activeVerification.action === 'approve' ? 'btn-confirm-approve' : 'btn-confirm-reject'}
                onClick={confirmVerificationReview}
                disabled={submittingVerif}
              >
                {submittingVerif ? 'Đang lưu...' : activeVerification.action === 'approve' ? 'Xác nhận Duyệt' : 'Xác nhận Từ chối'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Report Action */}
      {activeReport && (
        <div className="command-modal-overlay" onClick={() => setActiveReport(null)}>
          <div className="command-modal-box" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">
                {activeReport.action === 'resolve' ? 'Giải quyết Báo cáo Vi phạm' : 'Bỏ qua Báo cáo'}
              </h3>
              <button
                type="button"
                className="modal-close"
                onClick={() => setActiveReport(null)}
              >
                ×
              </button>
            </div>
            {activeReport.action === 'resolve' && (
              <div className="moderation-side-effects">
                <p className="side-effect-title">Hành động khắc phục (Tùy chọn):</p>
                {activeReport.targetType === 'activity' && (
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={hideActivity}
                      onChange={e => setHideActivity(e.target.checked)}
                    />
                    <span>Ẩn hoạt động vi phạm ngay lập tức (Soft-delete)</span>
                  </label>
                )}
                {activeReport.targetType === 'user' && (
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={deactivateUser}
                      onChange={e => setDeactivateUser(e.target.checked)}
                    />
                    <span>Khóa tài khoản người dùng vi phạm</span>
                  </label>
                )}
              </div>
            )}
            <div className="form-group">
              <label htmlFor="report-note">Ghi chú xử lý:</label>
              <textarea
                id="report-note"
                rows={3}
                placeholder="Nhập ghi chú xử lý vi phạm..."
                value={reportNote}
                onChange={e => setReportNote(e.target.value)}
              />
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn-cancel"
                onClick={() => setActiveReport(null)}
              >
                Hủy
              </button>
              <button
                type="button"
                className="btn-confirm-resolve"
                onClick={confirmReportReview}
                disabled={submittingReport}
              >
                {submittingReport ? 'Đang lưu...' : 'Xác nhận Xử lý'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Trophy Action */}
      {activeTrophyReview && (
        <div className="command-modal-overlay" onClick={() => setActiveTrophyReview(null)}>
          <div className="command-modal-box" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">
                {activeTrophyReview.action === 'approve' ? 'Xác nhận Duyệt Cấp Danh hiệu' : 'Từ chối Cấp Danh hiệu'}
              </h3>
              <button
                type="button"
                className="modal-close"
                onClick={() => setActiveTrophyReview(null)}
              >
                ×
              </button>
            </div>
            <p className="modal-desc">
              Hoạt động: <strong>{activeTrophyReview.title}</strong>
              {activeTrophyReview.action === 'approve'
                ? ' — Phê duyệt sẽ tự động cấp danh hiệu cho toàn bộ sinh viên đã xác nhận tham gia sự kiện này.'
                : ' — Yêu cầu cấp danh hiệu sẽ bị từ chối và không cấp danh hiệu cho người tham gia.'}
            </p>
            <div className="form-group">
              <label htmlFor="trophy-review-note">Ghi chú kiểm duyệt:</label>
              <textarea
                id="trophy-review-note"
                rows={3}
                placeholder="Nhập ghi chú phản hồi..."
                value={trophyReviewNote}
                onChange={e => setTrophyReviewNote(e.target.value)}
              />
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn-cancel"
                onClick={() => setActiveTrophyReview(null)}
              >
                Hủy
              </button>
              <button
                type="button"
                className={activeTrophyReview.action === 'approve' ? 'btn-confirm-resolve' : 'btn-confirm-reject'}
                onClick={confirmTrophyReview}
                disabled={submittingTrophy}
              >
                {submittingTrophy ? 'Đang lưu...' : activeTrophyReview.action === 'approve' ? 'Xác nhận Duyệt cấp' : 'Xác nhận Từ chối'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
