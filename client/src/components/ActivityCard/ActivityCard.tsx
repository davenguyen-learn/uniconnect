import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calendar,
  MapPin,
  AlertTriangle,
  CheckCircle2,
  Share2,
  ExternalLink,
  Trash2,
  User,
  FileText,
} from 'lucide-react';
import type { ActivityResponse } from '../../api/activities';
import {
  mapActivityToCardViewModel,
  type ActivityCardViewModel,
} from '../../types/activity-mapper';
import { useAuth } from '../../contexts/AuthContext';
import LikeButton from '../LikeButton/LikeButton';
import { formatCtxh } from '../../utils/format';
import './ActivityCard.css';

interface ActivityCardProps {
  activity: ActivityResponse;
  onClick?: () => void;
  onRegister?: (activityId: string) => void;
  onBookmark?: (activityId: string) => void;
  onShare?: (activityId: string) => void;
  onDelete?: (activityId: string) => void;
  onCertificate?: (activityId: string) => void;
  isRegistered?: boolean;
}

export const ActivityCardComponent: React.FC<ActivityCardProps> = ({
  activity,
  onClick,
  onRegister,
  onShare,
  onDelete,
  onCertificate,
  isRegistered = false,
}) => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const isHost = Boolean(user?.id && String(activity.host_id) === String(user.id));
  const effectiveIsRegistered =
    Boolean(isRegistered) ||
    Boolean(activity.joined_at) ||
    activity.attendance_confirmed !== undefined ||
    isHost;

  const vm: ActivityCardViewModel = mapActivityToCardViewModel(activity, effectiveIsRegistered, undefined, user?.id);

  const handleCardClick = () => {
    if (onClick) {
      onClick();
    } else {
      navigate(`/activities/${vm.id}`);
    }
  };

  const handleCtaClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isHost && onRegister && (vm.registrationState === 'available' || vm.registrationState === 'conflict_warn')) {
      onRegister(vm.id);
    } else {
      handleCardClick();
    }
  };

  const handleShareClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onShare) onShare(vm.id);
  };

  const getCategoryClass = (cat: string) => {
    const c = (cat || '').toLowerCase();
    if (c.includes('học thuật') || c.includes('study') || c.includes('kỹ thuật') || c.includes('học tập') || c.includes('workshop')) return 'study';
    if (c.includes('tình nguyện') || c.includes('ctxh') || c.includes('social')) return 'social';
    if (c.includes('thể thao') || c.includes('sports') || c.includes('vận động')) return 'sports';
    if (c.includes('câu lạc bộ') || c.includes('clb') || c.includes('đội nhóm') || c.includes('nhóm')) return 'club';
    if (c.includes('sự nghiệp') || c.includes('doanh nghiệp') || c.includes('career') || c.includes('hướng nghiệp') || c.includes('việc làm')) return 'career';
    return 'default';
  };

  return (
    <article
      className={`activity-card ${vm.isPast ? 'activity-card--past' : ''}`}
      onClick={handleCardClick}
      aria-label={`Hoạt động: ${vm.title}`}
    >
      {/* Tầng 1: Media Header (Chỉ hiển thị khi hoạt động thực sự có ảnh) */}
      {vm.coverUrl && (
        <div className="activity-card__media">
          <img
            src={vm.coverUrl}
            alt={vm.title}
            className="activity-card__cover-image"
            loading="lazy"
          />
          <span className={`activity-card__cover-category activity-card__cover-category--${getCategoryClass(vm.category)}`}>
            {vm.category}
          </span>

          {/* Floating Utility Actions */}
          <div className="activity-card__utilities">
            {onDelete && (
              <button
                type="button"
                className="activity-card__util-btn activity-card__util-btn--danger"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(vm.id);
                }}
                aria-label="Hủy hoạt động"
                title="Hủy hoạt động"
              >
                <Trash2 size={15} />
              </button>
            )}
            <button
              type="button"
              className="activity-card__util-btn"
              onClick={handleShareClick}
              aria-label="Chia sẻ hoạt động"
              title="Chia sẻ"
            >
              <Share2 size={15} />
            </button>
          </div>

          {/* Distance Badge */}
          {vm.distanceKm && (
            <span className="activity-card__distance-badge">
              <MapPin size={12} /> {vm.distanceKm}
            </span>
          )}
        </div>
      )}

      {/* Card Body */}
      <div className="activity-card__body">
        {/* Header hàng đầu khi hoạt động không có ảnh */}
        {!vm.coverUrl && (
          <div className="activity-card__header-row">
            <div className="activity-card__meta-tags">
              <span className="activity-card__category-tag">
                {vm.category}
              </span>
              {vm.distanceKm && (
                <span className="activity-card__distance-tag">
                  <MapPin size={12} /> {vm.distanceKm}
                </span>
              )}
            </div>

            <div className="activity-card__actions">
              {onDelete && (
                <button
                  type="button"
                  className="activity-card__action-btn activity-card__action-btn--danger"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(vm.id);
                  }}
                  aria-label="Hủy hoạt động"
                  title="Hủy hoạt động"
                >
                  <Trash2 size={15} />
                </button>
              )}
              <button
                type="button"
                className="activity-card__action-btn"
                onClick={handleShareClick}
                aria-label="Chia sẻ hoạt động"
                title="Chia sẻ"
              >
                <Share2 size={15} />
              </button>
            </div>
          </div>
        )}

        {/* Tầng 3: Secondary Badges (Hình thức tham gia, CTXH, Trophy, Co-organizer) */}
        <div className="activity-card__secondary-row">
          {vm.requireApproval ? (
            <span className="activity-badge activity-badge--approval" title="Cần người tổ chức phê duyệt để tham gia">
              <span>Cần phê duyệt</span>
            </span>
          ) : (
            <span className="activity-badge activity-badge--free" title="Tham gia tự do, không cần phê duyệt">
              <span>Tham gia tự do</span>
            </span>
          )}

          {vm.socialWorkDays && (
            <span className="activity-badge activity-badge--ctxh">
              <span>+{formatCtxh(vm.socialWorkDays)} ngày CTXH</span>
            </span>
          )}

          {vm.trophy && (
            <span className="activity-badge activity-badge--trophy">
              <span>{vm.trophy.name}</span>
            </span>
          )}

          {vm.coOrganizerName && (
            <span className="activity-badge activity-badge--cohost" title={`Đồng tổ chức: ${vm.coOrganizerName}`}>
              <span>🤝 {vm.coOrganizerName}</span>
            </span>
          )}
        </div>

        {/* Cảnh báo trùng lịch cá nhân (Bấm vào để chuyển đến hoạt động đang bị trùng lịch) */}
        {vm.hasConflict && (
          <div
            className={`activity-card__conflict-banner ${vm.conflictingTargetId ? 'activity-card__conflict-banner--clickable' : ''}`}
            role="alert"
            onClick={(e) => {
              if (vm.conflictingTargetId) {
                e.stopPropagation();
                if (vm.conflictingType === 'busy_slot') {
                  navigate('/calendar');
                } else {
                  navigate(`/activities/${vm.conflictingTargetId}`);
                }
              }
            }}
            title={vm.conflictingTargetId ? (vm.conflictingType === 'busy_slot' ? 'Xem lịch bận cá nhân trên Calendar' : 'Bấm để xem chi tiết hoạt động bị trùng lịch') : undefined}
          >
            <AlertTriangle size={14} className="activity-card__conflict-icon" />
            <span className="activity-card__conflict-text">
              {vm.conflictWarning || 'Trùng giờ với lịch cá nhân'}
            </span>
            {vm.conflictingTargetId && (
              <ExternalLink size={13} className="activity-card__conflict-link-icon" />
            )}
          </div>
        )}

        {/* Tầng 1: Title & Time/Venue Info */}
        <h3 className="activity-card__title" title={vm.title}>
          {vm.title}
        </h3>

        <div className="activity-card__meta">
          {vm.host && (
            <div className="activity-card__meta-item activity-card__meta-host">
              <User size={14} className="activity-card__meta-icon" />
              <span className="activity-card__meta-host-text">
                <span className="activity-card__host-prefix">Người tạo: </span>
                <span
                  role="button"
                  tabIndex={0}
                  className="activity-card__host-name"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/profile/${vm.host!.id}`);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.stopPropagation();
                      navigate(`/profile/${vm.host!.id}`);
                    }
                  }}
                  title={vm.host.fullName ? `${vm.host.fullName} (@${vm.host.username})` : `@${vm.host.username}`}
                >
                  {vm.host.fullName || `@${vm.host.username}`}
                </span>
                {vm.group && (
                  <>
                    <span className="activity-card__host-dot">•</span>
                    <span
                      role="button"
                      tabIndex={0}
                      className="activity-card__host-group"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/groups/${vm.group!.id}`);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.stopPropagation();
                          navigate(`/groups/${vm.group!.id}`);
                        }
                      }}
                      title={`Xem nhóm: ${vm.group.name}`}
                    >
                      {vm.group.name}
                    </span>
                  </>
                )}
                {vm.coHosts && vm.coHosts.length > 0 && (
                  <>
                    <span className="activity-card__host-dot">•</span>
                    <span className="activity-card__host-cohosts" title="Các đơn vị đồng tổ chức">
                      🤝 {vm.coHosts.map((ch, idx) => (
                        <span
                          key={ch.id}
                          role="button"
                          tabIndex={0}
                          className="activity-card__host-group"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/groups/${ch.id}`);
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.stopPropagation();
                              navigate(`/groups/${ch.id}`);
                            }
                          }}
                          title={`Xem nhóm đồng tổ chức: ${ch.name}`}
                        >
                          {idx > 0 ? ', ' : ''}{ch.name}
                        </span>
                      ))}
                    </span>
                  </>
                )}
              </span>
            </div>
          )}
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
            <span className="activity-card__capacity-label">Số người tham gia</span>
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
          <LikeButton
            targetType="activities"
            targetId={vm.id}
            autoFetch
            compact
          />

          {onCertificate && vm.isPast ? (
            <button
              type="button"
              className="card-btn card-btn--certificate"
              onClick={(e) => {
                e.stopPropagation();
                onCertificate(vm.id);
              }}
              title="Xuất Giấy chứng nhận / Minh chứng tham gia"
            >
              <FileText size={14} />
              <span>Xuất giấy xác nhận</span>
            </button>
          ) : (
            <>
              {vm.registrationState === 'available' && !isHost && (
                <button
                  type="button"
                  className="card-btn card-btn--primary"
                  onClick={handleCtaClick}
                >
                  Đăng ký ngay
                </button>
              )}

              {vm.registrationState === 'conflict_warn' && !isHost && (
                <button
                  type="button"
                  className="card-btn card-btn--warning"
                  onClick={handleCtaClick}
                >
                  <AlertTriangle size={14} />
                  <span>Đăng ký (Trùng lịch)</span>
                </button>
              )}

              {isHost && !vm.isPast && (
                <span className="card-badge-status card-badge-status--host">
                  <CheckCircle2 size={15} />
                  <span>Đang tổ chức</span>
                </span>
              )}

              {isHost && vm.isPast && (
                <span className="card-badge-status card-badge-status--host">
                  <CheckCircle2 size={15} />
                  <span>Đã tổ chức</span>
                </span>
              )}

              {!isHost && vm.registrationState === 'registered' && (
                <span className="card-badge-status card-badge-status--success">
                  <CheckCircle2 size={15} />
                  <span>{vm.isPast ? 'Đã tham gia' : 'Đã đăng ký'}</span>
                </span>
              )}

              {vm.registrationState === 'capacity_full' && !isHost && (
                <span className="card-badge-status card-badge-status--muted">
                  Đã đủ số lượng
                </span>
              )}

              {vm.registrationState === 'deadline_passed' && !isHost && (
                <span className="card-badge-status card-badge-status--muted">
                  Đã kết thúc
                </span>
              )}
            </>
          )}
        </div>
      </div>
    </article>
  );
};

// Export memoized component to prevent unnecessary re-renders during feed scrolling
export const ActivityCard = React.memo(ActivityCardComponent);
export default ActivityCard;
