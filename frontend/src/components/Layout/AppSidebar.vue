<template>
  <el-aside
    :width="collapsed ? '64px' : '240px'"
    class="app-sidebar"
    ref="asideRef"
    :style="spotlightStyle"
    @mousemove="onMouseMove"
    @mouseleave="onMouseLeave"
  >
    <div class="sidebar-content">
      <!-- 菜单 -->
      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        :unique-opened="true"
        class="sidebar-menu"
        router
      >
        <!-- 仪表板 -->
        <el-menu-item index="/dashboard">
          <el-icon><i-tabler-layout-dashboard /></el-icon>
          <template #title>仪表板</template>
        </el-menu-item>
        
        <!-- 任务管理 -->
        <el-menu-item index="/tasks">
          <el-icon><i-tabler-checklist /></el-icon>
          <template #title>任务管理</template>
        </el-menu-item>
        
        <!-- 日报管理 -->
        <el-menu-item index="/reports">
          <el-icon><i-tabler-file-text /></el-icon>
          <template #title>日报管理</template>
        </el-menu-item>
        
        <!-- 数据分析 - 所有用户都可以访问，但看到的数据范围不同 -->
        <el-menu-item index="/analytics">
          <el-icon><i-tabler-chart-line /></el-icon>
          <template #title>数据分析</template>
        </el-menu-item>
        
        <!-- 知识库 - 仅管理员及以上可见 -->
        <el-menu-item v-if="isAdmin" index="/knowledge-base">
          <el-icon><i-tabler-book-2 /></el-icon>
          <template #title>知识库</template>
        </el-menu-item>
        
        <!-- 设置 -->
        <el-menu-item v-if="isSuperAdmin" index="/settings">
          <el-icon><i-tabler-settings /></el-icon>
          <template #title>设置</template>
        </el-menu-item>
        
        <!-- 管理功能：管理员可见，但具体项按权限细分 -->
        <el-sub-menu v-if="isAdmin" index="admin-menu">
          <template #title>
            <el-icon><i-tabler-tools /></el-icon>
            <span>管理功能</span>
          </template>
          
          <!-- 用户管理：仅超级管理员可见 -->
          <el-menu-item v-if="isSuperAdmin" index="/admin/users">
            <el-icon><i-tabler-users /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
          
          <!-- 组别管理：管理员及以上可见（页面内再细化权限） -->
          <el-menu-item index="/admin/groups">
            <el-icon><i-tabler-users /></el-icon>
            <template #title>组别管理</template>
          </el-menu-item>
          
          <el-menu-item v-if="isSuperAdmin" index="/admin/ai">
            <el-icon><i-tabler-cpu /></el-icon>
            <template #title>AI配置</template>
          </el-menu-item>
          
          <el-menu-item v-if="isSuperAdmin" index="/admin/metrics">
            <el-icon><i-tabler-chart-dots-2 /></el-icon>
            <template #title>自定义指标</template>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </div>
  </el-aside>
</template>

<script setup>
import { computed, onMounted, watch, ref, watchEffect } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()

// 定义props
const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})

// 当前激活的菜单
const activeMenu = computed(() => {
  return route.path
})

// 创建响应式的用户状态
const userState = ref(null)

// 更新用户状态的函数
const updateUserState = () => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || 'null')
    userState.value = user
    console.log('User state updated:', user)
  } catch (error) {
    console.error('Error parsing user from localStorage:', error)
    userState.value = null
  }
}

// 基于响应式用户状态的权限检查
const isSuperAdmin = computed(() => {
  // 优先使用authStore的状态
  if (authStore.user && authStore.user.role) {
    const result = authStore.user.role === 'super_admin'
    console.log('isSuperAdmin computed (authStore):', { user: authStore.user.username, role: authStore.user.role, isSuperAdmin: result })
    return result
  }
  
  // 备用：使用本地状态
  const user = userState.value
  if (user && user.role) {
    const result = user.role === 'super_admin'
    console.log('isSuperAdmin computed (userState):', { user: user.username, role: user.role, isSuperAdmin: result })
    return result
  }
  
  // 最后备用：直接从localStorage读取
  try {
    const localUser = JSON.parse(localStorage.getItem('user') || 'null')
    const result = localUser && localUser.role === 'super_admin'
    console.log('isSuperAdmin computed (localStorage):', { user: localUser?.username, role: localUser?.role, isSuperAdmin: result })
    return result
  } catch (error) {
    console.error('Error reading from localStorage:', error)
    return false
  }
})

