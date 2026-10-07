import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  SlidersHorizontal,
  Sparkles,
  UserCheck,
  Calendar as CalendarIcon,
  History,
  Clock,
  CheckCircle2,
  Trash2,
  XCircle,
  Award,
  CalendarOff,
  Users,
  X,
} from 'lucide-react';
import { activitiesApi, type ActivityResponse } from '../../api/activities';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../components/Toast/ToastContext';
import Button from '../../components/Button/Button';
import CollectionLayout from '../../components/Layout/CollectionLayout';
import ActivityCard from '../../components/ActivityCard/ActivityCard';
import { CertificateModal } from '../../components/CertificateModal/CertificateModal';
import './MyActivities.css';

export type RoleFilter = 'all' | 'hosting';
export type TimeFilter = 'all' | 'upcoming' | 'past';
export type StatusFilter =
  | 'all'
  | 'pending'
  | 'approved'
  | 'canceled'
  | 'denied'
  | 'attended'
  | 'absent';

function getEffectiveRegistrationStatus(act: ActivityResponse, now: Date): string | undefined {
  const status = act.registration_status?.toLowerCase();
  if (status === 'pending') {
    // Nếu hoạt động đã tới giờ bắt đầu mà vẫn pending => coi như bị từ chối
    const startTime = new Date(act.start_time);
    if (startTime <= now) {
      return 'declined';
    }
  }
  return status;
}

