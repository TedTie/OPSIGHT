<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">个人资料</h1>
      <p class="page-description">查看和管理您的个人信息</p>
    </div>

    <!-- 用户信息概览 -->
    <el-card class="content-card user-overview">
      <div class="user-info-header">
        <div class="user-avatar-section">
          <el-avatar :size="80" class="user-avatar">
            {{ userInitials }}
          </el-avatar>
          <div class="user-basic-info">
            <h2>{{ authStore.user?.full_name || authStore.user?.username }}</h2>
            <div class="user-meta">
              <el-tag :type="getRoleTagType(authStore.user)" size="large">
                {{ formatUserRole(authStore.user) }}
              </el-tag>
              <span class="user-identity">{{ formatUserIdentity(authStore.user?.identity_type) }}</span>
            </div>
          </div>
        </div>
        <div class="user-status">
          <el-tag :type="authStore.user?.is_active ? 'success' : 'danger'" size="large">
            {{ authStore.user?.is_active ? '活跃' : '停用' }}
          </el-tag>
        </div>
      </div>
    </el-card>

    <!-- 详细信息 -->
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>基本信息</span>
          <el-button 
            v-if="canEdit" 
            type="primary" 
            size="small" 
            @click="toggleEdit"
          >
            {{ isEditing ? '取消编辑' : '编辑信息' }}
          </el-button>
        </div>
      </template>

      <el-form
        ref="profileFormRef"
        :model="userForm"
        :rules="rules"
        label-width="120px"
        :disabled="!isEditing"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用户名">
              <el-input v-model="userForm.username" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="userForm.email" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名" prop="full_name">
              <el-input v-model="userForm.full_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="角色">
              <el-input :value="formatUserRole(authStore.user)" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="身份">
              <el-input :value="formatUserIdentity(authStore.user?.identity_type)" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属组别">
              <el-input :value="authStore.user?.group_name || '未分配'" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="创建时间">
              <el-input :value="formatDate(authStore.user?.created_at)" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最后更新">
              <el-input :value="formatDate(authStore.user?.updated_at)" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item v-if="isEditing">
          <el-button type="primary" @click="saveProfile" :loading="saving">
            保存修改
          </el-button>
          <el-button @click="cancelEdit">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计信息 -->
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>个人统计</span>
        </div>
      </template>

      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ userStats.totalTasks }}</div>
            <div class="stat-label">总任务数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ userStats.completedTasks }}</div>
            <div class="stat-label">已完成任务</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ userStats.totalReports }}</div>
            <div class="stat-label">日报总数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ userStats.avgMood || 'N/A' }}</div>
            <div class="stat-label">平均情绪值</div>
          </div>
        </el-col>
      </el-row>
    </el-card>


  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { formatUserRole, getUserRoleColor } from '@/utils/auth'
import api from '@/utils/api'

// Store
const authStore = useAuthStore()

// 响应式数据
const userForm = reactive({
  username: '',
  email: '',
  full_name: ''
})

const userStats = reactive({
  totalTasks: 0,
  completedTasks: 0,
  totalReports: 0,
  avgMood: null
})

// userGroup变量已移除，直接使用authStore.user.group_name
const isEditing = ref(false)
const saving = ref(false)

// 表单引用
const profileFormRef = ref()

// 计算属性
const userInitials = computed(() => {
  const user = authStore.user
  if (user?.full_name) {
    return user.full_name.charAt(0).toUpperCase()
  }
  if (user?.username) {
    return user.username.charAt(0).toUpperCase()
  }
  return 'U'
})

const canEdit = computed(() => {
  // 用户可以编辑自己的基本信息
  return authStore.isAuthenticated
})

