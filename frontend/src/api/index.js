import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 统一错误处理
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '请求失败'
    console.error('[API Error]', msg)
    return Promise.reject(err)
  }
)

// ===== 老人信息 =====
export const patientApi = {
  list: (params) => api.get('/patients', { params }),
  count: () => api.get('/patients/count'),
  update: (id, data) => api.put(`/patients/${id}`, data),
  delete: (id) => api.delete(`/patients/${id}`),
  import: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/patients/import', form)
  },
}

// ===== 拨打任务 =====
export const taskApi = {
  create: (data) => api.post('/tasks/create', data),
  listBatches: () => api.get('/tasks/batches'),
  getBatchDetail: (batchId) => api.get(`/tasks/batch/${batchId}`),
  getBatchStats: (batchId) => api.get(`/tasks/batch/${batchId}/stats`),
  start: (batchId) => api.post(`/tasks/batch/${batchId}/start`),
  pause: (batchId) => api.post(`/tasks/batch/${batchId}/pause`),
  resume: (batchId) => api.post(`/tasks/batch/${batchId}/resume`),
  pendingTransfers: () => api.get('/tasks/pending-transfers'),
}

// ===== 预约管理 =====
export const appointmentApi = {
  list: (params) => api.get('/appointments', { params }),
  create: (data) => api.post('/appointments', data),
  update: (id, data) => api.put(`/appointments/${id}`, data),
  delete: (id) => api.delete(`/appointments/${id}`),
  getByDate: (date) => api.get(`/appointments/date/${date}`),
}

// ===== 统计报表 =====
export const statsApi = {
  overview: () => api.get('/stats/overview'),
  batch: (batchId) => api.get(`/stats/batch/${batchId}`),
  exportUrl: (batchId) => `/api/stats/export/${batchId}`,
}
