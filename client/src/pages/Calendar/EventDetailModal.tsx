import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, Clock, MapPin, Repeat, Trash2, ExternalLink, X } from 'lucide-react';
import type { CalendarEventViewModel } from '../../types/calendar-mapper';

interface EventDetailModalProps {
  event: CalendarEventViewModel | null;
  isOpen: boolean;
  onClose: () => void;
  onDeleteSlot?: (event: CalendarEventViewModel) => Promise<void>;
  deleting?: boolean;
}

export const EventDetailModal: React.FC<EventDetailModalProps> = ({
  event,
  isOpen,
  onClose,
  onDeleteSlot,
  deleting = false,
}) => {
  const navigate = useNavigate();

  if (!isOpen || !event) return null;

  const isBusySlot = event.eventType === 'busy_slot';
  const isActivity = event.eventType === 'activity_joined' || event.eventType === 'activity_hosted';

  const handleNavigateToActivity = () => {
    if (event.activityId) {
      onClose();
      navigate(`/activities/${event.activityId}`);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content event-detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="event-detail-header-badge">
            <span className={`legend-dot dot-${event.colorTag}`} />
            <span className="event-detail-type-text">{event.typeLabel}</span>
          </div>
          <button
            type="button"
            className="btn-close-modal"
            onClick={onClose}
            aria-label="Đóng chi tiết sự kiện"
          >
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          <h3 className="event-detail-title">{event.title}</h3>

          <div className="event-detail-meta-list">
            <div className="event-meta-item">
              <Calendar size={18} className="event-meta-icon" />
              <span>{event.dateDisplay}</span>
            </div>

            <div className="event-meta-item">
              <Clock size={18} className="event-meta-icon" />
              <span>{event.timeRange}</span>
            </div>

            {event.locationName && (
              <div className="event-meta-item">
                <MapPin size={18} className="event-meta-icon" />
                <span>{event.locationName}</span>
              </div>
            )}

            {event.isRecurring && (
              <div className="event-meta-item">
                <Repeat size={18} className="event-meta-icon" />
                <span className="card-badge-recurring">Lặp lại hàng tuần theo lịch đăng ký</span>
              </div>
            )}
          </div>
        </div>

        <div className="modal-footer">
          {isBusySlot && onDeleteSlot && (
            <button
              type="button"
              className="btn-danger-action"
              onClick={() => onDeleteSlot(event)}
              disabled={deleting}
            >
              <Trash2 size={16} />
              {deleting ? 'Đang xóa...' : 'Xóa Lịch Bận'}
            </button>
          )}

          {isActivity && (
            <button
              type="button"
              className="btn-primary"
              onClick={handleNavigateToActivity}
            >
              <ExternalLink size={16} />
              Xem Chi Tiết Hoạt Động
            </button>
          )}

          <button type="button" className="btn-secondary" onClick={onClose}>
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
};
