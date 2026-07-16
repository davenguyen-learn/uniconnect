import { useState, useEffect, useCallback } from 'react';
import { adminApi, type AdminUserItem } from '../../api/admin';
import './AdminDashboard.css';

export default function AdminUsers() {
  const [users, setUsers] = useState<AdminUserItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(0);
  const limit = 20;

  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      const data = await adminApi.listUsers({
        search: search || undefined,
        role: roleFilter || undefined,
        is_active: statusFilter === '' ? undefined : statusFilter === 'true',
        limit,
        offset: page * limit,
      });
      setUsers(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setLoading(false);
    }
  }, [search, roleFilter, statusFilter, page]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // Reset page when filters change
  useEffect(() => {
    setPage(0);
  }, [search, roleFilter, statusFilter]);

  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      await adminApi.updateUserRole(userId, newRole);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, role: newRole } : u));
    } catch (err) {
      console.error('Failed to update role:', err);
    }
  };

  const handleStatusToggle = async (userId: string, currentActive: boolean) => {
    try {
      await adminApi.updateUserStatus(userId, !currentActive);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_active: !currentActive } : u));
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('vi-VN', {
      day: '2-digit', month: '2-digit', year: 'numeric'
    });
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="admin-dashboard">
      <div className="admin-page-header">
        <h1 className="admin-page-title">👥 Quản lý Users</h1>
        <p className="admin-page-desc">Tổng cộng {total} người dùng</p>
      </div>

      {/* Filters */}
      <div className="admin-filters">
        <input
          type="text"
          className="admin-search-input"
          placeholder="🔍 Tìm kiếm username, email, tên..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select
          className="admin-filter-select"
          value={roleFilter}
          onChange={e => setRoleFilter(e.target.value)}
        >
          <option value="">Tất cả roles</option>
          <option value="student">Student</option>
          <option value="moderator">Moderator</option>
          <option value="admin">Admin</option>
        </select>
        <select
          className="admin-filter-select"
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
        >
          <option value="">Tất cả status</option>
          <option value="true">Active</option>
          <option value="false">Inactive</option>
        </select>
      </div>

      {/* Table */}
      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Email</th>
              <th>University</th>
              <th>Role</th>
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
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--color-text-tertiary)' }}>
                  Không tìm thấy user nào
                </td>
              </tr>
            ) : (
              users.map(user => (
                <tr key={user.id}>
                  <td>
                    <div className="admin-user-cell">
                      <span className="admin-user-cell-name">{user.full_name || user.username}</span>
                      <span style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-xs)' }}>
                        @{user.username}
                      </span>
                    </div>
                  </td>
                  <td>{user.email}</td>
                  <td className="admin-cell-muted">{user.university || '—'}</td>
                  <td>
                    <span className={`admin-badge admin-badge-${user.role}`}>
                      {user.role}
                    </span>
                  </td>
                  <td>
                    <span className={`admin-badge admin-badge-${user.is_active ? 'active' : 'inactive'}`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="admin-cell-muted">{formatDate(user.created_at)}</td>
                  <td>
                    <div className="admin-actions-cell">
                      <select
                        className="admin-filter-select"
                        value={user.role}
                        onChange={e => handleRoleChange(user.id, e.target.value)}
                        style={{ padding: '4px 28px 4px 8px', fontSize: 'var(--font-size-xs)' }}
                      >
                        <option value="student">Student</option>
                        <option value="moderator">Moderator</option>
                        <option value="admin">Admin</option>
                      </select>
                      <button
                        className={`admin-btn ${user.is_active ? 'admin-btn-danger' : 'admin-btn-success'}`}
                        onClick={() => handleStatusToggle(user.id, user.is_active)}
                      >
                        {user.is_active ? 'Ban' : 'Unban'}
                      </button>
                    </div>
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
    </div>
  );
}
