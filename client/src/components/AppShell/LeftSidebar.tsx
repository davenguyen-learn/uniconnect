import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  Compass,
  Calendar,
  Users,
  Trophy,
  PlusCircle,
  LogOut,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Moon,
  Sun,
  LayoutDashboard,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import './LeftSidebar.css';

interface LeftSidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export const LeftSidebar: React.FC<LeftSidebarProps> = ({
  isCollapsed,
  onToggleCollapse,
}) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isDarkMode, setIsDarkMode] = React.useState(() => {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  });

  const toggleTheme = () => {
    const nextTheme = isDarkMode ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', nextTheme);
    setIsDarkMode(!isDarkMode);
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isOrgOrAdmin =
    user?.role === 'organization' ||
    user?.role === 'education_admin' ||
    user?.role === 'admin' ||
    user?.is_verified === true;

  const isAdmin = user?.role === 'admin' || user?.role === 'education_admin';

  const initials = user?.full_name
    ? user.full_name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .slice(0, 2)
        .toUpperCase()
    : user?.username?.slice(0, 2).toUpperCase() || 'U';

  return (
    <aside
      className={`left-sidebar ${isCollapsed ? 'left-sidebar--collapsed' : ''}`}
      aria-label="Thanh điều hướng chính"
    >
      {/* Brand Header */}
      <div className="sidebar__header">
        <NavLink to="/dashboard" className="sidebar__brand">
          <div className="sidebar__brand-logo" aria-hidden="true">
            <span>U</span>
          </div>
          {!isCollapsed && (
            <div className="sidebar__brand-info">
              <span className="sidebar__brand-title">UniConnect</span>
              <span className="sidebar__brand-subtitle">Campus Network</span>
            </div>
          )}
        </NavLink>

        <button
          type="button"
          className="sidebar__collapse-btn"
          onClick={onToggleCollapse}
          aria-label={isCollapsed ? 'Mở rộng thanh điều hướng' : 'Thu gọn thanh điều hướng'}
          title={isCollapsed ? 'Mở rộng' : 'Thu gọn'}
        >
          {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      {/* Primary Navigation Menu */}
      <nav className="sidebar__nav" aria-label="Menu điều hướng">
        <ul className="sidebar__nav-list">
          <li className="sidebar__nav-item">
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                `sidebar__nav-link ${isActive ? 'sidebar__nav-link--active' : ''}`
              }
              title="Khám phá"
            >
              <Compass size={20} className="sidebar__nav-icon" />
              {!isCollapsed && <span className="sidebar__nav-label">Khám phá</span>}
            </NavLink>
          </li>

          <li className="sidebar__nav-item">
            <NavLink
              to="/calendar"
              className={({ isActive }) =>
                `sidebar__nav-link ${isActive ? 'sidebar__nav-link--active' : ''}`
              }
              title="Lịch của tôi"
            >
              <Calendar size={20} className="sidebar__nav-icon" />
              {!isCollapsed && <span className="sidebar__nav-label">Lịch của tôi</span>}
            </NavLink>
          </li>

          <li className="sidebar__nav-item">
            <NavLink
              to="/groups"
              className={({ isActive }) =>
                `sidebar__nav-link ${isActive ? 'sidebar__nav-link--active' : ''}`
              }
              title="Câu lạc bộ"
            >
              <Users size={20} className="sidebar__nav-icon" />
              {!isCollapsed && <span className="sidebar__nav-label">Câu lạc bộ</span>}
            </NavLink>
          </li>

          <li className="sidebar__nav-item">
            <NavLink
              to="/profile"
              className={({ isActive }) =>
                `sidebar__nav-link ${isActive ? 'sidebar__nav-link--active' : ''}`
              }
              title="Trophy & Thành tích"
            >
              <Trophy size={20} className="sidebar__nav-icon" />
              {!isCollapsed && <span className="sidebar__nav-label">Trophy & Minh chứng</span>}
            </NavLink>
          </li>

          {isAdmin && (
            <li className="sidebar__nav-item">
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  `sidebar__nav-link ${isActive ? 'sidebar__nav-link--active' : ''}`
                }
                title="Quản trị trường"
              >
                <LayoutDashboard size={20} className="sidebar__nav-icon" />
                {!isCollapsed && <span className="sidebar__nav-label">Quản trị</span>}
              </NavLink>
            </li>
          )}
        </ul>
      </nav>

      {/* Primary CTA: Only for Verified Organization / Admins */}
      {isOrgOrAdmin && (
        <div className="sidebar__cta-container">
          <NavLink
            to="/activities/create"
            className="sidebar__cta-btn"
            title="Tạo hoạt động mới"
            aria-label="Tạo hoạt động mới"
          >
            <PlusCircle size={20} />
            {!isCollapsed && <span>Tạo hoạt động</span>}
          </NavLink>
        </div>
      )}

      {/* Footer Profile & Utility */}
      <div className="sidebar__footer">
        <div className="sidebar__user-card">
          <NavLink to="/profile" className="sidebar__user-link" title="Xem hồ sơ cá nhân">
            <div className="sidebar__user-avatar" aria-hidden="true">
              {initials}
            </div>
            {!isCollapsed && (
              <div className="sidebar__user-details">
                <div className="sidebar__user-name-row">
                  <span className="sidebar__user-name">{user?.full_name || user?.username}</span>
                  {user?.is_verified && (
                    <span title="Tổ chức đã xác minh" className="sidebar__verified-wrapper">
                      <ShieldCheck size={14} className="sidebar__verified-badge" />
                    </span>
                  )}
                </div>
                <span className="sidebar__user-role">
                  {user?.role === 'organization'
                    ? 'Ban Tổ chức'
                    : user?.role === 'education_admin'
                    ? 'Quản lý Giáo dục'
                    : user?.role === 'admin'
                    ? 'Quản trị viên'
                    : 'Sinh viên'}
                </span>
              </div>
            )}
          </NavLink>

          <div className="sidebar__user-actions">
            <button
              type="button"
              className="sidebar__action-icon-btn"
              onClick={toggleTheme}
              aria-label={isDarkMode ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối'}
              title={isDarkMode ? 'Giao diện sáng' : 'Giao diện tối'}
            >
              {isDarkMode ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <button
              type="button"
              className="sidebar__action-icon-btn sidebar__action-icon-btn--danger"
              onClick={handleLogout}
              aria-label="Đăng xuất khỏi tài khoản"
              title="Đăng xuất"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
};
