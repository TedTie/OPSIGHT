<template>
  <el-header class="app-header">
    <div class="header-left">
      <el-button
        type="text"
        :icon="Expand"
        class="menu-toggle"
        @click="toggleSidebar"
      />
      <h1 class="app-title"><TextFlip text="OPSIGHT" /></h1>
    </div>
    
    <div class="header-right">
      <!-- 通知 -->
      <el-dropdown @command="handleNotificationCommand" trigger="click">
        <el-badge :value="notificationCount" :hidden="notificationCount === 0">
          <el-button type="text" :icon="Bell" class="header-button" />
        </el-badge>
        <template #dropdown>
          <el-dropdown-menu>
            <div class="notification-header">
              <span>通知消息</span>
              <el-button type="text" size="small" @click="markAllAsRead">全部已读</el-button>
            </div>
            <el-divider style="margin: 8px 0;" />
            <div class="notification-list">
              <div v-if="notificationsLoading" class="empty-notifications">加载中…</div>
              <div 
                v-for="notification in notifications" 
                :key="notification.id"
                class="notification-item"
                :class="{ 'unread': !notification.is_read }"
                @click="handleNotificationClick(notification)"
              >
                <div class="notification-content">
                  <div class="notification-title">{{ notification.title }}</div>
                  <div class="notification-message">{{ notification.message }}</div>
                  <div class="notification-time">{{ formatNotificationTime(notification.created_at) }}</div>
                </div>
                <div v-if="!notification.is_read" class="notification-dot"></div>
              </div>
              <div v-if="notifications.length === 0 && !notificationsLoading" class="empty-notifications">
                暂无通知消息
              </div>
            </div>
            <el-divider style="margin: 8px 0;" />
            <el-dropdown-item command="viewAll">
              <el-icon><Bell /></el-icon>
              查看全部通知
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <!-- 通知弹窗：查看全部通知 -->
      <el-dialog v-model="notificationsDialogVisible" title="通知消息" width="560px">
        <div class="notif-dialog-toolbar">
          <el-button text size="small" :loading="notificationsLoading" @click="refreshNotifications">刷新</el-button>
          <el-button text size="small" @click="markAllAsRead">全部已读</el-button>
        </div>
        <!-- 分组筛选标签 -->
        <el-tabs v-model="activeNotifTab" class="notif-tabs" @tab-change="onTabChange">
          <el-tab-pane :label="`全部(${counts.all})`" name="all" />
          <el-tab-pane :label="`任务提醒(${counts.task})`" name="task" />
          <el-tab-pane :label="`系统通知(${counts.system})`" name="system" />
          <el-tab-pane :label="`日报提醒(${counts.report})`" name="report" />
        </el-tabs>
        <div class="notif-dialog-list">
          <div v-if="notificationsLoading" class="empty-notifications">加载中…</div>
          <div v-else>
            <div 
              v-for="notification in filteredNotifications" 
              :key="notification.id"
              class="notification-item"
              :class="{ 'unread': !notification.is_read }"
            >
              <div class="notification-content" @click="handleNotificationClick(notification)">
                <div class="notification-title">{{ notification.title }}</div>
                <div class="notification-message">{{ notification.message }}</div>
                <div class="notification-time">{{ formatNotificationTime(notification.created_at) }}</div>
              </div>
              <div class="notification-actions">
                <el-button v-if="notification.type === 'task' && notification.meta?.taskId" size="small" type="primary" text @click.stop="completeTask(notification)">完成</el-button>
              </div>
              <div v-if="!notification.is_read" class="notification-dot"></div>
            </div>
            <div v-if="filteredNotifications.length === 0" class="empty-notifications">
              暂无通知消息
            </div>
          </div>
        </div>
      </el-dialog>
      
      <!-- 用户菜单 -->
      <el-dropdown @command="handleUserCommand">
        <div class="user-info">
          <el-avatar :size="32" :src="userAvatar">
            {{ userInitials }}
          </el-avatar>
          <span class="username">{{ authStore.user?.username }}</span>
          <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>
              个人资料
            </el-dropdown-item>
            <el-dropdown-item command="settings">
              <el-icon><Setting /></el-icon>
              设置
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import Expand from '~icons/tabler/layout-sidebar-left-expand'
import Bell from '~icons/tabler/bell'
import User from '~icons/tabler/user'
import Setting from '~icons/tabler/settings'
import SwitchButton from '~icons/tabler/logout'
import ArrowDown from '~icons/tabler/chevron-down'
import { useAuthStore } from '@/stores/auth'
import TextFlip from '@/components/Effects/TextFlip.vue'
import api from '@/utils/api'
const useMock = String(import.meta.env.VITE_USE_MOCK || '').toLowerCase() === 'true' && !!(import.meta.env && import.meta.env.DEV)

