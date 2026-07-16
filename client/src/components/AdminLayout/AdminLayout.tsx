import { useState } from 'react';
import { NavLink, Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import './AdminLayout.css';

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const initials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
    : user?.username?.slice(0, 2).toUpperCase() || '?';

  return (
    <div className="admin-wrapper">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="admin-overlay" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`admin-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="admin-sidebar-header">
          <Link to="/admin" className="admin-logo" onClick={() => setSidebarOpen(false)}>
            <span className="admin-logo-icon">⚡</span>
            <div>
              <div className="admin-logo-text">UniConnect</div>
              <div className="admin-logo-sub">Admin Panel</div>
            </div>
          </Link>
        </div>

        <nav className="admin-nav">
          <div className="admin-nav-section">
            <span className="admin-nav-label">Main</span>
            <NavLink
              to="/admin"
              end
              className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <span className="admin-nav-icon">📊</span>
              Dashboard
            </NavLink>
          </div>

          <div className="admin-nav-section">
            <span className="admin-nav-label">Management</span>
            <NavLink
              to="/admin/users"
              className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <span className="admin-nav-icon">👥</span>
              Users
            </NavLink>
            <NavLink
              to="/admin/reports"
              className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <span className="admin-nav-icon">🚩</span>
              Reports
            </NavLink>
            <NavLink
              to="/admin/content"
              className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <span className="admin-nav-icon">📄</span>
              Content
            </NavLink>
          </div>

          <div className="admin-nav-section">
            <span className="admin-nav-label">Quick Links</span>
            <Link
              to="/dashboard"
              className="admin-nav-link"
              onClick={() => setSidebarOpen(false)}
            >
              <span className="admin-nav-icon">🏠</span>
              Back to App
            </Link>
          </div>
        </nav>

        <div className="admin-sidebar-footer">
          <div className="admin-user-info">
            <div className="admin-user-avatar">{initials}</div>
            <div className="admin-user-details">
              <div className="admin-user-name">{user?.full_name || user?.username}</div>
              <div className="admin-user-role">Administrator</div>
            </div>
          </div>
          <button className="admin-logout-btn" onClick={handleLogout} title="Logout">
            🚪
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="admin-main">
        <header className="admin-header">
          <button
            className="admin-menu-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle sidebar"
          >
            <span /><span /><span />
          </button>
          <div className="admin-header-spacer" />
          <div className="admin-header-badge">Admin</div>
        </header>

        <div className="admin-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
