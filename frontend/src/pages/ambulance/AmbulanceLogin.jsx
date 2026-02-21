import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import * as ambulanceApi from '../../api/ambulanceApi';

export default function AmbulanceLogin() {
  const navigate = useNavigate();
  const { loginAmbulance } = useAuth();
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState('phone');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSendOtp = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const normalized = phone.replace(/\D/g, '').slice(-10);
      const payload = normalized.length === 10 ? `+91${normalized}` : phone;
      await ambulanceApi.sendOtp(payload);
      setStep('otp');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const normalized = phone.replace(/\D/g, '').slice(-10);
      const payload = normalized.length === 10 ? `+91${normalized}` : phone;
      const { data } = await ambulanceApi.verifyOtp(payload, otp);
      loginAmbulance({ token: data.token, ambulance_id: data.ambulance_id });
      navigate('/ambulance/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Invalid or expired OTP');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ paddingTop: '2rem' }}>
      <h2 style={{ marginBottom: '1.5rem' }}>Ambulance Login</h2>
      <div className="card">
        {step === 'phone' ? (
          <form onSubmit={handleSendOtp}>
            <div className="form-group">
              <label>Phone Number</label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="e.g. 9876543210"
                required
              />
            </div>
            {error && <p className="error-msg">{error}</p>}
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Sending…' : 'Send OTP'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp}>
            <div className="form-group">
              <label>OTP</label>
              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                placeholder="Enter 6-digit OTP"
                maxLength={6}
                required
              />
            </div>
            {error && <p className="error-msg">{error}</p>}
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Verifying…' : 'Verify OTP'}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ marginTop: '0.5rem' }}
              onClick={() => setStep('phone')}
            >
              Change Number
            </button>
          </form>
        )}
      </div>
      <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
        <Link to="/">← Back to portals</Link>
      </p>
    </div>
  );
}
