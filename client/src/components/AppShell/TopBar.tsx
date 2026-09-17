import React, { useEffect, useRef } from 'react';
import { Search } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import NotificationBell from '../NotificationBell/NotificationBell';
import './TopBar.css';

interface TopBarProps {
  isMobile?: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({ isMobile }) => {
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Global Ctrl + K / Cmd + K keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <header className="topbar" aria-label="Thanh điều khiển trên cùng">
      {/* Mobile Brand Logo */}
      {isMobile && (
        <NavLink to="/dashboard" className="topbar__mobile-brand">
          <div className="topbar__mobile-logo">U</div>
          <span className="topbar__mobile-title">UniConnect</span>
        </NavLink>
      )}

      {/* Global Search Box */}
      <div className="topbar__search-wrapper">
        <Search size={16} className="topbar__search-icon" aria-hidden="true" />
        <input
          ref={searchInputRef}
          type="search"
          className="topbar__search-input"
          placeholder="Tìm hoạt động, câu lạc bộ, bạn bè..."
          aria-label="Tìm kiếm toàn hệ thống"
        />
        <kbd className="topbar__search-kbd" title="Nhấn Ctrl + K để tìm nhanh">
          <span className="topbar__kbd-key">Ctrl</span> K
        </kbd>
      </div>

      {/* Actions: AI Assistant & Notification Bell */}
      <div className="topbar__actions">
        <NotificationBell />
      </div>
    </header>
  );
};