const router = useRouter()
const authStore = useAuthStore()

// 定义事件
const emit = defineEmits(['toggle-sidebar'])

// 通知相关数据
const notificationCount = ref(0)
const notifications = ref([])
const notificationsLoading = ref(false)
const notificationsDialogVisible = ref(false)
// 分组筛选
const activeNotifTab = ref('all')
const counts = computed(() => {
  return {
    all: notifications.value.length,
    task: notifications.value.filter(n => n.type === 'task').length,
    system: notifications.value.filter(n => n.type === 'system').length,
    report: notifications.value.filter(n => n.type === 'report').length,
  }
})
const filteredNotifications = computed(() => {
  if (activeNotifTab.value === 'all') return notifications.value
  return notifications.value.filter(n => n.type === activeNotifTab.value)
})
const onTabChange = () => {
  // 预留：切换标签时可上报埋点或做额外刷新
}

// 已读状态持久化
const READ_KEY = 'notifications_read_map'
const readMap = ref({})
const loadReadMap = () => {
  try { readMap.value = JSON.parse(localStorage.getItem(READ_KEY) || '{}') } catch (_) { readMap.value = {} }
}
const saveReadMap = () => {
  try { localStorage.setItem(READ_KEY, JSON.stringify(readMap.value)) } catch (_) {}
}

// 兜底模拟通知（仅在接口失败且空列表时使用）
const mockNotifications = [
  { id: 'mock-1', title: '任务提醒', message: '您有一个任务即将到期，请及时处理', type: 'task', is_read: false, created_at: new Date(Date.now() - 1000 * 60 * 30) },
  { id: 'mock-2', title: '系统通知', message: '系统将于今晚22:00进行维护，预计持续1小时', type: 'system', is_read: false, created_at: new Date(Date.now() - 1000 * 60 * 60 * 2) },
  { id: 'mock-3', title: '日报提醒', message: '今日日报尚未提交，请及时完成', type: 'report', is_read: true, created_at: new Date(Date.now() - 1000 * 60 * 60 * 4) }
]

// 用户头像
const userAvatar = computed(() => {
  const url = authStore.user?.avatar_url || ''
  console.log('[AppHeader] userAvatar:', url, 'user:', authStore.user)
  return url
})

// 用户姓名首字母
const userInitials = computed(() => {
  const user = authStore.user
  if (!user) return ''
  
  if (user.full_name) {
    return user.full_name.charAt(0).toUpperCase()
  }
  return user.username?.charAt(0).toUpperCase() || 'U'
})

// 切换侧边栏
const toggleSidebar = () => {
  emit('toggle-sidebar')
}

// 处理用户菜单命令
const handleUserCommand = async (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm(
          '确定要退出登录吗？',
          '提示',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        await authStore.logout()
        router.push('/login')
      } catch (error) {
        // 用户取消
      }
      break
  }
}

// 处理通知命令
const handleNotificationCommand = (command) => {
  switch (command) {
    case 'viewAll':
      // 打开弹窗显示全部通知
      notificationsDialogVisible.value = true
      break
  }
}

