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
  const [initialCenter, setInitialCenter] = useState<[number, number]>([40.7128, -74.0060]);
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

  return (
    <div className="location-picker-wrapper">
      <MapContainer
        center={center}
        zoom={14}
        scrollWheelZoom={true}
        className="leaflet-container"
      >
        <TileLayer
          attribution='&copy; OpenStreetMap contributors &copy; CARTO'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />
        
        {hasLocated && !position && <RecenterAutomatically lat={initialCenter[0]} lng={initialCenter[1]} />}
        
        <MapClickHandler onChange={onChange} />
        
        {position && (
          <Marker position={position} icon={defaultIcon} />
        )}
      </MapContainer>
      <div className="location-picker-hint">
        Click on the map to place a pin
      </div>
    </div>
  );
}
