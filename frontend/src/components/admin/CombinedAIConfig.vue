<template>
  <div>
    <div class="list-header">
      <h3>配置（智能体与功能点）</h3>
      <div>
        <el-button type="primary" @click="openCreateAgent()">新增智能体</el-button>
        <el-button link @click="init">刷新</el-button>
      </div>
    </div>

    <el-alert type="info" show-icon class="mb-12" :closable="false">
      在此统一创建功能点、创建智能体，并为功能点分配智能体。
    </el-alert>

    <el-table :data="features" v-loading="loading" border style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" min-width="180" />
      <el-table-column prop="description" label="描述" min-width="220" />
      <el-table-column prop="type" label="类型" width="140">
        <template #default="{ row }">
          <el-tag>{{ row.type || 'custom' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="关联智能体" min-width="260">
        <template #default="{ row }">
          <div class="agent-assign">
            <el-select v-model="row.agent_id" placeholder="选择智能体" style="width: 220px" @change="(val)=>onAgentSelect(row, val)" filterable>
              <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id" />
              <el-option :label="'新建智能体…'" :value="CREATE_OPTION_VALUE" />
            </el-select>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="启用" width="120">
        <template #default="{ row }">
          <el-switch v-model="row.is_active" @change="(val)=>updateActive(row, val)" />
        </template>
      </el-table-column>
    </el-table>

    

    <!-- 新增智能体 -->
    <el-dialog v-model="agentVisible" :title="agentEditing ? '编辑智能体' : '新增智能体'" width="680px">
      <el-form :model="agentForm" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="agentForm.name" placeholder="Agent 名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="agentForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="提供商">
          <el-select v-model="agentForm.provider" placeholder="选择提供商">
            <el-option v-for="opt in providerOpts" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="作用">
          <el-select v-model="purpose" placeholder="选择用途" @change="onPurposeChange">
            <el-option v-for="opt in purposeOpts" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型">
          <el-select v-model="agentForm.model_name" placeholder="选择模型" filterable allow-create default-first-option>
            <el-option v-for="m in modelOpts" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="System Prompt">
          <el-input v-model="agentForm.system_prompt" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="绑定功能点">
          <el-select v-model="bindFeatureValues" multiple placeholder="选择要绑定的功能点" style="width: 100%" filterable>
            <el-option v-for="opt in featureOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button link @click="quickBind('personal')">快速绑定：个人数据洞察</el-button>
          <el-button link @click="quickBind('team')">快速绑定：团队数据洞察</el-button>
        </el-form-item>
        <el-form-item label="温度">
          <el-input-number v-model="agentForm.temperature" :min="0" :max="2" :step="0.1" />
        </el-form-item>
        <el-form-item label="Max Tokens">
          <el-input-number v-model="agentForm.max_tokens" :min="256" :step="128" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="agentForm.is_active">
            <el-option label="启用" :value="true" />
            <el-option label="关闭" :value="false" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="agentVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreateAgent">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

// 常量
const CREATE_OPTION_VALUE = '__create__'

// 状态
const loading = ref(false)
const features = ref([])
const agents = ref([])

// 功能点（仅绑定，不新增）

// 智能体创建
const agentVisible = ref(false)
const agentEditing = ref(false)
const agentForm = ref({
  name: '', description: '', provider: 'openai', model_name: '', system_prompt: '', temperature: 0.7, max_tokens: 1024, is_active: true,
})
const assignFeatureId = ref(null)
// 绑定功能点选择，支持真实ID与占位值（当功能点尚未创建时）
const bindFeatureValues = ref([])
const PSEUDO_PERSONAL = '__FEATURE_PERSONAL__'
const PSEUDO_TEAM = '__FEATURE_TEAM__'
const pseudoOptions = [
  { value: PSEUDO_PERSONAL, label: '个人数据洞察（固定选择）' },
  { value: PSEUDO_TEAM, label: '团队数据洞察（固定选择）' },
]
const featureOptions = computed(() => {
  const realOpts = (features.value || []).map(f => ({ value: f.id, label: f.name }))
  return [...realOpts, ...pseudoOptions]
})

// 作用下拉与模板
const purpose = ref('')
const purposeOpts = [
  { label: '通用对话', value: 'chat' },
  { label: '内容生成', value: 'content' },
  { label: '文本分析', value: 'analysis' },
  { label: '翻译', value: 'translate' },
  { label: '摘要', value: 'summarize' },
  { label: '问答', value: 'qa' },
]
const purposeTemplates = {
  chat: '你是一名友善且高效的助手，擅长通用对话与任务协助。请用简洁、明确的方式回答用户问题。',
  content: '你是一名资深内容创作者。根据用户意图生成高质量文案，保持结构清晰、语气自然，并给出可执行的建议。',
  analysis: '你是一名文本分析专家。请从事实准确性、结构逻辑、情感倾向等维度分析输入文本，并给出客观结论。',
  translate: '你是一名专业翻译。保持原文含义不变，语言自然流畅；必要时可解释关键术语的译法选择。',
  summarize: '你是一名摘要助手。请在忠实原文的前提下，生成结构化要点摘要，突出结论与行动项。',
  qa: '你是一名知识问答助手。请先给出直接答案，再提供简短的依据或出处，避免无根据的臆测。',
}
const onPurposeChange = () => {
  if (!agentForm.value.system_prompt) {
    agentForm.value.system_prompt = purposeTemplates[purpose.value] || ''
  }
}

// 提供商与模型下拉
const providerOpts = [
  { label: 'OpenRouter', value: 'openrouter' },
  { label: 'OpenAI', value: 'openai' },
  { label: 'Claude', value: 'claude' },
  { label: 'Gemini', value: 'gemini' },
  { label: 'DeepSeek', value: 'deepseek' },
]
const MODEL_PRESETS = {
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1', 'gpt-4.1-mini', 'o4-mini'],
  claude: ['claude-3-5-sonnet-latest', 'claude-3-5-haiku-latest', 'claude-3-opus-latest'],
  gemini: ['gemini-1.5-pro', 'gemini-1.5-flash'],
  deepseek: ['deepseek-chat', 'deepseek-reasoner'],
  openrouter: ['openrouter/anthropic/claude-3-5-sonnet', 'openrouter/google/gemini-1.5-pro', 'openrouter/openai/gpt-4o'],
}
const modelOpts = computed(() => MODEL_PRESETS[agentForm.value.provider] || [])
watch(() => agentForm.value.provider, () => {
  if (modelOpts.value.length && !modelOpts.value.includes(agentForm.value.model_name)) {
    agentForm.value.model_name = modelOpts.value[0]
  }
})

// 数据加载
const fetchAgents = async () => {
  try {
    const { data } = await api.get('/api/v1/ai/agents')
    agents.value = data || []
  } catch (err) {
    console.error(err)
    ElMessage.error('获取智能体失败')
  }
}

const fetchFeatures = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/api/v1/ai/functions')
    features.value = (data || []).map((f) => ({
      id: f.id,
      name: f.name,
      description: f.description,
      type: f.function_type ?? 'custom',
      agent_id: f.agent_id ?? null,
      is_active: f.is_active ?? true,
    }))
  } catch (err2) {
    console.error(err2)
    ElMessage.error('获取功能点失败')
  } finally {
    loading.value = false
  }
}