const isAdmin = computed(() => {
  // 优先使用authStore的状态
  if (authStore.user && authStore.user.role) {
    const result = authStore.user.role === 'admin' || authStore.user.role === 'super_admin'
    console.log('isAdmin computed (authStore):', { user: authStore.user.username, role: authStore.user.role, isAdmin: result })
    return result
  }
  
  // 备用：使用本地状态
  const user = userState.value
  if (user && user.role) {
    const result = user.role === 'admin' || user.role === 'super_admin'
    console.log('isAdmin computed (userState):', { user: user.username, role: user.role, isAdmin: result })
    return result
  }
  
  // 最后备用：直接从localStorage读取
  try {
    const localUser = JSON.parse(localStorage.getItem('user') || 'null')
    const result = localUser && (localUser.role === 'admin' || localUser.role === 'super_admin')
    console.log('isAdmin computed (localStorage):', { user: localUser?.username, role: localUser?.role, isAdmin: result })
    return result
  } catch (error) {
    console.error('Error reading from localStorage:', error)
    return false
  }
})

// 组件挂载时初始化
onMounted(() => {
  console.log('AppSidebar mounted')
  
  // 初始化用户状态
  updateUserState()
  
  // 监听localStorage变化
  window.addEventListener('storage', updateUserState)
  
  // 调试authStore状态
  console.log('AuthStore state:', {
    user: authStore.user,
    isAuthenticated: authStore.isAuthenticated,
    isAdmin: authStore.isAdmin,
    isSuperAdmin: authStore.isSuperAdmin
  })
  
  // 如果authStore没有用户信息，尝试重新初始化
  if (!authStore.user) {
    console.log('No user in authStore, calling initAuth...')
    authStore.initAuth()
  }
})

// 监听authStore状态变化，同步更新本地状态
watch(() => authStore.user, (newUser) => {
  console.log('AuthStore user changed:', newUser)
  if (newUser) {
    userState.value = newUser
  } else {
    updateUserState()
  }
}, { immediate: true })

// 监听计算属性变化进行调试
watch(isSuperAdmin, (newValue) => {
  console.log('isSuperAdmin changed:', newValue)
}, { immediate: true })

watch(isAdmin, (newValue) => {
  console.log('isAdmin changed:', newValue)
}, { immediate: true })

// Sidebar spotlight 跟随鼠标的高亮效果
const asideRef = ref(null)
const spotlightStyle = ref({})

const onMouseMove = (e) => {
  try {
    const el = asideRef.value?.$el || asideRef.value || e.currentTarget
    const rect = el.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    spotlightStyle.value = { '--sb-x': `${x}px`, '--sb-y': `${y}px` }
  } catch (_) {
    // 静默失败
  }
}

const onMouseLeave = () => {
  spotlightStyle.value = {}
}
</script>

<style scoped>
.app-sidebar {
  background: #ffffff;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  position: relative;
  border-right: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

/* 顶部渐变装饰 */
.app-sidebar::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--gradient-primary);
  z-index: 1;
}

