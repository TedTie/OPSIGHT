<template>
  <div class="dashboard">
    <!-- 欢迎信息 -->
    <div class="welcome-section">
      <h1>欢迎回来，{{ authStore.user?.full_name || authStore.user?.username }}！</h1>
      <p>今天是 {{ formatDate(new Date(), 'yyyy年MM月dd日 EEEE') }}</p>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon pending">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stats-info">
              <h3>{{ stats.pendingTasks }}</h3>
              <p>待处理任务</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon progress">
              <el-icon><Loading /></el-icon>
            </div>
            <div class="stats-info">
              <h3>{{ stats.inProgressTasks }}</h3>
              <p>进行中任务</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon completed">
              <el-icon><Check /></el-icon>
            </div>
            <div class="stats-info">
              <h3>{{ stats.completedTasks }}</h3>
              <p>已完成任务</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon reports">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stats-info">
              <h3>{{ stats.reportsThisWeek }}</h3>
              <p>本周日报</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 主要内容区 -->
    <el-row :gutter="20" class="content-row">
      <!-- 最近任务 -->
      <el-col :xs="24" :lg="12">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>最近任务</span>
              <el-button type="text" @click="$router.push('/tasks')">
                查看全部
              </el-button>
            </div>
          </template>
          
          <div v-loading="tasksLoading" class="task-list">
            <div
              v-for="task in recentTasks"
              :key="task.id"
              class="task-item"
              @click="viewTask(task)"
            >
              <div class="task-info">
                <h4>{{ task.title }}</h4>
                <p>{{ task.description }}</p>
                <div class="task-meta">
                  <el-tag :type="getTaskStatusType(task.status)" size="small">
                    {{ getTaskStatusText(task.status) }}
                  </el-tag>
                  <span class="task-date">
                    {{ formatDate(task.created_at) }}
                  </span>
                </div>
              </div>
            </div>
            
            <div v-if="recentTasks.length === 0" class="empty-state">
              <el-empty description="暂无任务" />
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 最近日报 -->
      <el-col :xs="24" :lg="12">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>最近日报</span>
              <el-button type="text" @click="$router.push('/reports')">
                查看全部
              </el-button>
            </div>
          </template>
          
          <div v-loading="reportsLoading" class="report-list">
            <div
              v-for="report in recentReports"
              :key="report.id"
              class="report-item"
              @click="viewReport(report)"
            >
              <div class="report-info">
                <h4>{{ formatDate(report.work_date) }} 日报</h4>
                <p>{{ report.work_summary || '暂无摘要' }}</p>
                <div class="report-meta">
                  <span class="report-date">
                    {{ formatDateTime(report.created_at) }}
                  </span>
                </div>
              </div>
            </div>
            
            <div v-if="recentReports.length === 0" class="empty-state">
              <el-empty description="暂无日报" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表展示 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :xs="24" :lg="12">
        <el-card class="content-card">
          <template #header>
            <span>任务状态分布</span>
          </template>
          <TaskChart
            type="pie"
            :data="taskStatusData"
            title=""
            height="300px"
          />
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <el-card class="content-card">
          <template #header>
            <span>本周任务趋势</span>
          </template>
          <TaskChart
            type="line"
            :data="weeklyTaskData"
            title=""
            height="300px"
          />
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 工作效率分析 -->
    <el-row :gutter="20" class="efficiency-row">
      <el-col :span="24">
        <el-card class="content-card">
          <template #header>
            <span>工作效率分析</span>
          </template>
          
          <el-row :gutter="20">
            <el-col :xs="24" :md="8">
              <div class="efficiency-item">
                <h4>平均完成时间</h4>
                <div class="efficiency-value">
                  {{ efficiency.avgCompletionTime }}小时
                </div>
                <p class="efficiency-desc">任务平均完成时间</p>
              </div>
            </el-col>
            
            <el-col :xs="24" :md="8">
              <div class="efficiency-item">
                <h4>本周完成率</h4>
                <div class="efficiency-value">
                  {{ efficiency.weeklyCompletionRate }}%
                </div>
                <p class="efficiency-desc">本周任务完成率</p>
              </div>
            </el-col>
            
            <el-col :xs="24" :md="8">
              <div class="efficiency-item">
                <h4>工作时长</h4>
                <div class="efficiency-value">
                  {{ efficiency.totalWorkHours }}小时
                </div>
                <p class="efficiency-desc">本周总工作时长</p>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快速操作 -->
    <el-row :gutter="20" class="quick-actions">
      <el-col :span="24">
        <el-card class="content-card">
          <template #header>
            <span>快速操作</span>
          </template>
          
          <div class="action-buttons">
            <el-button
              type="primary"
              :icon="Plus"
              @click="$router.push('/tasks')"
            >
              创建任务
            </el-button>
            
            <el-button
              type="success"
              :icon="EditPen"
              @click="$router.push('/reports')"
            >
              写日报
            </el-button>
            
            <el-button
              type="info"
              :icon="TrendCharts"
              @click="$router.push('/analytics')"
            >
              查看分析
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Clock from '~icons/tabler/clock'
import Loading from '~icons/tabler/loader-2'
import Check from '~icons/tabler/check'
import Document from '~icons/tabler/file-text'
import Plus from '~icons/tabler/plus'
import EditPen from '~icons/tabler/edit'
import TrendCharts from '~icons/tabler/chart-line'
import { useAuthStore } from '@/stores/auth'
import { formatDate, formatDateTime, getWeekStartEnd, getMonthStartEnd } from '@/utils/date'
import api from '@/utils/api'
import TaskChart from '@/components/Charts/TaskChart.vue'

