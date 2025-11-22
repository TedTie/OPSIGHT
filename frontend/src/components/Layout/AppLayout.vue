<template>
  <el-container class="app-layout">
    <!-- Sidebar (Floating) -->
    <AppSidebar :collapsed="sidebarCollapsed" />
    
    <!-- Main Content -->
    <el-container class="main-container">
      <!-- Header (Transparent) -->
      <AppHeader @toggle-sidebar="toggleSidebar" />
      
      <!-- Content Area -->
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'

const sidebarCollapsed = ref(false)

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<style scoped>
.app-layout {
  height: 100vh;
  overflow: hidden;
  background: transparent;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.app-main {
  flex: 1;
  padding: 0 16px 16px 16px;
  overflow-y: auto;
  overflow-x: hidden;
}

/* Scrollbar styling for main content */
.app-main::-webkit-scrollbar {
  width: 8px;
}

.app-main::-webkit-scrollbar-track {
  background: transparent;
}

.app-main::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
}

.app-main::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.2);
}

/* Responsive */
@media (max-width: 768px) {
  .app-main {
    padding: 16px;
  }
}
</style>