import React, { useState, useEffect, useCallback, useMemo, Suspense, lazy } from 'react';
import { Link } from 'react-router-dom';
import {
  Compass,
  GraduationCap,
  Calendar as CalendarIcon,
  SlidersHorizontal,
  MapPin,
  Award,
  Heart,
  Film,
  Dices,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Minimize2,
  Coffee,
  Trophy,
  BookOpen,
  Users,
  Sparkles,
  Briefcase,
  Music,
  Gamepad2,
  Tent,
  Search,
  X,
  CalendarOff,
  Utensils,
  Flame,
  Lightbulb,
  PartyPopper,
  Palette,
  Swords,
  Footprints,
  Clock,
  Navigation,
} from 'lucide-react';
import { activitiesApi, type ActivityResponse, type NearbyQuery } from '../../api/activities';
import { usersApi, type MyUserStats } from '../../api/users';
import { useToast } from '../../components/Toast/ToastContext';
import { useAuth } from '../../contexts/AuthContext';
import ActivityCard from '../../components/ActivityCard/ActivityCard';
import { formatCtxh } from '../../utils/format';
import './Dashboard.css';

// Lazy-load Leaflet Map to optimize initial bundle and page responsiveness
const LazyMap = lazy(() => import('../../components/Map/Map'));

const PAGE_SIZE = 12;

