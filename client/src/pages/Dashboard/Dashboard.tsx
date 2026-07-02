import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { activitiesApi, type ActivityResponse, type NearbyQuery } from '../../api/activities';
import { useToast } from '../../components/Toast/ToastContext';
import Map from '../../components/Map/Map';
import Input from '../../components/Input/Input';
import './Dashboard.css';
import L from 'leaflet';

export default function Dashboard() {
  const toast = useToast();
  const navigate = useNavigate();
  
  const [activities, setActivities] = useState<ActivityResponse[]>([]);
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [radius, setRadius] = useState<number>(50000);
  const [freeToJoin, setFreeToJoin] = useState(false);
  const [category, setCategory] = useState<string | undefined>(undefined);

  // Debounced search
  const [debouncedSearch, setDebouncedSearch] = useState('');
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchQuery]);

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
  }, [userLocation, debouncedSearch, radius, freeToJoin, category]);

  async function fetchNearby(lat: number, lng: number) {
    try {
      setLoading(true);
      const query: NearbyQuery = { 
        lat, 
        lng, 
        radius, 
        limit: 50,
        search: debouncedSearch || undefined,
        free_to_join: freeToJoin ? true : undefined,
        category: category !== 'All' ? category : undefined
      };
      const response = await activitiesApi.nearby(query);
      setActivities(response.items);
    } catch (err) {
      toast.error('Failed to fetch nearby activities');
    } finally {
      setLoading(false);
    }
  }

  // When map moves, we could re-fetch based on map center
  function handleBoundsChange(_bounds: L.LatLngBounds) {
    // For MVP, we'll just fetch based on initial location to avoid spamming the API.
    // In a real app, we'd debounce this and fetch using map center.
  }

  const categories = ['All', 'Study', 'Sports', 'Social', 'Gaming', 'Food'];

  return (
    <div className="dashboard-page">
      <div className="dashboard-sidebar glass">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <h2>Discover</h2>
          <Link to="/activities/new" className="btn btn-primary" style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}>
            + Create
          </Link>
        </div>
        <p className="dashboard-subtitle">Find activities happening near you.</p>
        
        <div className="filters-section" style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px', maxWidth: '100%', boxSizing: 'border-box' }}>
          <Input 
            placeholder="Search activities..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
            <select 
              value={radius} 
              onChange={(e) => setRadius(Number(e.target.value))}
              style={{
                padding: '8px',
                borderRadius: '8px',
                border: '1px solid rgba(255,255,255,0.1)',
                background: 'rgba(255,255,255,0.05)',
                color: 'inherit',
                outline: 'none'
              }}
            >
              <option value={5000}>Within 5 km</option>
              <option value={10000}>Within 10 km</option>
              <option value={25000}>Within 25 km</option>
              <option value={50000}>Within 50 km</option>
            </select>
            
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '0.9rem' }}>
              <input 
                type="checkbox" 
                checked={freeToJoin}
                onChange={(e) => setFreeToJoin(e.target.checked)}
              />
              Free to join
            </label>
          </div>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', paddingBottom: '4px', width: '100%' }}>
            {categories.map(c => (
              <div 
                key={c}
                className={`filter-pill ${category === c || (c === 'All' && !category) ? 'active' : ''}`}
                onClick={() => setCategory(c === 'All' ? undefined : c)}
              >
                {c}
              </div>
            ))}
          </div>
        </div>

        <div className="activity-list" style={{ marginTop: '16px' }}>
          {loading ? (
            <div className="activity-list-loading">Loading activities...</div>
          ) : activities.length === 0 ? (
            <div className="activity-list-empty">
              No activities found nearby. Try creating one!
            </div>
          ) : (
            activities.map(a => (
              <div 
                key={a.id} 
                className="activity-list-item" 
                onClick={() => navigate(`/activities/${a.id}`)}
                style={{ cursor: 'pointer' }}
              >
                <div className="activity-list-item-header">
                  <span className="activity-category">{a.category || 'General'}</span>
                  {a.distance_meters !== undefined && (
                    <span className="activity-distance">
                      {(a.distance_meters / 1000).toFixed(1)} km
                    </span>
                  )}
                </div>
                <h4>{a.title}</h4>
                <div className="activity-list-item-footer">
                  <span>{new Date(a.start_time).toLocaleDateString()}</span>
                  <span>{a.current_participants}/{a.max_participants} joined</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
      
      <div className="dashboard-map-container">
        <Map 
          activities={activities} 
          userLocation={userLocation} 
          onBoundsChange={handleBoundsChange} 
        />
      </div>
    </div>
  );
}
