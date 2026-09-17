import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calendar,
  MapPin,
  GraduationCap,
  Trophy,
  Handshake,
  AlertTriangle,
  CheckCircle2,
  Bookmark,
  Share2,
} from 'lucide-react';
import type { ActivityResponse } from '../../api/activities';
import {
  mapActivityToCardViewModel,
  type ActivityCardViewModel,
} from '../../types/activity-mapper';
import './ActivityCard.css';

interface ActivityCardProps {
  activity: ActivityResponse;
  onClick?: () => void;
  onRegister?: (activityId: string) => void;
  onBookmark?: (activityId: string) => void;
  onShare?: (activityId: string) => void;
  isRegistered?: boolean;
}

export const ActivityCardComponent: React.FC<ActivityCardProps> = ({
  activity,
  onClick,
  onRegister,
  onBookmark,
  onShare,
  isRegistered = false,
}) => {
  const navigate = useNavigate();
  const vm: ActivityCardViewModel = mapActivityToCardViewModel(activity, isRegistered);

  const handleCardClick = () => {
    if (onClick) {
      onClick();
    } else {
      navigate(`/activities/${vm.id}`);
    }
  };

  const handleCtaClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onRegister && (vm.registrationState === 'available' || vm.registrationState === 'conflict_warn')) {
      onRegister(vm.id);
    } else {
      handleCardClick();
    }
  };

  const handleBookmarkClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onBookmark) onBookmark(vm.id);
  };

  const handleShareClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onShare) onShare(vm.id);
  };

  return (
    <article
      className={`activity-card ${vm.isPast ? 'activity-card--past' : ''}`}
      onClick={handleCardClick}
      aria-label={`Hoạt động: ${vm.title}`}
    >
      {/* Tầng 1: Media Header */}
      <div className="activity-card__media">
        <div className="activity-card__cover-placeholder" aria-hidden="true">
          <span className="activity-card__cover-category">{vm.category}</span>
        </div>

        {/* Floating Utility Actions (Tầng 4) */}
        <div className="activity-card__utilities">
          <button
            type="button"
            className="activity-card__util-btn"
            onClick={handleBookmarkClick}
            aria-label="Lưu hoạt động vào danh sách yêu thích"
            title="Lưu hoạt động"
          >
            <Bookmark size={16} />
          </button>
          <button
            type="button"
            className="activity-card__util-btn"
            onClick={handleShareClick}
            aria-label="Chia sẻ hoạt động"
            title="Chia sẻ"
          >
            <Share2 size={16} />
          </button>
        </div>

        {/* Distance Badge */}
        {vm.distanceKm && (
          <span className="activity-card__distance-badge">
            <MapPin size={12} /> {vm.distanceKm}
          </span>
        )}
      </div>

      {/* Card Body */}
      <div className="activity-card__body">
        {/* Tầng 3: Secondary Badges (CTXH, Trophy, Co-organizer) */}
        <div className="activity-card__secondary-row">
          {vm.socialWorkDays && (
            <span className="activity-badge activity-badge--ctxh">
              <GraduationCap size={13} />
              <span>+{vm.socialWorkDays} ngày CTXH</span>
            </span>
          )}

          {vm.trophy && (
            <span className="activity-badge activity-badge--trophy">
              <Trophy size={13} />
              <span>{vm.trophy.name}</span>
            </span>
          )}

          {vm.coOrganizerName && (
            <span className="activity-badge activity-badge--cohost">
              <Handshake size={13} />
              <span>{vm.coOrganizerName}</span>
            </span>
          )}
        </div>

        {/* Conflict Warning Banner if any */}
        {vm.hasConflict && (
          <div className="activity-card__conflict-banner" role="alert">
            <AlertTriangle size={14} className="activity-card__conflict-icon" />
            <span>{vm.conflictWarning || 'Trùng giờ với lịch cá nhân'}</span>
          </div>
        )}

        {/* Tầng 1: Title & Time/Venue Info */}
        <h3 className="activity-card__title" title={vm.title}>
          {vm.title}
        </h3>

        <div className="activity-card__meta">
          <div className="activity-card__meta-item">
            <Calendar size={14} className="activity-card__meta-icon" />
            <span>{vm.startTimeFormatted}</span>
          </div>
          <div className="activity-card__meta-item">
            <MapPin size={14} className="activity-card__meta-icon" />
            <span className="activity-card__meta-venue">{vm.locationName}</span>
          </div>
        </div>

        {/* Tầng 2: Status & Capacity Progress */}
        <div className="activity-card__capacity">
          <div className="activity-card__capacity-header">
            <span className="activity-card__capacity-label">Chỗ tham gia</span>
            <span className="activity-card__capacity-numbers">
              {vm.currentParticipants} / {vm.maxParticipants}
            </span>
          </div>
          <div className="activity-card__progress-track" aria-hidden="true">
            <div
              className={`activity-card__progress-fill ${
                vm.percentFilled >= 100
                  ? 'activity-card__progress-fill--full'
                  : vm.percentFilled >= 80
                  ? 'activity-card__progress-fill--warn'
                  : ''
              }`}
              style={{ width: `${vm.percentFilled}%` }}
            />
          </div>
        </div>

        {/* Tầng 2: Primary CTA mapped to RegistrationState */}
        <div className="activity-card__cta-row">
          {vm.registrationState === 'available' && (
            <button
              type="button"
              className="card-btn card-btn--primary"
              onClick={handleCtaClick}
            >
              Đăng ký ngay
            </button>
          )}

          {vm.registrationState === 'conflict_warn' && (
            <button
              type="button"
              className="card-btn card-btn--warning"
              onClick={handleCtaClick}
            >
              <AlertTriangle size={14} />
              <span>Đăng ký (Trùng lịch)</span>
            </button>
          )}

          {vm.registrationState === 'registered' && (
            <span className="card-badge-status card-badge-status--success">
              <CheckCircle2 size={15} />
              <span>Đã tham gia</span>
            </span>
          )}

          {vm.registrationState === 'capacity_full' && (
            <span className="card-badge-status card-badge-status--muted">
              Đã đủ số lượng
            </span>
          )}

          {vm.registrationState === 'deadline_passed' && (
            <span className="card-badge-status card-badge-status--muted">
              Đã kết thúc
            </span>
          )}
        </div>
      </div>
    </article>
  );
};

// Export memoized component to prevent unnecessary re-renders during feed scrolling
export const ActivityCard = React.memo(ActivityCardComponent);
export default ActivityCard;
