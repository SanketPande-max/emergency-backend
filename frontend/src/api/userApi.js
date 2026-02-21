import api from './client';

export const getMe = () => api.get('/user/me');
export const sendOtp = (phone) => api.post('/user/send-otp', { phone });
export const verifyOtp = (phone, otp) => api.post('/user/verify-otp', { phone, otp });
export const updateProfile = (data) => api.post('/user/update-profile', data);
export const updateLocation = (lat, lng) => api.post('/user/update-location', { lat, lng });
export const requestEmergency = (lat, lng) => api.post('/user/request-emergency', { lat, lng });
export const getMyRequest = () => api.get('/user/my-request');
