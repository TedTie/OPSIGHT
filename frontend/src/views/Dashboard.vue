<template>
  <div class="dashboard-container">
    <!-- Welcome Section -->
    <div class="welcome-card glass-panel">
      <div class="welcome-content">
        <h1>早安，{{ authStore.user?.full_name || authStore.user?.username }}</h1>
        <p>今天是 {{ formatDate(new Date(), 'yyyy年MM月dd日 EEEE') }}，祝你拥有高效的一天！</p>
      </div>
      <div class="welcome-decoration">
        <div class="leaf-shape"></div>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="stats-grid">
      <div class="stat-card glass-panel">
        <div class="stat-icon pending">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.pendingTasks }}</span>
          <span class="stat-label">待处理任务</span>
        </div>
      </div>
      
      <div class="stat-card glass-panel">
        <div class="stat-icon progress">
          <el-icon><Loading /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.inProgressTasks }}</span>
          <span class="stat-label">进行中任务</span>
        </div>
      </div>
      
      <div class="stat-card glass-panel">
        <div class="stat-icon completed">
          <el-icon><Check /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.completedTasks }}</span>
          <span class="stat-label">已完成任务</span>
        </div>
      </div>
      
      <div class="stat-card glass-panel">
        <div class="stat-icon reports">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.reportsThisWeek }}</span>
          <span class="stat-label">本周日报</span>
        </div>
      </div>
    </div>

    <!-- Main Content Grid (Bento Layout) -->
    <div class="bento-grid">
      <!-- Charts Section -->
      <div class="bento-item chart-card glass-panel">
        <div class="card-header">
          <h3>任务趋势</h3>
        </div>
        <div class="chart-container">
          <TaskChart
            type="line"
            :data="weeklyTaskData"
            height="100%"
          />
        </div>
      </div>

      <div class="bento-item pie-card glass-panel">
        <div class="card-header">
          <h3>状态分布</h3>
        </div>
        <div class="chart-container">
          <TaskChart
            type="pie"
            :data="taskStatusData"
            height="100%"
          />
        </div>
      </div>

      <!-- Recent Tasks -->
      <div class="bento-item tasks-card glass-panel">
        <div class="card-header">
          <h3>最近任务</h3>
          <el-button text class="view-all-btn" @click="$router.push('/tasks')">
            查看全部 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
        <div class="list-container" v-loading="tasksLoading">
          <div
            v-for="task in recentTasks"
            :key="task.id"
            class="list-item"
            @click="viewTask(task)"
          >
            <div class="item-content">
              <span class="item-title">{{ task.title }}</span>
              <span class="item-desc">{{ task.description }}</span>
            </div>
            <el-tag :type="getTaskStatusType(task.status)" size="small" effect="light" round>
              {{ getTaskStatusText(task.status) }}
            </el-tag>
          </div>
          <el-empty v-if="recentTasks.length === 0" description="暂无任务" :image-size="60" />
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="bento-item actions-card glass-panel">
        <div class="card-header">
          <h3>快速操作</h3>
        </div>
        <div class="actions-grid">
          <div class="action-btn primary" @click="$router.push('/tasks')">
            <el-icon><Plus /></el-icon>
            <span>新建任务</span>
          </div>
          <div class="action-btn success" @click="$router.push('/reports')">
            <el-icon><EditPen /></el-icon>
            <span>写日报</span>
          </div>
          <div class="action-btn info" @click="$router.push('/analytics')">
            <el-icon><TrendCharts /></el-icon>
            <span>看分析</span>
          </div>
        </div>
      </div>
    </div>
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
import ArrowRight from '~icons/tabler/arrow-right'
import { useAuthStore } from '@/stores/auth'
import { formatDate, getWeekStartEnd } from '@/utils/date'
import api from '@/utils/api'
import TaskChart from '@/components/Charts/TaskChart.vue'

const router = useRouter()
const authStore = useAuthStore()

// Data
const stats = reactive({
  pendingTasks: 0,
  inProgressTasks: 0,
  completedTasks: 0,
  reportsThisWeek: 0
})
const recentTasks = ref([])
const tasksLoading = ref(false)
const taskStatusData = ref([])
const weeklyTaskData = ref([])

// Helpers
const getTaskStatusType = (status) => {
  const map = { pending: 'warning', processing: 'primary', done: 'success' }
  return map[status] || 'info'
}
const getTaskStatusText = (status) => {
  const map = { pending: '待处理', processing: '进行中', done: '已完成' }
  return map[status] || status
}
const viewTask = (task) => router.push(`/tasks?openTaskId=${task.id}`)

