<template>
  <el-header class="app-header">
    <div class="header-left">
      <el-button
        type="text"
        :icon="Expand"
        class="menu-toggle"
        @click="toggleSidebar"
      />
      <h1 class="app-title">OPSIGHT</h1>
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
              <div v-if="notifications.length === 0" class="empty-notifications">
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
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Expand,
  Bell,
  User,
  Setting,
  SwitchButton,
  ArrowDown
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 定义事件
const emit = defineEmits(['toggle-sidebar'])

// 通知相关数据
const notificationCount = ref(0)
const notifications = ref([])

// 模拟通知数据
const mockNotifications = [
  {
    id: 1,
    title: '任务提醒',
    message: '您有一个任务即将到期，请及时处理',
    type: 'task',
    is_read: false,
    created_at: new Date(Date.now() - 1000 * 60 * 30) // 30分钟前
  },
  {
    id: 2,
    title: '系统通知',
    message: '系统将于今晚22:00进行维护，预计持续1小时',
    type: 'system',
    is_read: false,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 2) // 2小时前
  },
  {
    id: 3,
    title: '日报提醒',
    message: '今日日报尚未提交，请及时完成',
    type: 'report',
    is_read: true,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 4) // 4小时前
  }
]

// 用户头像
const userAvatar = computed(() => {
  return authStore.user?.avatar || ''
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
      // 跳转到通知页面（如果有的话）
      ElMessage.info('跳转到通知页面')
      break
  }
}

// 处理通知点击
const handleNotificationClick = (notification) => {
  // 标记为已读
  notification.is_read = true
  updateNotificationCount()
  
  // 根据通知类型跳转到相应页面
  switch (notification.type) {
    case 'task':
      router.push('/tasks')
      break
    case 'report':
      router.push('/reports')
      break
    case 'system':
      // 显示系统通知详情
      ElMessage.info(notification.message)
      break
  }
}

// 标记所有通知为已读
const markAllAsRead = () => {
  notifications.value.forEach(notification => {
    notification.is_read = true
  })
  updateNotificationCount()
  ElMessage.success('所有通知已标记为已读')
}

// 更新通知数量
const updateNotificationCount = () => {
  notificationCount.value = notifications.value.filter(n => !n.is_read).length
}

// 格式化通知时间
const formatNotificationTime = (date) => {
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

// 初始化通知数据
const initNotifications = () => {
  notifications.value = [...mockNotifications]
  updateNotificationCount()
}

// 组件挂载时初始化
onMounted(() => {
  initNotifications()
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
  color: #606266;
}

.app-title {
  font-size: 20px;
  font-weight: bold;
  color: #2c3e50;
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
  color: #606266;
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
  background-color: #f5f7fa;
}

.username {
  font-size: 14px;
  color: #303133;
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
  background-color: #409eff;
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

.empty-notifications {
  text-align: center;
  padding: 40px 16px;
  color: #909399;
  font-size: 14px;
}

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