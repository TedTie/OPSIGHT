<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">数据分析</h1>
      <p class="page-description">查看任务和日报的统计分析</p>
    </div>
    
    <!-- 时间范围选择 -->
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>时间范围</span>
        </div>
      </template>
      
      <div class="time-range-selector">
        <el-radio-group v-model="timeRange" @change="onTimeRangeChange">
          <el-radio-button label="week">本周</el-radio-button>
          <el-radio-button label="month">本月</el-radio-button>
          <el-radio-button label="quarter">本季度</el-radio-button>
          <el-radio-button label="custom">自定义</el-radio-button>
        </el-radio-group>
        
        <el-date-picker
          v-if="timeRange === 'custom'"
          v-model="customDateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="fetchAnalytics"
        />
        
        <!-- 用户组选择（仅管理员可见） -->
        <el-select
          v-if="currentUser?.is_admin || currentUser?.is_super_admin"
          v-model="selectedGroupId"
          placeholder="选择用户组"
          clearable
          @change="fetchAnalytics"
          style="width: 200px"
        >
          <el-option label="全部用户组" :value="null" />
          <el-option
            v-for="group in userGroups"
            :key="group.id"
            :label="group.name"
            :value="group.id"
          />
        </el-select>
      </div>
    </el-card>
    
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalTasks }}</div>
          <div class="stat-label">总任务数</div>
        </div>
        <div class="stat-icon">
          <el-icon><Document /></el-icon>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ stats.completedTasks }}</div>
          <div class="stat-label">已完成任务</div>
        </div>
        <div class="stat-icon">
          <el-icon><Check /></el-icon>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ stats.completionRate }}%</div>
          <div class="stat-label">完成率</div>
        </div>
        <div class="stat-icon">
          <el-icon><TrendCharts /></el-icon>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalReports }}</div>
          <div class="stat-label">日报数量</div>
        </div>
        <div class="stat-icon">
          <el-icon><Notebook /></el-icon>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ stats.avgEmotionScore }}</div>
          <div class="stat-label">平均情感分数</div>
        </div>
        <div class="stat-icon">
          <el-icon><Star /></el-icon>
        </div>
      </el-card>
    </div>
    
    <!-- 图表区域 -->
    <div class="charts-grid">
      <!-- 任务完成趋势 -->
      <el-card class="chart-card">
        <template #header>
          <span>任务完成趋势</span>
        </template>
        <div class="chart-container">
          <v-chart
            :option="taskTrendOption"
            :loading="loading"
            style="height: 300px"
          />
        </div>
      </el-card>
      
      <!-- 任务状态分布 -->
      <el-card class="chart-card">
        <template #header>
          <span>任务状态分布</span>
        </template>
        <div class="chart-container">
          <v-chart
            :option="taskStatusOption"
            :loading="loading"
            style="height: 300px"
          />
        </div>
      </el-card>
      
      <!-- 情感分数趋势 -->
      <el-card class="chart-card">
        <template #header>
          <span>情感分数趋势</span>
        </template>
        <div class="chart-container">
          <v-chart
            :option="emotionTrendOption"
            :loading="loading"
            style="height: 300px"
          />
        </div>
      </el-card>
      
      <!-- 任务优先级分布 -->
      <el-card class="chart-card">
        <template #header>
          <span>任务优先级分布</span>
        </template>
        <div class="chart-container">
          <v-chart
            :option="priorityDistributionOption"
            :loading="loading"
            style="height: 300px"
          />
        </div>
      </el-card>
      
      <!-- AI使用统计 -->
      <el-card class="chart-card">
        <template #header>
          <span>AI使用统计</span>
        </template>
        <div class="ai-stats-content">
          <div class="ai-stat-item">
            <div class="ai-stat-label">总调用次数</div>
            <div class="ai-stat-value">{{ aiStats.totalCalls }}</div>
          </div>
          <div class="ai-stat-item">
            <div class="ai-stat-label">总Token数</div>
            <div class="ai-stat-value">{{ aiStats.totalTokens }}</div>
          </div>
          <div class="ai-stat-item">
            <div class="ai-stat-label">总成本</div>
            <div class="ai-stat-value">${{ aiStats.totalCost }}</div>
          </div>
          <div class="ai-stat-item">
            <div class="ai-stat-label">平均处理时间</div>
            <div class="ai-stat-value">{{ aiStats.avgProcessingTime }}s</div>
          </div>
        </div>
      </el-card>
      
      <!-- 用户绩效排行（仅管理员可见） -->
      <el-card 
        v-if="currentUser?.is_admin || currentUser?.is_super_admin"
        class="chart-card user-performance-card"
      >
        <template #header>
          <span>用户绩效排行</span>
        </template>
        <div class="user-performance-content">
          <el-table
            :data="userPerformance"
            style="width: 100%"
            :loading="loading"
            size="small"
          >
            <el-table-column prop="username" label="用户名" width="120" />
            <el-table-column prop="totalTasks" label="总任务" width="80" />
            <el-table-column prop="completedTasks" label="已完成" width="80" />
            <el-table-column prop="completionRate" label="完成率" width="80">
              <template #default="scope">
                <el-tag
                  :type="scope.row.completionRate >= 80 ? 'success' : 
                         scope.row.completionRate >= 60 ? 'warning' : 'danger'"
                >
                  {{ scope.row.completionRate }}%
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="totalReports" label="日报数" width="80" />
            <el-table-column prop="avgEmotionScore" label="情感分数" width="100">
              <template #default="scope">
                <el-progress
                  :percentage="scope.row.avgEmotionScore * 100"
                  :color="getEmotionColor(scope.row.avgEmotionScore)"
                  :show-text="false"
                  style="width: 60px"
                />
                <span style="margin-left: 8px">{{ scope.row.avgEmotionScore }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>
    </div>
    
    <!-- AI洞察面板 -->
    <el-card class="ai-insights-card">
      <template #header>
        <span>AI分析洞察</span>
      </template>
      <div class="ai-insights-content">
        <div class="insights-grid">
          <div class="insight-item">
            <h4>情感分析统计</h4>
            <div class="insight-stats">
              <div class="insight-stat">
                <span class="label">已分析报告:</span>
                <span class="value">{{ aiInsights.emotionStats.totalAnalyzed }}</span>
              </div>
              <div class="insight-stat">
                <span class="label">平均情感分数:</span>
                <span class="value">{{ aiInsights.emotionStats.avgEmotion }}</span>
              </div>
              <div class="insight-stat">
                <span class="label">情感分数范围:</span>
                <span class="value">
                  {{ aiInsights.emotionStats.minEmotion }} - {{ aiInsights.emotionStats.maxEmotion }}
                </span>
              </div>
            </div>
          </div>
          
          <div class="insight-item">
            <h4>常见关键词</h4>
            <div class="keywords-container">
              <el-tag
                v-for="keyword in aiInsights.commonKeywords.slice(0, 10)"
                :key="keyword.keyword"
                class="keyword-tag"
                :size="getKeywordSize(keyword.frequency)"
              >
                {{ keyword.keyword }} ({{ keyword.frequency }})
              </el-tag>
            </div>
          </div>
          
          <div class="insight-item">
            <h4>AI模型使用情况</h4>
            <div class="model-usage">
              <div
                v-for="model in aiInsights.modelUsage"
                :key="model.model"
                class="model-item"
              >
                <div class="model-name">{{ model.model }}</div>
                <div class="model-stats">
                  <span>使用次数: {{ model.count }}</span>
                  <span>平均处理时间: {{ model.avgProcessingTime }}s</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Check, Notebook, TrendCharts, Star } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import {
  CanvasRenderer
} from 'echarts/renderers'
import {
  LineChart,
  PieChart,
  BarChart
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import api from '@/utils/api'
import { getWeekStartEnd, getMonthStartEnd } from '@/utils/date'
import { useAuthStore } from '@/stores/auth'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  PieChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const authStore = useAuthStore()
const currentUser = computed(() => authStore.user)

// 数据
const loading = ref(false)
const timeRange = ref('month')
const customDateRange = ref([])
const selectedGroupId = ref(null)
const userGroups = ref([])

// 统计数据
const stats = reactive({
  totalTasks: 0,
  completedTasks: 0,
  completionRate: 0,
  totalReports: 0,
  avgEmotionScore: 0
})

// 图表数据
const chartData = reactive({
  taskTrend: [],
  taskStatus: [],
  emotionTrend: [],
  priorityDistribution: []
})

// AI统计数据
const aiStats = reactive({
  totalCalls: 0,
  totalTokens: 0,
  totalCost: 0,
  avgProcessingTime: 0
})

// 用户绩效数据
const userPerformance = ref([])

// AI洞察数据
const aiInsights = reactive({
  emotionStats: {
    totalAnalyzed: 0,
    avgEmotion: 0,
    minEmotion: 0,
    maxEmotion: 0
  },
  commonKeywords: [],
  modelUsage: []
})

// 计算日期范围
const dateRange = computed(() => {
  if (timeRange.value === 'custom') {
    return customDateRange.value
  }
  
  const now = new Date()
  switch (timeRange.value) {
    case 'week':
      return getWeekStartEnd(now)
    case 'month':
      return getMonthStartEnd(now)
    case 'quarter':
      const quarterStart = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3, 1)
      const quarterEnd = new Date(quarterStart.getFullYear(), quarterStart.getMonth() + 3, 0)
      return [quarterStart.toISOString().split('T')[0], quarterEnd.toISOString().split('T')[0]]
    default:
      return getMonthStartEnd(now)
  }
})