// 表单验证规则
const rules = {
  email: [
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  full_name: [
    { min: 1, max: 50, message: '姓名长度应在1-50个字符之间', trigger: 'blur' }
  ]
}

// 工具函数
const formatUserIdentity = (identity) => {
  const identityMap = {
    'cc': 'CC(顾问)',
    'ss': 'SS(班主任)',
    'lp': 'LP(英文辅导)',
    'sa': 'SA(超级分析师)'
  }
  return identityMap[identity] || identity || '未知'
}

const getRoleTagType = (user) => {
  if (user?.is_super_admin) return 'danger'
  if (user?.is_admin) return 'warning'
  return 'primary'
}

const formatDate = (dateString) => {
  if (!dateString) return '未知'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 初始化用户表单数据
const initUserForm = () => {
  if (authStore.user) {
    userForm.username = authStore.user.username || ''
    userForm.email = authStore.user.email || ''
    userForm.full_name = authStore.user.full_name || ''
  }
}

// 获取用户统计信息
const fetchUserStats = async () => {
  try {
    // 获取任务统计
    const taskStatsResponse = await api.get('/tasks/stats/summary')
    const taskStats = taskStatsResponse.data
    
    // 获取日报统计
    const reportStatsResponse = await api.get('/reports/stats/summary')
    const reportStats = reportStatsResponse.data
    
    // 更新统计数据
    Object.assign(userStats, {
      totalTasks: taskStats.total || 0,
      completedTasks: taskStats.done || 0,
      totalReports: reportStats.total_reports || 0,
      avgMood: reportStats.avg_emotion_score || 0
    })
  } catch (error) {
    console.error('获取用户统计失败:', error)
    // 如果API调用失败，显示默认值
    Object.assign(userStats, {
      totalTasks: 0,
      completedTasks: 0,
      totalReports: 0,
      avgMood: 0
    })
  }
}

// 用户组信息直接从authStore.user.group_name获取，无需单独API调用

// 切换编辑模式
const toggleEdit = () => {
  if (isEditing.value) {
    cancelEdit()
  } else {
    isEditing.value = true
  }
}

// 取消编辑
const cancelEdit = () => {
  isEditing.value = false
  initUserForm()
  profileFormRef.value?.clearValidate()
}

// 保存个人资料
const saveProfile = async () => {
  if (!profileFormRef.value) return
  
  try {
    await profileFormRef.value.validate()
    saving.value = true
    
    // 调用API更新用户信息
    const updateData = {
      email: userForm.email,
      full_name: userForm.full_name
    }
    
    // await api.put('/user/me', updateData)
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 更新store中的用户信息
    await authStore.fetchUserInfo()
    
    ElMessage.success('保存成功')
    isEditing.value = false
  } catch (error) {
    if (error.message) {
      ElMessage.error('表单验证失败')
    } else {
      ElMessage.error('保存失败')
      console.error('保存失败:', error)
    }
  } finally {
    saving.value = false
  }
}



// 组件挂载时初始化数据
onMounted(() => {
  initUserForm()
  fetchUserStats()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-description {
  color: #909399;
  margin: 0;
  font-size: 14px;
}

.content-card {
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #303133;
}

/* 用户概览样式 */
.user-overview {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.user-overview :deep(.el-card__body) {
  padding: 30px;
}

.user-info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-avatar-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-avatar {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 24px;
  font-weight: 600;
  border: 3px solid rgba(255, 255, 255, 0.3);
}

.user-basic-info h2 {
  margin: 0 0 10px 0;
  font-size: 24px;
  font-weight: 600;
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-identity {
  background-color: rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
}

.user-status {
  display: flex;
  align-items: center;
}

/* 统计信息样式 */
.stats-row {
  margin: 0;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

/* 表单样式 */
.el-form {
  max-width: none;
}

.el-form-item {
  margin-bottom: 20px;
}

.el-form-item :deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

.el-input :deep(.el-input__wrapper) {
  border-radius: 6px;
}

.el-input :deep(.el-input__wrapper.is-disabled) {
  background-color: #f5f7fa;
}

/* 按钮样式 */
.el-button {
  border-radius: 6px;
  font-weight: 500;
}

.el-button--primary {
  background-color: #409eff;
  border-color: #409eff;
}

.el-button--primary:hover {
  background-color: #66b1ff;
  border-color: #66b1ff;
}

/* 标签样式 */
.el-tag {
  border-radius: 12px;
  font-weight: 500;
}

.el-tag--large {
  padding: 6px 16px;
  font-size: 13px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-container {
    padding: 15px;
  }
  
  .user-info-header {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .user-avatar-section {
    flex-direction: column;
    gap: 15px;
  }
  
  .user-meta {
    justify-content: center;
  }
  
  .stats-row .el-col {
    margin-bottom: 15px;
  }
  
  .stat-item {
    padding: 15px;
  }
  
  .stat-value {
    font-size: 24px;
  }
}

@media (max-width: 480px) {
  .page-title {
    font-size: 20px;
  }
  
  .user-basic-info h2 {
    font-size: 20px;
  }
  
  .user-avatar {
    width: 60px !important;
    height: 60px !important;
    font-size: 20px;
  }
  
  .content-card :deep(.el-card__body) {
    padding: 20px 15px;
  }
  
  .user-overview :deep(.el-card__body) {
    padding: 20px 15px;
  }
}
</style>