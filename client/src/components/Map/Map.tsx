import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { type ActivityResponse } from '../../api/activities';
import { Link } from 'react-router-dom';
import { LocateFixed, Star } from 'lucide-react';
import Button from '../Button/Button';
import { normalizeCategoryName } from '../../types/activity-mapper';
import './Map.css';

// Fix Leaflet's default icon issue with webpack/vite
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

L.Icon.Default.mergeOptions({
  iconRetinaUrl,
  iconUrl,
  shadowUrl,
});

// Custom DivIcon markers based on urgency
type UrgencyLevel = 'urgent' | 'soon' | 'normal' | 'ongoing';

const getUrgencyLevel = (startTime: string): UrgencyLevel => {
  const start = new Date(startTime).getTime();
  const now = new Date().getTime();
  const hoursUntilStart = (start - now) / (1000 * 60 * 60);

  if (hoursUntilStart < 0) return 'ongoing';
  if (hoursUntilStart < 24) return 'urgent';
  if (hoursUntilStart < 72) return 'soon';
  return 'normal';
};

const urgencyColors: Record<UrgencyLevel, string> = {
  urgent: '#ef4444',
  soon: '#f97316',
  normal: '#6366f1',
  ongoing: '#22c55e',
};

const getTimeLabel = (startTime: string): string => {
  const start = new Date(startTime).getTime();
  const now = new Date().getTime();
  const diffMs = start - now;

  if (diffMs < 0) return 'Bây giờ';
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  if (hours < 1) {
    const mins = Math.max(1, Math.floor(diffMs / (1000 * 60)));
    return `${mins}m`;
  }
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  return `${days}d`;
};

const createDivIcon = (urgency: UrgencyLevel, hasConflict = false) => {
  const color = urgencyColors[urgency];
  const pulseClass = urgency === 'urgent' && !hasConflict ? 'marker-pulse' : '';
  const conflictClass = hasConflict ? 'custom-marker--conflict' : '';

  return L.divIcon({
    className: `custom-marker-wrapper ${conflictClass}`,
    html: `
      <div class="custom-marker marker-${urgency} ${pulseClass} ${conflictClass}">
        <div class="marker-pin" style="background: ${color}; border-color: ${color};">
          <div class="marker-dot"></div>
        </div>
        <div class="marker-shadow-dot"></div>
      </div>
    `,
    iconSize: [30, 42],
    iconAnchor: [15, 42],
    popupAnchor: [0, -42],
    tooltipAnchor: [0, -42],
  });
};

interface MapProps {
  activities: ActivityResponse[];
  userLocation: [number, number] | null;
  onBoundsChange?: (bounds: L.LatLngBounds) => void;
  userInterests?: string[];
  onMapClick?: () => void;
  isCompact?: boolean;
}

// Component to handle map movement/bounds changes & optional map click
function MapEvents({ 
  onBoundsChange,
  onMapClick,
}: { 
  onBoundsChange?: (bounds: L.LatLngBounds) => void;
  onMapClick?: () => void;
}) {
  const map = useMap();
  
  useEffect(() => {
    const handleMoveEnd = () => {
      onBoundsChange?.(map.getBounds());
    };

    const handleClick = () => {
      onMapClick?.();
    };

    map.on('moveend', handleMoveEnd);
    if (onMapClick) {
      map.on('click', handleClick);
    }
    
    // Initial bounds
    handleMoveEnd();

    return () => {
      map.off('moveend', handleMoveEnd);
      if (onMapClick) {
        map.off('click', handleClick);
      }
    };
  }, [map, onBoundsChange, onMapClick]);

  return null;
}