const router = useRouter()
const authStore = useAuthStore()

// 统计数据
const stats = reactive({
  pendingTasks: 0,
  inProgressTasks: 0,
  completedTasks: 0,
  reportsThisWeek: 0
})

// 最近任务
const recentTasks = ref([])
const tasksLoading = ref(false)

// 最近日报
const recentReports = ref([])
const reportsLoading = ref(false)

// 图表数据
const taskStatusData = ref([])
const weeklyTaskData = ref([])

// 工作效率数据
const efficiency = reactive({
  avgCompletionTime: 0,
  weeklyCompletionRate: 0,
  totalWorkHours: 0
})

// 获取任务状态类型
const getTaskStatusType = (status) => {
  const statusMap = {
    'pending': 'warning',
    'processing': 'primary',
    'done': 'success'
  }
  return statusMap[status] || 'info'
}

// 获取任务状态文本
const getTaskStatusText = (status) => {
  const statusMap = {
    'pending': '待处理',
    'processing': '进行中',
    'done': '已完成'
  }
  return statusMap[status] || status
}



// 查看任务详情
const viewTask = (task) => {
  router.push(`/tasks/${parseInt(task.id)}`)
}

// 查看日报详情
const viewReport = (report) => {
  router.push(`/reports/${parseInt(report.id)}`)
}

