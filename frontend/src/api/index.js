import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',  // 使用相对路径，便于部署
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 从localStorage获取用户信息
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    
    // 如果用户已登录，自动为请求添加user_id
    if (user && user.id) {
      // 对于GET请求，添加到URL参数
      if (config.method === 'get') {
        config.params = { ...config.params, user_id: user.id }
      } 
      // 对于非GET请求，且非form-data的情况，添加到请求体
      else if (!config.headers['Content-Type'] || !config.headers['Content-Type'].includes('multipart/form-data')) {
        config.data = { ...config.data, user_id: user.id }
      }
    }
    
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      // 未授权，可能是登录过期
      if (error.response.status === 401) {
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
      
      // 服务器返回了错误信息
      if (error.response.data && error.response.data.error) {
        console.error('API Error:', error.response.data.error)
      }
    } else {
      console.error('Network Error:', error.message)
    }
    
    return Promise.reject(error)
  }
)

export default api 