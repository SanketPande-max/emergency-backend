import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import * as ambulanceApi from '../../api/ambulanceApi';
import { fetchNearbyHospitals } from '../../api/hospitals';
import { MapPicker, MapView, MapExpandable } from '../../components/LeafletMap';
import { fetchRoute } from '../../api/osrm';

export default function AmbulanceDashboard() {
  const { logout } = useAuth();
  const [assigned, setAssigned] = useState(null);
  const [status, setStatus] = useState('inactive');
  const [location, setLocation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showMapPicker, setShowMapPicker] = useState(false);
  const [showHospitalPicker, setShowHospitalPicker] = useState(false);
  const [hospitals, setHospitals] = useState([]);
  const [routeToHospital, setRouteToHospital] = useState([]);

  const fetchAssigned = async () => {
    try {
      const { data } = await ambulanceApi.getAssignedDetails();
      const prevAssigned = assigned;
      setAssigned(data.assigned);
      // Play alarm if new assignment received
      if (!prevAssigned && data.assigned) {
        playAlarmSound();
      }
    } catch {
      setAssigned(null);
    }
  };

  const playAlarmSound = () => {
    // Create a simple alarm sound using Web Audio API
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800; // High frequency for alarm
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 3);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 3);
  };

  useEffect(() => {
    (async () => {
      try {
        const { data } = await ambulanceApi.getMe();
        // Redirect to profile if not completed
        if (!data.ambulance?.profile_completed) {
          window.location.href = '/ambulance/profile';
          return;
        }
        setStatus(data.ambulance?.status || 'inactive');
        const loc = data.ambulance?.current_location;
        if (loc?.lat) setLocation({ lat: loc.lat, lng: loc.lng });
      } catch { /* ignore */ }
    })();
    fetchAssigned();
    const id = setInterval(fetchAssigned, 3000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (!assigned || !location?.lat) { setRouteToHospital([]); return; }
    const dest = assigned.status === 'to_hospital' ? assigned.selected_hospital : assigned.accident_location;
    if (dest?.lat) fetchRoute(location, dest).then((r) => r && setRouteToHospital(r));
    else setRouteToHospital([]);
  }, [assigned?.status, assigned?.selected_hospital, assigned?.accident_location, location]);

  // Auto-update location when active (not just when assigned)
  useEffect(() => {
    if (status !== 'active' || !navigator.geolocation) return;
    const wid = navigator.geolocation.watchPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        setLocation({ lat: latitude, lng: longitude });
        try {
          await ambulanceApi.updateLocation(latitude, longitude);
        } catch { /* ignore */ }
      },
      () => {},
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }
    );
    return () => navigator.geolocation.clearWatch(wid);
  }, [status === 'active']);

  const tryGeolocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation not supported. Select location on map.');
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
        setError('Location denied. Please select your location on the map.');
        setShowMapPicker(true);
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  };

  const toggleStatus = async () => {
    const next = status === 'active' ? 'inactive' : 'active';
    setLoading(true);
    setError('');
    try {
      const { data } = await ambulanceApi.updateStatus(next);
      setStatus(data.status);
    } catch (e) {
      setError(e.response?.data?.error || 'Failed to update status');
    } finally {
      setLoading(false);
    }
  };

  const updateLocationWithCoords = async (lat, lng) => {
    setLoading(true);
    setError('');
    try {
      await ambulanceApi.updateLocation(lat, lng);
      setLocation({ lat, lng });
      setShowMapPicker(false);
    } catch (e) {
      setError(e.response?.data?.error || 'Failed to update location');
    } finally {
      setLoading(false);
    }
  };

  const handleReachedUser = async () => {
    const acc = assigned?.accident_location;
    if (!acc?.lat) return;
    setLoading(true);
    try {
      const list = await fetchNearbyHospitals(acc.lat, acc.lng);
      setHospitals(list);
      setShowHospitalPicker(true);
    } catch (e) {
      setError('Could not fetch hospitals');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectHospital = async (hospital) => {
    setLoading(true);
    setError('');
    try {
      await ambulanceApi.selectHospital(assigned.request_id, hospital);
      setShowHospitalPicker(false);
      fetchAssigned();
    } catch (e) {
      setError(e.response?.data?.error || 'Failed to select hospital');
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async (requestId) => {
    if (!requestId) {
      setError('Invalid request ID');
      return;
    }
    setLoading(true);
    setError('');
    try {
      let lat = null, lng = null;
      if (location?.lat && location?.lng) {
        lat = location.lat;
        lng = location.lng;
      } else if (navigator.geolocation) {
        try {
          const pos = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 3000, maximumAge: 0 });
          });
          lat = pos.coords.latitude;
          lng = pos.coords.longitude;
        } catch (geoError) {
          console.warn('Geolocation failed, completing without location update');
        }
      }
      const response = await ambulanceApi.completeRequest(requestId, lat, lng);
      if (response?.data?.message) {
        setAssigned(null);
        setStatus('active');
        setShowHospitalPicker(false);
        setError('');
      } else {
        throw new Error('Unexpected response from server');
      }
    } catch (e) {
      const errorMsg = e.response?.data?.error || e.message || 'Failed to complete request';
      setError(errorMsg);
      console.error('Complete request error:', e);
      if (e.response) {
        console.error('Response status:', e.response.status);
        console.error('Response data:', e.response.data);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReportIssue = async (requestId) => {
    if (!requestId) {
      setError('Invalid request ID');
      return;
    }
    const issueDescription = prompt('Describe the issue (e.g., Engine failure, Puncture, etc.):');
    if (!issueDescription) return;
    
    setLoading(true);
    setError('');
    try {
      const response = await ambulanceApi.reportIssue(requestId, issueDescription);
      if (response?.data?.message) {
        alert(response.data.message);
        setAssigned(null);
        setStatus('inactive');
        setShowHospitalPicker(false);
        setError('');
      } else {
        throw new Error('Unexpected response from server');
      }
    } catch (e) {
      const errorMsg = e.response?.data?.error || e.message || 'Failed to report issue';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleReportFake = async (requestId) => {
    if (!requestId) {
      setError('Invalid request ID');
      return;
    }
    if (!window.confirm('Are you sure this is a fake request? This will add a demerit point to the user.')) {
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await ambulanceApi.reportFake(requestId);
      if (response?.data?.message) {
        alert(response.data.message);
        setAssigned(null);
        setStatus('active');
        setShowHospitalPicker(false);
        setError('');
      } else {
        throw new Error('Unexpected response from server');
      }
    } catch (e) {
      const errorMsg = e.response?.data?.error || e.message || 'Failed to report fake request';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const openDirections = () => {
    const origin = assigned?.directions?.origin || location;
    const dest = assigned?.status === 'to_hospital' ? assigned?.selected_hospital : assigned?.accident_location;
    if (!origin?.lat || !dest?.lat) return;
    const route = `${origin.lat},${origin.lng};${dest.lat},${dest.lng}`;
    window.open(`https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=${route}`, '_blank');
  };

  const dest = assigned?.status === 'to_hospital' ? assigned?.selected_hospital : assigned?.accident_location;

  return (
    <div className="page">
      <header className="page-header">
        <h1>Ambulance Dashboard</h1>
        <button className="btn btn-ghost" onClick={logout}>Logout</button>
      </header>
      {error && <div className="alert alert-error">{error}</div>}
      <section className="card">
        <h2 className="card-title">Status & Location</h2>
        <div className="status-row">
          <span className={`badge badge-${status}`}>{status}</span>
        </div>
        {location && <p className="success-msg">Location: {location.lat.toFixed(4)}, {location.lng.toFixed(4)} (Auto-updating)</p>}
        {showMapPicker && (
          <div className="map-picker-wrapper">
            <MapPicker initialCenter={location} onSelect={updateLocationWithCoords} height={260} />
          </div>
        )}
        <button className={`btn ${status === 'active' ? 'btn-secondary' : 'btn-primary'}`} onClick={toggleStatus} disabled={loading}>
          Go {status === 'active' ? 'Inactive' : 'Active'}
        </button>
      </section>
      {assigned ? (
        <section className="card card--highlight">
          <h2 className="card-title">Active Assignment</h2>
          <div className="status-row">
            <span className={`badge badge-${assigned.status}`}>{assigned.status === 'to_hospital' ? 'To Hospital' : assigned.status}</span>
          </div>
          <div className="info-grid">
            <div><strong>User</strong><br />{assigned.user_name || '—'}</div>
            <div><strong>Phone</strong><br /><a href={`tel:${assigned.user_phone}`}>{assigned.user_phone}</a></div>
            <div><strong>Accident</strong><br />{assigned.accident_location?.lat?.toFixed(4)}, {assigned.accident_location?.lng?.toFixed(4)}</div>
            {assigned.selected_hospital && <div><strong>Hospital</strong><br />{assigned.selected_hospital.name}</div>}
          </div>
          {assigned.status === 'assigned' && (
            <>
              <button className="btn btn-primary" onClick={handleReachedUser} disabled={loading}>
                Reached User – Select Hospital
              </button>
              <button className="btn btn-secondary" onClick={() => handleReportIssue(assigned.request_id)} disabled={loading} style={{ marginTop: '0.5rem', background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b', borderColor: 'rgba(245, 158, 11, 0.3)' }}>
                ⚠️ Report Issue (Engine/Puncture)
              </button>
              <button className="btn btn-secondary" onClick={() => handleReportFake(assigned.request_id)} disabled={loading} style={{ marginTop: '0.5rem', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderColor: 'rgba(239, 68, 68, 0.3)' }}>
                ⚠️ Report Fake Request
              </button>
            </>
          )}
          {showHospitalPicker && hospitals.length > 0 && (
            <div className="hospital-picker">
              <p className="card-desc">Select nearest hospital:</p>
              {hospitals.map((h, i) => (
                <button key={i} type="button" className="btn btn-secondary hospital-btn" onClick={() => handleSelectHospital(h)}>
                  {h.name}
                </button>
              ))}
            </div>
          )}
          {assigned.status === 'to_hospital' && (
            <>
              <button className="btn btn-primary" onClick={openDirections}>Navigate to Hospital</button>
              <button className="btn btn-secondary" onClick={() => handleComplete(assigned.request_id)} disabled={loading}>
                Mark Completed
              </button>
            </>
          )}
          {assigned.status === 'assigned' && !showHospitalPicker && (
            <>
              <button className="btn btn-primary" onClick={openDirections}>Navigate to User</button>
            </>
          )}
          {(assigned.status === 'assigned' || assigned.status === 'to_hospital') && location && dest && (
            <div className="map-section">
              <MapExpandable defaultHeight={260}>
                <MapView
                  center={location}
                  zoom={14}
                  accident={assigned.accident_location}
                  ambulance={location}
                  hospital={assigned.selected_hospital}
                  track={[]}
                  route={routeToHospital.length ? routeToHospital : []}
                  height={260}
                />
              </MapExpandable>
            </div>
          )}
        </section>
      ) : (
        <section className="card">
          <p className="card-desc">No active assignment. Stay active and you will receive requests.</p>
        </section>
      )}
      <footer className="page-footer">
        <Link to="/ambulance/profile">Edit Profile</Link>
      </footer>
    </div>
  );
}
