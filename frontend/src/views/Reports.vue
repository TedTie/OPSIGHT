<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">日报管理</h1>
      <p class="page-description">查看和管理您的日报</p>
    </div>
    
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>日报列表</span>
          <el-button 
            v-can="'reports:create'"
            type="primary" 
            :icon="Plus" 
            @click="openCreateDialog"
          >
            写日报
          </el-button>
        </div>
      </template>
      
      <div class="table-toolbar">
        <div class="table-filters">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
          
          <el-input
            v-model="filters.search"
            placeholder="搜索日报..."
            :prefix-icon="Search"
            clearable
          />
        </div>
        
        <div class="table-actions">
          <el-button :icon="Refresh" @click="fetchReports">刷新</el-button>
          <el-button 
            v-can="'reports:auto_generate'"
            type="info" 
            @click="autoGenerateReport"
            :loading="autoGenerating"
          >
            自动生成今日日报
          </el-button>
          <el-button 
            v-can="'reports:analyze:batch'"
            type="success" 
            @click="batchAnalyzeReports"
            :loading="loading"
          >
            批量AI分析
          </el-button>
        </div>
      </div>
      
      <el-table
        v-loading="loading"
        :data="reports"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="report_date" label="日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.report_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="摘要" min-width="300" />
        <el-table-column label="AI分析" width="120">
          <template #default="{ row }">
            <el-tag
              v-if="row.ai_result"
              :type="getEmotionType(row.ai_result.emotion_score)"
              size="small"
            >
              {{ row.ai_result.emotion_score }}
            </el-tag>
            <span v-else class="text-muted">未分析</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-can:report.view="row"
              type="primary" 
              size="small" 
              @click="viewReport(row)"
            >
              查看
            </el-button>
            <el-button 
              v-can:report.edit="row"
              type="warning" 
              size="small" 
              @click="editReport(row)"
            >
              编辑
            </el-button>
            <el-button 
              v-if="!row.ai_result" 
              v-can="'reports:analyze'"
              type="success" 
              size="small" 
              @click="analyzeReport(row)"
              :loading="analyzingReports.includes(row.id)"
            >
              AI分析
            </el-button>
            <el-button 
              v-can:report.delete="row"
              type="danger" 
              size="small" 
              @click="deleteReport(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchReports"
          @current-change="fetchReports"
        />
      </div>
    </el-card>
    
    <!-- 创建/编辑日报对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑日报' : '写日报'"
      width="800px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="reportForm"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="日报日期" prop="report_date">
          <el-date-picker
            v-model="reportForm.report_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :disabled="isEdit"
          />
        </el-form-item>
        
        <el-form-item label="工作摘要" prop="summary">
          <el-input
            v-model="reportForm.summary"
            type="textarea"
            :rows="3"
            placeholder="请简要描述今日工作内容"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="完成任务" prop="completed_tasks">
          <div class="completed-tasks-section">
            <!-- 任务选择器 -->
            <div class="task-selector">
              <el-select
                v-model="selectedTaskIds"
                multiple
                placeholder="选择今日完成的任务"
                style="width: 100%; margin-bottom: 10px;"
                @change="updateCompletedTasksText"
              >
                <el-option
                  v-for="task in availableTasks"
                  :key="task.id"
                  :label="task.title"
                  :value="task.id"
                >
                  <span style="float: left">{{ task.title }}</span>
                  <span style="float: right; color: #8492a6; font-size: 13px">
                    {{ getTaskStatusText(task.status) }}
                  </span>
                </el-option>
              </el-select>
              <el-button 
                type="primary" 
                size="small" 
                @click="fetchUserTasks"
                :loading="tasksLoading"
              >
                刷新任务列表
              </el-button>
              <el-button 
                type="success" 
                size="small" 
                @click="loadTaskSummary"
                :loading="loadingSummary"
                style="margin-left: 10px;"
              >
                加载任务完成汇总
              </el-button>
            </div>
            
            <!-- 额外描述 -->
            <el-input
              v-model="reportForm.completed_tasks"
              type="textarea"
              :rows="3"
              placeholder="补充描述完成任务的详细情况或其他工作内容"
              maxlength="1000"
              show-word-limit
            />
          </div>
        </el-form-item>
        
        <el-form-item label="遇到问题" prop="issues_encountered">
          <el-input
            v-model="reportForm.issues_encountered"
            type="textarea"
            :rows="3"
            placeholder="描述工作中遇到的问题和困难"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="明日计划" prop="next_day_plan">
          <el-input
            v-model="reportForm.next_day_plan"
            type="textarea"
            :rows="3"
            placeholder="描述明日的工作计划"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="工作时长" prop="work_hours">
              <el-input-number
                v-model="reportForm.work_hours"
                :min="0"
                :max="24"
                :step="0.5"
                placeholder="工作时长（小时）"
              />
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="心情评分" prop="mood_score">
              <el-rate
                v-model="reportForm.mood_score"
                :max="5"
                show-text
                :texts="['很差', '较差', '一般', '较好', '很好']"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="KPI 通次" prop="call_count">
              <el-input-number
                v-model="reportForm.call_count"
                :min="0"
                :step="1"
                placeholder="今日拨打次数"
              />
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="KPI 通时" prop="call_duration">
              <el-input-number
                v-model="reportForm.call_duration"
                :min="0"
                :step="1"
                placeholder="拨打总时长（分钟）"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitReport" :loading="submitting">
            {{ isEdit ? '更新' : '提交' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 查看日报对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      title="查看日报"
      width="800px"
    >
      <div v-if="currentReport" class="report-detail">
        <div class="report-header">
          <h3>{{ formatDate(currentReport.report_date) }} 日报</h3>
          <div class="report-meta">
            <el-tag>工作时长: {{ currentReport.work_hours }}小时</el-tag>
            <el-tag v-if="currentReport.call_count !== undefined && currentReport.call_duration !== undefined" type="success">
              KPI 通次/通时: {{ currentReport.call_count }}/{{ currentReport.call_duration }}
            </el-tag>
            <el-rate
              v-model="currentReport.mood_score"
              :max="5"
              disabled
              show-text
              :texts="['很差', '较差', '一般', '较好', '很好']"
            />
          </div>
        </div>
        
        <div class="report-section">
          <h4>工作摘要</h4>
          <p>{{ currentReport.summary }}</p>
        </div>
        
        <div class="report-section">
          <h4>完成任务</h4>
          <p>{{ currentReport.completed_tasks }}</p>
        </div>
        
        <div v-if="currentReport.issues_encountered" class="report-section">
          <h4>遇到问题</h4>
          <p>{{ currentReport.issues_encountered }}</p>
        </div>
        
        <div class="report-section">
          <h4>明日计划</h4>
          <p>{{ currentReport.next_day_plan }}</p>
        </div>
        
        <div v-if="currentReport.ai_result" class="report-section">
          <h4>AI分析结果</h4>
          <div class="ai-analysis">
            <div class="ai-analysis-header">
              <el-tag :type="getEmotionType(currentReport.ai_result.emotion_score)" size="large">
                情感评分: {{ currentReport.ai_result.emotion_score }}
              </el-tag>
              <span class="analysis-model">
                模型: {{ currentReport.ai_result.model_used }}
              </span>
            </div>
            
            <div v-if="currentReport.ai_result.emotion_analysis" class="analysis-item">
              <h5>情感分析</h5>
              <p>{{ currentReport.ai_result.emotion_analysis }}</p>
            </div>
            
            <div v-if="currentReport.ai_result.summary" class="analysis-item">
              <h5>工作摘要</h5>
              <p>{{ currentReport.ai_result.summary }}</p>
            </div>
            
            <div v-if="currentReport.ai_result.reflection" class="analysis-item">
              <h5>反思与总结</h5>
              <p>{{ currentReport.ai_result.reflection }}</p>
            </div>
            
            <div v-if="currentReport.ai_result.suggestions" class="analysis-item">
              <h5>改进建议</h5>
              <p>{{ currentReport.ai_result.suggestions }}</p>
            </div>
            
            <div v-if="currentReport.ai_result.keywords && currentReport.ai_result.keywords.length > 0" class="analysis-item">
              <h5>关键词</h5>
              <div class="keywords-container">
                <el-tag
                  v-for="keyword in currentReport.ai_result.keywords"
                  :key="keyword"
                  class="keyword-tag"
                  size="small"
                >
                  {{ keyword }}
                </el-tag>
              </div>
            </div>
            
            <div class="analysis-meta">
              <span class="processing-time">
                处理时间: {{ currentReport.ai_result.processing_time?.toFixed(2) }}秒
              </span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { formatDate, formatDateTime } from '@/utils/date'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import api from '@/utils/api'

// 数据
const loading = ref(false)
const reports = ref([])
const analyzingReports = ref([]) // 正在分析的日报ID列表

// 过滤器
const filters = reactive({
  dateRange: [],
  search: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 对话框
const dialogVisible = ref(false)
const viewDialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref()
const currentReport = ref(null)

// 日报表单
const reportForm = reactive({
  report_date: '',
  summary: '',
  completed_tasks: '',
  issues_encountered: '',
  next_day_plan: '',
  work_hours: 8,
  mood_score: 3,
  call_count: 0,
  call_duration: 0
})

// 任务相关数据
const availableTasks = ref([])
const selectedTaskIds = ref([])
const tasksLoading = ref(false)
const loadingSummary = ref(false)
const autoGenerating = ref(false)

// 表单验证规则
const formRules = {
  report_date: [
    { required: true, message: '请选择日报日期', trigger: 'change' }
  ],
  summary: [
    { required: true, message: '请输入工作摘要', trigger: 'blur' },
    { min: 10, max: 500, message: '摘要长度在 10 到 500 个字符', trigger: 'blur' }
  ],
  completed_tasks: [
    { required: true, message: '请输入完成的任务', trigger: 'blur' }
  ],
  next_day_plan: [
    { required: true, message: '请输入明日计划', trigger: 'blur' }
  ],
  work_hours: [
    { required: true, message: '请输入工作时长', trigger: 'blur' }
  ]
}

// 获取情感类型
const getEmotionType = (score) => {
  if (score >= 0.7) return 'success'
  if (score >= 0.3) return 'warning'
  return 'danger'
}

// 获取任务状态文本
const getTaskStatusText = (status) => {
  const statusMap = {
    'pending': '待处理',
    'processing': '进行中',
    'done': '已完成'
  }
  return statusMap[status] || status
}

// 获取用户任务
const fetchUserTasks = async () => {
  tasksLoading.value = true
  try {
    const response = await api.get('/tasks', {
      params: {
        assigned_to_me: true,
        status: 'done',
        limit: 100
      }
    })
    availableTasks.value = response.data || []
  } catch (error) {
    ElMessage.error('获取任务列表失败')
  } finally {
    tasksLoading.value = false
  }
}

// 更新完成任务文本
const updateCompletedTasksText = () => {
  const selectedTasks = availableTasks.value.filter(task => 
    selectedTaskIds.value.includes(task.id)
  )
  
  if (selectedTasks.length > 0) {
    const taskTitles = selectedTasks.map(task => `• ${task.title}`).join('\n')
    const currentText = reportForm.completed_tasks || ''
    
    // 如果当前文本为空或只包含之前的任务列表，则替换
    if (!currentText || currentText.startsWith('• ')) {
      reportForm.completed_tasks = taskTitles
    } else {
      // 否则在前面添加任务列表
      reportForm.completed_tasks = taskTitles + '\n\n' + currentText
    }
  }
}

// 获取日报列表
const fetchReports = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      ...filters
    }
    
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_date = filters.dateRange[0]
      params.end_date = filters.dateRange[1]
    }
    
    const response = await api.get('/reports', { params })
    reports.value = response.data.items || []
    pagination.total = response.data.total || 0
  } catch (error) {
    ElMessage.error('获取日报列表失败')
  } finally {
    loading.value = false
  }
}

