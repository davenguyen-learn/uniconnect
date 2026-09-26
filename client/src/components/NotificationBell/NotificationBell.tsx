import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell } from 'lucide-react';
import { notificationsApi, type NotificationResponse } from '../../api/notifications';
import { useAuth } from '../../contexts/AuthContext';
import { resolveAvatarUrl } from '../../utils/avatar';
import './NotificationBell.css';

function NotificationItemAvatar({
  avatarUrl,
  name,
}: {
  avatarUrl?: string | null;
  name?: string | null;
}) {
  const [hasError, setHasError] = useState(false);
  const resolvedSrc = resolveAvatarUrl(avatarUrl);
  const initial = (name?.trim()?.charAt(0) || '?').toUpperCase();

  if (resolvedSrc && !hasError) {
    return (
      <img
        src={resolvedSrc}
        alt={name || 'User'}
        onError={() => setHasError(true)}
      />
    );
  }

  return <div className="avatar-placeholder">{initial}</div>;
}

export default function NotificationBell() {
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { user } = useAuth();
  const navigate = useNavigate();

  const fetchNotifications = async () => {
    if (!user) return;
    try {
      const data = await notificationsApi.listNotifications({ limit: 10 });
      setNotifications(data.items);
      setUnreadCount(data.unread_count);
    } catch (err) {
      console.error('Failed to fetch notifications', err);
    }
  };

  useEffect(() => {
    fetchNotifications();
    // Poll every 30 seconds
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [user]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleNotificationClick = async (notification: NotificationResponse) => {
    if (!notification.is_read) {
      try {
        await notificationsApi.markAsRead(notification.id);
        setUnreadCount(prev => Math.max(0, prev - 1));
        setNotifications(prev => 
          prev.map(n => n.id === notification.id ? { ...n, is_read: true } : n)
        );
      } catch (err) {
        console.error('Failed to mark read', err);
      }
    }

    setIsOpen(false);

    // Navigate to target
    if (notification.action_url) {
      navigate(notification.action_url);
    } else {
      const targetActivityId = notification.activity_id || notification.target_id;
      if (targetActivityId) {
        navigate(`/activities/${targetActivityId}`);
      } else {
        navigate(`/map`);
      }
    }
  };

  const handleMarkAllRead = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await notificationsApi.markAllAsRead();
      setUnreadCount(0);
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (err) {
      console.error('Failed to mark all read', err);
    }
  };

  if (!user) return null;

  return (
    <div className="notification-container" ref={dropdownRef}>
      <button 
        className="notification-bell" 
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Thông báo"
      >
        <Bell size={20} className="bell-icon" strokeWidth={1.8} />
        {unreadCount > 0 && (
          <span className="notification-badge">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="notification-dropdown">
          <div className="notification-header">
            <h3>Thông báo</h3>
            {unreadCount > 0 && (
              <button className="mark-all-btn" onClick={handleMarkAllRead}>
                Đánh dấu đã đọc tất cả
              </button>
            )}
          </div>
          
          <div className="notification-list">
            {notifications.length === 0 ? (
              <div className="notification-empty">Chưa có thông báo nào</div>
            ) : (
              notifications.map(notification => (
                <div 
                  key={notification.id} 
                  className={`notification-item ${!notification.is_read ? 'unread' : ''}`}
                  onClick={() => handleNotificationClick(notification)}
                >
                  <div className="notification-avatar">
                    <NotificationItemAvatar
                      avatarUrl={notification.actor?.avatar_url}
                      name={notification.actor?.full_name || notification.actor?.username}
                    />
                  </div>
                  <div className="notification-content">
                    <p>{notification.message}</p>
                    <span className="notification-time">
                      {new Date(notification.created_at).toLocaleDateString()} {new Date(notification.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </span>
                  </div>
                  {!notification.is_read && <div className="unread-dot"></div>}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
