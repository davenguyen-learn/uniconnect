import { useState, useEffect, useCallback } from 'react';
import { Landmark, ExternalLink, AlertTriangle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { adminApi, type AdminGroupItem } from '../../api/admin';
import './AdminDashboard.css';

export default function AdminGroups() {
  const [groups, setGroups] = useState<AdminGroupItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(0);
  const limit = 15;

  // Status toggle confirmation modal
  const [confirmModal, setConfirmModal] = useState<{
    group: AdminGroupItem;
    targetStatus: 'active' | 'inactive';
  } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadGroups = useCallback(async () => {
    try {
      setLoading(true);
      const data = await adminApi.listGroups({
        search: search || undefined,
        status: statusFilter || undefined,
        limit,
        offset: page * limit,
      });
      setGroups(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to load groups:', err);
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, page]);

  useEffect(() => {
    loadGroups();
  }, [loadGroups]);

  // Reset page when filters change
  useEffect(() => {
    setPage(0);
  }, [search, statusFilter]);

  const handleConfirmToggle = async () => {
    if (!confirmModal) return;
    try {
      setSubmitting(true);
      const updated = await adminApi.updateGroupStatus(confirmModal.group.id, confirmModal.targetStatus);
      setGroups(prev =>
        prev.map(g => (g.id === updated.id ? { ...g, status: updated.status } : g))
      );
      setConfirmModal(null);
    } catch (err) {
      console.error('Failed to update group status:', err);
      alert('Không thể cập nhật trạng thái nhóm. Vui lòng thử lại!');
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="admin-dashboard">
      <div className="admin-page-header">
        <h1 className="admin-page-title" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Landmark size={28} /> Quản lý Nhóm
        </h1>
        <p className="admin-page-desc">
          Tổng cộng {total} nhóm trong hệ thống
        </p>
      </div>

      {/* Filters */}
      <div className="admin-filters">
        <input
          type="text"
          className="admin-search-input"
          placeholder="Tìm kiếm theo tên nhóm hoặc mô tả..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select
          className="admin-filter-select"
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
        >
          <option value="">Tất cả trạng thái</option>
          <option value="active">Đang hoạt động</option>
          <option value="inactive">Đã dừng hoạt động</option>
        </select>
      </div>

      {/* Table */}
      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Nhóm</th>
              <th>Trưởng nhóm (Leader)</th>
              <th>Quyền riêng tư</th>
              <th>Thành viên</th>
              <th>Hoạt động</th>
              <th>Trạng thái</th>
              <th>Ngày tạo</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 8 }).map((__, j) => (
                    <td key={j}>
                      <div className="skeleton" style={{ width: '80%', height: 14 }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : groups.length === 0 ? (
              <tr>
                <td
                  colSpan={8}
                  style={{
                    textAlign: 'center',
                    padding: 'var(--space-8)',
                    color: 'var(--color-text-tertiary)',
                  }}
                >
                  Không tìm thấy nhóm nào phù hợp
                </td>
              </tr>
            ) : (
              groups.map(group => {
                const isActive = group.status === 'active';
                return (
                  <tr key={group.id}>
                    <td>
                      <div className="admin-user-cell">
                        <span className="admin-user-cell-name" style={{ fontWeight: 600 }}>
                          {group.name}
                        </span>
                        {group.description && (
                          <span
                            style={{
                              color: 'var(--color-text-tertiary)',
                              fontSize: 'var(--font-size-xs)',
                              maxWidth: 240,
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                            }}
                          >
                            {group.description}
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      {group.owner ? (
                        <div className="admin-user-cell">
                          <span className="admin-user-cell-name">
                            {group.owner.full_name || group.owner.username}
                          </span>
                          <span style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-xs)' }}>
                            {group.owner.email}
                          </span>
                        </div>
                      ) : (
                        <span className="admin-cell-muted">—</span>
                      )}
                    </td>
                    <td>
                      <span className="admin-cell-muted">
                        {group.privacy === 'public' ? '🌐 Công khai' : '🔒 Riêng tư'}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                        {group.member_count}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                        {group.activity_count}
                      </span>
                    </td>
                    <td>
                      <span className={`admin-badge admin-badge-${isActive ? 'active' : 'inactive'}`}>
                        {isActive ? 'Đang hoạt động' : 'Đã dừng hoạt động'}
                      </span>
                    </td>
                    <td className="admin-cell-muted">{formatDate(group.created_at)}</td>
                    <td>
                      <div className="admin-actions-cell">
                        <Link
                          to={`/groups/${group.id}`}
                          target="_blank"
                          rel="noreferrer"
                          className="admin-btn admin-btn-secondary"
                          title="Xem chi tiết nhóm"
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 4,
                            textDecoration: 'none',
                          }}
                        >
                          <ExternalLink size={13} />
                          <span>Xem</span>
                        </Link>
                        <button
                          className={`admin-btn ${isActive ? 'admin-btn-danger' : 'admin-btn-success'}`}
                          onClick={() =>
                            setConfirmModal({
                              group,
                              targetStatus: isActive ? 'inactive' : 'active',
                            })
                          }
                        >
                          {isActive ? 'Dừng hoạt động' : 'Kích hoạt lại'}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
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

      {/* Confirmation Modal */}
      {confirmModal && (
        <div className="admin-modal-backdrop" onClick={() => setConfirmModal(null)}>
          <div
            className="admin-modal"
            onClick={e => e.stopPropagation()}
            style={{ maxWidth: 460 }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 10,
                  backgroundColor:
                    confirmModal.targetStatus === 'inactive' ? '#fee2e2' : '#dcfce7',
                  color:
                    confirmModal.targetStatus === 'inactive' ? '#dc2626' : '#16a34a',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <AlertTriangle size={22} />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>
                  {confirmModal.targetStatus === 'inactive'
                    ? 'Dừng hoạt động nhóm'
                    : 'Kích hoạt lại nhóm'}
                </h3>
                <p style={{ margin: '2px 0 0', fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                  Xác nhận thay đổi trạng thái nhóm
                </p>
              </div>
            </div>

            <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
              Bạn có chắc chắn muốn{' '}
              <strong>
                {confirmModal.targetStatus === 'inactive'
                  ? 'dừng hoạt động'
                  : 'kích hoạt lại'}
              </strong>{' '}
              nhóm <strong>"{confirmModal.group.name}"</strong>?
              {confirmModal.targetStatus === 'inactive' && (
                <span style={{ display: 'block', marginTop: 8, color: '#b91c1c' }}>
                  ⚠️ Khi dừng hoạt động: Nhóm sẽ không thể tạo thêm hoạt động mới và người dùng không thể gửi yêu cầu tham gia nhóm.
                </span>
              )}
            </p>

            <div
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                gap: 10,
                marginTop: 24,
              }}
            >
              <button
                className="admin-btn admin-btn-secondary"
                onClick={() => setConfirmModal(null)}
                disabled={submitting}
              >
                Hủy
              </button>
              <button
                className={`admin-btn ${
                  confirmModal.targetStatus === 'inactive'
                    ? 'admin-btn-danger'
                    : 'admin-btn-success'
                }`}
                onClick={handleConfirmToggle}
                disabled={submitting}
              >
                {submitting ? 'Đang xử lý...' : 'Xác nhận'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
