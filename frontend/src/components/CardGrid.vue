<template>
  <div class="grid-container">
    <el-card class="content-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>指标概览</span>
        </div>
      </template>

      <div v-if="keys.length === 0" class="empty">暂无数据</div>
      <div v-else class="grid">
        <DataCard
          v-for="k in keys"
          :key="k"
          :metricKey="k"
          :title="metricDict[k]?.name || k"
          :unit="metricDict[k]?.unit || ''"
          :value="summaryData[k]"
          :isActive="activeMetricKey === k"
          @cardClick="emit('cardClick', k)"
          @aiClick="emit('aiClick', k)"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import DataCard from './DataCard.vue'

const props = defineProps({
  summaryData: { type: Object, required: true },
  activeMetricKey: { type: String, default: '' },
  visibleKeys: { type: Array, default: () => [] }
})
const emit = defineEmits(['cardClick', 'aiClick'])

// 指标字典（严格按需求的15项）
const metricDict = {
  task_completion_rate: { name: '任务完成率', unit: '%' },
  period_sales_amount: { name: '销售总额', unit: 'USD' },
  sales_achievement_rate: { name: '销售目标达成率', unit: '%' },
  period_new_sign_amount: { name: '新单金额', unit: 'USD' },
  new_sign_count: { name: '新单单量', unit: '单' },
  new_sign_achievement_rate: { name: '新单目标达成率', unit: '%' },
  period_referral_amount: { name: '转介绍金额', unit: 'USD' },
  referral_count: { name: '转介绍单量', unit: '单' },
  referral_achievement_rate: { name: '转介绍目标达成率', unit: '%' },
  period_total_renewal_amount: { name: '总续费金额', unit: 'USD' },
  total_renewal_achievement_rate: { name: '总续费目标达成率', unit: '%' },
  period_upgrade_amount: { name: '升舱金额', unit: 'USD' },
  upgrade_count: { name: '升舱单量', unit: '单' },
  upgrade_rate: { name: '升舱率', unit: '%' },
  report_submission_rate: { name: '日报提交率', unit: '%' }
}

const keys = computed(() => {
  const all = Object.keys(props.summaryData || {})
  if (props.visibleKeys && props.visibleKeys.length > 0) {
    return props.visibleKeys.filter(k => all.includes(k))
  }
  return all
})
</script>

<style scoped>
.grid-container { margin-top: 8px; }
.grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.empty { padding: 24px; color: #909399; text-align: center; }
.content-card { margin-bottom: 8px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
@media (max-width: 1200px) { .grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 900px) { .grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }
</style>