// 任务完成趋势图表配置
const taskTrendOption = computed(() => ({
  tooltip: {
    trigger: 'axis'
  },
  legend: {
    data: ['已完成', '新增']
  },
  xAxis: {
    type: 'category',
    data: chartData.taskTrend.map(item => item.date)
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: '已完成',
      type: 'line',
      data: chartData.taskTrend.map(item => item.completed),
      smooth: true,
      itemStyle: { color: '#67C23A' }
    },
    {
      name: '新增',
      type: 'line',
      data: chartData.taskTrend.map(item => item.created),
      smooth: true,
      itemStyle: { color: '#409EFF' }
    }
  ]
}))

// 任务状态分布图表配置
const taskStatusOption = computed(() => ({
  tooltip: {
    trigger: 'item'
  },
  legend: {
    orient: 'vertical',
    left: 'left'
  },
  series: [
    {
      type: 'pie',
      radius: '50%',
      data: chartData.taskStatus,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }
  ]
}))

// 情感分数趋势图表配置
const emotionTrendOption = computed(() => ({
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: chartData.emotionTrend.map(item => item.date)
  },
  yAxis: {
    type: 'value',
    min: 0,
    max: 1
  },
  series: [
    {
      name: '情感分数',
      type: 'line',
      data: chartData.emotionTrend.map(item => item.score),
      smooth: true,
      itemStyle: { color: '#E6A23C' },
      areaStyle: {
        opacity: 0.3
      }
    }
  ]
}))

