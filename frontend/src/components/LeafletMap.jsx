import { useState, useCallback, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { fetchRoute } from '../api/osrm';
import 'leaflet/dist/leaflet.css';

const ROUTE_COLOR = '#4285F4';
const TRACK_COLOR = '#34A853';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const ACCIDENT_ICON = new L.DivIcon({
  html: '<div class="map-marker map-marker--accident"></div>',
  className: 'map-marker-wrap',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

const AMBULANCE_ICON = new L.DivIcon({
  html: '<div class="map-marker map-marker--ambulance"></div>',
  className: 'map-marker-wrap',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

const HOSPITAL_ICON = new L.DivIcon({
  html: '<div class="map-marker map-marker--hospital"></div>',
  className: 'map-marker-wrap',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

const DEFAULT_CENTER = [20.5937, 78.9629];

function MapClickHandler({ onSelect }) {
  useMapEvents({ click: (e) => onSelect && onSelect(e.latlng.lat, e.latlng.lng) });
  return null;
}

export function MapExpandable({ children, defaultHeight = 280, minHeight = 200 }) {
  const [expanded, setExpanded] = useState(false);
  const height = expanded ? '70vh' : defaultHeight;
  return (
    <div className="map-expandable">
      <button type="button" className="map-expand-btn" onClick={() => setExpanded(!expanded)} title={expanded ? 'Minimize' : 'Maximize'}>
        {expanded ? '− Minimize' : '+ Expand Map'}
      </button>
      <div className="map-expandable-inner" style={{ height, minHeight }}>
        {children}
      </div>
    </div>
  );
}

export function MapPicker({ initialCenter, onSelect, height = 280 }) {
  const [selected, setSelected] = useState(initialCenter ? [initialCenter.lat, initialCenter.lng] : null);

  const handleMapClick = useCallback((lat, lng) => {
    setSelected([lat, lng]);
  }, []);

  const handleConfirm = () => {
    if (selected && onSelect) onSelect(selected[0], selected[1]);
  };

  const center = selected || (initialCenter ? [initialCenter.lat, initialCenter.lng] : null) || DEFAULT_CENTER;

  return (
    <div className="map-picker">
      <p className="map-picker-hint">Click on the map to select your location</p>
      <div className="map-container" style={{ height }}>
        <MapContainer center={center} zoom={14} style={{ height: '100%' }} scrollWheelZoom>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <MapClickHandler onSelect={handleMapClick} />
          {selected && <Marker position={selected} />}
        </MapContainer>
      </div>
      {selected && (
        <div className="map-picker-actions">
          <span className="map-picker-coords">{selected[0].toFixed(5)}, {selected[1].toFixed(5)}</span>
          <button type="button" className="btn btn-primary" onClick={handleConfirm}>Use This Location</button>
        </div>
      )}
    </div>
  );
}

export function MapView({ center, zoom = 14, accident, ambulance, hospital, track = [], route = [], height = 280 }) {
  const mapCenter = center ? [center.lat, center.lng] : (accident ? [accident.lat, accident.lng] : ambulance ? [ambulance.lat, ambulance.lng] : hospital ? [hospital.lat, hospital.lng] : DEFAULT_CENTER);
  const trackPositions = track?.length ? track.map((t) => [t.lat, t.lng]) : [];
  const routePositions = route?.length ? route.map((r) => [r.lat, r.lng]) : [];

  return (
    <div className="map-view" style={{ height, borderRadius: 12, overflow: 'hidden' }}>
      <MapContainer center={mapCenter} zoom={zoom} style={{ height: '100%' }} scrollWheelZoom>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {accident?.lat && <Marker position={[accident.lat, accident.lng]} icon={ACCIDENT_ICON}><Popup>Accident / Pickup</Popup></Marker>}
        {hospital?.lat && <Marker position={[hospital.lat, hospital.lng]} icon={HOSPITAL_ICON}><Popup>{hospital.name || 'Hospital'}</Popup></Marker>}
        {ambulance?.lat && <Marker position={[ambulance.lat, ambulance.lng]} icon={AMBULANCE_ICON}><Popup>Ambulance</Popup></Marker>}
        {trackPositions.length > 1 && <Polyline positions={trackPositions} color={TRACK_COLOR} weight={4} opacity={0.9} />}
        {routePositions.length > 1 && <Polyline positions={routePositions} color={ROUTE_COLOR} weight={5} opacity={0.85} />}
      </MapContainer>
    </div>
  );
}

export function TrackingMap({ request, height = 300, expandable }) {
  const [route, setRoute] = useState([]);
  const accident = request?.location;
  const ambulance = request?.assigned_ambulance?.current_location;
  const hospital = request?.selected_hospital;
  const track = request?.track || [];
  const isToHospital = request?.status === 'to_hospital';
  const dest = isToHospital ? hospital : accident;
  const center = accident || ambulance ? { lat: (dest || ambulance)?.lat ?? accident?.lat, lng: (dest || ambulance)?.lng ?? accident?.lng } : undefined;

  useEffect(() => {
    if (ambulance?.lat && dest?.lat) {
      fetchRoute(ambulance, dest).then((r) => r && setRoute(r));
    } else {
      setRoute([]);
    }
  }, [ambulance?.lat, ambulance?.lng, dest?.lat, dest?.lng]);

  const content = (
    <MapView
      center={center}
      zoom={15}
      accident={accident}
      ambulance={ambulance}
      hospital={hospital}
      track={track}
      route={route}
      height={height}
    />
  );

  return expandable ? <MapExpandable defaultHeight={height}>{content}</MapExpandable> : content;
}

export function AdminMapView({ requests = [], height = 420, expandable }) {
  const [routes, setRoutes] = useState({});
  const firstLoc = requests[0]?.location;
  const center = firstLoc ? [firstLoc.lat, firstLoc.lng] : DEFAULT_CENTER;

  useEffect(() => {
    requests.forEach((r) => {
      const amb = r.assigned_ambulance?.current_location;
      const dest = r.status === 'to_hospital' && r.selected_hospital ? r.selected_hospital : r.location;
      if (amb?.lat && dest?.lat) {
        fetchRoute(amb, dest).then((route) => {
          if (route) setRoutes((prev) => ({ ...prev, [r.id]: route }));
        });
      }
    });
  }, [requests]);

  const content = (
    <div className="map-view" style={{ height, borderRadius: 12, overflow: 'hidden' }}>
      <MapContainer center={center} zoom={12} style={{ height: '100%' }} scrollWheelZoom>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {requests.map((r) => (
          <div key={r.id}>
            {r.location?.lat && <Marker position={[r.location.lat, r.location.lng]} icon={ACCIDENT_ICON}><Popup>Accident</Popup></Marker>}
            {r.selected_hospital?.lat && <Marker position={[r.selected_hospital.lat, r.selected_hospital.lng]} icon={HOSPITAL_ICON}><Popup>{r.selected_hospital.name}</Popup></Marker>}
            {r.assigned_ambulance?.current_location?.lat && (
              <Marker position={[r.assigned_ambulance.current_location.lat, r.assigned_ambulance.current_location.lng]} icon={AMBULANCE_ICON}>
                <Popup>Ambulance: {r.assigned_ambulance.name}</Popup>
              </Marker>
            )}
            {r.track?.length > 1 && <Polyline key={`t-${r.id}`} positions={r.track.map((t) => [t.lat, t.lng])} color={r.track_color || TRACK_COLOR} weight={3} opacity={0.8} />}
            {routes[r.id]?.length > 1 && <Polyline key={`r-${r.id}`} positions={routes[r.id].map((p) => [p.lat, p.lng])} color={r.track_color || ROUTE_COLOR} weight={4} opacity={0.85} />}
          </div>
        ))}
      </MapContainer>
    </div>
  );

  return expandable ? <MapExpandable defaultHeight={height}>{content}</MapExpandable> : content;
}