// 打开创建对话框
const openCreateDialog = () => {
  isEdit.value = false
  reportForm.report_date = new Date().toISOString().split('T')[0]
  dialogVisible.value = true
  fetchUserTasks() // 自动获取任务列表
}

// 查看日报
const viewReport = (report) => {
  currentReport.value = report
  viewDialogVisible.value = true
}

// 编辑日报
const editReport = (report) => {
  isEdit.value = true
  Object.assign(reportForm, {
    id: parseInt(report.id), // 确保ID是数字类型
    report_date: report.report_date,
    summary: report.summary,
    completed_tasks: report.completed_tasks,
    issues_encountered: report.issues_encountered || '',
    next_day_plan: report.next_day_plan,
    work_hours: report.work_hours,
    mood_score: report.mood_score,
    call_count: report.call_count || 0,
    call_duration: report.call_duration || 0
  })
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  Object.assign(reportForm, {
    report_date: '',
    summary: '',
    completed_tasks: '',
    issues_encountered: '',
    next_day_plan: '',
    work_hours: 8,
    mood_score: 3,
    call_count: 0,
    call_duration: 0
  })
  selectedTaskIds.value = []
}

// 提交日报
const submitReport = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (isEdit.value) {
      await api.put(`/reports/${reportForm.id}`, reportForm)
      ElMessage.success('日报更新成功')
    } else {
      await api.post('/reports', reportForm)
      ElMessage.success('日报提交成功')
    }
    
    dialogVisible.value = false
    fetchReports()
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error(isEdit.value ? '更新失败' : '提交失败')
    }
  } finally {
    submitting.value = false
  }
}