// 任务优先级分布图表配置
const priorityDistributionOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    }
  },
  xAxis: {
    type: 'category',
    data: chartData.priorityDistribution.map(item => item.priority)
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      type: 'bar',
      data: chartData.priorityDistribution.map(item => ({
        value: item.count,
        itemStyle: {
          color: item.priority === '高优先级' ? '#F56C6C' : 
                 item.priority === '中优先级' ? '#E6A23C' : '#67C23A'
        }
      }))
    }
  ]
}))

// 工具函数
const getEmotionColor = (score) => {
  if (score >= 0.7) return '#67C23A'
  if (score >= 0.4) return '#E6A23C'
  return '#F56C6C'
}

const getKeywordSize = (frequency) => {
  if (frequency >= 10) return 'large'
  if (frequency >= 5) return 'default'
  return 'small'
}

// 时间范围变化处理
const onTimeRangeChange = () => {
  if (timeRange.value !== 'custom') {
    fetchAnalytics()
  }
}

// 获取用户组列表
const fetchUserGroups = async () => {
  if (!(currentUser.value?.is_admin || currentUser.value?.is_super_admin)) {
    return
  }
  
  try {
    const response = await api.get('/groups')
    userGroups.value = response.data
  } catch (error) {
    console.error('获取用户组失败:', error)
  }
}

