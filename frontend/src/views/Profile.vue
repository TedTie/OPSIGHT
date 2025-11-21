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
          <div class="avatar-wrapper" @click="triggerFileInput" :class="{ 'is-editable': isEditing }">
            <el-avatar :size="80" :src="userForm.avatar_url || authStore.user?.avatar_url" class="user-avatar">
              {{ userInitials }}
            </el-avatar>
            <div v-if="isEditing" class="avatar-overlay">
              <i class="el-icon-camera">📷</i>
            </div>
            <input
              ref="fileInput"
              type="file"
              accept="image/png, image/jpeg"
              style="display: none"
              @change="handleFileChange"
            />
          </div>
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

    <!-- 图片裁剪弹窗 -->
    <el-dialog
      v-model="showCropper"
      title="修改头像"
      width="600px"
      :close-on-click-modal="false"
    >
      <div style="height: 400px">
        <vue-cropper
          ref="cropperRef"
          :img="cropOption.img"
          :output-size="cropOption.size"
          :output-type="cropOption.outputType"
          :info="true"
          :full="cropOption.full"
          :can-move="cropOption.canMove"
          :can-move-box="cropOption.canMoveBox"
          :fixed-box="cropOption.fixedBox"
          :original="cropOption.original"
          :auto-crop="cropOption.autoCrop"
          :auto-crop-width="cropOption.autoCropWidth"
          :auto-crop-height="cropOption.autoCropHeight"
          :center-box="cropOption.centerBox"
          :high="cropOption.high"
        />
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCropper = false">取消</el-button>
          <el-button type="primary" @click="confirmCrop" :loading="uploadLoading">
            确认并上传
          </el-button>
        </span>
      </template>
    </el-dialog>

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
import 'vue-cropper/dist/index.css'
import { VueCropper } from "vue-cropper"
import { createClient } from '@supabase/supabase-js'

// Supabase Client
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY
const supabase = (supabaseUrl && supabaseKey) ? createClient(supabaseUrl, supabaseKey) : null

// Store
const authStore = useAuthStore()

// 响应式数据
const userForm = reactive({
  username: '',
  email: '',
  full_name: '',
  avatar_url: ''
})

const userStats = reactive({
  totalTasks: 0,
  completedTasks: 0,
  totalReports: 0,
  avgMood: null
})

// 头像上传相关
const showCropper = ref(false)
const cropperImg = ref('')
const cropperRef = ref()
const uploadLoading = ref(false)
const fileInput = ref()
const cropOption = reactive({
  img: '',
  size: 1,
  full: false,
  outputType: 'png',
  canMove: true,
  fixedBox: false,
  original: false,
  canMoveBox: true,
  autoCrop: true,
  autoCropWidth: 200,
  autoCropHeight: 200,
  centerBox: true,
  high: true
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
    userForm.avatar_url = authStore.user.avatar_url || ''
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

// 头像上传逻辑
const triggerFileInput = () => {
  if (!isEditing.value) return
  fileInput.value.click()
}

const handleFileChange = (e) => {
  const file = e.target.files[0]
  if (!file) return
  
  // 验证文件类型
  const isJPG = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isJPG) {
    ElMessage.error('上传头像图片只能是 JPG/PNG 格式!')
    return
  }
  if (!isLt2M) {
    ElMessage.error('上传头像图片大小不能超过 2MB!')
    return
  }

  // 读取文件
  const reader = new FileReader()
  reader.onload = (e) => {
    cropOption.img = e.target.result
    showCropper.value = true
  }
  reader.readAsDataURL(file)
  // 清空 input，允许重复选择同一文件
  e.target.value = ''
}

const confirmCrop = () => {
  cropperRef.value.getCropBlob(async (blob) => {
    if (!blob) return
    
    uploadLoading.value = true
    try {
      if (!supabase) {
        throw new Error('Supabase client not initialized')
      }

      const fileName = `avatar_${authStore.user.id}_${Date.now()}.png`
      const { data, error } = await supabase.storage
        .from('avatars')
        .upload(fileName, blob, {
          contentType: 'image/png',
          upsert: true
        })

      if (error) throw error

      // 获取公开链接
      const { data: { publicUrl } } = supabase.storage
        .from('avatars')
        .getPublicUrl(fileName)

      userForm.avatar_url = publicUrl
      showCropper.value = false
      ElMessage.success('头像上传成功，请点击保存以生效')
    } catch (error) {
      console.error('Upload failed:', error)
      ElMessage.error('头像上传失败: ' + (error.message || '未知错误'))
    } finally {
      uploadLoading.value = false
    }
  })
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
      full_name: userForm.full_name,
      avatar_url: userForm.avatar_url
    }
    
    await api.put('/users/me', updateData)
    
    // 更新store中的用户信息
    await authStore.fetchUserInfo()
    
    ElMessage.success('保存成功')
    isEditing.value = false
  } catch (error) {
    if (error.message) {
      // ElMessage.error('表单验证失败')
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
  background: var(--brand-gradient);
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

.avatar-wrapper {
  position: relative;
  cursor: default;
}

.avatar-wrapper.is-editable {
  cursor: pointer;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: white;
  font-size: 24px;
  opacity: 0;
  transition: opacity 0.3s;
}

.avatar-wrapper.is-editable:hover .avatar-overlay {
  opacity: 1;
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