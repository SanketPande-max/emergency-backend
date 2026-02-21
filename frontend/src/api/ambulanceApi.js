import api from './client';

export const getMe = () => api.get('/ambulance/me');
export const sendOtp = (phone) => api.post('/ambulance/send-otp', { phone });
export const verifyOtp = (phone, otp) => api.post('/ambulance/verify-otp', { phone, otp });
export const updateProfile = (data) => api.post('/ambulance/update-profile', data);
export const updateStatus = (status) => api.put('/ambulance/status', { status });
export const updateLocation = (lat, lng) => api.post('/ambulance/update-location', { lat, lng });
export const getMyRequests = () => api.get('/ambulance/my-requests');
export const getAssignedDetails = () => api.get('/ambulance/assigned-details');
export const selectHospital = (requestId, hospital) => api.post('/ambulance/select-hospital', { request_id: requestId, hospital });
export const completeRequest = (requestId, lat, lng) => {
  const body = (lat != null && lng != null) ? { lat, lng } : {};
  return api.put(`/ambulance/complete-request/${requestId}`, body);
};
export const reportFake = (requestId) => api.post(`/ambulance/report-fake/${requestId}`);
