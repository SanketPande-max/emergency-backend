import { Link } from 'react-router-dom';

export default function Landing() {
  return (
    <div className="page">
      <h1 style={{ textAlign: 'center', marginBottom: '0.5rem', fontSize: '1.75rem', paddingTop: '2rem' }}>
        Emergency Response System
      </h1>
      <p style={{ textAlign: 'center', color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Select your portal to continue
      </p>
      <Link to="/user" className="portal-link user">
        User Portal – Request Emergency
      </Link>
      <Link to="/ambulance" className="portal-link ambulance">
        Ambulance Portal – Accept Requests
      </Link>
      <Link to="/admin" className="portal-link admin">
        Admin Portal – Dashboard
      </Link>
    </div>
  );
}
