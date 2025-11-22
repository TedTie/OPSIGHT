<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
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
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 50%, #d1fae5 100%);
}

/* 轻盈装饰 */
.login-container::before {
  content: '';
  position: absolute;
  inset: 0;
  background: 
    radial-gradient(circle at 20% 30%, rgba(16, 185, 129, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(110, 231, 183, 0.06) 0%, transparent 50%);
}

/* 浮动几何装饰 */
.login-container::after {
  content: '';
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  top: -200px;
  right: -200px;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.05) 0%, transparent 70%);
  animation: float 20s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-50px, 50px) scale(1.1); }
}

.login-card {
  width: 100%;
  max-width: 420px;
  position: relative;
  z-index: 1;
  
  /* 明亮卡片 */
  background: #ffffff;
  border-radius: var(--radius-2xl);
  border: 1px solid rgba(16, 185, 129, 0.15);
  box-shadow: 
    0 20px 60px rgba(15, 23, 42, 0.12),
    0 0 0 1px rgba(16, 185, 129, 0.1);
  
  padding: 48px 40px;
  text-align: center;
  
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.login-card:hover {
  border-color: rgba(16, 185, 129, 0.3);
  box-shadow: 
    0 24px 70px rgba(15, 23, 42, 0.15),
    0 0 0 1px rgba(16, 185, 129, 0.2);
  transform: translateY(-4px);
}

.login-header {
  margin-bottom: 40px;
  position: relative;
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

:deep(.el-input__wrapper) {
  background: var(--surface);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: var(--border-color-hover);
}

/* 聚焦时的绿色发光 */
:deep(.el-input__wrapper.is-focus) {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-glow);
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