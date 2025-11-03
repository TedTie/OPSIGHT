import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

import App from './App.vue'
import router from './router'
import pinia from './stores'
import { useAuthStore } from './stores/auth'
import { canDirective } from './directives/can'

import './style.css'

const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 使用插件
app.use(ElementPlus, {
  locale: zhCn,
})
app.use(router)
app.use(pinia)

// 注册自定义指令
app.directive('can', canDirective)

// 初始化认证状态
const authStore = useAuthStore()
authStore.initAuth()

app.mount('#app')