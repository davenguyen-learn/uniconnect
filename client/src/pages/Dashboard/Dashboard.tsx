import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { activitiesApi, type ActivityResponse, type NearbyQuery } from '../../api/activities';
import { useToast } from '../../components/Toast/ToastContext';
import { useAuth } from '../../contexts/AuthContext';
import Map from '../../components/Map/Map';
import Input from '../../components/Input/Input';
import './Dashboard.css';
import L from 'leaflet';

const PAGE_SIZE = 15;

export default function Dashboard() {
  const toast = useToast();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [activities, setActivities] = useState<ActivityResponse[]>([]);
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);
  const [loading, setLoading] = useState(true);

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [radius, setRadius] = useState<number>(50000);
  const [freeToJoin, setFreeToJoin] = useState(false);
  const [category, setCategory] = useState<string | undefined>(undefined);
  const [daysAhead, setDaysAhead] = useState<number | undefined>(undefined);
  const [showFilters, setShowFilters] = useState(false);

  // Pagination states
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const daysOptions = [
    { label: 'Tất cả', value: undefined },
    { label: '1 ngày', value: 1 },
    { label: '3 ngày', value: 3 },
    { label: '7 ngày', value: 7 },
    { label: '14 ngày', value: 14 },
    { label: '30 ngày', value: 30 },
  ];

  // Debounced search
  const [debouncedSearch, setDebouncedSearch] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, radius, freeToJoin, category, daysAhead]);

  // Get user location on mount
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation([position.coords.latitude, position.coords.longitude]);
        },
        () => {
          toast.error("Could not get your location. Using default location.");
          // Default to NYC
          setUserLocation([40.7128, -74.0060]);
        }
      );
    } else {
      setUserLocation([40.7128, -74.0060]);
    }
  }, []);

  useEffect(() => {
    if (userLocation) {
      fetchNearby(userLocation[0], userLocation[1]);
    }
  }, [userLocation, debouncedSearch, radius, freeToJoin, category, daysAhead, page]);

  async function fetchNearby(lat: number, lng: number) {
    try {
      setLoading(true);
      const query: NearbyQuery = {
        lat,
        lng,
        radius,
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
        search: debouncedSearch || undefined,
        free_to_join: freeToJoin ? true : undefined,
        category: category !== 'All' ? category : undefined,
        days_ahead: daysAhead,
      };
      const response = await activitiesApi.nearby(query);
      setActivities(response.items);
      setTotal(response.total);
    } catch (err) {
      toast.error('Không thể tải các hoạt động gần đây');
    } finally {
      setLoading(false);
    }
  }

  function handleBoundsChange(_bounds: L.LatLngBounds) {
    // For MVP, we'll just fetch based on initial location to avoid spamming the API.
  }

  const categories = ['All', 'Study', 'Sports', 'Social', 'Gaming', 'Food'];

  return (
    <div className="dashboard-page">
      <div className="dashboard-sidebar glass">
        <div className="dashboard-header">
          <h2>Khám phá</h2>
          <Link to="/activities/new" className="btn btn-primary btn-sm">
            Tạo mới
          </Link>
        </div>
        <div className="filters-section">
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <div style={{ flex: 1 }}>
              <Input
                placeholder="Tìm kiếm hoạt động..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <button
              className="btn btn-secondary"
              onClick={() => setShowFilters(!showFilters)}
              style={{ whiteSpace: 'nowrap' }}
            >
              {showFilters ? 'Ẩn bộ lọc' : 'Bộ lọc'}
            </button>
          </div>

          {showFilters && (
            <div className="filters-grid" style={{ marginTop: 'var(--space-3)' }}>
              <select
                value={radius}
                onChange={(e) => setRadius(Number(e.target.value))}
                className="form-select"
              >
                <option value={5000}>Trong bán kính 5 km</option>
                <option value={10000}>Trong bán kính 10 km</option>
                <option value={25000}>Trong bán kính 25 km</option>
                <option value={50000}>Trong bán kính 50 km</option>
              </select>

              <select
                value={category || 'All'}
                onChange={(e) => setCategory(e.target.value === 'All' ? undefined : e.target.value)}
                className="form-select"
              >
                <option value="All">Tất cả danh mục</option>
                {categories.filter(c => c !== 'All').map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>

              <select
                value={daysAhead !== undefined ? String(daysAhead) : 'all'}
                onChange={(e) => setDaysAhead(e.target.value === 'all' ? undefined : Number(e.target.value))}
                className="form-select"
              >
                <option value="all">Bất kỳ lúc nào</option>
                {daysOptions.filter(opt => opt.value !== undefined).map(opt => (
                  <option key={opt.label} value={opt.value}>Trong vòng {opt.label}</option>
                ))}
              </select>

              <label className="filter-checkbox-label">
                <input
                  type="checkbox"
                  checked={freeToJoin}
                  onChange={(e) => setFreeToJoin(e.target.checked)}
                />
                Tham gia miễn phí
              </label>
            </div>
          )}
        </div>

        <div className="activity-list">
          {loading ? (
            <div className="activity-list-loading">Đang tải hoạt động...</div>
          ) : activities.length === 0 ? (
            <div className="activity-list-empty">
              Không tìm thấy hoạt động nào gần đây. Hãy thử tạo một hoạt động!
            </div>
          ) : (
            activities.map(a => (
              <div
                key={a.id}
                className="activity-list-item"
                onClick={() => navigate(`/activities/${a.id}`)}
              >
                <div className="activity-list-item-header">
                  <span className="activity-category">{a.category || 'Chung'}</span>
                  {a.distance_meters !== undefined && (
                    <span className="activity-distance">
                      {(a.distance_meters / 1000).toFixed(1)} km
                    </span>
                  )}
                </div>
                <h4>{a.title}</h4>
                <div className="activity-list-item-footer">
                  <span>{new Date(a.start_time).toLocaleDateString('vi-VN')}</span>
                  <span>{a.current_participants}/{a.max_participants} người tham gia</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Pagination */}
        {total > PAGE_SIZE && (
          <div className="pagination">
            <button
              className="pagination-btn"
              disabled={page <= 1}
              onClick={() => setPage(p => Math.max(1, p - 1))}
            >
              ‹ Trước
            </button>
            <div className="pagination-pages">
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                let pageNum: number;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (page <= 3) {
                  pageNum = i + 1;
                } else if (page >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = page - 2 + i;
                }
                return (
                  <button
                    key={pageNum}
                    className={`pagination-page ${page === pageNum ? 'active' : ''}`}
                    onClick={() => setPage(pageNum)}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>
            <button
              className="pagination-btn"
              disabled={page >= totalPages}
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            >
              Tiếp ›
            </button>
          </div>
        )}

        {!loading && total > 0 && (
          <div className="pagination-info">
            Hiển thị {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, total)} trên {total}
          </div>
        )}
      </div>

      <div className="dashboard-map-container">
        <Map
          activities={activities}
          userLocation={userLocation}
          onBoundsChange={handleBoundsChange}
          userInterests={(user as any)?.interests}
        />
      </div>
    </div>
  );
}
