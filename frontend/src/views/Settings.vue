<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">系统设置</h1>
      <p class="page-description">配置系统参数和AI服务</p>
    </div>
    
    <!-- AI配置 -->
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>AI服务配置</span>
        </div>
      </template>
      
      <el-form
        ref="aiFormRef"
        :model="aiSettings"
        :rules="aiFormRules"
        label-width="120px"
      >
        <el-form-item label="API提供商" prop="provider">
          <el-select v-model="aiSettings.provider" placeholder="选择AI服务提供商">
            <el-option label="OpenRouter" value="openrouter" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="Claude" value="claude" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="API密钥" prop="api_key">
          <el-input
            v-model="aiSettings.api_key"
            type="password"
            placeholder="请输入API密钥"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="API基础URL" prop="base_url">
          <el-input
            v-model="aiSettings.base_url"
            placeholder="API基础URL（可选）"
          />
        </el-form-item>
        
        <el-form-item label="默认模型" prop="default_model">
          <el-select
            v-model="aiSettings.default_model"
            placeholder="选择默认模型"
            filterable
            allow-create
          >
            <el-option
              v-for="model in availableModels"
              :key="model.value"
              :label="model.label"
              :value="model.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="最大Token数" prop="max_tokens">
          <el-input-number
            v-model="aiSettings.max_tokens"
            :min="100"
            :max="8000"
            :step="100"
            placeholder="最大Token数"
          />
        </el-form-item>
        
        <el-form-item label="温度参数" prop="temperature">
          <el-slider
            v-model="aiSettings.temperature"
            :min="0"
            :max="2"
            :step="0.1"
            show-input
            :input-size="'small'"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveAISettings" :loading="saving">
            保存配置
          </el-button>
          <el-button @click="testConnection" :loading="testing">
            测试连接
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 系统配置 -->
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>系统配置</span>
        </div>
      </template>
      
      <el-form
        ref="systemFormRef"
        :model="systemSettings"
        :rules="systemFormRules"
        label-width="120px"
      >
        <el-form-item label="系统名称" prop="system_name">
          <el-input v-model="systemSettings.system_name" placeholder="系统名称" />
        </el-form-item>
        
        <el-form-item label="时区设置" prop="timezone">
          <el-select v-model="systemSettings.timezone" placeholder="选择时区">
            <el-option label="北京时间 (UTC+8)" value="Asia/Shanghai" />
            <el-option label="东京时间 (UTC+9)" value="Asia/Tokyo" />
            <el-option label="纽约时间 (UTC-5)" value="America/New_York" />
            <el-option label="伦敦时间 (UTC+0)" value="Europe/London" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="语言设置" prop="language">
          <el-select v-model="systemSettings.language" placeholder="选择语言">
            <el-option label="简体中文" value="zh-CN" />
            <el-option label="English" value="en-US" />
            <el-option label="日本語" value="ja-JP" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="自动分析" prop="auto_analysis">
          <el-switch
            v-model="systemSettings.auto_analysis"
            active-text="开启"
            inactive-text="关闭"
          />
          <div class="form-help-text">
            开启后，系统将自动对新提交的日报进行AI分析
          </div>
        </el-form-item>
        
        <el-form-item label="数据保留期" prop="data_retention_days">
          <el-input-number
            v-model="systemSettings.data_retention_days"
            :min="30"
            :max="365"
            placeholder="数据保留天数"
          />
          <div class="form-help-text">
            超过此天数的数据将被自动清理
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveSystemSettings" :loading="saving">
            保存配置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 数据管理 -->
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>数据管理</span>
        </div>
      </template>
      
      <div class="data-management">
        <div class="management-item">
          <div class="item-info">
            <h4>导出数据</h4>
            <p>导出所有任务和日报数据</p>
          </div>
          <el-button type="primary" @click="exportData" :loading="exporting">
            导出数据
          </el-button>
        </div>
        
        <div class="management-item">
          <div class="item-info">
            <h4>清理缓存</h4>
            <p>清理系统缓存和临时文件</p>
          </div>
          <el-button @click="clearCache" :loading="clearing">
            清理缓存
          </el-button>
        </div>
        
        <div class="management-item">
          <div class="item-info">
            <h4>重置设置</h4>
            <p>将所有设置恢复为默认值</p>
          </div>
          <el-button type="danger" @click="resetSettings">
            重置设置
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

// 数据
const saving = ref(false)
const testing = ref(false)
const exporting = ref(false)
const clearing = ref(false)

// 表单引用
const aiFormRef = ref()
const systemFormRef = ref()

// AI设置
const aiSettings = reactive({
  provider: 'openrouter',
  api_key: '',
  base_url: 'https://openrouter.ai/api/v1',
  default_model: 'openai/gpt-5',
  max_tokens: 2000,
  temperature: 0.7
})

// 系统设置
const systemSettings = reactive({
  system_name: 'KillerApp',
  timezone: 'Asia/Shanghai',
  language: 'zh-CN',
  auto_analysis: true,
  data_retention_days: 90
})

