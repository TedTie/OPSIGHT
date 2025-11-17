<template>
  <div class="page-container">
    <div class="page-header">
      <h2>AI 管理</h2>
      <p class="subtitle">统一管理智能体、功能点配置与调用日志</p>
    </div>

    <el-card class="stats-card" v-loading="statsLoading">
      <template #header>
        <div class="card-header">
          <span>概览统计</span>
          <el-button type="primary" link @click="loadStats">刷新</el-button>
        </div>
      </template>
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-value">{{ stats.total_agents }}</div>
          <div class="stat-label">智能体数量</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.total_features }}</div>
          <div class="stat-label">功能点数量</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.total_calls }}</div>
          <div class="stat-label">调用次数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ successRateDisplay }}%</div>
          <div class="stat-label">成功率</div>
        </div>
      </div>
    </el-card>

    <el-tabs type="border-card" class="mt-16">
      <el-tab-pane label="配置（智能体与功能点）">
        <CombinedAIConfig />
      </el-tab-pane>
      <el-tab-pane label="调用日志">
        <LogViewer />
      </el-tab-pane>
    </el-tabs>
  </div>
  
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import CombinedAIConfig from '@/components/admin/CombinedAIConfig.vue'
import LogViewer from '@/components/admin/LogViewer.vue'
import api from '@/utils/api'

const statsLoading = ref(false)
const stats = ref({
  total_agents: 0,
  total_features: 0,
  total_calls: 0,
  success_rate: 0,
})

const successRateDisplay = computed(() => {
  const val = Number(stats.value.success_rate || 0)
  // 保留一位小数，避免过多小数点
  return val.toFixed(1)
})

const loadStats = async () => {
  statsLoading.value = true
  try {
    const { data } = await api.get('/ai/stats')
    // 统一字段映射：兼容旧版返回（functions -> features）
    stats.value = {
      total_agents: data.total_agents ?? 0,
      total_features: data.total_features ?? data.total_functions ?? 0,
      total_calls: data.total_calls ?? 0,
      success_rate: data.success_rate ?? 0,
    }
  } catch (err) {
    ElMessage.error('获取统计信息失败')
    console.error(err)
  } finally {
    statsLoading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.page-container {
  padding: 16px;
}
.page-header {
  margin-bottom: 12px;
}
.subtitle {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.stats-card {
  margin-top: 8px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.stat-item {
  background: var(--el-fill-color-light);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
}
.stat-value {
  font-size: 20px;
  font-weight: 600;
}
.stat-label {
  margin-top: 6px;
  color: var(--el-text-color-secondary);
}
.mt-16 { margin-top: 16px; }
</style>