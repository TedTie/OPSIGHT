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

.login-header h1 {
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 12px 0;
  
  /* 渐变文字 */
  background: var(--gradient-emerald);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  
  /* 呼吸动画 */
  animation: breathe 4s ease-in-out infinite;
  letter-spacing: -0.5px;
}

@keyframes breathe {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.9;
    transform: scale(1.02);
  }
}

.login-header p {
  color: var(--text-muted);
  font-size: 15px;
  margin: 0;
  font-weight: 500;
}

.login-form {
  text-align: left;
}

/* 增强表单项 */
:deep(.el-form-item) {
  margin-bottom: 24px;
}

.custom-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
  padding: 4px 12px;
}

.custom-input :deep(.el-input__wrapper:hover) {
  border-color: var(--border-color-hover);
  background: #ffffff;
}

/* 聚焦时的绿色发光 */
.custom-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-glow);
  background: #ffffff;
}

:deep(.el-input__inner) {
  color: var(--text-normal);
  font-weight: 500;
}

:deep(.el-input__inner::placeholder) {
  color: var(--text-disabled);
}

/* Checkbox样式 */
:deep(.el-checkbox__label) {
  color: var(--text-muted);
  font-size: 14px;
}

.login-button {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.5px;
  
  background: var(--gradient-primary);
  border: none;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.35);
}

.login-button:active {
  transform: translateY(0);
}

.login-footer {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.login-footer p {
  color: var(--text-muted);
  font-size: 13px;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-card {
    padding: 36px 28px;
  }
  
  .login-header h1 {
    font-size: 30px;
  }
  
  .login-button {
    height: 46px;
    font-size: 15px;
  }
}
</style>