// 获取统计数据（按用户所在组过滤）
const fetchStats = async () => {
  if (!authStore.isAuthenticated) {
    console.log('User not authenticated, skipping stats fetch')
    return
  }
  
  try {
    // 统计卡片：优先使用按组过滤的分析接口（按本周范围对齐趋势图）
    const groupId = authStore.user?.group_id ?? null
    const [weekStartForStatus, weekEndForStatus] = getWeekStartEnd(new Date())
    const chartsResp = await api.get('/analytics/charts', {
      params: {
        start_date: weekStartForStatus,
        end_date: weekEndForStatus,
        ...(groupId ? { group_id: groupId } : {})
      }
    })
    const charts = chartsResp.data || {}
    const statusArr = charts.taskStatus || charts.task_status || []
    const toMap = (name) => {
      const item = statusArr.find(s => (s.name === name || s.status === name))
      return item ? (item.value ?? item.count ?? 0) : 0
    }
    stats.pendingTasks = toMap('pending')
    stats.inProgressTasks = toMap('processing')
    stats.completedTasks = toMap('done')

    // 更新任务状态图表数据（展示中文标签）
    taskStatusData.value = [
      { name: '待处理', value: stats.pendingTasks },
      { name: '进行中', value: stats.inProgressTasks },
      { name: '已完成', value: stats.completedTasks }
    ]

    // 本周日报数量：按组过滤的统计接口
    const [weekStart, weekEnd] = getWeekStartEnd(new Date())
    const statsResp = await api.get('/analytics/stats', {
      params: {
        start_date: weekStart,
        end_date: weekEnd,
        ...(groupId ? { group_id: groupId } : {})
      }
    })
    const sdata = statsResp.data || {}
    stats.reportsThisWeek = sdata.totalReports ?? 0
  } catch (error) {
    console.error('Failed to fetch stats:', error)
    if (error.response?.status === 401) {
      authStore.logout()
      router.push('/login')
    }
  }
}

// 获取本周任务趋势数据（按用户所在组过滤）
const fetchWeeklyTrend = async () => {
  if (!authStore.isAuthenticated) {
    console.log('User not authenticated, skipping weekly trend fetch')
    return
  }
  
  try {
    const groupId = authStore.user?.group_id ?? null
    const [weekStart, weekEnd] = getWeekStartEnd(new Date())
    const response = await api.get('/analytics/charts', {
      params: {
        start_date: weekStart,
        end_date: weekEnd,
        ...(groupId ? { group_id: groupId } : {})
      }
    })
    const trend = (response.data?.taskTrend || response.data?.task_trend || [])
    // 选择“已完成”作为趋势展示值
    weeklyTaskData.value = trend.map(item => ({
      name: item.date,
      value: item.completed ?? item.count ?? 0
    }))
  } catch (error) {
    console.error('Failed to fetch weekly trend:', error)
    if (error.response?.status === 401) {
      authStore.logout()
      router.push('/login')
      return
    }
    // 失败时不使用模拟数据，保持为空以反映真实情况
    weeklyTaskData.value = []
  }
}

// 获取工作效率数据（尽可能按组过滤本周完成率）
const fetchEfficiency = async () => {
  if (!authStore.isAuthenticated) {
    console.log('User not authenticated, skipping efficiency fetch')
    return
  }
  
  try {
    // 使用真实后端端点
    const response = await api.get('/stats/overview')
    const data = response.data || {}
    efficiency.avgCompletionTime = data.avgCompletionTime ?? 0
    efficiency.totalWorkHours = data.totalWorkHours ?? 0

    // 覆盖本周完成率为“按组过滤”的值
    const groupId = authStore.user?.group_id ?? null
    const [weekStart, weekEnd] = getWeekStartEnd(new Date())
    const statsResp = await api.get('/analytics/stats', {
      params: {
        start_date: weekStart,
        end_date: weekEnd,
        ...(groupId ? { group_id: groupId } : {})
      }
    })
    const sdata = statsResp.data || {}
    efficiency.weeklyCompletionRate = sdata.completionRate ?? (data.weeklyCompletionRate ?? 0)
  } catch (error) {
    console.error('Failed to fetch efficiency:', error)
    if (error.response?.status === 401) {
      authStore.logout()
      router.push('/login')
      return
    }
    // 不使用模拟数据，保持默认值
    efficiency.avgCompletionTime = 0
    efficiency.totalWorkHours = 0
    // 尝试保留已有的本周完成率值（若可用）
    try {
      const groupId = authStore.user?.group_id ?? null
      const [weekStart, weekEnd] = getWeekStartEnd(new Date())
      const statsResp = await api.get('/analytics/stats', {
        params: {
          start_date: weekStart,
          end_date: weekEnd,
          ...(groupId ? { group_id: groupId } : {})
        }
      })
      efficiency.weeklyCompletionRate = statsResp.data?.completionRate ?? 0
    } catch (e) {
      efficiency.weeklyCompletionRate = 0
    }
  }
}

