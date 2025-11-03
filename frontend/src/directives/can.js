import { useAuthStore } from '@/stores/auth'

/**
 * v-can 权限指令
 * 用法：
 * v-can="'tasks:create'" - 检查是否有创建任务权限
 * v-can:scope="'tasks:view'" - 检查是否有查看任务权限
 * v-can:task="task" - 检查对特定任务的权限
 */
export const canDirective = {
  mounted(el, binding) {
    const authStore = useAuthStore()
    
    // 如果没有权限，隐藏元素
    if (!checkPermission(authStore, binding)) {
      el.style.display = 'none'
      el.setAttribute('data-v-can-hidden', 'true')
    }
  },
  
  updated(el, binding) {
    const authStore = useAuthStore()
    const hasPermission = checkPermission(authStore, binding)
    
    if (hasPermission) {
      if (el.getAttribute('data-v-can-hidden')) {
        el.style.display = ''
        el.removeAttribute('data-v-can-hidden')
      }
    } else {
      el.style.display = 'none'
      el.setAttribute('data-v-can-hidden', 'true')
    }
  }
}

function checkPermission(authStore, binding) {
  const { value, arg, modifiers } = binding
  
  if (!authStore.isAuthenticated) {
    return false
  }
  
  // 基础权限检查
  if (typeof value === 'string') {
    return authStore.can(value)
  }
  
  // 任务特定权限检查
  if (arg === 'task' && value) {
    const task = value
    const action = Object.keys(modifiers)[0] || 'view'
    
    switch (action) {
      case 'edit':
        return canEditTask(authStore, task)
      case 'delete':
        return canDeleteTask(authStore, task)
      case 'complete':
        return canCompleteTask(authStore, task)
      case 'participate':
        return canCompleteTask(authStore, task)
      case 'view':
        return canViewTask(authStore, task)
      default:
        return false
    }
  }
  
  // 日报特定权限检查
  if (arg === 'report' && value) {
    const report = value
    const action = Object.keys(modifiers)[0] || 'view'
    
    switch (action) {
      case 'edit':
        return canEditReport(authStore, report)
      case 'delete':
        return canDeleteReport(authStore, report)
      case 'view':
        return canViewReport(authStore, report)
      default:
        return false
    }
  }
  
  return false
}

// 任务权限检查函数
function canEditTask(authStore, task) {
  if (authStore.isSuperAdmin || authStore.isAdmin) {
    return true
  }
  return task.created_by === authStore.user?.id
}

function canDeleteTask(authStore, task) {
  if (authStore.isSuperAdmin || authStore.isAdmin) {
    return true
  }
  return task.created_by === authStore.user?.id
}

function canCompleteTask(authStore, task) {
  if (task.status === 'completed') {
    return false
  }
  
  const currentUserId = authStore.user?.id
  
  // 如果任务分配给所有人
  if (task.assignment_type === 'all') {
    return true
  }
  
  // 如果任务分配给特定用户
  if (task.assignment_type === 'user' && task.assigned_to === currentUserId) {
    return true
  }
  
  // 如果任务分配给特定身份
  if (task.assignment_type === 'identity' && task.target_identity === authStore.user?.identity_type) {
    return true
  }
  
  // 如果任务分配给用户组
  if (task.assignment_type === 'group' && task.target_group_id) {
    return authStore.user?.group_id === task.target_group_id
  }
  
  return false
}

function canViewTask(authStore, task) {
  // 管理员可以查看所有任务
  if (authStore.isSuperAdmin || authStore.isAdmin) {
    return true
  }
  
  // 任务创建者可以查看
  if (task.created_by === authStore.user?.id) {
    return true
  }
  
  // 任务分配对象可以查看
  return canCompleteTask(authStore, task)
}

// 日报权限检查函数
function canEditReport(authStore, report) {
  if (authStore.isSuperAdmin || authStore.isAdmin) {
    return true
  }
  return report.user_id === authStore.user?.id
}

function canDeleteReport(authStore, report) {
  if (authStore.isSuperAdmin || authStore.isAdmin) {
    return true
  }
  return report.user_id === authStore.user?.id
}

function canViewReport(authStore, report) {
  // 管理员可以查看所有日报
  if (authStore.isSuperAdmin || authStore.isAdmin) {
    return true
  }
  
  // 作者可以查看自己的日报
  if (report.user_id === authStore.user?.id) {
    return true
  }
  
  // 同组成员可以查看
  if (authStore.user?.group_id && report.user_group_id === authStore.user.group_id) {
    return true
  }
  
  return false
}