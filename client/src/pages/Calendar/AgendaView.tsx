import React from 'react';
import { Calendar, Clock, MapPin, Repeat, CalendarX } from 'lucide-react';
import {
  groupEventsByDate,
  type CalendarEventViewModel,
} from '../../types/calendar-mapper';

interface AgendaViewProps {
  events: CalendarEventViewModel[];
  onSelectEvent: (event: CalendarEventViewModel) => void;
}

export const AgendaView: React.FC<AgendaViewProps> = ({ events, onSelectEvent }) => {
  const dayGroups = groupEventsByDate(events);

  if (dayGroups.length === 0) {
    return (
      <div className="agenda-empty-state">
        <CalendarX size={44} className="agenda-empty-icon" />
        <h4>Không có lịch trình trong khoảng thời gian này</h4>
        <p>Tất cả các ngày đều đang trống lịch. Bạn có thể thêm lịch bận cá nhân hoặc khám phá hoạt động để đăng ký.</p>
      </div>
    );
  }

  return (
    <div className="agenda-view-container">
      {dayGroups.map((group) => (
        <div
          key={group.dateKey}
          className={`agenda-day-section ${group.isToday ? 'is-today-section' : ''}`}
        >
          <div className="agenda-date-header">
            <Calendar size={16} className="agenda-date-icon" />
            <span className="agenda-date-title">{group.dateTitle}</span>
            <span className="agenda-day-count-badge">
              {group.events.length} sự kiện
            </span>
          </div>

          <div className="agenda-events-list">
            {group.events.map((ev) => (
              <div
                key={ev.id}
                className={`agenda-card card-${ev.colorTag}`}
                onClick={() => onSelectEvent(ev)}
                tabIndex={0}
                role="button"
                aria-label={`Xem ${ev.title}`}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelectEvent(ev);
                  }
                }}
              >
                <div className="agenda-card-indicator" />

                <div className="agenda-card-main">
                  <div className="agenda-card-top">
                    <span className={`agenda-tag tag-${ev.colorTag}`}>
                      {ev.typeLabel}
                    </span>
                    {ev.isRecurring && (
                      <span className="card-badge-recurring">
                        <Repeat size={12} /> Lặp tuần
                      </span>
                    )}
                  </div>

                  <h4 className="agenda-card-title">{ev.title}</h4>

                  <div className="agenda-card-meta">
                    <div className="agenda-meta-item">
                      <Clock size={14} />
                      <span>{ev.timeRange}</span>
                    </div>

                    {ev.locationName && (
                      <div className="agenda-meta-item">
                        <MapPin size={14} />
                        <span>{ev.locationName}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
