import { createRouter, createWebHistory } from 'vue-router'

// 导入布局组件
const AppLayout = () => import('@/components/Layout/AppLayout.vue')

// 导入页面组件
const Login = () => import('@/views/Login.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const Tasks = () => import('@/views/Tasks.vue')
const Reports = () => import('@/views/Reports.vue')
const Analytics = () => import('@/views/Analytics.vue')
const Settings = () => import('@/views/Settings.vue')
const AdminUsers = () => import('@/views/AdminUsers.vue')
const AdminGroups = () => import('@/views/AdminGroups.vue')
const AdminAI = () => import('@/views/AdminAI.vue')
const AdminMetrics = () => import('@/views/AdminMetrics.vue')
const PermissionTest = () => import('@/views/PermissionTest.vue')
const TestButtons = () => import('@/views/TestButtons.vue')
const Profile = () => import('@/views/Profile.vue')
const KnowledgeBase = () => import('@/views/KnowledgeBase.vue')

const routes = [
  {
    path: '/',
    redirect: (to) => {
      // 检查是否有token
      const token = localStorage.getItem('token')
      return token ? '/dashboard' : '/login'
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: AppLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: Tasks
      },
      {
        path: 'reports',
        name: 'Reports',
        component: Reports
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: Analytics
      },
      {
        path: 'settings',
        name: 'Settings',
        component: Settings,
        meta: { requiresSuperAdmin: true }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: Profile
      },
      {
        path: 'knowledge-base',
        name: 'KnowledgeBase',
        component: KnowledgeBase
      },
      {
        path: 'admin/users',
        name: 'AdminUsers',
        component: AdminUsers,
        meta: { requiresSuperAdmin: true }
      },
      {
        path: 'admin/groups',
        name: 'AdminGroups',
        component: AdminGroups,
        meta: { requiresAdmin: true }
      },
      {
        path: 'admin/ai',
        name: 'AdminAI',
        component: AdminAI,
        meta: { requiresSuperAdmin: true }
      },
      {
        path: 'admin/metrics',
        name: 'AdminMetrics',
        component: AdminMetrics,
        meta: { requiresSuperAdmin: true }
      },
      {
        path: 'permission-test',
        name: 'PermissionTest',
        component: PermissionTest
      },
      {
        path: 'test-buttons',
        name: 'TestButtons',
        component: TestButtons
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')
  
  // 检查是否需要认证
  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }
  
  // 如果已登录访问登录页，重定向到仪表板
  if (to.path === '/login' && token) {
    next('/dashboard')
    return
  }
  
  // 检查管理员权限
  if (to.meta.requiresAdmin && (!user || (user.role !== 'admin' && user.role !== 'super_admin'))) {
    next('/dashboard')
    return
  }
  
  // 检查超级管理员权限
  if (to.meta.requiresSuperAdmin && (!user || user.role !== 'super_admin')) {
    next('/dashboard')
    return
  }
  
  next()
})

export default router