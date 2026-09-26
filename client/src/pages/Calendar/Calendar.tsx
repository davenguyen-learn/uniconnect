import React, { useState, useEffect, useMemo } from 'react';
import {
  Calendar as CalendarIcon,
  CalendarDays,
  ListFilter,
  ChevronLeft,
  ChevronRight,
  Plus,
  SlidersHorizontal,
  Clock,
  MapPin,
  Repeat,
  Trash2,
  X,
} from 'lucide-react';
import {
  calendarApi,
  type BusySlotCreate,
} from '../../api/calendar';
import {
  mapCalendarEventToViewModel,
  DAYS_OF_WEEK_VI,
  type CalendarEventViewModel,
} from '../../types/calendar-mapper';
import { EventDetailModal } from './EventDetailModal';
import { BusySlotManagerModal } from './BusySlotManagerModal';
import { AgendaView } from './AgendaView';
import { useToast } from '../../components/Toast/ToastContext';
import './Calendar.css';

export default function CalendarPage() {
  const toast = useToast();

  const [currentDate, setCurrentDate] = useState<Date>(new Date());
  const [viewMode, setViewMode] = useState<'week' | 'month' | 'agenda'>('week');
  const [events, setEvents] = useState<CalendarEventViewModel[]>([]);
  const [loading, setLoading] = useState(false);

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showManagerModal, setShowManagerModal] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEventViewModel | null>(null);
  const [savingSlot, setSavingSlot] = useState(false);
  const [deletingSlot, setDeletingSlot] = useState(false);

  const [slotForm, setSlotForm] = useState<BusySlotCreate>({
    title: '',
    recurrence: 'weekly',
    day_of_week: 0,
    start_time_of_day: '07:30',
    end_time_of_day: '11:30',
    start_datetime: '',
    end_datetime: '',
    valid_from: new Date().toISOString().split('T')[0],
    valid_until: '',
  });

  // Calculate start and end date for current view
  const { viewStartDate, viewEndDate, weekDays } = useMemo(() => {
    if (viewMode === 'week') {
      const d = new Date(currentDate);
      const day = d.getDay(); // 0 is Sunday, 1 is Monday...
      const diff = d.getDate() - day + (day === 0 ? -6 : 1);
      const monday = new Date(d.setDate(diff));
      monday.setHours(0, 0, 0, 0);

      const days: Date[] = [];
      for (let i = 0; i < 7; i++) {
        const nextDay = new Date(monday);
        nextDay.setDate(monday.getDate() + i);
        days.push(nextDay);
      }

      const sunday = new Date(days[6]);
      sunday.setHours(23, 59, 59, 999);

      return {
        viewStartDate: monday.toISOString().split('T')[0],
        viewEndDate: sunday.toISOString().split('T')[0],
        weekDays: days,
      };
    } else if (viewMode === 'month') {
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth();
      const firstDay = new Date(year, month, 1);

      const startDayOffset = firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1;
      const calStart = new Date(firstDay);
      calStart.setDate(firstDay.getDate() - startDayOffset);

      const calEnd = new Date(calStart);
      calEnd.setDate(calStart.getDate() + 41);

      return {
        viewStartDate: calStart.toISOString().split('T')[0],
        viewEndDate: calEnd.toISOString().split('T')[0],
        weekDays: [],
      };
    } else {
      // Agenda View: from Monday of current week to +35 days
      const d = new Date(currentDate);
      const day = d.getDay();
      const diff = d.getDate() - day + (day === 0 ? -6 : 1);
      const monday = new Date(d.setDate(diff));
      monday.setHours(0, 0, 0, 0);

      const end = new Date(monday);
      end.setDate(monday.getDate() + 35);
      end.setHours(23, 59, 59, 999);

      return {
        viewStartDate: monday.toISOString().split('T')[0],
        viewEndDate: end.toISOString().split('T')[0],
        weekDays: [],
      };
    }
  }, [currentDate, viewMode]);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const data = await calendarApi.getEvents(viewStartDate, viewEndDate);
      // Map server events into ViewModel with 0 client calculation
      setEvents(data.map(mapCalendarEventToViewModel));
    } catch (err: any) {
      toast.error('Không thể tải dữ liệu lịch: ' + (err.message || 'Lỗi kết nối'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [viewStartDate, viewEndDate]);

  // Navigation handlers
  const handlePrev = () => {
    const d = new Date(currentDate);
    if (viewMode === 'week') {
      d.setDate(d.getDate() - 7);
    } else if (viewMode === 'month') {
      d.setMonth(d.getMonth() - 1);
    } else {
      d.setDate(d.getDate() - 14);
    }
    setCurrentDate(d);
  };

  const handleNext = () => {
    const d = new Date(currentDate);
    if (viewMode === 'week') {
      d.setDate(d.getDate() + 7);
    } else if (viewMode === 'month') {
      d.setMonth(d.getMonth() + 1);
    } else {
      d.setDate(d.getDate() + 14);
    }
    setCurrentDate(d);
  };

  const handleToday = () => {
    setCurrentDate(new Date());
  };

  // Submit Busy Slot
  const handleSaveSlot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!slotForm.title.trim()) {
      toast.error('Vui lòng nhập tiêu đề lịch bận');
      return;
    }

    setSavingSlot(true);
    try {
      const payload: BusySlotCreate = {
        title: slotForm.title.trim(),
        recurrence: slotForm.recurrence,
      };

      if (slotForm.recurrence === 'weekly') {
        payload.day_of_week = Number(slotForm.day_of_week);
        payload.start_time_of_day = slotForm.start_time_of_day;
        payload.end_time_of_day = slotForm.end_time_of_day;
        payload.valid_from = slotForm.valid_from || null;
        payload.valid_until = slotForm.valid_until || null;
      } else {
        payload.start_datetime = new Date(slotForm.start_datetime || '').toISOString();
        payload.end_datetime = new Date(slotForm.end_datetime || '').toISOString();
      }

      await calendarApi.createBusySlot(payload);
      toast.success('Đã thêm lịch bận thành công!');
      setShowCreateModal(false);
      // Reset form
      setSlotForm({
        title: '',
        recurrence: 'weekly',
        day_of_week: 0,
        start_time_of_day: '07:30',
        end_time_of_day: '11:30',
        start_datetime: '',
        end_datetime: '',
        valid_from: new Date().toISOString().split('T')[0],
        valid_until: '',
      });
      fetchEvents();
    } catch (err: any) {
      toast.error(err.message || 'Không thể tạo lịch bận');
    } finally {
      setSavingSlot(false);
    }
  };

  // Delete Busy Slot via Event
  const handleDeleteSlot = async (eventItem: CalendarEventViewModel) => {
    if (!window.confirm(`Bạn có chắc chắn muốn xóa lịch bận "${eventItem.title}"?`)) return;

    // extract busy slot id from id format (e.g. busy_weekly_UUID_date or busy_oneoff_UUID)
    const parts = eventItem.id.split('_');
    const slotId = parts[2] || parts[1];

    setDeletingSlot(true);
    try {
      await calendarApi.deleteBusySlot(slotId);
      toast.success('Đã xóa lịch bận');
      setSelectedEvent(null);
      fetchEvents();
    } catch (err: any) {
      toast.error('Không thể xóa: ' + err.message);
    } finally {
      setDeletingSlot(false);
    }
  };

  const formatPeriodLabel = () => {
    const month = currentDate.getMonth() + 1;
    const year = currentDate.getFullYear();
    if (viewMode === 'week') {
      return `Tháng ${month}, ${year}`;
    } else if (viewMode === 'month') {
      return `Tháng ${month} năm ${year}`;
    }
    return `Lịch trình Tháng ${month}, ${year}`;
  };

  return (
    <div className="calendar-page">
      {/* Header */}
      <div className="calendar-header">
        <div className="calendar-title-group">
          <h1>Lịch cá nhân</h1>
        </div>

        <div className="calendar-header-actions">
          <button
            type="button"
            className="btn-manage-rules"
            onClick={() => setShowManagerModal(true)}
            aria-label="Quản lý các quy tắc lịch bận"
          >
            <SlidersHorizontal size={16} />
            <span>Quản Lý Lịch Bận</span>
          </button>

          <button
            type="button"
            className="btn-add-slot"
            onClick={() => setShowCreateModal(true)}
            aria-label="Thêm lịch bận mới"
          >
            <Plus size={16} />
            <span>Thêm Lịch Bận</span>
          </button>
        </div>
      </div>

      {/* Controls Bar */}
      <div className="calendar-controls">
        <div className="nav-buttons">
          <button
            type="button"
            className="btn-nav-arrow"
            onClick={handlePrev}
            aria-label="Thời gian trước"
          >
            <ChevronLeft size={18} />
          </button>
          <button type="button" className="btn-today" onClick={handleToday}>
            Hôm nay
          </button>
          <button
            type="button"
            className="btn-nav-arrow"
            onClick={handleNext}
            aria-label="Thời gian sau"
          >
            <ChevronRight size={18} />
          </button>
          <span className="current-period-label">{formatPeriodLabel()}</span>
          {loading && <span className="loading-tag">Đang đồng bộ...</span>}
        </div>

        <div className="view-mode-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === 'week'}
            className={`view-tab ${viewMode === 'week' ? 'active' : ''}`}
            onClick={() => setViewMode('week')}
          >
            <CalendarIcon size={15} />
            <span>Tuần</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === 'month'}
            className={`view-tab ${viewMode === 'month' ? 'active' : ''}`}
            onClick={() => setViewMode('month')}
          >
            <CalendarDays size={15} />
            <span>Tháng</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === 'agenda'}
            className={`view-tab ${viewMode === 'agenda' ? 'active' : ''}`}
            onClick={() => setViewMode('agenda')}
          >
            <ListFilter size={15} />
            <span>Lịch trình</span>
          </button>
        </div>
      </div>

      {/* Legend Bar */}
      <div className="calendar-legend">
        <div className="legend-item">
          <span className="legend-dot dot-busy" />
          <span>Lịch cá nhân</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot dot-joined" />
          <span>Hoạt động đã đăng ký</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot dot-hosted" />
          <span>Hoạt động bạn tổ chức</span>
        </div>
      </div>

      {/* View: Week Grid */}
      {viewMode === 'week' && (
        <div className="week-grid">
          {weekDays.map((dayDate, idx) => {
            const isToday = dayDate.toDateString() === new Date().toDateString();
            const dateStr = dayDate.toISOString().split('T')[0];

            const dayEvents = events.filter((ev) => ev.dateKey === dateStr);

            return (
              <div key={idx} className="week-day-col">
                <div className={`week-day-header ${isToday ? 'is-today' : ''}`}>
                  <span className="day-name">{DAYS_OF_WEEK_VI[idx]}</span>
                  <span className={`day-number ${isToday ? 'highlight-today' : ''}`}>
                    {dayDate.getDate()}
                  </span>
                </div>

                <div className="week-day-events">
                  {dayEvents.length === 0 ? (
                    <div className="no-events-hint">Rảnh cả ngày</div>
                  ) : (
                    dayEvents.map((ev) => (
                      <div
                        key={ev.id}
                        className={`calendar-card card-${ev.colorTag}`}
                        onClick={() => setSelectedEvent(ev)}
                        tabIndex={0}
                        role="button"
                        aria-label={`Xem chi tiết ${ev.title}`}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            setSelectedEvent(ev);
                          }
                        }}
                      >
                        {ev.eventType === 'busy_slot' && (
                          <button
                            type="button"
                            className="btn-card-del"
                            title="Xóa lịch bận"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteSlot(ev);
                            }}
                          >
                            <Trash2 size={13} />
                          </button>
                        )}
                        <div className="card-time">
                          <Clock size={12} className="inline-icon" />
                          <span>{ev.timeRange}</span>
                        </div>
                        <div className="card-title" title={ev.title}>{ev.title}</div>
                        {ev.isRecurring && (
                          <span className="card-badge-recurring">
                            <Repeat size={10} /> Lặp tuần
                          </span>
                        )}
                        {ev.locationName && (
                          <div className="card-location">
                            <MapPin size={11} className="inline-icon" />
                            <span>{ev.locationName}</span>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* View: Month Grid */}
      {viewMode === 'month' && (
        <div className="month-grid">
          <div className="month-days-header">
            {DAYS_OF_WEEK_VI.map((d, i) => (
              <div key={i}>{d}</div>
            ))}
          </div>

          <div className="month-cells-grid">
            {Array.from({ length: 42 }).map((_, i) => {
              const cellDate = new Date(viewStartDate);
              cellDate.setDate(cellDate.getDate() + i);
              const dateStr = cellDate.toISOString().split('T')[0];
              const isCurrentMonth = cellDate.getMonth() === currentDate.getMonth();
              const isToday = cellDate.toDateString() === new Date().toDateString();

              const dayEvents = events.filter((ev) => ev.dateKey === dateStr);

              return (
                <div
                  key={i}
                  className={`month-cell ${!isCurrentMonth ? 'is-other-month' : ''} ${isToday ? 'is-today' : ''
                    }`}
                >
                  <div className="month-cell-header">
                    <span className="month-cell-num">{cellDate.getDate()}</span>
                  </div>
                  <div className="month-cell-content">
                    {dayEvents.slice(0, 3).map((ev) => (
                      <div
                        key={ev.id}
                        className={`month-event-pill pill-${ev.colorTag}`}
                        title={`${ev.title} (${ev.timeRange})`}
                        onClick={() => setSelectedEvent(ev)}
                      >
                        <span className="pill-time">{ev.timeRange.split(' - ')[0]}</span>
                        <span className="pill-title">{ev.title}</span>
                      </div>
                    ))}
                    {dayEvents.length > 3 && (
                      <span
                        className="month-more-count"
                        onClick={() => {
                          setCurrentDate(cellDate);
                          setViewMode('agenda');
                        }}
                      >
                        +{dayEvents.length - 3} lịch khác
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* View: Agenda View */}
      {viewMode === 'agenda' && (
        <AgendaView events={events} onSelectEvent={(ev) => setSelectedEvent(ev)} />
      )}

      {/* Event Detail Modal */}
      <EventDetailModal
        event={selectedEvent}
        isOpen={Boolean(selectedEvent)}
        onClose={() => setSelectedEvent(null)}
        onDeleteSlot={handleDeleteSlot}
        deleting={deletingSlot}
      />

      {/* Busy Slot Rule Manager Modal */}
      <BusySlotManagerModal
        isOpen={showManagerModal}
        onClose={() => setShowManagerModal(false)}
        onOpenCreateModal={() => setShowCreateModal(true)}
        onRulesChanged={fetchEvents}
      />

      {/* Modal Thêm Lịch Bận */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)} role="dialog" aria-modal="true">
          <div className="modal-content create-slot-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Thêm Lịch Bận Cá Nhân</h3>
              <button
                type="button"
                className="btn-close-modal"
                onClick={() => setShowCreateModal(false)}
                aria-label="Đóng biểu mẫu"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSaveSlot}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Tiêu đề lịch bận *</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Ví dụ: Học Thể Dục, Ca trực lab, Học Tiếng Anh..."
                    value={slotForm.title}
                    onChange={(e) => setSlotForm({ ...slotForm, title: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Hình thức lặp</label>
                  <div className="recurrence-toggle">
                    <button
                      type="button"
                      className={`recurrence-btn ${slotForm.recurrence === 'weekly' ? 'active' : ''}`}
                      onClick={() => setSlotForm({ ...slotForm, recurrence: 'weekly' })}
                    >
                      <Repeat size={14} /> Lặp hàng tuần
                    </button>
                    <button
                      type="button"
                      className={`recurrence-btn ${slotForm.recurrence === 'none' ? 'active' : ''}`}
                      onClick={() => setSlotForm({ ...slotForm, recurrence: 'none' })}
                    >
                      Chỉ bận 1 lần
                    </button>
                  </div>
                </div>

                {slotForm.recurrence === 'weekly' ? (
                  <>
                    {/* Presets shortcut */}


                    <div className="form-group">
                      <label>Ngày trong tuần *</label>
                      <select
                        className="form-control"
                        value={slotForm.day_of_week ?? 0}
                        onChange={(e) => setSlotForm({ ...slotForm, day_of_week: Number(e.target.value) })}
                      >
                        {DAYS_OF_WEEK_VI.map((name, idx) => (
                          <option key={idx} value={idx}>
                            {name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="form-row">
                      <div className="form-group">
                        <label>Giờ bắt đầu *</label>
                        <input
                          type="time"
                          className="form-control"
                          value={slotForm.start_time_of_day || ''}
                          onChange={(e) => setSlotForm({ ...slotForm, start_time_of_day: e.target.value })}
                          required
                        />
                      </div>
                      <div className="form-group">
                        <label>Giờ kết thúc *</label>
                        <input
                          type="time"
                          className="form-control"
                          value={slotForm.end_time_of_day || ''}
                          onChange={(e) => setSlotForm({ ...slotForm, end_time_of_day: e.target.value })}
                          required
                        />
                      </div>
                    </div>

                    <div className="form-row">
                      <div className="form-group">
                        <label>Hiệu lực từ ngày</label>
                        <input
                          type="date"
                          className="form-control"
                          value={slotForm.valid_from || ''}
                          onChange={(e) => setSlotForm({ ...slotForm, valid_from: e.target.value })}
                        />
                      </div>
                      <div className="form-group">
                        <label>Đến ngày</label>
                        <input
                          type="date"
                          className="form-control"
                          value={slotForm.valid_until || ''}
                          onChange={(e) => setSlotForm({ ...slotForm, valid_until: e.target.value })}
                        />
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="form-group">
                      <label>Thời điểm bắt đầu *</label>
                      <input
                        type="datetime-local"
                        className="form-control"
                        value={slotForm.start_datetime || ''}
                        onChange={(e) => setSlotForm({ ...slotForm, start_datetime: e.target.value })}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label>Thời điểm kết thúc *</label>
                      <input
                        type="datetime-local"
                        className="form-control"
                        value={slotForm.end_datetime || ''}
                        onChange={(e) => setSlotForm({ ...slotForm, end_datetime: e.target.value })}
                        required
                      />
                    </div>
                  </>
                )}
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowCreateModal(false)}
                >
                  Hủy
                </button>
                <button type="submit" className="btn-primary" disabled={savingSlot}>
                  {savingSlot ? 'Đang lưu...' : 'Lưu Lịch Bận'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
