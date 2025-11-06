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
// 开发环境调试：捕获非法 setAttribute（如属性名为数字）
// 仅在开发模式启用，不影响生产环境
if (import.meta && import.meta.env && import.meta.env.DEV) {
  try {
    const originalSetAttribute = Element.prototype.setAttribute
    const isValidAttrName = (n) => typeof n === 'string' && /^[A-Za-z_][A-Za-z0-9_:\-.]*$/.test(n)
    Element.prototype.setAttribute = function(name, value) {
      const stack = (new Error('setAttribute debug stack')).stack
      // 发现非法属性名（如以数字开头），直接拦截并记录
      if (!isValidAttrName(name)) {
        console.warn('[dev] Blocked invalid attribute name', { name, value, el: this, stack })
        return // 阻止抛出 InvalidCharacterError
      }
      try {
        return originalSetAttribute.call(this, name, value)
      } catch (err) {
        console.error('[dev] setAttribute threw', { name, value, el: this, err, stack })
      }
    }
  } catch (e) {
    // 安全兜底：不影响正常运行
    console.warn('[dev] setAttribute debug instrumentation failed:', e)
  }
}

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

// 全局错误处理：记录详细信息，帮助定位 InvalidCharacterError
if (import.meta && import.meta.env && import.meta.env.DEV) {
  app.config.errorHandler = (err, instance, info) => {
    console.error('[GlobalError]', { err, info, instance })
  }
  window.addEventListener('error', (e) => {
    console.error('[WindowError]', e.error || e)
  })
}

app.mount('#app')