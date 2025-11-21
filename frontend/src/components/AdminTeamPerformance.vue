<template>
  <el-card class="team-performance-card" shadow="never">
    <template #header>
      <div class="card-header">
        <span>团队绩效表</span>
        <div class="header-actions">
          <el-button type="primary" link :loading="loading" @click="fetchData">刷新</el-button>
        </div>
      </div>
    </template>

    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      style="width: 100%"
      show-summary
      :summary-method="getSummaries"
      max-height="500"
    >
      <el-table-column prop="group_name" label="组别" sortable min-width="120" />
      <el-table-column prop="username" label="姓名" min-width="120">
        <template #default="{ row }">
          <div class="user-cell">
            <span class="name">{{ row.username }}</span>
            <el-tag size="small" effect="plain">{{ row.identity }}</el-tag>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column prop="goal_amount" label="目标金额" min-width="140" align="right" sortable>
        <template #default="{ row }">
          {{ formatCurrency(row.goal_amount) }}
        </template>
      </el-table-column>
      
      <el-table-column prop="completed_amount" label="已完成金额" min-width="140" align="right" sortable>
        <template #default="{ row }">
          <span :class="getAmountClass(row)">{{ formatCurrency(row.completed_amount) }}</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="completion_rate" label="完成率" min-width="180" sortable>
        <template #default="{ row }">
          <div class="rate-cell">
            <el-progress 
              :percentage="Math.min(row.completion_rate, 100)" 
              :status="getProgressStatus(row.completion_rate)"
              :format="() => row.completion_rate + '%'"
            />
          </div>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const props = defineProps({
  filterParams: { type: Object, required: true }
})

const loading = ref(false)
const tableData = ref([])

// 格式化金额
const formatCurrency = (value) => {
  if (value === undefined || value === null) return '-'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value)
}

// 进度条状态
const getProgressStatus = (rate) => {
  if (rate >= 100) return 'success'
  if (rate >= 80) return 'warning'
  return 'exception'
}

// 金额颜色
const getAmountClass = (row) => {
  if (row.completed_amount >= row.goal_amount && row.goal_amount > 0) return 'text-success'
  return ''
}

// 获取数据
async function fetchData() {
  loading.value = true
  try {
    const [start, end] = props.filterParams?.dateRange || []
    const query = {
      start_date: start,
      end_date: end,
      group_id: props.filterParams?.groupId || undefined,
      role_scope: props.filterParams?.role || undefined
    }
    
    const { data } = await api.get('/analytics/team-performance', {
      params: query
    })
    
    tableData.value = Array.isArray(data) ? data : []
  } catch (err) {
    console.error('Fetch team performance failed:', err)
    ElMessage.warning('获取团队绩效数据失败')
  } finally {
    loading.value = false
  }
}

// 合计逻辑
const getSummaries = (param) => {
  const { columns, data } = param
  const sums = []
  
  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = '合计'
      return
    }
    
    // 不计算列
    if (['username', 'identity'].includes(column.property)) {
      sums[index] = ''
      return
    }

    const values = data.map(item => Number(item[column.property]))
    
    if (column.property === 'goal_amount' || column.property === 'completed_amount') {
      if (!values.every(value => Number.isNaN(value))) {
        const total = values.reduce((prev, curr) => {
          const value = Number(curr)
          if (!Number.isNaN(value)) {
            return prev + curr
          } else {
            return prev
          }
        }, 0)
        sums[index] = formatCurrency(total)
        
        // 保存总计值用于计算完成率
        if (column.property === 'goal_amount') sums.totalGoal = total
        if (column.property === 'completed_amount') sums.totalCompleted = total
      } else {
        sums[index] = ''
      }
    } else if (column.property === 'completion_rate') {
      // 重新计算总完成率
      const totalGoal = sums.totalGoal || 0
      const totalCompleted = sums.totalCompleted || 0
      if (totalGoal > 0) {
        const rate = ((totalCompleted / totalGoal) * 100).toFixed(1)
        sums[index] = rate + '%'
      } else if (totalCompleted > 0) {
        sums[index] = '100.0%'
      } else {
        sums[index] = '0.0%'
      }
    } else {
      sums[index] = ''
    }
  })

  return sums
}

watch(() => props.filterParams, () => { fetchData() }, { deep: true })

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.team-performance-card {
  margin-top: 16px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.text-success {
  color: var(--el-color-success);
  font-weight: 600;
}

.rate-cell {
  display: flex;
  align-items: center;
}
/* 调整进度条样式 */
:deep(.el-progress__text) {
  min-width: 45px;
  font-size: 12px;
}
</style>