// 事件：下拉选择智能体
const onAgentSelect = async (row, val) => {
  if (val === CREATE_OPTION_VALUE) {
    assignFeatureId.value = row.id
    openCreateAgent()
    // 重置行选择，避免显示字符串
    row.agent_id = null
    return
  }
  await updateAgent(row, val)
}

// 更新功能绑定
const updateAgent = async (row, val) => {
  try {
    const body = { agent_id: val }
    await api.put(`/api/v1/ai/functions/${row.id}`, body)
    ElMessage.success('已更新关联智能体')
  } catch (err) {
    console.error(err)
    ElMessage.error('更新失败')
  }
}

// 更新功能启用
const updateActive = async (row, val) => {
  try {
    const body = { is_active: val }
    await api.put(`/api/v1/ai/functions/${row.id}`, body)
    ElMessage.success('状态已更新')
  } catch (err) {
    console.error(err)
    ElMessage.error('更新失败')
  }
}

// 删除创建功能点相关逻辑（按需求：不新增，只绑定）

// 打开/提交：创建智能体
const openCreateAgent = () => {
  Object.assign(agentForm.value, { name: '', description: '', provider: 'openai', model_name: '', system_prompt: '', temperature: 0.7, max_tokens: 1024, is_active: true })
  purpose.value = ''
  agentVisible.value = true
  bindFeatureValues.value = []
}
const submitCreateAgent = async () => {
  try {
    const payload = {
      name: agentForm.value.name,
      description: agentForm.value.description,
      provider: agentForm.value.provider,
      model_name: agentForm.value.model_name,
      system_prompt: agentForm.value.system_prompt,
      temperature: agentForm.value.temperature,
      max_tokens: agentForm.value.max_tokens,
      is_active: agentForm.value.is_active,
    }
    const { data } = await api.post('/api/v1/ai/agents', payload)
    ElMessage.success('智能体创建成功')
    agentVisible.value = false
    await fetchAgents()
    // 若来自某个功能的“新建智能体”，自动绑定
    if (assignFeatureId.value) {
      const createdId = data?.id || (agents.value[0]?.id) // 防御：取返回id
      const target = features.value.find(f => f.id === assignFeatureId.value)
      assignFeatureId.value = null
      if (target && createdId) {
        target.agent_id = createdId
        await updateAgent(target, createdId)
      }
    }
    // 批量绑定到选中的功能点
    const createdId = data?.id
    if (createdId && bindFeatureValues.value.length) {
      // 仅绑定真实存在的功能点（数值ID），占位项忽略
      for (const val of bindFeatureValues.value) {
        if (typeof val === 'number') {
          const target = features.value.find(f => f.id === val)
          if (target) {
            target.agent_id = createdId
            await updateAgent(target, createdId)
          }
        }
      }
      bindFeatureValues.value = []
      ElMessage.success('已为选定功能点绑定该智能体')
      await fetchFeatures()
    }
  } catch (err) {
    console.error(err)
    ElMessage.error('保存失败')
  }
}

// 快速绑定功能点：若存在则选中其ID；若不存在，则加入“固定选择”的占位项，不再提示创建
const ensureFeatureOrPseudo = (name) => {
  const existing = features.value.find(f => f.name === name)
  if (existing) return existing.id
  return name === '个人数据洞察' ? PSEUDO_PERSONAL : PSEUDO_TEAM
}
const quickBind = (which) => {
  const val = which === 'personal'
    ? ensureFeatureOrPseudo('个人数据洞察')
    : ensureFeatureOrPseudo('团队数据洞察')
  if (!bindFeatureValues.value.includes(val)) {
    bindFeatureValues.value.push(val)
    ElMessage.success('已添加到绑定列表')
  }
}

const init = async () => {
  await Promise.all([fetchAgents(), fetchFeatures()])
}

onMounted(init)
</script>

<style scoped>
.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.mb-12 { margin-bottom: 12px; }
.agent-assign { display: flex; gap: 8px; align-items: center; }
</style>