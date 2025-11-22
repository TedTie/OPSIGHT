<template>
  <el-aside
    :width="collapsed ? '64px' : '240px'"
    class="app-sidebar"
    ref="asideRef"
  >
    <div class="sidebar-container glass-panel">
      <!-- Logo Area -->
      <div class="sidebar-logo">
        <img src="@/assets/logo.svg" alt="OPSIGHT" class="sidebar-logo-img" />
        <span v-if="!collapsed" class="logo-text">OPSIGHT</span>
      </div>

      <!-- Menu -->
      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        :unique-opened="true"
        class="sidebar-menu"
        router
      >
        <!-- Dashboard -->
        <el-menu-item index="/dashboard">
          <el-icon><i-tabler-layout-dashboard /></el-icon>
          <template #title>仪表板</template>
        </el-menu-item>
        
        <!-- Tasks -->
        <el-menu-item index="/tasks">
          <el-icon><i-tabler-checklist /></el-icon>
          <template #title>任务管理</template>
        </el-menu-item>
        
        <!-- Reports -->
        <el-menu-item index="/reports">
          <el-icon><i-tabler-file-text /></el-icon>
          <template #title>日报管理</template>
        </el-menu-item>
        
        <!-- Analytics -->
        <el-menu-item index="/analytics">
          <el-icon><i-tabler-chart-line /></el-icon>
          <template #title>数据分析</template>
        </el-menu-item>
        
        <!-- Knowledge Base -->
        <el-menu-item v-if="isAdmin" index="/knowledge-base">
          <el-icon><i-tabler-book-2 /></el-icon>
          <template #title>知识库</template>
        </el-menu-item>
        
        <!-- Settings -->
        <el-menu-item v-if="isSuperAdmin" index="/settings">
          <el-icon><i-tabler-settings /></el-icon>
          <template #title>设置</template>
        </el-menu-item>
        
        <!-- Admin -->
        <el-sub-menu v-if="isAdmin" index="admin-menu">
          <template #title>
            <el-icon><i-tabler-tools /></el-icon>
            <span>管理功能</span>
          </template>
          
          <el-menu-item v-if="isSuperAdmin" index="/admin/users">
            <el-icon><i-tabler-users /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
          
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
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})

const activeMenu = computed(() => route.path)

const isSuperAdmin = computed(() => {
  return authStore.user?.role === 'super_admin'
})

const isAdmin = computed(() => {
  return authStore.user?.role === 'admin' || authStore.user?.role === 'super_admin'
})
</script>

<style scoped>
.app-sidebar {
  background: transparent;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 16px 0 16px 16px;
  height: 100vh;
  overflow: visible;
}

.sidebar-container {
  height: 100%;
  border-radius: var(--radius-xl);
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--glass-border);
}

.sidebar-logo {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
}

.sidebar-logo-img {
  width: 36px;
  height: 36px;
  object-fit: contain;
  flex-shrink: 0;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-strong);
  letter-spacing: -0.5px;
}

.sidebar-menu {
  flex: 1;
  border: none;
  background: transparent;
  padding: 12px;
  overflow-y: auto;
}

/* Menu Items (Crextio Style) */
:deep(.el-menu-item) {
  height: 48px;
  line-height: 48px;
  margin: 4px 0;
  border-radius: var(--radius-md);
  color: var(--text-muted);
  font-weight: 500;
  transition: all 0.2s ease;
}

:deep(.el-menu-item:hover) {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

:deep(.el-menu-item.is-active) {
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: 600;
}

/* Icons */
:deep(.el-icon) {
  font-size: 20px;
  margin-right: 12px;
  transition: all 0.2s ease;
}

:deep(.el-menu-item.is-active .el-icon) {
  color: var(--color-primary);
}

/* Submenu */
:deep(.el-sub-menu__title) {
  height: 48px;
  line-height: 48px;
  margin: 4px 0;
  border-radius: var(--radius-md);
  color: var(--text-muted);
  font-weight: 500;
}

:deep(.el-sub-menu__title:hover) {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

/* Collapsed State - Let Element Plus handle it naturally */
:deep(.el-menu--collapse) {
  width: 100%;
}

/* Center the menu items */
:deep(.el-menu--collapse .el-menu-item) {
  padding: 0 !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
}

:deep(.el-menu--collapse .el-sub-menu > .el-sub-menu__title) {
  padding: 0 !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
}

/* Ensure icons are visible and properly sized */
:deep(.el-menu--collapse .el-icon) {
  margin: 0 !important;
  font-size: 22px !important;
}

/* Hide submenu arrow in collapsed state */
:deep(.el-menu--collapse .el-sub-menu__icon-arrow) {
  display: none !important;
}

/* Hide logo text when collapsed */
.logo-text {
  transition: opacity 0.2s;
}

:deep(.el-menu--collapse) ~ .sidebar-logo .logo-text {
  display: none !important;
}
</style>