// 删除日报
const deleteReport = async (report) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除${formatDate(report.report_date)}的日报吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/reports/${parseInt(report.id)}`)
    ElMessage.success('删除成功')
    fetchReports()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// AI分析日报
const analyzeReport = async (report) => {
  try {
    analyzingReports.value.push(parseInt(report.id))
    const response = await api.post(`/ai/analyze-report/${parseInt(report.id)}`)
    
    if (response.data.success) {
      ElMessage.success('AI分析完成')
      // 更新报告状态
      const reportIndex = reports.value.findIndex(r => parseInt(r.id) === parseInt(report.id))
      if (reportIndex !== -1) {
        reports.value[reportIndex].ai_result = response.data.ai_result
      }
    } else {
      ElMessage.warning(response.data.message || 'AI分析失败')
    }
  } catch (error) {
    console.error('AI分析错误:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('AI分析失败，请稍后重试')
    }
  } finally {
    // 移除分析状态
    const index = analyzingReports.value.indexOf(parseInt(report.id))
    if (index > -1) {
      analyzingReports.value.splice(index, 1)
    }
  }
}

// 批量AI分析
const batchAnalyzeReports = async () => {
  try {
    const unanalyzedReports = reports.value.filter(report => !report.ai_result)
    
    if (unanalyzedReports.length === 0) {
      ElMessage.info('所有日报都已完成AI分析')
      return
    }
    
    await ElMessageBox.confirm(
      `确定要对${unanalyzedReports.length}个未分析的日报进行批量AI分析吗？`,
      '批量AI分析',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    loading.value = true
    const reportIds = unanalyzedReports.map(report => parseInt(report.id))
    
    const response = await api.post('/ai/batch-analyze', { report_ids: reportIds })
    
    if (response.data.success) {
      ElMessage.success(`批量分析已启动，正在处理${reportIds.length}个日报`)
      // 刷新列表以获取最新的分析结果
      setTimeout(() => {
        fetchReports()
      }, 2000)
    } else {
      ElMessage.warning(response.data.message || '批量分析启动失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量AI分析错误:', error)
      if (error.response?.data?.detail) {
        ElMessage.error(error.response.data.detail)
      } else {
        ElMessage.error('批量分析失败，请稍后重试')
      }
    }
  } finally {
    loading.value = false
  }
}

// 加载任务完成汇总
const loadTaskSummary = async () => {
  if (!reportForm.report_date) {
    ElMessage.warning('请先选择日报日期')
    return
  }
  
  loadingSummary.value = true
  try {
    const response = await api.get('/task-sync/daily-task-summary', {
      params: {
        date: reportForm.report_date
      }
    })
    
    if (response.data && response.data.length > 0) {
      // 自动填充完成的任务
      const taskSummary = response.data.map(task => 
        `${task.title}: ${task.completion_data || '已完成'}`
      ).join('\n')
      
      reportForm.completed_tasks = taskSummary
      ElMessage.success(`已加载${response.data.length}个任务完成记录`)
    } else {
      ElMessage.info('该日期没有任务完成记录')
    }
  } catch (error) {
    console.error('加载任务汇总失败:', error)
    ElMessage.error('加载任务汇总失败')
  } finally {
    loadingSummary.value = false
  }
}

// 自动生成今日日报
const autoGenerateReport = async () => {
  autoGenerating.value = true
  try {
    const today = new Date().toISOString().split('T')[0]
    const response = await api.post('/task-sync/auto-generate-daily-report', {
      date: today
    })
    
    if (response.data.success) {
      ElMessage.success('自动生成日报成功')
      fetchReports() // 刷新日报列表
    } else {
      ElMessage.warning(response.data.message || '自动生成日报失败')
    }
  } catch (error) {
    console.error('自动生成日报失败:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('自动生成日报失败')
    }
  } finally {
    autoGenerating.value = false
  }
}

// 初始化
onMounted(() => {
  fetchReports()
})
</script>

<style scoped>
.table-toolbar {
  margin-bottom: 16px;
}

.table-filters {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.text-muted {
  color: #909399;
}

.report-detail {
  padding: 20px 0;
}

.report-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.report-header h3 {
  margin: 0 0 12px 0;
  color: #303133;
}

.report-meta {
  display: flex;
  align-items: center;
  gap: 16px;
}

.report-section {
  margin-bottom: 24px;
}

.report-section h4 {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 16px;
  font-weight: 600;
}

.report-section p {
  margin: 0;
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
}

.ai-analysis {
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8f4fd 100%);
  border-radius: 12px;
  border: 1px solid #e1e8ed;
}

.ai-analysis-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #d1dce5;
}

.analysis-model {
  color: #909399;
  font-size: 12px;
  background-color: #fff;
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.analysis-item {
  margin-bottom: 16px;
}

.analysis-item h5 {
  margin: 0 0 8px 0;
  color: #409eff;
  font-size: 14px;
  font-weight: 600;
}

.analysis-item p {
  margin: 0;
  color: #303133;
  line-height: 1.6;
  background-color: #fff;
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.keywords-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword-tag {
  background-color: #fff !important;
  border: 1px solid #409eff !important;
  color: #409eff !important;
}

.analysis-meta {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #d1dce5;
  text-align: right;
}

.processing-time {
  color: #909399;
  font-size: 12px;
}

.completed-tasks-section {
  width: 100%;
}

.task-selector {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.task-selector .el-select {
  flex: 1;
}

@media (max-width: 768px) {
  .table-filters {
    flex-direction: column;
  }
  
  .report-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>