// 获取分析数据
const fetchAnalytics = async () => {
  loading.value = true
  try {
    const [startDate, endDate] = dateRange.value
    const params = {
      start_date: startDate,
      end_date: endDate
    }
    
    if (selectedGroupId.value) {
      params.group_id = selectedGroupId.value
    }
    
    // 获取统计数据
    const statsResponse = await api.get('/analytics/stats', { params })
    Object.assign(stats, statsResponse.data)
    
    // 获取图表数据
    const chartsResponse = await api.get('/analytics/charts', { params })
    Object.assign(chartData, chartsResponse.data.taskTrend ? chartsResponse.data : {
      taskTrend: chartsResponse.data.task_trend || [],
      taskStatus: chartsResponse.data.task_status || [],
      emotionTrend: chartsResponse.data.emotion_trend || [],
      priorityDistribution: chartsResponse.data.priority_distribution || []
    })
    
    // 更新AI统计数据
    if (chartsResponse.data.ai_stats) {
      Object.assign(aiStats, {
        totalCalls: chartsResponse.data.ai_stats.total_calls,
        totalTokens: chartsResponse.data.ai_stats.total_tokens,
        totalCost: chartsResponse.data.ai_stats.total_cost,
        avgProcessingTime: chartsResponse.data.ai_stats.avg_processing_time
      })
    }
    
    // 获取用户绩效数据（仅管理员）
    if (currentUser.value?.is_admin || currentUser.value?.is_super_admin) {
      const performanceResponse = await api.get('/analytics/user-performance', { params })
      userPerformance.value = performanceResponse.data
    }
    
    // 获取AI洞察数据
    const insightsResponse = await api.get('/analytics/ai-insights', { params })
    Object.assign(aiInsights, {
      emotionStats: insightsResponse.data.emotion_stats,
      commonKeywords: insightsResponse.data.common_keywords,
      modelUsage: insightsResponse.data.model_usage
    })
    
  } catch (error) {
    ElMessage.error('获取分析数据失败')
    console.error('Analytics fetch error:', error)
  } finally {
    loading.value = false
  }
}

// 初始化
onMounted(async () => {
  await fetchUserGroups()
  await fetchAnalytics()
})
</script>

<style scoped>
.time-range-selector {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  .el-card__body {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px;
  }
}

.stat-content {
  .stat-value {
    font-size: 28px;
    font-weight: bold;
    color: #303133;
    margin-bottom: 8px;
  }
  
  .stat-label {
    font-size: 14px;
    color: #909399;
  }
}

.stat-icon {
  font-size: 40px;
  color: #409EFF;
  opacity: 0.8;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.chart-card {
  min-height: 400px;
}

.chart-container {
  width: 100%;
  height: 300px;
}

.ai-stats-content {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  padding: 20px;
}

.ai-stat-item {
  text-align: center;
  
  .ai-stat-label {
    font-size: 14px;
    color: #909399;
    margin-bottom: 8px;
  }
  
  .ai-stat-value {
    font-size: 24px;
    font-weight: bold;
    color: #303133;
  }
}

.user-performance-card {
  grid-column: 1 / -1;
}

.user-performance-content {
  max-height: 400px;
  overflow-y: auto;
}

.ai-insights-card {
  margin-top: 24px;
}

.ai-insights-content {
  padding: 20px;
}

.insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.insight-item {
  h4 {
    margin: 0 0 16px 0;
    color: #303133;
    font-size: 16px;
  }
}

.insight-stats {
  .insight-stat {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    
    .label {
      color: #909399;
    }
    
    .value {
      font-weight: bold;
      color: #303133;
    }
  }
}

.keywords-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword-tag {
  margin: 0;
}

.model-usage {
  .model-item {
    padding: 12px;
    border: 1px solid #EBEEF5;
    border-radius: 4px;
    margin-bottom: 8px;
    
    .model-name {
      font-weight: bold;
      margin-bottom: 4px;
    }
    
    .model-stats {
      font-size: 12px;
      color: #909399;
      
      span {
        margin-right: 16px;
      }
    }
  }
}

@media (max-width: 768px) {
  .time-range-selector {
    flex-direction: column;
    align-items: stretch;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .ai-stats-content {
    grid-template-columns: 1fr;
  }
  
  .insights-grid {
    grid-template-columns: 1fr;
  }
}
</style>