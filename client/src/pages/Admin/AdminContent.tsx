import { useState, useEffect, useCallback } from 'react';
import { adminApi, type AdminActivityItem } from '../../api/admin';
import './AdminDashboard.css';

export default function AdminContent() {
  return (
    <div className="admin-dashboard">
      <div className="admin-page-header">
        <h1 className="admin-page-title">🎯 Quản lý hoạt động</h1>
        <p className="admin-page-desc">Quản lý và kiểm duyệt các hoạt động trong hệ thống</p>
      </div>

      <ActivitiesTab />
    </div>
  );
}

// ── Activities Tab ──

function ActivitiesTab() {
  const [activities, setActivities] = useState<AdminActivityItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const limit = 20;

  // Delete confirmation
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const loadActivities = useCallback(async () => {
    try {
      setLoading(true);
      const data = await adminApi.listActivities({
        search: search || undefined,
        limit,
        offset: page * limit,
      });
      setActivities(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to load activities:', err);
    } finally {
      setLoading(false);
    }
  }, [search, page]);

  useEffect(() => {
    loadActivities();
  }, [loadActivities]);

  useEffect(() => {
    setPage(0);
  }, [search]);

  const handleDelete = async (id: string) => {
    try {
      await adminApi.deleteActivity(id);
      setDeleteId(null);
      loadActivities();
    } catch (err) {
      console.error('Failed to delete activity:', err);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('vi-VN', {
      day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <>
      <div className="admin-filters">
        <input
          type="text"
          className="admin-search-input"
          placeholder="🔍 Tìm kiếm hoạt động..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Tiêu đề</th>
              <th>Người tổ chức</th>
              <th>Danh mục</th>
              <th>Người tham gia</th>
              <th>Quyền riêng tư</th>
              <th>Thời gian</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 7 }).map((__, j) => (
                    <td key={j}><div className="skeleton admin-table-skeleton" /></td>
                  ))}
                </tr>
              ))
            ) : activities.length === 0 ? (
              <tr>
                <td colSpan={7} className="admin-table-empty">
                  Không tìm thấy hoạt động nào
                </td>
              </tr>
            ) : (
              activities.map(act => (
                <tr key={act.id}>
                  <td>
                    <span className="admin-user-cell-name">{act.title}</span>
                  </td>
                  <td className="admin-cell-muted">@{act.host_username || '—'}</td>
                  <td>
                    {act.category ? (
                      <span className="admin-badge admin-badge-activity">{act.category}</span>
                    ) : '—'}
                  </td>
                  <td>
                    {act.current_participants}/{act.max_participants}
                  </td>
                  <td>
                    <span className={`admin-badge ${act.privacy === 'public' ? 'admin-badge-active' : 'admin-badge-inactive'}`}>
                      {act.privacy}
                    </span>
                  </td>
                  <td className="admin-cell-muted admin-text-xs">
                    {formatDate(act.start_time)}
                  </td>
                  <td>
                    <button
                      className="admin-btn admin-btn-danger"
                      onClick={() => setDeleteId(act.id)}
                    >
                      🗑 Xóa
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

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

      {/* Delete Modal */}
      {deleteId && (
        <div className="admin-modal-overlay" onClick={() => setDeleteId(null)}>
          <div className="admin-modal" onClick={e => e.stopPropagation()}>
            <h3 className="admin-modal-title">⚠️ Xác nhận xóa hoạt động</h3>
            <p className="admin-modal-desc">
              Hoạt động sẽ bị ẩn và không hiển thị cho người dùng nữa. Hành động này có thể được khôi phục trong cơ sở dữ liệu.
            </p>
            <div className="admin-modal-actions">
              <button className="admin-modal-btn admin-modal-btn-cancel" onClick={() => setDeleteId(null)}>
                Hủy
              </button>
              <button
                className="admin-modal-btn admin-modal-btn-danger"
                onClick={() => handleDelete(deleteId)}
              >
                Xóa
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
