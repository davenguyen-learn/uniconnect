import { useState, useEffect, useCallback } from 'react';
import { AlertTriangle } from 'lucide-react';
import { adminApi, type AdminReportItem } from '../../api/admin';
import './AdminDashboard.css';

export default function AdminReports() {
  const [reports, setReports] = useState<AdminReportItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [typeFilter, setTypeFilter] = useState('');
  const [page, setPage] = useState(0);
  const limit = 20;

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [modalAction, setModalAction] = useState<'resolved' | 'dismissed'>('resolved');
  const [modalReportId, setModalReportId] = useState('');
  const [adminNote, setAdminNote] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const loadReports = useCallback(async () => {
    try {
      setLoading(true);
      const data = await adminApi.listReports({
        status: statusFilter || undefined,
        target_type: typeFilter || undefined,
        limit,
        offset: page * limit,
      });
      setReports(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to load reports:', err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, typeFilter, page]);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  useEffect(() => {
    setPage(0);
  }, [statusFilter, typeFilter]);

  const openActionModal = (reportId: string, action: 'resolved' | 'dismissed') => {
    setModalReportId(reportId);
    setModalAction(action);
    setAdminNote('');
    setModalOpen(true);
  };

  const handleAction = async () => {
    try {
      setActionLoading(true);
      await adminApi.updateReport(modalReportId, {
        status: modalAction,
        admin_note: adminNote || undefined,
      });
      setModalOpen(false);
      loadReports();
    } catch (err) {
      console.error('Failed to update report:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const timeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Vừa xong';
    if (mins < 60) return `${mins}m`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h`;
    const days = Math.floor(hours / 24);
    return `${days}d`;
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="admin-dashboard">
      <div className="admin-page-header">
        <h1 className="admin-page-title" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <AlertTriangle size={28} /> Quản lý báo cáo
        </h1>
        <p className="admin-page-desc">Tổng cộng {total} báo cáo</p>
      </div>

      {/* Filters */}
      <div className="admin-filters">
        <select
          className="admin-filter-select"
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
        >
          <option value="">Tất cả trạng thái</option>
          <option value="pending">Đang chờ xử lý</option>
          <option value="resolved">Đã giải quyết</option>
          <option value="dismissed">Đã bỏ qua</option>
        </select>
        <select
          className="admin-filter-select"
          value={typeFilter}
          onChange={e => setTypeFilter(e.target.value)}
        >
          <option value="">Tất cả loại</option>
          <option value="activity">Hoạt động</option>
          <option value="user">Người dùng</option>
        </select>
      </div>

      {/* Table */}
      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Người báo cáo</th>
              <th>Loại</th>
              <th>Lý do</th>
              <th>Mô tả</th>
              <th>Trạng thái</th>
              <th>Thời gian</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 7 }).map((__, j) => (
                    <td key={j}><div className="skeleton" style={{ width: '80%', height: 14 }} /></td>
                  ))}
                </tr>
              ))
            ) : reports.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--color-text-tertiary)' }}>
                  Không có báo cáo nào
                </td>
              </tr>
            ) : (
              reports.map(report => (
                <tr key={report.id}>
                  <td>
                    <div className="admin-user-cell">
                      <span className="admin-user-cell-name">
                        {report.reporter?.username || 'Unknown'}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className={`admin-badge admin-badge-${report.target_type}`}>
                      {report.target_type}
                    </span>
                  </td>
                  <td className="admin-cell-truncate">{report.reason}</td>
                  <td className="admin-cell-truncate admin-cell-muted">
                    {report.description || '—'}
                  </td>
                  <td>
                    <span className={`admin-badge admin-badge-${report.status}`}>
                      {report.status}
                    </span>
                  </td>
                  <td className="admin-cell-muted">{timeAgo(report.created_at)}</td>
                  <td>
                    {report.status === 'pending' ? (
                      <div className="admin-actions-cell">
                        <button
                          className="admin-btn admin-btn-success"
                          onClick={() => openActionModal(report.id, 'resolved')}
                        >
                          ✓ Giải quyết
                        </button>
                        <button
                          className="admin-btn admin-btn-muted"
                          onClick={() => openActionModal(report.id, 'dismissed')}
                        >
                          ✕ Bỏ qua
                        </button>
                      </div>
                    ) : (
                      <span className="admin-cell-muted" style={{ fontSize: 'var(--font-size-xs)' }}>
                        {report.admin_note || '—'}
                      </span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="admin-pagination">
          <button
            className="admin-pagination-btn"
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
          >
            ← Trước
          </button>
          <span className="admin-pagination-info">
            Trang {page + 1} / {totalPages}
          </span>
          <button
            className="admin-pagination-btn"
            onClick={() => setPage(p => p + 1)}
            disabled={page + 1 >= totalPages}
          >
            Sau →
          </button>
        </div>
      )}

      {/* Action Modal */}
      {modalOpen && (
        <div className="admin-modal-overlay" onClick={() => setModalOpen(false)}>
          <div className="admin-modal" onClick={e => e.stopPropagation()}>
            <h3 className="admin-modal-title">
              {modalAction === 'resolved' ? '✓ Giải quyết báo cáo' : '✕ Bỏ qua báo cáo'}
            </h3>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-4)' }}>
              {modalAction === 'resolved'
                ? 'Báo cáo sẽ được đánh dấu là đã xử lý.'
                : 'Báo cáo sẽ bị bỏ qua. Nội dung không vi phạm.'}
            </p>
            <textarea
              className="admin-modal-textarea"
              placeholder="Ghi chú của quản trị viên (không bắt buộc)..."
              value={adminNote}
              onChange={e => setAdminNote(e.target.value)}
            />
            <div className="admin-modal-actions">
              <button
                className="admin-modal-btn admin-modal-btn-cancel"
                onClick={() => setModalOpen(false)}
              >
                Hủy
              </button>
              <button
                className="admin-modal-btn admin-modal-btn-confirm"
                onClick={handleAction}
                disabled={actionLoading}
              >
                {actionLoading ? 'Đang xử lý...' : 'Xác nhận'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
