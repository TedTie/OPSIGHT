import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 基础布局
const Layout = () => import('@/views/Layout.vue')

// 页面组件
const Login = () => import('@/views/Login.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const Tasks = () => import('@/views/Tasks.vue')
const Reports = () => import('@/views/Reports.vue')
const Analytics = () => import('@/views/Analytics.vue')
const UserManagement = () => import('@/components/admin/UserManagement.vue')

// 简单路由配置
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { title: '仪表板' }
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: Tasks,
        meta: { title: '任务管理' }
      },
      {
        path: 'reports',
        name: 'Reports',
        component: Reports,
        meta: { title: '日报管理' }
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: Analytics,
        meta: { title: '数据分析' }
      },
      {
        path: 'admin/users',
        name: 'UserManagement',
        component: UserManagement,
        meta: {
          title: '用户管理',
          requiresSuperAdmin: true
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 简单的路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 检查是否需要认证
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }

  // 检查是否需要超级管理员权限
  if (to.meta.requiresSuperAdmin && !authStore.isSuperAdmin) {
    next('/dashboard')
    return
  }

  // 如果已登录但访问登录页，重定向到仪表板
  if (to.path === '/login' && authStore.isAuthenticated) {
    next('/dashboard')
    return
  }

  next()
})

export default router