export default function MyActivities() {
  const { user } = useAuth();
  const toast = useToast();
  const [allActivities, setAllActivities] = useState<ActivityResponse[]>([]);
  const [loading, setLoading] = useState(true);

  // Combinable multi-dimensional filters
  const [filterHosting, setFilterHosting] = useState(false);
  const [filterGroup, setFilterGroup] = useState(false);
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('all');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');

  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCertificateActivityId, setSelectedCertificateActivityId] = useState<string | null>(null);

  useEffect(() => {
    loadActivities();
  }, []);

  async function loadActivities() {
    try {
      setLoading(true);
      const [joinedRes, hostedRes] = await Promise.all([
        activitiesApi.getJoinedActivities({ limit: 100 }),
        activitiesApi.getMyActivities({ limit: 100 }),
      ]);

      const map = new Map<string, ActivityResponse>();
      // Process hosted activities
      for (const act of hostedRes.items) {
        map.set(act.id, act);
      }
      // Process joined activities (merge and preserve joined_at, attendance status, registration status)
      for (const act of joinedRes.items) {
        if (!map.has(act.id)) {
          map.set(act.id, act);
        } else {
          const existing = map.get(act.id)!;
          if (act.joined_at && !existing.joined_at) {
            existing.joined_at = act.joined_at;
          }
          if (act.attendance_confirmed !== undefined) {
            existing.attendance_confirmed = act.attendance_confirmed;
          }
          if (act.registration_status) {
            existing.registration_status = act.registration_status;
          }
        }
      }

      const combined = Array.from(map.values());
      // Sort by action timestamp (time user joined or created the activity, newest first)
      combined.sort((a, b) => {
        const timeA = new Date(a.joined_at || a.created_at).getTime();
        const timeB = new Date(b.joined_at || b.created_at).getTime();
        return timeB - timeA;
      });

      setAllActivities(combined);
    } catch {
      toast.error('Không thể tải danh sách hoạt động');
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteActivity(activityId: string) {
    const confirm = window.confirm('Bạn có chắc chắn muốn hủy hoạt động này? Hành động này không thể hoàn tác.');
    if (!confirm) return;

    try {
      await activitiesApi.delete(activityId);
      toast.success('Đã hủy hoạt động thành công');
      // Mark as deleted so it appears under Canceled filter
      setAllActivities((prev) =>
        prev.map((a) => (a.id === activityId ? { ...a, is_deleted: true } : a))
      );
    } catch (error: any) {
      toast.error(error?.message || 'Không thể hủy hoạt động');
    }
  }

  const handleShare = (actId: string) => {
    const shareUrl = `${window.location.origin}/activities/${actId}`;
    navigator.clipboard.writeText(shareUrl).then(() => {
      toast.success('Đã sao chép liên kết hoạt động!');
    }).catch(() => {
      toast.info(`Liên kết: ${shareUrl}`);
    });
  };

  const counts = useMemo(() => {
    const now = new Date();
    const isHost = (a: ActivityResponse) => a.host_id === user?.id;
    const isGroup = (a: ActivityResponse) => Boolean(a.group_id || a.group || (a.co_hosts && a.co_hosts.length > 0));

    return {
      // Role & Scope
      all: allActivities.filter((a) => !a.is_deleted).length,
      hosting: allActivities.filter((a) => isHost(a) && !a.is_deleted).length,
      group: allActivities.filter((a) => isGroup(a) && !a.is_deleted).length,

      // Time
      timeAll: allActivities.filter((a) => !a.is_deleted).length,
      timeUpcoming: allActivities.filter((a) => new Date(a.end_time) >= now && !a.is_deleted).length,
      timePast: allActivities.filter((a) => new Date(a.end_time) < now && !a.is_deleted).length,

      // Status
      statusAll: allActivities.filter((a) => !a.is_deleted).length,
      statusPending: allActivities.filter(
        (a) => !isHost(a) && !a.is_deleted && getEffectiveRegistrationStatus(a, now) === 'pending'
      ).length,
      statusApproved: allActivities.filter(
        (a) =>
          !isHost(a) &&
          !a.is_deleted &&
          (getEffectiveRegistrationStatus(a, now) === 'approved' || (!a.registration_status && a.joined_at))
      ).length,
      statusCanceled: allActivities.filter((a) => isHost(a) && a.is_deleted === true).length,
      statusDenied: allActivities.filter(
        (a) =>
          !isHost(a) &&
          (getEffectiveRegistrationStatus(a, now) === 'declined' ||
            getEffectiveRegistrationStatus(a, now) === 'denied')
      ).length,
      statusAttended: allActivities.filter((a) => !isHost(a) && !a.is_deleted && a.attendance_confirmed === true).length,
      statusAbsent: allActivities.filter(
        (a) =>
          !isHost(a) &&
          !a.is_deleted &&
          new Date(a.end_time) < now &&
          (getEffectiveRegistrationStatus(a, now) === 'approved' || (!a.registration_status && a.joined_at)) &&
          !a.attendance_confirmed
      ).length,
    };
  }, [allActivities, user?.id]);

  const timeFilters = [
    { id: 'all' as TimeFilter, label: 'Tất cả', icon: Sparkles, count: counts.timeAll },
    { id: 'upcoming' as TimeFilter, label: 'Sắp diễn ra', icon: CalendarIcon, count: counts.timeUpcoming },
    { id: 'past' as TimeFilter, label: 'Đã diễn ra', icon: History, count: counts.timePast },
  ];

  const statusFilters = [
    { id: 'all' as StatusFilter, label: 'Tất cả', icon: Sparkles, count: counts.statusAll },
    { id: 'pending' as StatusFilter, label: 'Chờ duyệt', icon: Clock, count: counts.statusPending },
    { id: 'approved' as StatusFilter, label: 'Đã được duyệt', icon: CheckCircle2, count: counts.statusApproved },
    { id: 'canceled' as StatusFilter, label: 'Đã hủy', icon: Trash2, count: counts.statusCanceled },
    { id: 'denied' as StatusFilter, label: 'Bị từ chối', icon: XCircle, count: counts.statusDenied },
    { id: 'attended' as StatusFilter, label: 'Đã điểm danh', icon: Award, count: counts.statusAttended },
    { id: 'absent' as StatusFilter, label: 'Bị đánh vắng', icon: CalendarOff, count: counts.statusAbsent },
  ];

  const activeFilterCount =
    (filterHosting ? 1 : 0) +
    (filterGroup ? 1 : 0) +
    (timeFilter !== 'all' ? 1 : 0) +
    (statusFilter !== 'all' ? 1 : 0);

  const resetAllFilters = () => {
    setFilterHosting(false);
    setFilterGroup(false);
    setTimeFilter('all');
    setStatusFilter('all');
  };

  const filteredActivities = useMemo(() => {
    const now = new Date();
    const isHost = (a: ActivityResponse) => a.host_id === user?.id;
    const isGroup = (a: ActivityResponse) => Boolean(a.group_id || a.group || (a.co_hosts && a.co_hosts.length > 0));

    return allActivities.filter((act) => {
      // 1. Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchTitle = act.title.toLowerCase().includes(q);
        const matchLocation = (act.meeting_location || act.location_name || '').toLowerCase().includes(q);
        if (!matchTitle && !matchLocation) return false;
      }

      const effectiveStatus = getEffectiveRegistrationStatus(act, now);

      // 2. Scope filter (Hosting / Group)
      if (filterHosting && !isHost(act)) {
        return false;
      }
      if (filterGroup && !isGroup(act)) {
        return false;
      }

      // 3. Time filter
      if (timeFilter === 'upcoming' && new Date(act.end_time) < now) {
        return false;
      }
      if (timeFilter === 'past' && new Date(act.end_time) >= now) {
        return false;
      }

      // 4. Status filter
      if (statusFilter === 'canceled') {
        // Canceled targets hosted activities that were cancelled/deleted
        return isHost(act) && act.is_deleted === true;
      }

      // If status filter is not 'canceled', always hide deleted activities
      if (act.is_deleted) {
        return false;
      }

      if (statusFilter === 'pending') {
        return !isHost(act) && effectiveStatus === 'pending';
      }
      if (statusFilter === 'approved') {
        return !isHost(act) && (effectiveStatus === 'approved' || (!act.registration_status && act.joined_at));
      }
      if (statusFilter === 'denied') {
        return !isHost(act) && (effectiveStatus === 'declined' || effectiveStatus === 'denied');
      }
      if (statusFilter === 'attended') {
        return !isHost(act) && act.attendance_confirmed === true;
      }
      if (statusFilter === 'absent') {
        return (
          !isHost(act) &&
          new Date(act.end_time) < now &&
          (effectiveStatus === 'approved' || (!act.registration_status && act.joined_at)) &&
          !act.attendance_confirmed
        );
      }

      return true;
    });
  }, [allActivities, searchQuery, filterHosting, filterGroup, timeFilter, statusFilter, user?.id]);

  return (
    <>
      <CollectionLayout
        title="Hoạt động của tôi"
        gridColumns={2}
        searchPlaceholder="Tìm theo tên hoạt động hoặc địa điểm..."
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
        extraFilters={
          <button
            type="button"
            className={`my-filter-toggle-btn ${showFilterPanel ? 'my-filter-toggle-btn--open' : ''} ${activeFilterCount > 0 ? 'my-filter-toggle-btn--has-active' : ''}`}
            onClick={() => setShowFilterPanel(!showFilterPanel)}
            title="Bộ lọc hoạt động"
          >
            <SlidersHorizontal size={16} />
            <span>Bộ lọc</span>
            {activeFilterCount > 0 && (
              <span className="my-filter-badge">{activeFilterCount}</span>
            )}
          </button>
        }
        loading={loading}
        loadingMessage="Đang tải hoạt động..."
        isEmpty={filteredActivities.length === 0}
        emptyTitle={
          allActivities.length === 0
            ? 'Chưa có hoạt động nào'
            : 'Không tìm thấy hoạt động phù hợp'
        }
        emptyMessage={
          allActivities.length === 0
            ? 'Bạn chưa tham gia hay tổ chức hoạt động nào. Hãy khám phá các sự kiện thú vị quanh bạn!'
            : 'Không có hoạt động nào khớp với bộ lọc hoặc từ khóa tìm kiếm.'
        }
        emptyAction={
          allActivities.length === 0 ? (
            <Link to="/dashboard">
              <Button variant="secondary">Khám phá hoạt động</Button>
            </Link>
          ) : (
            <Button
              variant="secondary"
              onClick={() => {
                resetAllFilters();
                setSearchQuery('');
              }}
            >
              Xem tất cả
            </Button>
          )
        }
        filterPanel={
          <>
            {/* Active Filter Pill Summary */}
            {activeFilterCount > 0 && (
              <div className="my-active-filter-row">
                <span className="my-active-filter-label">Đang lọc:</span>

                {filterHosting && (
                  <span className="my-active-pill">
                    <UserCheck size={13} />
                    <span>Bản thân tổ chức ({counts.hosting})</span>
                    <button
                      type="button"
                      onClick={() => setFilterHosting(false)}
                      aria-label="Bỏ lọc vai trò"
                      title="Bỏ lọc vai trò"
                    >
                      <X size={12} />
                    </button>
                  </span>
                )}

                {filterGroup && (
                  <span className="my-active-pill">
                    <Users size={13} />
                    <span>Thuộc về nhóm ({counts.group})</span>
                    <button
                      type="button"
                      onClick={() => setFilterGroup(false)}
                      aria-label="Bỏ lọc hoạt động nhóm"
                      title="Bỏ lọc hoạt động nhóm"
                    >
                      <X size={12} />
                    </button>
                  </span>
                )}

                {timeFilter !== 'all' && (
                  <span className="my-active-pill">
                    {timeFilter === 'upcoming' ? <CalendarIcon size={13} /> : <History size={13} />}
                    <span>
                      {timeFilter === 'upcoming' ? 'Sắp diễn ra' : 'Đã diễn ra'} (
                      {timeFilter === 'upcoming' ? counts.timeUpcoming : counts.timePast})
                    </span>
                    <button
                      type="button"
                      onClick={() => setTimeFilter('all')}
                      aria-label="Bỏ lọc thời gian"
                      title="Bỏ lọc thời gian"
                    >
                      <X size={12} />
                    </button>
                  </span>
                )}

                {statusFilter !== 'all' && (
                  <span className="my-active-pill">
                    {statusFilter === 'pending' && <Clock size={13} />}
                    {statusFilter === 'approved' && <CheckCircle2 size={13} />}
                    {statusFilter === 'canceled' && <Trash2 size={13} />}
                    {statusFilter === 'denied' && <XCircle size={13} />}
                    {statusFilter === 'attended' && <Award size={13} />}
                    {statusFilter === 'absent' && <CalendarOff size={13} />}
                    <span>
                      {statusFilters.find((s) => s.id === statusFilter)?.label} (
                      {statusFilters.find((s) => s.id === statusFilter)?.count})
                    </span>
                    <button
                      type="button"
                      onClick={() => setStatusFilter('all')}
                      aria-label="Bỏ lọc trạng thái"
                      title="Bỏ lọc trạng thái"
                    >
                      <X size={12} />
                    </button>
                  </span>
                )}

                <button
                  type="button"
                  className="my-btn-reset-filters"
                  onClick={resetAllFilters}
                >
                  Đặt lại
                </button>
              </div>
            )}

            {/* Collapsible Filter Panel */}
            {showFilterPanel && (
              <div className="my-filter-panel">
                {/* Nhóm 1: Vai trò & Nguồn tổ chức */}
                <div className="my-filter-section">
                  <span className="my-filter-title">Vai trò & Nguồn tổ chức</span>
                  <div className="my-filter-chips">
                    <button
                      type="button"
                      className={`my-chip-btn ${!filterHosting && !filterGroup ? 'my-chip-btn--active' : ''}`}
                      onClick={() => {
                        setFilterHosting(false);
                        setFilterGroup(false);
                      }}
                    >
                      <Sparkles size={14} />
                      <span>Tất cả</span>
                      <span className="my-chip-count">({counts.all})</span>
                    </button>

                    <button
                      type="button"
                      className={`my-chip-btn ${filterHosting ? 'my-chip-btn--active' : ''}`}
                      onClick={() => setFilterHosting(!filterHosting)}
                    >
                      <UserCheck size={14} />
                      <span>Bản thân tổ chức</span>
                      <span className="my-chip-count">({counts.hosting})</span>
                    </button>

                    <button
                      type="button"
                      className={`my-chip-btn ${filterGroup ? 'my-chip-btn--active' : ''}`}
                      onClick={() => setFilterGroup(!filterGroup)}
                    >
                      <Users size={14} />
                      <span>Thuộc về nhóm</span>
                      <span className="my-chip-count">({counts.group})</span>
                    </button>
                  </div>
                </div>

                {/* Nhóm 2: Thời gian */}
                <div className="my-filter-section">
                  <span className="my-filter-title">Thời gian</span>
                  <div className="my-filter-chips">
                    {timeFilters.map((f) => {
                      const Icon = f.icon;
                      const isActive = timeFilter === f.id;
                      return (
                        <button
                          key={f.id}
                          type="button"
                          className={`my-chip-btn ${isActive ? 'my-chip-btn--active' : ''}`}
                          onClick={() => setTimeFilter(timeFilter === f.id && f.id !== 'all' ? 'all' : f.id)}
                        >
                          <Icon size={14} />
                          <span>{f.label}</span>
                          <span className="my-chip-count">({f.count})</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Nhóm 3: Trạng thái */}
                <div className="my-filter-section">
                  <span className="my-filter-title">Trạng thái</span>
                  <div className="my-filter-chips">
                    {statusFilters.map((f) => {
                      const Icon = f.icon;
                      const isActive = statusFilter === f.id;
                      return (
                        <button
                          key={f.id}
                          type="button"
                          className={`my-chip-btn ${isActive ? 'my-chip-btn--active' : ''}`}
                          onClick={() => setStatusFilter(statusFilter === f.id && f.id !== 'all' ? 'all' : f.id)}
                        >
                          <Icon size={14} />
                          <span>{f.label}</span>
                          <span className="my-chip-count">({f.count})</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </>
        }
      >

        {filteredActivities.map((activity) => (
          <ActivityCard
            key={activity.id}
            activity={activity}
            isRegistered={true}
            onDelete={
              activity.host_id === user?.id && !activity.is_deleted && new Date(activity.end_time) >= new Date()
                ? handleDeleteActivity
                : undefined
            }
            onShare={handleShare}
            onCertificate={(actId) => setSelectedCertificateActivityId(actId)}
          />
        ))}
      </CollectionLayout>

      {/* Certificate Modal */}
      {selectedCertificateActivityId && (
        <CertificateModal
          isOpen={!!selectedCertificateActivityId}
          onClose={() => setSelectedCertificateActivityId(null)}
          activityId={selectedCertificateActivityId}
        />
      )}
    </>
  );
}
