<template>
  <div class="login-container">
    <div class="login-card glass-panel">
      <div class="login-header">
        <div class="logo-container">
          <img src="@/assets/logo.png" alt="OPSIGHT Logo" class="login-logo" />
        </div>
        <h1>OPSIGHT</h1>
        <p>智能任务与日报管理系统</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            size="large"
            :prefix-icon="User"
            clearable
            class="custom-input"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            placeholder="请输入密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            class="custom-input"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="loginForm.remember_me">记住我（30天）</el-checkbox>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="authStore.loading"
            class="login-button"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p>© 2025 OPSIGHT. All rights reserved.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import User from '~icons/tabler/user'
import Lock from '~icons/tabler/lock'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 表单引用
const loginFormRef = ref()

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: '',
  remember_me: true
})

// 表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度至少 6 位', trigger: 'blur' }
  ]
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    const valid = await loginFormRef.value.validate()
    if (!valid) return
    
    const success = await authStore.login({
      username: loginForm.username,
      password: loginForm.password,
      remember_me: loginForm.remember_me
    })
    
    if (success) {
      // 登录成功，跳转到仪表板
      router.push('/dashboard')
    }
  } catch (error) {
    console.error('Login error:', error)
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
  background-color: #fdfdf9; /* Warm white base */
  background-image: 
    radial-gradient(circle at 10% 20%, rgba(16, 185, 129, 0.08) 0%, transparent 40%),
    radial-gradient(circle at 90% 80%, rgba(252, 211, 77, 0.08) 0%, transparent 40%);
}

/* Floating decorations */
.login-container::before {
  content: '';
  position: absolute;
  top: -100px;
  left: -100px;
  width: 400px;
  height: 400px;
  background: var(--gradient-primary);
  opacity: 0.05;
  border-radius: 50%;
  filter: blur(60px);
  animation: float 15s ease-in-out infinite;
}

.login-container::after {
  content: '';
  position: absolute;
  bottom: -50px;
  right: -50px;
  width: 300px;
  height: 300px;
  background: var(--gradient-nature);
  opacity: 0.05;
  border-radius: 50%;
  filter: blur(50px);
  animation: float 20s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(30px, -30px); }
}

.login-card {
  width: 100%;
  max-width: 440px;
  padding: 48px 40px;
  text-align: center;
  position: relative;
  z-index: 10;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 
    0 20px 40px -10px rgba(16, 185, 129, 0.1),
    0 0 0 1px rgba(16, 185, 129, 0.05);
}

.login-header {
  margin-bottom: 40px;
}

.logo-container {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
  border-radius: 24px;
  box-shadow: 
    0 10px 20px -5px rgba(16, 185, 129, 0.15),
    inset 0 0 0 1px rgba(255, 255, 255, 0.5);
}

.login-logo {
  width: 48px;
  height: 48px;
  object-fit: contain;
}