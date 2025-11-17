<template>
  <div>
    <div class="list-header">
      <h3>智能体列表</h3>
      <el-button type="primary" @click="openCreate">新增智能体</el-button>
    </div>

    <el-table :data="agents" v-loading="loading" border style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" min-width="160" />
      <el-table-column prop="provider" label="提供商" width="120" />
      <el-table-column prop="model_name" label="模型" min-width="160" />
      <el-table-column prop="is_active" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? '启用' : '未启用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑智能体' : '新增智能体'" width="680px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="Agent 名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="提供商">
          <el-select v-model="form.provider" placeholder="选择提供商">
            <el-option v-for="opt in providerOpts" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="作用">
          <el-select v-model="purpose" placeholder="选择用途" @change="onPurposeChange">
            <el-option v-for="opt in purposeOpts" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型">
          <el-select v-model="form.model_name" placeholder="选择模型" filterable allow-create default-first-option>
            <el-option v-for="m in modelOpts" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="System Prompt">
          <el-input v-model="form.system_prompt" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="温度">
          <el-input-number v-model="form.temperature" :min="0" :max="2" :step="0.1" />
        </el-form-item>
        <el-form-item label="Max Tokens">
          <el-input-number v-model="form.max_tokens" :min="256" :step="128" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.is_active">
            <el-option label="启用" :value="true" />
            <el-option label="关闭" :value="false" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const loading = ref(false)
const agents = ref([])
const dialogVisible = ref(false)
const editing = ref(false)
const currentId = ref(null)
const form = ref({
  name: '',
  description: '',
  provider: 'openai',
  model_name: '',
  system_prompt: '',
  temperature: 0.7,
  max_tokens: 1024,
  is_active: true,
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
  if (!form.value.system_prompt) {
    form.value.system_prompt = purposeTemplates[purpose.value] || ''
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
const modelOpts = computed(() => MODEL_PRESETS[form.value.provider] || [])
watch(() => form.value.provider, (val) => {
  if (modelOpts.value.length && !modelOpts.value.includes(form.value.model_name)) {
    form.value.model_name = modelOpts.value[0]
  }
})

const fetchAgents = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/ai/agents')
    agents.value = data || []
  } catch (err) {
    ElMessage.error('获取智能体列表失败')
    console.error(err)
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editing.value = false
  currentId.value = null
  Object.assign(form.value, {
    name: '', description: '', provider: 'openai', model_name: '', system_prompt: '', temperature: 0.7, max_tokens: 1024, is_active: true,
  })
  purpose.value = ''
  dialogVisible.value = true
}

const openEdit = (row) => {
  editing.value = true
  currentId.value = row.id
  Object.assign(form.value, row)
  dialogVisible.value = true
}

const submit = async () => {
  try {
    // 仅发送后端支持字段
    const payload = {
      name: form.value.name,
      description: form.value.description,
      provider: form.value.provider,
      model_name: form.value.model_name,
      system_prompt: form.value.system_prompt,
      temperature: form.value.temperature,
      max_tokens: form.value.max_tokens,
      is_active: form.value.is_active,
    }
    if (editing.value && currentId.value) {
      await api.put(`/ai/agents/${currentId.value}`, payload)
      ElMessage.success('更新成功')
    } else {
      await api.post('/ai/agents', payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchAgents()
  } catch (err) {
    ElMessage.error('保存失败')
    console.error(err)
  }
}

const remove = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除智能体「${row.name}」？`, '提示', { type: 'warning' })
    await api.delete(`/ai/agents/${row.id}`)
    ElMessage.success('删除成功')
    fetchAgents()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(err)
    }
  }
}

onMounted(fetchAgents)
</script>

<style scoped>
.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
</style>