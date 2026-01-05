import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const instance = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
instance.interceptors.request.use(
  config => {
    // 可以在这里添加 token 等
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
instance.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default {
  // 状态管理
  getState: (date) => instance.get(`/state/${date}`),
  saveState: (data) => instance.post('/state', data),
  
  // 学习记录
  saveDailyRecord: (data) => instance.post('/records', data),
  getHistory: (days = 30) => instance.get(`/records?days=${days}`),
  getRecordByDate: (date) => instance.get(`/records/${date}`),
  
  // 统计分析
  getWeeklyStats: () => instance.get('/stats/weekly'),
  getSubjectAnalysis: (subject) => instance.get(`/stats/subject/${subject}`),
  getPatternAnalysis: () => instance.get('/stats/pattern'),
  
  // AI 助手
  chat: (message) => instance.post('/chat', { message }),
  generatePlan: (params) => instance.post('/plan/generate', params),
  
  // 同步
  syncToGithub: () => instance.post('/sync/github'),
  getSyncStatus: () => instance.get('/sync/status')
}