.sidebar-content {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.sidebar-menu {
  flex: 1;
  border: none;
  background: transparent;
  padding: 12px 8px;
}

/* 菜单项入场动画 */
@keyframes menuItemSlideIn {
  from {
    opacity: 0;
    transform: translateX(-12px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  position: relative;
  margin: 4px 0;
  border-radius: var(--radius-md);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  animation: menuItemSlideIn 0.4s ease both;
  color: var(--text-normal);
  font-weight: 500;
}

/* 级联延迟动画 */
:deep(.sidebar-menu > .el-menu-item:nth-child(1)),
:deep(.sidebar-menu > .el-sub-menu:nth-child(1)) { animation-delay: 30ms; }
:deep(.sidebar-menu > .el-menu-item:nth-child(2)),
:deep(.sidebar-menu > .el-sub-menu:nth-child(2)) { animation-delay: 60ms; }
:deep(.sidebar-menu > .el-menu-item:nth-child(3)),
:deep(.sidebar-menu > .el-sub-menu:nth-child(3)) { animation-delay: 90ms; }
:deep(.sidebar-menu > .el-menu-item:nth-child(4)),
:deep(.sidebar-menu > .el-sub-menu:nth-child(4)) { animation-delay: 120ms; }
:deep(.sidebar-menu > .el-menu-item:nth-child(5)),
:deep(.sidebar-menu > .el-sub-menu:nth-child(5)) { animation-delay: 150ms; }
:deep(.sidebar-menu > .el-menu-item:nth-child(6)),
:deep(.sidebar-menu > .el-sub-menu:nth-child(6)) { animation-delay: 180ms; }
:deep(.sidebar-menu > .el-menu-item:nth-child(7)),
:deep(.sidebar-menu > .el-sub-menu:nth-child(7)) { animation-delay: 210ms; }

:deep(.el-menu-item) {
  background: transparent !important;
  border: 1px solid transparent !important;
}

:deep(.el-menu-item:hover) {
  background: var(--surface-hover) !important;
  border-color: rgba(16, 185, 129, 0.2) !important;
  color: var(--color-primary);
  transform: translateX(4px);
}

/* 活跃菜单项 */
:deep(.el-menu-item.is-active) {
  background: linear-gradient(
    135deg,
    rgba(16, 185, 129, 0.1) 0%,
    rgba(16, 185, 129, 0.05) 100%
  ) !important;
  border-color: rgba(16, 185, 129, 0.3) !important;
  color: var(--color-primary);
  font-weight: 600;
  transform: translateX(4px);
  box-shadow: inset 0 1px 2px rgba(16, 185, 129, 0.1);
}

/* 活跃项左侧渐变指示条 */
:deep(.el-menu-item.is-active)::before {
  content: '';
  position: absolute;
  left: 0;
  top: 6px;
  bottom: 6px;
  width: 4px;
  background: var(--gradient-primary);
  border-radius: 0 4px 4px 0;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
}

/* 活跃项图标发光 */
:deep(.el-menu-item.is-active .el-icon) {
  filter: drop-shadow(0 0 6px rgba(16, 185, 129, 0.6));
}

:deep(.el-sub-menu__title) {
  color: var(--text-normal);
  background: transparent !important;
  border: 1px solid transparent !important;
}

:deep(.el-sub-menu__title:hover) {
  background: rgba(16, 185, 129, 0.1) !important;
  border-color: rgba(16, 185, 129, 0.15) !important;
  color: var(--color-accent-mint);
  transform: translateX(4px);
}

:deep(.el-sub-menu .el-menu-item) {
  background: rgba(0, 0, 0, 0.15) !important;
  min-height: 42px;
  margin: 2px 0;
}

:deep(.el-sub-menu .el-menu-item:hover) {
  background: rgba(16, 185, 129, 0.12) !important;
  transform: translateX(4px);
}

:deep(.el-sub-menu .el-menu-item.is-active) {
  background: linear-gradient(
    135deg,
    rgba(16, 185, 129, 0.2) 0%,
    rgba(16, 185, 129, 0.12) 100%
  ) !important;
  color: var(--color-accent-mint);
}

/* 折叠状态 */
:deep(.el-menu--collapse) {
  width: 64px;
}

:deep(.el-menu--collapse .el-menu-item) {
  text-align: center;
  padding: 0 20px;
  justify-content: center;
}

:deep(.el-menu--collapse .el-sub-menu) {
  text-align: center;
}

:deep(.el-menu--collapse .el-sub-menu__title) {
  padding: 0 20px;
  justify-content: center;
}

/* 图标样式 */
:deep(.el-icon) {
  width: 22px;
  height: 22px;
  margin-right: 10px;
  transition: all 0.3s ease;
}

:deep(.el-menu--collapse .el-icon) {
  margin-right: 0;
}

:deep(.el-menu-item:hover .el-icon),
:deep(.el-sub-menu__title:hover .el-icon) {
  transform: scale(1.1);
  filter: drop-shadow(0 0 4px rgba(16, 185, 129, 0.4));
}
</style>