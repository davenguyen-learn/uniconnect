import { useState, useRef, useEffect } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
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
            Discover
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/chat"
            className={({ isActive }) => `navbar-link ${isActive ? 'active' : ''}`}
            onClick={() => setMenuOpen(false)}
          >
            AI Chat
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/groups"
            className={({ isActive }) => `navbar-link ${isActive ? 'active' : ''}`}
            onClick={() => setMenuOpen(false)}
          >
            Groups
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/my-activities"
            className={({ isActive }) => `navbar-link ${isActive ? 'active' : ''}`}
            onClick={() => setMenuOpen(false)}
          >
            My Activities
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/documents"
            className={({ isActive }) => `navbar-link ${isActive ? 'active' : ''}`}
            onClick={() => setMenuOpen(false)}
          >
            Documents
          </NavLink>
        </li>
      </ul>

      <div className="navbar-actions">
        <div className="navbar-user-menu" ref={dropdownRef}>
          <button
            className="navbar-avatar"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            aria-label="User menu"
          >
            {initials}
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
                Profile
              </Link>
              <div className="navbar-dropdown-divider" />
              <button className="navbar-dropdown-item danger" onClick={handleLogout}>
                Log out
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
