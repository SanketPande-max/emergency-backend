import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import * as userApi from '../../api/userApi';
import { sensorService } from '../../services/sensorService';

export default function UserProfile() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [dob, setDob] = useState('');
  const [gender, setGender] = useState('');
  const [accidentDetectionEnabled, setAccidentDetectionEnabled] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [message, setMessage] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const { data } = await userApi.getMe();
        const u = data.user || {};
        setName(u.name || '');
        setEmail(u.email || '');
        setDob(u.date_of_birth ? (typeof u.date_of_birth === 'string' ? u.date_of_birth.slice(0, 10) : new Date(u.date_of_birth).toISOString().slice(0, 10)) : '');
        setGender(u.gender || '');
        setAccidentDetectionEnabled(!!u.accident_detection_enabled);
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
      await userApi.updateProfile({ name, email, date_of_birth: dob, gender, accident_detection_enabled: accidentDetectionEnabled });
      if (accidentDetectionEnabled) sensorService.start();
      else sensorService.stop();
      setMessage('Profile updated successfully');
    } catch (err) {
      setMessage(err.response?.data?.error || 'Update failed');
    } finally {
      setLoading(false);
    }
  };

  const handleAccidentToggle = async (checked) => {
    setAccidentDetectionEnabled(checked);
    setMessage('');
    try {
      await userApi.updateProfile({ accident_detection_enabled: checked });
      if (checked) sensorService.start();
      else sensorService.stop();
      setMessage('Accident detection ' + (checked ? 'enabled' : 'disabled'));
    } catch (err) {
      setAccidentDetectionEnabled(!checked);
      setMessage(err.response?.data?.error || 'Update failed');
    }
  };

  if (loadingProfile) return <div className="page"><div className="loading">Loading profile…</div></div>;

  return (
    <div className="page">
      <header className="page-header">
        <h1>Edit Profile</h1>
        <Link to="/user/dashboard" className="btn btn-ghost">← Dashboard</Link>
      </header>
      <section className="card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email@example.com" />
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
            <label className="toggle-label">
              <input type="checkbox" checked={accidentDetectionEnabled} onChange={(e) => handleAccidentToggle(e.target.checked)} />
              <span>Auto accident detection (rural/remote)</span>
            </label>
            <small>Uses phone sensors. If an accident is detected, we call you twice. No answer = we send help automatically.</small>
          </div>
          {message && <p className={message.includes('success') ? 'success-msg' : 'error-msg'}>{message}</p>}
          <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Saving…' : 'Save Profile'}</button>
        </form>
      </section>
      <footer className="page-footer">
        <Link to="/user/dashboard">← Back to Dashboard</Link>
      </footer>
    </div>
  );
}
