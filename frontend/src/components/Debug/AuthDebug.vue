<template>
  <div class="auth-debug">
    <h3>🔍 认证状态调试</h3>
    
    <div class="debug-section">
      <h4>用户信息</h4>
      <pre>{{ JSON.stringify(authStore.user, null, 2) }}</pre>
    </div>
    
    <div class="debug-section">
      <h4>认证状态</h4>
      <ul>
        <li>isAuthenticated: {{ authStore.isAuthenticated }}</li>
        <li>isAdmin: {{ authStore.isAdmin }}</li>
        <li>isSuperAdmin: {{ authStore.isSuperAdmin }}</li>
        <li>isUser: {{ authStore.isUser }}</li>
      </ul>
    </div>
    
    <div class="debug-section">
      <h4>LocalStorage</h4>
      <ul>
        <li>user: {{ localStorageUser }}</li>
        <li>token: {{ localStorageToken }}</li>
      </ul>
    </div>
    
    <div class="debug-section">
      <h4>菜单显示逻辑</h4>
      <ul>
        <li>设置菜单应该显示: {{ authStore.isSuperAdmin }}</li>
        <li>管理功能菜单应该显示: {{ authStore.isAdmin }}</li>
        <li>AI配置菜单应该显示: {{ authStore.isSuperAdmin }}</li>
      </ul>
    </div>
    
    <div class="debug-section">
      <h4>操作</h4>
      <el-button @click="refreshAuth">刷新认证状态</el-button>
      <el-button @click="clearAuth">清除认证</el-button>
      <el-button @click="testLogin">测试登录</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElButton, ElMessage } from 'element-plus'

const authStore = useAuthStore()

const localStorageUser = ref('')
const localStorageToken = ref('')

const updateLocalStorageInfo = () => {
  localStorageUser.value = localStorage.getItem('user') || 'null'
  localStorageToken.value = localStorage.getItem('token') || 'null'
}

const refreshAuth = () => {
  authStore.initAuth()
  updateLocalStorageInfo()
  ElMessage.success('认证状态已刷新')
}

const clearAuth = () => {
  authStore.logout()
  updateLocalStorageInfo()
}

const testLogin = async () => {
  const success = await authStore.login({
    username: 'admin',
    password: 'admin123'
  })
  
  if (success) {
    updateLocalStorageInfo()
  }
}

onMounted(() => {
  updateLocalStorageInfo()
})
</script>

<style scoped>
.auth-debug {
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
  margin: 20px;
}

.debug-section {
  margin-bottom: 20px;
  padding: 15px;
  background: white;
  border-radius: 4px;
  border-left: 4px solid #409eff;
}

.debug-section h4 {
  margin: 0 0 10px 0;
  color: #409eff;
}

.debug-section ul {
  margin: 0;
  padding-left: 20px;
}

.debug-section li {
  margin: 5px 0;
}

pre {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
}
</style>