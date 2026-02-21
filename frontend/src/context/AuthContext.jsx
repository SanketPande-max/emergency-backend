import { createContext, useContext, useState, useEffect } from 'react';
import { sensorService } from '../services/sensorService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(localStorage.getItem('role'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token && role) {
      setUser({
        token,
        role,
        user_id: localStorage.getItem('user_id'),
        ambulance_id: localStorage.getItem('ambulance_id'),
      });
    }
    setLoading(false);
  }, [role]);

  const loginUser = (data) => {
    localStorage.setItem('token', data.token);
    localStorage.setItem('role', 'user');
    localStorage.setItem('user_id', data.user_id);
    setRole('user');
    setUser({ ...data, role: 'user' });
  };

  const loginAmbulance = (data) => {
    localStorage.setItem('token', data.token);
    localStorage.setItem('role', 'ambulance');
    localStorage.setItem('ambulance_id', data.ambulance_id);
    setRole('ambulance');
    setUser({ ...data, role: 'ambulance' });
  };

  const loginAdmin = (data) => {
    localStorage.setItem('token', data.token);
    localStorage.setItem('role', 'admin');
    setRole('admin');
    setUser({ token: data.token, role: 'admin' });
  };

  const logout = () => {
    try { sensorService.stop(); } catch { /* ignore */ }
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('user_id');
    localStorage.removeItem('ambulance_id');
    setUser(null);
    setRole(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        loading,
        isAuthenticated: !!user,
        loginUser,
        loginAmbulance,
        loginAdmin,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
