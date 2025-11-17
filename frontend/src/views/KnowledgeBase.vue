<template>
  <div class="knowledge-base-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>知识库管理</h1>
      <p>管理和组织团队知识资源</p>
    </div>

    <!-- 模块选择卡片 -->
    <el-row :gutter="20" class="module-cards">
      <el-col :span="6" v-for="module in modules" :key="module.type">
        <el-card 
          class="module-card" 
          :class="{ active: selectedModule === module.type }"
          @click="selectModule(module.type)"
          shadow="hover"
        >
          <div class="module-content">
            <el-icon :size="32" class="module-icon">
              <component :is="module.icon" />
            </el-icon>
            <h3>{{ module.name }}</h3>
            <p>{{ module.description }}</p>
            <div class="module-stats">
              <span>{{ module.count || 0 }} 条知识</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 知识库内容区域 -->
    <el-card class="content-card" v-if="selectedModule">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="searchQuery"
            placeholder="搜索知识..."
            style="width: 300px"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select v-model="selectedCategory" placeholder="选择分类" clearable style="width: 150px; margin-left: 10px">
            <el-option
              v-for="category in categories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>

          <el-select v-model="selectedStatus" placeholder="状态" clearable style="width: 120px; margin-left: 10px">
            <el-option label="草稿" value="DRAFT" />
            <el-option label="已发布" value="PUBLISHED" />
            <el-option label="已归档" value="ARCHIVED" />
          </el-select>
        </div>

        <div class="toolbar-right">
          <el-button 
            v-if="hasPermission" 
            type="primary" 
            @click="openCreateDialog" 
            :icon="Plus"
          >
            新建知识
          </el-button>
          <el-button @click="refreshKnowledge" :icon="Refresh" :loading="loading">
            刷新
          </el-button>
        </div>
      </div>

      <!-- 知识列表 -->
      <el-table
        :data="knowledgeList"
        v-loading="loading"
        style="width: 100%"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="title" label="标题" min-width="200" sortable="custom">
          <template #default="{ row }">
            <div class="knowledge-title">
              <el-link @click="viewKnowledge(row)" type="primary">{{ row.title }}</el-link>
              <el-tag v-if="row.tags && row.tags.length > 0" size="small" style="margin-left: 8px">
                {{ row.tags[0] }}
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.category || '未分类' }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusType(row.status)" 
              size="small"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="view_count" label="查看次数" width="100" sortable="custom" />

        <el-table-column prop="created_at" label="创建时间" width="180" sortable="custom">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewKnowledge(row)" :icon="View">
              查看
            </el-button>
            <el-button 
              v-if="canEdit(row)"
              size="small" 
              @click="editKnowledge(row)" 
              :icon="Edit"
            >
              编辑
            </el-button>
            <el-button 
              v-if="canDelete(row)"
              size="small" 
              type="danger" 
              @click="deleteKnowledge(row)"
              :icon="Delete"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑知识对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑知识' : '新建知识'"
      width="80%"
      :before-close="handleDialogClose"
    >
      <el-form
        ref="knowledgeFormRef"
        :model="knowledgeForm"
        :rules="formRules"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="标题" prop="title">
              <el-input v-model="knowledgeForm.title" placeholder="请输入知识标题" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类" prop="category">
              <el-input v-model="knowledgeForm.category" placeholder="请输入分类" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="knowledgeForm.status" style="width: 100%">
                <el-option label="草稿" value="DRAFT" />
                <el-option label="已发布" value="PUBLISHED" />
                <el-option label="已归档" value="ARCHIVED" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否公开">
              <el-switch v-model="knowledgeForm.is_public" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="标签">
          <el-input v-model="tagsInput" placeholder="请输入标签，用逗号分隔" />
        </el-form-item>

        <el-form-item label="描述">
          <el-input
            v-model="knowledgeForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入知识描述"
          />
        </el-form-item>

        <el-form-item label="内容" prop="content">
          <el-input
            v-model="knowledgeForm.content"
            type="textarea"
            :rows="10"
            placeholder="请输入知识内容"
          />
        </el-form-item>

        <!-- 文件上传区域 -->
        <el-form-item label="附件">
          <el-upload
            ref="uploadRef"
            :action="uploadUrl"
            :headers="uploadHeaders"
            :data="uploadData"
            :on-success="handleFileSuccess"
            :on-error="handleFileError"
            :before-upload="beforeFileUpload"
            multiple
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 doc/docx/pdf/txt/xlsx/pptx 等格式，单个文件不超过 10MB
              </div>
            </template>
          </el-upload>

          <!-- 已上传文件列表 -->
          <div v-if="uploadedFiles.length > 0" class="uploaded-files">
            <h4>已上传文件：</h4>
            <el-tag
              v-for="file in uploadedFiles"
              :key="file.id"
              closable
              @close="removeFile(file)"
              style="margin: 5px"
            >
              {{ file.original_filename }}
            </el-tag>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveKnowledge" :loading="saving">
            {{ isEdit ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 查看知识对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      title="查看知识"
      width="70%"
    >
      <div v-if="currentKnowledge" class="knowledge-detail">
        <h2>{{ currentKnowledge.title }}</h2>
        <div class="knowledge-meta">
          <el-tag>{{ currentKnowledge.category || '未分类' }}</el-tag>
          <el-tag :type="getStatusType(currentKnowledge.status)">
            {{ getStatusText(currentKnowledge.status) }}
          </el-tag>
          <span class="meta-info">
            创建时间：{{ formatDate(currentKnowledge.created_at) }}
          </span>
          <span class="meta-info">
            查看次数：{{ currentKnowledge.view_count || 0 }}
          </span>
        </div>
        
        <div class="knowledge-description" v-if="currentKnowledge.description">
          <h4>描述：</h4>
          <p>{{ currentKnowledge.description }}</p>
        </div>

        <div class="knowledge-content">
          <h4>内容：</h4>
          <div class="content-text">{{ currentKnowledge.content }}</div>
        </div>

        <!-- 附件列表 -->
        <div v-if="currentKnowledge.files && currentKnowledge.files.length > 0" class="knowledge-files">
          <h4>附件：</h4>
          <div class="file-list">
            <div v-for="file in currentKnowledge.files" :key="file.id" class="file-item">
              <el-link @click="downloadFile(file)" :icon="Download">
                {{ file.original_filename }}
              </el-link>
              <span class="file-size">({{ formatFileSize(file.file_size) }})</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Search from '~icons/tabler/search'
import Plus from '~icons/tabler/plus'
import Refresh from '~icons/tabler/refresh'
import View from '~icons/tabler/eye'
import Edit from '~icons/tabler/edit'
import Delete from '~icons/tabler/trash'
import UploadFilled from '~icons/tabler/upload'
import Download from '~icons/tabler/download'
import Document from '~icons/tabler/file-text'
import DataAnalysis from '~icons/tabler/chart-dots-2'
import User from '~icons/tabler/user'
import School from '~icons/tabler/school'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import api from '@/utils/api'

const authStore = useAuthStore()
const router = useRouter()

// 权限检查
const currentUser = computed(() => authStore.user)
const hasPermission = computed(() => {
  return currentUser.value?.is_admin || currentUser.value?.is_super_admin
})


// 模块定义
const modules = ref([
  {
    type: 'SUMMARY',
    name: '汇总模块',
    description: '数据汇总和分析相关知识',
    icon: DataAnalysis,
    count: 0
  },
  {
    type: 'CC',
    name: 'CC模块',
    description: '顾问相关知识和经验',
    icon: User,
    count: 0
  },
  {
    type: 'SS',
    name: 'SS模块',
    description: '班主任相关知识和经验',
    icon: School,
    count: 0
  },
  {
    type: 'LP',
    name: 'LP模块',
    description: '英文辅导相关知识',
    icon: Document,
    count: 0
  }
])

// 响应式数据
const selectedModule = ref('SUMMARY')
const searchQuery = ref('')
const selectedCategory = ref('')
const selectedStatus = ref('')
const loading = ref(false)
const saving = ref(false)

// 知识列表和分页
const knowledgeList = ref([])
const categories = ref([])
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 对话框状态
const dialogVisible = ref(false)
const viewDialogVisible = ref(false)
const isEdit = ref(false)
const currentKnowledge = ref(null)

// 表单数据
const knowledgeFormRef = ref()
const knowledgeForm = reactive({
  title: '',
  description: '',
  content: '',
  module_type: 'SUMMARY',
  category: '',
  status: 'DRAFT',
  is_public: false,
  tags: []
})

const tagsInput = ref('')
const uploadedFiles = ref([])

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入内容', trigger: 'blur' }
  ]
}

