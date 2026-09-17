import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './LocationPicker.css';

// Fix Leaflet's default icon issue
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

L.Icon.Default.mergeOptions({
  iconRetinaUrl,
  iconUrl,
  shadowUrl,
});

const defaultIcon = new L.Icon({
  iconUrl,
  iconRetinaUrl,
  shadowUrl,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

interface LocationPickerProps {
  position: [number, number] | null;
  onChange: (lat: number, lng: number) => void;
}

// Component to handle clicks on the map
function MapClickHandler({ onChange }: { onChange: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onChange(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

// Component to recenter on initial load
function RecenterAutomatically({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView([lat, lng]);
  }, [lat, lng, map]);
  return null;
}

export default function LocationPicker({ position, onChange }: LocationPickerProps) {
  // Default to Dinh Độc Lập (TP. Hồ Chí Minh)
  const [initialCenter, setInitialCenter] = useState<[number, number]>([10.7769, 106.6953]);
  const [hasLocated, setHasLocated] = useState(false);

  useEffect(() => {
    // Try to get user's location to center the map initially
    if (!position && navigator.geolocation && !hasLocated) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setInitialCenter([pos.coords.latitude, pos.coords.longitude]);
          setHasLocated(true);
        },
        () => {
          setHasLocated(true);
        }
      );
    }
  }, [position, hasLocated]);

  const center = position || initialCenter;

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
    <div className="location-picker-wrapper">
      <MapContainer
        center={center}
        zoom={14}
        scrollWheelZoom={true}
        className={`leaflet-container ${tileLayerConfig.className}`}
      >
        <TileLayer
          attribution={tileLayerConfig.attribution}
          url={tileLayerConfig.url}
        />
        
        {hasLocated && !position && <RecenterAutomatically lat={initialCenter[0]} lng={initialCenter[1]} />}
        
        <MapClickHandler onChange={onChange} />
        
        {position && (
          <Marker position={position} icon={defaultIcon} />
        )}
      </MapContainer>
      <div className="location-picker-hint">
        Nhấp vào bản đồ để thả ghim
      </div>
    </div>
  );
}
