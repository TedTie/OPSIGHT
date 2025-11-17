import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const loading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!user.value)
  const isAdmin = computed(() => {
    if (!user.value) return false
    return user.value.role === 'admin' || user.value.role === 'super_admin'
  })
  const isSuperAdmin = computed(() => {
    if (!user.value) return false
    return user.value.role === 'super_admin'
  })
  
  // 兼容性计算属性（保持向后兼容）
  const isUser = computed(() => {
    if (!user.value) return false
    return user.value.role === 'user'
  })

  // 登录
  const login = async (credentials) => {
    loading.value = true
    try {
      const response = await api.post('/auth/login', credentials)
      const { user: userData } = response.data
      
      user.value = userData
      
      // 保存到本地存储
      localStorage.setItem('user', JSON.stringify(userData))
      // 设置token标识（用于路由守卫）
      localStorage.setItem('token', 'authenticated')
      
      ElMessage.success('登录成功')
      return true
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '登录失败')
      return false
    } finally {
      loading.value = false
    }
  }

  // 登出
  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // 清除状态
      user.value = null
      
      // 清除本地存储
      localStorage.removeItem('user')
      localStorage.removeItem('token')
      
      ElMessage.success('已退出登录')
    }
  }

  // 获取当前用户信息
  const fetchUserInfo = async () => {
    try {
      // 抑制全局 401 弹窗，改为静默处理
      const response = await api.get('/auth/me', { suppressErrorMessage: true })
      user.value = response.data
      localStorage.setItem('user', JSON.stringify(response.data))
      return response.data
    } catch (error) {
      console.error('Fetch user info error:', error)
      // 401：未登录或会话过期。抑制全局弹窗，但向上抛出让页面按既有逻辑跳转登录。
      if (error?.response?.status === 401) {
        throw error
      }
      throw error
    }
  }

  // 初始化认证状态
  const initAuth = () => {
    // 从localStorage恢复用户状态
    const savedUser = localStorage.getItem('user')
    const savedToken = localStorage.getItem('token')
    
    console.log('initAuth called:', { savedUser, savedToken })
    
    if (savedUser && savedToken) {
      try {
        const userData = JSON.parse(savedUser)
        user.value = userData
        console.log('User restored from localStorage:', userData)
      } catch (error) {
        console.error('Failed to parse saved user:', error)
        localStorage.removeItem('user')
        localStorage.removeItem('token')
      }
    } else {
      console.log('No saved user or token found')
    }
  }

  // 监听localStorage变化
  const handleStorageChange = () => {
    console.log('Storage change detected, reinitializing auth...')
    initAuth()
  }

  // 在浏览器环境中监听storage事件
  if (typeof window !== 'undefined') {
    window.addEventListener('storage', handleStorageChange)
  }

  // 检查权限
  const hasPermission = (permission) => {
    if (!user.value) return false
    
    switch (permission) {
      case 'admin':
        return user.value.role === 'admin' || user.value.role === 'super_admin'
      case 'super_admin':
        return user.value.role === 'super_admin'
      case 'user':
        return user.value.role === 'user'
      default:
        return true
    }
  }
  
  // 根据身份检查权限
  const hasIdentityPermission = (identity) => {
    if (!user.value) return false
    if (user.value.role === 'super_admin') return true
    return user.value.identity_type === identity
  }
  
  // 检查组权限
  const hasGroupPermission = (groupName) => {
    if (!user.value) return false
    if (user.value.role === 'super_admin') return true
    return user.value.group_name === groupName
  }

  // 统一权限检查方法
  const can = (action) => {
    if (!user.value) return false
    
    const permissions = {
      // 任务相关权限
      'tasks:create': isAdmin.value || isSuperAdmin.value,
      'tasks:view:all': isAdmin.value || isSuperAdmin.value,
      'tasks:view:group': isAdmin.value || isSuperAdmin.value,
      'tasks:view:self': true,
      'tasks:assign': isAdmin.value || isSuperAdmin.value,
      'tasks:manage:all': isSuperAdmin.value,
      'tasks:manage:group': isAdmin.value || isSuperAdmin.value,
      
      // 日报相关权限
      'reports:create': true,
      'reports:view:all': isAdmin.value || isSuperAdmin.value,
      'reports:view:group': isAdmin.value || isSuperAdmin.value,
      'reports:view:self': true,
      'reports:manage:all': isSuperAdmin.value,
      'reports:manage:group': isAdmin.value || isSuperAdmin.value,
      
      // 分析相关权限
      'analytics:view:all': isSuperAdmin.value,
      'analytics:view:group': isAdmin.value || isSuperAdmin.value,
      'analytics:view:self': true,
      
      // 用户管理权限
      'users:manage': isSuperAdmin.value,
      'users:view:all': isSuperAdmin.value,
      'users:view:group': isAdmin.value || isSuperAdmin.value
    }
    
    return permissions[action] || false
  }

  // 获取允许的作用域
  const allowedScopes = (action) => {
    if (!user.value) return []
    
    const scopes = []
    
    // 根据权限级别确定可用作用域
    if (isSuperAdmin.value) {
      scopes.push('all', 'group', 'identity', 'user', 'self')
    } else if (isAdmin.value) {
      scopes.push('group', 'identity', 'user', 'self')
    } else {
      scopes.push('self')
    }
    
    // 根据具体操作进一步限制
    if (action.includes('create') || action.includes('assign')) {
      if (!isAdmin.value && !isSuperAdmin.value) {
        return ['self']
      }
    }
    
    return scopes
  }

  // 获取用户默认首页
  const getDefaultHome = () => {
    if (!user.value) return '/login'
    
    if (isSuperAdmin.value) return '/dashboard'
    if (isAdmin.value) return '/dashboard'
    return '/tasks'
  }

  return {
    // 状态
    user,
    loading,
    
    // 计算属性
    isAuthenticated,
    isAdmin,
    isSuperAdmin,
    isUser,
    
    // 方法
    login,
    logout,
    fetchUserInfo,
    initAuth,
    hasPermission,
    hasIdentityPermission,
    hasGroupPermission,
    
    // 新增权限方法
    can,
    allowedScopes,
    getDefaultHome
  }
})