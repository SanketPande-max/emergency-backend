import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import * as userApi from '../../api/userApi';
import { MapPicker, TrackingMap } from '../../components/LeafletMap';
import { sensorService } from '../../services/sensorService';

export default function UserDashboard() {
  const { logout } = useAuth();
  const [request, setRequest] = useState(null);
  const [location, setLocation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showMapPicker, setShowMapPicker] = useState(false);
  const [userInfo, setUserInfo] = useState(null);

  const fetchRequest = async () => {
    try {
      const { data } = await userApi.getMyRequest();
      setRequest(data.request);
    } catch {
      setRequest(null);
    }
  };

  useEffect(() => {
    fetchRequest();
    const id = setInterval(fetchRequest, 3000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await userApi.getMe();
        setUserInfo(data.user);
        if (data.user?.accident_detection_enabled) sensorService.start();
      } catch { /* ignore */ }
    })();
    return () => sensorService.stop();
  }, []);

  const tryGeolocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser');
      setShowMapPicker(true);
      return;
    }
    setLoading(true);
    setError('');
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        await updateLocationWithCoords(latitude, longitude);
        setLoading(false);
      },
      () => {
        setError('Location access denied. Please select your location on the map below.');
        setShowMapPicker(true);
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  };

  const updateLocationWithCoords = async (lat, lng) => {
    setLoading(true);
    setError('');
    try {
      await userApi.updateLocation(lat, lng);
      setLocation({ lat, lng });
      setShowMapPicker(false);
    } catch (e) {
      setError(e.response?.data?.error || 'Failed to update location');
    } finally {
      setLoading(false);
    }
  };

  const handleMapPickerSelect = (lat, lng) => {
    updateLocationWithCoords(lat, lng);
  };

  const handleRequestEmergency = async () => {
    if (!location) {
      setError('Please set your location first');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const { data } = await userApi.requestEmergency(location.lat, location.lng);
      setRequest(data.request);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="page-header">
        <h1>User Dashboard</h1>
        <button className="btn btn-ghost" onClick={logout}>Logout</button>
      </header>
      {error && <div className="alert alert-error">{error}</div>}
      {userInfo?.is_blacklisted && (
        <div className="alert alert-error" style={{ background: 'rgba(239, 68, 68, 0.15)', borderColor: '#ef4444', color: '#dc2626' }}>
          ⚠️ Your account is blacklisted due to fake emergency requests. You cannot create new requests.
        </div>
      )}
      {userInfo && userInfo.demerit_points > 0 && !userInfo.is_blacklisted && (
        <div className="alert" style={{ background: 'rgba(245, 158, 11, 0.15)', borderColor: '#f59e0b', color: '#d97706' }}>
          ⚠️ Warning: You have {userInfo.demerit_points} demerit point(s). {userInfo.demerit_points === 1 ? 'One more fake request will result in blacklisting.' : ''}
        </div>
      )}
      <section className="card">
        <h2 className="card-title">Your Location</h2>
        <p className="card-desc">Allow browser location or select manually on the map</p>
        <button className="btn btn-secondary" onClick={tryGeolocation} disabled={loading}>
          {loading ? 'Getting location…' : 'Allow & Update Location'}
        </button>
        {location && (
          <p className="success-msg">Location set: {location.lat.toFixed(4)}, {location.lng.toFixed(4)}</p>
        )}
        {showMapPicker && (
          <div className="map-picker-wrapper">
            <MapPicker
              initialCenter={location}
              onSelect={handleMapPickerSelect}
              height={260}
            />
          </div>
        )}
      </section>
      {request ? (
        <section className="card card--highlight">
          <h2 className="card-title">Current Request</h2>
          <div className="request-status">
            <span className={`badge badge-${request.status}`}>{request.status === 'to_hospital' ? 'To Hospital' : request.status}</span>
          </div>
          {request.assigned_ambulance && (
            <div className="info-grid">
              <div><strong>Driver</strong><br />{request.assigned_ambulance.name}</div>
              <div><strong>Phone</strong><br /><a href={`tel:${request.assigned_ambulance.phone}`}>{request.assigned_ambulance.phone}</a></div>
              <div><strong>Vehicle</strong><br />{request.assigned_ambulance.vehicle_number}</div>
              {request.selected_hospital && <div><strong>Hospital</strong><br />{request.selected_hospital.name}</div>}
            </div>
          )}
          <div className="map-section">
            <TrackingMap request={request} height={300} expandable />
          </div>
        </section>
      ) : (
        <section className="card">
          <h2 className="card-title">Request Emergency</h2>
          <p className="card-desc">Set your location first, then request an ambulance.</p>
          <button className="btn btn-primary" onClick={handleRequestEmergency} disabled={loading || !location || userInfo?.is_blacklisted}>
            {loading ? 'Requesting…' : userInfo?.is_blacklisted ? 'Account Blacklisted' : 'Request Emergency'}
          </button>
        </section>
      )}
      <footer className="page-footer">
        <Link to="/user/profile">Edit Profile</Link>
      </footer>
    </div>
  );
}
