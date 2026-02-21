import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import * as adminApi from '../../api/adminApi';

export default function AdminLogin() {
  const navigate = useNavigate();
  const { loginAdmin } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await adminApi.login(username, password);
      loginAdmin({ token: data.token });
      navigate('/admin/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ paddingTop: '2rem' }}>
      <h2 style={{ marginBottom: '1.5rem' }}>Admin Login</h2>
      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input value={username} onChange={(e) => setUsername(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error && <p className="error-msg">{error}</p>}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Logging in…' : 'Login'}
          </button>
        </form>
      </div>
      <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
        <Link to="/">← Back to portals</Link>
      </p>
    </div>
  );
}