export const Dashboard: React.FC = () => {
  const toast = useToast();
  const { user } = useAuth();

  const [activities, setActivities] = useState<ActivityResponse[]>([]);
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);
  const [loading, setLoading] = useState(true);
  const [userStats, setUserStats] = useState<MyUserStats | null>(null);
  const [isMapExpanded, setIsMapExpanded] = useState(false);

  const [upcomingJoinedActivities, setUpcomingJoinedActivities] = useState<ActivityResponse[]>([]);
  const [loadingUpcoming, setLoadingUpcoming] = useState(false);

  useEffect(() => {
    usersApi
      .getMyStats()
      .then((res) => setUserStats(res))
      .catch(() => setUserStats(null));
  }, []);

  useEffect(() => {
    if (!user) {
      setUpcomingJoinedActivities([]);
      return;
    }

    setLoadingUpcoming(true);
    Promise.all([
      activitiesApi.getJoinedActivities({ status: 'upcoming', limit: 20 }).catch(() => ({ items: [] })),
      activitiesApi.getMyActivities({ status: 'upcoming', limit: 20 }).catch(() => ({ items: [] })),
    ])
      .then(([joinedRes, hostingRes]) => {
        const map = new Map<string, ActivityResponse>();
        (joinedRes.items || []).forEach((act) => map.set(act.id, act));
        (hostingRes.items || []).forEach((act) => map.set(act.id, act));
        const all = Array.from(map.values());

        const now = new Date();
        const in7Days = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

        const filtered = all
          .filter((act) => {
            const start = new Date(act.start_time);
            const end = new Date(act.end_time || act.start_time);
            return end >= now && start <= in7Days;
          })
          .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());

        setUpcomingJoinedActivities(filtered);
      })
      .catch(() => {
        setUpcomingJoinedActivities([]);
      })
      .finally(() => {
        setLoadingUpcoming(false);
      });
  }, [user]);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [radius, setRadius] = useState<number>(50000);
  const [category, setCategory] = useState<string>('all');
  const [filterCtxhOnly, setFilterCtxhOnly] = useState(false);
  const [filterTrophyOnly, setFilterTrophyOnly] = useState(false);
  const [hideConflicts, setHideConflicts] = useState(false);
  const [sortBy, setSortBy] = useState<'distance' | 'time' | 'created_at'>('distance');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  const activeFilterCount =
    (category !== 'all' ? 1 : 0) +
    (filterCtxhOnly ? 1 : 0) +
    (filterTrophyOnly ? 1 : 0) +
    (hideConflicts ? 1 : 0) +
    (radius !== 50000 ? 1 : 0) +
    (sortBy !== 'distance' ? 1 : 0);

  const handleResetFilters = useCallback(() => {
    setCategory('all');
    setFilterCtxhOnly(false);
    setFilterTrophyOnly(false);
    setHideConflicts(false);
    setRadius(50000);
    setSortBy('distance');
    setPage(1);
  }, []);

  // Pagination
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery.trim());
    }, 350);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  useEffect(() => {
    setPage(1);
  }, [radius, category, filterCtxhOnly, filterTrophyOnly, debouncedSearch, hideConflicts, sortBy]);

  // Geolocation
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation([position.coords.latitude, position.coords.longitude]);
        },
        () => {
          setUserLocation([10.7769, 106.6953]); // TP. Hồ Chí Minh
        }
      );
    } else {
      setUserLocation([10.7769, 106.6953]);
    }
  }, []);

  // Keyboard shortcut (ESC) & scroll lock for expanded map modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMapExpanded) {
        setIsMapExpanded(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMapExpanded]);

  useEffect(() => {
    if (isMapExpanded) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isMapExpanded]);

  const fetchNearby = useCallback(async (lat: number, lng: number) => {
    try {
      setLoading(true);
      const query: NearbyQuery = {
        lat,
        lng,
        radius,
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
        category: category !== 'all' ? category : undefined,
        search: debouncedSearch || undefined,
        is_ctxh: filterCtxhOnly || undefined,
        has_trophy: filterTrophyOnly || undefined,
        sort_by: sortBy,
        exclude_my_activities: true,
        include_conflicts: !hideConflicts,
      };
      const response = await activitiesApi.nearby(query);

      setActivities(response.items);
      setTotal(response.total);
    } catch {
      toast.error('Không thể tải danh sách hoạt động gần đây');
    } finally {
      setLoading(false);
    }
  }, [radius, page, category, debouncedSearch, filterCtxhOnly, filterTrophyOnly, sortBy, hideConflicts, toast]);

  useEffect(() => {
    if (userLocation) {
      fetchNearby(userLocation[0], userLocation[1]);
    }
  }, [userLocation, fetchNearby]);

  // Client-side filter & sort (excludes own hosted activities so users can discover new activities)
  const displayedActivities: ActivityResponse[] = useMemo(() => {
    let list = activities.filter((act) => {
      if (user?.id && (act.host_id === user.id || act.host?.username === user.username)) {
        return false;
      }
      if (hideConflicts && act.conflict_info?.has_conflict) {
        return false;
      }
      return true;
    });

    if (sortBy === 'distance') {
      return [...list].sort((a, b) => (a.distance_meters ?? Infinity) - (b.distance_meters ?? Infinity));
    }
    if (sortBy === 'time') {
      return [...list].sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());
    }
    if (sortBy === 'created_at') {
      return [...list].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    }
    return list;
  }, [activities, hideConflicts, sortBy, user]);

  // Stable callbacks for ActivityCard to prevent unnecessary re-renders
  const handleCardShare = useCallback((activityId: string) => {
    const url = `${window.location.origin}/activities/${activityId}`;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url);
      toast.success('Đã sao chép liên kết hoạt động');
    }
  }, [toast]);

  // Filter Categories matching actual database categories and WeGoWhere styles
  const categoryChips = [
    { id: 'all', label: 'Tất cả', icon: Compass },
    { id: 'Ăn uống', label: 'Ăn uống', icon: Utensils },
    { id: 'Cà phê', label: 'Cà phê', icon: Coffee },
    { id: 'Học tập', label: 'Học tập', icon: BookOpen },
    { id: 'Workshop', label: 'Workshop', icon: Lightbulb },
    { id: 'Thể thao', label: 'Thể thao', icon: Trophy },
    { id: 'Vận động', label: 'Vận động', icon: Flame },
    { id: 'Tình nguyện', label: 'Tình nguyện', icon: Heart },
    { id: 'CTXH', label: 'CTXH', icon: GraduationCap },
    { id: 'CLB', label: 'Nhóm', icon: Sparkles },
    { id: 'Đội nhóm', label: 'Đội nhóm', icon: Users },
    { id: 'Hướng nghiệp', label: 'Hướng nghiệp', icon: Compass },
    { id: 'Việc làm', label: 'Việc làm', icon: Briefcase },
    { id: 'Xem phim', label: 'Xem phim', icon: Film },
    { id: 'Giải trí', label: 'Giải trí', icon: PartyPopper },
    { id: 'Âm nhạc', label: 'Âm nhạc', icon: Music },
    { id: 'Nghệ thuật', label: 'Nghệ thuật', icon: Palette },
    { id: 'Boardgame', label: 'Boardgame', icon: Dices },
    { id: 'Game', label: 'Game', icon: Gamepad2 },
    { id: 'Esports', label: 'Esports', icon: Swords },
    { id: 'Dã ngoại', label: 'Dã ngoại', icon: Tent },
    { id: 'Phượt', label: 'Phượt', icon: Footprints },
    { id: 'Giao lưu kết bạn', label: 'Giao lưu kết bạn', icon: Users },
  ];

  return (
    <div className="dashboard-tri-pane">
      {/* CỘT GIỮA: BẢNG TIN HOẠT ĐỘNG (FEED - MAX 720px) */}
      <section className="dashboard-feed-pane" aria-label="Bảng tin hoạt động">
        {/* Thanh tìm kiếm & Nút mở Bộ lọc */}
        <div className="dashboard-search-container">
          <div className="dashboard-search-bar">
            <Search size={18} className="dashboard-search-icon" />
            <input
              type="text"
              className="dashboard-search-input"
              placeholder="Tìm kiếm hoạt động theo tên, địa điểm, chủ đề..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Tìm kiếm hoạt động"
            />
            {searchQuery && (
              <button
                type="button"
                className="dashboard-search-clear"
                onClick={() => setSearchQuery('')}
                aria-label="Xóa nội dung tìm kiếm"
                title="Xóa tìm kiếm"
              >
                <X size={15} />
              </button>
            )}
          </div>

          <button
            type="button"
            className={`chip-filter-toggle ${showAdvancedFilters ? 'chip-filter-toggle--open' : ''} ${activeFilterCount > 0 ? 'chip-filter-toggle--has-active' : ''}`}
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            aria-label="Tùy chỉnh khoảng cách và bộ lọc chi tiết"
            title="Bộ lọc nâng cao"
          >
            <SlidersHorizontal size={16} />
            <span className="chip-filter-toggle-text">Bộ lọc</span>
            {activeFilterCount > 0 && (
              <span className="filter-count-badge">{activeFilterCount}</span>
            )}
          </button>
        </div>

        {/* Active Filters Summary (Khi đóng panel nhưng đang có filter hoạt động) */}
        {activeFilterCount > 0 && !showAdvancedFilters && (
          <div className="dashboard-active-filters-row">
            <span className="active-filters-title">Đang lọc:</span>
            {category !== 'all' && (
              <span className="active-filter-pill">
                <span>{categoryChips.find((c) => c.id === category)?.label || category}</span>
                <button type="button" onClick={() => setCategory('all')} aria-label="Bỏ chọn danh mục"><X size={12} /></button>
              </span>
            )}
            {filterCtxhOnly && (
              <span className="active-filter-pill">
                <span>Có CTXH</span>
                <button type="button" onClick={() => setFilterCtxhOnly(false)} aria-label="Bỏ lọc CTXH"><X size={12} /></button>
              </span>
            )}
            {filterTrophyOnly && (
              <span className="active-filter-pill">
                <span>Có Trophy</span>
                <button type="button" onClick={() => setFilterTrophyOnly(false)} aria-label="Bỏ lọc Trophy"><X size={12} /></button>
              </span>
            )}
            {hideConflicts && (
              <span className="active-filter-pill">
                <span>Ẩn trùng lịch</span>
                <button type="button" onClick={() => setHideConflicts(false)} aria-label="Bỏ ẩn trùng lịch"><X size={12} /></button>
              </span>
            )}
            {radius !== 50000 && (
              <span className="active-filter-pill">
                <span>{radius / 1000} km</span>
                <button type="button" onClick={() => setRadius(50000)} aria-label="Bỏ lọc bán kính"><X size={12} /></button>
              </span>
            )}
            {sortBy !== 'distance' && (
              <span className="active-filter-pill">
                <span>{sortBy === 'time' ? 'Xếp: Sắp diễn ra' : 'Xếp: Mới đăng'}</span>
                <button type="button" onClick={() => setSortBy('distance')} aria-label="Bỏ chọn sắp xếp"><X size={12} /></button>
              </span>
            )}
            <button
              type="button"
              className="btn-clear-all-filters"
              onClick={handleResetFilters}
            >
              Đặt lại
            </button>
          </div>
        )}

        {/* Panel Bộ Lọc Chi Tiết (Khi bấm nút Bộ lọc) */}
        {showAdvancedFilters && (
          <div className="dashboard-filters-panel">
            {/* 1. Chọn Tag / Danh mục hoạt động */}
            <div className="filters-panel-section">
              <span className="filters-panel-title">Danh mục hoạt động ({categoryChips.length} tags)</span>
              <div className="filters-panel-chips">
                {categoryChips.map((chip) => {
                  const IconComponent = chip.icon;
                  const isActive = category === chip.id;
                  return (
                    <button
                      key={chip.id}
                      type="button"
                      className={`chip-btn ${isActive ? 'chip-btn--active' : ''}`}
                      onClick={() => setCategory(chip.id)}
                      aria-pressed={isActive}
                    >
                      <IconComponent size={14} className="chip-btn__icon" />
                      <span>{chip.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 2. Tiêu chí lọc bổ sung */}
            <div className="filters-panel-section">
              <span className="filters-panel-title">Tiêu chí tham gia & Lịch cá nhân</span>
              <div className="filters-panel-chips">
                <button
                  type="button"
                  className={`chip-btn ${filterCtxhOnly ? 'chip-btn--active' : ''}`}
                  onClick={() => setFilterCtxhOnly(!filterCtxhOnly)}
                  aria-pressed={filterCtxhOnly}
                >
                  <GraduationCap size={14} className="chip-btn__icon" />
                  <span>Có ngày CTXH</span>
                </button>

                <button
                  type="button"
                  className={`chip-btn ${filterTrophyOnly ? 'chip-btn--active' : ''}`}
                  onClick={() => setFilterTrophyOnly(!filterTrophyOnly)}
                  aria-pressed={filterTrophyOnly}
                >
                  <Award size={14} className="chip-btn__icon" />
                  <span>Có Trophy</span>
                </button>

                <button
                  type="button"
                  className={`chip-btn ${hideConflicts ? 'chip-btn--active' : ''}`}
                  onClick={() => setHideConflicts(!hideConflicts)}
                  aria-pressed={hideConflicts}
                >
                  <CalendarOff size={14} className="chip-btn__icon" />
                  <span>Ẩn hoạt động trùng lịch</span>
                </button>
              </div>
            </div>

            {/* 3. Sắp xếp hoạt động */}
            <div className="filters-panel-section">
              <span className="filters-panel-title">Sắp xếp theo</span>
              <div className="filters-panel-chips">
                <button
                  type="button"
                  className={`chip-btn ${sortBy === 'distance' ? 'chip-btn--active' : ''}`}
                  onClick={() => setSortBy('distance')}
                  aria-pressed={sortBy === 'distance'}
                >
                  <Navigation size={14} className="chip-btn__icon" />
                  <span>Khoảng cách gần nhất</span>
                </button>

                <button
                  type="button"
                  className={`chip-btn ${sortBy === 'time' ? 'chip-btn--active' : ''}`}
                  onClick={() => setSortBy('time')}
                  aria-pressed={sortBy === 'time'}
                >
                  <Clock size={14} className="chip-btn__icon" />
                  <span>Sắp diễn ra nhất</span>
                </button>

                <button
                  type="button"
                  className={`chip-btn ${sortBy === 'created_at' ? 'chip-btn--active' : ''}`}
                  onClick={() => setSortBy('created_at')}
                  aria-pressed={sortBy === 'created_at'}
                >
                  <Sparkles size={14} className="chip-btn__icon" />
                  <span>Mới đăng gần đây</span>
                </button>
              </div>
            </div>

            {/* 4. Bán kính & Thao tác */}
            <div className="filters-panel-footer">
              <div className="filter-group">
                <label htmlFor="radius-select" className="filter-label">
                  <MapPin size={14} /> Bán kính:
                </label>
                <select
                  id="radius-select"
                  value={radius}
                  onChange={(e) => setRadius(Number(e.target.value))}
                  className="filter-select"
                >
                  <option value={5000}>Trong vòng 5 km</option>
                  <option value={10000}>Trong vòng 10 km</option>
                  <option value={25000}>Trong vòng 25 km</option>
                  <option value={50000}>Toàn khu vực (50 km)</option>
                </select>
              </div>

              <div className="filters-panel-actions">
                {activeFilterCount > 0 && (
                  <button
                    type="button"
                    className="btn-reset-filters"
                    onClick={handleResetFilters}
                  >
                    Đặt lại ({activeFilterCount})
                  </button>
                )}
                <button
                  type="button"
                  className="btn-apply-filters"
                  onClick={() => setShowAdvancedFilters(false)}
                >
                  Áp dụng
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Activity Feed List */}
        <div className="dashboard-activity-list">
          {loading ? (
            <div className="activity-list-shimmer" aria-live="polite">
              <div className="shimmer-card" />
              <div className="shimmer-card" />
              <div className="shimmer-card" />
            </div>
          ) : displayedActivities.length === 0 ? (
            <div className="dashboard-empty-state">
              <div className="empty-state-icon" aria-hidden="true">
                <Compass size={40} />
              </div>
              <h3 className="empty-state-title">Chưa có hoạt động nào phù hợp</h3>
              <p className="empty-state-desc">
                {hideConflicts
                  ? 'Một số hoạt động có thể đã bị ẩn do trùng lịch cá nhân. Thử tắt "Ẩn trùng lịch" hoặc nới rộng bán kính tìm kiếm nhé!'
                  : 'Thử nới rộng bán kính hoặc đổi danh mục bộ lọc để khám phá các sự kiện thú vị khác nhé!'}
              </p>
            </div>
          ) : (
            displayedActivities.map((act) => (
              <ActivityCard
                key={act.id}
                activity={act}
                onShare={handleCardShare}
              />
            ))
          )}
        </div>

        {/* Pagination Bar */}
        {total > PAGE_SIZE && (
          <nav className="dashboard-pagination" aria-label="Phân trang danh sách hoạt động">
            <button
              type="button"
              className="pagination-btn"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              aria-label="Trang trước"
            >
              <ChevronLeft size={16} /> Trước
            </button>
            <span className="pagination-current">
              Trang {page} / {totalPages}
            </span>
            <button
              type="button"
              className="pagination-btn"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              aria-label="Trang tiếp"
            >
              Tiếp <ChevronRight size={16} />
            </button>
          </nav>
        )}
      </section>

      {/* CỘT PHẢI: BẢNG TIỆN ÍCH CTXH, LỊCH & BẢN ĐỒ MINI (WIDGETS - 320px) */}
      <aside className="dashboard-widgets-pane" aria-label="Tiện ích & Bản đồ">
        {/* Widget 1: Số ngày CTXH đã đạt được trên nền tảng */}
        <div className="dashboard-widget-card widget-ctxh">
          <div className="widget-header">
            <div className="widget-header-title">
              <GraduationCap size={18} className="widget-header-icon" />
              <span>Số ngày CTXH đạt được</span>
            </div>
          </div>
          <div className="widget-ctxh-stats">
            <div className="ctxh-stat-number">
              <span className="stat-big">
                {formatCtxh(userStats?.total_ctxh_days)}
              </span>
              <span className="stat-unit">ngày</span>
            </div>
            {userStats?.total_attended_activities != null && (
              <span className="ctxh-stat-badge">
                {userStats.total_attended_activities} hoạt động
              </span>
            )}
          </div>
          <p className="widget-footer-tip">
            Số ngày Công tác Xã hội bạn đã đạt được từ các hoạt động trên nền tảng UniConnect.
          </p>
        </div>

        {/* Widget 2: Sự kiện tôi tham gia sắp diễn ra (7 ngày tới) */}
        <div className="dashboard-widget-card widget-upcoming">
          <div className="widget-header">
            <div className="widget-header-title">
              <CalendarIcon size={18} className="widget-header-icon" />
              <span>Sự kiện sắp diễn ra</span>
            </div>
            <Link to="/my-activities" className="widget-view-all-link" title="Xem tất cả">
              Xem tất cả
            </Link>
          </div>
          <div className="upcoming-events-list">
            {loadingUpcoming ? (
              <div className="upcoming-empty-state">
                <span>Đang tải sự kiện của bạn...</span>
              </div>
            ) : upcomingJoinedActivities.length > 0 ? (
              upcomingJoinedActivities.slice(0, 4).map((act) => (
                <Link
                  key={act.id}
                  to={`/activities/${act.id}`}
                  className="upcoming-item"
                  title={`Xem chi tiết: ${act.title}`}
                >
                  <div className="upcoming-item-dot" aria-hidden="true" />
                  <div className="upcoming-item-details">
                    <span className="upcoming-item-title">{act.title}</span>
                    <span className="upcoming-item-time">
                      {new Date(act.start_time).toLocaleDateString('vi-VN')} • {new Date(act.start_time).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </Link>
              ))
            ) : (
              <div className="upcoming-empty-state">
                <span>Không có sự kiện nào sắp tới trong 7 ngày</span>
              </div>
            )}
          </div>
        </div>

        {/* Widget 3: Bản Đồ Số Mini (Lazy-Loaded) */}
        <div className="dashboard-widget-card widget-map">
          <div className="widget-header">
            <div className="widget-header-title">
              <MapPin size={18} className="widget-header-icon" />
              <span>Bản đồ không gian số</span>
            </div>
            <button
              type="button"
              className="widget-header-expand-btn"
              onClick={() => setIsMapExpanded(true)}
              title="Phóng to bản đồ"
            >
              <Maximize2 size={14} />
              <span>Phóng to</span>
            </button>
          </div>
          <div
            className="widget-map-viewport widget-map-viewport--compact"
            title="Bấm vào bản đồ để phóng to"
            onClick={() => setIsMapExpanded(true)}
          >
            <Suspense
              fallback={
                <div className="map-skeleton">
                  <MapPin size={24} className="map-skeleton-icon" />
                  <span>Đang tải bản đồ xung quanh...</span>
                </div>
              }
            >
              <LazyMap
                activities={displayedActivities}
                userLocation={userLocation}
                onBoundsChange={() => { }}
                userInterests={(user as any)?.interests}
                onMapClick={() => setIsMapExpanded(true)}
                isCompact={true}
              />
            </Suspense>
          </div>
        </div>
      </aside>

      {/* Modal Phóng To Bản Đồ Toàn Màn Hình */}
      {isMapExpanded && (
        <div
          className="map-expanded-modal-backdrop"
          onClick={() => setIsMapExpanded(false)}
          role="dialog"
          aria-modal="true"
        >
          <div
            className="map-expanded-modal-card"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="map-expanded-modal-header">
              <div className="map-expanded-header-info">
                <div className="map-expanded-title-row">
                  <MapPin size={20} className="map-expanded-header-pin" />
                  <h2 className="map-expanded-modal-title">Bản đồ hoạt động</h2>
                  <span className="map-expanded-count-badge">
                    {displayedActivities.length} hoạt động
                  </span>
                </div>
              </div>
              <button
                type="button"
                className="map-expanded-close-btn"
                onClick={() => setIsMapExpanded(false)}
                title="Thu nhỏ lại (ESC)"
                aria-label="Thu nhỏ lại (ESC)"
              >
                <Minimize2 size={18} />
              </button>
            </div>
            <div className="map-expanded-modal-viewport">
              <Suspense
                fallback={
                  <div className="map-skeleton">
                    <MapPin size={32} className="map-skeleton-icon" />
                    <span>Đang tải bản đồ toàn màn hình...</span>
                  </div>
                }
              >
                <LazyMap
                  activities={displayedActivities}
                  userLocation={userLocation}
                  onBoundsChange={() => { }}
                  userInterests={(user as any)?.interests}
                  isCompact={false}
                />
              </Suspense>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
