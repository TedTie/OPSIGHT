<template>
  <div>
    <div class="list-header">
      <h3>调用日志</h3>
      <div class="filters">
        <el-select v-model="filters.status" placeholder="状态" clearable @change="fetchLogs" style="width: 140px">
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failed" />
          <el-option label="进行中" value="pending" />
        </el-select>
        <el-select v-model="filters.function_id" placeholder="功能点" clearable @change="fetchLogs" style="width: 180px">
          <el-option v-for="f in functions" :key="f.id" :label="f.name" :value="f.id" />
        </el-select>
        <el-button :icon="Refresh" @click="fetchLogs">刷新</el-button>
      </div>
    </div>

    <el-table :data="logs" v-loading="loading" border style="width: 100%">
      <el-table-column prop="created_at" label="时间" width="180">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column prop="function_name" label="功能点" width="160" />
      <el-table-column prop="user_name" label="用户" width="120" />
      <el-table-column label="输入" min-width="220">
        <template #default="{ row }">
          <el-tooltip :content="row.input_text" placement="top">
            <span class="ellipsis">{{ row.input_text }}</span>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="tokens_used" label="Tokens" width="100" />
      <el-table-column label="耗时" width="100">
        <template #default="{ row }">
          <span v-if="row.completed_at && row.created_at">{{ durationMs(row) }}ms</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link size="small" @click="view(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="size"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchLogs"
        @current-change="fetchLogs"
      />
    </div>

    <el-dialog v-model="detailVisible" title="日志详情" width="720px">
      <div v-if="activeLog">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="时间">{{ formatDate(activeLog.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="功能点">{{ activeLog.function_name }}</el-descriptions-item>
          <el-descriptions-item label="用户">{{ activeLog.user_name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTag(activeLog.status)">{{ statusText(activeLog.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="Tokens">{{ activeLog.tokens_used || '-' }}</el-descriptions-item>
        </el-descriptions>
        <div class="log-content">
          <h4>输入</h4>
          <div class="content-box">{{ activeLog.input_text }}</div>
          <h4>输出</h4>
          <div class="content-box">{{ activeLog.output_text || '无' }}</div>
          <div v-if="activeLog.error_message">
            <h4>错误</h4>
            <div class="content-box error">{{ activeLog.error_message }}</div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Refresh from '~icons/tabler/refresh'
import api from '@/utils/api'

const loading = ref(false)
const logs = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const filters = ref({ status: '', function_id: '' })
const detailVisible = ref(false)
const activeLog = ref(null)
const functions = ref([])

const statusText = (s) => ({ success: '成功', failed: '失败', pending: '进行中' }[s] || s)
const statusTag = (s) => ({ success: 'success', failed: 'danger', pending: 'warning' }[s] || 'info')

const formatDate = (v) => new Date(v).toLocaleString()
const durationMs = (row) => new Date(row.completed_at).getTime() - new Date(row.created_at).getTime()

const fetchFunctions = async () => {
  try {
    const { data } = await api.get('/ai/functions')
    functions.value = data || []
  } catch {}
}

const fetchLogs = async () => {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.function_id) params.function_id = filters.value.function_id
    const { data } = await api.get('/ai/logs', { params })
    logs.value = data.items || []
    total.value = data.total || 0
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

const view = (row) => { activeLog.value = row; detailVisible.value = true }

onMounted(async () => {
  await Promise.all([fetchFunctions(), fetchLogs()])
})
</script>

<style scoped>
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.filters { display: flex; gap: 8px; align-items: center; }
.pagination { margin-top: 12px; display: flex; justify-content: flex-end; }
.ellipsis { display: inline-block; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.log-content { margin-top: 12px; }
.content-box { background: #f5f7fa; padding: 10px; border-radius: 6px; white-space: pre-wrap; }
.content-box.error { background: #fff1f0; }
</style>