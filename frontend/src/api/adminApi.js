import api from './client';

export const login = (username, password) => api.post('/admin/login', { username, password });
export const getAllUsers = () => api.get('/admin/all-users');
export const getAllAmbulances = () => api.get('/admin/all-ambulances');
export const getAllRequests = () => api.get('/admin/all-requests');
export const getDashboardMap = () => api.get('/admin/dashboard-map');
