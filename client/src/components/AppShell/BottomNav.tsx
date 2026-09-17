import React from 'react';
import { NavLink } from 'react-router-dom';
import { Compass, Calendar, Users, User, Plus, ListTodo } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import './BottomNav.css';

export const BottomNav: React.FC = () => {
  const { user } = useAuth();

  const isOrgOrAdmin =
    user?.role === 'organization' ||
    user?.role === 'education_admin' ||
    user?.role === 'admin' ||
    user?.is_verified === true;

  return (
    <nav className="bottom-nav" aria-label="Thanh điều hướng di động">
      {/* 1. Khám phá */}
      <NavLink
        to="/dashboard"
        className={({ isActive }) =>
          `bottom-nav__item ${isActive ? 'bottom-nav__item--active' : ''}`
        }
        aria-label="Khám phá hoạt động"
      >
        <Compass size={22} className="bottom-nav__icon" />
        <span className="bottom-nav__label">Khám phá</span>
      </NavLink>

      {/* 2. Lịch của tôi */}
      <NavLink
        to="/calendar"
        className={({ isActive }) =>
          `bottom-nav__item ${isActive ? 'bottom-nav__item--active' : ''}`
        }
        aria-label="Lịch của tôi"
      >
        <Calendar size={22} className="bottom-nav__icon" />
        <span className="bottom-nav__label">Lịch</span>
      </NavLink>

      {/* 3. Trung tâm FAB (Tạo hoạt động nếu là Org/Admin; Hoạt động đã tham gia nếu là Student) */}
      {isOrgOrAdmin ? (
        <NavLink
          to="/activities/create"
          className="bottom-nav__fab-link"
          aria-label="Tạo hoạt động mới"
        >
          <div className="bottom-nav__fab" title="Tạo hoạt động mới">
            <Plus size={26} />
          </div>
        </NavLink>
      ) : (
        <NavLink
          to="/my-activities"
          className={({ isActive }) =>
            `bottom-nav__item ${isActive ? 'bottom-nav__item--active' : ''}`
          }
          aria-label="Hoạt động của tôi"
        >
          <ListTodo size={22} className="bottom-nav__icon" />
          <span className="bottom-nav__label">Của tôi</span>
        </NavLink>
      )}

      {/* 4. Câu lạc bộ */}
      <NavLink
        to="/groups"
        className={({ isActive }) =>
          `bottom-nav__item ${isActive ? 'bottom-nav__item--active' : ''}`
        }
        aria-label="Câu lạc bộ"
      >
        <Users size={22} className="bottom-nav__icon" />
        <span className="bottom-nav__label">CLB</span>
      </NavLink>

      {/* 5. Cá nhân */}
      <NavLink
        to="/profile"
        className={({ isActive }) =>
          `bottom-nav__item ${isActive ? 'bottom-nav__item--active' : ''}`
        }
        aria-label="Hồ sơ cá nhân và Trophy"
      >
        <User size={22} className="bottom-nav__icon" />
        <span className="bottom-nav__label">Cá nhân</span>
      </NavLink>
    </nav>
  );
};
