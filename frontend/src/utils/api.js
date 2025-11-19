import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const useCreds = String(import.meta.env.VITE_USE_CREDENTIALS || '').toLowerCase() === 'true'
const api = axios.create({
  baseURL: baseURL,
  timeout: 10000,
  withCredentials: useCreds,
  headers: {
    'Content-Type': 'application/json'
  }
})

const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''
if (supabaseAnonKey) {
  api.defaults.headers.common['Authorization'] = `Bearer ${supabaseAnonKey}`
  api.defaults.headers.common['apikey'] = supabaseAnonKey
}
if (!supabaseAnonKey && import.meta && import.meta.env && import.meta.env.PROD) {
  ElMessage.warning('后端鉴权未配置，无法获取真实数据，请在 Vercel 设置 VITE_SUPABASE_ANON_KEY 并重新部署')
}

// 添加调试日志
console.log('🔧 Axios配置:', {
  baseURL: api.defaults.baseURL,
  timeout: api.defaults.timeout,
  withCredentials: api.defaults.withCredentials,
  hasAuthHeader: !!api.defaults.headers.common['Authorization'],
  hasApiKeyHeader: !!api.defaults.headers.common['apikey']
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
    const { response, config } = error
    const suppress = !!(config && (config.suppressErrorMessage || config.suppressError))
    
    if (response) {
      switch (response.status) {
        case 401:
          // 未授权：区分登录失败与会话过期
          {
            const reqUrl = (config && config.url) ? String(config.url) : ''
            const isLoginAttempt = reqUrl.includes('/auth/login')

            // 登录接口返回401时，不做全局重定向，直接提示后端详情
            if (isLoginAttempt) {
              const detail = response.data?.detail
              if (!suppress) ElMessage.error(detail || '用户名不存在或账户已被禁用')
              // 不清除现有登录态（可能是切换账号失败的场景）
              break
            }

            // /auth/me 或显式 suppress：不触发全局登出与重定向
            if (reqUrl.includes('/auth/me') || suppress) {
              break
            }

            // 其他接口401：视为会话过期，清除并回到登录页
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            router.push('/login')
            ElMessage.error('登录已过期，请重新登录')
          }
          break
        case 403:
          if (!suppress) ElMessage.error('权限不足')
          break
        case 404:
          if (!suppress) ElMessage.error('请求的资源不存在')
          break
        case 422:
          // 验证错误
          const detail = response.data?.detail
          if (Array.isArray(detail)) {
            const errors = detail.map(err => err.msg).join(', ')
            if (!suppress) ElMessage.error(`验证错误: ${errors}`)
          } else {
            if (!suppress) ElMessage.error(detail || '请求参数错误')
          }
          break
        case 500:
          {
            const serverDetail = response.data?.detail || response.data?.message || response.data?.error
            const reqUrl = (config && config.url) ? String(config.url) : ''
            const showText = serverDetail ? `服务器内部错误：${serverDetail}` : '服务器内部错误'
            if (!suppress) ElMessage.error(showText)
            // 输出更详细的上下文，便于定位后端异常源
            console.error('[API] 500 Internal Server Error', {
              url: reqUrl,
              method: config?.method,
              status: response.status,
              data: response.data
            })
          }
          break
        default:
          if (!suppress) ElMessage.error(response.data?.detail || '请求失败')
      }
    } else {
      // 网络错误 - 提供更详细的错误信息
      console.error('Network Error Details:', {
        message: error.message,
        code: error.code,
        config: error.config,
        stack: error.stack
      })
      
      if (!suppress) {
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
    }

    return Promise.reject(error)
  }
)

export default api