// 文件上传配置
const uploadUrl = computed(() => `${api.defaults.baseURL}/knowledge-base/upload`)
const uploadHeaders = computed(() => ({}))
const uploadData = computed(() => ({
  knowledge_id: knowledgeForm.id || null
}))

// 方法
const selectModule = (moduleType) => {
  selectedModule.value = moduleType
  knowledgeForm.module_type = moduleType
  fetchKnowledge()
}

const handleSearch = () => {
  pagination.page = 1
  fetchKnowledge()
}

const handleSortChange = ({ prop, order }) => {
  // 实现排序逻辑
  fetchKnowledge()
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  fetchKnowledge()
}

const handleCurrentChange = (page) => {
  pagination.page = page
  fetchKnowledge()
}

const refreshKnowledge = () => {
  fetchKnowledge()
}

const openCreateDialog = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const editKnowledge = (knowledge) => {
  isEdit.value = true
  Object.assign(knowledgeForm, knowledge)
  tagsInput.value = knowledge.tags ? knowledge.tags.join(', ') : ''
  uploadedFiles.value = knowledge.files || []
  dialogVisible.value = true
}

const viewKnowledge = async (knowledge) => {
  try {
    const response = await api.get(`/knowledge-base/${knowledge.id}`)
    currentKnowledge.value = response.data
    viewDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取知识详情失败')
  }
}