// 获取最近任务
const fetchRecentTasks = async () => {
  if (!authStore.isAuthenticated) {
    console.log('User not authenticated, skipping recent tasks fetch')
    return
  }
  
  tasksLoading.value = true
  try {
    const response = await api.get('/tasks', {
      params: { page: 1, size: 5 }
    })
    const data = response.data
    if (Array.isArray(data)) {
      recentTasks.value = data
    } else if (data && typeof data === 'object') {
      recentTasks.value = data.items || data.data || []
    } else {
      recentTasks.value = []
    }
  } catch (error) {
    console.error('Failed to fetch recent tasks:', error)
    if (error.response?.status === 401) {
      authStore.logout()
      router.push('/login')
      return
    }
  } finally {
    tasksLoading.value = false
  }
}

// 获取最近日报
const fetchRecentReports = async () => {
  if (!authStore.isAuthenticated) {
    console.log('User not authenticated, skipping reports fetch')
    return
  }
  
  reportsLoading.value = true
  try {
    const [weekStart, weekEnd] = getWeekStartEnd(new Date())
    const groupId = authStore.user?.group_id ?? null
    const response = await api.get('/reports', {
      params: {
        page: 1,
        size: 5,
        start_date: weekStart,
        end_date: weekEnd,
        ...(groupId ? { group_id: groupId } : {})
      }
    })
    const data = response.data
    if (Array.isArray(data)) {
      recentReports.value = data
    } else if (data && typeof data === 'object') {
      recentReports.value = data.items || data.data || []
    } else {
      recentReports.value = []
    }
  } catch (error) {
    console.error('Failed to fetch recent reports:', error)
    if (error.response?.status === 401) {
      authStore.logout()
      router.push('/login')
      return
    }
  } finally {
    reportsLoading.value = false
  }
}

// 初始化数据
onMounted(async () => {
  // 检查认证状态
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  
  // 尝试获取用户信息以验证token有效性
  try {
    await authStore.fetchUserInfo()
  } catch (error) {
    console.error('Token validation failed:', error)
    router.push('/login')
    return
  }
  
  // 并行获取数据
  await Promise.allSettled([
    fetchStats(),
    fetchWeeklyTrend(),
    fetchEfficiency(),
    fetchRecentTasks(),
    fetchRecentReports()
  ])
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.welcome-section {
  margin-bottom: 32px;
  padding: 24px;
  border-radius: var(--radius-xl);
  background: linear-gradient(
    135deg,
    rgba(16, 185, 129, 0.05) 0%,
    rgba(110, 231, 183, 0.03) 100%
  );
  border: 1px solid rgba(16, 185, 129, 0.1);
}

.welcome-section h1 {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px 0;
  background: var(--gradient-emerald);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

.welcome-section p {
  color: var(--text-muted);
  font-size: 16px;
  margin: 0;
  font-weight: 500;
}

.stats-row {
  margin-bottom: 32px;
}

.stats-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.stats-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--gradient-primary);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.stats-card:hover::before {
  transform: scaleX(1);
}

.stats-card:hover {
  transform: translateY(-6px);
}

.stats-content {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 8px 0;
}

.stats-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
  position: relative;
  box-shadow: var(--shadow-glow-soft);
  transition: all 0.3s ease;
}

.stats-card:hover .stats-icon {
  transform: scale(1.1) rotate(5deg);
  box-shadow: var(--shadow-glow);
}

.stats-icon.pending {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.stats-icon.progress {
  background: var(--gradient-cyber-green);
}

.stats-icon.completed {
  background: var(--gradient-emerald);
}

.stats-icon.reports {
  background: var(--gradient-nature);
}

.stats-info {
  flex: 1;
}

.stats-info h3 {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 4px 0;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.stats-info p {
  color: var(--text-muted);
  font-size: 14px;
  margin: 0;
  font-weight: 500;
}

.content-row {
  margin-bottom: 32px;
}

.content-card {
  margin-bottom: 20px;
  height: 450px;
  display: flex;
  flex-direction: column;
}

.content-card :deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.charts-row {
  margin-bottom: 32px;
}

.charts-row .content-card {
  height: 420px;
}

.efficiency-row {
  margin-bottom: 32px;
}

.efficiency-item {
  text-align: center;
  padding: 28px 20px;
  border-radius: var(--radius-lg);
  background: var(--gradient-primary);
  color: white;
  margin-bottom: 20px;
  box-shadow: var(--shadow-glow-soft);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.efficiency-item::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.1) 0%,
    transparent 50%
  );
  pointer-events: none;
}

.efficiency-item:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: var(--shadow-glow);
}

