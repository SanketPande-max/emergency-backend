import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Landing from './pages/Landing';
import UserLogin from './pages/user/UserLogin';
import UserDashboard from './pages/user/UserDashboard';
import UserProfile from './pages/user/UserProfile';
import AmbulanceLogin from './pages/ambulance/AmbulanceLogin';
import AmbulanceDashboard from './pages/ambulance/AmbulanceDashboard';
import AmbulanceProfile from './pages/ambulance/AmbulanceProfile';
import AdminLogin from './pages/admin/AdminLogin';
import AdminDashboard from './pages/admin/AdminDashboard';
import './styles/index.css';

function RequireAuth({ children, role }) {
  const { isAuthenticated, role: userRole, loading } = useAuth();
  if (loading) return <div className="container" style={{ padding: '3rem', textAlign: 'center' }}>Loading…</div>;
  if (!isAuthenticated) return <Navigate to="/" replace />;
  if (role && userRole !== role) return <Navigate to="/" replace />;
  return children;
}

function RequireGuest({ children, redirectTo, role }) {
  const { isAuthenticated, role: userRole, loading } = useAuth();
  if (loading) return null;
  if (isAuthenticated && (!role || userRole === role)) return <Navigate to={redirectTo} replace />;
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/user" element={<RequireGuest redirectTo="/user/dashboard" role="user"><UserLogin /></RequireGuest>} />
          <Route path="/user/dashboard" element={<RequireAuth role="user"><UserDashboard /></RequireAuth>} />
          <Route path="/user/profile" element={<RequireAuth role="user"><UserProfile /></RequireAuth>} />
          <Route path="/ambulance" element={<RequireGuest redirectTo="/ambulance/dashboard" role="ambulance"><AmbulanceLogin /></RequireGuest>} />
          <Route path="/ambulance/dashboard" element={<RequireAuth role="ambulance"><AmbulanceDashboard /></RequireAuth>} />
          <Route path="/ambulance/profile" element={<RequireAuth role="ambulance"><AmbulanceProfile /></RequireAuth>} />
          <Route path="/admin" element={<RequireGuest redirectTo="/admin/dashboard" role="admin"><AdminLogin /></RequireGuest>} />
          <Route path="/admin/dashboard" element={<RequireAuth role="admin"><AdminDashboard /></RequireAuth>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