const deleteKnowledge = async (knowledge) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除知识"${knowledge.title}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/knowledge-base/${knowledge.id}`)
    ElMessage.success('删除成功')
    fetchKnowledge()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const saveKnowledge = async () => {
  try {
    await knowledgeFormRef.value.validate()
    saving.value = true
    
    // 处理标签
    knowledgeForm.tags = tagsInput.value 
      ? tagsInput.value.split(',').map(tag => tag.trim()).filter(tag => tag)
      : []
    
    if (isEdit.value) {
      await api.put(`/knowledge-base/${knowledgeForm.id}`, knowledgeForm)
      ElMessage.success('更新成功')
    } else {
      await api.post('/knowledge-base/', knowledgeForm)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    fetchKnowledge()
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  Object.assign(knowledgeForm, {
    title: '',
    description: '',
    content: '',
    module_type: selectedModule.value,
    category: '',
    status: 'DRAFT',
    is_public: false,
    tags: []
  })
  tagsInput.value = ''
  uploadedFiles.value = []
}

const handleDialogClose = (done) => {
  ElMessageBox.confirm('确定要关闭吗？未保存的更改将丢失。')
    .then(() => {
      done()
    })
    .catch(() => {})
}

// 文件上传处理
const beforeFileUpload = (file) => {
  const allowedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain'
  ]
  
  const isAllowedType = allowedTypes.includes(file.type)
  const isLt10M = file.size / 1024 / 1024 < 10
  
  if (!isAllowedType) {
    ElMessage.error('只支持 doc/docx/pdf/txt/xlsx/pptx 格式的文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB!')
    return false
  }
  return true
}

const handleFileSuccess = (response, file) => {
  if (response.success && response.file_info) {
    uploadedFiles.value.push(response.file_info)
    ElMessage.success('文件上传成功')
  } else {
    ElMessage.error(response.message || '文件上传失败')
  }
}

const handleFileError = (error, file) => {
  ElMessage.error('文件上传失败')
}

const removeFile = async (file) => {
  try {
    await api.delete(`/knowledge-base/files/${file.id}`)
    uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== file.id)
    ElMessage.success('文件删除成功')
  } catch (error) {
    ElMessage.error('文件删除失败')
  }
}

const downloadFile = (file) => {
  window.open(`${api.defaults.baseURL}/knowledge-base/files/${file.id}/download`)
}