// 标记单条已读并处理点击跳转
const markAsRead = (notification) => {
  notification.is_read = true
  readMap.value[notification.id] = true
  saveReadMap()
  updateNotificationCount()
  syncServerRead([notification.id])
}
const handleNotificationClick = (notification) => {
  markAsRead(notification)
  // 根据通知类型跳转到相应页面
  switch (notification.type) {
    case 'task':
      if (notification.meta?.taskId) {
        router.push({ path: '/tasks', query: { openTaskId: notification.meta.taskId } })
      } else {
        router.push('/tasks')
      }
      break
    case 'report':
      if (notification.meta?.date) {
        router.push({ path: '/reports', query: { date: notification.meta.date } })
      } else {
        router.push('/reports')
      }
      break
    case 'system':
      ElMessage.info(notification.message)
      break
  }
}

// 从通知快速处理任务：跳转到任务页并打开对应任务详情
const completeTask = (notification) => {
  try {
    if (notification?.meta?.taskId) {
      markAsRead(notification)
      router.push({ path: '/tasks', query: { openTaskId: notification.meta.taskId } })
    } else {
      router.push('/tasks')
    }
  } catch (e) {
    console.error('跳转完成任务失败：', e)
    ElMessage.error('打开任务完成入口失败')
  }
}

// 标记所有通知为已读
const markAllAsRead = () => {
  notifications.value.forEach(notification => {
    notification.is_read = true
    readMap.value[notification.id] = true
  })
  saveReadMap()
  updateNotificationCount()
  syncServerRead(notifications.value.map(n => n.id))
  ElMessage.success('所有通知已标记为已读')
}

// 更新通知数量
const updateNotificationCount = () => {
  notificationCount.value = notifications.value.filter(n => !n.is_read).length
}

// 格式化通知时间
const formatNotificationTime = (dateInput) => {
  const date = (typeof dateInput === 'string') ? new Date(dateInput) : dateInput
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString()
}

// 从真实数据生成通知
const refreshNotifications = async () => {
  if (!authStore.isAuthenticated) {
    notifications.value = []
    updateNotificationCount()
    return
  }
  notificationsLoading.value = true
  try {
    const items = []
    // 任务：24小时内到期或已逾期且未完成
    const taskResp = await api.get('/tasks', { params: { page: 1, size: 50 }, suppressErrorMessage: true })
    const tData = taskResp.data
    const tasks = Array.isArray(tData) ? tData : (tData.items || tData.data || [])
    const now = new Date()
    const soonThresholdMs = 24 * 60 * 60 * 1000
    tasks.forEach(t => {
      const done = (t.is_completed === true) || (t.status === 'done')
      if (done) return
      if (!t.due_date) return
      const due = new Date(t.due_date)
      const diff = due.getTime() - now.getTime()
      const isOverdue = diff < 0
      const isSoon = diff >= 0 && diff <= soonThresholdMs
      if (!isOverdue && !isSoon) return
      items.push({
        id: `task-${t.id}`,
        title: isOverdue ? '任务逾期' : '任务提醒',
        message: isOverdue ? `${t.title} 已逾期` : `${t.title} 将在24小时内到期`,
        type: 'task',
        is_read: false,
        created_at: due,
        meta: { taskId: t.id }
      })
    })

    // 日报：今天未提交
    const uid = authStore.user?.id
    if (uid) {
      const todayStr = new Date().toISOString().split('T')[0]
      const repResp = await api.get('/reports', { params: { page: 1, size: 1, date_from: todayStr, date_to: todayStr, user_id: uid }, suppressErrorMessage: true })
      const rData = repResp.data
      const count = Array.isArray(rData) ? rData.length : ((rData.items || rData.data || []).length || 0)
      if (count === 0) {
        items.push({
          id: `report-${todayStr}`,
          title: '日报提醒',
          message: '今日日报尚未提交，请及时完成',
          type: 'report',
          is_read: false,
          created_at: new Date(),
          meta: { date: todayStr }
        })
      }
    }

    // 排序：最近优先
    notifications.value = items.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    // 同步已读状态
    notifications.value.forEach(n => { if (readMap.value[n.id]) n.is_read = true })
    updateNotificationCount()
  } catch (e) {
    console.error('刷新通知失败：', e)
    if (notifications.value.length === 0) {
      if (useMock) {
        notifications.value = [...mockNotifications]
        notifications.value.forEach(n => { if (readMap.value[n.id]) n.is_read = true })
        updateNotificationCount()
      } else {
        notifications.value = []
        updateNotificationCount()
      }
    }
  } finally {
    notificationsLoading.value = false
  }
}

