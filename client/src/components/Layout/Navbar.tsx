import { useState, useRef, useEffect } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import NotificationBell from '../NotificationBell/NotificationBell';
import './Navbar.css';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleLogout = () => {
    logout();
    setDropdownOpen(false);
    navigate('/');
  };

  const [imageError, setImageError] = useState(false);

  useEffect(() => {
    setImageError(false);
  }, [user?.avatar_url]);

  const resolveAvatarUrl = (url: string | null | undefined): string | null => {
    if (!url) return null;
    if (url.startsWith('http://') || url.startsWith('https://')) return url;
    const serverOrigin = import.meta.env.VITE_API_URL?.replace('/api/v1', '') || 'http://localhost:8000';
    return `${serverOrigin}${url}`;
  };

  const avatarSrc = resolveAvatarUrl(user?.avatar_url);

  const initials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
    : user?.username?.slice(0, 2).toUpperCase() || '?';

  return (
    <nav className="navbar">
      <Link to="/dashboard" className="navbar-brand">
        <span className="navbar-brand-icon">U</span>
        UniConnect
      </Link>

      <button
        className="navbar-toggle"
        onClick={() => setMenuOpen(!menuOpen)}
        aria-label="Toggle navigation"
      >
        <span />
        <span />
        <span />
      </button>

      <ul className={`navbar-links ${menuOpen ? 'open' : ''}`}>
        <li>
          <NavLink
            to="/dashboard"
            className={({ isActive }) => `navbar-link ${isActive ? 'active' : ''}`}
            onClick={() => setMenuOpen(false)}
          >
            Khám phá
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/chat"
            className={({ isActive }) => `navbar-link ${isActive ? 'active' : ''}`}
            onClick={() => setMenuOpen(false)}
          >
            Chat AI
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/groups"
            className={({ isActive }) => `navbar-link ${isActive ? 'active' : ''}`}
            onClick={() => setMenuOpen(false)}
          >
            Nhóm
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/my-activities"
            className={({ isActive }) => `navbar-link ${isActive ? 'active' : ''}`}
            onClick={() => setMenuOpen(false)}
          >
            Hoạt động của tôi
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/calendar"
            className={({ isActive }) => `navbar-link ${isActive ? 'active' : ''}`}
            onClick={() => setMenuOpen(false)}
          >
            Lịch của tôi
          </NavLink>
        </li>
      </ul>

      <div className="navbar-actions">
        <NotificationBell />
        <div className="navbar-user-menu" ref={dropdownRef}>
          <button
            className="navbar-avatar"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            aria-label="User menu"
          >
            {avatarSrc && !imageError ? (
              <img
                src={avatarSrc}
                alt="Avatar"
                className="navbar-avatar-img"
                onError={() => setImageError(true)}
              />
            ) : (
              initials
            )}
          </button>

          {dropdownOpen && (
            <div className="navbar-dropdown">
              <div style={{ padding: 'var(--space-2) var(--space-3)', marginBottom: 'var(--space-1)' }}>
                <div style={{ fontWeight: 'var(--font-weight-semibold)', fontSize: 'var(--font-size-sm)' }}>
                  {user?.full_name || user?.username}
                </div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)' }}>
                  {user?.email}
                </div>
              </div>
              <div className="navbar-dropdown-divider" />
              <Link
                to="/profile"
                className="navbar-dropdown-item"
                onClick={() => setDropdownOpen(false)}
              >
                Hồ sơ
              </Link>
              {user?.role === 'admin' && (
                <>
                  <div className="navbar-dropdown-divider" />
                  <Link
                    to="/admin"
                    className="navbar-dropdown-item"
                    onClick={() => setDropdownOpen(false)}
                  >
                    Trang Quản trị
                  </Link>
                </>
              )}
              <div className="navbar-dropdown-divider" />
              <button className="navbar-dropdown-item" onClick={handleLogout}>
                Đăng xuất
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
