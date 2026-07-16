import { useState, useEffect, useCallback } from 'react';
import { adminApi, type AdminActivityItem, type AdminDocumentItem } from '../../api/admin';
import './AdminDashboard.css';

type Tab = 'activities' | 'documents';

export default function AdminContent() {
  const [tab, setTab] = useState<Tab>('activities');

  return (
    <div className="admin-dashboard">
      <div className="admin-page-header">
        <h1 className="admin-page-title">📄 Quản lý Nội dung</h1>
        <p className="admin-page-desc">Quản lý activities và documents trong hệ thống</p>
      </div>

      {/* Tabs */}
      <div className="admin-tabs">
        <button
          className={`admin-tab ${tab === 'activities' ? 'active' : ''}`}
          onClick={() => setTab('activities')}
        >
          🎯 Activities
        </button>
        <button
          className={`admin-tab ${tab === 'documents' ? 'active' : ''}`}
          onClick={() => setTab('documents')}
        >
          📄 Documents
        </button>
      </div>

      {tab === 'activities' ? <ActivitiesTab /> : <DocumentsTab />}
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
          placeholder="🔍 Tìm kiếm activity..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Host</th>
              <th>Category</th>
              <th>Participants</th>
              <th>Privacy</th>
              <th>Thời gian</th>
              <th>Actions</th>
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
            ) : activities.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--color-text-tertiary)' }}>
                  Không tìm thấy activity nào
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
                  <td className="admin-cell-muted" style={{ fontSize: 'var(--font-size-xs)' }}>
                    {formatDate(act.start_time)}
                  </td>
                  <td>
                    <button
                      className="admin-btn admin-btn-danger"
                      onClick={() => setDeleteId(act.id)}
                    >
                      🗑 Xoá
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
            <h3 className="admin-modal-title">⚠️ Xác nhận xoá Activity</h3>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
              Activity sẽ bị soft-delete và không hiển thị cho người dùng nữa. Hành động này có thể được khôi phục trong database.
            </p>
            <div className="admin-modal-actions">
              <button className="admin-modal-btn admin-modal-btn-cancel" onClick={() => setDeleteId(null)}>
                Huỷ
              </button>
              <button
                className="admin-modal-btn admin-modal-btn-confirm"
                style={{ background: 'var(--color-error)' }}
                onClick={() => handleDelete(deleteId)}
              >
                Xoá
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ── Documents Tab ──

function DocumentsTab() {
  const [documents, setDocuments] = useState<AdminDocumentItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const limit = 20;

  const [deleteId, setDeleteId] = useState<string | null>(null);

  const loadDocuments = useCallback(async () => {
    try {
      setLoading(true);
      const data = await adminApi.listDocuments({
        search: search || undefined,
        limit,
        offset: page * limit,
      });
      setDocuments(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoading(false);
    }
  }, [search, page]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  useEffect(() => {
    setPage(0);
  }, [search]);

  const handleDelete = async (id: string) => {
    try {
      await adminApi.deleteDocument(id);
      setDeleteId(null);
      loadDocuments();
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('vi-VN', {
      day: '2-digit', month: '2-digit', year: 'numeric',
    });
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <>
      <div className="admin-filters">
        <input
          type="text"
          className="admin-search-input"
          placeholder="🔍 Tìm kiếm document..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Author</th>
              <th>File</th>
              <th>Size</th>
              <th>Status</th>
              <th>Ngày tạo</th>
              <th>Actions</th>
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
            ) : documents.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--color-text-tertiary)' }}>
                  Không tìm thấy document nào
                </td>
              </tr>
            ) : (
              documents.map(doc => (
                <tr key={doc.id} style={doc.is_deleted ? { opacity: 0.5 } : {}}>
                  <td>
                    <span className="admin-user-cell-name">{doc.title}</span>
                  </td>
                  <td className="admin-cell-muted">@{doc.author_username || '—'}</td>
                  <td className="admin-cell-truncate admin-cell-muted">{doc.file_name}</td>
                  <td className="admin-cell-muted">{formatSize(doc.file_size)}</td>
                  <td>
                    <span className={`admin-badge ${doc.is_deleted ? 'admin-badge-inactive' : 'admin-badge-active'}`}>
                      {doc.is_deleted ? 'Deleted' : 'Active'}
                    </span>
                  </td>
                  <td className="admin-cell-muted">{formatDate(doc.created_at)}</td>
                  <td>
                    {!doc.is_deleted && (
                      <button
                        className="admin-btn admin-btn-danger"
                        onClick={() => setDeleteId(doc.id)}
                      >
                        🗑 Xoá
                      </button>
                    )}
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
            <h3 className="admin-modal-title">⚠️ Xác nhận xoá Document</h3>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
              Document sẽ bị soft-delete. File vẫn còn trên storage nhưng sẽ không hiển thị cho người dùng.
            </p>
            <div className="admin-modal-actions">
              <button className="admin-modal-btn admin-modal-btn-cancel" onClick={() => setDeleteId(null)}>
                Huỷ
              </button>
              <button
                className="admin-modal-btn admin-modal-btn-confirm"
                style={{ background: 'var(--color-error)' }}
                onClick={() => handleDelete(deleteId)}
              >
                Xoá
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
