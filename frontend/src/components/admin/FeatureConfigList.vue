<template>
  <div>
    <div class="list-header">
      <h3>功能点配置</h3>
      <div>
        <el-button type="primary" @click="openCreate">新增功能点</el-button>
        <el-button link @click="init">刷新</el-button>
      </div>
    </div>

    <el-alert type="info" show-icon class="mb-12" :closable="false">
      优先使用新接口 /ai/features；若不存在则回退到 /ai/functions。
    </el-alert>

    <el-table :data="features" v-loading="loading" border style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" min-width="180" />
      <el-table-column prop="description" label="描述" min-width="220" />
      <el-table-column prop="type" label="类型" width="140">
        <template #default="{ row }">
          <el-tag>{{ row.type || 'generic' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="关联智能体" min-width="220">
        <template #default="{ row }">
          <el-select v-model="row.agent_id" placeholder="选择智能体" @change="(val)=>updateAgent(row, val)" style="width: 200px">
            <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="启用" width="120">
        <template #default="{ row }">
          <el-switch v-model="row.is_active" @change="(val)=>updateActive(row, val)" />
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="createVisible" title="新增功能点" width="600px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="createForm.name" placeholder="如 个人数据洞察 / 团队数据洞察" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="createForm.function_type" placeholder="选择类型">
            <el-option v-for="opt in functionTypeOpts" :key="opt" :label="opt" :value="opt" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="关联智能体">
          <el-select v-model="createForm.agent_id" placeholder="选择智能体">
            <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="createForm.is_active" />
        </el-form-item>
        <el-form-item>
          <el-button link @click="quickSet('personal')">快速填充：个人数据洞察</el-button>
          <el-button link @click="quickSet('team')">快速填充：团队数据洞察</el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const loading = ref(false)
const usingFeaturesApi = ref(false)
const features = ref([])
const agents = ref([])
const createVisible = ref(false)
const createForm = ref({
  name: '',
  description: '',
  function_type: 'custom',
  agent_id: null,
  is_active: true,
})
const functionTypeOpts = ['reflection_generation','task_analysis','report_summary','knowledge_qa','custom']

const fetchAgents = async () => {
  try {
    const { data } = await api.get('/ai/agents')
    agents.value = data || []
  } catch (err) {
    console.error(err)
    ElMessage.error('获取智能体失败')
  }
}

const fetchFeatures = async () => {
  loading.value = true
  try {
    // 优先尝试新接口
    const { data } = await api.get('/ai/features')
    usingFeaturesApi.value = true
    features.value = (data || []).map((f) => ({
      id: f.id ?? f.feature_id ?? f.function_id,
      name: f.name,
      description: f.description,
      type: f.type ?? f.category ?? 'generic',
      agent_id: f.agent_id ?? null,
      is_active: f.is_active ?? true,
    }))
  } catch (err) {
    // 回退到旧接口 /ai/functions
    try {
      const { data } = await api.get('/ai/functions')
      usingFeaturesApi.value = false
      features.value = (data || []).map((f) => ({
        id: f.id,
        name: f.name,
        description: f.description,
        type: f.function_type ?? f.type ?? 'generic',
        agent_id: f.agent_id ?? null,
        is_active: f.is_active ?? true,
      }))
    } catch (err2) {
      console.error(err2)
      ElMessage.error('获取功能点失败')
    }
  } finally {
    loading.value = false
  }
}

const updateAgent = async (row, val) => {
  try {
    const body = { agent_id: val }
    if (usingFeaturesApi.value) {
      await api.put(`/ai/features/${row.id}`, body)
    } else {
      await api.put(`/ai/functions/${row.id}`, body)
    }
    ElMessage.success('已更新关联智能体')
  } catch (err) {
    console.error(err)
    ElMessage.error('更新失败')
  }
}

const updateActive = async (row, val) => {
  try {
    const body = { is_active: val }
    if (usingFeaturesApi.value) {
      await api.put(`/ai/features/${row.id}`, body)
    } else {
      await api.put(`/ai/functions/${row.id}`, body)
    }
    ElMessage.success('状态已更新')
  } catch (err) {
    console.error(err)
    ElMessage.error('更新失败')
  }
}

const openCreate = () => {
  Object.assign(createForm.value, { name: '', description: '', function_type: 'custom', agent_id: agents.value[0]?.id ?? null, is_active: true })
  createVisible.value = true
}

const submitCreate = async () => {
  try {
    const body = {
      name: createForm.value.name,
      description: createForm.value.description,
      function_type: createForm.value.function_type,
      agent_id: createForm.value.agent_id,
      is_active: createForm.value.is_active,
    }
    if (usingFeaturesApi.value) {
      try {
        await api.post('/ai/features', body)
      } catch (err) {
        // 若新接口不可用，回退
        await api.post('/ai/functions', body)
      }
    } else {
      await api.post('/ai/functions', body)
    }
    ElMessage.success('功能点创建成功')
    createVisible.value = false
    await fetchFeatures()
  } catch (err) {
    console.error(err)
    ElMessage.error('创建失败')
  }
}

const quickSet = (which) => {
  createForm.value.function_type = 'custom'
  if (which === 'personal') {
    createForm.value.name = '个人数据洞察'
    createForm.value.description = '针对个人视角的AI洞察功能'
  } else if (which === 'team') {
    createForm.value.name = '团队数据洞察'
    createForm.value.description = '针对团队视角的AI洞察功能'
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
</style>