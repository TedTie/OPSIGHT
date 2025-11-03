// 权限相关工具函数

/**
 * 检查用户是否有指定权限
 * @param {Object} user - 用户对象
 * @param {string} permission - 权限类型 ('admin', 'super_admin')
 * @returns {boolean}
 */
export const hasPermission = (user, permission) => {
  if (!user) return false
  
  switch (permission) {
    case 'admin':
      return user.is_admin || user.is_super_admin
    case 'super_admin':
      return user.is_super_admin
    default:
      return true
  }
}

/**
 * 检查用户是否可以访问指定用户的数据
 * @param {Object} currentUser - 当前用户
 * @param {number} targetUserId - 目标用户ID
 * @returns {boolean}
 */
export const canAccessUser = (currentUser, targetUserId) => {
  if (!currentUser) return false
  
  // 超级管理员可以访问所有用户
  if (currentUser.is_super_admin) return true
  
  // 管理员可以访问同组用户
  if (currentUser.is_admin) {
    // 这里需要根据实际业务逻辑判断是否同组
    return true
  }
  
  // 普通用户只能访问自己的数据
  return currentUser.id === targetUserId
}

/**
 * 检查用户是否可以管理指定组
 * @param {Object} currentUser - 当前用户
 * @param {number} groupId - 组ID
 * @returns {boolean}
 */
export const canManageGroup = (currentUser, groupId) => {
  if (!currentUser) return false
  
  // 超级管理员可以管理所有组
  if (currentUser.is_super_admin) return true
  
  // 管理员可以管理自己的组
  if (currentUser.is_admin && currentUser.group_id === groupId) {
    return true
  }
  
  return false
}

/**
 * 格式化用户角色显示
 * @param {Object|string} userOrRole - 用户对象或角色字符串
 * @returns {string}
 */
export const formatUserRole = (userOrRole) => {
  if (!userOrRole) return '未知'
  
  // 如果传入的是字符串，直接处理
  const role = typeof userOrRole === 'string' ? userOrRole : userOrRole.role
  
  // 兼容旧的属性检查
  if (typeof userOrRole === 'object') {
    if (userOrRole.is_super_admin || role === 'super_admin') return '超级管理员'
    if (userOrRole.is_admin || role === 'admin') return '管理员'
  }
  
  // 直接根据role字段判断
  if (role === 'super_admin') return '超级管理员'
  if (role === 'admin') return '管理员'
  return '普通用户'
}

/**
 * 获取用户角色颜色
 * @param {Object|string} userOrRole - 用户对象或角色字符串
 * @returns {string}
 */
export const getUserRoleColor = (userOrRole) => {
  if (!userOrRole) return ''
  
  // 如果传入的是字符串，直接处理
  const role = typeof userOrRole === 'string' ? userOrRole : userOrRole.role
  
  // 兼容旧的属性检查
  if (typeof userOrRole === 'object') {
    if (userOrRole.is_super_admin || role === 'super_admin') return 'danger'
    if (userOrRole.is_admin || role === 'admin') return 'warning'
  }
  
  // 直接根据role字段判断
  if (role === 'super_admin') return 'danger'
  if (role === 'admin') return 'warning'
  return 'primary'
}