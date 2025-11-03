<template>
  <el-aside :width="collapsed ? '64px' : '240px'" class="app-sidebar">
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
          <el-icon><Odometer /></el-icon>
          <template #title>仪表板</template>
        </el-menu-item>
        
        <!-- 任务管理 -->
        <el-menu-item index="/tasks">
          <el-icon><List /></el-icon>
          <template #title>任务管理</template>
        </el-menu-item>
        
        <!-- 日报管理 -->
        <el-menu-item index="/reports">
          <el-icon><Document /></el-icon>
          <template #title>日报管理</template>
        </el-menu-item>
        
        <!-- 数据分析 - 所有用户都可以访问，但看到的数据范围不同 -->
        <el-menu-item index="/analytics">
          <el-icon><TrendCharts /></el-icon>
          <template #title>数据分析</template>
        </el-menu-item>
        
        <!-- 知识库 - 所有用户都可以访问 -->
        <el-menu-item index="/knowledge-base">
          <el-icon><Collection /></el-icon>
          <template #title>知识库</template>
        </el-menu-item>
        
        <!-- 设置 -->
        <el-menu-item v-if="isSuperAdmin" index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>设置</template>
        </el-menu-item>
        
        <!-- 管理员功能 -->
        <el-sub-menu v-if="isAdmin" index="admin-menu">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>管理功能</span>
          </template>
          
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
          
          <el-menu-item index="/admin/groups">
            <el-icon><UserFilled /></el-icon>
            <template #title>组别管理</template>
          </el-menu-item>
          
          <el-menu-item v-if="isSuperAdmin" index="/admin/ai">
            <el-icon><Cpu /></el-icon>
            <template #title>AI配置</template>
          </el-menu-item>
          
          <el-menu-item v-if="isSuperAdmin" index="/admin/metrics">
            <el-icon><DataAnalysis /></el-icon>
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
import {
  Odometer,
  List,
  Document,
  TrendCharts,
  Setting,
  User,
  UserFilled,
  Cpu,
  DataAnalysis,
  Collection
} from '@element-plus/icons-vue'
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
</script>

<style scoped>
.app-sidebar {
  background: #304156;
  transition: width 0.3s;
  overflow: hidden;
}

.sidebar-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.sidebar-menu {
  flex: 1;
  border: none;
  background: transparent;
}

:deep(.el-menu-item) {
  color: #bfcbd9;
  background: transparent !important;
  border: none !important;
}

:deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  color: #fff;
}

:deep(.el-menu-item.is-active) {
  background: #409eff !important;
  color: #fff;
}

:deep(.el-sub-menu__title) {
  color: #bfcbd9;
  background: transparent !important;
  border: none !important;
}

:deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  color: #fff;
}

:deep(.el-sub-menu .el-menu-item) {
  background: rgba(0, 0, 0, 0.1) !important;
  min-height: 40px;
}

:deep(.el-sub-menu .el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
}

:deep(.el-sub-menu .el-menu-item.is-active) {
  background: #409eff !important;
}

/* 折叠状态样式 */
:deep(.el-menu--collapse) {
  width: 64px;
}

:deep(.el-menu--collapse .el-menu-item) {
  text-align: center;
  padding: 0 20px;
}

:deep(.el-menu--collapse .el-sub-menu) {
  text-align: center;
}

:deep(.el-menu--collapse .el-sub-menu__title) {
  padding: 0 20px;
}

/* 图标样式 */
:deep(.el-icon) {
  width: 20px;
  height: 20px;
  margin-right: 8px;
}

:deep(.el-menu--collapse .el-icon) {
  margin-right: 0;
}
</style>