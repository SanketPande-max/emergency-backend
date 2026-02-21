import api from './client';

export const submitSensorReading = (data) => api.post('/sensor/submit', data);
export const submitSensorBatch = (readings) => api.post('/sensor/submit-batch', { readings });
export const getAlertStatus = () => api.get('/sensor/status');
