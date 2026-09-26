import React, { useEffect, useRef, useState } from 'react';
import { Search, Loader2, Calendar, Users as UsersIcon, User, X } from 'lucide-react';
import { NavLink, useNavigate } from 'react-router-dom';
import NotificationBell from '../NotificationBell/NotificationBell';
import { activitiesApi, type ActivityResponse } from '../../api/activities';
import { groupsApi, type GroupResponse } from '../../api/groups';
import { usersApi, type UserProfile } from '../../api/users';
import './TopBar.css';

interface TopBarProps {
  isMobile?: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({ isMobile }) => {
  const searchInputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const [activityResults, setActivityResults] = useState<ActivityResponse[]>([]);
  const [groupResults, setGroupResults] = useState<GroupResponse[]>([]);
  const [userResults, setUserResults] = useState<UserProfile[]>([]);

  // Global Ctrl + K / Cmd + K keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        searchInputRef.current?.focus();
        setIsOpen(true);
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Handle clicking outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        searchInputRef.current &&
        !searchInputRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search trigger
  useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      setActivityResults([]);
      setGroupResults([]);
      setUserResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const [actRes, grpRes, usrRes] = await Promise.allSettled([
          activitiesApi.list({ search: trimmed, limit: 5 }),
          groupsApi.discoverGroups({ search: trimmed, limit: 5 }),
          usersApi.searchUsers(trimmed, 5),
        ]);

        if (actRes.status === 'fulfilled') {
          setActivityResults(actRes.value.items || []);
        } else {
          setActivityResults([]);
        }

        if (grpRes.status === 'fulfilled') {
          setGroupResults(grpRes.value || []);
        } else {
          setGroupResults([]);
        }

        if (usrRes.status === 'fulfilled') {
          setUserResults(usrRes.value || []);
        } else {
          setUserResults([]);
        }
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setLoading(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query]);

  const handleSelectResult = (path: string) => {
    setIsOpen(false);
    setQuery('');
    navigate(path);
  };

  const handleClear = () => {
    setQuery('');
    setActivityResults([]);
    setGroupResults([]);
    setUserResults([]);
    searchInputRef.current?.focus();
  };

  const hasResults =
    activityResults.length > 0 || groupResults.length > 0 || userResults.length > 0;

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
          placeholder="Tìm hoạt động, nhóm, bạn bè..."
          aria-label="Tìm kiếm toàn hệ thống"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => {
            if (query.trim()) setIsOpen(true);
          }}
        />

        {loading ? (
          <Loader2 size={16} className="topbar__search-spinner animate-spin" />
        ) : query ? (
          <button
            type="button"
            className="topbar__search-clear"
            onClick={handleClear}
            title="Xóa tìm kiếm"
          >
            <X size={14} />
          </button>
        ) : (
          <kbd className="topbar__search-kbd" title="Nhấn Ctrl + K để tìm nhanh">
            <span className="topbar__kbd-key">Ctrl</span> K
          </kbd>
        )}

        {/* Search Results Dropdown */}
        {isOpen && query.trim().length > 0 && (
          <div ref={dropdownRef} className="topbar__search-dropdown glass">
            {loading && !hasResults && (
              <div className="topbar__search-empty">
                <Loader2 size={18} className="animate-spin inline mr-2" />
                Đang tìm kiếm...
              </div>
            )}

            {!loading && !hasResults && (
              <div className="topbar__search-empty">
                Không tìm thấy kết quả phù hợp với "<strong>{query}</strong>"
              </div>
            )}

            {/* Activities Section */}
            {activityResults.length > 0 && (
              <div className="topbar__search-section">
                <div className="topbar__search-section-title">
                  <Calendar size={13} /> Hoạt động ({activityResults.length})
                </div>
                {activityResults.map((act) => (
                  <div
                    key={act.id}
                    className="topbar__search-item"
                    onClick={() => handleSelectResult(`/activities/${act.id}`)}
                  >
                    <div className="topbar__search-item-info">
                      <span className="topbar__search-item-title">{act.title}</span>
                      <span className="topbar__search-item-sub">
                        {act.category || 'Chung'} • {act.meeting_location || act.location_name || 'Địa điểm TBD'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Groups Section */}
            {groupResults.length > 0 && (
              <div className="topbar__search-section">
                <div className="topbar__search-section-title">
                  <UsersIcon size={13} /> Nhóm ({groupResults.length})
                </div>
                {groupResults.map((grp) => (
                  <div
                    key={grp.id}
                    className="topbar__search-item"
                    onClick={() => handleSelectResult(`/groups/${grp.id}`)}
                  >
                    <div className="topbar__search-item-avatar">
                      {grp.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="topbar__search-item-info">
                      <span className="topbar__search-item-title">{grp.name}</span>
                      <span className="topbar__search-item-sub">
                        {grp.member_count} thành viên {grp.privacy ? `• ${grp.privacy === 'public' ? 'Công khai' : 'Riêng tư'}` : ''}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Users Section */}
            {userResults.length > 0 && (
              <div className="topbar__search-section">
                <div className="topbar__search-section-title">
                  <User size={13} /> Bạn bè & Sinh viên ({userResults.length})
                </div>
                {userResults.map((u) => (
                  <div
                    key={u.id}
                    className="topbar__search-item"
                    onClick={() => handleSelectResult(`/profile/${u.id}`)}
                  >
                    <div className="topbar__search-item-avatar topbar__search-item-avatar--user">
                      {u.avatar_url ? (
                        <img src={u.avatar_url} alt={u.username} />
                      ) : (
                        u.username.charAt(0).toUpperCase()
                      )}
                    </div>
                    <div className="topbar__search-item-info">
                      <span className="topbar__search-item-title">
                        @{u.username}
                        {u.full_name && <span className="topbar__search-item-realname"> ({u.full_name})</span>}
                      </span>
                      <span className="topbar__search-item-sub">
                        {u.university || 'Sinh viên'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="topbar__actions">
        <NotificationBell />
      </div>
    </header>
  );
};

