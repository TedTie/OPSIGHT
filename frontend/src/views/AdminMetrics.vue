<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">自定义指标管理</h1>
      <p class="page-description">管理和配置系统自定义指标</p>
    </div>

    <!-- 指标概览 -->
    <div class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalMetrics }}</div>
          <div class="stat-label">总指标数</div>
        </div>
        <el-icon class="stat-icon"><DataAnalysis /></el-icon>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ stats.activeMetrics }}</div>
          <div class="stat-label">活跃指标</div>
        </div>
        <el-icon class="stat-icon"><TrendCharts /></el-icon>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ stats.customMetrics }}</div>
          <div class="stat-label">自定义指标</div>
        </div>
        <el-icon class="stat-icon"><Setting /></el-icon>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ stats.systemMetrics }}</div>
          <div class="stat-label">系统指标</div>
        </div>
        <el-icon class="stat-icon"><Monitor /></el-icon>
      </el-card>
    </div>

    <!-- 指标管理 -->
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>指标列表</span>
          <div class="header-actions">
            <el-button type="primary" :icon="Plus" @click="showCreateDialog">
              新增指标
            </el-button>
            <el-button :icon="Refresh" @click="fetchMetrics">
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选器 -->
      <div class="filters">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-select v-model="filters.type" placeholder="指标类型" clearable @change="fetchMetrics">
              <el-option label="全部" value="" />
              <el-option label="系统指标" value="system" />
              <el-option label="业务指标" value="business" />
              <el-option label="性能指标" value="performance" />
              <el-option label="用户指标" value="user" />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-select v-model="filters.status" placeholder="状态" clearable @change="fetchMetrics">
              <el-option label="全部" value="" />
              <el-option label="启用" value="active" />
              <el-option label="禁用" value="inactive" />
            </el-select>
          </el-col>
          <el-col :span="8">
            <el-input
              v-model="filters.search"
              placeholder="搜索指标名称或描述"
              :prefix-icon="Search"
              clearable
              @input="debounceSearch"
            />
          </el-col>
          <el-col :span="4">
            <el-button type="primary" @click="fetchMetrics">搜索</el-button>
          </el-col>
        </el-row>
      </div>

      <!-- 指标表格 -->
      <el-table
        v-loading="loading"
        :data="metrics"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="name" label="指标名称" width="200">
          <template #default="{ row }">
            <div class="metric-name">
              <strong>{{ row.name }}</strong>
              <div class="metric-key">{{ row.key }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)" size="small">
              {{ getTypeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="description" label="描述" min-width="200" />
        
        <el-table-column prop="unit" label="单位" width="80" />
        
        <el-table-column prop="value" label="当前值" width="120">
          <template #default="{ row }">
            <span class="metric-value">{{ formatValue(row.value, row.unit) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewMetric(row)">
              查看
            </el-button>
            <el-button size="small" type="primary" @click="editMetric(row)">
              编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteMetric(row)"
              :disabled="row.type === 'system'"
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
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchMetrics"
          @current-change="fetchMetrics"
        />
      </div>
    </el-card>

    <!-- 创建/编辑指标对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑指标' : '新增指标'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="指标名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        
        <el-form-item label="指标键值" prop="key">
          <el-input v-model="form.key" placeholder="用于API调用的唯一标识" />
        </el-form-item>
        
        <el-form-item label="指标类型" prop="type">
          <el-select v-model="form.type" style="width: 100%">
            <el-option label="业务指标" value="business" />
            <el-option label="性能指标" value="performance" />
            <el-option label="用户指标" value="user" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入指标描述"
          />
        </el-form-item>
        
        <el-form-item label="单位" prop="unit">
          <el-input v-model="form.unit" placeholder="例如: 个, %, 秒, MB" />
        </el-form-item>
        
        <el-form-item label="计算公式" prop="formula">
          <el-input
            v-model="form.formula"
            type="textarea"
            :rows="2"
            placeholder="例如: SUM(tasks.completed) / COUNT(tasks.total) * 100"
          />
        </el-form-item>
        
        <el-form-item label="更新频率" prop="update_frequency">
          <el-select v-model="form.update_frequency" style="width: 100%">
            <el-option label="实时" value="realtime" />
            <el-option label="每分钟" value="minute" />
            <el-option label="每小时" value="hour" />
            <el-option label="每天" value="daily" />
            <el-option label="每周" value="weekly" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="submitForm">
            {{ isEdit ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 指标详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="指标详情"
      width="800px"
    >
      <div v-if="selectedMetric" class="metric-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="指标名称">{{ selectedMetric.name }}</el-descriptions-item>
          <el-descriptions-item label="指标键值">{{ selectedMetric.key }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :type="getTypeTagType(selectedMetric.type)" size="small">
              {{ getTypeLabel(selectedMetric.type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedMetric.is_active ? 'success' : 'danger'" size="small">
              {{ selectedMetric.is_active ? '启用' : '禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前值">{{ formatValue(selectedMetric.value, selectedMetric.unit) }}</el-descriptions-item>
          <el-descriptions-item label="单位">{{ selectedMetric.unit || '-' }}</el-descriptions-item>
          <el-descriptions-item label="更新频率">{{ getFrequencyLabel(selectedMetric.update_frequency) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDateTime(selectedMetric.updated_at) }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ selectedMetric.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="计算公式" :span="2">
            <code>{{ selectedMetric.formula || '-' }}</code>
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 历史趋势图 -->
        <div class="metric-chart" style="margin-top: 20px;">
          <h4>历史趋势</h4>
          <div ref="chartRef" style="width: 100%; height: 300px;"></div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Refresh,
  Search,
  DataAnalysis,
  TrendCharts,
  Setting,
  Monitor
} from '@element-plus/icons-vue'
import api from '@/utils/api'
import { formatDateTime } from '@/utils/date'
import { debounce } from 'lodash-es'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const chartRef = ref()

// 统计数据
const stats = reactive({
  totalMetrics: 0,
  activeMetrics: 0,
  customMetrics: 0,
  systemMetrics: 0
})

// 指标列表
const metrics = ref([])
const selectedMetric = ref(null)

// 筛选器
const filters = reactive({
  type: '',
  status: '',
  search: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 表单数据
const form = reactive({
  name: '',
  key: '',
  type: 'business',
  description: '',
  unit: '',
  formula: '',
  update_frequency: 'daily',
  is_active: true
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入指标名称', trigger: 'blur' }
  ],
  key: [
    { required: true, message: '请输入指标键值', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '键值必须以字母开头，只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择指标类型', trigger: 'change' }
  ],
  update_frequency: [
    { required: true, message: '请选择更新频率', trigger: 'change' }
  ]
}

// 计算属性
const debounceSearch = debounce(() => {
  fetchMetrics()
}, 500)

// 方法
const getTypeLabel = (type) => {
  const labels = {
    system: '系统指标',
    business: '业务指标',
    performance: '性能指标',
    user: '用户指标'
  }
  return labels[type] || type
}

const getTypeTagType = (type) => {
  const types = {
    system: 'info',
    business: 'success',
    performance: 'warning',
    user: 'primary'
  }
  return types[type] || 'default'
}

const getFrequencyLabel = (frequency) => {
  const labels = {
    realtime: '实时',
    minute: '每分钟',
    hour: '每小时',
    daily: '每天',
    weekly: '每周'
  }
  return labels[frequency] || frequency
}

const formatValue = (value, unit) => {
  if (value === null || value === undefined) return '-'
  return `${value}${unit ? ' ' + unit : ''}`
}

// 获取统计数据
const fetchStats = async () => {
  try {
    const response = await api.get('/admin/metrics/stats')
    Object.assign(stats, response.data)
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 获取指标列表
const fetchMetrics = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      ...filters
    }
    
    const response = await api.get('/admin/metrics', { params })
    metrics.value = response.data.items || []
    pagination.total = response.data.total || 0
  } catch (error) {
    ElMessage.error('获取指标列表失败')
  } finally {
    loading.value = false
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

// 编辑指标
const editMetric = (metric) => {
  isEdit.value = true
  Object.assign(form, {
    id: parseInt(metric.id), // 确保ID是数字类型
    name: metric.name,
    key: metric.key,
    type: metric.type,
    description: metric.description,
    unit: metric.unit,
    formula: metric.formula,
    update_frequency: metric.update_frequency,
    is_active: metric.is_active
  })
  dialogVisible.value = true
}

// 查看指标详情
const viewMetric = (metric) => {
  selectedMetric.value = metric
  detailDialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    id: '',
    name: '',
    key: '',
    type: 'business',
    description: '',
    unit: '',
    formula: '',
    update_frequency: 'daily',
    is_active: true
  })
  formRef.value?.clearValidate()
}

// 提交表单
const submitForm = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (isEdit.value) {
      await api.put(`/admin/metrics/${form.id}`, form)
      ElMessage.success('更新成功')
    } else {
      await api.post('/admin/metrics', form)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    fetchMetrics()
    fetchStats()
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

// 删除指标
const deleteMetric = async (metric) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除指标 ${metric.name} 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/admin/metrics/${parseInt(metric.id)}`)
    ElMessage.success('删除成功')
    fetchMetrics()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 初始化
onMounted(() => {
  fetchStats()
  fetchMetrics()
})
</script>

<style scoped>
.page-container {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
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
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  .el-card__body {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px;
  }
}

.stat-content {
  .stat-value {
    font-size: 28px;
    font-weight: bold;
    color: #303133;
    margin-bottom: 8px;
  }
  
  .stat-label {
    font-size: 14px;
    color: #909399;
  }
}

.stat-icon {
  font-size: 40px;
  color: #409EFF;
  opacity: 0.8;
}

.content-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.filters {
  margin-bottom: 16px;
}

.metric-name {
  .metric-key {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
  }
}

.metric-value {
  font-weight: 600;
  color: #409EFF;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.metric-detail {
  .metric-chart {
    h4 {
      margin: 0 0 16px 0;
      color: #303133;
    }
  }
}

code {
  background: #f5f7fa;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}
</style>