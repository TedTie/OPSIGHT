<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">AI智能体管理</h1>
      <p class="page-description">配置智能体、管理AI功能和监控调用日志</p>
    </div>

    <!-- 统计概览 -->
    <div class="stats-overview">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_agents }}</div>
          <div class="stat-label">智能体总数</div>
          <div class="stat-sub">活跃: {{ stats.active_agents }}</div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_functions }}</div>
          <div class="stat-label">AI功能总数</div>
          <div class="stat-sub">活跃: {{ stats.active_functions }}</div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_calls }}</div>
          <div class="stat-label">总调用次数</div>
          <div class="stat-sub">今日: {{ stats.today_calls }}</div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ successRate }}%</div>
          <div class="stat-label">成功率</div>
          <div class="stat-sub">失败: {{ stats.failed_calls }}</div>
        </div>
      </el-card>
    </div>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- 模块一：智能体配置 -->
      <el-tab-pane label="智能体配置" name="agents">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>智能体列表</span>
              <el-button type="primary" :icon="Plus" @click="showCreateAgentDialog">
                新增智能体
              </el-button>
            </div>
          </template>

          <el-table
            v-loading="agentsLoading"
            :data="agents"
            stripe
            style="width: 100%"
          >
            <el-table-column prop="name" label="智能体名称" width="150" />
            <el-table-column prop="description" label="描述" min-width="200" />
            <el-table-column prop="provider" label="模型提供商" width="120">
              <template #default="{ row }">
                <el-tag :type="getProviderTagType(row.provider)" size="small">
                  {{ formatProvider(row.provider) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="model_name" label="模型" width="180" />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button type="text" size="small" @click="viewAgent(row)">
                  查看
                </el-button>
                <el-button type="text" size="small" @click="editAgent(row)">
                  编辑
                </el-button>
                <el-button type="text" size="small" @click="deleteAgent(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 模块二：AI功能配置 -->
      <el-tab-pane label="AI功能配置" name="functions">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>AI功能列表</span>
              <el-button type="primary" :icon="Plus" @click="showCreateFunctionDialog">
                新增AI功能
              </el-button>
            </div>
          </template>

          <el-table
            v-loading="functionsLoading"
            :data="functions"
            stripe
            style="width: 100%"
          >
            <el-table-column prop="name" label="功能名称" width="150" />
            <el-table-column prop="description" label="描述" min-width="200" />
            <el-table-column prop="function_type" label="功能类型" width="120">
              <template #default="{ row }">
                <el-tag :type="getFunctionTypeTagType(row.function_type)" size="small">
                  {{ formatFunctionType(row.function_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="关联智能体" width="180">
              <template #default="{ row }">
                <span v-if="row.agent_name">{{ row.agent_name }}</span>
                <el-tag v-else type="warning" size="small">未配置</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button type="text" size="small" @click="testFunction(row)">
                  测试
                </el-button>
                <el-button type="text" size="small" @click="editFunction(row)">
                  编辑
                </el-button>
                <el-button type="text" size="small" @click="deleteFunction(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 模块三：功能配置 -->
      <el-tab-pane label="功能配置" name="config">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>AI功能配置</span>
              <div class="header-actions">
                <el-button :icon="Refresh" @click="fetchSystemFunctions">刷新</el-button>
              </div>
            </div>
          </template>

          <div class="config-description">
            <el-alert
              title="功能说明"
              description="以下是系统中所有使用AI功能的地方，您可以为每个功能选择对应的智能体，就像为不同文件类型选择默认应用程序一样。"
              type="info"
              :closable="false"
              style="margin-bottom: 20px"
            />
          </div>

          <el-table
            v-loading="systemFunctionsLoading"
            :data="systemFunctions"
            stripe
            style="width: 100%"
          >
            <el-table-column prop="name" label="功能名称" width="150" />
            <el-table-column prop="description" label="功能描述" min-width="250" />
            <el-table-column prop="category" label="功能分类" width="120">
              <template #default="{ row }">
                <el-tag :type="getCategoryTagType(row.category)" size="small">
                  {{ formatCategory(row.category) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="usage_location" label="使用位置" width="150" />
            <el-table-column label="当前智能体" width="200">
              <template #default="{ row }">
                <el-select
                  v-model="row.assigned_agent_id"
                  placeholder="选择智能体"
                  clearable
                  style="width: 100%"
                  @change="updateFunctionAgent(row)"
                >
                  <el-option
                    v-for="agent in activeAgents"
                    :key="agent.id"
                    :label="agent.name"
                    :value="agent.id"
                  >
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                      <span>{{ agent.name }}</span>
                      <el-tag :type="getProviderTagType(agent.provider)" size="small">
                        {{ formatProvider(agent.provider) }}
                      </el-tag>
                    </div>
                  </el-option>
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'warning'" size="small">
                  {{ row.assigned_agent_id ? '已配置' : '未配置' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button 
                  type="text" 
                  size="small" 
                  @click="testSystemFunction(row)"
                  :disabled="!row.assigned_agent_id"
                >
                  测试
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 模块四：调用日志 -->
      <el-tab-pane label="调用日志" name="logs">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>调用日志</span>
              <div class="header-actions">
                <el-select
                  v-model="logFilters.function_id"
                  placeholder="选择AI功能"
                  clearable
                  style="width: 200px; margin-right: 10px"
                  @change="fetchLogs"
                >
                  <el-option
                    v-for="func in functions"
                    :key="func.id"
                    :label="func.name"
                    :value="func.id"
                  />
                </el-select>
                <el-select
                  v-model="logFilters.status"
                  placeholder="选择状态"
                  clearable
                  style="width: 120px; margin-right: 10px"
                  @change="fetchLogs"
                >
                  <el-option label="成功" value="success" />
                  <el-option label="失败" value="failed" />
                  <el-option label="进行中" value="pending" />
                </el-select>
                <el-button :icon="Refresh" @click="fetchLogs">刷新</el-button>
              </div>
            </div>
          </template>

          <el-table
            v-loading="logsLoading"
            :data="logs"
            stripe
            style="width: 100%"
          >
            <el-table-column prop="created_at" label="调用时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="function_name" label="AI功能" width="150" />
            <el-table-column prop="user_name" label="调用用户" width="120" />
            <el-table-column label="输入内容" min-width="200">
              <template #default="{ row }">
                <el-tooltip :content="row.input_text" placement="top">
                  <span class="text-ellipsis">{{ row.input_text }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)" size="small">
                  {{ formatStatus(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="tokens_used" label="Token消耗" width="100" />
            <el-table-column label="响应时间" width="100">
              <template #default="{ row }">
                <span v-if="row.completed_at && row.created_at">
                  {{ getResponseTime(row.created_at, row.completed_at) }}ms
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button type="text" size="small" @click="viewLogDetail(row)">
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-container">
            <el-pagination
              v-model:current-page="logsPagination.page"
              v-model:page-size="logsPagination.size"
              :total="logsPagination.total"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="fetchLogs"
              @current-change="fetchLogs"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 智能体创建/编辑对话框 -->
    <el-dialog
      v-model="agentDialogVisible"
      :title="isEditAgent ? '编辑智能体' : '新增智能体'"
      width="700px"
    >
      <el-form
        ref="agentFormRef"
        :model="agentForm"
        :rules="agentFormRules"
        label-width="120px"
      >
        <el-form-item label="智能体名称" prop="name">
          <el-input v-model="agentForm.name" placeholder="请输入智能体名称" />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="agentForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入智能体描述"
          />
        </el-form-item>
        
        <el-form-item label="模型提供商" prop="provider">
          <el-select v-model="agentForm.provider" style="width: 100%">
            <el-option label="OpenAI" value="openai" />
            <el-option label="Claude" value="claude" />
            <el-option label="Gemini" value="gemini" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型名称" prop="model_name">
          <el-input v-model="agentForm.model_name" placeholder="例如: gpt-4, claude-3-sonnet" />
        </el-form-item>
        
        <el-form-item label="系统提示词" prop="system_prompt">
          <el-input
            v-model="agentForm.system_prompt"
            type="textarea"
            :rows="6"
            placeholder="请输入系统提示词，定义智能体的角色和行为"
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="温度" prop="temperature">
              <el-input-number
                v-model="agentForm.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大Token" prop="max_tokens">
              <el-input-number
                v-model="agentForm.max_tokens"
                :min="1"
                :max="32000"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="状态">
          <el-switch v-model="agentForm.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="agentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAgentForm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- AI功能创建/编辑对话框 -->
    <el-dialog
      v-model="functionDialogVisible"
      :title="isEditFunction ? '编辑AI功能' : '新增AI功能'"
      width="600px"
    >
      <el-form
        ref="functionFormRef"
        :model="functionForm"
        :rules="functionFormRules"
        label-width="120px"
      >
        <el-form-item label="功能名称" prop="name">
          <el-input v-model="functionForm.name" placeholder="请输入功能名称" />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="functionForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入功能描述"
          />
        </el-form-item>
        
        <el-form-item label="功能类型" prop="function_type">
          <el-select v-model="functionForm.function_type" style="width: 100%">
            <el-option label="文本生成" value="text_generation" />
            <el-option label="文本分析" value="text_analysis" />
            <el-option label="翻译" value="translation" />
            <el-option label="摘要" value="summarization" />
            <el-option label="问答" value="qa" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="关联智能体" prop="agent_id">
          <el-select v-model="functionForm.agent_id" style="width: 100%" clearable>
            <el-option
              v-for="agent in activeAgents"
              :key="agent.id"
              :label="agent.name"
              :value="agent.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch v-model="functionForm.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="functionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitFunctionForm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 日志详情对话框 -->
    <el-dialog
      v-model="logDetailDialogVisible"
      title="调用详情"
      width="800px"
    >
      <div v-if="selectedLog" class="log-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="调用时间">
            {{ formatDateTime(selectedLog.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="完成时间">
            {{ selectedLog.completed_at ? formatDateTime(selectedLog.completed_at) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="AI功能">
            {{ selectedLog.function_name }}
          </el-descriptions-item>
          <el-descriptions-item label="调用用户">
            {{ selectedLog.user_name }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(selectedLog.status)" size="small">
              {{ formatStatus(selectedLog.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="Token消耗">
            {{ selectedLog.tokens_used || '-' }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="log-content">
          <h4>输入内容：</h4>
          <div class="content-box">{{ selectedLog.input_text }}</div>
          
          <h4>输出内容：</h4>
          <div class="content-box">{{ selectedLog.output_text || '无输出内容' }}</div>
          
          <div v-if="selectedLog.error_message">
            <h4>错误信息：</h4>
            <div class="content-box error">{{ selectedLog.error_message }}</div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 功能测试对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="测试AI功能"
      width="600px"
    >
      <div v-if="testingFunction">
        <p><strong>功能：</strong>{{ testingFunction.name }}</p>
        <p><strong>描述：</strong>{{ testingFunction.description }}</p>
        
        <el-form>
          <el-form-item label="测试输入">
            <el-input
              v-model="testInput"
              type="textarea"
              :rows="4"
              placeholder="请输入测试内容"
            />
          </el-form-item>
        </el-form>
        
        <div v-if="testResult" class="test-result">
          <h4>测试结果：</h4>
          <div class="content-box">{{ testResult.output_text }}</div>
          <p><small>Token消耗: {{ testResult.tokens_used }}</small></p>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="testDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="runTest" :loading="testing">
          运行测试
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/date'
import api from '@/utils/api'

// 数据状态
const activeTab = ref('agents')
const agentsLoading = ref(false)
const functionsLoading = ref(false)
const logsLoading = ref(false)
const submitting = ref(false)
const testing = ref(false)

// 数据
const agents = ref([])
const functions = ref([])
const logs = ref([])
const systemFunctions = ref([])
const systemFunctionsLoading = ref(false)
const stats = reactive({
  total_agents: 0,
  active_agents: 0,
  total_functions: 0,
  active_functions: 0,
  total_calls: 0,
  success_calls: 0,
  failed_calls: 0,
  today_calls: 0
})

// 对话框状态
const agentDialogVisible = ref(false)
const functionDialogVisible = ref(false)
const logDetailDialogVisible = ref(false)
const testDialogVisible = ref(false)
const isEditAgent = ref(false)
const isEditFunction = ref(false)

// 表单引用
const agentFormRef = ref()
const functionFormRef = ref()

// 智能体表单
const agentForm = reactive({
  name: '',
  description: '',
  provider: 'openai',
  model_name: '',
  system_prompt: '',
  temperature: 0.7,
  max_tokens: 4000,
  is_active: true
})

// AI功能表单
const functionForm = reactive({
  name: '',
  description: '',
  function_type: 'text_generation',
  agent_id: null,
  is_active: true
})

// 日志过滤器
const logFilters = reactive({
  function_id: null,
  status: null
})

// 分页
const logsPagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 选中的日志
const selectedLog = ref(null)

// 测试相关
const testingFunction = ref(null)
const testInput = ref('')
const testResult = ref(null)

// 表单验证规则
const agentFormRules = {
  name: [{ required: true, message: '请输入智能体名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入描述', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择模型提供商', trigger: 'change' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  system_prompt: [{ required: true, message: '请输入系统提示词', trigger: 'blur' }]
}

const functionFormRules = {
  name: [{ required: true, message: '请输入功能名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入描述', trigger: 'blur' }],
  function_type: [{ required: true, message: '请选择功能类型', trigger: 'change' }]
}

// 计算属性
const successRate = computed(() => {
  if (stats.total_calls === 0) return 0
  return Math.round((stats.success_calls / stats.total_calls) * 100)
})

const activeAgents = computed(() => {
  return agents.value.filter(agent => agent.is_active)
})

// 格式化方法
const formatProvider = (provider) => {
  const map = {
    openai: 'OpenAI',
    claude: 'Claude',
    gemini: 'Gemini',
    other: '其他'
  }
  return map[provider] || provider
}

const formatFunctionType = (type) => {
  const map = {
    text_generation: '文本生成',
    text_analysis: '文本分析',
    translation: '翻译',
    summarization: '摘要',
    qa: '问答',
    other: '其他'
  }
  return map[type] || type
}

const formatStatus = (status) => {
  const map = {
    success: '成功',
    failed: '失败',
    pending: '进行中'
  }
  return map[status] || status
}

const getProviderTagType = (provider) => {
  const map = {
    openai: 'primary',
    claude: 'success',
    gemini: 'warning',
    other: 'info'
  }
  return map[provider] || 'info'
}

const getFunctionTypeTagType = (type) => {
  const map = {
    text_generation: 'primary',
    text_analysis: 'success',
    translation: 'warning',
    summarization: 'info',
    qa: 'danger',
    other: 'info'
  }
  return map[type] || 'info'
}

const getStatusTagType = (status) => {
  const map = {
    success: 'success',
    failed: 'danger',
    pending: 'warning'
  }
  return map[status] || 'info'
}

const getCategoryTagType = (category) => {
  const map = {
    '文本分析': 'primary',
    '内容生成': 'success',
    '数据分析': 'warning',
    '问答系统': 'info'
  }
  return map[category] || 'info'
}

const formatCategory = (category) => {
  return category || '未分类'
}

const getResponseTime = (startTime, endTime) => {
  const start = new Date(startTime)
  const end = new Date(endTime)
  return end.getTime() - start.getTime()
}

// API调用方法
const fetchStats = async () => {
  try {
    const response = await api.get('/ai/stats')
    Object.assign(stats, response.data)
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

const fetchAgents = async () => {
  agentsLoading.value = true
  try {
    const response = await api.get('/ai/agents')
    agents.value = response.data || []
  } catch (error) {
    ElMessage.error('获取智能体列表失败')
  } finally {
    agentsLoading.value = false
  }
}

const fetchFunctions = async () => {
  functionsLoading.value = true
  try {
    const response = await api.get('/ai/functions')
    functions.value = response.data || []
  } catch (error) {
    ElMessage.error('获取AI功能列表失败')
  } finally {
    functionsLoading.value = false
  }
}

const fetchLogs = async () => {
  logsLoading.value = true
  try {
    const params = {
      page: logsPagination.page,
      size: logsPagination.size,
      ...logFilters
    }
    
    const response = await api.get('/ai/logs', { params })
    logs.value = response.data.items || []
    logsPagination.total = response.data.total || 0
  } catch (error) {
    ElMessage.error('获取调用日志失败')
  } finally {
    logsLoading.value = false
  }
}

// 智能体操作
const showCreateAgentDialog = () => {
  isEditAgent.value = false
  resetAgentForm()
  agentDialogVisible.value = true
}

const editAgent = (agent) => {
  isEditAgent.value = true
  Object.assign(agentForm, agent)
  agentDialogVisible.value = true
}

const viewAgent = (agent) => {
  ElMessageBox.alert(
    `<p><strong>名称：</strong>${agent.name}</p>
     <p><strong>描述：</strong>${agent.description}</p>
     <p><strong>提供商：</strong>${formatProvider(agent.provider)}</p>
     <p><strong>模型：</strong>${agent.model_name}</p>
     <p><strong>系统提示词：</strong></p>
     <div style="max-height: 200px; overflow-y: auto; background: #f5f5f5; padding: 10px; border-radius: 4px;">${agent.system_prompt}</div>`,
    '智能体详情',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '关闭'
    }
  )
}

const deleteAgent = async (agent) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除智能体 "${agent.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/ai/agents/${agent.id}`)
    ElMessage.success('删除成功')
    fetchAgents()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const resetAgentForm = () => {
  Object.assign(agentForm, {
    name: '',
    description: '',
    provider: 'openai',
    model_name: '',
    system_prompt: '',
    temperature: 0.7,
    max_tokens: 4000,
    is_active: true
  })
  agentFormRef.value?.clearValidate()
}

const submitAgentForm = async () => {
  try {
    await agentFormRef.value.validate()
    submitting.value = true
    
    if (isEditAgent.value) {
      await api.put(`/ai/agents/${agentForm.id}`, agentForm)
      ElMessage.success('更新成功')
    } else {
      await api.post('/ai/agents', agentForm)
      ElMessage.success('创建成功')
    }
    
    agentDialogVisible.value = false
    fetchAgents()
    fetchStats()
  } catch (error) {
    ElMessage.error(isEditAgent.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

// AI功能操作
const showCreateFunctionDialog = () => {
  isEditFunction.value = false
  resetFunctionForm()
  functionDialogVisible.value = true
}

const editFunction = (func) => {
  isEditFunction.value = true
  Object.assign(functionForm, func)
  functionDialogVisible.value = true
}

const deleteFunction = async (func) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除AI功能 "${func.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/ai/functions/${func.id}`)
    ElMessage.success('删除成功')
    fetchFunctions()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const resetFunctionForm = () => {
  Object.assign(functionForm, {
    name: '',
    description: '',
    function_type: 'text_generation',
    agent_id: null,
    is_active: true
  })
  functionFormRef.value?.clearValidate()
}

const submitFunctionForm = async () => {
  try {
    await functionFormRef.value.validate()
    submitting.value = true
    
    if (isEditFunction.value) {
      await api.put(`/ai/functions/${functionForm.id}`, functionForm)
      ElMessage.success('更新成功')
    } else {
      await api.post('/ai/functions', functionForm)
      ElMessage.success('创建成功')
    }
    
    functionDialogVisible.value = false
    fetchFunctions()
    fetchStats()
  } catch (error) {
    ElMessage.error(isEditFunction.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

// 测试功能
const testFunction = (func) => {
  testingFunction.value = func
  testInput.value = ''
  testResult.value = null
  testDialogVisible.value = true
}

const runTest = async () => {
  if (!testInput.value.trim()) {
    ElMessage.warning('请输入测试内容')
    return
  }
  
  testing.value = true
  try {
    const response = await api.post('/ai/call', {
      function_id: testingFunction.value.id,
      input_text: testInput.value
    })
    testResult.value = response.data
    ElMessage.success('测试完成')
  } catch (error) {
    ElMessage.error('测试失败')
  } finally {
    testing.value = false
  }
}

// 日志操作
const viewLogDetail = (log) => {
  selectedLog.value = log
  logDetailDialogVisible.value = true
}

// 系统功能配置操作
const fetchSystemFunctions = async () => {
  systemFunctionsLoading.value = true
  try {
    // 定义系统内置的AI功能点
    systemFunctions.value = [
      {
        id: 'emotion_analysis',
        name: '情感分析',
        description: '分析用户日报中的情感状态，识别积极、消极或中性情绪',
        category: '文本分析',
        endpoint: '/api/ai/emotion',
        current_agent_id: null,
        current_agent_name: '未配置',
        is_enabled: true
      },
      {
        id: 'reflection_generation',
        name: '反思生成',
        description: '基于用户日报内容生成深度反思和改进建议',
        category: '内容生成',
        endpoint: '/api/ai/reflection',
        current_agent_id: null,
        current_agent_name: '未配置',
        is_enabled: true
      },
      {
        id: 'task_analysis',
        name: '任务分析',
        description: '分析任务完成情况，识别效率瓶颈和改进点',
        category: '数据分析',
        endpoint: '/api/ai/analytics',
        current_agent_id: null,
        current_agent_name: '未配置',
        is_enabled: true
      },
      {
        id: 'report_summary',
        name: '报告总结',
        description: '自动生成团队周报和月报摘要',
        category: '内容生成',
        endpoint: '/api/ai/summary',
        current_agent_id: null,
        current_agent_name: '未配置',
        is_enabled: true
      },
      {
        id: 'knowledge_qa',
        name: '知识问答',
        description: '基于项目知识库回答用户问题',
        category: '问答系统',
        endpoint: '/api/ai/qa',
        current_agent_id: null,
        current_agent_name: '未配置',
        is_enabled: false
      },
      {
        id: 'data_insights',
        name: '数据洞察',
        description: '分析工作数据，提供业务洞察和建议',
        category: '数据分析',
        endpoint: '/api/ai/insights',
        current_agent_id: null,
        current_agent_name: '未配置',
        is_enabled: false
      }
    ]
    
    // 获取当前配置的智能体信息
    const response = await api.get('/ai/system-config')
    const configs = response.data || {}
    
    // 更新当前配置的智能体信息
    systemFunctions.value.forEach(func => {
      const config = configs[func.id]
      if (config) {
        func.current_agent_id = config.agent_id
        func.current_agent_name = config.agent_name || '未配置'
        func.is_enabled = config.is_enabled !== false
      }
    })
  } catch (error) {
    console.error('获取系统功能配置失败:', error)
    ElMessage.error('获取系统功能配置失败')
  } finally {
    systemFunctionsLoading.value = false
  }
}

const updateSystemFunctionAgent = async (functionId, agentId) => {
  try {
    await api.post('/ai/system-config', {
      function_id: functionId,
      agent_id: agentId
    })
    
    // 更新本地数据
    const func = systemFunctions.value.find(f => f.id === functionId)
    if (func) {
      func.current_agent_id = agentId
      const agent = agents.value.find(a => a.id === agentId)
      func.current_agent_name = agent ? agent.name : '未配置'
    }
    
    ElMessage.success('配置更新成功')
  } catch (error) {
    ElMessage.error('配置更新失败')
  }
}

const toggleSystemFunction = async (functionId, enabled) => {
  try {
    await api.post('/ai/system-config', {
      function_id: functionId,
      is_enabled: enabled
    })
    
    // 更新本地数据
    const func = systemFunctions.value.find(f => f.id === functionId)
    if (func) {
      func.is_enabled = enabled
    }
    
    ElMessage.success(enabled ? '功能已启用' : '功能已禁用')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const testSystemFunction = async (func) => {
  try {
    if (!func.current_agent_id) {
      ElMessage.warning('请先为该功能配置智能体')
      return
    }
    
    const testData = {
      emotion_analysis: '今天工作很顺利，完成了所有任务，心情不错。',
      reflection_generation: '今天遇到了一些技术难题，花了很多时间调试。',
      task_analysis: '完成了3个任务，其中1个超时，2个按时完成。',
      report_summary: '本周团队完成了项目的核心功能开发。',
      knowledge_qa: '如何优化数据库查询性能？',
      data_insights: '用户活跃度数据：周一100人，周二120人，周三95人。'
    }
    
    const response = await api.post('/ai/test-function', {
      function_id: func.id,
      input_text: testData[func.id] || '测试输入内容'
    })
    
    ElMessageBox.alert(
      `<div style="max-height: 300px; overflow-y: auto;">
        <p><strong>测试结果：</strong></p>
        <div style="background: #f5f5f5; padding: 10px; border-radius: 4px; margin: 10px 0;">${response.data.output_text}</div>
        <p><small>Token消耗: ${response.data.tokens_used || 0}</small></p>
      </div>`,
      '功能测试结果',
      {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '关闭'
      }
    )
  } catch (error) {
    ElMessage.error('测试失败')
  }
}

// 初始化
onMounted(() => {
  fetchStats()
  fetchAgents()
  fetchFunctions()
  fetchLogs()
  fetchSystemFunctions()
})
</script>

<style scoped>
.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 20px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-sub {
  font-size: 12px;
  color: #C0C4CC;
}

.main-tabs {
  margin-top: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.text-ellipsis {
  display: inline-block;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-detail {
  margin-top: 16px;
}

.log-content {
  margin-top: 20px;
}

.log-content h4 {
  margin: 16px 0 8px 0;
  color: #303133;
}

.content-box {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
}

.content-box.error {
  background: #fef0f0;
  border-color: #fbc4c4;
  color: #f56c6c;
}

.test-result {
  margin-top: 16px;
}

@media (max-width: 768px) {
  .stats-overview {
    grid-template-columns: 1fr;
  }
  
  .header-actions {
    flex-direction: column;
    gap: 8px;
  }
}
</style>