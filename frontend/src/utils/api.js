import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1', // 使用代理路径
  timeout: 10000, // 减少超时时间
  withCredentials: true, // 支持cookie
  headers: {
    'Content-Type': 'application/json'
  }
})

// 添加调试日志
console.log('🔧 Axios配置:', {
  baseURL: api.defaults.baseURL,
  timeout: api.defaults.timeout,
  withCredentials: api.defaults.withCredentials
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加请求日志
    console.log('📤 发送请求:', {
      method: config.method?.toUpperCase(),
      url: config.url,
      baseURL: config.baseURL,
      fullURL: `${config.baseURL}${config.url}`,
      data: config.data
    })
    // 简化版不需要token，使用cookie认证
    return config
  },
  (error) => {
    console.error('📤 请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Error:', error)
    const { response } = error
    
    if (response) {
      switch (response.status) {
        case 401:
          // 未授权，清除token并跳转到登录页
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          router.push('/login')
          ElMessage.error('登录已过期，请重新登录')
          break
        case 403:
          ElMessage.error('权限不足')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 422:
          // 验证错误
          const detail = response.data?.detail
          if (Array.isArray(detail)) {
            const errors = detail.map(err => err.msg).join(', ')
            ElMessage.error(`验证错误: ${errors}`)
          } else {
            ElMessage.error(detail || '请求参数错误')
          }
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(response.data?.detail || '请求失败')
      }
    } else {
      // 网络错误 - 提供更详细的错误信息
      console.error('Network Error Details:', {
        message: error.message,
        code: error.code,
        config: error.config,
        stack: error.stack
      })
      
      if (error.code === 'ECONNREFUSED' || error.message.includes('ECONNREFUSED')) {
        ElMessage.error('无法连接到服务器，请确认后端服务是否启动')
      } else if (error.code === 'NETWORK_ERROR' || error.message.includes('Network Error')) {
        ElMessage.error('网络错误，请检查网络连接和CORS配置')
      } else if (error.message.includes('timeout')) {
        ElMessage.error('请求超时，请稍后重试')
      } else {
        ElMessage.error(`网络连接失败: ${error.message}`)
      }
    }
    
    return Promise.reject(error)
  }
)

export default api