// 多端已读同步：从服务端加载、上报已读
const loadServerReadMap = async () => {
  try {
    const resp = await api.get('/notifications/read-map', { suppressErrorMessage: true })
    const ids = resp?.data?.ids || []
    ids.forEach(id => { readMap.value[id] = true })
    saveReadMap()
    notifications.value.forEach(n => { if (readMap.value[n.id]) n.is_read = true })
    updateNotificationCount()
  } catch (_) {
    // 后端不可用时，继续本地方案
  }
}
const syncServerRead = async (ids) => {
  if (!Array.isArray(ids) || ids.length === 0) return
  try {
    await api.post('/notifications/read', { ids }, { suppressErrorMessage: true })
  } catch (_) {
    // 后端不可用时忽略
  }
}

// 组件挂载时初始化
onMounted(async () => {
  loadReadMap()
  await loadServerReadMap()
  await refreshNotifications()
})

// 登录用户变化时刷新通知
watch(() => authStore.user, async () => {
  loadReadMap()
  await loadServerReadMap()
  await refreshNotifications()
})

// 定时刷新（每5分钟）
let refreshTimer
onMounted(() => {
  refreshTimer = setInterval(() => refreshNotifications(), 5 * 60 * 1000)
})
onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.menu-toggle {
  font-size: 18px;
  color: var(--text-muted);
}

.app-title {
  font-size: 20px;
  font-weight: bold;
  margin: 0;
  background: var(--brand-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-button {
  font-size: 18px;
  color: var(--text-muted);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.user-info:hover {
  background-color: var(--bg-soft);
}

.username {
  font-size: 14px;
  color: var(--text-strong);
  font-weight: 500;
}

.dropdown-icon {
  font-size: 12px;
  color: #909399;
  transition: transform 0.2s;
}

.user-info:hover .dropdown-icon {
  transform: rotate(180deg);
}

/* 通知相关样式 */
.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px 8px;
  font-weight: 600;
  color: #303133;
}

.notification-list {
  max-height: 300px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
  position: relative;
}

.notification-item:hover {
  background-color: #f5f7fa;
}

.notification-item.unread {
  background-color: #f0f9ff;
}

.notification-item.unread::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: var(--el-color-primary);
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-message {
  font-size: 13px;
  color: #606266;
  line-height: 1.4;
  margin-bottom: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notification-time {
  font-size: 12px;
  color: #909399;
}

.notification-dot {
  width: 8px;
  height: 8px;
  background-color: #f56c6c;
  border-radius: 50%;
  margin-left: 8px;
  margin-top: 4px;
  flex-shrink: 0;
}

.notification-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 8px;
}

.empty-notifications {
  text-align: center;
  padding: 40px 16px;
  color: #909399;
  font-size: 14px;
}

/* 弹窗样式 */
.notif-dialog-toolbar { display: flex; justify-content: flex-end; gap: 8px; padding-bottom: 8px; }
.notif-tabs { margin-bottom: 8px; }
.notif-dialog-list { max-height: 420px; overflow-y: auto; }

/* 响应式设计 */
@media (max-width: 768px) {
  .app-header {
    padding: 0 16px;
  }
  
  .username {
    display: none;
  }
  
  .app-title {
    font-size: 18px;
  }
}
</style>