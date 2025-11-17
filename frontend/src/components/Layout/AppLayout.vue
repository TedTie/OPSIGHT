<template>
  <el-container class="app-layout">
    <!-- 侧边栏 -->
    <AppSidebar :collapsed="sidebarCollapsed" />
    
    <!-- 主内容区 -->
  <el-container class="main-container">
      <!-- 头部 -->
      <AppHeader @toggle-sidebar="toggleSidebar" />
      
      <!-- 内容区 -->
      <el-main class="app-main bubble-bg" v-click-spark="{ color: 'rgb(153,255,133)' }">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'

// 侧边栏折叠状态
const sidebarCollapsed = ref(true)

// 切换侧边栏
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<style scoped>
.app-layout {
  height: 100vh;
  overflow: hidden;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.app-main {
  flex: 1;
  padding: 20px;
  background: var(--bg-page);
  overflow-y: auto;
}

/* 保持 bubble-bg 样式控制层级 */

/* 响应式设计 */
@media (max-width: 768px) {
  .app-main {
    padding: 16px;
  }
}
</style>