// Force Leaflet to recalculate container dimensions when expanding or resizing
function InvalidateSizeOnResize() {
  const map = useMap();
  useEffect(() => {
    const invalidate = () => map.invalidateSize();
    invalidate();
    const t1 = setTimeout(invalidate, 120);
    const t2 = setTimeout(invalidate, 350);
    window.addEventListener('resize', invalidate);
    return () => {
      window.removeEventListener('resize', invalidate);
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [map]);
  return null;
}

// Component to recenter map when user location is found
function RecenterAutomatically({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView([lat, lng]);
  }, [lat, lng, map]);
  return null;
}

// Custom hook to get the map instance for the recenter button
function RecenterButton({ userLocation }: { userLocation: [number, number] | null }) {
  const map = useMap();
  if (!userLocation) return null;

  return (
    <div className="recenter-btn-wrapper">
      <Button 
        onClick={(e) => {
          e.stopPropagation();
          map.flyTo(userLocation, 13);
        }}
        className="recenter-btn"
        title="Quay lại vị trí của tôi"
      >
        <LocateFixed size={22} className="recenter-icon" color="#ef4444" strokeWidth={2.2} />
      </Button>
    </div>
  );
}

// User location marker icon (pulsing blue dot)
const userLocationIcon = L.divIcon({
  className: 'custom-marker-wrapper',
  html: `
    <div class="user-location-marker">
      <div class="user-location-pulse"></div>
      <div class="user-location-dot"></div>
    </div>
  `,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
  popupAnchor: [0, -10],
});

// Activity Marker with clickable Tooltip label that opens popup
function ActivityMarker({
  activity,
  urgency,
  matchesInterest,
  timeLabel,
}: {
  activity: ActivityResponse;
  urgency: UrgencyLevel;
  matchesInterest: boolean;
  timeLabel: string;
}) {
  const markerRef = useRef<L.Marker>(null);
  const hasConflict = !!activity.conflict_info?.has_conflict;

  const handleTooltipClick = (e: L.LeafletMouseEvent) => {
    if (e.originalEvent) {
      e.originalEvent.stopPropagation();
    }
    markerRef.current?.openPopup();
  };

  return (
    <Marker 
      ref={markerRef}
      key={activity.id} 
      position={[activity.latitude, activity.longitude]}
      icon={createDivIcon(urgency, hasConflict)}
      zIndexOffset={hasConflict ? -100 : matchesInterest ? 500 : 0}
    >
      <Tooltip 
        direction="top" 
        opacity={hasConflict ? 0.5 : 0.95} 
        permanent 
        interactive={true}
        className={`activity-tooltip ${hasConflict ? 'tooltip-conflict' : ''} ${matchesInterest ? 'tooltip-match' : ''}`}
        eventHandlers={{
          click: handleTooltipClick,
        }}
      >
        <span className={`tooltip-time-badge ${hasConflict ? 'tooltip-time-badge--conflict' : ''}`}>{timeLabel}</span>
        {hasConflict && <span className="tooltip-conflict-badge" title="Trùng lịch cá nhân">⚠️</span>}
        {matchesInterest && !hasConflict && (
          <span className="tooltip-star" title="Phù hợp sở thích của bạn">
            <Star size={12} fill="#eab308" color="#eab308" className="tooltip-star-icon" />
          </span>
        )}
        {' '}
        {activity.title.length > 18 ? activity.title.substring(0, 18) + '...' : activity.title}
      </Tooltip>
      <Popup className="custom-popup">
        <div className="activity-popup">
          {hasConflict && (
            <div className="popup-conflict-warning">
              ⚠️ {activity.conflict_info?.warning_message || 'Trùng giờ với lịch cá nhân của bạn'}
            </div>
          )}
          <div className="popup-header">
            <span className="popup-category">{normalizeCategoryName(activity.category)}</span>
            {activity.distance_meters !== undefined && (
              <span className="popup-distance">
                {(activity.distance_meters / 1000).toFixed(1)} km
              </span>
            )}
          </div>
          
          <h3 className="popup-title">{activity.title}</h3>
          <p className="popup-time">
            {new Date(activity.start_time).toLocaleString([], {
              month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
            })}
          </p>
          
          <div className="popup-host">
            Người tổ chức: @{activity.host?.username}
          </div>
          
          <div className="popup-participants">
            {activity.current_participants} / {activity.max_participants} người tham gia
          </div>

          <div className="popup-actions">
            <Link to={`/activities/${activity.id}`}>
              <Button size="sm" fullWidth>Xem chi tiết</Button>
            </Link>
          </div>
        </div>
      </Popup>
    </Marker>
  );
}

export default function Map({ 
  activities, 
  userLocation, 
  onBoundsChange, 
  userInterests,
  onMapClick,
  isCompact = false,
}: MapProps) {
  // Default to Dinh Độc Lập (TP. Hồ Chí Minh) if no GPS location
  const center: [number, number] = userLocation || [10.7769, 106.6953];

  const isMatchingInterest = (category: string | null): boolean => {
    if (!userInterests || userInterests.length === 0 || !category) return false;
    return userInterests.some(interest => 
      interest.toLowerCase() === category.toLowerCase()
    );
  };

  const cartoApiKey = import.meta.env.VITE_CARTO_API_KEY;

  const tileLayerConfig = cartoApiKey
    ? {
        url: `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=${cartoApiKey}`,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        className: '',
      }
    : {
        url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        className: 'modern-map-tiles',
      };

  return (
    <div className={`map-wrapper ${isCompact ? 'map-wrapper--compact' : ''}`}>
      <MapContainer
        center={center}
        zoom={13}
        scrollWheelZoom={true}
        className={`leaflet-container ${tileLayerConfig.className}`}
      >
        <TileLayer
          attribution={tileLayerConfig.attribution}
          url={tileLayerConfig.url}
        />
        
        <InvalidateSizeOnResize />

        {userLocation && <RecenterAutomatically lat={userLocation[0]} lng={userLocation[1]} />}
        
        <MapEvents onBoundsChange={onBoundsChange} onMapClick={onMapClick} />

        {/* User Location Marker */}
        {userLocation && (
          <Marker position={userLocation} icon={userLocationIcon} zIndexOffset={1000}>
            <Popup>Bạn ở đây</Popup>
          </Marker>
        )}

        {activities.map((activity) => {
          const urgency = getUrgencyLevel(activity.start_time);
          const matchesInterest = isMatchingInterest(activity.category);
          const timeLabel = getTimeLabel(activity.start_time);

          return (
            <ActivityMarker
              key={activity.id}
              activity={activity}
              urgency={urgency}
              matchesInterest={matchesInterest}
              timeLabel={timeLabel}
            />
          );
        })}
        <RecenterButton userLocation={userLocation} />
      </MapContainer>
    </div>
  );
}
