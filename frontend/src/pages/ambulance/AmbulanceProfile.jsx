import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import * as ambulanceApi from '../../api/ambulanceApi';

export default function AmbulanceProfile() {
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [dob, setDob] = useState('');
  const [gender, setGender] = useState('');
  const [vehicleNumber, setVehicleNumber] = useState('');
  const [drivingLicense, setDrivingLicense] = useState('');
  const [ambulanceType, setAmbulanceType] = useState('any');
  const [loading, setLoading] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [message, setMessage] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const { data } = await ambulanceApi.getMe();
        const a = data.ambulance || {};
        setName(a.name || '');
        setAge(a.age ? String(a.age) : '');
        setDob(a.date_of_birth ? (typeof a.date_of_birth === 'string' ? a.date_of_birth.slice(0, 10) : new Date(a.date_of_birth).toISOString().slice(0, 10)) : '');
        setGender(a.gender || '');
        setVehicleNumber(a.vehicle_number || '');
        setDrivingLicense(a.driving_license || '');
        setAmbulanceType(a.ambulance_type || 'any');
      } catch {
        setMessage('Could not load profile');
      } finally {
        setLoadingProfile(false);
      }
    })();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    try {
      await ambulanceApi.updateProfile({
        name,
        age: age ? parseInt(age, 10) : undefined,
        date_of_birth: dob || undefined,
        gender: gender || undefined,
        vehicle_number: vehicleNumber,
        driving_license: drivingLicense,
        ambulance_type: ambulanceType,
      });
      setMessage('Profile updated successfully');
      // Check if profile is now complete and redirect to dashboard
      if (name && age && dob && gender && vehicleNumber && drivingLicense) {
        setTimeout(() => {
          window.location.href = '/ambulance/dashboard';
        }, 1000);
      }
    } catch (err) {
      setMessage(err.response?.data?.error || 'Update failed');
    } finally {
      setLoading(false);
    }
  };

  if (loadingProfile) return <div className="page"><div className="loading">Loading profile…</div></div>;

  return (
    <div className="page">
      <header className="page-header">
        <h1>Ambulance Profile</h1>
        <Link to="/ambulance/dashboard" className="btn btn-ghost">← Dashboard</Link>
      </header>
      <section className="card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Driver name" required />
          </div>
          <div className="form-group">
            <label>Age</label>
            <input type="number" value={age} onChange={(e) => setAge(e.target.value)} placeholder="Age" />
          </div>
          <div className="form-group">
            <label>Date of Birth</label>
            <input type="date" value={dob} onChange={(e) => setDob(e.target.value)} />
          </div>
          <div className="form-group">
            <label>Gender</label>
            <select value={gender} onChange={(e) => setGender(e.target.value)}>
              <option value="">Select</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="form-group">
            <label>Vehicle Number</label>
            <input value={vehicleNumber} onChange={(e) => setVehicleNumber(e.target.value)} placeholder="e.g. MH 12 AB 1234" required />
          </div>
          <div className="form-group">
            <label>Driving License</label>
            <input value={drivingLicense} onChange={(e) => setDrivingLicense(e.target.value)} placeholder="License number" required />
          </div>
          <div className="form-group">
            <label>Ambulance Type</label>
            <select value={ambulanceType} onChange={(e) => setAmbulanceType(e.target.value)} className="form-control">
              <option value="any">Any</option>
              <option value="basic_life">Basic Life Support</option>
              <option value="advance_life">Advance Life Support</option>
              <option value="icu_life">ICU Life Support</option>
            </select>
          </div>
          {message && <p className={message.includes('success') ? 'success-msg' : 'error-msg'}>{message}</p>}
          <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Saving…' : 'Save Profile'}</button>
        </form>
      </section>
      <footer className="page-footer">
        <Link to="/ambulance/dashboard">← Back to Dashboard</Link>
      </footer>
    </div>
  );
}
