import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { adminApi, type AdminStats, type AdminReportItem } from '../../api/admin';
import './AdminDashboard.css';

export default function AdminDashboard() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [recentReports, setRecentReports] = useState<AdminReportItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const [statsData, reportsData] = await Promise.all([
        adminApi.getStats(),
        adminApi.listReports({ status: 'pending', limit: 5 }),
      ]);
      setStats(statsData);
      setRecentReports(reportsData.items);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const timeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Vừa xong';
    if (mins < 60) return `${mins} phút trước`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours} giờ trước`;
    const days = Math.floor(hours / 24);
    return `${days} ngày trước`;
  };

  if (loading) {
    return (
      <div className="admin-dashboard">
        <div className="admin-page-header">
          <h1 className="admin-page-title">Dashboard</h1>
          <p className="admin-page-desc">Tổng quan hệ thống</p>
        </div>
        <div className="admin-stats-grid">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="admin-stat-card skeleton-card">
              <div className="skeleton" style={{ width: '60%', height: 16 }} />
              <div className="skeleton" style={{ width: '40%', height: 32, marginTop: 12 }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const statCards = [
    { label: 'Tổng Users', value: stats?.total_users ?? 0, icon: '👥', color: '#6c5ce7' },
    { label: 'Tổng Activities', value: stats?.total_activities ?? 0, icon: '🎯', color: '#00b894' },
    { label: 'Tổng Documents', value: stats?.total_documents ?? 0, icon: '📄', color: '#0984e3' },
    { label: 'Tổng Reports', value: stats?.total_reports ?? 0, icon: '🚩', color: '#e17055' },
    { label: 'Reports Pending', value: stats?.pending_reports ?? 0, icon: '⏳', color: '#fdcb6e' },
    { label: 'Users mới (tuần)', value: stats?.new_users_this_week ?? 0, icon: '✨', color: '#a29bfe' },
  ];

  return (
    <div className="admin-dashboard">
      <div className="admin-page-header">
        <h1 className="admin-page-title">Dashboard</h1>
        <p className="admin-page-desc">Tổng quan hệ thống UniConnect</p>
      </div>

      {/* Stats Grid */}
      <div className="admin-stats-grid">
        {statCards.map((card, idx) => (
          <div
            key={card.label}
            className="admin-stat-card"
            style={{ '--stat-color': card.color, animationDelay: `${idx * 60}ms` } as React.CSSProperties}
          >
            <div className="admin-stat-header">
              <span className="admin-stat-label">{card.label}</span>
              <span className="admin-stat-icon">{card.icon}</span>
            </div>
            <div className="admin-stat-value">{card.value.toLocaleString()}</div>
            <div className="admin-stat-glow" />
          </div>
        ))}
      </div>

      {/* Recent Reports */}
      <div className="admin-section">
        <div className="admin-section-header">
          <h2 className="admin-section-title">🚩 Reports chờ xử lý</h2>
          <Link to="/admin/reports" className="admin-section-link">
            Xem tất cả →
          </Link>
        </div>

        {recentReports.length === 0 ? (
          <div className="admin-empty-state">
            <span className="admin-empty-icon">✅</span>
            <p>Không có report nào cần xử lý!</p>
          </div>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Reporter</th>
                  <th>Loại</th>
                  <th>Lý do</th>
                  <th>Thời gian</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentReports.map(report => (
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
                    <td className="admin-cell-muted">{timeAgo(report.created_at)}</td>
                    <td>
                      <Link to="/admin/reports" className="admin-action-link">
                        Xử lý
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
