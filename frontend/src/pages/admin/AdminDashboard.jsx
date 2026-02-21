import { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../../context/AuthContext';
import * as adminApi from '../../api/adminApi';
import { AdminMapView } from '../../components/LeafletMap';

export default function AdminDashboard() {
  const { logout } = useAuth();
  const [requests, setRequests] = useState([]);
  const [users, setUsers] = useState([]);
  const [ambulances, setAmbulances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('map');

  const fetch = async () => {
    try {
      const [mapRes, usersRes, ambRes] = await Promise.all([
        adminApi.getDashboardMap(),
        adminApi.getAllUsers(),
        adminApi.getAllAmbulances(),
      ]);
      setRequests(mapRes.data.requests || []);
      setUsers(usersRes.data.users || []);
      setAmbulances(ambRes.data.ambulances || []);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetch();
    const id = setInterval(fetch, 10000);
    return () => clearInterval(id);
  }, []);

  if (loading) return <div className="page"><div className="loading">Loading…</div></div>;
  if (error) return <div className="page"><div className="alert alert-error">{error}</div></div>;

  return (
    <div className="page page--wide">
      <header className="page-header">
        <h1>Admin Dashboard</h1>
        <div className="header-actions">
          <button className={`btn btn-tab ${tab === 'map' ? 'btn-tab--active' : ''}`} onClick={() => setTab('map')}>Map</button>
          <button className={`btn btn-tab ${tab === 'list' ? 'btn-tab--active' : ''}`} onClick={() => setTab('list')}>List</button>
          <button className="btn btn-ghost" onClick={logout}>Logout</button>
        </div>
      </header>
      {tab === 'map' && (
        <section className="card">
          <h2 className="card-title">Live Map</h2>
          <AdminMapView requests={requests} height={420} expandable />
        </section>
      )}
      {tab === 'list' && (
        <>
          <section className="card">
            <h2 className="card-title">Requests ({requests.length})</h2>
            {requests.length === 0 && <p className="card-desc">No requests</p>}
            <div className="list-items">
              {requests.slice(0, 15).map((r) => (
                <div key={r.id} className="list-item list-item--request">
                  <span className={`badge badge-${r.status}`}>{r.status === 'to_hospital' ? 'To Hospital' : r.status}</span>
                  <span>Accident: {r.location?.lat?.toFixed(4)}, {r.location?.lng?.toFixed(4)}</span>
                  {r.assigned_ambulance && (
                    <div className="ambulance-details">
                      <strong>Vehicle:</strong> {r.assigned_ambulance.vehicle_number} | <strong>Driver:</strong> {r.assigned_ambulance.name} | <strong>Phone:</strong> {r.assigned_ambulance.phone}
                      {r.assigned_ambulance.current_location && (
                        <span> | <strong>Location:</strong> {r.assigned_ambulance.current_location.lat?.toFixed(4)}, {r.assigned_ambulance.current_location.lng?.toFixed(4)}</span>
                      )}
                      {r.selected_hospital && <span> | <strong>Hospital:</strong> {r.selected_hospital.name}</span>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
          <section className="card">
            <h2 className="card-title">Users ({users.length})</h2>
            <div className="list-items">
              {users.slice(0, 8).map((u) => (
                <div key={u._id} className="list-item">{u.phone} – {u.name || '—'}</div>
              ))}
            </div>
          </section>
          <section className="card">
            <h2 className="card-title">Ambulances ({ambulances.length})</h2>
            <div className="list-items">
              {ambulances.slice(0, 8).map((a) => (
                <div key={a._id} className="list-item">{a.phone} – {a.name || '—'} <span className={`badge badge-${a.status || 'inactive'}`}>{a.status || 'inactive'}</span></div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
