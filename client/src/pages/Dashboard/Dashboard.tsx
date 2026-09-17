import React, { useState, useEffect, useCallback, Suspense, lazy } from 'react';
import {
  Compass,
  GraduationCap,
  Calendar as CalendarIcon,
  SlidersHorizontal,
  MapPin,
  Flame,
  Award,
  ChevronLeft,
  ChevronRight,
  Search,
} from 'lucide-react';
import { activitiesApi, type ActivityResponse, type NearbyQuery } from '../../api/activities';
import { useToast } from '../../components/Toast/ToastContext';
import { useAuth } from '../../contexts/AuthContext';
import ActivityCard from '../../components/ActivityCard/ActivityCard';
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

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [radius, setRadius] = useState<number>(50000);
  const [category, setCategory] = useState<string>('all');
  const [filterCtxhOnly, setFilterCtxhOnly] = useState(false);
  const [filterTrophyOnly, setFilterTrophyOnly] = useState(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  // Pagination
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  // Debounced search
  const [debouncedSearch, setDebouncedSearch] = useState('');
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, radius, category, filterCtxhOnly, filterTrophyOnly]);

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

  const fetchNearby = useCallback(async (lat: number, lng: number) => {
    try {
      setLoading(true);
      const query: NearbyQuery = {
        lat,
        lng,
        radius,
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
        search: debouncedSearch || undefined,
        category: category !== 'all' ? category : undefined,
      };
      const response = await activitiesApi.nearby(query);
      
      let items = response.items;
      if (filterCtxhOnly) {
        items = items.filter((a) => typeof a.social_work_days === 'number' && a.social_work_days > 0);
      }
      if (filterTrophyOnly) {
        items = items.filter((a) => !!a.trophy);
      }

      setActivities(items);
      setTotal(response.total);
    } catch {
      toast.error('Không thể tải danh sách hoạt động gần đây');
    } finally {
      setLoading(false);
    }
  }, [radius, page, debouncedSearch, category, filterCtxhOnly, filterTrophyOnly, toast]);

  useEffect(() => {
    if (userLocation) {
      fetchNearby(userLocation[0], userLocation[1]);
    }
  }, [userLocation, fetchNearby]);

  // Stable callbacks for ActivityCard to prevent unnecessary re-renders
  const handleCardBookmark = useCallback((_activityId: string) => {
    toast.info('Đã lưu hoạt động vào danh sách quan tâm');
  }, [toast]);

  const handleCardShare = useCallback((activityId: string) => {
    const url = `${window.location.origin}/activities/${activityId}`;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url);
      toast.success('Đã sao chép liên kết hoạt động');
    }
  }, [toast]);

  // Filter Categories
  const categoryChips = [
    { id: 'all', label: 'Tất cả', icon: Compass },
    { id: 'Study', label: 'Học thuật', icon: Flame },
    { id: 'Social', label: 'Tình nguyện', icon: GraduationCap },
    { id: 'Sports', label: 'Thể thao', icon: Award },
    { id: 'Gaming', label: 'Giải trí', icon: Award },
  ];

  return (
    <div className="dashboard-tri-pane">
      {/* CỘT GIỮA: BẢNG TIN HOẠT ĐỘNG (FEED - MAX 720px) */}
      <section className="dashboard-feed-pane" aria-label="Bảng tin hoạt động">
        {/* Search Input */}
        <div className="dashboard-search-row">
          <div className="dashboard-search-field">
            <Search size={16} className="search-field-icon" aria-hidden="true" />
            <input
              type="search"
              placeholder="Tìm kiếm sự kiện, hoạt động..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-field-input"
              aria-label="Tìm kiếm sự kiện"
            />
          </div>
        </div>

        {/* Filter Chips Bar */}
        <div className="dashboard-chips-bar" role="toolbar" aria-label="Bộ lọc nhanh">
          <div className="dashboard-chips-scroll">
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
          </div>

          <button
            type="button"
            className={`chip-filter-toggle ${showAdvancedFilters ? 'chip-filter-toggle--open' : ''}`}
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            aria-label="Tùy chỉnh khoảng cách và bộ lọc chi tiết"
            title="Bộ lọc nâng cao"
          >
            <SlidersHorizontal size={16} />
          </button>
        </div>

        {/* Advanced Filters Drawer */}
        {showAdvancedFilters && (
          <div className="dashboard-advanced-filters">
            <div className="filter-group">
              <label htmlFor="radius-select" className="filter-label">
                <MapPin size={14} /> Bán kính tìm kiếm:
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
          ) : activities.length === 0 ? (
            <div className="dashboard-empty-state">
              <div className="empty-state-icon" aria-hidden="true">
                <Compass size={40} />
              </div>
              <h3 className="empty-state-title">Chưa có hoạt động nào phù hợp</h3>
              <p className="empty-state-desc">
                Thử nới rộng bán kính hoặc đổi danh mục bộ lọc để khám phá các sự kiện thú vị khác nhé!
              </p>
            </div>
          ) : (
            activities.map((act) => (
              <ActivityCard
                key={act.id}
                activity={act}
                onBookmark={handleCardBookmark}
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
        {/* Widget 1: Hộ Chiếu Ngày CTXH */}
        <div className="dashboard-widget-card widget-ctxh">
          <div className="widget-header">
            <div className="widget-header-title">
              <GraduationCap size={18} className="widget-header-icon" />
              <span>Tiến độ Ngày CTXH</span>
            </div>
            <span className="widget-badge-target">Mục tiêu: 5.0 ngày</span>
          </div>
          <div className="widget-ctxh-stats">
            <div className="ctxh-stat-number">
              <span className="stat-big">4.5</span>
              <span className="stat-unit">/ 5.0 ngày</span>
            </div>
            <span className="ctxh-stat-percent">90% hoàn thành</span>
          </div>
          <div className="ctxh-progress-bar" aria-hidden="true">
            <div className="ctxh-progress-fill" style={{ width: '90%' }} />
          </div>
          <p className="widget-footer-tip">
            Chỉ còn 0.5 ngày CTXH để đủ điều kiện xét tốt nghiệp chính thức!
          </p>
        </div>

        {/* Widget 2: Lịch Sắp Diễn Ra */}
        <div className="dashboard-widget-card widget-upcoming">
          <div className="widget-header">
            <div className="widget-header-title">
              <CalendarIcon size={18} className="widget-header-icon" />
              <span>Sự kiện sắp diễn ra</span>
            </div>
          </div>
          <div className="upcoming-events-list">
            {activities.slice(0, 2).map((act) => (
              <div key={act.id} className="upcoming-item">
                <div className="upcoming-item-dot" aria-hidden="true" />
                <div className="upcoming-item-details">
                  <span className="upcoming-item-title">{act.title}</span>
                  <span className="upcoming-item-time">
                    {new Date(act.start_time).toLocaleDateString('vi-VN')} • {new Date(act.start_time).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Widget 3: Bản Đồ Số Mini (Lazy-Loaded) */}
        <div className="dashboard-widget-card widget-map">
          <div className="widget-header">
            <div className="widget-header-title">
              <MapPin size={18} className="widget-header-icon" />
              <span>Bản đồ không gian số</span>
            </div>
          </div>
          <div className="widget-map-viewport">
            <Suspense
              fallback={
                <div className="map-skeleton">
                  <MapPin size={24} className="map-skeleton-icon" />
                  <span>Đang tải bản đồ xung quanh...</span>
                </div>
              }
            >
              <LazyMap
                activities={activities}
                userLocation={userLocation}
                onBoundsChange={() => {}}
                userInterests={(user as any)?.interests}
              />
            </Suspense>
          </div>
        </div>
      </aside>
    </div>
  );
};

export default Dashboard;