// 获取知识列表
const fetchKnowledge = async () => {
  try {
    loading.value = true
    const params = {
      module_type: selectedModule.value,
      page: pagination.page,
      size: pagination.size,
      search: searchQuery.value,
      category: selectedCategory.value,
      status: selectedStatus.value
    }
    
    const response = await api.get('/knowledge-base/search', { params })
    knowledgeList.value = response.data.items
    pagination.total = response.data.total
    
    // 更新模块统计
    const moduleStats = await api.get('/knowledge-base/stats')
    modules.value.forEach(module => {
      const stat = moduleStats.data.find(s => s.module_type === module.type)
      module.count = stat ? stat.count : 0
    })
  } catch (error) {
    ElMessage.error('获取知识列表失败')
  } finally {
    loading.value = false
  }
}

// 获取分类列表
const fetchCategories = async () => {
  try {
    const response = await api.get('/knowledge-base/categories', {
      params: { module_type: selectedModule.value }
    })
    categories.value = response.data
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}

// 工具函数
const getStatusType = (status) => {
  const types = {
    'DRAFT': 'info',
    'PUBLISHED': 'success',
    'ARCHIVED': 'warning'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    'DRAFT': '草稿',
    'PUBLISHED': '已发布',
    'ARCHIVED': '已归档'
  }
  return texts[status] || '未知'
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('zh-CN')
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 权限检查函数
const canEdit = (knowledge) => {
  if (!currentUser.value) return false
  
  // 超级管理员可以编辑所有内容
  if (currentUser.value.is_super_admin) return true
  
  // 创建者可以编辑自己的内容
  if (knowledge.created_by === currentUser.value.id) return true
  
  // 管理员可以编辑自己模块的内容（大小写统一）
  if (
    currentUser.value.is_admin &&
    String(knowledge.module_type || '').toUpperCase() === String(currentUser.value.identity_type || '').toUpperCase()
  ) {
    return true
  }
  
  return false
}

const canDelete = (knowledge) => {
  if (!currentUser.value) return false
  
  // 超级管理员可以删除所有内容
  if (currentUser.value.is_super_admin) return true
  
  // 创建者可以删除自己的内容
  if (knowledge.created_by === currentUser.value.id) return true
  
  // 管理员可以删除自己模块的内容（大小写统一）
  if (
    currentUser.value.is_admin &&
    String(knowledge.module_type || '').toUpperCase() === String(currentUser.value.identity_type || '').toUpperCase()
  ) {
    return true
  }
  
  return false
}

// 监听模块变化
watch(selectedModule, () => {
  fetchCategories()
  fetchKnowledge()
})

// 组件挂载
onMounted(() => {
  fetchCategories()
  fetchKnowledge()
})
</script>

<style scoped>
.knowledge-base-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
}

.page-header p {
  margin: 5px 0 0 0;
  color: #909399;
}

.module-cards {
  margin-bottom: 20px;
}

.module-card {
  cursor: pointer;
  transition: all 0.3s;
}

.module-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.module-card.active {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.module-content {
  text-align: center;
}

.module-icon {
  color: #409eff;
  margin-bottom: 10px;
}

.module-content h3 {
  margin: 10px 0 5px 0;
  color: #303133;
}

.module-content p {
  margin: 0 0 10px 0;
  color: #909399;
  font-size: 14px;
}

.module-stats {
  color: #409eff;
  font-weight: bold;
}

.content-card {
  margin-top: 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.knowledge-title {
  display: flex;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

.uploaded-files {
  margin-top: 10px;
}

.uploaded-files h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #303133;
}

.knowledge-detail {
  padding: 20px 0;
}

.knowledge-detail h2 {
  margin: 0 0 15px 0;
  color: #303133;
}

.knowledge-meta {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.meta-info {
  color: #909399;
  font-size: 14px;
}

.knowledge-description,
.knowledge-content {
  margin-bottom: 20px;
}

.knowledge-description h4,
.knowledge-content h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.content-text {
  white-space: pre-wrap;
  line-height: 1.6;
  color: #606266;
}

.knowledge-files h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-size {
  color: #909399;
  font-size: 12px;
}
</style>