// Fetch Data
const fetchData = async () => {
  if (!authStore.isAuthenticated) return

  try {
    // Stats & Charts
    const groupId = authStore.user?.group_id
    const [weekStart, weekEnd] = getWeekStartEnd(new Date())
    
    // Parallel requests
    const [chartsResp, statsResp, tasksResp] = await Promise.all([
      api.get('/analytics/charts', { params: { start_date: weekStart, end_date: weekEnd, group_id: groupId } }),
      api.get('/analytics/stats', { params: { start_date: weekStart, end_date: weekEnd, group_id: groupId } }),
      api.get('/tasks', { params: { page: 1, size: 5 } })
    ])

    // Process Charts
    const charts = chartsResp.data || {}
    const statusArr = charts.taskStatus || []
    const toMap = (name) => {
      const item = statusArr.find(s => s.name === name || s.status === name)
      return item ? (item.value ?? item.count ?? 0) : 0
    }
    stats.pendingTasks = toMap('pending')
    stats.inProgressTasks = toMap('processing')
    stats.completedTasks = toMap('done')
    
    taskStatusData.value = [
      { name: '待处理', value: stats.pendingTasks },
      { name: '进行中', value: stats.inProgressTasks },
      { name: '已完成', value: stats.completedTasks }
    ]

    const trend = charts.taskTrend || []
    weeklyTaskData.value = trend.map(item => ({
      name: item.date,
      value: item.completed ?? item.count ?? 0
    }))

    // Process Stats
    stats.reportsThisWeek = statsResp.data?.totalReports ?? 0

    // Process Tasks
    recentTasks.value = Array.isArray(tasksResp.data) ? tasksResp.data : (tasksResp.data?.items || [])

  } catch (error) {
    console.error('Dashboard data fetch error:', error)
  }
}

onMounted(fetchData)
</script>

<style scoped>
.dashboard-container {
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Welcome Section */
.welcome-card {
  padding: 32px;
  border-radius: var(--radius-xl);
  background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.welcome-content h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-strong);
  margin-bottom: 8px;
}

.welcome-content p {
  color: var(--text-muted);
  font-size: 16px;
}

.welcome-decoration {
  position: absolute;
  right: -50px;
  top: -50px;
  width: 200px;
  height: 200px;
  background: var(--gradient-primary);
  opacity: 0.1;
  border-radius: 50%;
  filter: blur(40px);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}

.stat-card {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.pending { background: #f59e0b; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3); }
.stat-icon.progress { background: #3b82f6; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); }
.stat-icon.completed { background: #10b981; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3); }
.stat-icon.reports { background: #8b5cf6; box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3); }

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-strong);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--text-muted);
}

/* Bento Grid */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(2, minmax(300px, auto));
  gap: 24px;
}

.bento-item {
  padding: 24px;
  display: flex;
  flex-direction: column;
}

.chart-card {
  grid-column: span 3;
}

.pie-card {
  grid-column: span 1;
}

.tasks-card {
  grid-column: span 2;
  height: 400px;
}

.actions-card {
  grid-column: span 2;
  height: 400px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-strong);
  margin: 0;
}

.chart-container {
  flex: 1;
  min-height: 0;
}

.list-container {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-radius: 12px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.list-item:hover {
  background: var(--bg-soft);
}

.item-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow: hidden;
}

.item-title {
  font-weight: 500;
  color: var(--text-strong);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-desc {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  height: 100%;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.action-btn:hover {
  transform: translateY(-4px);
  background: white;
  box-shadow: var(--shadow-md);
}

.action-btn .el-icon {
  font-size: 32px;
  padding: 16px;
  border-radius: 50%;
  color: white;
}

.action-btn span {
  font-weight: 600;
  color: var(--text-normal);
}

.action-btn.primary .el-icon { background: var(--color-primary); box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3); }
.action-btn.success .el-icon { background: #8b5cf6; box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3); }
.action-btn.info .el-icon { background: #3b82f6; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); }

/* Responsive */
@media (max-width: 1200px) {
  .bento-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .chart-card, .pie-card, .tasks-card, .actions-card {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .bento-grid {
    grid-template-columns: 1fr;
  }
  .chart-card, .pie-card, .tasks-card, .actions-card {
    grid-column: span 1;
  }
}
</style>ign-items: center;
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