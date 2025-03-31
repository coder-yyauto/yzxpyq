import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
    baseURL: '/api',  // 使用相对路径
    timeout: 5000,
    headers: {
        'Content-Type': 'application/json'
    }
})

export default api 