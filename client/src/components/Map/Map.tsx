import { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { type ActivityResponse } from '../../api/activities';
import { Link } from 'react-router-dom';
import Button from '../Button/Button';
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

// Custom icons based on urgency
const getIconUrl = (color: string) => `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`;

const createIcon = (color: string) => new L.Icon({
  iconUrl: getIconUrl(color),
  shadowUrl: shadowUrl,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  tooltipAnchor: [1, -34],
  shadowSize: [41, 41],
});

const icons = {
  blue: createIcon('blue'),
  red: createIcon('red'),
  orange: createIcon('orange'),
  green: createIcon('green'),
};

const getActivityIcon = (startTime: string) => {
  const start = new Date(startTime).getTime();
  const now = new Date().getTime();
  const hoursUntilStart = (start - now) / (1000 * 60 * 60);

  if (hoursUntilStart < 0) return icons.green; // Ongoing
  if (hoursUntilStart < 24) return icons.red; // Urgent (starts within 24h)
  if (hoursUntilStart < 72) return icons.orange; // Soon (starts within 3 days)
  return icons.blue; // Normal
};

interface MapProps {
  activities: ActivityResponse[];
  userLocation: [number, number] | null;
  onBoundsChange?: (bounds: L.LatLngBounds) => void;
}

// Component to handle map movement/bounds changes
function MapEvents({ onBoundsChange }: { onBoundsChange?: (bounds: L.LatLngBounds) => void }) {
  const map = useMap();
  
  useEffect(() => {
    if (!onBoundsChange) return;

    const handleMoveEnd = () => {
      onBoundsChange(map.getBounds());
    };

    map.on('moveend', handleMoveEnd);
    
    // Initial bounds
    handleMoveEnd();

    return () => {
      map.off('moveend', handleMoveEnd);
    };
  }, [map, onBoundsChange]);

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
    <div style={{ position: 'absolute', bottom: '20px', right: '20px', zIndex: 1000 }}>
      <Button 
        onClick={(e) => {
          e.stopPropagation();
          map.flyTo(userLocation, 13);
        }}
        style={{
          borderRadius: '50%',
          width: '40px',
          height: '40px',
          padding: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 2px 6px rgba(0,0,0,0.3)',
        }}
        title="Recenter to my location"
      >
        📍
      </Button>
    </div>
  );
}

// User location marker icon (red dot)
const userIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

export default function Map({ activities, userLocation, onBoundsChange }: MapProps) {
  // Default to a central location (e.g., somewhere in US or Europe) if no location
  const center: [number, number] = userLocation || [40.7128, -74.0060]; // Default NYC

  return (
    <div className="map-wrapper" style={{ position: 'relative' }}>
      <MapContainer
        center={center}
        zoom={13}
        scrollWheelZoom={true}
        className="leaflet-container"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />
        
        {userLocation && <RecenterAutomatically lat={userLocation[0]} lng={userLocation[1]} />}
        
        <MapEvents onBoundsChange={onBoundsChange} />

        {/* User Location Marker */}
        {userLocation && (
          <Marker position={userLocation} icon={userIcon} zIndexOffset={1000}>
            <Popup>You are here</Popup>
          </Marker>
        )}

        {activities.map((activity) => (
          <Marker 
            key={activity.id} 
            position={[activity.latitude, activity.longitude]}
            icon={getActivityIcon(activity.start_time)}
          >
            <Tooltip direction="top" opacity={0.9} permanent className="activity-tooltip">
              {activity.title.length > 20 ? activity.title.substring(0, 20) + '...' : activity.title}
            </Tooltip>
            <Popup className="custom-popup">
              <div className="activity-popup">
                <div className="popup-header">
                  <span className="popup-category">{activity.category || 'General'}</span>
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
                  Host: @{activity.host?.username}
                </div>
                
                <div className="popup-participants">
                  {activity.current_participants} / {activity.max_participants} joined
                </div>

                <div className="popup-actions">
                  <Link to={`/activities/${activity.id}`}>
                    <Button size="sm" fullWidth>View Details</Button>
                  </Link>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
        <RecenterButton userLocation={userLocation} />
      </MapContainer>
      
      {/* Legend */}
      <div style={{ position: 'absolute', bottom: '20px', left: '20px', zIndex: 1000, background: 'rgba(255,255,255,0.9)', padding: '10px', borderRadius: '8px', boxShadow: '0 2px 6px rgba(0,0,0,0.3)', fontSize: '0.85rem' }}>
        <h4 style={{ margin: '0 0 8px 0', fontSize: '0.9rem', color: '#333' }}>Legend</h4>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
          <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png" alt="Red" style={{ width: '12px' }} />
          <span style={{ color: '#333' }}>Starts &lt; 24h (Urgent)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
          <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png" alt="Orange" style={{ width: '12px' }} />
          <span style={{ color: '#333' }}>Starts &lt; 3 days</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
          <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png" alt="Blue" style={{ width: '12px' }} />
          <span style={{ color: '#333' }}>Normal</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png" alt="Green" style={{ width: '12px' }} />
          <span style={{ color: '#333' }}>Ongoing</span>
        </div>
      </div>
    </div>
  );
}