// 可用模型列表（按照开发文档要求）
const availableModels = ref([
  { label: 'Google Gemini 2.5 Pro', value: 'google/gemini-2.5-pro' },
  { label: 'OpenAI GPT-5', value: 'openai/gpt-5' },
  { label: 'DeepSeek Chat v3.1', value: 'deepseek/deepseek-chat-v3.1' }
])

// 表单验证规则
const aiFormRules = {
  provider: [
    { required: true, message: '请选择API提供商', trigger: 'change' }
  ],
  api_key: [
    { required: true, message: '请输入API密钥', trigger: 'blur' }
  ],
  default_model: [
    { required: true, message: '请选择默认模型', trigger: 'change' }
  ]
}

const systemFormRules = {
  system_name: [
    { required: true, message: '请输入系统名称', trigger: 'blur' }
  ],
  timezone: [
    { required: true, message: '请选择时区', trigger: 'change' }
  ],
  language: [
    { required: true, message: '请选择语言', trigger: 'change' }
  ]
}

// 获取设置
const fetchSettings = async () => {
  try {
    // 加载AI设置
    const aiResponse = await api.get('/settings/ai')
    Object.assign(aiSettings, {
      provider: aiResponse.data.provider,
      api_key: aiResponse.data.api_key,
      base_url: aiResponse.data.base_url,
      default_model: aiResponse.data.model_name,
      max_tokens: aiResponse.data.max_tokens,
      temperature: aiResponse.data.temperature
    })
    
    // 加载系统设置
    const systemResponse = await api.get('/settings/system')
    Object.assign(systemSettings, {
      system_name: systemResponse.data.system_name,
      timezone: systemResponse.data.timezone,
      language: systemResponse.data.language,
      auto_analysis: systemResponse.data.auto_analysis,
      data_retention_days: systemResponse.data.data_retention_days
    })
  } catch (error) {
    console.error('获取设置失败:', error)
  }
}

// 保存AI设置
const saveAISettings = async () => {
  if (!aiFormRef.value) return
  
  try {
    await aiFormRef.value.validate()
    saving.value = true
    
    const aiData = {
      provider: aiSettings.provider,
      api_key: aiSettings.api_key,
      base_url: aiSettings.base_url,
      model_name: aiSettings.default_model,
      max_tokens: aiSettings.max_tokens,
      temperature: aiSettings.temperature
    }
    
    await api.put('/settings/ai', aiData)
    ElMessage.success('AI设置保存成功')
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('保存失败')
    }
  } finally {
    saving.value = false
  }
}

// 保存系统设置
const saveSystemSettings = async () => {
  if (!systemFormRef.value) return
  
  try {
    await systemFormRef.value.validate()
    saving.value = true
    
    const systemData = {
      system_name: systemSettings.system_name,
      timezone: systemSettings.timezone,
      language: systemSettings.language,
      auto_analysis: systemSettings.auto_analysis,
      data_retention_days: systemSettings.data_retention_days
    }
    
    await api.put('/settings/system', systemData)
    ElMessage.success('系统设置保存成功')
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('保存失败')
    }
  } finally {
    saving.value = false
  }
}

// 测试连接
const testConnection = async () => {
  if (!aiSettings.api_key) {
    ElMessage.warning('请先输入API密钥')
    return
  }
  
  testing.value = true
  try {
    const testData = {
      provider: aiSettings.provider,
      api_key: aiSettings.api_key,
      base_url: aiSettings.base_url,
      model_name: aiSettings.default_model,
      max_tokens: 100,
      temperature: aiSettings.temperature
    }
    
    const response = await api.post('/settings/ai/test', testData)
    
    if (response.data.success) {
      ElMessage.success(`连接测试成功: ${response.data.response}`)
    } else {
      ElMessage.error(`连接测试失败: ${response.data.message}`)
    }
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(`连接测试失败: ${error.response.data.detail}`)
    } else {
      ElMessage.error('连接测试失败')
    }
  } finally {
    testing.value = false
  }
}

// 导出数据
const exportData = async () => {
  exporting.value = true
  try {
    const response = await api.get('/settings/export')
    ElMessage.success(response.data.message)
  } catch (error) {
    ElMessage.error('导出数据失败')
    console.error('Export data error:', error)
  } finally {
    exporting.value = false
  }
}

// 清理缓存
const clearCache = async () => {
  clearing.value = true
  try {
    await api.post('/settings/clear-cache')
    ElMessage.success('缓存清理成功')
  } catch (error) {
    ElMessage.error('清理缓存失败')
    console.error('Clear cache error:', error)
  } finally {
    clearing.value = false
  }
}

// 重置设置
const resetSettings = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置所有设置吗？此操作不可恢复。',
      '确认重置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.post('/settings/reset')
    ElMessage.success('设置重置成功')
    
    // 重新加载设置
    await fetchSettings()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('设置重置失败')
      console.error('Reset settings error:', error)
    }
  }
}

// 初始化
onMounted(() => {
  fetchSettings()
})
</script>

<style scoped>
.form-help-text {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.data-management {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.management-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
}

.item-info h4 {
  margin: 0 0 4px 0;
  color: #303133;
}

.item-info p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

@media (max-width: 768px) {
  .management-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>