.efficiency-item h4 {
  font-size: 15px;
  margin: 0 0 12px 0;
  opacity: 0.9;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.efficiency-value {
  font-size: 40px;
  font-weight: 700;
  margin: 16px 0;
  line-height: 1;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.efficiency-desc {
  font-size: 13px;
  margin: 0;
  opacity: 0.85;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: var(--text-strong);
}

.task-list,
.report-list {
  height: 360px;
  overflow-y: auto;
  padding-right: 4px;
}

.task-item,
.report-item {
  padding: 16px;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgba(16, 185, 129, 0.03);
}

.task-item:hover,
.report-item:hover {
  background: rgba(16, 185, 129, 0.08);
  border-color: rgba(16, 185, 129, 0.2);
  transform: translateX(4px);
  box-shadow: var(--shadow-sm);
}

.task-item:last-child,
.report-item:last-child {
  margin-bottom: 0;
}

.task-info h4,
.report-info h4 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-strong);
  margin: 0 0 8px 0;
}

.task-info p,
.report-info p {
  color: var(--text-muted);
  font-size: 14px;
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.5;
}

.task-meta,
.report-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.task-date,
.report-date {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 500;
}

:deep(.el-tag) {
  border-radius: 6px;
  font-weight: 500;
  padding: 0 10px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 280px;
  color: var(--text-muted);
}

.empty-state :deep(.el-empty__description) {
  color: var(--text-muted);
}

.quick-actions {
  margin-bottom: 32px;
}

.action-buttons {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: center;
}

.action-buttons .el-button {
  padding: 12px 28px;
  font-size: 15px;
  font-weight: 600;
  border-radius: var(--radius-md);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.action-buttons .el-button:hover {
  transform: translateY(-2px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard {
    padding: 16px;
  }
  
  .welcome-section {
    padding: 20px;
    margin-bottom: 24px;
  }
  
  .welcome-section h1 {
    font-size: 26px;
  }
  
  .welcome-section p {
    font-size: 14px;
  }
  
  .stats-content {
    gap: 16px;
  }
  
  .stats-icon {
    width: 48px;
    height: 48px;
    font-size: 24px;
  }
  
  .stats-info h3 {
    font-size: 26px;
  }
  
  .stats-info p {
    font-size: 13px;
  }
  
  .content-card {
    height: auto;
    min-height: 350px;
  }
  
  .charts-row .content-card {
    height: auto;
    min-height: 350px;
  }
  
  .task-list,
  .report-list {
    height: auto;
    max-height: 400px;
  }
  
  .efficiency-item {
    padding: 24px 16px;
  }
  
  .efficiency-value {
    font-size: 32px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .action-buttons .el-button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .stats-info h3 {
    font-size: 24px;
  }
  
  .efficiency-value {
    font-size: 28px;
  }
}
</style>